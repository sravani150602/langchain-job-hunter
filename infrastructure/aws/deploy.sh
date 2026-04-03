#!/bin/bash
# =============================================
# AWS Deployment Script for FAANG Job Hunter
# Deploys to: EC2 (backend) + S3/CloudFront (frontend)
# Cost: ~$8-15/month (t3.micro + S3 + CloudFront)
# =============================================
set -e

# --- CONFIG (edit these) ---
APP_NAME="faang-job-hunter"
AWS_REGION="us-east-1"
EC2_INSTANCE_TYPE="t3.micro"       # free tier eligible
KEY_PAIR_NAME="your-ec2-keypair"   # create in AWS Console > EC2 > Key Pairs
YOUR_IP="0.0.0.0/0"               # restrict to your IP for security: "1.2.3.4/32"

echo "=== FAANG Job Hunter AWS Deployment ==="
echo "Region: $AWS_REGION"

# Step 1: Create S3 bucket for frontend
BUCKET_NAME="${APP_NAME}-frontend-$(date +%s)"
echo ""
echo ">>> Creating S3 bucket: $BUCKET_NAME"
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION
aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document index.html

# Build frontend
echo ""
echo ">>> Building frontend..."
cd ../../frontend
npm install
npm run build
aws s3 sync dist/ s3://$BUCKET_NAME --delete
cd ../infrastructure/aws

# Step 2: Create security group for EC2
echo ""
echo ">>> Creating EC2 security group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name "${APP_NAME}-sg" \
  --description "FAANG Job Hunter backend" \
  --region $AWS_REGION \
  --query 'GroupId' --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${APP_NAME}-sg" \
    --query 'SecurityGroups[0].GroupId' --output text)

# Allow HTTP + SSH
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 22 --cidr $YOUR_IP 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 8000 --cidr $YOUR_IP 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 2>/dev/null || true

# Step 3: Launch EC2 instance with user data
echo ""
echo ">>> Launching EC2 instance..."

# Create startup script
cat > /tmp/user_data.sh << 'USERDATA'
#!/bin/bash
apt-get update -y
apt-get install -y docker.io git

# Start Docker
systemctl start docker
systemctl enable docker

# Clone repo (or pull from S3/CodeCommit in production)
# For now, we'll pull from GitHub - update this URL
# git clone https://github.com/YOUR_USERNAME/faang-job-hunter.git /app

# For manual deployment: files will be SCP'd in
mkdir -p /app
cd /app

# Add cron job to refresh jobs every 30 minutes
(crontab -l 2>/dev/null; echo "*/30 * * * * curl -s -X POST http://localhost:8000/api/jobs/refresh/sync > /var/log/job-refresh.log 2>&1") | crontab -

echo "Setup complete!" > /var/log/setup.log
USERDATA

# Get latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
            "Name=state,Values=available" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text --region $AWS_REGION)

echo "Using AMI: $AMI_ID"

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type $EC2_INSTANCE_TYPE \
  --key-name $KEY_PAIR_NAME \
  --security-group-ids $SG_ID \
  --user-data file:///tmp/user_data.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${APP_NAME}}]" \
  --region $AWS_REGION \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text --region $AWS_REGION)

echo ""
echo "============================================"
echo "DEPLOYMENT COMPLETE!"
echo "============================================"
echo "EC2 Instance IP: $PUBLIC_IP"
echo "S3 Bucket (frontend): $BUCKET_NAME"
echo ""
echo "NEXT STEPS:"
echo "1. Copy your .env file to the server:"
echo "   scp -i ~/.ssh/${KEY_PAIR_NAME}.pem .env ubuntu@${PUBLIC_IP}:/app/"
echo ""
echo "2. Copy backend code to server:"
echo "   scp -ri ~/.ssh/${KEY_PAIR_NAME}.pem backend/ ubuntu@${PUBLIC_IP}:/app/"
echo ""
echo "3. SSH in and start the app:"
echo "   ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@${PUBLIC_IP}"
echo "   cd /app && docker build -t job-hunter ./backend && docker run -d -p 8000:8000 --env-file .env job-hunter"
echo ""
echo "4. Update frontend API URL to: http://${PUBLIC_IP}:8000"
echo "   Then rebuild and redeploy frontend to S3"
echo ""
echo "5. Access your app at: http://${PUBLIC_IP}:8000"

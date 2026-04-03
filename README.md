# FAANG Job Hunter
**LangChain-powered job tracker for fresh grad Software & Data Engineering roles**

Pulls jobs from FAANG companies as soon as they're posted, scores them against your profile using Claude AI, and shows you the best matches first.

---

## What it does
- **Fetches jobs** from Greenhouse (Uber, Stripe, Airbnb, Discord...), Lever (Netflix...), Amazon Jobs, and Adzuna (Google, Meta, Apple, Microsoft...)
- **AI-powered matching** via LangChain + Claude — scores each job 0-100 against your skills & YOE
- **Shows hours-since-posted** so you can apply before hundreds of others
- **Applicant count** shown where available (Greenhouse exposes this on some postings)
- **Auto-refreshes** every 30 minutes on AWS

---

## Quick Start (Local)

### 1. Clone & set up environment
```bash
cd /path/to/Langchain
cp .env.example .env
# Edit .env with your API keys
```

### 2. Get your API keys
| Key | Where to get | Required? |
|-----|-------------|-----------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Yes (for AI scoring) |
| `ADZUNA_APP_ID` + `ADZUNA_API_KEY` | [developer.adzuna.com](https://developer.adzuna.com) — free tier | For Google/Meta/Apple/Microsoft jobs |

> Greenhouse (Uber, Stripe, Airbnb etc.) and Lever (Netflix) require **no API key** — completely public.

### 3. Run with Docker Compose
```bash
docker-compose up
```
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Or run manually

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 5. Load jobs
Click **Refresh Jobs** in the UI. First load takes ~30-60 seconds.

---

## AWS Deployment (Daily Use)

### Option A: CloudFormation (Recommended — one command)

```bash
# Deploy infrastructure
aws cloudformation deploy \
  --template-file infrastructure/aws/cloudformation.yaml \
  --stack-name faang-job-hunter \
  --parameter-overrides \
    KeyPairName=your-keypair \
    AnthropicApiKey=sk-ant-... \
    AdzunaAppId=your_id \
    AdzunaApiKey=your_key \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Get your server IP
aws cloudformation describe-stacks \
  --stack-name faang-job-hunter \
  --query 'Stacks[0].Outputs'
```

### Option B: Manual EC2 Deployment

```bash
# 1. Launch EC2 t3.micro (Ubuntu 22.04) in AWS Console
# 2. SSH into it
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 3. Install Docker
sudo apt update && sudo apt install -y docker.io git
sudo systemctl start docker

# 4. Copy your project (from local)
scp -ri your-key.pem /c/Users/srava/Downloads/Langchain/ ubuntu@YOUR_EC2_IP:/app/

# 5. Build and run
cd /app
sudo docker build -t job-hunter ./backend
sudo docker run -d \
  --name job-hunter \
  -p 8000:8000 \
  --env-file .env \
  --restart always \
  job-hunter

# 6. Set up auto-refresh (every 30 min)
(crontab -l; echo "*/30 * * * * curl -s -X POST http://localhost:8000/api/jobs/refresh") | crontab -
```

### Monthly Cost Estimate (AWS)
| Resource | Cost |
|----------|------|
| EC2 t3.micro | ~$8/mo |
| DynamoDB (low traffic) | Free tier |
| Data transfer | ~$1/mo |
| **Total** | **~$9/mo** |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Your Browser                      │
│         React + TailwindCSS + React Query           │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / REST
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                      │
│  ┌─────────────┐  ┌──────────────────────────────┐  │
│  │   Fetchers  │  │    LangChain Job Matcher     │  │
│  │  Greenhouse │  │  Claude Haiku / GPT-4o-mini  │  │
│  │  Lever      │  │  LCEL Chain Pipeline         │  │
│  │  Adzuna     │  │  Score 0-100 per job         │  │
│  │  Amazon     │  └──────────────────────────────┘  │
│  └─────────────┘                                     │
│                    ┌────────────────┐                │
│                    │   Job Store    │                 │
│                    │ In-memory (dev)│                 │
│                    │ DynamoDB (prod)│                 │
│                    └────────────────┘                │
└──────────────────────────────────────────────────────┘

Auto-refresh: EventBridge (AWS) / cron → POST /api/jobs/refresh every 30 min
```

---

## Job Sources

| Source | Companies | Auth |
|--------|-----------|------|
| **Greenhouse** | Uber, Stripe, Airbnb, Discord, Figma, Databricks, Snowflake, OpenAI, Anthropic, + more | None (public API) |
| **Lever** | Netflix, Reddit, Dropbox | None (public API) |
| **Adzuna** | Google, Meta, Amazon, Apple, Microsoft, Nvidia, PayPal | Free API key |
| **Amazon Jobs** | Amazon (all teams) | None (public) |

---

## LangChain Integration
- **Model**: Claude Haiku (fast, cheap — ~$0.01 per 100 jobs scored)
- **Chain**: LCEL prompt → LLM → JSON parser
- **Output per job**: match score (0-100), reasons, skill gaps, one-line summary
- **Fallback**: keyword-based scoring if no API key configured

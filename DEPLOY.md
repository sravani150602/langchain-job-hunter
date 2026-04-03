# How to Deploy CareerCopilot AI — LIVE in 20 Minutes

Two options below. **Start with Option A** (free, no credit card for frontend).

---

## Option A: Render (Backend) + Vercel (Frontend) — FREE

### Step 1: Push to GitHub (one-time setup)

```bash
cd /c/Users/srava/Downloads/Langchain

# Initialize git
git init
git add .
git commit -m "Initial commit: CareerCopilot AI"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/careercopolit-ai.git
git push -u origin main
```

---

### Step 2: Deploy Backend on Render.com

1. Go to **render.com** → Sign up (free, no credit card)
2. Click **New +** → **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name**: `careercopolit-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Instance Type**: Free
5. Click **Add Environment Variables** and add:
   ```
   ANTHROPIC_API_KEY = sk-ant-...
   LANGCHAIN_API_KEY = ls__...
   LANGCHAIN_TRACING_V2 = true
   LANGCHAIN_PROJECT = faang-job-hunter
   LLM_PROVIDER = anthropic
   JOBRIGHT_MAX_JOBS = 60
   ```
6. Click **Deploy**. Wait ~3 min for first deploy.
7. Note your backend URL: `https://careercopolit-backend.onrender.com`

---

### Step 3: Deploy Frontend on Vercel (Free)

1. Go to **vercel.com** → Sign up with GitHub (free)
2. Click **Add New Project** → Import your GitHub repo
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add environment variable:
   ```
   VITE_API_URL = https://careercopolit-backend.onrender.com
   ```
5. Update `frontend/vite.config.js` to use env variable for proxy:
   (Already handled — Vite proxies `/api` to backend in dev mode)
6. Click **Deploy**. Done in ~2 min.
7. Your live URL: `https://careercopolit-ai.vercel.app`

---

### Step 4: Update Frontend API URL

In `frontend/src/hooks/useJobs.js`, the API calls use `/api/...` which works via Vite proxy in dev.

For production on Vercel, add a `vercel.json` to the frontend folder:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://careercopolit-backend.onrender.com/api/:path*"
    }
  ]
}
```

Create this file:
```bash
echo '{"rewrites":[{"source":"/api/:path*","destination":"https://YOUR-RENDER-URL.onrender.com/api/:path*"}]}' > frontend/vercel.json
git add frontend/vercel.json && git commit -m "Add Vercel API proxy" && git push
```

Vercel will auto-redeploy.

---

### Step 5: Set Up Auto-Refresh (Every 30 Minutes)

Use **cron-job.org** (free) to call your refresh endpoint automatically:

1. Go to **cron-job.org** → Sign up free
2. Create a new cron job:
   - URL: `https://careercopolit-backend.onrender.com/api/jobs/refresh`
   - Method: POST
   - Schedule: Every 30 minutes
3. Save. Now jobs auto-refresh every 30 min while you sleep!

> **Note on Render Free Tier**: The free tier spins down after 15 min of inactivity.
> The cron job above keeps it alive AND refreshes jobs. No action needed.

---

## Option B: AWS EC2 (More Control, ~$9/month)

Use the CloudFormation template in `infrastructure/aws/cloudformation.yaml`:

```bash
aws cloudformation deploy \
  --template-file infrastructure/aws/cloudformation.yaml \
  --stack-name careercopolit \
  --parameter-overrides \
    KeyPairName=your-ec2-keypair \
    AnthropicApiKey=sk-ant-... \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Get your server IP
aws cloudformation describe-stacks --stack-name careercopolit \
  --query 'Stacks[0].Outputs'

# SSH and deploy
ssh -i your-key.pem ubuntu@YOUR_IP
cd /app
docker build -t careercopolit ./backend
docker run -d -p 8000:8000 --env-file .env --restart always --name app careercopolit

# Build and serve frontend
cd /app/frontend && npm install && npm run build
# Serve via nginx or just visit http://YOUR_IP:8000 (backend serves frontend)
```

---

## Running Locally (Development)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Open http://localhost:5173
# Click "Refresh Jobs" to load from jobright.ai
```

---

## Architecture: 3 LangChain Features (for Professor Demo)

| Feature | LangChain Component | Where |
|---------|-------------------|-------|
| **Job Matching** | LCEL chain: `ChatPromptTemplate \| LLM \| JsonOutputParser` | `backend/app/chains/job_matcher.py` |
| **Resume Analysis** | LCEL chains for parsing, optimizing, interview prep | `backend/app/chains/resume_*.py`, `interview_prep.py` |
| **LangSmith Tracing** | `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` | All chains auto-traced |

After deploying, visit **smith.langchain.com** to see every AI call traced in real-time.

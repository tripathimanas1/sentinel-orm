---
description: Deploy Sentinel ORM to Render
---

# Deploy Sentinel ORM to Render

Render is another excellent cloud platform for deploying full-stack applications. This guide covers deploying Sentinel ORM to Render.

## Why Render?

- ✅ Free tier for web services
- ✅ Built-in PostgreSQL, Redis
- ✅ Automatic HTTPS
- ✅ Simple pricing
- ✅ GitHub integration
- ✅ No credit card for free tier

## Prerequisites

- [ ] GitHub account
- [ ] Render account (sign up at https://render.com)
- [ ] Code pushed to GitHub

## Architecture on Render

```
Frontend (Static Site) → Backend (Web Service) → PostgreSQL
                                                → Redis
                                                → ClickHouse (External)
```

## Step-by-Step Deployment

### 1. Push Code to GitHub

```powershell
git init
git add .
git commit -m "Deploy to Render"
git remote add origin https://github.com/yourusername/sentinel-orm.git
git branch -M main
git push -u origin main
```

### 2. Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Settings:
   - **Name:** `sentinel-postgres`
   - **Database:** `sentinel_orm`
   - **User:** `sentinel`
   - **Region:** Choose closest to you
   - **Plan:** Free (or paid for production)
4. Click **"Create Database"**
5. **Save the connection details** (Internal Database URL)

### 3. Create Redis Instance

1. Click **"New +"** → **"Redis"**
2. Settings:
   - **Name:** `sentinel-redis`
   - **Region:** Same as PostgreSQL
   - **Plan:** Free (max 25MB) or Starter
3. Click **"Create Redis"**
4. **Save the connection URL**

### 4. Set Up ClickHouse (External)

Since Render doesn't offer ClickHouse, use an external provider:

**Option A: ClickHouse Cloud (Recommended)**
1. Sign up at https://clickhouse.cloud
2. Create a free tier instance
3. Note connection details
4. Cost: Free tier available, then ~$0.37/hr

**Option B: Self-hosted on DigitalOcean/AWS**
1. Create a droplet/EC2 instance
2. Install ClickHouse
3. Configure firewall rules
4. Cost: ~$5-10/month

### 5. Deploy Backend Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `sentinel-backend`
   - **Region:** Same as databases
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** Python 3
   - **Build Command:** `pip install poetry && poetry install --no-dev`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or paid for production)

### 6. Configure Environment Variables

In your backend service, go to **Environment** and add:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<your-generated-secret>

# PostgreSQL (use Render's internal URL)
# Format: postgresql://user:password@host:port/database
DATABASE_URL=<your-postgres-internal-url>

# Or split it:
POSTGRES_HOST=<from-render-dashboard>
POSTGRES_PORT=5432
POSTGRES_DB=sentinel_orm
POSTGRES_USER=sentinel
POSTGRES_PASSWORD=<from-render-dashboard>

# ClickHouse
CLICKHOUSE_HOST=<clickhouse-cloud-host>
CLICKHOUSE_PORT=9440
CLICKHOUSE_DB=sentinel_events
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<your-password>

# Redis (use Render's internal URL)
REDIS_URL=<your-redis-internal-url>

# Or split it:
REDIS_HOST=<from-render-dashboard>
REDIS_PORT=6379

# Kafka - Use Upstash or CloudKarafka
KAFKA_BOOTSTRAP_SERVERS=<external-kafka-url>

# API Credentials
TWITTER_BEARER_TOKEN=<your-token>
RAPIDAPI_KEY=<your-key>
REDDIT_CLIENT_ID=<your-id>
REDDIT_CLIENT_SECRET=<your-secret>

# Add all other variables from .env.production
```

### 7. Create render.yaml (Infrastructure as Code)

Create `render.yaml` in your project root:

```yaml
services:
  # Backend API
  - type: web
    name: sentinel-backend
    runtime: python
    plan: free  # or starter, standard
    buildCommand: pip install poetry && poetry install --no-dev
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: SECRET_KEY
        generateValue: true
      - key: POSTGRES_HOST
        fromDatabase:
          name: sentinel-postgres
          property: host
      - key: POSTGRES_PORT
        fromDatabase:
          name: sentinel-postgres
          property: port
      - key: POSTGRES_DB
        fromDatabase:
          name: sentinel-postgres
          property: database
      - key: POSTGRES_USER
        fromDatabase:
          name: sentinel-postgres
          property: user
      - key: POSTGRES_PASSWORD
        fromDatabase:
          name: sentinel-postgres
          property: password
      - key: REDIS_HOST
        fromService:
          name: sentinel-redis
          type: redis
          property: host
      # Add other env vars here

  # Frontend Static Site
  - type: web
    name: sentinel-frontend
    runtime: static
    buildCommand: echo "No build needed"
    staticPublishPath: ./frontend
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

databases:
  - name: sentinel-postgres
    plan: free  # or starter
    databaseName: sentinel_orm
    user: sentinel

  - name: sentinel-redis
    plan: free  # or starter
```

### 8. Deploy Frontend

**Option 1: Render Static Site**

1. Click **"New +"** → **"Static Site"**
2. Connect your repository
3. Configure:
   - **Name:** `sentinel-frontend`
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** (leave empty for static files)
   - **Publish Directory:** `.`
4. Click **"Create Static Site"**

**Option 2: Netlify (Recommended for Frontend)**

1. Go to https://netlify.com
2. **"Add new site"** → **"Import from Git"**
3. Select repository
4. Configure:
   - **Base directory:** `frontend`
   - **Build command:** (empty)
   - **Publish directory:** `frontend`
5. Deploy

### 9. Update Frontend API URL

After backend is deployed, get the backend URL (e.g., `https://sentinel-backend.onrender.com`)

Edit `frontend/app.js`:

```javascript
const API_URL = 'https://sentinel-backend.onrender.com';
```

Commit and push to redeploy.

### 10. Run Database Migrations

After first deployment:

**Using Render Shell:**

1. Go to your backend service
2. Click **"Shell"** in the top right
3. Run: `poetry run alembic upgrade head`

**Or use Render Deploy Hook:**

Add to your service settings → Environment:
```bash
PRE_DEPLOY_COMMAND=poetry run alembic upgrade head
```

Render will run this before each deployment.

### 11. Set Up Background Workers (Optional)

If you need background tasks (e.g., scrapers):

1. Click **"New +"** → **"Background Worker"**
2. Use same repository
3. Configure:
   - **Start Command:** `python scripts/run_live_ingestion.py`
   - Use same environment variables as backend
4. Deploy

### 12. Custom Domain

1. Go to service **Settings**
2. Click **"Custom Domain"**
3. Add your domain
4. Update DNS records (Render provides instructions)
5. SSL is automatic

## Cost Estimation

**Render Free Tier:**
- Web services: 750 hours/month (1 service running 24/7)
- PostgreSQL: 90 days free, then expires
- Redis: 25MB free
- Static sites: Unlimited

**Paid Plans (Monthly):**
- Web Service (Starter): $7/month
- PostgreSQL (Starter): $7/month
- Redis (Starter): $10/month
- **Total: ~$24/month**

**External Services:**
- ClickHouse Cloud: Free tier or ~$27/month
- Upstash Kafka: Free tier (10K messages/day)

**Total Estimated Cost: $24-51/month**

## Monitoring

**View Logs:**
1. Go to service dashboard
2. Click **"Logs"**
3. Real-time streaming logs

**Metrics:**
- CPU, Memory, Bandwidth in dashboard
- Set up alerts in Settings

## Auto-Deploy

Render auto-deploys on every push to main branch.

**Configure:**
1. Settings → **"Auto-Deploy"**
2. Choose **"Yes"** or **"No"**

## Troubleshooting

### Build Failures

**Problem:** Poetry installation fails

**Solution:**
Update build command:
```bash
pip install --upgrade pip && pip install poetry && poetry install --no-dev
```

### Database Connection Issues

**Problem:** Can't connect to PostgreSQL

**Solution:**
- Use internal URL (faster, free bandwidth)
- Check environment variables
- Verify database is running

### Service Crashes

**Problem:** Service keeps restarting

**Solution:**
1. Check logs for errors
2. Verify all env vars are set
3. Ensure health check endpoint (`/health`) works
4. Check resource limits

### Slow Cold Starts (Free Tier)

**Problem:** Service spins down after 15 min of inactivity

**Solution:**
- Upgrade to paid plan for always-on
- Use external uptime monitor to ping every 10 min (not recommended for production)

## Backup Strategy

**PostgreSQL:**

Render provides daily backups on paid plans.

**Manual Backup:**
```bash
# Using Render shell
pg_dump $DATABASE_URL > backup.sql
```

**Automated Backups:**

Set up GitHub Actions to backup regularly.

## Health Checks

Render automatically monitors your health check endpoint.

Configure in `render.yaml`:
```yaml
healthCheckPath: /health
```

Or in dashboard under **Health & Alerts**.

## Secrets Management

**Add Secrets:**

1. Dashboard → Environment
2. Click **"Add Environment Variable"**
3. Check **"Secret"** for sensitive values
4. Secrets are encrypted at rest

## CI/CD Pipeline

**GitHub Actions Integration:**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Trigger Render Deploy
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

Get deploy hook URL from Render dashboard → Settings → Deploy Hook.

## Next Steps

1. ✅ Test all endpoints
2. ✅ Verify data ingestion
3. ✅ Set up monitoring
4. ✅ Configure backups
5. ✅ Add custom domain
6. ✅ Enable auto-scaling (paid plans)

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Status: https://status.render.com

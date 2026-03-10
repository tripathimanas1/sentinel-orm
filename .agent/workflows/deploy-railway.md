---
description: Deploy Sentinel ORM to Railway
---

# Deploy Sentinel ORM to Railway

Railway is the easiest cloud platform for deploying full-stack applications with databases. This guide will walk you through deploying Sentinel ORM to Railway.

## Why Railway?

- ✅ Free tier with $5 credit/month
- ✅ Built-in PostgreSQL, Redis databases
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Simple pricing ($0.000231/GB-hour)
- ✅ No credit card required for trial

## Prerequisites

- [ ] GitHub account
- [ ] Railway account (sign up at https://railway.app)
- [ ] Your Sentinel ORM code pushed to GitHub

## Step-by-Step Deployment

### 1. Prepare Your Code

**Push to GitHub:**

```powershell
# Initialize git if not already done
git init
git add .
git commit -m "Prepare for Railway deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/yourusername/sentinel-orm.git
git branch -M main
git push -u origin main
```

### 2. Create Railway Project

1. Go to https://railway.app and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your `sentinel-orm` repository
5. Railway will detect your app automatically

### 3. Add Required Services

You need to add these services to your Railway project:

**A. Add PostgreSQL:**
1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically create a PostgreSQL instance
3. Note: Railway will auto-generate connection credentials

**B. Add Redis:**
1. Click **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway will automatically create a Redis instance

**C. Add ClickHouse (Custom):**

ClickHouse isn't a Railway template, so we'll use a Docker deployment:

1. Click **"+ New"** → **"Empty Service"**
2. Name it `clickhouse`
3. Go to **Settings** → **Source** → **Image**
4. Enter: `clickhouse/clickhouse-server:latest`
5. Under **Variables**, add:
   - `CLICKHOUSE_DB=sentinel_events`
   - `CLICKHOUSE_USER=default`
   - `CLICKHOUSE_PASSWORD=<strong-password>`
6. Under **Networking**, expose port `8123` (HTTP) and `9000` (Native)

### 4. Configure Backend Service

Click on your main application service (backend):

**A. Set Environment Variables:**

Go to **Variables** tab and add all from `.env.production`:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<your-generated-secret>

# PostgreSQL (use Railway's provided variables)
POSTGRES_HOST=${{Postgres.PGHOST}}
POSTGRES_PORT=${{Postgres.PGPORT}}
POSTGRES_DB=${{Postgres.PGDATABASE}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}

# ClickHouse (reference your ClickHouse service)
CLICKHOUSE_HOST=${{clickhouse.RAILWAY_PRIVATE_DOMAIN}}
CLICKHOUSE_PORT=9000
CLICKHOUSE_DB=sentinel_events
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<your-clickhouse-password>

# Redis (use Railway's provided variables)
REDIS_HOST=${{Redis.REDIS_PRIVATE_URL}}
REDIS_PORT=6379

# Kafka - Use Upstash Kafka (free tier)
# Sign up at https://upstash.com
KAFKA_BOOTSTRAP_SERVERS=<your-upstash-kafka-endpoint>

# API Keys
TWITTER_BEARER_TOKEN=<your-token>
RAPIDAPI_KEY=<your-key>
REDDIT_CLIENT_ID=<your-id>
REDDIT_CLIENT_SECRET=<your-secret>

# Add all other variables from .env.production
```

**B. Configure Build:**

Go to **Settings** → **Build**:
- Build Command: (leave default, Railway auto-detects)
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**C. Set Port:**

Railway auto-assigns a PORT variable, but make sure your app uses it:
- In Settings → Variables, ensure `PORT` is set (Railway does this automatically)

### 5. Create Nixpacks Configuration

Railway uses Nixpacks for building. Create `nixpacks.toml` in your project root:

```toml
[phases.setup]
nixPkgs = ["python311", "poetry"]

[phases.install]
cmds = ["poetry install --no-dev --no-interaction"]

[phases.build]
cmds = []

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

### 6. Deploy Frontend (Separate Service)

**Option A: Deploy to Railway (Static Site)**

1. Click **"+ New"** → **"Empty Service"**
2. Name it `frontend`
3. Connect to your GitHub repo
4. Go to Settings → Build:
   - Root Directory: `/frontend`
   - Build Command: (none needed for static files)
5. Install Nginx buildpack or use static serving

**Option B: Deploy to Vercel (Recommended for Frontend)**

1. Go to https://vercel.com
2. Import your GitHub repository
3. Set Root Directory: `frontend`
4. Deploy

**Update API URL in Frontend:**

Edit `frontend/app.js`:
```javascript
const API_URL = 'https://your-backend.railway.app';
```

Then redeploy.

### 7. Run Database Migrations

Once deployed, run migrations:

1. Go to your backend service in Railway
2. Click **"Deploy Logs"**
3. Wait for deployment to complete
4. Go to **Settings** → **Service**
5. Click **"One-off Command"**
6. Run: `poetry run alembic upgrade head`

Or use Railway CLI:

```powershell
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run poetry run alembic upgrade head
```

### 8. Set Up Kafka (Upstash)

Since Railway doesn't have Kafka, use Upstash (free tier):

1. Sign up at https://upstash.com
2. Create a new Kafka cluster (free tier available)
3. Get connection details
4. Update `KAFKA_BOOTSTRAP_SERVERS` in Railway environment variables

### 9. Health Check & Verify

1. **Check Backend:**
   - Visit: `https://your-backend.railway.app/health`
   - Should return `{"status": "ok"}`

2. **Check API Docs:**
   - Visit: `https://your-backend.railway.app/docs`

3. **Check Frontend:**
   - Visit your frontend URL

### 10. Custom Domain (Optional)

**Add Custom Domain:**

1. Go to your service Settings
2. Click **"Domains"**
3. Click **"Custom Domain"**
4. Add your domain (e.g., `api.yourdomain.com`)
5. Update DNS records as instructed by Railway
6. Wait for SSL certificate to provision (automatic)

## Cost Estimation

**Railway Free Tier:**
- $5 credit/month
- Typically enough for small projects
- ~500 hours of usage

**Estimated Monthly Cost (after free tier):**
- Backend: ~$5-10/month
- PostgreSQL: ~$5/month
- Redis: ~$2/month
- ClickHouse: ~$5-10/month
- **Total: ~$17-27/month**

**Upstash (Kafka):**
- Free tier: 10K messages/day
- Paid: $0.2 per 100K messages

## Monitoring & Logs

**View Logs:**
1. Go to your service
2. Click **"Deploy Logs"** or **"Build Logs"**
3. Real-time logs appear

**Metrics:**
1. Railway provides CPU, Memory, and Network metrics
2. View in the **"Metrics"** tab

## Troubleshooting

### Build Fails

**Problem:** Poetry installation fails

**Solution:** Add `nixpacks.toml` (see Step 5)

### Database Connection Errors

**Problem:** Backend can't connect to databases

**Solution:** 
- Use Railway's reference variables: `${{Postgres.PGHOST}}`
- Ensure all services are in the same project
- Check logs for exact error

### Port Binding Error

**Problem:** `Address already in use`

**Solution:**
- Ensure you're using Railway's `$PORT` variable
- Update start command: `--host 0.0.0.0 --port $PORT`

### ClickHouse Connection Issues

**Problem:** Can't connect to ClickHouse

**Solution:**
- Use private networking: `${{clickhouse.RAILWAY_PRIVATE_DOMAIN}}`
- Ensure port 9000 is exposed
- Check ClickHouse logs

## Backup Strategy

**PostgreSQL Backup:**

Railway doesn't auto-backup on free tier. Set up manual backups:

```powershell
# Using Railway CLI
railway run pg_dump -U postgres sentinel_orm > backup.sql
```

**Scheduled Backups:**

Use GitHub Actions to schedule backups (see `.github/workflows/backup.yml`)

## Scaling

**Vertical Scaling:**
1. Go to service Settings
2. Adjust CPU/Memory limits

**Horizontal Scaling:**
- Railway supports horizontal scaling on paid plans
- Enable replicas in service settings

## CI/CD

Railway auto-deploys on every push to main branch.

**Configure Auto-Deploy:**
1. Settings → Source
2. Enable **"Auto Deploy"**
3. Select branch (main)

**Disable for manual deploys:**
1. Turn off Auto Deploy
2. Manually trigger with **"Deploy"** button

## Environment Management

**Staging Environment:**

Create separate Railway project for staging:
1. Duplicate project
2. Connect to `staging` branch
3. Update environment variables

## Next Steps

After deployment:

1. ✅ Test all API endpoints
2. ✅ Verify data ingestion works
3. ✅ Check ML models load correctly  
4. ✅ Set up monitoring alerts
5. ✅ Configure backup strategy
6. ✅ Add custom domain
7. ✅ Enable HTTPS (automatic on Railway)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://railway.statuspage.io

---
description: Deploy Sentinel ORM Application
---

# Deployment Workflow for Sentinel ORM

This workflow guides you through deploying the Sentinel ORM application to production.

## Prerequisites

Before deploying, ensure you have:
- [ ] All code tested and working locally
- [ ] Docker and Docker Compose installed
- [ ] Production environment variables configured
- [ ] Database backups strategy in place
- [ ] Monitoring tools configured

## Deployment Options

Choose one of the following deployment methods:

### Option 1: Docker Compose Production Deployment (Recommended for VPS/Self-Hosted)

This deploys all services (backend, databases, frontend) using Docker on a single server or VPS.

**Step 1:** Create production environment file

```bash
cp .env .env.production
```

**Step 2:** Update `.env.production` with production values:
- Change `ENVIRONMENT=production`
- Change `DEBUG=false`
- Set strong `SECRET_KEY` (generate with: `openssl rand -hex 32`)
- Update database passwords
- Configure external service URLs
- Set proper CORS origins

**Step 3:** Create production Docker Compose file

Create `docker-compose.prod.yml` (see file creation below)

**Step 4:** Build and start all services

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

**Step 5:** Wait for services to be healthy

```bash
docker-compose -f docker-compose.prod.yml ps
```

**Step 6:** Run database migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend poetry run alembic upgrade head
```

**Step 7:** Initialize database with test data (optional)

```bash
docker-compose -f docker-compose.prod.yml exec backend python scripts/test_system.py
```

**Step 8:** Verify deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
curl http://localhost:8000/docs
```

### Option 2: Cloud Platform Deployment (Railway, Render, etc.)

**For Railway:**

**Step 1:** Install Railway CLI

```bash
npm install -g @railway/cli
```

**Step 2:** Login to Railway

```bash
railway login
```

**Step 3:** Initialize project

```bash
railway init
```

**Step 4:** Add services via Railway dashboard:
- PostgreSQL database
- Redis instance
- ClickHouse (via template or custom)

**Step 5:** Set environment variables in Railway dashboard using `.env.production` values

**Step 6:** Deploy backend

```bash
railway up
```

**Step 7:** Deploy frontend to a static hosting service (Netlify, Vercel, or Railway static site)

### Option 3: AWS Deployment (Advanced)

**Services needed:**
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- EC2 for ClickHouse or managed alternative
- ALB for load balancing
- Route53 for DNS
- S3 + CloudFront for frontend

(Detailed AWS deployment requires infrastructure-as-code setup with Terraform/CloudFormation)

## Post-Deployment Steps

**Step 1:** Set up SSL/TLS certificates

For Let's Encrypt with Nginx:
```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Step 2:** Configure monitoring

- Set up logging aggregation
- Configure alerts for service health
- Set up uptime monitoring
- Configure error tracking (Sentry, etc.)

**Step 3:** Set up backups

```bash
# PostgreSQL backup (add to crontab)
docker exec sentinel-postgres pg_dump -U sentinel sentinel_orm > backup_$(date +%Y%m%d).sql

# ClickHouse backup
docker exec sentinel-clickhouse clickhouse-client --query "BACKUP DATABASE sentinel_events TO Disk('backups', 'backup_$(date +%Y%m%d)')"
```

**Step 4:** Configure firewall rules

```bash
# Example for UFW on Ubuntu
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

**Step 5:** Test the deployment

- [ ] Frontend loads correctly
- [ ] API endpoints respond
- [ ] Database connections work
- [ ] Real-time data ingestion works
- [ ] ML models are functioning
- [ ] Monitoring is active

## Rollback Procedure

If deployment fails:

```bash
# Stop new containers
docker-compose -f docker-compose.prod.yml down

# Restore previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Restore database if needed
docker exec -i sentinel-postgres psql -U sentinel sentinel_orm < backup_<date>.sql
```

## Maintenance

**Update application:**
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec backend poetry run alembic upgrade head
```

**View logs:**
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Restart services:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

## Performance Tuning

1. **PostgreSQL:** Adjust `shared_buffers`, `work_mem` in postgres config
2. **ClickHouse:** Configure memory limits and compression
3. **Redis:** Set maxmemory policy
4. **Application:** Tune worker count, connection pools

## Security Checklist

- [ ] All default passwords changed
- [ ] Secrets stored in environment variables, not in code
- [ ] HTTPS enabled with valid certificates
- [ ] Firewall configured properly
- [ ] Database access restricted to application only
- [ ] API rate limiting enabled
- [ ] CORS configured correctly
- [ ] Security headers set (HSTS, CSP, etc.)
- [ ] Regular security updates scheduled

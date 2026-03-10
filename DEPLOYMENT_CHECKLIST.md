# 🚀 Sentinel ORM Deployment Checklist

Use this checklist to ensure a smooth deployment to production.

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing locally
- [ ] Code reviewed and approved
- [ ] No debug code or console.logs in production
- [ ] Error handling implemented
- [ ] Logging configured properly

### Configuration
- [ ] `.env.production` file created from `.env.production.example`
- [ ] `SECRET_KEY` generated (use: `openssl rand -hex 32` or PowerShell equivalent)
- [ ] Strong database passwords set
- [ ] API credentials configured (Twitter, Reddit, RapidAPI)
- [ ] CORS origins updated for production domain
- [ ] Frontend API endpoint configured correctly

### Infrastructure
- [ ] Docker and Docker Compose installed on target server
- [ ] Sufficient disk space (minimum 20GB recommended)
- [ ] Sufficient RAM (minimum 8GB recommended)
- [ ] Firewall rules configured
- [ ] Domain name configured (if applicable)
- [ ] SSL certificates obtained (Let's Encrypt recommended)

## Deployment Steps

### 1. Initial Setup

```powershell
# Clone repository (if not already done)
git clone <your-repo-url>
cd sentinel-orm

# Create production environment file
cp .env.production.example .env.production

# Edit .env.production with your production values
notepad .env.production
```

### 2. Generate Secrets

Generate a secure secret key:

```powershell
# PowerShell
$secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "SECRET_KEY=$secret"
```

Or use Python:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Update Configuration

Edit `.env.production` and update:
- `SECRET_KEY=<generated-secret>`
- `POSTGRES_PASSWORD=<strong-password>`
- `CLICKHOUSE_PASSWORD=<strong-password>`
- `TWITTER_BEARER_TOKEN=<your-token>`
- `RAPIDAPI_KEY=<your-key>`
- `REDDIT_CLIENT_ID=<your-id>`
- `REDDIT_CLIENT_SECRET=<your-secret>`
- `CORS_ORIGINS=https://yourdomain.com`

### 4. Update Frontend API URL

Edit `frontend/app.js` and update the API URL to your production backend URL (if different from localhost).

### 5. Deploy

Run the deployment script:

```powershell
# Windows PowerShell
.\deploy.ps1
```

Or manually:

```powershell
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start (30 seconds)
Start-Sleep -Seconds 30

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend poetry run alembic upgrade head

# Check health
curl http://localhost:8000/health
```

## Post-Deployment Checklist

### Verification
- [ ] Frontend loads at http://localhost or your domain
- [ ] Backend API responds at http://localhost:8000/health
- [ ] API documentation accessible at http://localhost:8000/docs
- [ ] Database connections working (check logs)
- [ ] Social media scrapers working
- [ ] ML models loading correctly

### Security
- [ ] SSL/TLS configured (for production domains)
- [ ] Firewall rules in place
- [ ] Only necessary ports exposed
- [ ] Default passwords changed
- [ ] Environment variables not committed to git
- [ ] Security headers configured in Nginx

### Monitoring
- [ ] Application logs accessible
- [ ] Database logs accessible
- [ ] Error tracking configured (optional: Sentry)
- [ ] Uptime monitoring configured (optional: UptimeRobot)
- [ ] Backup strategy in place

### Performance
- [ ] API response times acceptable
- [ ] Database queries optimized
- [ ] Caching working correctly
- [ ] Memory usage normal
- [ ] CPU usage normal

## Useful Commands

### View Logs
```powershell
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f postgres

# ClickHouse
docker-compose -f docker-compose.prod.yml logs -f clickhouse
```

### Service Management
```powershell
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose -f docker-compose.prod.yml down -v
```

### Database Operations
```powershell
# PostgreSQL shell
docker-compose -f docker-compose.prod.yml exec postgres psql -U sentinel -d sentinel_orm

# ClickHouse shell
docker-compose -f docker-compose.prod.yml exec clickhouse clickhouse-client

# Redis shell
docker-compose -f docker-compose.prod.yml exec redis redis-cli
```

### Backup
```powershell
# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U sentinel sentinel_orm > backup_$(Get-Date -Format "yyyyMMdd").sql

# Backup volumes
docker-compose -f docker-compose.prod.yml exec postgres tar -czf /tmp/pg_backup.tar.gz /var/lib/postgresql/data
docker cp sentinel-postgres-prod:/tmp/pg_backup.tar.gz ./backups/
```

## Troubleshooting

### Services Won't Start
```powershell
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check specific container logs
docker-compose -f docker-compose.prod.yml logs backend

# Restart problematic service
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Issues
```powershell
# Verify PostgreSQL is running
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U sentinel

# Verify ClickHouse is running
docker-compose -f docker-compose.prod.yml exec clickhouse clickhouse-client --query "SELECT 1"

# Check network connectivity
docker-compose -f docker-compose.prod.yml exec backend ping postgres
```

### Port Conflicts
If ports are already in use, edit `docker-compose.prod.yml` and change the host ports:
- PostgreSQL: `5432:5432` → `5433:5432`
- Backend: `8000:8000` → `8001:8000`
- Nginx: `80:80` → `8080:80`

### Out of Memory
Increase Docker memory limits or reduce service memory usage in `docker-compose.prod.yml`.

## Rollback

If deployment fails, rollback to previous version:

```powershell
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git log --oneline  # Find previous commit
git checkout <previous-commit-hash>

# Redeploy
.\deploy.ps1
```

## SSL/TLS Setup (Production Only)

### Using Let's Encrypt with Certbot

```powershell
# Install Certbot (on server)
# For Ubuntu/Debian:
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test renewal
sudo certbot renew --dry-run

# Setup auto-renewal (cron)
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet
```

Then uncomment the HTTPS server block in `nginx/nginx.conf`.

## Next Steps

After successful deployment:

1. **Monitor** - Keep an eye on logs and metrics for the first 24-48 hours
2. **Test** - Run through all critical user flows
3. **Document** - Note any deployment-specific configurations
4. **Backup** - Set up automated backups
5. **Scale** - Plan for horizontal scaling if needed

## Support

If you encounter issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify configuration: `.env.production`
3. Check service health: `docker-compose -f docker-compose.prod.yml ps`
4. Review documentation: `README.md` and `DEPLOYMENT_CHECKLIST.md`

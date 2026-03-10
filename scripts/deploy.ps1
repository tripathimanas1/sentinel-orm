# Production deployment script for Sentinel ORM (Windows PowerShell)
# Usage: .\deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Sentinel ORM Production Deployment..." -ForegroundColor Cyan

# Check if .env.production exists
if (-Not (Test-Path .env.production)) {
    Write-Host "❌ Error: .env.production file not found!" -ForegroundColor Red
    Write-Host "Please create .env.production from .env.production.example"
    exit 1
}

# Load environment variables from .env.production
Get-Content .env.production | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($name -and -not $name.StartsWith('#')) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Validate critical environment variables
Write-Host "📋 Validating environment variables..." -ForegroundColor Yellow

$secretKey = [Environment]::GetEnvironmentVariable("SECRET_KEY", "Process")
if ($secretKey -eq "CHANGE_ME_USE_OPENSSL_RAND_HEX_32") {
    Write-Host "❌ Error: SECRET_KEY is not set!" -ForegroundColor Red
    Write-Host "Generate one with PowerShell:" -ForegroundColor Yellow
    Write-Host '$secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_}); Write-Host $secret'
    exit 1
}

$pgPassword = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD", "Process")
if ($pgPassword -eq "CHANGE_ME_STRONG_PASSWORD") {
    Write-Host "❌ Error: POSTGRES_PASSWORD is not set!" -ForegroundColor Red
    exit 1
}

$chPassword = [Environment]::GetEnvironmentVariable("CLICKHOUSE_PASSWORD", "Process")
if ($chPassword -eq "CHANGE_ME_STRONG_PASSWORD") {
    Write-Host "❌ Error: CLICKHOUSE_PASSWORD is not set!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment validation passed" -ForegroundColor Green

# Build and start containers
Write-Host "🐳 Building and starting Docker containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

docker-compose -f docker-compose.prod.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker compose up failed!" -ForegroundColor Red
    exit 1
}

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "🏥 Checking service status..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml ps

# Wait for PostgreSQL to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
do {
    $pgReady = docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U sentinel 2>&1
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "PostgreSQL is unavailable - waiting..."
    Start-Sleep -Seconds 2
    $attempt++
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ PostgreSQL failed to start!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green

# Wait for ClickHouse to be ready
Write-Host "⏳ Waiting for ClickHouse to be ready..." -ForegroundColor Yellow
$attempt = 0
do {
    $chReady = docker-compose -f docker-compose.prod.yml exec -T clickhouse clickhouse-client --query "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "ClickHouse is unavailable - waiting..."
    Start-Sleep -Seconds 2
    $attempt++
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ ClickHouse failed to start!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ ClickHouse is ready" -ForegroundColor Green

# Run database migrations
Write-Host "🗄️  Running database migrations..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml exec -T backend poetry run alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations completed" -ForegroundColor Green
} else {
    Write-Host "❌ Migrations failed!" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
}

# Health check
Write-Host "🔍 Running health checks..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check backend health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
}

# Check nginx
try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Nginx is serving frontend" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Nginx check failed (may be normal if not configured)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📌 Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:         docker-compose -f docker-compose.prod.yml logs -f"
Write-Host "  View backend logs: docker-compose -f docker-compose.prod.yml logs -f backend"
Write-Host "  Restart services:  docker-compose -f docker-compose.prod.yml restart"
Write-Host "  Stop services:     docker-compose -f docker-compose.prod.yml down"
Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "  Frontend:         http://localhost"
Write-Host "  Backend:          http://localhost:8000"
Write-Host "  API Docs:         http://localhost:8000/docs"
Write-Host "  Redpanda Console: http://localhost:8080"
Write-Host ""
Write-Host "⚠️  Remember to configure SSL/TLS for production!" -ForegroundColor Yellow

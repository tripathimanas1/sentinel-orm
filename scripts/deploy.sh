#!/bin/bash
# Production deployment script for Sentinel ORM
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting Sentinel ORM Production Deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production file not found!${NC}"
    echo "Please create .env.production from .env.production.example"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.production | xargs)

# Validate critical environment variables
echo "📋 Validating environment variables..."

if [ "$SECRET_KEY" = "CHANGE_ME_USE_OPENSSL_RAND_HEX_32" ]; then
    echo -e "${RED}❌ Error: SECRET_KEY is not set!${NC}"
    echo "Generate one with: openssl rand -hex 32"
    exit 1
fi

if [ "$POSTGRES_PASSWORD" = "CHANGE_ME_STRONG_PASSWORD" ]; then
    echo -e "${RED}❌ Error: POSTGRES_PASSWORD is not set!${NC}"
    exit 1
fi

if [ "$CLICKHOUSE_PASSWORD" = "CHANGE_ME_STRONG_PASSWORD" ]; then
    echo -e "${RED}❌ Error: CLICKHOUSE_PASSWORD is not set!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment validation passed${NC}"

# Pull latest code (optional, comment out if deploying from local)
# echo "📥 Pulling latest code..."
# git pull origin main

# Build and start containers
echo "🐳 Building and starting Docker containers..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U sentinel > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Wait for ClickHouse to be ready
echo "⏳ Waiting for ClickHouse to be ready..."
until docker-compose -f docker-compose.prod.yml exec -T clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; do
    echo "ClickHouse is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}✅ ClickHouse is ready${NC}"

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend poetry run alembic upgrade head
echo -e "${GREEN}✅ Migrations completed${NC}"

# Optional: Initialize with test data (comment out for production)
# echo "📊 Initializing test data..."
# docker-compose -f docker-compose.prod.yml exec -T backend python scripts/test_system.py

# Health check
echo "🔍 Running health checks..."
sleep 5

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

# Check nginx
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx is serving frontend${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx check failed (may be normal if not configured)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📌 Useful commands:"
echo "  View logs:        docker-compose -f docker-compose.prod.yml logs -f"
echo "  View backend logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Stop services:    docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🌐 Access points:"
echo "  Frontend:  http://localhost"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Redpanda Console: http://localhost:8080"
echo ""
echo -e "${YELLOW}⚠️  Remember to configure SSL/TLS for production!${NC}"

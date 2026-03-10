"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.logging import setup_logging
from app.db.postgres import get_postgres_engine, close_postgres_engine
from app.db.clickhouse import get_clickhouse_client, close_clickhouse_client
from app.db.redis import get_redis_client, close_redis_client

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await get_postgres_engine()
    await get_clickhouse_client()
    await get_redis_client()
    
    yield
    
    # Shutdown
    await close_postgres_engine()
    await close_clickhouse_client()
    await close_redis_client()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered Online Reputation Intelligence & Early Warning System",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )


@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint."""
    return JSONResponse(
        content={
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "AI-powered Online Reputation Intelligence System",
        }
    )


# Import and include routers
from app.api.v1 import brand_health, sentiment, risk_alerts, source_insights

app.include_router(brand_health.router, prefix=settings.api_v1_prefix, tags=["brand-health"])
app.include_router(sentiment.router, prefix=settings.api_v1_prefix, tags=["sentiment"])
app.include_router(risk_alerts.router, prefix=settings.api_v1_prefix, tags=["risk-alerts"])
app.include_router(source_insights.router, prefix=settings.api_v1_prefix, tags=["source-insights"])
# app.include_router(attribution.router, prefix=settings.api_v1_prefix, tags=["attribution"])
# app.include_router(explanations.router, prefix=settings.api_v1_prefix, tags=["explanations"])
# app.include_router(actions.router, prefix=settings.api_v1_prefix, tags=["actions"])

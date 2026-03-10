"""Brand health API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.ml.brand_health import BrandHealthEngine
from app.db.redis import cache_get, cache_set
from app.config import get_settings
import json

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


class BrandHealthResponse(BaseModel):
    """Brand health response model."""

    snapshot_id: str
    brand_id: str
    timestamp: datetime
    health_index: float = Field(..., ge=0, le=100, description="Brand health index [0-100]")
    weighted_sentiment: float = Field(..., ge=-1, le=1, description="Credibility-weighted sentiment")
    volume_score: float = Field(..., ge=0, le=1, description="Signal volume score")
    diversity_score: float = Field(..., ge=0, le=1, description="Source diversity score")
    recency_score: float = Field(..., ge=0, le=1, description="Recency score")
    signal_count: int = Field(..., ge=0, description="Number of signals in window")
    time_window_hours: int
    model_version: str
    trend: Optional[str] = Field(None, description="Trend direction: improving, declining, stable")


@router.get("/brand-health/{brand_id}", response_model=BrandHealthResponse)
async def get_brand_health(
    brand_id: str,
    time_window: Optional[int] = Query(
        None, description="Time window in hours (overrides default)"
    ),
    granularity: Optional[str] = Query("current", description="Granularity: current, hourly, daily"),
) -> BrandHealthResponse:
    """Get brand health metrics.
    
    Args:
        brand_id: Brand identifier
        time_window: Optional time window override
        granularity: Time granularity for aggregation
    
    Returns:
        Brand health metrics
    """
    try:
        # Check cache
        cache_key = f"brand_health:{brand_id}:{time_window or 'default'}"
        cached = await cache_get(cache_key)
        
        if cached:
            logger.debug("Brand health cache hit", brand_id=brand_id)
            data = json.loads(cached)
            return BrandHealthResponse(**data)
        
        # Compute brand health
        engine = BrandHealthEngine()
        
        # Override window if provided
        if time_window:
            engine.window_hours = time_window
        
        health_data = engine.compute_brand_health(brand_id)
        
        # Determine trend (simplified - compare with previous period)
        # TODO: Implement proper trend calculation
        health_data["trend"] = "stable"
        
        # Cache result
        await cache_set(
            cache_key,
            json.dumps(health_data, default=str),
            ttl=settings.cache_brand_health_ttl,
        )
        
        logger.info(
            "Computed brand health",
            brand_id=brand_id,
            health_index=health_data["health_index"],
        )
        
        return BrandHealthResponse(**health_data)
    
    except Exception as e:
        logger.error("Failed to get brand health", brand_id=brand_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to compute brand health: {str(e)}")


@router.get("/brand-health/{brand_id}/history")
async def get_brand_health_history(
    brand_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    granularity: str = Query("daily", description="Granularity: hourly, daily, weekly"),
) -> dict:
    """Get historical brand health data.
    
    Args:
        brand_id: Brand identifier
        start_date: Start date for history
        end_date: End date for history
        granularity: Time granularity
    
    Returns:
        Historical brand health data
    """
    try:
        # TODO: Implement historical query from ClickHouse
        # This would query brand_health_snapshots table
        
        return {
            "brand_id": brand_id,
            "start_date": start_date,
            "end_date": end_date,
            "granularity": granularity,
            "data_points": [],
            "message": "Historical data endpoint - implementation pending",
        }
    
    except Exception as e:
        logger.error("Failed to get brand health history", brand_id=brand_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

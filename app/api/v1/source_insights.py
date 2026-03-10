"""Source insights API endpoints."""

from typing import Any, Dict, List, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.ml.source_insights import SourceInsightsEngine
from app.services.ml.llm_visibility import LLMVisibilityEngine

logger = get_logger(__name__)
router = APIRouter()

class VisibilityMetrics(BaseModel):
    views: int
    engagement: int
    volume: int

class ConversionMetrics(BaseModel):
    count: int
    value: float

class PRHealthMetrics(BaseModel):
    sentiment: float
    negative_signals: int
    anger: float
    frustration: float
    credibility: float = 0.5

class LLMVisibilityMetrics(BaseModel):
    score: float
    risk_level: str
    risk_score: float = 0.0
    potential_drop_pct: float = 0.0
    reasons: List[str] = []
    cross_model_scores: Dict[str, float] = {}

class PlatformInsight(BaseModel):
    visibility: VisibilityMetrics
    conversions: ConversionMetrics
    pr_health: PRHealthMetrics
    llm_visibility: LLMVisibilityMetrics

class SourceInsightsResponse(BaseModel):
    brand_id: str
    period_days: int
    platforms: Dict[str, PlatformInsight]
    top_insights: List[str]

class SimulationAction(str, Enum):
    LAUNCH_PR_CAMPAIGN = "launch_pr_campaign"
    INCREASE_SOCIAL_POSTS = "increase_social_posts"
    PARTNER_WITH_INFLUENCER = "partner_with_influencer"
    IMPROVE_CUSTOMER_SUPPORT = "improve_customer_support"
    GET_VERIFIED = "get_verified"

class SimulationRequest(BaseModel):
    brand_id: str
    platform: Optional[str] = None
    current_metrics: Optional[Dict[str, float]] = None
    actions: List[SimulationAction]
    model_name: str = "average"

class SimulationResponse(BaseModel):
    original_score: float
    new_score: float
    absolute_change: float
    percent_change: float
    model_used: str
    actions_applied: List[str]
    volatility_used: Dict[str, float] = {}
    baseline_metrics: Dict[str, float]

@router.get("/source-insights/{brand_id}", response_model=SourceInsightsResponse)
async def get_source_insights(
    brand_id: str,
    lookback_days: int = Query(90, ge=1, le=180, description="Lookback period in days")
) -> SourceInsightsResponse:
    """Get source-specific performance and PR insights."""
    try:
        engine = SourceInsightsEngine()
        engine.lookback_days = lookback_days
        
        insights = engine.get_source_performance(brand_id)
        
        return SourceInsightsResponse(**insights)
    
    except Exception as e:
        logger.error("Failed to get source insights", brand_id=brand_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/source-insights/simulate", response_model=SimulationResponse)
async def simulate_visibility_change(
    request: SimulationRequest
) -> SimulationResponse:
    """Simulate how business actions affect LLM visibility based on brand volatility.
    
    Args:
        request: SimulationRequest containing brand_id, actions, and optional platform.
    """
    try:
        llm_engine = LLMVisibilityEngine()
        source_engine = SourceInsightsEngine()
        
        # 0. Get Baseline Metrics (Auto-fetched or Provided)
        baseline = request.current_metrics
        if not baseline:
            # Auto-fetch if not provided
            baseline = source_engine.get_brand_metrics(request.brand_id, request.platform)
            
        # 1. Get Brand Volatility (or defaults)
        volatility = {
            "sentiment": 0.2,    # Default sigma: Sentiment moves 0.2 on [-1,1] scale
            "engagement": 0.5,   # Default sigma: Log engagement moves 0.5
            "volume": 0.2,       # Default sigma: Volume moves 20% relative
            "credibility": 0.1
        }
        
        try:
            # Override with real data
            # Fetching real stddev from DB
            real_vol = source_engine.get_brand_volatility(request.brand_id)
            volatility.update(real_vol)
        except Exception as e:
            logger.warning(f"Failed to fetch brand volatility for {request.brand_id}, using defaults.", error=str(e))

        # 2. Translate Actions to Metric Changes (Scaled by Volatility)
        # We define actions as "Sigma Events" (e.g. PR Campaign = +1.5 Sigma Sentiment)
        aggregated_changes = {
            "credibility": 0.0,
            "sentiment": 0.0,
            "engagement": 0.0,
            "volume": 0.0
        }
        
        # Define impact in terms of SIGMA MULTIPLIERS
        # E.g., PR Campaign is a +1.5 Sigma event for Sentiment
        sigma_map = {
            SimulationAction.LAUNCH_PR_CAMPAIGN: {"sentiment": 1.5, "volume": 1.0, "credibility": 0.5},
            SimulationAction.INCREASE_SOCIAL_POSTS: {"volume": 2.0, "engagement": 0.5},
            SimulationAction.PARTNER_WITH_INFLUENCER: {"engagement": 2.5, "sentiment": 0.5, "volume": 1.5},
            SimulationAction.IMPROVE_CUSTOMER_SUPPORT: {"sentiment": 2.0, "credibility": 1.0},
            SimulationAction.GET_VERIFIED: {"credibility": 4.0} # Massive jump in credibility usually
        }
        
        for action in request.actions:
            multipliers = sigma_map.get(action, {})
            for metric, sigma in multipliers.items():
                if metric in volatility:
                    # Calculate raw delta: Sigma * Volatility
                    delta = sigma * volatility[metric]
                    aggregated_changes[metric] += delta

        result = llm_engine.simulate_content_change(
            baseline,
            aggregated_changes,
            request.model_name
        )
        
        # Add metadata
        result["actions_applied"] = [a.value for a in request.actions]
        result["volatility_used"] = volatility
        result["baseline_metrics"] = baseline
        
        return SimulationResponse(**result)
    except Exception as e:
        logger.error("Failed to simulate visibility", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

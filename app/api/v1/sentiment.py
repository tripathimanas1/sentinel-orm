"""Sentiment trends API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.db.clickhouse import execute_clickhouse_query

logger = get_logger(__name__)
router = APIRouter()


class SentimentDataPoint(BaseModel):
    """Single sentiment data point."""

    timestamp: datetime
    sentiment_score: float = Field(..., ge=-1, le=1)
    confidence: float = Field(..., ge=0, le=1)
    signal_count: int


class SentimentTrendsResponse(BaseModel):
    """Sentiment trends response."""

    brand_id: str
    start_date: datetime
    end_date: datetime
    source_type: Optional[str]
    granularity: str
    credibility_weighted: bool
    data_points: list[SentimentDataPoint]
    aggregations: dict


@router.get("/sentiment-trends/{brand_id}", response_model=SentimentTrendsResponse)
async def get_sentiment_trends(
    brand_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    granularity: str = Query("daily", description="Granularity: hourly, daily, weekly"),
    credibility_weighted: bool = Query(True, description="Apply credibility weighting"),
) -> SentimentTrendsResponse:
    """Get sentiment trends over time.
    
    Args:
        brand_id: Brand identifier
        start_date: Start date (defaults to 7 days ago)
        end_date: End date (defaults to now)
        source_type: Optional source type filter
        granularity: Time granularity
        credibility_weighted: Whether to weight by credibility
    
    Returns:
        Sentiment trends data
    """
    try:
        # Default date range
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=7)
        
        # Build query
        if credibility_weighted:
            query = """
            SELECT
                toStartOfDay(ss.timestamp) AS day,
                AVG(ss.sentiment_score * cs.credibility_score) AS avg_sentiment,
                AVG(ss.confidence) AS avg_confidence,
                COUNT(*) AS signal_count
            FROM sentiment_scores ss
            LEFT JOIN credibility_scores cs ON ss.event_id = cs.event_id
            WHERE ss.brand_id = %(brand_id)s
              AND ss.timestamp >= %(start_date)s
              AND ss.timestamp <= %(end_date)s
            """
        else:
            query = """
            SELECT
                toStartOfDay(timestamp) AS day,
                AVG(sentiment_score) AS avg_sentiment,
                AVG(confidence) AS avg_confidence,
                COUNT(*) AS signal_count
            FROM sentiment_scores
            WHERE brand_id = %(brand_id)s
              AND timestamp >= %(start_date)s
              AND timestamp <= %(end_date)s
            """
        
        if source_type:
            query += " AND source_type = %(source_type)s"
        
        query += " GROUP BY day ORDER BY day"
        
        # Execute query
        params = {
            "brand_id": brand_id,
            "start_date": start_date,
            "end_date": end_date,
        }
        if source_type:
            params["source_type"] = source_type
        
        results = execute_clickhouse_query(query, params)
        
        # Format data points
        data_points = [
            SentimentDataPoint(
                timestamp=row[0],
                sentiment_score=float(row[1]),
                confidence=float(row[2]),
                signal_count=int(row[3]),
            )
            for row in results
        ]
        
        # Calculate aggregations
        if data_points:
            sentiments = [dp.sentiment_score for dp in data_points]
            aggregations = {
                "mean_sentiment": sum(sentiments) / len(sentiments),
                "min_sentiment": min(sentiments),
                "max_sentiment": max(sentiments),
                "total_signals": sum(dp.signal_count for dp in data_points),
            }
        else:
            aggregations = {
                "mean_sentiment": 0.0,
                "min_sentiment": 0.0,
                "max_sentiment": 0.0,
                "total_signals": 0,
            }
        
        logger.info(
            "Retrieved sentiment trends",
            brand_id=brand_id,
            data_points=len(data_points),
        )
        
        return SentimentTrendsResponse(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date,
            source_type=source_type,
            granularity=granularity,
            credibility_weighted=credibility_weighted,
            data_points=data_points,
            aggregations=aggregations,
        )
    
    except Exception as e:
        logger.error("Failed to get sentiment trends", brand_id=brand_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

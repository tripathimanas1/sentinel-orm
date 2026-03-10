"""Risk alerts API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.db.clickhouse import execute_clickhouse_query

logger = get_logger(__name__)
router = APIRouter()


class RiskAlert(BaseModel):
    """Risk alert model."""

    risk_id: str
    brand_id: str
    detected_at: datetime
    risk_type: str
    severity: str
    confidence: float = Field(..., ge=0, le=1)
    risk_score: float
    velocity: float
    amplification_risk: float
    business_impact: float
    description: str
    trigger_event_ids: list[str]
    affected_sources: list[str]
    status: str
    resolved_at: Optional[datetime] = None


class RiskAlertsResponse(BaseModel):
    """Risk alerts response."""

    brand_id: str
    alerts: list[RiskAlert]
    total_count: int
    active_critical: int
    active_high: int
    active_medium: int


@router.get("/risk-alerts/{brand_id}", response_model=RiskAlertsResponse)
async def get_risk_alerts(
    brand_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: str = Query("active", description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of alerts"),
) -> RiskAlertsResponse:
    """Get risk alerts for a brand.
    
    Args:
        brand_id: Brand identifier
        severity: Optional severity filter (low, medium, high, critical)
        status: Status filter (active, resolved, all)
        limit: Maximum number of alerts to return
    
    Returns:
        Risk alerts
    """
    try:
        # Build query
        query = """
        SELECT
            risk_id,
            brand_id,
            detected_at,
            risk_type,
            severity,
            confidence,
            risk_score,
            velocity,
            amplification_risk,
            business_impact,
            description,
            trigger_event_ids,
            affected_sources,
            status,
            resolved_at
        FROM risk_events
        WHERE brand_id = %(brand_id)s
        """
        
        params = {"brand_id": brand_id}
        
        if status != "all":
            query += " AND status = %(status)s"
            params["status"] = status
        
        if severity:
            query += " AND severity = %(severity)s"
            params["severity"] = severity
        
        query += " ORDER BY detected_at DESC LIMIT %(limit)s"
        params["limit"] = limit
        
        # Execute query
        results = execute_clickhouse_query(query, params)
        
        # Format alerts
        alerts = [
            RiskAlert(
                risk_id=row[0],
                brand_id=row[1],
                detected_at=row[2],
                risk_type=row[3],
                severity=row[4],
                confidence=float(row[5]),
                risk_score=float(row[6]),
                velocity=float(row[7]),
                amplification_risk=float(row[8]),
                business_impact=float(row[9]),
                description=row[10],
                trigger_event_ids=row[11],
                affected_sources=row[12],
                status=row[13],
                resolved_at=row[14],
            )
            for row in results
        ]
        
        # Count active alerts by severity
        active_critical = sum(1 for a in alerts if a.status == "active" and a.severity == "critical")
        active_high = sum(1 for a in alerts if a.status == "active" and a.severity == "high")
        active_medium = sum(1 for a in alerts if a.status == "active" and a.severity == "medium")
        
        logger.info(
            "Retrieved risk alerts",
            brand_id=brand_id,
            total=len(alerts),
            active_critical=active_critical,
        )
        
        return RiskAlertsResponse(
            brand_id=brand_id,
            alerts=alerts,
            total_count=len(alerts),
            active_critical=active_critical,
            active_high=active_high,
            active_medium=active_medium,
        )
    
    except Exception as e:
        logger.error("Failed to get risk alerts", brand_id=brand_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-alerts/{brand_id}/{risk_id}", response_model=RiskAlert)
async def get_risk_alert_detail(brand_id: str, risk_id: str) -> RiskAlert:
    """Get detailed information about a specific risk alert.
    
    Args:
        brand_id: Brand identifier
        risk_id: Risk alert identifier
    
    Returns:
        Risk alert details
    """
    try:
        query = """
        SELECT
            risk_id,
            brand_id,
            detected_at,
            risk_type,
            severity,
            confidence,
            risk_score,
            velocity,
            amplification_risk,
            business_impact,
            description,
            trigger_event_ids,
            affected_sources,
            status,
            resolved_at
        FROM risk_events
        WHERE brand_id = %(brand_id)s AND risk_id = %(risk_id)s
        LIMIT 1
        """
        
        results = execute_clickhouse_query(
            query, {"brand_id": brand_id, "risk_id": risk_id}
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Risk alert not found")
        
        row = results[0]
        return RiskAlert(
            risk_id=row[0],
            brand_id=row[1],
            detected_at=row[2],
            risk_type=row[3],
            severity=row[4],
            confidence=float(row[5]),
            risk_score=float(row[6]),
            velocity=float(row[7]),
            amplification_risk=float(row[8]),
            business_impact=float(row[9]),
            description=row[10],
            trigger_event_ids=row[11],
            affected_sources=row[12],
            status=row[13],
            resolved_at=row[14],
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get risk alert detail", risk_id=risk_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

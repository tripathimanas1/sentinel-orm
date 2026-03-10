"""Brand Health Index computation engine."""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import numpy as np

from app.config import get_settings
from app.core.logging import get_logger
from app.db.clickhouse import execute_clickhouse_query

logger = get_logger(__name__)
settings = get_settings()


class BrandHealthEngine:
    """Compute Brand Health Index from sentiment, credibility, and engagement data.
    
    The Brand Health Index is a transparent composite metric that combines:
    1. Credibility-weighted sentiment
    2. Volume score (signal count)
    3. Source diversity score
    4. Recency score (time decay)
    
    Output range: [0, 100] where higher is better.
    """

    def __init__(self) -> None:
        self.window_hours = settings.health_index_window_hours
        self.recency_decay_hours = settings.recency_decay_hours

    def compute_brand_health(
        self, brand_id: str, timestamp: Optional[datetime] = None
    ) -> dict[str, Any]:
        """Compute Brand Health Index for a brand.
        
        Args:
            brand_id: Brand ID
            timestamp: Reference timestamp (defaults to now)
        
        Returns:
            Dictionary with health index and components
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        window_start = timestamp - timedelta(hours=self.window_hours)
        
        # Query sentiment and credibility scores
        query = """
        SELECT
            se.event_id,
            se.timestamp,
            se.source_type,
            ss.sentiment_score,
            cs.credibility_score,
            se.likes + se.shares + se.comments AS engagement
        FROM signal_events se
        LEFT JOIN sentiment_scores ss ON se.event_id = ss.event_id
        LEFT JOIN credibility_scores cs ON se.event_id = cs.event_id
        WHERE se.brand_id = %(brand_id)s
          AND se.timestamp >= %(window_start)s
          AND se.timestamp <= %(timestamp)s
        """
        
        results = execute_clickhouse_query(
            query,
            {
                "brand_id": brand_id,
                "window_start": window_start,
                "timestamp": timestamp,
            },
        )
        
        if not results:
            # No data - return neutral health
            return self._create_health_snapshot(
                brand_id=brand_id,
                timestamp=timestamp,
                health_index=50.0,
                weighted_sentiment=0.0,
                volume_score=0.0,
                diversity_score=0.0,
                recency_score=0.0,
                signal_count=0,
            )
        
        # Extract data
        sentiments = []
        credibilities = []
        source_types = []
        timestamps_list = []
        
        for row in results:
            event_id, ts, source_type, sentiment, credibility, engagement = row
            
            if sentiment is not None and credibility is not None:
                sentiments.append(sentiment)
                credibilities.append(credibility)
                source_types.append(source_type)
                timestamps_list.append(ts)
        
        if not sentiments:
            return self._create_health_snapshot(
                brand_id=brand_id,
                timestamp=timestamp,
                health_index=50.0,
                weighted_sentiment=0.0,
                volume_score=0.0,
                diversity_score=0.0,
                recency_score=0.0,
                signal_count=len(results),
            )
        
        # 1. Credibility-weighted sentiment
        sentiments = np.array(sentiments)
        credibilities = np.array(credibilities)
        
        weighted_sentiment = np.average(sentiments, weights=credibilities)
        
        # 2. Volume score (normalized)
        signal_count = len(sentiments)
        volume_score = min(signal_count / 100.0, 1.0)  # Cap at 100 signals
        
        # 3. Source diversity score
        unique_sources = len(set(source_types))
        max_sources = 5  # review, social, ticket, news, influencer
        diversity_score = unique_sources / max_sources
        
        # 4. Recency score (time decay)
        recency_scores = []
        for ts in timestamps_list:
            hours_ago = (timestamp - ts).total_seconds() / 3600
            decay = np.exp(-hours_ago / self.recency_decay_hours)
            recency_scores.append(decay)
        
        recency_score = np.mean(recency_scores)
        
        # Compute final health index
        # Weighted combination of components
        health_index = (
            40 * (weighted_sentiment + 1) / 2  # Convert [-1,1] to [0,1], weight 40%
            + 30 * volume_score  # 30%
            + 20 * diversity_score  # 20%
            + 10 * recency_score  # 10%
        )
        
        health_index = np.clip(health_index, 0.0, 100.0)
        
        return self._create_health_snapshot(
            brand_id=brand_id,
            timestamp=timestamp,
            health_index=float(health_index),
            weighted_sentiment=float(weighted_sentiment),
            volume_score=float(volume_score),
            diversity_score=float(diversity_score),
            recency_score=float(recency_score),
            signal_count=signal_count,
        )

    def _create_health_snapshot(
        self,
        brand_id: str,
        timestamp: datetime,
        health_index: float,
        weighted_sentiment: float,
        volume_score: float,
        diversity_score: float,
        recency_score: float,
        signal_count: int,
    ) -> dict[str, Any]:
        """Create a brand health snapshot dictionary."""
        return {
            "snapshot_id": str(uuid4()),
            "brand_id": brand_id,
            "timestamp": timestamp,
            "health_index": health_index,
            "weighted_sentiment": weighted_sentiment,
            "volume_score": volume_score,
            "diversity_score": diversity_score,
            "recency_score": recency_score,
            "signal_count": signal_count,
            "time_window_hours": self.window_hours,
            "model_version": "v1.0.0",
        }

"""Signal processor for ingesting and storing events."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from app.config import get_settings
from app.core.logging import get_logger
from app.db.clickhouse import execute_clickhouse_insert

logger = get_logger(__name__)
settings = get_settings()


class SignalProcessor:
    """Process and store signal events."""

    async def process_signal(self, event: dict[str, Any]) -> None:
        """Process a signal event and store in ClickHouse.
        
        Args:
            event: Signal event data
        """
        try:
            # Validate required fields
            required_fields = ["brand_id", "source_id", "source_type", "platform", "text"]
            for field in required_fields:
                if field not in event:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure event has ID and timestamp
            if "event_id" not in event:
                event["event_id"] = str(uuid4())
            
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow()
            
            # Prepare data for ClickHouse
            author_metadata = event.get("author_metadata", "{}")
            if not isinstance(author_metadata, str):
                import json
                author_metadata = json.dumps(author_metadata)

            raw_data = event.get("raw_data", "{}")
            if not isinstance(raw_data, str):
                import json
                raw_data = json.dumps(raw_data)

            signal_data = {
                "event_id": event["event_id"],
                "brand_id": event["brand_id"],
                "source_id": event["source_id"],
                "source_type": event["source_type"],
                "platform": event["platform"],
                "timestamp": event["timestamp"],
                "text": event["text"],
                "language": event.get("language", "en"),
                "author_id": event.get("author_id", ""),
                "author_name": event.get("author_name", ""),
                "author_metadata": author_metadata,
                "likes": event.get("likes", 0),
                "shares": event.get("shares", 0),
                "comments": event.get("comments", 0),
                "views": event.get("views", 0),
                "raw_data": raw_data,
            }
            
            # Store in ClickHouse
            execute_clickhouse_insert("signal_events", [signal_data])
            
            logger.info(
                "Stored signal event",
                event_id=signal_data["event_id"],
                brand_id=signal_data["brand_id"],
                source_type=signal_data["source_type"],
            )
        
        except Exception as e:
            logger.error(
                "Failed to process signal",
                event_id=event.get("event_id"),
                error=str(e),
            )
            raise

    async def process_sentiment_score(self, score: dict[str, Any]) -> None:
        """Store sentiment score in ClickHouse."""
        try:
            execute_clickhouse_insert("sentiment_scores", [score])
            logger.debug("Stored sentiment score", event_id=score.get("event_id"))
        except Exception as e:
            logger.error("Failed to store sentiment score", error=str(e))
            raise

    async def process_emotion_vector(self, emotion: dict[str, Any]) -> None:
        """Store emotion vector in ClickHouse."""
        try:
            execute_clickhouse_insert("emotion_vectors", [emotion])
            logger.debug("Stored emotion vector", event_id=emotion.get("event_id"))
        except Exception as e:
            logger.error("Failed to store emotion vector", error=str(e))
            raise

    async def process_credibility_score(self, credibility: dict[str, Any]) -> None:
        """Store credibility score in ClickHouse."""
        try:
            execute_clickhouse_insert("credibility_scores", [credibility])
            logger.debug("Stored credibility score", event_id=credibility.get("event_id"))
        except Exception as e:
            logger.error("Failed to store credibility score", error=str(e))
            raise

    async def process_brand_health_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Store brand health snapshot in ClickHouse."""
        try:
            execute_clickhouse_insert("brand_health_snapshots", [snapshot])
            logger.info(
                "Stored brand health snapshot",
                brand_id=snapshot.get("brand_id"),
                health_index=snapshot.get("health_index"),
            )
        except Exception as e:
            logger.error("Failed to store brand health snapshot", error=str(e))
            raise

    async def process_risk_event(self, risk: dict[str, Any]) -> None:
        """Store risk event in ClickHouse."""
        try:
            execute_clickhouse_insert("risk_events", [risk])
            logger.warning(
                "Stored risk event",
                risk_id=risk.get("risk_id"),
                brand_id=risk.get("brand_id"),
                severity=risk.get("severity"),
            )
        except Exception as e:
            logger.error("Failed to store risk event", error=str(e))
            raise

    async def process_attribution_record(self, attribution: dict[str, Any]) -> None:
        """Store attribution record in ClickHouse."""
        try:
            execute_clickhouse_insert("attribution_records", [attribution])
            logger.info(
                "Stored attribution record",
                brand_id=attribution.get("brand_id"),
                cause_type=attribution.get("cause_type"),
            )
        except Exception as e:
            logger.error("Failed to store attribution record", error=str(e))
            raise

    async def process_feature_contributions(
        self, contributions: list[dict[str, Any]]
    ) -> None:
        """Store feature contributions (SHAP values) in ClickHouse."""
        try:
            if contributions:
                execute_clickhouse_insert("feature_contributions", contributions)
                logger.debug(
                    "Stored feature contributions",
                    count=len(contributions),
                    event_id=contributions[0].get("event_id"),
                )
        except Exception as e:
            logger.error("Failed to store feature contributions", error=str(e))
            raise

    async def process_conversion_event(self, conversion: dict[str, Any]) -> None:
        """Store conversion event in ClickHouse.
        
        Args:
            conversion: Conversion event data including conversion_id, brand_id, 
                       event_id, platform, conversion_type, conversion_value, etc.
        """
        try:
            execute_clickhouse_insert("conversion_events", [conversion])
            logger.info(
                "Stored conversion event",
                conversion_id=conversion.get("conversion_id"),
                brand_id=conversion.get("brand_id"),
                value=conversion.get("conversion_value"),
            )
        except Exception as e:
            logger.error("Failed to store conversion event", error=str(e))
            raise


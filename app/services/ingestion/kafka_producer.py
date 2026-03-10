"""Kafka producer for signal events."""

import json
from typing import Any, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_producer: Optional[AIOKafkaProducer] = None


async def get_kafka_producer() -> AIOKafkaProducer:
    """Get or create Kafka producer."""
    global _producer
    
    if _producer is None:
        logger.info("Creating Kafka producer", servers=settings.kafka_bootstrap_servers)
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            compression_type="gzip",
            acks="all",
            retries=3,
        )
        await _producer.start()
    
    return _producer


async def close_kafka_producer() -> None:
    """Close Kafka producer."""
    global _producer
    
    if _producer is not None:
        logger.info("Closing Kafka producer")
        await _producer.stop()
        _producer = None


async def publish_signal_event(event: dict[str, Any], key: Optional[str] = None) -> str:
    """Publish a signal event to Kafka.
    
    Args:
        event: Signal event data
        key: Optional partition key (defaults to event_id)
    
    Returns:
        Event ID
    """
    producer = await get_kafka_producer()
    
    # Ensure event has an ID
    if "event_id" not in event:
        event["event_id"] = str(uuid4())
    
    event_id = event["event_id"]
    partition_key = key or event_id
    
    try:
        await producer.send(
            settings.kafka_topic_signals,
            value=event,
            key=partition_key,
        )
        logger.debug("Published signal event", event_id=event_id, brand_id=event.get("brand_id"))
        return event_id
    except Exception as e:
        logger.error("Failed to publish signal event", event_id=event_id, error=str(e))
        raise


async def publish_prediction(prediction: dict[str, Any], key: Optional[str] = None) -> None:
    """Publish ML prediction to Kafka.
    
    Args:
        prediction: Prediction data
        key: Optional partition key
    """
    producer = await get_kafka_producer()
    
    partition_key = key or prediction.get("event_id", str(uuid4()))
    
    try:
        await producer.send(
            settings.kafka_topic_predictions,
            value=prediction,
            key=partition_key,
        )
        logger.debug("Published prediction", event_id=prediction.get("event_id"))
    except Exception as e:
        logger.error("Failed to publish prediction", error=str(e))
        raise

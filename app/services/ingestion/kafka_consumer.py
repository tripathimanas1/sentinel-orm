"""Kafka consumer for signal events."""

import asyncio
import json
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SignalConsumer:
    """Kafka consumer for signal events."""

    def __init__(
        self,
        topic: str,
        group_id: Optional[str] = None,
        handler: Optional[Callable[[dict[str, Any]], Any]] = None,
    ) -> None:
        """Initialize consumer.
        
        Args:
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            handler: Async function to handle each message
        """
        self.topic = topic
        self.group_id = group_id or settings.kafka_consumer_group
        self.handler = handler
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Start the consumer."""
        logger.info(
            "Starting Kafka consumer",
            topic=self.topic,
            group_id=self.group_id,
        )
        
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=settings.kafka_auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
        )
        
        await self.consumer.start()
        self._running = True

    async def stop(self) -> None:
        """Stop the consumer."""
        logger.info("Stopping Kafka consumer", topic=self.topic)
        self._running = False
        
        if self.consumer:
            await self.consumer.stop()

    async def consume(self) -> None:
        """Consume messages from Kafka."""
        if not self.consumer:
            raise RuntimeError("Consumer not started")
        
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                
                try:
                    event = msg.value
                    logger.debug(
                        "Received signal event",
                        event_id=event.get("event_id"),
                        brand_id=event.get("brand_id"),
                    )
                    
                    if self.handler:
                        await self.handler(event)
                
                except Exception as e:
                    logger.error(
                        "Error processing message",
                        error=str(e),
                        topic=msg.topic,
                        partition=msg.partition,
                        offset=msg.offset,
                    )
        
        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        except Exception as e:
            logger.error("Consumer error", error=str(e))
            raise

    async def run(self) -> None:
        """Run the consumer (start and consume)."""
        await self.start()
        try:
            await self.consume()
        finally:
            await self.stop()

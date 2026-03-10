"""Example script to ingest a signal event."""

import asyncio
from datetime import datetime
from uuid import uuid4

from app.services.ingestion.kafka_producer import publish_signal_event, get_kafka_producer, close_kafka_producer


async def main() -> None:
    """Example signal ingestion."""
    
    # Example signal event
    event = {
        "event_id": str(uuid4()),
        "brand_id": "brand-123",
        "source_id": "source-456",
        "source_type": "review",
        "platform": "google",
        "timestamp": datetime.utcnow(),
        "text": "This product is amazing! Best purchase I've made this year.",
        "language": "en",
        "author_id": "user-789",
        "author_name": "John Doe",
        "author_metadata": {
            "account_age_days": 365,
            "follower_count": 150,
            "following_count": 200,
            "post_count": 50,
            "verified": False,
        },
        "likes": 10,
        "shares": 2,
        "comments": 3,
        "views": 100,
        "raw_data": {},
    }
    
    # Publish event
    event_id = await publish_signal_event(event)
    print(f"Published signal event: {event_id}")
    
    # Close producer
    await close_kafka_producer()


if __name__ == "__main__":
    asyncio.run(main())

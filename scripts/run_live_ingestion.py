import asyncio
import sys
import signal
import random
from pathlib import Path
from datetime import datetime

# Force unbuffered output for immediate feedback
sys.stdout.reconfigure(line_buffering=True)
print("Initializing Sentinel Ingestion Engine...", flush=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import get_logger, setup_logging
from app.services.ingestion.scrapers import ScraperFactory
from app.services.ingestion.signal_processor import SignalProcessor
from app.db.clickhouse import get_clickhouse_client, close_clickhouse_client
from app.db.postgres import get_postgres_engine, close_postgres_engine
from app.db.redis import get_redis_client, close_redis_client

from app.services.ml.sentiment_model import SentimentModel
from app.services.ml.emotion_model import EmotionModel
from app.services.ml.credibility_model import CredibilityModel

print("Imports complete. Setting up logging...", flush=True)
logger = get_logger(__name__)

async def run_ingestion_cycle(brands: list, platforms: list, processor: SignalProcessor, models: dict):
    """Runs a single cycle of ingestion across all sources."""
    
    tasks = []
    
    for brand in brands:
        for platform in platforms:
            scraper = ScraperFactory.get_scraper(platform)
            # Create a coroutine for each scrape job
            tasks.append(process_scrape_job(scraper, brand, processor, models))
            
    # Run all scrape jobs in parallel
    await asyncio.gather(*tasks)

async def process_scrape_job(scraper, brand: str, processor: SignalProcessor, models: dict):
    try:
        # Fetch real-time signals from external APIs
        signals = await scraper.fetch_signals(query=brand, limit=5)
        
        count = 0
        conversion_count = 0
        for sig_data in signals:
            # Transform to internal event format used by SignalProcessor
            event = {
                "event_id": sig_data.get("source_id"), # In real app, hash this
                "brand_id": brand,
                "text": sig_data["text"],
                "source_id": sig_data["source_id"],
                "source_type": sig_data["source_type"],
                "platform": sig_data["platform"],
                "timestamp": datetime.fromisoformat(sig_data["timestamp"]),
                "likes": sig_data.get("likes", 0),
                "shares": sig_data.get("shares", 0),
                "comments": sig_data.get("comments", 0),
                "views": sig_data.get("views", 0),
                "author_metadata": sig_data.get("author_metadata", {})
            }
            
            # 1. Store Raw Signal
            await processor.process_signal(event)
            
            # 2. Run ML Models
            # We need to ensure the event has all keys expected by feature extractor
            # The models' predict methods handle feature extraction internally via FeatureExtractor
            try:
                sentiment = models['sentiment'].predict(event)
                await processor.process_sentiment_score(sentiment)
                
                emotion = models['emotion'].predict(event)
                await processor.process_emotion_vector(emotion)
                
                credibility = models['credibility'].predict(event)
                await processor.process_credibility_score(credibility)
                
                # 3. Generate Conversion Events (2-5% conversion rate)
                # Only generate conversions for positive sentiment signals
                if sentiment.get('sentiment_score', 0) > 0.3 and random.random() < 0.04:
                    import uuid
                    conversion_value = random.uniform(50, 500)  # Conversion value in dollars
                    conversion_event = {
                        "conversion_id": str(uuid.uuid4()),
                        "brand_id": brand,
                        "event_id": event["event_id"],
                        "platform": event["platform"],
                        "conversion_type": random.choice(["click", "signup", "purchase", "inquiry"]),
                        "conversion_value": conversion_value,
                        "timestamp": event["timestamp"],
                        "attribution_confidence": random.uniform(0.6, 0.95)
                    }
                    await processor.process_conversion_event(conversion_event)
                    conversion_count += 1
                    
            except Exception as ml_err:
                logger.error(f"ML Processing failed for event {event.get('event_id')}: {ml_err}")

            count += 1
            
        logger.info(f"Successfully ingested {count} signals and {conversion_count} conversions for {brand} from {scraper.platform}")
        
    except Exception as e:
        logger.error(f"Failed to ingest from {scraper.platform} for {brand}: {e}")
    finally:
        await scraper.close()

async def main():
    setup_logging("INFO")
    logger.info("Starting Sentinel Real-Time Ingestion Engine...")
    
    # Initialize Infrastructure
    await get_postgres_engine()
    await get_clickhouse_client()
    await get_redis_client()
    
    processor = SignalProcessor()

    # Initialize ML Models
    logger.info("Loading ML Models...")
    models = {
        'sentiment': SentimentModel(),
        'emotion': EmotionModel(),
        'credibility': CredibilityModel()
    }
    
    # Configuration
    TARGET_BRANDS = ["squareyards"]
    TARGET_PLATFORMS = ["twitter", "reddit", "instagram", "quora"]
    POLL_INTERVAL = 10 # Seconds (Fast for demo)
    
    logger.info(f"Targeting Brands: {TARGET_BRANDS}")
    logger.info(f"Monitoring Sources: {TARGET_PLATFORMS}")
    
    running = True
    
    def handle_exit(sig, frame):
        nonlocal running
        print("\nGeneric shutdown signal received...")
        running = False
        
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        while running:
            start_time = datetime.now()
            logger.info(">>> Starting Ingestion Cycle")
            
            await run_ingestion_cycle(TARGET_BRANDS, TARGET_PLATFORMS, processor, models)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"<<< Cycle Complete in {elapsed:.2f}s. Sleeping for {POLL_INTERVAL}s...")
            
            # Interruptible sleep
            for _ in range(int(POLL_INTERVAL)):
                if not running: break
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Fatal Ingestion Error: {e}")
    finally:
        logger.info("Shutting down connections...")
        await close_postgres_engine()
        await close_clickhouse_client()
        await close_redis_client()
        logger.info("Ingestion Engine Stopped.")

if __name__ == "__main__":
    asyncio.run(main())

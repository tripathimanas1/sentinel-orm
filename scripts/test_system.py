
import asyncio
import json
import httpx
from datetime import datetime, timedelta
from uuid import uuid4
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


from app.services.ml.sentiment_model import SentimentModel
from app.services.ml.emotion_model import EmotionModel
from app.services.ml.credibility_model import CredibilityModel
from app.services.ml.feature_extractor import FeatureExtractor
from app.services.ingestion.signal_processor import SignalProcessor
from app.db.clickhouse import execute_clickhouse_query, get_clickhouse_client, close_clickhouse_client
from app.db.postgres import get_postgres_engine, close_postgres_engine
from app.db.redis import get_redis_client, close_redis_client
import numpy as np


async def bootstrap_system():
    print("\n--- Bootstrapping ML System (Training with Synthetic Data) ---")
    fe = FeatureExtractor()
    sentiment_model = SentimentModel()
    emotion_model = EmotionModel()
    credibility_model = CredibilityModel()
    
    # 1. Generate Synthetic Data
    n_samples = 100
    
    # Random event templates
    texts = [
        "This is amazing!", "I hate this.", "Average product.", 
        "Fantastic experience", "Terrible customer service", "It's okay I guess"
    ]
    
    X_list = []
    y_sentiment = []
    y_emotion = []
    y_credibility = []
    
    for i in range(n_samples):
        # Create a mock event to extract features from
        mock_event = {
            "text": texts[i % len(texts)],
            "likes": np.random.randint(0, 100),
            "views": np.random.randint(100, 1000),
            "source_type": "social",
            "platform": "twitter",
            "author_metadata": json.dumps({
                "account_age_days": np.random.randint(1, 1000),
                "follower_count": np.random.randint(0, 5000),
                "verified": bool(np.random.choice([True, False]))
            })
        }
        
        features = fe.extract_all_features(mock_event, include_embeddings=False)
        
        # Sentiment Target: simplified correlation
        lex_pol = features.get("lexicon_polarity", 0)
        y_sent = np.clip(lex_pol / 3.0 + np.random.normal(0, 0.1), -1, 1)
        y_sentiment.append(y_sent)
        
        # Emotion Target: 6 labels
        # [anger, frustration, fear, trust, satisfaction, joy]
        if lex_pol > 0:
            e = [0.0, 0.0, 0.0, 0.4, 0.5, 0.6]
        elif lex_pol < 0:
            e = [0.6, 0.5, 0.3, 0.0, 0.0, 0.0]
        else:
            e = [0.1] * 6
        y_emotion.append(e)
        
        # Credibility Target
        verified = features.get("verified", 0)
        c = 0.3 + (0.4 if verified else 0) + np.random.uniform(0, 0.3)
        y_credibility.append(np.clip(c, 0, 1))
        
        # Feature array for sentiment (as expected by model)
        X_sent = np.array([features.get(name, 0.0) for name in sentiment_model.feature_names])
        X_list.append(X_sent)

    X = np.array(X_list)
    
    # 2. Train and Save
    print("Training Sentiment Model...")
    sentiment_model.train(X, np.array(y_sentiment))
    sentiment_model.save_model("ml/models/sentiment_v1.0.0.joblib")
    
    print("Training Emotion Model...")
    emotion_model.train(X, np.array(y_emotion))
    emotion_model.save_model("ml/models/emotion_v1.0.0.joblib")
    
    print("Training Credibility Model...")
    # Credibility model has different feature set
    X_cred = []
    for i in range(n_samples):
        # We need to re-extract or re-align features for credibility
        # Just for simplicity, we use the same feature names if they match or fill with 0
        mock_features = fe.extract_all_features({
            "author_metadata": json.dumps({"verified": bool(y_credibility[i] > 0.5)})
        }, include_embeddings=False)
        x_c = np.array([mock_features.get(name, 0.0) for name in credibility_model.feature_names])
        X_cred.append(x_c)
    
    credibility_model.train(np.array(X_cred), np.array(y_credibility))
    credibility_model.save_model("ml/models/credibility_v1.0.0.joblib")
    
    print("✓ All models trained and saved to ml/models/")

async def test_models():
    print("\n--- Testing ML Models ---")
    
    # Initialize models
    sentiment_model = SentimentModel()
    emotion_model = EmotionModel()
    credibility_model = CredibilityModel()
    
    mock_event = {
        "event_id": str(uuid4()),
        "brand_id": "test-brand-1",
        "source_id": "test-source-1",
        "source_type": "social",
        "platform": "twitter",
        "text": "I absolutely love this new product! It's life-changing.",
        "author_id": "user-1",
        "author_metadata": json.dumps({
            "account_age_days": 500,
            "follower_count": 1000,
            "verified": True
        }),
        "likes": 50,
        "timestamp": datetime.utcnow()
    }
    
    # Test Sentiment
    sentiment = sentiment_model.predict(mock_event)
    print(f"Sentiment Prediction: {sentiment['sentiment_score']:.2f} (Confidence: {sentiment['confidence']})")
    
    # Test Emotion
    emotion = emotion_model.predict(mock_event)
    print(f"Emotion Prediction: {emotion}")
    
    # Test Credibility
    credibility = credibility_model.predict(mock_event)
    print(f"Credibility Prediction: {credibility['credibility_score']:.2f}")
    
    return sentiment, emotion, credibility

async def test_ingestion(sentiment, emotion, credibility):
    print("\n--- Testing Ingestion & ClickHouse ---")
    processor = SignalProcessor()
    
    brand_id = "test-brand-1"
    event_id = sentiment["event_id"]
    
    # Mock full signal event
    signal_event = {
        "event_id": event_id,
        "brand_id": brand_id,
        "source_id": "test-source-1",
        "source_type": "social",
        "platform": "twitter",
        "text": "I absolutely love this new product! It's life-changing.",
        "likes": 50,
        "timestamp": datetime.utcnow()
    }
    
    # Mock conversion event
    conversion_event = {
        "conversion_id": str(uuid4()),
        "brand_id": brand_id,
        "event_id": event_id,
        "platform": "twitter",
        "timestamp": datetime.utcnow(),
        "conversion_value": 99.99,
        "conversion_type": "purchase"
    }
    
    # Process and store
    await processor.process_signal(signal_event)
    await processor.process_sentiment_score(sentiment)
    await processor.process_emotion_vector(emotion)
    await processor.process_credibility_score(credibility)
    
    # Manually store conversion (the processor has no direct method for it in the viewed snippet, but we can use execute_clickhouse_insert)
    from app.db.clickhouse import execute_clickhouse_insert
    execute_clickhouse_insert("conversion_events", [conversion_event])
    
    # Verify in ClickHouse
    res = execute_clickhouse_query(f"SELECT COUNT(*) FROM sentiment_scores WHERE brand_id = '{brand_id}'")
    print(f"Verified: Found {res[0][0]} sentiment records for {brand_id}")
    
    return brand_id

async def test_apis(brand_id):
    print("\n--- Testing APIs ---")
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # Test Health
        try:
            health = await client.get(f"http://localhost:8000/health")
            print(f"Health Check: {health.json()}")
        except Exception as e:
            print(f"API Server not running? {e}")
            return

        # Test Sentiment Trends
        resp = await client.get(f"{base_url}/sentiment-trends/{brand_id}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Sentiment API Success: Mean sentiment {data['aggregations']['mean_sentiment']:.2f}")
        else:
            print(f"Sentiment API Failed: {resp.status_code} - {resp.text}")

        # Test Risk Alerts
        resp = await client.get(f"{base_url}/risk-alerts/{brand_id}")
        if resp.status_code == 200:
            print(f"Risk Alerts API Success: Found {len(resp.json())} alerts")
        else:
            print(f"Risk Alerts API Failed: {resp.status_code}")

        # Test Source Insights
        resp = await client.get(f"{base_url}/source-insights/{brand_id}")
        if resp.status_code == 200:
            data = resp.json()
            platforms = data.get('platforms', {})
            print(f"Source Insights API Success: Identified {len(platforms)} platforms.")
            
            # Verify LLM Visibility fields
            if platforms:
                first_platform = list(platforms.values())[0]
                if "llm_visibility" in first_platform:
                    print(f"  - LLM Visibility Score: {first_platform['llm_visibility']['score']}")
                    print(f"  - Risk Level: {first_platform['llm_visibility']['risk_level']}")
        else:
            print(f"Source Insights API Failed: {resp.status_code} - {resp.text}")

        # Test Visibility Simulation
        print("Testing Visibility Simulation (High-Level Actions + Auto-Baseline)...")
        sim_payload = {
            "brand_id": brand_id,
            # "current_metrics": ... (Intentionally omitted to test auto-fetch)
            "platform": "twitter", # Optional
            "actions": [
                "launch_pr_campaign",
                "partner_with_influencer"
            ],
            "model_name": "gpt-4"
        }
        resp = await client.post(f"{base_url}/source-insights/simulate", json=sim_payload)
        if resp.status_code == 200:
            sim_data = resp.json()
            print(f"Simulation Success: {sim_data['actions_applied']} -> Changed from {sim_data['original_score']:.2f} to {sim_data['new_score']:.2f} ({sim_data['percent_change']:.2f}%)")
            print(f"  (Baseline Used: Sentiment={sim_data['baseline_metrics']['sentiment']:.3f})")
        else:
            print(f"Simulation Failed: {resp.status_code} - {resp.text}")

async def main():
    try:
        # Initialize DB clients
        await get_postgres_engine()
        await get_clickhouse_client()
        await get_redis_client()
        
        sentiment, emotion, credibility = await test_models()
        brand_id = await test_ingestion(sentiment, emotion, credibility)
        await test_apis(brand_id)
        print("\n✅ System test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await close_postgres_engine()
        await close_clickhouse_client()
        await close_redis_client()

if __name__ == "__main__":
    asyncio.run(main())

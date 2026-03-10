from clickhouse_driver import Client
import os
from dotenv import load_dotenv

def truncate_tables():
    load_dotenv()
    
    user = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "sanam2021")
    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", 9000))
    database = os.getenv("CLICKHOUSE_DB", "sentinel_events")
    
    print(f"Connecting to {host}:{port} ({database}) as {user}")
    
    tables = [
        "signal_events",
        "sentiment_scores",
        "emotion_vectors",
        "credibility_scores",
        "brand_health_snapshots",
        "risk_events",
        "attribution_records",
        "feature_contributions",
        "conversion_events"
    ]
    
    try:
        client = Client(host=host, port=port, user=user, password=password, database=database)
        
        for table in tables:
            print(f"Truncating table: {table}...")
            client.execute(f"TRUNCATE TABLE {table}")
            print(f"Done: {table}")
            
        print("\nAll tables truncated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    truncate_tables()

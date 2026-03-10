"""Initialize ClickHouse database and tables."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clickhouse_driver import Client
from app.config import get_settings
from migrations.clickhouse.schemas import ALL_TABLES

settings = get_settings()


def init_clickhouse() -> None:
    """Initialize ClickHouse database and create all tables."""
    print(f"Connecting to ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    # Ensure password is a string (even if empty) to avoid AttributeError in clickhouse-driver
    conn_password = settings.clickhouse_password if settings.clickhouse_password is not None else ""
    print(f"User: '{settings.clickhouse_user}', Password length: {len(conn_password)}")

    client = Client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=conn_password,
        connect_timeout=10,
    )
    
    # Create database if not exists
    try:
        print(f"Creating database: {settings.clickhouse_db}")
        client.execute(f"CREATE DATABASE IF NOT EXISTS {settings.clickhouse_db}")
    except Exception as e:
        print(f"Failed to create database: {e}")
        # If it's an auth error, it might be because the driver doesn't like the empty string behavior
        # But we've ensured it's a string now.
        raise

    # Switch to database
    client = Client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        database=settings.clickhouse_db,
        user=settings.clickhouse_user,
        password=conn_password,
        connect_timeout=10,
    )
    
    # Create all tables
    for i, table_sql in enumerate(ALL_TABLES, 1):
        print(f"Executing statement {i}/{len(ALL_TABLES)}...")
        try:
            client.execute(table_sql)
        except Exception as e:
            print(f"Error executing statement {i}: {e}")
    
    print("✓ ClickHouse initialization complete!")


if __name__ == "__main__":
    init_clickhouse()

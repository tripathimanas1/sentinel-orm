"""ClickHouse database connection."""

from typing import Any, Optional

from clickhouse_driver import Client

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: Optional[Client] = None


async def get_clickhouse_client() -> Client:
    """Get or create ClickHouse client."""
    global _client
    
    if _client is None:
        logger.info(
            "Creating ClickHouse client",
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
        )
        _client = Client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
    
    return _client


async def close_clickhouse_client() -> None:
    """Close ClickHouse client."""
    global _client
    
    if _client is not None:
        logger.info("Closing ClickHouse client")
        _client.disconnect()
        _client = None


def execute_clickhouse_query(query: str, params: Optional[dict[str, Any]] = None) -> Any:
    """Execute a ClickHouse query."""
    client = _client
    if client is None:
        raise RuntimeError("ClickHouse client not initialized")
    
    return client.execute(query, params or {})


def execute_clickhouse_insert(
    table: str, data: list[dict[str, Any]], columns: Optional[list[str]] = None
) -> None:
    """Insert data into ClickHouse table."""
    client = _client
    if client is None:
        raise RuntimeError("ClickHouse client not initialized")
    
    if not data:
        return
    
    if columns is None:
        columns = list(data[0].keys())
    
    values = [[row.get(col) for col in columns] for row in data]
    client.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES", values)

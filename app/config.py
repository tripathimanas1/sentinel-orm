"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="sentinel-orm", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # PostgreSQL
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="sentinel_orm", alias="POSTGRES_DB")
    postgres_user: str = Field(default="sentinel", alias="POSTGRES_USER")
    postgres_password: str = Field(default="sentinel_password", alias="POSTGRES_PASSWORD")
    postgres_pool_size: int = Field(default=20, alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=10, alias="POSTGRES_MAX_OVERFLOW")

    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ClickHouse
    clickhouse_host: str = Field(default="localhost", alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(default=9000, alias="CLICKHOUSE_PORT")
    clickhouse_db: str = Field(default="sentinel_events", alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field(default="default", alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field(default="", alias="CLICKHOUSE_PASSWORD")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Kafka/Redpanda
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_signals: str = Field(default="sentinel.signals", alias="KAFKA_TOPIC_SIGNALS")
    kafka_topic_predictions: str = Field(
        default="sentinel.predictions", alias="KAFKA_TOPIC_PREDICTIONS"
    )
    kafka_consumer_group: str = Field(
        default="sentinel-consumers", alias="KAFKA_CONSUMER_GROUP"
    )
    kafka_auto_offset_reset: str = Field(default="earliest", alias="KAFKA_AUTO_OFFSET_RESET")

    # ML Models
    model_path: str = Field(default="./ml/models", alias="MODEL_PATH")
    sentiment_model_version: str = Field(default="v1.0.0", alias="SENTIMENT_MODEL_VERSION")
    emotion_model_version: str = Field(default="v1.0.0", alias="EMOTION_MODEL_VERSION")
    credibility_model_version: str = Field(default="v1.0.0", alias="CREDIBILITY_MODEL_VERSION")
    enable_shap_explanations: bool = Field(default=True, alias="ENABLE_SHAP_EXPLANATIONS")

    # Feature Engineering
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    max_text_length: int = Field(default=512, alias="MAX_TEXT_LENGTH")

    # Brand Health
    health_index_window_hours: int = Field(default=24, alias="HEALTH_INDEX_WINDOW_HOURS")
    health_index_update_interval_minutes: int = Field(
        default=5, alias="HEALTH_INDEX_UPDATE_INTERVAL_MINUTES"
    )
    recency_decay_hours: int = Field(default=72, alias="RECENCY_DECAY_HOURS")

    # Risk Detection
    anomaly_detection_window_hours: int = Field(
        default=168, alias="ANOMALY_DETECTION_WINDOW_HOURS"
    )
    risk_detection_interval_minutes: int = Field(
        default=10, alias="RISK_DETECTION_INTERVAL_MINUTES"
    )
    min_confidence_threshold: float = Field(default=0.7, alias="MIN_CONFIDENCE_THRESHOLD")

    # Attribution
    attribution_window_hours: int = Field(default=48, alias="ATTRIBUTION_WINDOW_HOURS")
    max_attribution_causes: int = Field(default=5, alias="MAX_ATTRIBUTION_CAUSES")

    # Cache
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    cache_brand_health_ttl: int = Field(default=300, alias="CACHE_BRAND_HEALTH_TTL")
    cache_sentiment_trends_ttl: int = Field(default=600, alias="CACHE_SENTIMENT_TRENDS_TTL")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, alias="RATE_LIMIT_BURST")

    # GDPR
    data_retention_days: int = Field(default=730, alias="DATA_RETENTION_DAYS")
    pii_masking_enabled: bool = Field(default=True, alias="PII_MASKING_ENABLED")
    audit_log_retention_days: int = Field(default=2555, alias="AUDIT_LOG_RETENTION_DAYS")

    # Monitoring
    prometheus_port: int = Field(default=9090, alias="PROMETHEUS_PORT")
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    jaeger_agent_host: str = Field(default="localhost", alias="JAEGER_AGENT_HOST")
    jaeger_agent_port: int = Field(default=6831, alias="JAEGER_AGENT_PORT")

    # Social Media APIs
    reddit_client_id: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(default="SentinelORM/1.0", alias="REDDIT_USER_AGENT")
    twitter_bearer_token: Optional[str] = Field(default=None, alias="TWITTER_BEARER_TOKEN")
    rapidapi_key: Optional[str] = Field(default=None, alias="RAPIDAPI_KEY")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""ClickHouse schema initialization scripts."""

# Signal Events Table
CREATE_SIGNAL_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS signal_events (
    event_id String,
    brand_id String,
    source_id String,
    source_type LowCardinality(String),
    platform LowCardinality(String),
    timestamp DateTime64(3),
    ingested_at DateTime64(3) DEFAULT now64(3),
    
    -- Content
    text String,
    language LowCardinality(String),
    
    -- Author metadata
    author_id String,
    author_name String,
    author_metadata String,
    
    -- Engagement
    likes UInt32 DEFAULT 0,
    shares UInt32 DEFAULT 0,
    comments UInt32 DEFAULT 0,
    views UInt32 DEFAULT 0,
    
    -- Raw data
    raw_data String,
    
    -- Partitioning
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, source_type, timestamp)
TTL date + INTERVAL 2 YEAR;
"""

# Signal Events Indexes
CREATE_SIGNAL_EVENTS_INDEX_1 = """
ALTER TABLE signal_events ADD INDEX IF NOT EXISTS idx_event_id event_id TYPE bloom_filter(0.01) GRANULARITY 1;
"""

CREATE_SIGNAL_EVENTS_INDEX_2 = """
ALTER TABLE signal_events ADD INDEX IF NOT EXISTS idx_author author_id TYPE bloom_filter(0.01) GRANULARITY 1;
"""

# Sentiment Scores Table
CREATE_SENTIMENT_SCORES_TABLE = """
CREATE TABLE IF NOT EXISTS sentiment_scores (
    event_id String,
    brand_id String,
    timestamp DateTime64(3),
    
    -- Sentiment
    sentiment_score Float32,
    confidence Float32,
    
    -- Model metadata
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, timestamp);
"""

# Emotion Vectors Table
CREATE_EMOTION_VECTORS_TABLE = """
CREATE TABLE IF NOT EXISTS emotion_vectors (
    event_id String,
    brand_id String,
    timestamp DateTime64(3),
    
    -- Emotion scores [0, 1]
    anger Float32 DEFAULT 0,
    frustration Float32 DEFAULT 0,
    fear Float32 DEFAULT 0,
    trust Float32 DEFAULT 0,
    satisfaction Float32 DEFAULT 0,
    joy Float32 DEFAULT 0,
    
    -- Model metadata
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, timestamp);
"""

# Credibility Scores Table
CREATE_CREDIBILITY_SCORES_TABLE = """
CREATE TABLE IF NOT EXISTS credibility_scores (
    event_id String,
    brand_id String,
    source_id String,
    author_id String,
    timestamp DateTime64(3),
    
    -- Credibility
    credibility_score Float32,
    confidence Float32,
    
    -- Features used
    account_age_days UInt32,
    historical_post_count UInt32,
    avg_engagement Float32,
    verified Boolean,
    
    -- Model metadata
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, author_id, timestamp);
"""

# Brand Health Snapshots Table
CREATE_BRAND_HEALTH_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS brand_health_snapshots (
    snapshot_id String,
    brand_id String,
    timestamp DateTime64(3),
    
    -- Brand Health Index
    health_index Float32,
    
    -- Components
    weighted_sentiment Float32,
    volume_score Float32,
    diversity_score Float32,
    recency_score Float32,
    
    -- Metadata
    signal_count UInt32,
    time_window_hours UInt16,
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, timestamp);
"""

# Risk Events Table
CREATE_RISK_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS risk_events (
    risk_id String,
    brand_id String,
    detected_at DateTime64(3),
    
    -- Risk classification
    risk_type LowCardinality(String),
    severity LowCardinality(String),
    confidence Float32,
    
    -- Risk metrics
    risk_score Float32,
    velocity Float32,
    amplification_risk Float32,
    business_impact Float32,
    
    -- Context
    trigger_event_ids Array(String),
    affected_sources Array(String),
    description String,
    
    -- Status
    status LowCardinality(String) DEFAULT 'active',
    resolved_at DateTime64(3),
    
    -- Model metadata
    model_version String,
    
    date Date MATERIALIZED toDate(detected_at)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, detected_at);
"""

# Attribution Records Table
CREATE_ATTRIBUTION_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS attribution_records (
    attribution_id String,
    brand_id String,
    timestamp DateTime64(3),
    
    -- What changed
    metric_type LowCardinality(String),
    change_magnitude Float32,
    change_direction Int8,
    
    -- Probable causes (ranked)
    cause_type LowCardinality(String),
    cause_identifier String,
    cause_timestamp DateTime64(3),
    confidence Float32,
    rank UInt8,
    
    -- Supporting evidence
    correlated_event_ids Array(String),
    evidence_summary String,
    
    -- Model metadata
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, timestamp, rank);
"""

# Feature Contributions Table
CREATE_FEATURE_CONTRIBUTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS feature_contributions (
    event_id String,
    brand_id String,
    model_type LowCardinality(String),
    timestamp DateTime64(3),
    
    -- SHAP values
    feature_name String,
    feature_value Float32,
    shap_value Float32,
    
    -- Model metadata
    model_version String,
    computed_at DateTime64(3) DEFAULT now64(3),
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, model_type, event_id, feature_name);
"""

# Conversion Events Table
CREATE_CONVERSION_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS conversion_events (
    conversion_id String,
    brand_id String,
    event_id String,
    platform LowCardinality(String),
    timestamp DateTime64(3),
    conversion_value Float32 DEFAULT 0,
    conversion_type String,
    
    date Date MATERIALIZED toDate(timestamp)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (brand_id, platform, timestamp);
"""

# All table creation statements
ALL_TABLES = [
    CREATE_SIGNAL_EVENTS_TABLE,
    CREATE_SIGNAL_EVENTS_INDEX_1,
    CREATE_SIGNAL_EVENTS_INDEX_2,
    CREATE_SENTIMENT_SCORES_TABLE,
    CREATE_EMOTION_VECTORS_TABLE,
    CREATE_CREDIBILITY_SCORES_TABLE,
    CREATE_BRAND_HEALTH_SNAPSHOTS_TABLE,
    CREATE_RISK_EVENTS_TABLE,
    CREATE_ATTRIBUTION_RECORDS_TABLE,
    CREATE_FEATURE_CONTRIBUTIONS_TABLE,
    CREATE_CONVERSION_EVENTS_TABLE,
]

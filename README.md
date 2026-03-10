# Sentinel ORM

**AI-powered Online Reputation Intelligence & Early Warning System**

Sentinel ORM is a production-grade system that solves critical failures of traditional ORM tools: fragmentation, reactivity, lack of attribution, fake reviews, opaque metrics, alert fatigue, and lack of governance.

## Features

- 🔍 **Unified Signal Ingestion** - Reviews, social mentions, support tickets, influencer posts, news
- 🧠 **ML-Powered Intelligence** - Sentiment, emotion, credibility scoring with explainability
- 📊 **Brand Health Index** - Transparent, auditable reputation metric
- ⚠️ **Early Risk Detection** - Detect threats before they spread
- 🎯 **Root Cause Attribution** - Understand why reputation changed
- 🚨 **Smart Alerting** - Prioritized, confidence-scored alerts
- 📝 **Full Auditability** - GDPR-compliant with complete governance

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Databases**: PostgreSQL (entities), ClickHouse (events), Redis (cache)
- **Streaming**: Kafka/Redpanda
- **ML**: scikit-learn, XGBoost, PyTorch, sentence-transformers
- **Explainability**: SHAP

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd sentinel-orm

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start infrastructure services
docker-compose up -d

# Run migrations
poetry run alembic upgrade head

# Start the API server
poetry run uvicorn app.main:app --reload
```

### Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy app/
```

## Architecture

```
Signal Sources → Kafka → Ingestion Service → ClickHouse (Events)
                                          → PostgreSQL (Entities)
                                          ↓
                                    ML Pipeline
                                          ↓
                            (Sentiment, Emotion, Credibility)
                                          ↓
                                  Brand Health Engine
                                          ↓
                              Risk Detection & Attribution
                                          ↓
                                    FastAPI Layer
```

## API Endpoints

- `GET /api/v1/brand-health/{brand_id}` - Brand health metrics
- `GET /api/v1/sentiment-trends/{brand_id}` - Sentiment trends over time
- `GET /api/v1/risk-alerts/{brand_id}` - Active risk alerts
- `GET /api/v1/root-causes/{brand_id}/{metric_type}` - Attribution analysis
- `GET /api/v1/signal-explanations/{event_id}` - ML model explanations
- `GET /api/v1/action-priorities/{brand_id}` - Prioritized action items

## ML Models

1. **Sentiment Regression** - Continuous sentiment scoring [-1, 1]
2. **Emotion Classification** - Multi-label emotion detection
3. **Credibility Scoring** - Source trustworthiness evaluation
4. **Brand Health Index** - Composite reputation metric
5. **Anomaly Detection** - Early risk identification
6. **Attribution Engine** - Root cause analysis

All models include SHAP-based explainability.

## Database Schema

### PostgreSQL
- Brands, Sources, Users, Action Logs

### ClickHouse
- Signal Events, Sentiment Scores, Emotion Vectors
- Credibility Scores, Brand Health Snapshots
- Risk Events, Attribution Records, Feature Contributions

## Configuration

See `.env.example` for all configuration options.

## License

[Your License]

## Contributing

[Contributing guidelines]

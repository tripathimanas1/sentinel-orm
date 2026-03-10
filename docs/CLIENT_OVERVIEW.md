# Client Presentation Guide: AI Online Reputation Intelligence System (SENTINEL)

This document provides a comprehensive walkthrough for presenting the **Sentinel** system. It details the technical architecture, data lifecycle, and the AI-driven insights that make Sentinel a world-class reputation intelligence platform.

---

## 1. The Core Vision: Moving Beyond Vanity Metrics
**The Problem:** Traditional ORM (Online Reputation Management) tools are reactive. They count mentions but fail to understand the **context**, **credibility** of the speaker, and the **velocity** of risk.
**The Solution:** Sentinel is a **Predictive Early Warning System**. It weights every signal by author credibility and platform influence, allowing brands to see a crisis *before* it peaks.

---

## 2. Technical Infrastructure (The Multi-Layered Engine)

### A. The Storage Strategy (Truth, Velocity, & Speed)
Sentinel utilizes a specialized database trio to ensure data integrity and sub-second performance at scale:

*   **PostgreSQL (The Source of Truth):**
    *   **Role:** Manages relational "Metadata"—Users, Brands, Sources, and System Governance.
    *   **Governance:** Every analyst action is logged in `action_logs` for a full audit trail (GDPR/Compliance ready).
    *   **Risk Management:** Stores the final "Risk Alerts" triggered by the AI engine.

*   **ClickHouse (The Analytical Powerhouse):**
    *   **Role:** Handles Big Data ingestion and sub-second OLAP queries.
    *   **Scale:** Optimized for storing millions of "Signal Events," sentiment scores, and emotion vectors.
    *   **Explainability:** Stores SHAP attribution records, allowing us to explain *why* the AI made a specific prediction.

*   **Redis (The Instant Acceleration Layer):**
    *   **Role:** Caches the complex "Brand Health" snapshots.
    *   **Impact:** Ensures the dashboard feels instantaneous by retrieving pre-computed health scores without re-querying the raw data.

### B. The AI Brain (Multi-Model Intelligence)
Sentinel doesn't rely on a single model; it uses an ensemble of XGBoost-powered engines:

1.  **Sentiment Engine (Regression):**
    *   Predicts a continuous score from **-1.0 (Critical Negative)** to **1.0 (Heroic Positive)**.
    *   Analyzes 25+ features including text complexity, lexicon polarity, and engagement velocity.
2.  **Emotion Engine (Multi-Label):**
    *   Detects underlying triggers: **Anger, Frustration, Fear, Trust, Satisfaction, and Joy**.
    *   Identifies the "Emotional Pulse" of a conversation, not just the polarity.
3.  **Credibility Model (Impact Scoring):**
    *   Automatically discounts "trolls" or "bot" behavior.
    *   Amplifies signals from verified, high-impact, or authoritative accounts based on account age, follower/following ratios, and historical engagement.

---

## 3. The Data Lifecycle (From Signal to Alert)

Walk the client through the "Signal Journey" to demonstrate technical robustness:

1.  **Ingestion:** Signals from Social Media, News, and Reviews flow through **Kafka/Redpanda**.
2.  **Enrichment:** The `SignalProcessor` extracts 25+ features (engagement rate, account metadata, text stats).
3.  **Analysis (Parallel Inference):**
    *   The **Credibility Model** decides "Who is talking?"
    *   The **Sentiment Model** decides "What are they saying?"
    *   The **Emotion Model** decides "How do they feel?"
4.  **Aggregation:** All scores are synced to **ClickHouse** for real-time trend analysis.
5.  **Intelligence Layer:** The **Brand Health Engine** computes a composite score (0-100) based on weighted sentiment, volume, diversity, and recency.
6.  **Action:** If sentiment drops below a threshold or an "Anger Spike" is detected, the **Risk Engine** persists a Critical Alert to **PostgreSQL** and notifies the analyst.

---

## 4. API & Integration (API-First Architecture)

Sentinel is designed to power any interface: Web Dashboards, Mobile Apps, or Slack Bots.

*   **`GET /api/v1/brand-health/{brand_id}`:** Returns the core Health Index.
    *   *Diversity Score:* Measures platform resilience (Social vs. News vs. Reviews).
    *   *Recency Score:* Uses exponential decay to prioritize today's news over yesterday's.
*   **`GET /api/v1/risk-alerts`:** A prioritized queue of "Signals that Matter."
*   **`GET /api/v1/sentiment/trends`:** Visualizes the brand's trajectory over time.
*   **`GET /api/v1/source-insights`:** Identifies which platform is driving the conversation.

---

## 5. Key Presentation Talking Points

*   **Explainable AI (XAI):** We can show the client exactly which words or metrics triggered a "Critical" alert. This builds trust in the AI.
*   **Delayed Ground Truth:** Our models "learn" as engagement grows. A post that has 10 shares now vs. 10,000 shares in two hours will be automatically re-scored.
*   **High Performance:** Sub-second response times even with millions of signals in the database.

---

## 6. Future Roadmap
*   **Patient Zero Detection:** Identifying the exact account that started a misinformation campaign.
*   **Predictive Forecasting:** Predicting next week's sentiment based on current emotional triggers.
*   **Graph Propagation:** Visualizing how a signal "infects" different clusters of accounts.

---
*Sentinel: Precision Intelligence for Modern Brands.*

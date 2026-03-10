# SENTINEL: MOAT & SIMULATION API EXPLANATION

## 1. Source Insights API (The "Where & Why")

### **The MOAT Perspective**
In the age of AI and algorithmic feeds, **not all mentions are created equal**. A thousand tweets might have less business impact than a single Reddit thread that ranks on Google. The **Source Insights API** is your "Terrain Map." It doesn't just count mentions; it qualifies them by their **impact on your defensive moat**.

### **USP (Unique Selling Proposition)**
- **Platform-Specific "PR Health"**: Unlike generic sentiment analysis, this API calculates "PR Health" differently for Reddit (threading depth/upvotes) vs. Twitter (retweet velocity) vs. Instagram (visual engagement).
- **LLM Visibility Score**: A proprietary metric that predicts how likely your brand's content on a specific platform is to be picked up by Large Language Models (ChatGPT, Gemini, etc.) based on that platform's authoritative weight.

### **Business Impact**
- **Allocate Budget Surgically**: Stop spending on platforms where you have high volume but low "Conversion Impact."
- **Defend Against "Rot"**: Identify which specific sub-communities (subreddits, hashtags) are acting as "Patient Zero" for negative narratives before they breed.

### **Inputs & Outputs**
- **Input**: `brand_id` (e.g., "tesla"), `lookback_days` (default 30).
- **Output**:
  - `platforms`: Breakdown by generic platform (Twitter, Reddit, etc.).
    - `visibility`: Views, Engagement, Volume.
    - `conversions`: Hard business metrics (signups, purchases attributed to this source).
    - `pr_health`: A composite score of Sentiment, Anger levels, and Credibility.
    - `llm_visibility`:
      - `score`: 0-100 likelihood of inclusion in AI training data/RAG results.
      - `risk_level`: Low/Medium/High.
      - `potential_drop_pct`: Projected loss in AI visibility if negative trends continue.

---

## 2. Simulate API (The "War Games")

### **The MOAT Perspective**
Passive monitoring is defensive. **Simulation is offensive.** This API allows you to "War Game" your reputation strategy. It answers the question: *"If we launch this PR campaign, will it actually move the needle, or are we shouting into the void?"*

### **USP (Unique Selling Proposition)**
- **Volatility-Aware Physics**: This isn't a linear calculator. It uses your brand's specific **Historical Volatility**. If your brand is volatile (e.g., crypto), a small PR stunt won't move your score. If you are stable (e.g., insurance), it will. The API knows the "inertia" of your brand.
- **Sigma-Event Modeling**: Actions are modeled as "Standard Deviation Events" (Sigmas). We don't guess; we apply statistical probability to predict outcomes.

### **Business Impact**
- **ROI Prediction**: Estimate the impact of a $50k influencer campaign on your "LLM Visibility" score *before* you spend the money.
- **Crisis Simulation**: "If we stay silent (do nothing), how much will our reputation bleed in the next 24 hours?"

### **Inputs & Outputs**
- **Input**:
  - `brand_id`: Target brand.
  - `actions`: List of strategic moves (e.g., `["launch_pr_campaign", "partner_with_influencer"]`).
  - `platform` (Optional): Target specific platform physics.
  - `current_metrics` (Optional): Baseline state (auto-fetched if missing).
- **Output**:
  - `original_score`: Where you are now.
  - `new_score`: Predicted score after actions.
  - `percent_change`: The "Lift."
  - `baseline_metrics`: The starting usage stats.
  - `volatility_used`: The specific "Inertia" parameters used for the math (e.g., "Sentiment moves slow for this brand").

---

## Integration Strategy

### **Real-Time Pipeline**
1. **Ingest**: High-fidelity scrapers feed raw signals (Tweets, Reddit threads) into ClickHouse.
2. **Process**: The `SourceInsightsEngine` aggregates these into "Platform Insights."
3. **Act**: The Dashboard calls `Simulate` to let you test strategies on this live data.

*Sentinel: Don't just watch your reputation. Engineer it.*

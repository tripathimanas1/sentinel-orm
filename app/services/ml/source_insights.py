from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import numpy as np
from app.core.logging import get_logger
from app.db.clickhouse import execute_clickhouse_query
from app.services.ml.llm_visibility import LLMVisibilityEngine

logger = get_logger(__name__)


class SourceInsightsEngine:
    """Engine for generating insights across different platforms (Instagram, Reddit, Quora, etc.)."""

    def __init__(self) -> None:
        self.lookback_days = 90
        self.llm_visibility_engine = LLMVisibilityEngine()

    def get_brand_volatility(self, brand_id: str) -> dict[str, float]:
        """Calculate historical volatility (Standard Deviation) for brand metrics.
        
        This allows simulations to be grounded in the brand's actual historical behavior.
        """
        # 1. Sentiment Volatility
        sent_query = """
        SELECT stddevSamp(sentiment_score) as sentiment_std
        FROM sentiment_scores
        WHERE brand_id = %(brand_id)s
        """
        sent_res = execute_clickhouse_query(sent_query, {"brand_id": brand_id})
        sentiment_std = sent_res[0][0] if sent_res and sent_res[0][0] > 0 else 0.2  # Default fallback

        # 2. Engagement Volatility (Log-scale to handle viral outliers)
        # We look at average engagement per event
        eng_query = """
        SELECT stddevSamp(log1p(likes + shares + comments)) as engagement_log_std
        FROM signal_events
        WHERE brand_id = %(brand_id)s
        """
        eng_res = execute_clickhouse_query(eng_query, {"brand_id": brand_id})
        engagement_std = eng_res[0][0] if eng_res and eng_res[0][0] > 0 else 0.5

        # 3. Volume Volatility (Daily count fluctuation)
        vol_query = """
        SELECT stddevSamp(daily_count) as volume_std
        FROM (
            SELECT toDate(timestamp) as day, count(*) as daily_count
            FROM signal_events
            WHERE brand_id = %(brand_id)s
            GROUP BY day
        )
        """
        vol_res = execute_clickhouse_query(vol_query, {"brand_id": brand_id})
        volume_std = vol_res[0][0] if vol_res and vol_res[0][0] > 0 else 5.0

        return {
            "sentiment": float(sentiment_std),
            "engagement": float(engagement_std),
            "volume": float(volume_std),
            "credibility": 0.1 # Credibility is usually stable, fixed small std dev
        }

    def get_brand_metrics(self, brand_id: str, platform: Optional[str] = None) -> dict[str, float]:
        """Fetch current metrics for the brand to serve as baseline for simulation.
        
        Aggregates data over the lookback period (default 30 days).
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        query = """
        SELECT
            count(*) as volume,
            sum(likes + shares + comments) as engagement,
            avg(ss.sentiment_score) as sentiment,
            avg(cs.credibility_score) as credibility
        FROM signal_events se
        LEFT JOIN sentiment_scores ss ON se.event_id = ss.event_id
        LEFT JOIN credibility_scores cs ON se.event_id = cs.event_id
        WHERE se.brand_id = %(brand_id)s
          AND se.timestamp >= %(start_date)s
        """
        
        params = {"brand_id": brand_id, "start_date": start_date}
        
        if platform:
            query += " AND se.platform = %(platform)s"
            params["platform"] = platform
            
        res = execute_clickhouse_query(query, params)
        
        if not res or not res[0]:
            # meaningful defaults if no data
            return {"volume": 0, "engagement": 0, "sentiment": 0.0, "credibility": 0.5}
            
        row = res[0]
        return {
            "volume": float(row[0]),
            "engagement": float(row[1]),
            "sentiment": float(row[2] if row[2] is not None else 0.0),
            "credibility": float(row[3] if row[3] is not None else 0.5)
        }

    def get_source_performance(self, brand_id: str) -> dict[str, Any]:
        """Compute performance metrics across all sources.
        
        Metrics:
        - Conversions
        - Brand Visibility (Views/Engagement)
        - Sentiment/PR Health
        - LLM Visibility/SEO
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.lookback_days)

        # 1. Get Visibility and Engagement by Platform
        visibility_query = """
        SELECT
            platform,
            SUM(views) as total_views,
            SUM(likes + shares + comments) as total_engagement,
            COUNT(*) as signal_volume
        FROM signal_events
        WHERE brand_id = %(brand_id)s
          AND timestamp >= %(start_date)s
        GROUP BY platform
        """
        
        visibility_results = execute_clickhouse_query(
            visibility_query, {"brand_id": brand_id, "start_date": start_date}
        )

        # 2. Get Conversions by Platform
        conversion_query = """
        SELECT
            platform,
            COUNT(*) as conversion_count,
            SUM(conversion_value) as total_value
        FROM conversion_events
        WHERE brand_id = %(brand_id)s
          AND timestamp >= %(start_date)s
        GROUP BY platform
        """
        
        conversion_results = execute_clickhouse_query(
            conversion_query, {"brand_id": brand_id, "start_date": start_date}
        )

        # 3. Get PR/Sentiment/Credibility Health by Platform
        # Assuming credibility_scores table exists and is linked by event_id
        # If not, avg_credibility will be null, handled in code.
        sentiment_query = """
        SELECT
            se.platform,
            AVG(ss.sentiment_score) as avg_sentiment,
            SUM(CASE WHEN ss.sentiment_score < -0.5 THEN 1 ELSE 0 END) as negative_signals,
            AVG(ev.anger) as avg_anger,
            AVG(ev.frustration) as avg_frustration,
            AVG(cs.credibility_score) as avg_credibility
        FROM signal_events se
        LEFT JOIN sentiment_scores ss ON se.event_id = ss.event_id
        LEFT JOIN emotion_vectors ev ON se.event_id = ev.event_id
        LEFT JOIN credibility_scores cs ON se.event_id = cs.event_id
        WHERE se.brand_id = %(brand_id)s
          AND se.timestamp >= %(start_date)s
        GROUP BY se.platform
        """
        
        sentiment_results = execute_clickhouse_query(
            sentiment_query, {"brand_id": brand_id, "start_date": start_date}
        )

        # Process Results
        platforms = {}
        
        for row in visibility_results:
            p, views, engagement, volume = row
            platforms[p] = {
                "visibility": {"views": int(views), "engagement": int(engagement), "volume": int(volume)},
                "conversions": {"count": 0, "value": 0.0},
                "pr_health": {"sentiment": 0.0, "negative_signals": 0, "anger": 0.0, "frustration": 0.0, "credibility": 0.5},
                "llm_visibility": {"score": 0.0, "risk_level": "Low", "cross_model_scores": {}}
            }
            
        for row in conversion_results:
            p, count, value = row
            if p not in platforms:
                platforms[p] = {
                    "visibility": {"views": 0, "engagement": 0, "volume": 0},
                    "conversions": {"count": 0, "value": 0.0},
                    "pr_health": {"sentiment": 0.0, "negative_signals": 0, "anger": 0.0, "frustration": 0.0, "credibility": 0.5},
                    "llm_visibility": {"score": 0.0, "risk_level": "Low", "cross_model_scores": {}}
                }
            platforms[p]["conversions"] = {"count": int(count), "value": float(value)}

        for row in sentiment_results:
            p, sent, neg, anger, frust, cred = row
            if p in platforms:
                platforms[p]["pr_health"] = {
                    "sentiment": float(sent or 0),
                    "negative_signals": int(neg or 0),
                    "anger": float(anger or 0),
                    "frustration": float(frust or 0),
                    "credibility": float(cred or 0.5)
                }

        # Calculate LLM Visibility for each platform
        for p, data in platforms.items():
            metrics = {
                "credibility": data["pr_health"]["credibility"],
                "sentiment": data["pr_health"]["sentiment"],
                "engagement": data["visibility"]["engagement"],
                "volume": data["visibility"]["volume"]
            }
            
            # 1. Main Score
            vis_score = self.llm_visibility_engine.calculate_visibility_score(
                metrics["credibility"],
                metrics["sentiment"],
                metrics["engagement"],
                metrics["volume"]
            )
            
            # 2. Risk Prediction
            risk_data = self.llm_visibility_engine.predict_risk(data)
            
            # 3. Cross Model Scores
            cross_model = self.llm_visibility_engine.get_cross_model_scores(metrics)
            
            data["llm_visibility"] = {
                "score": vis_score,
                "risk_level": risk_data["risk_level"],
                "risk_score": risk_data["risk_score"],
                "potential_drop_pct": risk_data["potential_visibility_drop_pct"],
                "reasons": risk_data["reasons"],
                "cross_model_scores": cross_model
            }

        # Determine "Insights"
        insights = []
        
        if not platforms:
            return {"brand_id": brand_id, "platforms": {}, "top_insights": ["No data available for the selected period."]}

        # Conversion Leader
        top_conv_platform = max(platforms.items(), key=lambda x: x[1]["conversions"]["count"], default=(None, None))
        if top_conv_platform[0] and top_conv_platform[1]["conversions"]["count"] > 0:
            insights.append(f"{top_conv_platform[0].capitalize()} is leading in conversions with {top_conv_platform[1]['conversions']['count']} events.")

        # Visibility Leader
        top_vis_platform = max(platforms.items(), key=lambda x: x[1]["llm_visibility"]["score"], default=(None, None))
        if top_vis_platform[0] and top_vis_platform[1]["llm_visibility"]["score"] > 0:
            insights.append(f"{top_vis_platform[0].capitalize()} has the HIGHEST LLM Visibility Score ({top_vis_platform[1]['llm_visibility']['score']:.1f}).")

        # PR Needs Attention
        pr_attention = [p for p, data in platforms.items() if data["pr_health"]["sentiment"] < 0 or data["pr_health"]["anger"] > 0.5]
        if pr_attention:
            platforms_str = ", ".join([p.capitalize() for p in pr_attention])
            insights.append(f"PR needs attention on: {platforms_str} due to low sentiment or high anger scores.")
            
        # Risk Alerts
        high_risk = [p for p, data in platforms.items() if data["llm_visibility"]["risk_level"] == "High"]
        if high_risk:
            platforms_str = ", ".join([p.capitalize() for p in high_risk])
            insights.append(f"HIGH RISK of visibility drop on: {platforms_str}. Check negative sentiment trends.")

        return {
            "brand_id": brand_id,
            "period_days": self.lookback_days,
            "platforms": platforms,
            "top_insights": insights
        }

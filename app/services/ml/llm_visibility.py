"""LLM Visibility and Simulation Engine."""

from typing import Any, Dict, List, Optional
from uuid import uuid4

import numpy as np
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMVisibilityEngine:
    """Engine for analyzing and predicting LLM visibility metrics."""

    def __init__(self) -> None:
        self.weights = {
            "credibility": 0.35,
            "sentiment": 0.25,
            "engagement": 0.25,
            "volume": 0.15,
        }
        # Simulation of different model biases
        self.model_biases = {
            "gpt-4": {"credibility": 1.2, "sentiment": 0.9, "engagement": 1.0},
            "claude-3": {"credibility": 1.4, "sentiment": 1.1, "engagement": 0.8},
            "gemini-pro": {"credibility": 1.1, "sentiment": 1.0, "engagement": 1.2},
        }

    def calculate_visibility_score(
        self,
        credibility_score: float,
        sentiment_score: float,
        engagement_metric: float,
        volume_metric: float,
        model_name: str = "average",
    ) -> float:
        """Calculate LLM visibility score (0-100)."""
        
        # Normalize inputs
        # Credibility is 0-1
        # Sentiment is -1 to 1 -> Normalize to 0-1
        norm_sentiment = (sentiment_score + 1) / 2
        
        # Engagement and Volume need log scaling or similar normalization
        # Assuming engagement is e.g. 0-10000+, map to 0-1
        norm_engagement = min(np.log1p(engagement_metric) / 10, 1.0)
        norm_volume = min(np.log1p(volume_metric) / 5, 1.0)

        # Apply Model Bias
        bias = self.model_biases.get(model_name, {"credibility": 1.0, "sentiment": 1.0, "engagement": 1.0})

        score = (
            (credibility_score * self.weights["credibility"] * bias["credibility"]) +
            (norm_sentiment * self.weights["sentiment"] * bias["sentiment"]) +
            (norm_engagement * self.weights["engagement"] * bias["engagement"]) +
            (norm_volume * self.weights["volume"])
        )
        
        # Clip and scale to 0-100
        return float(np.clip(score * 100, 0, 100))

    def simulate_content_change(
        self,
        current_metrics: Dict[str, float],
        changes: Dict[str, float],
        model_name: str = "average"
    ) -> Dict[str, Any]:
        """Simulate how changing content parameters affects visibility.
        
        Args:
            current_metrics: Dict with keys 'credibility', 'sentiment', 'engagement', 'volume'
            changes: Dict with keys representing delta percentage (e.g. {'sentiment': 0.1} for +10%)
            model_name: specific AI model to simulate against
            
        Returns:
            Dict containing new score, old score, delta, and percentage change.
        """
        old_score = self.calculate_visibility_score(
            current_metrics.get("credibility", 0.5),
            current_metrics.get("sentiment", 0.0),
            current_metrics.get("engagement", 0),
            current_metrics.get("volume", 0),
            model_name
        )

        # Apply changes
        new_cred = current_metrics.get("credibility", 0.5) * (1 + changes.get("credibility", 0.0))
        new_sent = current_metrics.get("sentiment", 0.0)  # Sentiment is additive for simulation usually, but let's assume raw score shift
        if "sentiment" in changes:
             # If sentiment change is passed as additive delta (e.g. +0.2)
             # rather than multiplicative since sentiment is -1 to 1
             new_sent += changes["sentiment"]

        new_eng = current_metrics.get("engagement", 0) * (1 + changes.get("engagement", 0.0))
        new_vol = current_metrics.get("volume", 0) * (1 + changes.get("volume", 0.0))

        new_score = self.calculate_visibility_score(
            min(max(new_cred, 0), 1),
            min(max(new_sent, -1), 1),
            new_eng,
            new_vol,
            model_name
        )

        delta = new_score - old_score
        pct_change = (delta / old_score * 100) if old_score > 0 else 0

        return {
            "original_score": old_score,
            "new_score": new_score,
            "absolute_change": delta,
            "percent_change": pct_change,
            "model_used": model_name
        }

    def predict_risk(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict risk of visibility drop based on negative trends.
        
        This acts as the 'predictive risk model'.
        """
        # Heuristic: If sentiment is trending down or credibility is low, high risk.
        sentiment = platform_data.get("pr_health", {}).get("sentiment", 0)
        neg_signals = platform_data.get("pr_health", {}).get("negative_signals", 0)
        current_vis = platform_data.get("visibility", {}).get("views", 0)
        
        risk_score = 0.0
        reasons = []

        if sentiment < -0.2:
            risk_score += 40
            reasons.append("Negative sentiment detected")
        
        if neg_signals > 50:
            risk_score += 30
            reasons.append("High volume of negative signals")

        # Simulate a drop if rating/sentiment drops further
        potential_drop_simulation = self.simulate_content_change(
            {
                "credibility": 0.7, # default
                "sentiment": sentiment,
                "engagement": platform_data.get("visibility", {}).get("engagement", 0),
                "volume": platform_data.get("visibility", {}).get("volume", 0)
            },
            {"sentiment": -0.5} # Simulate 0.5 drop in sentiment
        )
        
        predicted_drop_pct = potential_drop_simulation["percent_change"]

        return {
            "risk_score": min(risk_score, 100), # 0-100 High Risk
            "risk_level": "High" if risk_score > 60 else "Medium" if risk_score > 30 else "Low",
            "potential_visibility_drop_pct": predicted_drop_pct,
            "reasons": reasons
        }

    def get_cross_model_scores(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Get visibility scores across different AI models."""
        scores = {}
        for model in self.model_biases.keys():
            scores[model] = self.calculate_visibility_score(
                metrics.get("credibility", 0.5),
                metrics.get("sentiment", 0.0),
                metrics.get("engagement", 0),
                metrics.get("volume", 0),
                model_name=model
            )
        scores["average"] = self.calculate_visibility_score(
            metrics.get("credibility", 0.5),
            metrics.get("sentiment", 0.0),
            metrics.get("engagement", 0),
            metrics.get("volume", 0),
            model_name="average"
        )
        return scores

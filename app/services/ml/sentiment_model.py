"""Sentiment regression model."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import joblib
import numpy as np
import xgboost as xgb

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ml.feature_extractor import FeatureExtractor

logger = get_logger(__name__)
settings = get_settings()


class SentimentModel:
    """Sentiment regression model using XGBoost.
    
    Predicts continuous sentiment score in range [-1.0, 1.0]
    where -1.0 is very negative and 1.0 is very positive.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        """Initialize sentiment model.
        
        Args:
            model_path: Path to saved model file
        """
        self.feature_extractor = FeatureExtractor()
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: list[str] = []
        self.model_version = settings.sentiment_model_version
        
        # Determine model path if not provided
        if model_path is None:
            default_path = Path(settings.model_path) / f"sentiment_{self.model_version}.joblib"
            if default_path.exists():
                model_path = str(default_path)

        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize a new XGBoost model."""
        logger.info("Initializing new sentiment model")
        
        self.model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        
        # Define feature names (excluding embedding which is handled separately)
        self.feature_names = [
            "word_count",
            "char_count",
            "avg_word_length",
            "positive_word_count",
            "negative_word_count",
            "lexicon_polarity",
            "likes",
            "shares",
            "comments",
            "views",
            "total_engagement",
            "engagement_rate",
            "engagement_velocity",
            "share_ratio",
            "account_age_days",
            "follower_count",
            "following_count",
            "post_count",
            "verified",
            "follower_following_ratio",
            "avg_posts_per_day",
            "source_type_review",
            "source_type_social",
            "source_type_ticket",
            "source_type_news",
            "source_type_influencer",
            "platform_credibility",
        ]

    def predict(self, event: dict[str, Any]) -> dict[str, Any]:
        """Predict sentiment score for an event.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary with sentiment score and confidence
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Extract features
        features = self.feature_extractor.extract_all_features(event)
        
        # Convert to array (excluding embedding for now - can be added later)
        feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
        feature_array = feature_array.reshape(1, -1)
        
        # Predict
        sentiment_score = float(self.model.predict(feature_array)[0])
        
        # Clip to valid range
        sentiment_score = np.clip(sentiment_score, -1.0, 1.0)
        
        # Calculate confidence
        confidence = 0.8  # Placeholder
        
        return {
            "event_id": event.get("event_id", str(uuid4())),
            "brand_id": event["brand_id"],
            "timestamp": event.get("timestamp", datetime.utcnow()),
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "model_version": self.model_version,
        }

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the sentiment model.
        
        Args:
            X: Feature matrix
            y: Target sentiment scores [-1, 1]
        """
        if self.model is None:
            self._initialize_model()
        
        logger.info("Training sentiment model", samples=len(X))
        self.model.fit(X, y)
        logger.info("Sentiment model training complete")

    def save_model(self, path: str) -> None:
        """Save model to disk.
        
        Args:
            path: Path to save model
        """
        if self.model is None:
            raise RuntimeError("No model to save")
        
        model_data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "model_version": self.model_version,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, path)
        logger.info("Saved sentiment model", path=path)

    def load_model(self, path: str) -> None:
        """Load model from disk.
        
        Args:
            path: Path to model file
        """
        logger.info("Loading sentiment model", path=path)
        model_data = joblib.load(path)
        
        self.model = model_data["model"]
        self.feature_names = model_data["feature_names"]
        self.model_version = model_data.get("model_version", "unknown")
        
        logger.info("Loaded sentiment model", version=self.model_version)

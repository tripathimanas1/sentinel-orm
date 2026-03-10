"""Source credibility scoring model."""

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


class CredibilityModel:
    """Source credibility scoring model using XGBoost.
    
    Predicts credibility score in range [0.0, 1.0]
    where 0.0 is not credible and 1.0 is highly credible.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        """Initialize credibility model.
        
        Args:
            model_path: Path to saved model file
        """
        self.feature_extractor = FeatureExtractor()
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: list[str] = []
        self.model_version = settings.credibility_model_version
        
        # Determine model path if not provided
        if model_path is None:
            default_path = Path(settings.model_path) / f"credibility_{self.model_version}.joblib"
            if default_path.exists():
                model_path = str(default_path)

        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize a new XGBoost model."""
        logger.info("Initializing new credibility model")
        
        self.model = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        
        # Features focused on author and source credibility
        self.feature_names = [
            "account_age_days",
            "follower_count",
            "following_count",
            "post_count",
            "verified",
            "follower_following_ratio",
            "avg_posts_per_day",
            "platform_credibility",
            "total_engagement",
            "engagement_rate",
            "avg_engagement_per_post",
        ]

    def predict(self, event: dict[str, Any]) -> dict[str, Any]:
        """Predict credibility score for an event/author.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary with credibility score and metadata
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Extract features
        all_features = self.feature_extractor.extract_all_features(event)
        
        # Add derived feature
        post_count = all_features.get("post_count", 0)
        total_engagement = all_features.get("total_engagement", 0)
        all_features["avg_engagement_per_post"] = (
            total_engagement / post_count if post_count > 0 else 0
        )
        
        # Convert to array
        feature_array = np.array([all_features.get(name, 0.0) for name in self.feature_names])
        feature_array = feature_array.reshape(1, -1)
        
        # Predict
        credibility_score = float(self.model.predict(feature_array)[0])
        
        # Clip to valid range
        credibility_score = np.clip(credibility_score, 0.0, 1.0)
        
        # Calculate confidence
        confidence = 0.85  # Placeholder
        
        # Extract author metadata for storage
        import json
        author_metadata = event.get("author_metadata", "{}")
        if isinstance(author_metadata, str):
            try:
                author_metadata = json.loads(author_metadata)
            except json.JSONDecodeError:
                author_metadata = {}
        
        return {
            "event_id": event.get("event_id", str(uuid4())),
            "brand_id": event["brand_id"],
            "source_id": event["source_id"],
            "author_id": event.get("author_id", ""),
            "timestamp": event.get("timestamp", datetime.utcnow()),
            "credibility_score": credibility_score,
            "confidence": confidence,
            "account_age_days": int(all_features.get("account_age_days", 0)),
            "historical_post_count": int(all_features.get("post_count", 0)),
            "avg_engagement": all_features.get("avg_engagement_per_post", 0.0),
            "verified": bool(all_features.get("verified", False)),
            "model_version": self.model_version,
        }

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the credibility model.
        
        Args:
            X: Feature matrix
            y: Target credibility scores [0, 1]
        """
        if self.model is None:
            self._initialize_model()
        
        logger.info("Training credibility model", samples=len(X))
        self.model.fit(X, y)
        logger.info("Credibility model training complete")

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
        logger.info("Saved credibility model", path=path)

    def load_model(self, path: str) -> None:
        """Load model from disk.
        
        Args:
            path: Path to model file
        """
        logger.info("Loading credibility model", path=path)
        model_data = joblib.load(path)
        
        self.model = model_data["model"]
        self.feature_names = model_data["feature_names"]
        self.model_version = model_data.get("model_version", "unknown")
        
        logger.info("Loaded credibility model", version=self.model_version)

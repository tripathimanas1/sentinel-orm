"""Emotion multi-label classification model."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import joblib
import numpy as np
import xgboost as xgb
from sklearn.multioutput import MultiOutputRegressor

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ml.feature_extractor import FeatureExtractor

logger = get_logger(__name__)
settings = get_settings()


class EmotionModel:
    """Emotion multi-label classification model.
    
    Predicts probabilities for 6 emotions:
    - anger
    - frustration
    - fear
    - trust
    - satisfaction
    - joy
    """

    EMOTION_LABELS = ["anger", "frustration", "fear", "trust", "satisfaction", "joy"]

    def __init__(self, model_path: Optional[str] = None) -> None:
        """Initialize emotion model.
        
        Args:
            model_path: Path to saved model file
        """
        self.feature_extractor = FeatureExtractor()
        self.model: Optional[MultiOutputRegressor] = None
        self.feature_names: list[str] = []
        self.model_version = settings.emotion_model_version
        
        # Determine model path if not provided
        if model_path is None:
            default_path = Path(settings.model_path) / f"emotion_{self.model_version}.joblib"
            if default_path.exists():
                model_path = str(default_path)

        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize a new multi-output XGBoost model."""
        logger.info("Initializing new emotion model")
        
        base_estimator = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        
        self.model = MultiOutputRegressor(base_estimator)
        
        # Same features as sentiment model
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
        """Predict emotion probabilities for an event.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary with emotion scores
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Extract features
        features = self.feature_extractor.extract_all_features(event)
        
        # Convert to array
        feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
        feature_array = feature_array.reshape(1, -1)
        
        # Predict
        emotion_probs = self.model.predict(feature_array)[0]
        
        # Clip to valid range [0, 1]
        emotion_probs = np.clip(emotion_probs, 0.0, 1.0)
        
        # Create result dictionary
        result = {
            "event_id": event.get("event_id", str(uuid4())),
            "brand_id": event["brand_id"],
            "timestamp": event.get("timestamp", datetime.utcnow()),
            "model_version": self.model_version,
        }
        
        # Add emotion scores
        for label, score in zip(self.EMOTION_LABELS, emotion_probs):
            result[label] = float(score)
        
        return result

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the emotion model.
        
        Args:
            X: Feature matrix
            y: Target emotion matrix (samples x 6 emotions)
        """
        if self.model is None:
            self._initialize_model()
        
        logger.info("Training emotion model", samples=len(X))
        self.model.fit(X, y)
        logger.info("Emotion model training complete")

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
            "emotion_labels": self.EMOTION_LABELS,
            "model_version": self.model_version,
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, path)
        logger.info("Saved emotion model", path=path)

    def load_model(self, path: str) -> None:
        """Load model from disk.
        
        Args:
            path: Path to model file
        """
        logger.info("Loading emotion model", path=path)
        model_data = joblib.load(path)
        
        self.model = model_data["model"]
        self.feature_names = model_data["feature_names"]
        self.model_version = model_data.get("model_version", "unknown")
        
        logger.info("Loaded emotion model", version=self.model_version)

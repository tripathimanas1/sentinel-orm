"""Feature extraction for ML models."""

from datetime import datetime
from typing import Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global embedding model (lazy loaded)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or load the sentence embedding model."""
    global _embedding_model
    
    if _embedding_model is None:
        logger.info("Loading embedding model", model=settings.embedding_model)
        _embedding_model = SentenceTransformer(settings.embedding_model)
    
    return _embedding_model


class FeatureExtractor:
    """Extract features from signal events for ML models."""

    def __init__(self) -> None:
        self._embedding_model: Optional[SentenceTransformer] = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model

    def extract_text_features(self, text: str, include_embeddings: bool = True) -> dict[str, Any]:
        """Extract text-based features.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary of text features
        """
        # Truncate text if too long
        text = text[:settings.max_text_length]
        
        # Get text embedding
        res = {}
        if include_embeddings:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            res["embedding"] = embedding.tolist()
        
        # Basic text statistics
        word_count = len(text.split())
        char_count = len(text)
        avg_word_length = char_count / word_count if word_count > 0 else 0
        
        # Sentiment lexicon features (simplified)
        positive_words = ["good", "great", "excellent", "love", "amazing", "wonderful", "best"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "poor", "disappointing"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        res.update({
            "word_count": word_count,
            "char_count": char_count,
            "avg_word_length": avg_word_length,
            "positive_word_count": positive_count,
            "negative_word_count": negative_count,
            "lexicon_polarity": positive_count - negative_count,
        })
        return res

    def extract_engagement_features(self, event: dict[str, Any]) -> dict[str, float]:
        """Extract engagement-based features.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary of engagement features
        """
        likes = event.get("likes", 0)
        shares = event.get("shares", 0)
        comments = event.get("comments", 0)
        views = event.get("views", 0)
        
        # Engagement metrics
        total_engagement = likes + shares + comments
        engagement_rate = total_engagement / views if views > 0 else 0
        
        # Engagement velocity (requires timestamp)
        timestamp = event.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hours_since = (datetime.utcnow() - timestamp).total_seconds() / 3600
            engagement_velocity = total_engagement / hours_since if hours_since > 0 else 0
        else:
            engagement_velocity = 0
        
        return {
            "likes": float(likes),
            "shares": float(shares),
            "comments": float(comments),
            "views": float(views),
            "total_engagement": float(total_engagement),
            "engagement_rate": engagement_rate,
            "engagement_velocity": engagement_velocity,
            "share_ratio": shares / total_engagement if total_engagement > 0 else 0,
        }

    def extract_author_features(self, event: dict[str, Any]) -> dict[str, float]:
        """Extract author-based features.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary of author features
        """
        # Parse author metadata
        import json
        author_metadata = event.get("author_metadata", "{}")
        if isinstance(author_metadata, str):
            try:
                author_metadata = json.loads(author_metadata)
            except json.JSONDecodeError:
                author_metadata = {}
        
        account_age_days = author_metadata.get("account_age_days", 0)
        follower_count = author_metadata.get("follower_count", 0)
        following_count = author_metadata.get("following_count", 0)
        post_count = author_metadata.get("post_count", 0)
        verified = author_metadata.get("verified", False)
        
        # Derived features
        follower_following_ratio = (
            follower_count / following_count if following_count > 0 else 0
        )
        avg_posts_per_day = post_count / account_age_days if account_age_days > 0 else 0
        
        return {
            "account_age_days": float(account_age_days),
            "follower_count": float(follower_count),
            "following_count": float(following_count),
            "post_count": float(post_count),
            "verified": float(verified),
            "follower_following_ratio": follower_following_ratio,
            "avg_posts_per_day": avg_posts_per_day,
        }

    def extract_source_features(self, event: dict[str, Any]) -> dict[str, float]:
        """Extract source-based features.
        
        Args:
            event: Signal event
        
        Returns:
            Dictionary of source features
        """
        source_type = event.get("source_type", "")
        platform = event.get("platform", "")
        
        # One-hot encoding for source types
        source_types = ["review", "social", "ticket", "news", "influencer"]
        source_features = {
            f"source_type_{st}": float(source_type == st) for st in source_types
        }
        
        # Platform credibility (simplified heuristic)
        platform_credibility = {
            "google": 0.9,
            "apple": 0.9,
            "twitter": 0.7,
            "reddit": 0.6,
            "facebook": 0.7,
            "instagram": 0.7,
            "tiktok": 0.5,
        }
        
        source_features["platform_credibility"] = platform_credibility.get(
            platform.lower(), 0.5
        )
        
        return source_features

    def extract_all_features(self, event: dict[str, Any], include_embeddings: bool = True) -> dict[str, Any]:
        """Extract all features from an event.
        
        Args:
            event: Signal event
            include_embeddings: Whether to include text embeddings
        
        Returns:
            Dictionary of all features
        """
        text = event.get("text", "")
        
        features = {}
        features.update(self.extract_text_features(text, include_embeddings=include_embeddings))
        features.update(self.extract_engagement_features(event))
        features.update(self.extract_author_features(event))
        features.update(self.extract_source_features(event))
        
        return features

    def features_to_array(
        self, features: dict[str, Any], feature_names: list[str]
    ) -> np.ndarray:
        """Convert feature dictionary to numpy array.
        
        Args:
            features: Feature dictionary
            feature_names: Ordered list of feature names
        
        Returns:
            Numpy array of features
        """
        # Handle embedding separately
        if "embedding" in feature_names:
            embedding = features.get("embedding", [])
            other_features = [
                features.get(name, 0.0)
                for name in feature_names
                if name != "embedding"
            ]
            return np.concatenate([embedding, other_features])
        else:
            return np.array([features.get(name, 0.0) for name in feature_names])

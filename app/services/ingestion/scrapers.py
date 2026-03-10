import asyncio
import httpx
import json
import random
from typing import List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
from app.core.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class BaseScraper(ABC):
    def __init__(self, platform_name: str, delay: float = 2.0):
        self.platform = platform_name
        self.delay = delay
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": settings.reddit_user_agent}
        )

    @abstractmethod
    async def fetch_signals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    async def close(self):
        await self.client.aclose()

class TwitterScraper(BaseScraper):
    """
    Real-time Twitter scraper integration using RapidAPI (twitter-api45).
    """
    def __init__(self):
        super().__init__("twitter")
        self.api_url = "https://twitter-api45.p.rapidapi.com/search.php"

    async def fetch_signals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not settings.rapidapi_key or settings.rapidapi_key == "your_rapidapi_key":
            logger.error("RapidAPI Key not configured in .env for Twitter scraping.")
            return []

        try:
            headers = {
                "x-rapidapi-host": "twitter-api45.p.rapidapi.com",
                "x-rapidapi-key": settings.rapidapi_key
            }
            params = {
                "query": query,
                "search_type": "Latest"
            }
            response = await self.client.get(self.api_url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"Twitter RapidAPI failed with status {response.status_code}: {response.text}")
                return []
                
            data = response.json()
            
            signals = []
            # twitter-api45 typically returns timeline or search results
            # We'll look for common search result keys
            items = data.get("timeline", []) or data.get("tweets", []) or data.get("data", []) or data.get("results", [])
            
            # If data is a dict and none of the above keys exist, it might be the timeline itself
            if not items and isinstance(data, dict):
                # Check for standard Twitter API v2 'data' key or v1.1 search 'statuses'
                items = data.get("statuses", [])
            
            for tweet in items[:limit]:
                # Extract text, id, and metrics with fallbacks
                text = tweet.get("text") or tweet.get("full_text") or ""
                tweet_id = tweet.get("id_str") or tweet.get("id") or str(random.randint(1000, 9999))
                
                # RapidAPI structures often vary, we try multiple paths for metrics
                likes = tweet.get("favorite_count", 0)
                shares = tweet.get("retweet_count", 0)
                replies = tweet.get("reply_count", 0)
                views = tweet.get("views_count", 0) or (likes * 15)
                
                signals.append({
                    "source_id": f"tw-{tweet_id}",
                    "source_type": "social",
                    "platform": "twitter",
                    "text": text,
                    "likes": likes,
                    "shares": shares,
                    "comments": replies,
                    "views": views,
                    "timestamp": tweet.get("created_at") or datetime.utcnow().isoformat(),
                    "author_metadata": {"user": tweet.get("user", {})},
                    "raw_response": tweet
                })
            return signals
        except Exception as e:
            logger.error(f"Twitter RapidAPI error: {e}")
            return []

class RedditScraper(BaseScraper):
    """
    Real-time Reddit scraper using RapidAPI (reddit34).
    """
    def __init__(self):
        super().__init__("reddit")
        self.api_url = "https://reddit34.p.rapidapi.com/getSearchPosts"

    async def fetch_signals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not settings.rapidapi_key or settings.rapidapi_key == "your_rapidapi_key":
            logger.error("RapidAPI Key not configured in .env for Reddit scraping.")
            # Fallback to public API if RapidAPI is not configured
            return await self._fetch_public(query, limit)

        try:
            headers = {
                "x-rapidapi-host": "reddit34.p.rapidapi.com",
                "x-rapidapi-key": settings.rapidapi_key
            }
            params = {"query": query}
            response = await self.client.get(self.api_url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"Reddit RapidAPI failed with status {response.status_code}: {response.text}")
                return await self._fetch_public(query, limit)

            data = response.json()
            
            signals = []
            # Mapping logic based on updated reddit34 schema
            # Structure: data['data']['posts'] -> post['data']
            posts = data.get("data", {}).get("posts", [])
            
            for post in posts[:limit]:
                # Extract inner data object
                item = post.get("data", {})
                if not item:
                    continue
                    
                created_at = datetime.fromtimestamp(item.get("created_utc", datetime.utcnow().timestamp())).isoformat()
                
                signals.append({
                    "source_id": f"rd-{item.get('id', random.randint(1000, 9999))}",
                    "source_type": "social",
                    "platform": "reddit",
                    "text": f"{item.get('title', '')}\n{item.get('selftext', '')[:2000]}",
                    "likes": item.get("ups", 0),
                    "shares": item.get("num_crossposts", 0),
                    "comments": item.get("num_comments", 0),
                    "views": int(item.get("ups", 0) * random.uniform(20, 50)) + item.get("num_comments", 0) * 10,
                    "timestamp": created_at,
                    "author_metadata": {
                        "subreddit": item.get("subreddit_name_prefixed", f"r/{item.get('subreddit', 'unknown')}"),
                        "author": item.get("author", "anonymous"),
                        "subreddit_subscribers": item.get("subreddit_subscribers", 0)
                    },
                    "raw_data": item
                })
            
            return signals
        except Exception as e:
            logger.error(f"Reddit RapidAPI error: {e}. Falling back to public API.")
            return await self._fetch_public(query, limit)

    async def _fetch_public(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            url = f"https://www.reddit.com/search.json?q={query}&sort=new&limit={limit}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            signals = []
            for post in data.get("data", {}).get("children", []):
                item = post["data"]
                created_at = datetime.fromtimestamp(item.get("created_utc", datetime.utcnow().timestamp())).isoformat()
                signals.append({
                    "source_id": f"rd-{item['id']}",
                    "source_type": "social",
                    "platform": "reddit",
                    "text": f"{item['title']}\n{item.get('selftext', '')[:1000]}",
                    "likes": item.get("ups", 0),
                    "shares": item.get("num_crossposts", 0),
                    "comments": item.get("num_comments", 0),
                    "views": int(item.get("ups", 0) * random.uniform(20, 50)) + item.get("num_comments", 0) * 10,
                    "timestamp": created_at,
                    "author_metadata": {"subreddit": item.get("subreddit_name_prefixed"), "author": item.get("author")}
                })
            return signals
        except: return []

class InstagramScraper(BaseScraper):
    """
    Real-time Instagram scraper using RapidAPI (instagram120).
    """
    def __init__(self):
        super().__init__("instagram")
        self.api_url = "https://instagram120.p.rapidapi.com/api/instagram/posts"

    async def fetch_signals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not settings.rapidapi_key or settings.rapidapi_key == "your_rapidapi_key":
            logger.error("RapidAPI Key not configured in .env for Instagram scraping.")
            return []
            
        try:
            # The instagram120 API uses a POST request with username
            headers = {
                "x-rapidapi-host": "instagram120.p.rapidapi.com",
                "x-rapidapi-key": settings.rapidapi_key,
                "Content-Type": "application/json"
            }
            # We treat the brand query as a username for this specific API
            payload = {
                "username": query.replace(" ", ""),
                "maxId": ""
            }
            
            response = await self.client.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Instagram RapidAPI failed with status {response.status_code}: {response.text}")
                return []
                
            data = response.json()
            
            signals = []
            # Mapping logic based on the provided sample JSON for instagram120
            # Structure: data['result']['edges'] -> edge['node']
            edges = data.get("result", {}).get("edges", [])
            
            items = []
            if edges:
                items = [edge.get("node", {}) for edge in edges if edge.get("node")]
            else:
                # Fallback for other common Instagram API structures
                items = data.get("items", []) or data.get("data", {}).get("items", [])

            for item in items[:limit]:
                # Safely extract caption text (handle cases where caption is None)
                caption = item.get("caption") or {}
                text = caption.get("text", "") if isinstance(caption, dict) else ""
                
                # RapidAPI provides a 'pk' or 'id'
                post_id = item.get("pk") or item.get("id") or str(random.randint(1000, 9999))
                
                # Metrics match the sample: comment_count, like_count, view_count
                signals.append({
                    "source_id": f"ig-{post_id}",
                    "source_type": "social",
                    "platform": "instagram",
                    "text": text,
                    "likes": item.get("like_count", 0),
                    "shares": item.get("reshare_count", 0),  # Not explicitly in sample, keeping as metric
                    "comments": item.get("comment_count", 0),
                    "views": item.get("view_count", 0) or (item.get("like_count", 0) * 15),
                    "timestamp": datetime.fromtimestamp(item.get("taken_at", datetime.utcnow().timestamp())).isoformat(),
                    "author_metadata": {
                        "username": item.get("user", {}).get("username"),
                        "is_verified": item.get("user", {}).get("is_verified"),
                        "full_name": item.get("user", {}).get("full_name")
                    },
                    "raw_data": item  # Store the full node for future parsing if needed
                })
            return signals
        except Exception as e:
            logger.error(f"Instagram RapidAPI error: {e}")
            return []

class QuoraScraper(BaseScraper):
    """
    Real-time Quora scraper using RapidAPI (quora-api).
    """
    def __init__(self):
        super().__init__("quora")
        self.api_url = "https://quora-api.p.rapidapi.com/search"

    async def fetch_signals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not settings.rapidapi_key or settings.rapidapi_key == "your_rapidapi_key":
            logger.error("RapidAPI Key not configured in .env for Quora scraping.")
            return []

        try:
            headers = {
                "x-rapidapi-host": "quora-api.p.rapidapi.com",
                "x-rapidapi-key": settings.rapidapi_key
            }
            params = {"query": query}
            response = await self.client.get(self.api_url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"Quora RapidAPI failed with status {response.status_code}: {response.text}")
                # Fallback to public web scraping if RapidAPI fails
                return await self._scrape_quora_web(query, limit)

            data = response.json()
            signals = []
            
            # Mapping logic for quora-api (placeholder structure)
            items = data.get("data", []) or data.get("items", [])
            for item in items[:limit]:
                signals.append({
                    "source_id": f"qr-{item.get('id', random.randint(1000, 9999))}",
                    "source_type": "social",
                    "platform": "quora",
                    "text": item.get("text", "") or item.get("title", ""),
                    "likes": item.get("upvotes", 0),
                    "shares": item.get("shares", 0),
                    "comments": item.get("comments_count", 0),
                    "views": item.get("views", 0),
                    "timestamp": item.get("created_at", datetime.utcnow().isoformat()),
                    "author_metadata": {
                        "author": item.get("author", {}).get("name", "anonymous")
                    },
                    "raw_data": item
                })
            return signals

        except Exception as e:
            logger.error(f"Quora RapidAPI error: {e}. Falling back to web scraping.")
            return await self._scrape_quora_web(query, limit)

    async def _scrape_quora_web(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Attempt to scrape Quora using public search URL."""
        try:
            search_url = f"https://www.quora.com/search?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            response = await self.client.get(search_url, headers=headers)
            
            if response.status_code != 200 or "Login" in response.text:
                return []
                
            # Basic parsing logic would go here if needed
            return [] 
        except Exception:
            return []

class ScraperFactory:
    @staticmethod
    def get_scraper(platform: str) -> BaseScraper:
        scrapers = {
            "twitter": TwitterScraper,
            "reddit": RedditScraper,
            "instagram": InstagramScraper,
            "quora": QuoraScraper
        }
        scraper_class = scrapers.get(platform)
        if scraper_class:
            return scraper_class()
        raise ValueError(f"Unknown platform: {platform}")


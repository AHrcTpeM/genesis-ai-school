"""Wikimedia Analytics API Client with local caching and bot-traffic comparison.

Follows Wikimedia Foundation User-Agent and Access policies:
https://meta.wikimedia.org/wiki/User-Agent_policy
"""

import hashlib
import json
import logging
import os
import time
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "WikipediaMarketInsightsSkill/1.0 (https://agentskills.io; contact@agentskills.io)"
BASE_API_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")


class WikimediaClient:
    """Client for Wikimedia Analytics Pageviews API with caching."""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, cache_ttl_seconds: int = 86400):
        self.cache_dir = cache_dir
        self.cache_ttl_seconds = cache_ttl_seconds
        os.makedirs(self.cache_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })

    def close(self):
        """Close HTTP session."""
        if hasattr(self, "session") and self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_cache_path(self, url: str) -> str:
        """Generate deterministic cache file path for a URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")

    def _fetch_with_cache(self, url: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Fetch URL with local file cache and exponential backoff retry."""
        cache_path = self._get_cache_path(url)

        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                cached_time = cached_data.get("_cached_at", 0)
                # If cache is valid or data is purely historical, return cached
                if (time.time() - cached_time) < self.cache_ttl_seconds:
                    return cached_data.get("data")
            except Exception as e:
                logger.warning(f"Error reading cache at {cache_path}: {e}")

        # Execute HTTP request with polite retry
        retries = 3
        backoff = 1.0
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump({"_cached_at": time.time(), "url": url, "data": data}, f)
                    except Exception as e:
                        logger.warning(f"Could not write cache to {cache_path}: {e}")
                    return data
                elif resp.status_code == 404:
                    # Article not found or no views recorded
                    return None
                elif resp.status_code in (429, 503):
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.warning(f"HTTP error {resp.status_code} for URL: {url}")
                    return None
            except requests.RequestException as e:
                if attempt == retries - 1:
                    logger.error(f"Network error fetching {url}: {e}")
                    return None
                time.sleep(backoff)
                backoff *= 2
        return None

    def get_article_pageviews(
        self,
        project: str,
        article: str,
        start: str,
        end: str,
        granularity: str = "monthly",
        access: str = "all-access",
        agent: str = "user",
    ) -> List[Dict[str, Any]]:
        """Fetch per-article pageviews.

        Args:
            project: e.g. 'uk.wikipedia.org' or 'uk.wikipedia'
            article: Article title (e.g. 'Астрономія' or 'Intermittent_fasting')
            start: Start date string 'YYYYMMDD'
            end: End date string 'YYYYMMDD'
            granularity: 'monthly' or 'daily'
            access: 'all-access', 'desktop', 'mobile-app', 'mobile-web'
            agent: 'user' (human), 'spider' (crawlers), 'bot', or 'all-agents'

        Returns:
            List of item dicts with timestamp, views, etc.
        """
        # Ensure project has no .org suffix if passed with it
        proj = project.replace(".org", "")
        # Sanitize article title: replace spaces with underscores and quote URL
        sanitized_article = urllib.parse.quote(article.replace(" ", "_"), safe="")
        url = f"{BASE_API_URL}/per-article/{proj}/{access}/{agent}/{sanitized_article}/{granularity}/{start}/{end}"
        res = self._fetch_with_cache(url)
        if not res or "items" not in res:
            return []
        return res.get("items", [])

    def get_project_aggregate_views(
        self,
        project: str,
        start: str,
        end: str,
        granularity: str = "monthly",
        access: str = "all-access",
        agent: str = "user",
    ) -> List[Dict[str, Any]]:
        """Fetch aggregate total pageviews for an entire project (e.g. uk.wikipedia).

        Used for market baseline normalization (e.g. views per million project views).
        """
        proj = project.replace(".org", "")
        url = f"{BASE_API_URL}/aggregate/{proj}/{access}/{agent}/{granularity}/{start}/{end}"
        res = self._fetch_with_cache(url)
        if not res or "items" not in res:
            return []
        return res.get("items", [])

    def get_article_traffic_breakdown(
        self,
        project: str,
        article: str,
        start: str,
        end: str,
        granularity: str = "monthly",
    ) -> Dict[str, Any]:
        """Fetch both human ('user') and crawler ('spider') pageviews to measure bot ratio."""
        user_items = self.get_article_pageviews(
            project=project, article=article, start=start, end=end, granularity=granularity, agent="user"
        )
        spider_items = self.get_article_pageviews(
            project=project, article=article, start=start, end=end, granularity=granularity, agent="spider"
        )

        user_views = sum(it.get("views", 0) for it in user_items)
        spider_views = sum(it.get("views", 0) for it in spider_items)
        total_combined = user_views + spider_views
        spider_ratio = (spider_views / total_combined) if total_combined > 0 else 0.0

        return {
            "project": project,
            "article": article,
            "user_items": user_items,
            "spider_items": spider_items,
            "total_user_views": user_views,
            "total_spider_views": spider_views,
            "spider_ratio": spider_ratio,
        }

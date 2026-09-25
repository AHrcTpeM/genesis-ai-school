"""Multi-language Topic & Article Resolver using MediaWiki and Wikidata APIs.

Resolves concept titles across Wikipedia language editions, follows redirects,
detects missing articles using Wikidata sitelinks, and finds relevant candidate topics.
"""

from reportlab.lib import styles
from reportlab.lib import styles
from reportlab.lib import styles
import json
import logging
import os
import urllib.parse
from typing import Any, Dict, List, Optional
import requests

try:
    from .wikimedia_client import DEFAULT_CACHE_DIR, USER_AGENT
except ImportError:
    from wikimedia_client import DEFAULT_CACHE_DIR, USER_AGENT

logger = logging.getLogger(__name__)


class TopicResolver:
    """Resolves topics across language editions of Wikipedia using MediaWiki and Wikidata."""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.cache_dir = cache_dir
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

    def _api_get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cached GET helper for MediaWiki/Wikidata API."""
        query_string = urllib.parse.urlencode(sorted(params.items()))
        full_url = f"{url}?{query_string}"
        cache_key = f"mw_{abs(hash(full_url))}.json"
        cache_file = os.path.join(self.cache_dir, cache_key)

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            # === [DEBUG TEMP PRINT REQUEST] ===
            print(f"\n[API REQUEST] GET {url}")
            print(f"[API REQUEST PARAMS] {json.dumps(params, ensure_ascii=False)}")
            # === [END DEBUG TEMP PRINT] ===

            resp = self.session.get(url, params=params, timeout=12)

            # === [DEBUG TEMP PRINT RESPONSE STATUS] ===
            print(f"[API RESPONSE STATUS] {resp.status_code} for {url}")
            # === [END DEBUG TEMP PRINT] ===

            if resp.status_code == 200:
                data = resp.json()

                # === [DEBUG TEMP PRINT RESPONSE DATA] ===
                print(f"[API RESPONSE DATA] {json.dumps(data, ensure_ascii=False)[:300]}...")
                # === [END DEBUG TEMP PRINT] ===

                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass
                return data
        except Exception as e:
            logger.warning(f"Error calling {url}: {e}")
        return None

    def verify_article_exists(self, lang: str, title: str) -> Dict[str, Any]:
        """Check if article exists on {lang}.wikipedia.org, following redirects."""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "format": "json",
        }
        res = self._api_get(url, params)
        if not res or "query" not in res:
            return {"exists": False, "canonical_title": title, "pageid": None}

        pages = res["query"].get("pages", {})
        for page_id, page_info in pages.items():
            if str(page_id) == "-1" or "missing" in page_info:
                return {"exists": False, "canonical_title": title, "pageid": None}
            canonical_title = page_info.get("title", title)
            return {"exists": True, "canonical_title": canonical_title, "pageid": int(page_id)}

        return {"exists": False, "canonical_title": title, "pageid": None}

    def search_articles(self, lang: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Wikipedia in a given language for candidate topics."""
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }
        res = self._api_get(url, params)
        if not res or "query" not in res:
            return []
        hits = res["query"].get("search", [])
        return [{"title": h["title"], "pageid": h["pageid"], "snippet": h.get("snippet", "")} for h in hits]

    def get_wikidata_sitelinks(self, source_lang: str, title: str) -> Dict[str, str]:
        """Fetch Wikidata sitelinks and langlinks for a concept."""
        # 1. Get wikibase_item (QID) from Wikipedia article pageprops
        url = f"https://{source_lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "prop": "pageprops|langlinks",
            "lllimit": "500",
            "redirects": "1",
            "format": "json",
        }
        res = self._api_get(url, params)
        sitelinks: Dict[str, str] = {}
        qid = None

        if res and "query" in res:
            pages = res["query"].get("pages", {})
            for page in pages.values():
                if "missing" in page or str(page.get("pageid", "-1")) == "-1":
                    continue
                # Extract langlinks
                for ll in page.get("langlinks", []):
                    l_code = ll.get("lang")
                    l_title = ll.get("*")
                    if l_code and l_title:
                        sitelinks[l_code] = l_title
                # Extract QID
                qid = page.get("pageprops", {}).get("wikibase_item")

        # 2. If QID found, query Wikidata for complete sitelinks
        if qid:
            wd_url = "https://www.wikidata.org/w/api.php"
            wd_params = {
                "action": "wbgetentities",
                "ids": qid,
                "props": "sitelinks",
                "format": "json",
            }
            wd_res = self._api_get(wd_url, wd_params)
            if wd_res and "entities" in wd_res:
                entity = wd_res["entities"].get(qid, {})
                for site_key, site_val in entity.get("sitelinks", {}).items():
                    if site_key.endswith("wiki"):
                        code = site_key[:-4]
                        sitelinks[code] = site_val.get("title")

        return sitelinks

    def resolve_topic_for_languages(
        self,
        topic: str,
        target_langs: List[str],
        source_lang: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Resolve a topic across target language editions with concept validation.

        Returns:
            Dict keyed by language code:
              - 'title': canonical title (or None if missing)
              - 'exists': bool
              - 'method': 'direct_match', 'wikidata_sitelink', 'missing_no_page'
              - 'closest_candidates': list of related titles
              - 'notes': clear commentary on concept availability
        """
        results: Dict[str, Dict[str, Any]] = {}

        # 1. Identify primary source languages
        candidate_sources = []
        if source_lang:
            candidate_sources.append(source_lang)
        if any(ord(c) > 1000 for c in topic):
            candidate_sources.extend(["uk", "ru", "en"])
        else:
            candidate_sources.extend(["en", "uk"])

        sitelinks: Optional[Dict[str, str]] = None

        for lang in target_langs:
            # Case 1: Topic directly exists in target language
            direct_check = self.verify_article_exists(lang, topic)
            if direct_check["exists"]:
                results[lang] = {
                    "title": direct_check["canonical_title"],
                    "exists": True,
                    "method": "direct_match",
                    "closest_candidates": [],
                    "notes": f"Exact article '{direct_check['canonical_title']}' exists on {lang}.wikipedia.",
                }
                continue

            # Fetch Wikidata sitelinks lazily only if Case 1 failed and sitelinks not fetched yet
            if sitelinks is None:
                sitelinks = {}
                for src in candidate_sources:
                    links = self.get_wikidata_sitelinks(src, topic)
                    if links:
                        sitelinks = links
                        break

            # Case 2: Sitelink exists in Wikidata / interlanguage links
            if lang in sitelinks:
                target_title = sitelinks[lang]
                verify = self.verify_article_exists(lang, target_title)
                if verify["exists"]:
                    results[lang] = {
                        "title": verify["canonical_title"],
                        "exists": True,
                        "method": "wikidata_sitelink",
                        "closest_candidates": [],
                        "notes": f"Resolved via Wikidata/langlink as '{verify['canonical_title']}' on {lang}.wikipedia.",
                    }
                    continue

            # Case 3: Concept does NOT have a direct dedicated page on target wiki
            # Search for candidate or related articles
            search_hits = self.search_articles(lang, topic, limit=5)
            candidate_titles = [h["title"] for h in search_hits]

            results[lang] = {
                "title": None,
                "exists": False,
                "method": "missing_no_page",
                "closest_candidates": candidate_titles,
                "notes": (
                    f"No dedicated article for '{topic}' found on {lang}.wikipedia. "
                    f"Topic may be covered under related subjects. "
                    f"Closest related search candidates: {', '.join(candidate_titles[:3]) if candidate_titles else 'None'}."
                ),
            }

        return results

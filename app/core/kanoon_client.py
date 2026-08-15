"""
KanoonRAG — Kanoon API Client (Offline Only)

Async wrapper for the Indian Kanoon API. Used ONLY by scripts/seed_kanoon.py
to pre-fetch the case law corpus. Never imported or called at runtime.

Implements:
- Caching: every response saved as JSON to data/kanoon_cache/
- Rate limiting: configurable delay between API calls
- Proper URL-path based endpoints per Kanoon API spec
"""

import json
import asyncio
import hashlib
import httpx
from pathlib import Path
from typing import Dict, Any, Optional

import config


class KanoonClient:
    """Offline-only Kanoon API client."""

    def __init__(self):
        self.base_url = config.KANOON_API_BASE
        self.headers = {
            "Authorization": f"Token {config.KANOON_API_TOKEN}",
            "Accept": "application/json",
        }
        self.cache_dir = Path(config.KANOON_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, cache_key: str) -> Path:
        """Return the cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"

    async def _fetch_with_cache(
        self,
        url: str,
        params: Optional[Dict] = None,
        cache_key: Optional[str] = None,
        method: str = "POST",
    ) -> Dict[str, Any]:
        """Fetch data from API or load from cache if available."""
        if not cache_key:
            key_str = f"{url}_{json.dumps(params, sort_keys=True)}"
            cache_key = hashlib.md5(key_str.encode()).hexdigest()

        cache_path = self._get_cache_path(cache_key)

        # Return cached response if available
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Rate limit
        await asyncio.sleep(config.KANOON_RATE_LIMIT_DELAY)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "POST":
                response = await client.post(url, headers=self.headers, data=params)
            else:
                response = await client.get(url, headers=self.headers, params=params)

            response.raise_for_status()
            data = response.json()

            # Cache the response
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return data

    async def search(
        self,
        query: str,
        doctypes: str,
        pagenum: int = 0,
        maxpages: int = 1,
    ) -> Dict[str, Any]:
        """
        Search the Kanoon API.

        Uses the /search/ endpoint with formInput containing the query
        and doctypes filter.
        """
        url = f"{self.base_url}/search/"
        full_query = f"{query} doctypes:{doctypes}"
        params = {
            "formInput": full_query,
            "pagenum": str(pagenum),
        }
        cache_key = hashlib.md5(
            f"search_{full_query}_{pagenum}".encode()
        ).hexdigest()
        return await self._fetch_with_cache(url, params, cache_key)

    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Fetch the full document by ID.

        Uses the /doc/<docid>/ endpoint.
        """
        url = f"{self.base_url}/doc/{doc_id}/"
        return await self._fetch_with_cache(
            url, params=None, cache_key=f"doc_{doc_id}", method="POST"
        )

    async def get_doc_metadata(self, doc_id: str) -> Dict[str, Any]:
        """
        Fetch document metadata by ID.

        Uses the /docmeta/<docid>/ endpoint.
        """
        url = f"{self.base_url}/docmeta/{doc_id}/"
        return await self._fetch_with_cache(
            url, params=None, cache_key=f"meta_{doc_id}", method="POST"
        )

import logging
from typing import Optional, Dict, Any, List

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class JikanRateLimited(Exception):
    pass


class JikanService:
    BASE_URL = "https://api.jikan.moe/v4"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    @retry(
        retry=retry_if_exception_type(JikanRateLimited),
        wait=wait_exponential(multiplier=0.7, min=1, max=12),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = await self.client.get(f"{self.BASE_URL}{path}", params=params)
        if response.status_code == 429:
            logger.warning("Jikan API rate limited for path=%s", path)
            raise JikanRateLimited()
        response.raise_for_status()
        return response.json()

    async def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        try:
            payload = await self._request(f"/anime/{mal_id}/full")
            return payload.get("data")
        except Exception as e:
            logger.error("Error fetching anime %s: %s", mal_id, e)
            return None

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        try:
            payload = await self._request("/anime", params={"q": query, "limit": 5})
            return payload.get("data", [])
        except Exception as e:
            logger.error("Error searching anime %s: %s", query, e)
            return []


jikan_service = JikanService()

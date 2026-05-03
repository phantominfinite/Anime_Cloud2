import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class JikanService:
    BASE_URL = "https://api.jikan.moe/v4"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.BASE_URL}/anime/{mal_id}/full")
            if response.status_code == 200:
                return response.json().get("data")
            elif response.status_code == 429:
                logger.warning("Jikan API Rate Limit Hit")
                return None
            else:
                logger.error(f"Jikan API Error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching anime {mal_id}: {e}")
            return None

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.BASE_URL}/anime", params={"q": query, "limit": 5})
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                logger.error(f"Jikan Search Error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error searching anime {query}: {e}")
            return []

jikan_service = JikanService()

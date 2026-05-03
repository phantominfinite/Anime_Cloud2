import json
import logging
import asyncio
import time
from typing import Optional, Any, Dict, List, Tuple
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class MockRedis:
    """In-memory Redis mock for development/fallback."""
    def __init__(self):
        self.store: Dict[str, str] = {}
        self.expirations: Dict[str, float] = {}
        self.zsets: Dict[str, Dict[str, float]] = {} # key -> {member: score}
        self._loop = asyncio.get_event_loop()

    async def get(self, key: str) -> Optional[str]:
        if key in self.expirations:
            if self.expirations[key] < self._loop.time():
                del self.store[key]
                del self.expirations[key]
                return None
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        self.store[key] = value
        if ex:
            self.expirations[key] = self._loop.time() + ex

    async def delete(self, key: str):
        if key in self.store: del self.store[key]
        if key in self.expirations: del self.expirations[key]
        if key in self.zsets: del self.zsets[key]

    async def zadd(self, key: str, mapping: Dict[str, float]):
        if key not in self.zsets:
            self.zsets[key] = {}
        self.zsets[key].update(mapping)

    async def zpopmin(self, key: str, count: int = 1) -> List[Tuple[str, float]]:
        if key not in self.zsets or not self.zsets[key]:
            return []
        
        # Sort by score
        sorted_members = sorted(self.zsets[key].items(), key=lambda item: item[1])
        popped = sorted_members[:count]
        
        # Remove popped
        for member, _ in popped:
            del self.zsets[key][member]
            
        return popped

    async def close(self):
        pass
    async def ping(self):
        return True

class RedisCacheService:
    def __init__(self):
        self.redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        self.client: Any = None
        self.is_mock = False

    async def connect(self):
        if self.client:
            return

        try:
            client = redis.from_url(
                self.redis_url, 
                encoding="utf-8", 
                decode_responses=True,
                socket_connect_timeout=1
            )
            await client.ping()
            self.client = client
            self.is_mock = False
            logger.info(f"Connected to Real Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Switching to In-Memory Mock.")
            self.client = MockRedis()
            self.is_mock = True

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.client: await self.connect()
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error(f"Redis GET error key={key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 300):
        if not self.client: await self.connect()
        try:
            val_str = json.dumps(value)
            await self.client.set(key, val_str, ex=expire)
        except Exception as e:
            logger.error(f"Redis SET error key={key}: {e}")

    async def delete(self, key: str):
        if not self.client: await self.connect()
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DEL error key={key}: {e}")

    # --- Sorted Sets for LRU Cache ---
    
    async def update_access(self, file_path: str):
        """Update last accessed time for a file in Redis ZSET."""
        if not self.client: await self.connect()
        try:
            # ZSET key: "cache_access_log"
            # Member: file_path
            # Score: current timestamp
            current_time = time.time()
            await self.client.zadd("cache_access_log", {file_path: current_time})
        except Exception as e:
             logger.error(f"Redis ZADD error: {e}")

    async def get_coldest_files(self, count: int = 10) -> List[str]:
        """Get 'count' oldest accessed files from ZSET."""
        if not self.client: await self.connect()
        try:
            # ZPOPMIN removes and returns members with lowest scores
            items = await self.client.zpopmin("cache_access_log", count)
            # items is list of (member, score) tuples
            return [item[0] for item in items]
        except Exception as e:
            logger.error(f"Redis ZPOPMIN error: {e}")
            return []

redis_service = RedisCacheService()

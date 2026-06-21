from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import os
import shutil
import time
from typing import AsyncIterator

import aiofiles
import redis.asyncio as redis

from app.core.config import settings
from app.services.redis_cache import redis_service

logger = logging.getLogger(__name__)


class RedisDistributedLock:
    """Minimal Redis lock wrapper with explicit token ownership checks, falling back to local lock if Redis is down."""
    _local_locks = {}
    _local_locks_lock = asyncio.Lock()

    def __init__(self, client: redis.Redis, name: str, timeout: int = 30, blocking_timeout: float = 10.0):
        self.name = name
        self._lock = client.lock(name=name, timeout=timeout, blocking_timeout=blocking_timeout, thread_local=False)
        self._fallback_lock = None

    async def __aenter__(self):
        try:
            await self._lock.acquire()
        except Exception as e:
            # Fallback to local asyncio lock if Redis is offline
            logger.warning("Redis is unavailable for lock '%s'; falling back to local lock: %s", self.name, e)
            async with self._local_locks_lock:
                if self.name not in self._local_locks:
                    self._local_locks[self.name] = asyncio.Lock()
                self._fallback_lock = self._local_locks[self.name]
            await self._fallback_lock.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._fallback_lock:
            try:
                self._fallback_lock.release()
            except RuntimeError:
                pass
        else:
            with contextlib.suppress(Exception):
                await self._lock.release()


class CacheService:
    """On-disk chunk cache with Redis-backed distributed locks + Redis LRU metadata."""

    def __init__(self):
        self.cache_dir = settings.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

        self._evict_local_lock = asyncio.Lock()
        self._last_size_check = 0.0
        self._size_check_interval_seconds = 15.0
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=False)

    def _lock_for_path(self, path: str, op: str, timeout: int = 30) -> RedisDistributedLock:
        digest = hashlib.sha1(f"{op}:{path}".encode()).hexdigest()
        return RedisDistributedLock(self._redis, f"lock:cache:{digest}", timeout=timeout)

    async def _get_chunk_path(self, file_id: str, chunk_index: int) -> str:
        safe_file_id = hashlib.md5(file_id.encode()).hexdigest()
        file_dir = os.path.join(self.cache_dir, safe_file_id)
        await asyncio.to_thread(os.makedirs, file_dir, exist_ok=True)
        return os.path.join(file_dir, str(chunk_index))

    async def exists(self, file_id: str, chunk_index: int) -> bool:
        path = await self._get_chunk_path(file_id, chunk_index)
        return await asyncio.to_thread(os.path.exists, path)

    async def get_chunk(self, file_id: str, chunk_index: int) -> bytes | None:
        path = await self._get_chunk_path(file_id, chunk_index)
        if not await asyncio.to_thread(os.path.exists, path):
            return None

        try:
            async with self._lock_for_path(path, "read", timeout=10):
                if not await asyncio.to_thread(os.path.exists, path):
                    return None
                asyncio.create_task(redis_service.update_access(path))
                async with aiofiles.open(path, mode="rb") as f:
                    return await f.read()
        except Exception as e:
            logger.error("Error reading cache for %s/%s: %s", file_id, chunk_index, e)
            return None

    async def save_chunk(self, file_id: str, chunk_index: int, data: bytes):
        path = await self._get_chunk_path(file_id, chunk_index)
        temp_path = f"{path}.tmp"
        try:
            async with self._lock_for_path(path, "write", timeout=20):
                async with aiofiles.open(temp_path, mode="wb") as f:
                    await f.write(data)
                await asyncio.to_thread(os.replace, temp_path, path)
                asyncio.create_task(redis_service.update_access(path))

                now = time.monotonic()
                if now - self._last_size_check >= self._size_check_interval_seconds:
                    self._last_size_check = now
                    asyncio.create_task(self._check_cache_size())
        except Exception as e:
            logger.error("Error writing cache for %s/%s: %s", file_id, chunk_index, e)
            with contextlib.suppress(Exception):
                if await asyncio.to_thread(os.path.exists, temp_path):
                    await asyncio.to_thread(os.remove, temp_path)

    async def _check_cache_size(self):
        if self._evict_local_lock.locked():
            return
        async with self._evict_local_lock:
            # Global process-safe lock: only one worker performs eviction.
            async with self._lock_for_path("global-eviction", "evict", timeout=45):
                max_size = int(getattr(settings, "CACHE_MAX_BYTES", 2 * 1024 * 1024 * 1024))
                total_size = await self._get_total_size()
                if total_size <= max_size:
                    return
                logger.info("Cache size %s exceeds limit %s, starting eviction", total_size, max_size)

                while total_size > max_size:
                    candidates = await redis_service.get_coldest_files(count=50)
                    if not candidates:
                        break
                    for fp in candidates:
                        if not await asyncio.to_thread(os.path.exists, fp):
                            continue
                        try:
                            async with self._lock_for_path(fp, "write", timeout=8):
                                if await asyncio.to_thread(os.path.exists, fp):
                                    size = await asyncio.to_thread(os.path.getsize, fp)
                                    await asyncio.to_thread(os.remove, fp)
                                    total_size -= size
                                    if total_size <= max_size:
                                        break
                        except Exception as e:
                            logger.warning("Failed to evict %s: %s", fp, e)

    async def _get_total_size(self) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_get_size)

    def _sync_get_size(self) -> int:
        total_size = 0
        for root, _dirs, files in os.walk(self.cache_dir):
            for f in files:
                fp = os.path.join(root, f)
                with contextlib.suppress(Exception):
                    total_size += os.path.getsize(fp)
        return total_size

    async def clear_cache(self):
        with contextlib.suppress(Exception):
            await asyncio.to_thread(shutil.rmtree, self.cache_dir)
        await asyncio.to_thread(os.makedirs, self.cache_dir, exist_ok=True)


cache_service = CacheService()

from __future__ import annotations

import os
import aiofiles
import logging
import hashlib
import shutil
import asyncio
import time
from app.core.config import settings
from app.services.redis_cache import redis_service

logger = logging.getLogger(__name__)


class CacheService:
    """On-disk chunk cache with Redis-backed LRU eviction (best-effort).

    Design goals:
    - Atomic writes (temp file + rename)
    - Best-effort LRU eviction when size exceeds CACHE_MAX_BYTES
    - Avoid running multiple expensive size scans at the same time
    """

    def __init__(self):
        self.cache_dir = settings.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

        self._evict_lock = asyncio.Lock()
        self._last_size_check = 0.0
        self._size_check_interval_seconds = 15.0  # throttle expensive scans

    def _get_chunk_path(self, file_id: str, chunk_index: int) -> str:
        # Hashing file_id to avoid directory traversal or long names
        safe_file_id = hashlib.md5(file_id.encode()).hexdigest()

        file_dir = os.path.join(self.cache_dir, safe_file_id)
        os.makedirs(file_dir, exist_ok=True)
        return os.path.join(file_dir, str(chunk_index))

    async def exists(self, file_id: str, chunk_index: int) -> bool:
        path = self._get_chunk_path(file_id, chunk_index)
        return os.path.exists(path)

    async def get_chunk(self, file_id: str, chunk_index: int) -> bytes | None:
        path = self._get_chunk_path(file_id, chunk_index)
        if os.path.exists(path):
            try:
                # Update Redis Access Log (fire-and-forget)
                asyncio.create_task(redis_service.update_access(path))
                async with aiofiles.open(path, mode="rb") as f:
                    return await f.read()
            except Exception as e:
                logger.error(f"Error reading cache for {file_id}/{chunk_index}: {e}")
                return None
        return None

    async def save_chunk(self, file_id: str, chunk_index: int, data: bytes):
        path = self._get_chunk_path(file_id, chunk_index)
        temp_path = f"{path}.tmp"
        try:
            # Atomic write pattern: write to temp then rename
            async with aiofiles.open(temp_path, mode="wb") as f:
                await f.write(data)
            os.replace(temp_path, path)

            # Update Redis Access Log (fire-and-forget)
            asyncio.create_task(redis_service.update_access(path))

            # Throttle heavy scans
            now = time.monotonic()
            if now - self._last_size_check >= self._size_check_interval_seconds:
                self._last_size_check = now
                asyncio.create_task(self._check_cache_size())

        except Exception as e:
            logger.error(f"Error writing cache for {file_id}/{chunk_index}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    async def _check_cache_size(self):
        if self._evict_lock.locked():
            return

        async with self._evict_lock:
            max_size = int(getattr(settings, "CACHE_MAX_BYTES", 2 * 1024 * 1024 * 1024))
            try:
                total_size = await self._get_total_size()
                if total_size <= max_size:
                    return

                logger.info(f"Cache size {total_size} exceeds limit {max_size}. Evicting...")

                # Evict in batches until under limit (or until we run out of candidates)
                while total_size > max_size:
                    eviction_candidates = await redis_service.get_coldest_files(count=50)
                    if not eviction_candidates:
                        break

                    for fp in eviction_candidates:
                        try:
                            if os.path.exists(fp):
                                size = os.path.getsize(fp)
                                os.remove(fp)
                                total_size -= size
                        except Exception as e:
                            logger.warning(f"Failed to delete {fp}: {e}")

            except Exception as e:
                logger.error(f"Error checking cache size: {e}")

    async def _get_total_size(self) -> int:
        # Potentially slow if millions of files, so run in executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_get_size)

    def _sync_get_size(self) -> int:
        total_size = 0
        for root, _dirs, files in os.walk(self.cache_dir):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                except Exception:
                    pass
        return total_size

    async def clear_cache(self):
        """Clears the entire cache."""
        try:
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


cache_service = CacheService()

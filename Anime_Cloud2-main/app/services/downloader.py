import asyncio
import hashlib
import logging
from typing import Dict, Tuple, Optional, List

import redis.asyncio as redis
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId
from pyrogram.raw.functions.upload import GetFile

from app.core.config import settings
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


class SmartDownloader:
    def __init__(self, clients: List[Client], chunk_size: int = 1024 * 1024):
        self.clients = clients
        self._current_client_idx = 0
        self.chunk_size = chunk_size
        self.pending_chunks: Dict[Tuple[str, int], asyncio.Future] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max(5, len(clients) * 4))
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=False)

    def _get_next_client(self) -> Client:
        if not self.clients:
            raise RuntimeError("No Telegram clients configured")
        client = self.clients[self._current_client_idx]
        self._current_client_idx = (self._current_client_idx + 1) % len(self.clients)
        return client

    def _download_lock_key(self, file_id: str, chunk_index: int) -> str:
        digest = hashlib.sha1(f"{file_id}:{chunk_index}".encode()).hexdigest()
        return f"lock:download:{digest}"

    async def get_chunk(self, file_id: str, chunk_index: int) -> Optional[bytes]:
        data = await cache_service.get_chunk(file_id, chunk_index)
        if data:
            if not hasattr(self, "_background_tasks"):
                self._background_tasks = set()
            task = asyncio.create_task(self.prefetch_chunks(file_id, chunk_index + 1))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return data

        future = await self._get_or_create_future(file_id, chunk_index)
        try:
            await future
        except Exception:
            return None

        data = await cache_service.get_chunk(file_id, chunk_index)
        if data:
            if not hasattr(self, "_background_tasks"):
                self._background_tasks = set()
            task = asyncio.create_task(self.prefetch_chunks(file_id, chunk_index + 1))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        return data

    async def prefetch_chunks(self, file_id: str, start_index: int, count: int = 3):
        for i in range(count):
            idx = start_index + i
            if await cache_service.exists(file_id, idx):
                continue
            await self._get_or_create_future(file_id, idx)

    async def _get_or_create_future(self, file_id: str, chunk_index: int) -> asyncio.Future:
        async with self._lock:
            key = (file_id, chunk_index)
            if key in self.pending_chunks:
                return self.pending_chunks[key]
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self.pending_chunks[key] = future

            async def run_worker():
                try:
                    await self._download_worker(file_id, chunk_index, future)
                except Exception as e:
                    logger.error(f"Worker failed: {e}")
                    if not future.done():
                        future.set_exception(e)

            # create_task does not save a strong reference, so we will assign it to an attribute
            # to avoid the "task was destroyed but it is pending" warning and garbage collection.
            if not hasattr(self, "_background_tasks"):
                self._background_tasks = set()
            task = asyncio.create_task(run_worker())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return future

    async def _download_worker(self, file_id: str, chunk_index: int, future: asyncio.Future):
        max_retries = 5
        redis_lock = self._redis.lock(self._download_lock_key(file_id, chunk_index), timeout=45, blocking_timeout=15, thread_local=False)
        try:
            for attempt in range(max_retries):
                try:
                    async with self._semaphore:
                        if await cache_service.exists(file_id, chunk_index):
                            if not future.done():
                                future.set_result(True)
                            return

                        use_fallback = False
                        try:
                            acquired = await redis_lock.acquire()
                        except Exception as e:
                            logger.warning("Redis lock acquire failed (Redis offline?), falling back to local lock: %s", e)
                            acquired = True
                            use_fallback = True

                        if not acquired:
                            await asyncio.sleep(0.25)
                            continue
                        try:
                            if await cache_service.exists(file_id, chunk_index):
                                if not future.done():
                                    future.set_result(True)
                                return

                            client = self._get_next_client()
                            offset = chunk_index * self.chunk_size
                            decoded = FileId.decode(file_id)
                            location = decoded.file_type.location(
                                id=decoded.media_id,
                                access_hash=decoded.access_hash,
                                file_reference=decoded.file_reference,
                            )
                            r = await client.invoke(GetFile(location=location, offset=offset, limit=self.chunk_size))
                            await cache_service.save_chunk(file_id, chunk_index, r.bytes)
                        except Exception as e:
                            # If FILEREF_EXPIRED or similar MTProto error occurs, catch it
                            if "FILE_REFERENCE_" in str(e) or "FILEREF_EXPIRED" in str(e):
                                logger.warning(f"File reference expired for {file_id}, attempting to refresh...")
                                # Attempt refresh using the first client and database info
                                refreshed = await self._refresh_file_reference(file_id)
                                if refreshed:
                                    logger.info(f"File reference refreshed for {file_id}, retrying chunk download...")
                                    # Update file_id in this scope and retry the exact chunk
                                    file_id = refreshed
                                    # Re-decode location with new file_id
                                    decoded = FileId.decode(file_id)
                                    location = decoded.file_type.location(
                                        id=decoded.media_id,
                                        access_hash=decoded.access_hash,
                                        file_reference=decoded.file_reference,
                                    )
                                    r = await client.invoke(GetFile(location=location, offset=offset, limit=self.chunk_size))
                                    await cache_service.save_chunk(file_id, chunk_index, r.bytes)
                                else:
                                    raise e
                            else:
                                raise e
                        finally:
                            if not use_fallback:
                                try:
                                    if redis_lock.locked():
                                        await redis_lock.release()
                                except Exception as le:
                                    logger.warning("Failed to release Redis lock: %s", le)

                    if not future.done():
                        future.set_result(True)
                    return
                except FloodWait as e:
                    wait_for = min(int(e.value), 45)
                    logger.warning("FloodWait (%ss) for %s/%s", wait_for, file_id, chunk_index)
                    await asyncio.sleep(wait_for)
                except Exception as e:
                    logger.error("Attempt %s failed for %s/%s: %s", attempt + 1, file_id, chunk_index, e)
                    await asyncio.sleep(2 ** attempt)

            if not future.done():
                future.set_exception(Exception("Max retries exceeded"))
        finally:
            async with self._lock:
                self.pending_chunks.pop((file_id, chunk_index), None)

    async def _refresh_file_reference(self, file_id: str) -> Optional[str]:
        # Need to import inside to avoid circular import if necessary, or just use db directly.
        from app.db.session import async_session_factory
        from app.db.models import Episode
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(select(Episode).filter(Episode.file_id == file_id))
            episode = result.scalars().first()
            if not episode or not episode.chat_id or not episode.message_id:
                return None

            try:
                # Use the main client (bot or user) that has access to the chat to fetch the message
                client = self.clients[0]
                message = await client.get_messages(episode.chat_id, episode.message_id)
                if not message:
                    return None

                file = message.video or message.document
                if not file:
                    return None

                new_file_id = file.file_id

                # Update database with new file_id
                episode.file_id = new_file_id
                await db.commit()
                return new_file_id
            except Exception as e:
                logger.error(f"Failed to refresh file reference for {file_id}: {e}")
                return None

downloader = None


def init_downloader(clients: List[Client]):
    global downloader
    downloader = SmartDownloader(clients)

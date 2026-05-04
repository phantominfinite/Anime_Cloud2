import logging
import asyncio
import time
from typing import Dict, Tuple, Optional, List
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputFileLocation
from pyrogram.file_id import FileId
from pyrogram.errors import FloodWait

from app.services.cache import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class SmartDownloader:
    def __init__(self, clients: List[Client], chunk_size: int = 1024 * 1024):
        self.clients = clients
        self._current_client_idx = 0
        self.chunk_size = chunk_size
        # Map (file_id, chunk_index) -> Future
        self.pending_chunks: Dict[Tuple[str, int], asyncio.Future] = {} 
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(10) # Increased concurrency for multiple clients

    def _get_next_client(self) -> Client:
        if not self.clients:
             raise RuntimeError("No Telegram clients configured")
        client = self.clients[self._current_client_idx]
        self._current_client_idx = (self._current_client_idx + 1) % len(self.clients)
        return client

    async def get_chunk(self, file_id: str, chunk_index: int) -> Optional[bytes]:
        # 1. Check Cache
        data = await cache_service.get_chunk(file_id, chunk_index)
        if data:
            asyncio.create_task(self.prefetch_chunks(file_id, chunk_index + 1))
            return data
        
        # 2. Join or Create download task
        future = await self._get_or_create_future(file_id, chunk_index)
        
        # 3. Wait for result
        try:
            await future
        except Exception:
            return None
            
        # 4. Check cache again
        data = await cache_service.get_chunk(file_id, chunk_index)
        if data:
            asyncio.create_task(self.prefetch_chunks(file_id, chunk_index + 1))
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
            asyncio.create_task(self._download_worker(file_id, chunk_index, future))
            return future

    async def _download_worker(self, file_id: str, chunk_index: int, future: asyncio.Future):
        max_retries = 5
        retry_delay = 1

        try:
            for attempt in range(max_retries):
                should_sleep = False
                sleep_for = 0
                try:
                    async with self._semaphore:
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

                    if not future.done():
                        future.set_result(True)
                    return
                except FloodWait as e:
                    wait_for = min(int(e.value), 30)
                    logger.warning(f"FloodWait on client: {e.value}s. Retrying in {wait_for}s.")
                    should_sleep = True
                    sleep_for = wait_for
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed for {file_id}/{chunk_index}: {e}")
                    should_sleep = True
                    sleep_for = retry_delay * (2 ** attempt)

                if should_sleep:
                    await asyncio.sleep(sleep_for)

            if not future.done():
                future.set_exception(Exception("Max retries exceeded"))
        finally:
            async with self._lock:
                key = (file_id, chunk_index)
                if key in self.pending_chunks and self.pending_chunks[key] is future:
                    del self.pending_chunks[key]

downloader = None 

def init_downloader(clients: List[Client]):
    global downloader
    downloader = SmartDownloader(clients)

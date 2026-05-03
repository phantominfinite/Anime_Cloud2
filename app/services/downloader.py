import asyncio
import logging
from typing import Dict, Tuple, Optional
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputFileLocation
from pyrogram.file_id import FileId

from app.services.cache import cache_service

logger = logging.getLogger(__name__)

class SmartDownloader:
    def __init__(self, client: Client, chunk_size: int = 1024 * 1024):
        self.client = client
        self.chunk_size = chunk_size
        # Map (file_id, chunk_index) -> Future
        # If a key exists, it means the chunk is being downloaded.
        # The future will be set to True when done, or Exception if failed.
        self.pending_chunks: Dict[Tuple[str, int], asyncio.Future] = {} 
        self._lock = asyncio.Lock() # Global lock for modifying pending_chunks
        self._semaphore = asyncio.Semaphore(5) # Global limit of concurrent download tasks

    async def get_chunk(self, file_id: str, chunk_index: int) -> Optional[bytes]:
        """
        Get a specific chunk.
        If it's in cache, return it and trigger prefetch.
        If not, wait for it to be downloaded (joining an existing task or creating one).
        """
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
            # Error is already logged in worker
            return None
            
        # 4. Check cache again (it should be there now)
        data = await cache_service.get_chunk(file_id, chunk_index)
        if data:
            asyncio.create_task(self.prefetch_chunks(file_id, chunk_index + 1))
        return data

    async def prefetch_chunks(self, file_id: str, start_index: int, count: int = 3):
        """
        Fire and forget download tasks for upcoming chunks.
        """
        for i in range(count):
            idx = start_index + i
            # Check if already cached
            if await cache_service.exists(file_id, idx):
                continue
            
            # Start download if not already pending
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
        async with self._semaphore:
            try:
                # Double check cache
                if await cache_service.exists(file_id, chunk_index):
                    if not future.done():
                        future.set_result(True)
                    return

                logger.debug(f"Downloading chunk {chunk_index} for {file_id[:10]}...")
                
                offset = chunk_index * self.chunk_size
                limit = self.chunk_size
                
                decoded = FileId.decode(file_id)
                location = decoded.file_type.location(
                    id=decoded.media_id,
                    access_hash=decoded.access_hash,
                    file_reference=decoded.file_reference
                )
                
                r = await self.client.invoke(
                    GetFile(
                        location=location,
                        offset=offset,
                        limit=limit
                    )
                )
                
                chunk_data = r.bytes
                await cache_service.save_chunk(file_id, chunk_index, chunk_data)

                if not future.done():
                    future.set_result(True)

            except Exception as e:
                logger.error(f"Error in download worker for {file_id}/{chunk_index}: {e}")
                if not future.done():
                    future.set_exception(e)
            finally:
                # Cleanup pending map
                async with self._lock:
                    key = (file_id, chunk_index)
                    if key in self.pending_chunks and self.pending_chunks[key] is future:
                        del self.pending_chunks[key]

downloader = None 

def init_downloader(client: Client):
    global downloader
    downloader = SmartDownloader(client)

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.downloader import SmartDownloader

# Mock CacheService
@pytest.fixture
def mock_cache_service():
    with patch("app.services.downloader.cache_service") as mock:
        # Mock async methods to return awaitable objects
        mock.get_chunk = AsyncMock()
        mock.exists = AsyncMock()
        mock.save_chunk = AsyncMock()
        yield mock

# Mock Pyrogram Client and FileId
@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock invoke
    client.invoke = AsyncMock()
    
    # Mock return of invoke
    mock_result = MagicMock()
    mock_result.bytes = b"chunk_data"
    client.invoke.return_value = mock_result
    
    return client

@pytest.fixture(autouse=True)
def mock_file_id():
    # Mock FileId which is now imported at top level
    with patch("app.services.downloader.FileId") as mock_cls:
        mock_decoded = MagicMock()
        mock_decoded.file_type.location.return_value = "mock_location"
        mock_decoded.media_id = 123
        mock_decoded.access_hash = 456
        mock_decoded.file_reference = b"ref"
        
        mock_cls.decode.return_value = mock_decoded
        yield mock_cls

@pytest.mark.asyncio
async def test_get_chunk_cached(mock_client, mock_cache_service):
    """Test retrieving a chunk that is already in cache."""
    downloader = SmartDownloader(mock_client)
    
    # Setup cache to return data
    mock_cache_service.get_chunk.return_value = b"cached_data"
    
    data = await downloader.get_chunk("file_123", 0)
    
    assert data == b"cached_data"
    mock_cache_service.get_chunk.assert_called_with("file_123", 0)
    # Ensure no download was triggered
    mock_client.invoke.assert_not_called()

@pytest.mark.asyncio
async def test_get_chunk_download(mock_client, mock_cache_service):
    """Test retrieving a chunk that needs to be downloaded."""
    downloader = SmartDownloader(mock_client)
    
    # First check returns None (not in cache)
    # Second check (after download) returns data
    mock_cache_service.get_chunk.side_effect = [None, b"downloaded_data"]
    # exists checks: first False (prefetch check), second False (worker check)
    mock_cache_service.exists.return_value = False
    
    # Ensure FileId decode is mocked correctly (via fixture)
    
    data = await downloader.get_chunk("file_123", 0)
    
    assert data == b"downloaded_data"
    # Verify download was triggered via invoke
    mock_client.invoke.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_downloads(mock_client, mock_cache_service):
    """Test that multiple requests for the same chunk share the same download task."""
    downloader = SmartDownloader(mock_client)
    
    # Simulate slow network
    async def slow_invoke(*args, **kwargs):
        await asyncio.sleep(0.05)
        mock_res = MagicMock()
        mock_res.bytes = b"chunk_data"
        return mock_res
    
    mock_client.invoke.side_effect = slow_invoke
    
    mock_cache_service.get_chunk.side_effect = [None, None, b"final_data", b"final_data"]
    
    with patch.object(downloader, 'prefetch_chunks', new=AsyncMock()) as mock_prefetch:
        mock_cache_service.exists.return_value = False
        
        # Launch two requests concurrently
        task1 = asyncio.create_task(downloader.get_chunk("file_shared", 5))
        task2 = asyncio.create_task(downloader.get_chunk("file_shared", 5))
    
        res1, res2 = await asyncio.gather(task1, task2)
    
        assert res1 == b"final_data"
        assert res2 == b"final_data"
    
        # Crucial: invoke should be called ONLY ONCE for the requested chunk
        mock_client.invoke.assert_called_once()

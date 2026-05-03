from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional, Dict, Any
import time
import logging

from pydantic import BaseModel, Field
from app.db.session import get_db
from app.db.models import Anime, Episode, Comment, User
from app.services.telegram import telegram_service
from app.services.websocket import manager
from app.services.redis_cache import redis_service
from app.services.search import search_service
from app.core.config import settings
from app.services.auth import get_current_user
from app.services.ratelimit import rate_limiter

router = APIRouter()

logger = logging.getLogger(__name__)


class EpisodeOut(BaseModel):
    episode_number: str = Field(..., description="Episode number (string)")
    label: str | None = None
    quality: str | None = None
    url: str
    # Backward-compatible alias
    episode: str | None = None


class AnimeOut(BaseModel):
    mal_id: str
    title: str | None = None
    image_url: str | None = None
    score: float | None = None
    type: str | None = None
    year: int | None = None


class AnimeWithEpisodesOut(BaseModel):
    anime: AnimeOut
    episodes: list[EpisodeOut]

@router.websocket("/ws")
@router.websocket("/ws/{anime_mal_id}")
async def websocket_endpoint(websocket: WebSocket, anime_mal_id: Optional[str] = None):
    await manager.connect(websocket, anime_mal_id)
    try:
        while True:
            # Keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, anime_mal_id)

@router.get("/health", response_model=Dict[str, Any])
async def health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns:
        dict: Status and counts of animes/episodes.
    """
    try:
        anime_count = await db.scalar(select(func.count(Anime.id)))
        episode_count = await db.scalar(select(func.count(Episode.id)))
        return {"ok": True, "anime_count": anime_count, "episodes_count": episode_count}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    return await health(db)

@router.get("/anime/list", response_model=Dict[str, List[Dict[str, Any]]])
async def list_animes(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, le=1000), 
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a list of all animes with their episodes.
    
    Args:
        skip (int): Pagination offset.
        limit (int): Pagination limit.
        db (AsyncSession): Database session.
        
    Returns:
        dict: Grouped episodes by Anime MAL ID.
    """
    cache_key = f"anime_list:{skip}:{limit}"
    cached_data = await redis_service.get(cache_key)
    if cached_data:
        return cached_data

    result = await db.execute(select(Episode).offset(skip).limit(limit))
    episodes = result.scalars().all()
    
    data: Dict[str, List[Dict[str, Any]]] = {}
    for ep in episodes:
        if ep.anime_mal_id not in data:
            data[ep.anime_mal_id] = []
        
        data[ep.anime_mal_id].append({
            "episode": ep.episode_number,
            "label": ep.label,
            "quality": ep.quality,
            "url": f"/api/stream/{ep.file_id}",
            "original_url": f"https://t.me/file/{ep.file_id}" 
        })
    
    await redis_service.set(cache_key, data, expire=60)
    return data


@router.get("/anime/available")
async def available_animes(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Return a compact list of MAL IDs that have at least one episode."""
    stmt = (
        select(Episode.anime_mal_id, func.count(Episode.id))
        .group_by(Episode.anime_mal_id)
        .order_by(func.count(Episode.id).desc())
    )
    res = await db.execute(stmt)
    items = res.all()
    return {
        "ok": True,
        "items": [{"mal_id": mal_id, "episodes": int(cnt)} for mal_id, cnt in items],
    }


@router.get("/anime/{mal_id}", response_model=AnimeWithEpisodesOut)
async def get_anime(mal_id: str, db: AsyncSession = Depends(get_db)) -> AnimeWithEpisodesOut:
    """Return anime metadata stored in DB + its episodes.

    Frontend can use this to avoid extra requests and to build a working
    player (stream URLs are generated from Telegram file_id).
    """
    anime = await db.scalar(select(Anime).filter(Anime.mal_id == mal_id))
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")

    result = await db.execute(
        select(Episode)
        .filter(Episode.anime_mal_id == mal_id)
        .order_by(Episode.episode_number)
    )
    episodes = result.scalars().all()

    return AnimeWithEpisodesOut(
        anime=AnimeOut(
            mal_id=anime.mal_id,
            title=anime.title,
            image_url=anime.image_url,
            score=anime.score,
            type=anime.type,
            year=anime.year,
        ),
        episodes=[
            EpisodeOut(
                episode_number=ep.episode_number,
                episode=ep.episode_number,
                label=ep.label,
                quality=ep.quality,
                url=f"/api/stream/{ep.file_id}",
            )
            for ep in episodes
        ],
    )

@router.get("/anime/{mal_id}/episodes", response_model=List[EpisodeOut])
async def get_anime_episodes(mal_id: str, db: AsyncSession = Depends(get_db)) -> List[EpisodeOut]:
    """
    Get all episodes for a specific anime.
    """
    result = await db.execute(
        select(Episode)
        .filter(Episode.anime_mal_id == mal_id)
        .order_by(Episode.episode_number) 
    )
    episodes = result.scalars().all()
    
    # Backward compatible + frontend friendly fields
    return [
        EpisodeOut(
            episode_number=ep.episode_number,
            episode=ep.episode_number,
            label=ep.label,
            quality=ep.quality,
            url=f"/api/stream/{ep.file_id}",
        )
        for ep in episodes
    ]

class CommentCreate(BaseModel):
    user_name: str
    text: str

@router.get("/anime/{mal_id}/comments")
async def get_comments(mal_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment)
        .filter(Comment.anime_mal_id == mal_id)
        .order_by(Comment.created_at.desc())
        .limit(50)
    )
    comments = result.scalars().all()
    return [{
        "id": c.id,
        "user": c.user_name,
        "text": c.text,
        "likes": c.likes,
        "date": c.created_at.strftime("%Y/%m/%d")
    } for c in comments]

@router.post("/anime/{mal_id}/comments")
async def post_comment(
    mal_id: str,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    comment = Comment(
        anime_mal_id=mal_id,
        user_id=user.id if user else None,
        user_name=(user.first_name or user.username) if user else comment_in.user_name,
        text=comment_in.text,
        likes=0
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Broadcast new comment
    await manager.broadcast_room(mal_id, {
        "type": "new_comment",
        "data": {
            "id": comment.id,
            "anime_mal_id": mal_id,
            "user": comment.user_name,
            "text": comment.text,
            "likes": 0,
            "date": comment.created_at.strftime("%Y/%m/%d")
        }
    })
    
    return {"ok": True}

@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    comment.likes += 1
    await db.commit()
    await db.refresh(comment)
    
    # Broadcast like update to the room
    await manager.broadcast_room(comment.anime_mal_id, {
        "type": "comment_like",
        "data": {"id": comment.id, "anime_mal_id": comment.anime_mal_id, "likes": comment.likes},
    })
    
    return {"ok": True, "likes": comment.likes}

@router.get("/search", response_model=Dict[str, List[Dict[str, Any]]])
async def search(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for episodes or animes by title or label.
    Refactored to use SearchService for smarter anime lookup.
    """
    # First search for Anime
    animes = await search_service.search_anime(db, q)
    
    data: Dict[str, List[Dict[str, Any]]] = {}
    
    if animes:
        # If we found anime, fetch their episodes
        anime_ids = [a['mal_id'] for a in animes]
        stmt = select(Episode).filter(Episode.anime_mal_id.in_(anime_ids))
        result = await db.execute(stmt)
        episodes = result.scalars().all()
        
        for ep in episodes:
            if ep.anime_mal_id not in data:
                data[ep.anime_mal_id] = []
            data[ep.anime_mal_id].append({
                "episode": ep.episode_number,
                "label": ep.label,
                "quality": ep.quality,
                "url": f"/api/stream/{ep.file_id}"
            })
            
    # Fallback: Search episodes directly if no anime found (or to augment results)
    # This covers cases where episode label matches but anime title doesn't (rare but possible)
    if not data:
        stmt = select(Episode).join(Anime).filter(Episode.label.ilike(f"%{q}%"))
        result = await db.execute(stmt.limit(50))
        episodes = result.scalars().all()
        for ep in episodes:
            if ep.anime_mal_id not in data:
                data[ep.anime_mal_id] = []
            data[ep.anime_mal_id].append({
                "episode": ep.episode_number,
                "label": ep.label,
                "quality": ep.quality,
                "url": f"/api/stream/{ep.file_id}"
            })
            
    return data

@router.get("/stream/{file_id}")
@router.head("/stream/{file_id}")
async def stream_video(
    file_id: str,
    request: Request,
    range_header: str | None = Header(default=None, alias="Range"),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
):
    """
    Streams a Telegram-hosted media file with HTTP Range support (seekable playback).

    - Supports single-range requests (e.g. `Range: bytes=0-` or `bytes=100-200` or `bytes=-500`)
    - Returns `206 Partial Content` when Range is supplied
    - Returns `416 Range Not Satisfiable` for invalid ranges
    """
    # Best-effort rate limit (per IP) to protect Telegram bandwidth
    if getattr(settings, "RATE_LIMIT_ENABLED", True):
        ip = (request.client.host if request.client else "unknown").replace(":", "_")
        rl = await rate_limiter.hit("stream", ip, int(getattr(settings, "RATE_LIMIT_STREAM_RPM", 120)), 60)
        # expose basic limit headers (best-effort)
        if not rl.allowed:
            retry_after = max(1, rl.reset_epoch - int(time.time()))
            raise HTTPException(
                status_code=429,
                detail="Too Many Requests",
                headers={"Retry-After": str(retry_after)},
            )

    from app.db.session import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(select(Episode).filter(Episode.file_id == file_id))
        episode = result.scalars().first()

        if not episode:
            raise HTTPException(status_code=404, detail="File not found in database.")

        file_size = int(episode.file_size or 0)
        if file_size <= 0:
            # Telegram can sometimes omit size; fail clearly so we can fix ingest.
            raise HTTPException(status_code=409, detail="File size unknown; cannot stream with Range")
        content_type = episode.mime_type or "video/mp4"
        file_name = f"{episode.label or 'video'}.mp4"

    # ETag: stable-ish identifier for clients/caches
    etag = f'W/"{file_id}-{file_size}"'
    if if_none_match and if_none_match.strip() == etag and request.method.upper() == "GET" and not range_header:
        return JSONResponse(status_code=304, content=None, headers={"ETag": etag})

    def parse_single_range(rh: str, size: int) -> tuple[int, int]:
        rh = (rh or "").strip().lower()
        if not rh:
            return (0, size - 1)
        if not rh.startswith("bytes="):
            raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})
        spec = rh[len("bytes="):].strip()
        if "," in spec:
            # We don't support multipart ranges (most video players don't need them).
            raise HTTPException(status_code=416, detail="Multiple ranges not supported", headers={"Content-Range": f"bytes */{size}"})
        if "-" not in spec:
            raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})
        start_s, end_s = spec.split("-", 1)

        if start_s == "" and end_s == "":
            raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})

        if start_s == "":
            # suffix: last N bytes
            try:
                suffix = int(end_s)
            except Exception:
                raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})
            if suffix <= 0:
                raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})
            start = max(0, size - suffix)
            end = size - 1
            return (start, end)

        try:
            start = int(start_s)
        except Exception:
            raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})

        if end_s == "":
            end = size - 1
        else:
            try:
                end = int(end_s)
            except Exception:
                raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})

        if start < 0 or end < 0 or start > end or start >= size:
            raise HTTPException(status_code=416, detail="Range Not Satisfiable", headers={"Content-Range": f"bytes */{size}"})
        end = min(end, size - 1)
        return (start, end)

    start, end = (0, file_size - 1)
    status_code = 200
    if range_header:
        start, end = parse_single_range(range_header, file_size)
        status_code = 206

    content_length = end - start + 1

    headers = {
        "Content-Disposition": f'inline; filename="{file_name}"',
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": content_type,
        "ETag": etag,
        # Streaming is usually personalized / expensive; keep caches conservative by default.
        "Cache-Control": "private, max-age=0, no-store",
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    # For HEAD requests: return headers only
    if request.method.upper() == "HEAD":
        return JSONResponse(status_code=status_code, content=None, headers=headers)

    async def iterfile():
        try:
            async for chunk in telegram_service.stream_file(file_id, offset=start, limit=content_length):
                yield chunk
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            # This will typically close the connection; status can't be changed mid-stream.
            raise

    return StreamingResponse(iterfile(), status_code=status_code, media_type=content_type, headers=headers)


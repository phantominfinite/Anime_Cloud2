from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db.models import User, UserAnime
from app.services.auth import get_current_user, require_user
from pydantic import BaseModel

router = APIRouter()

class UserAnimeUpdate(BaseModel):
    # All fields are optional so the frontend can PATCH-like update.
    status: Optional[str] = None  # plan_to_watch, watching, completed, dropped
    is_favorite: Optional[bool] = None
    score: Optional[int] = None
    progress_episode: Optional[str] = None
    progress_time: Optional[int] = None  # seconds

@router.post("/auth/login")
async def login(user: User = Depends(require_user)):
    """
    Verifies Telegram Init Data and returns the user.
    Called by frontend on startup.
    """
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "photo_url": user.photo_url
        }
    }

@router.get("/user/me")
async def me(user: User = Depends(require_user)):
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "photo_url": user.photo_url,
            "is_admin": user.is_admin,
        },
    }


@router.get("/user/library")
async def get_library(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    """
    Returns user's library (favorites, history).
    """
    result = await db.execute(select(UserAnime).filter(UserAnime.user_id == user.id))
    items = result.scalars().all()
    
    return {
        "ok": True,
        "library": [
            {
                "anime_mal_id": item.anime_mal_id,
                "status": item.status,
                "is_favorite": item.is_favorite,
                "score": item.score,
                "progress": item.progress_episode
            }
            for item in items
        ]
    }

@router.post("/user/library/{mal_id}")
async def update_library(
    mal_id: str, 
    data: UserAnimeUpdate, 
    user: User = Depends(require_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Updates or creates a library entry.
    """
    result = await db.execute(
        select(UserAnime).filter(UserAnime.user_id == user.id, UserAnime.anime_mal_id == mal_id)
    )
    entry = result.scalars().first()
    
    if not entry:
        entry = UserAnime(
            user_id=user.id,
            anime_mal_id=mal_id,
            status=data.status or "plan_to_watch",
            is_favorite=bool(data.is_favorite),
            score=data.score,
            progress_episode=data.progress_episode
        )
        db.add(entry)
    else:
        if data.status is not None:
            entry.status = data.status
        if data.is_favorite is not None:
            entry.is_favorite = data.is_favorite
        if data.score is not None:
            entry.score = data.score
        if data.progress_episode is not None:
            entry.progress_episode = data.progress_episode
        if getattr(entry, "progress_time", None) is not None and data.progress_time is not None:
            entry.progress_time = data.progress_time
            
    await db.commit()
    return {"ok": True}


@router.post("/user/progress/{mal_id}/{episode}")
async def update_progress(
    mal_id: str,
    episode: str,
    payload: Dict[str, Any] = Body(default_factory=dict),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Store continue-watching progress (episode + optional time)."""
    result = await db.execute(
        select(UserAnime).filter(UserAnime.user_id == user.id, UserAnime.anime_mal_id == mal_id)
    )
    entry = result.scalars().first()
    if not entry:
        entry = UserAnime(user_id=user.id, anime_mal_id=mal_id, status="watching", is_favorite=False)
        db.add(entry)

    entry.status = entry.status or "watching"
    entry.progress_episode = episode
    # progress_time column may not exist on older DBs; ignore if missing.
    if "progress_time" in payload and hasattr(entry, "progress_time"):
        try:
            entry.progress_time = int(payload["progress_time"])
        except Exception:
            pass

    await db.commit()
    return {"ok": True}


@router.get("/user/continue")
async def continue_watching(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    """Return items where the user has progress_episode set."""
    result = await db.execute(
        select(UserAnime)
        .filter(UserAnime.user_id == user.id)
        .filter(UserAnime.progress_episode.isnot(None))
    )
    items = result.scalars().all()
    return {
        "ok": True,
        "items": [
            {
                "anime_mal_id": it.anime_mal_id,
                "progress_episode": it.progress_episode,
                "progress_time": getattr(it, "progress_time", None),
                "status": it.status,
            }
            for it in items
        ],
    }

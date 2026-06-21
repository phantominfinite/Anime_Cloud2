from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.db.session import get_db
from app.db.models import User, Anime, Episode, UserAnime
from app.services.auth import require_user
from app.core.config import settings

router = APIRouter()

async def require_admin(user: User = Depends(require_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/admin/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user_count = await db.scalar(select(func.count(User.id)))
    anime_count = await db.scalar(select(func.count(Anime.id)))
    episode_count = await db.scalar(select(func.count(Episode.id)))
    total_views = await db.scalar(select(func.sum(Episode.views))) or 0

    return {
        "total_users": user_count,
        "total_animes": anime_count,
        "total_episodes": episode_count,
        "total_views": total_views
    }

@router.get("/admin/trending")
async def get_trending_anime(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    # Simplistic trending: based on episode views
    stmt = (
        select(Anime, func.sum(Episode.views).label("total_views"))
        .join(Episode)
        .group_by(Anime.id)
        .order_by(func.sum(Episode.views).desc())
        .limit(10)
    )
    res = await db.execute(stmt)
    results = []
    for anime, total_views in res.all():
        results.append({
            "mal_id": anime.mal_id,
            "title": anime.title,
            "views": total_views
        })
    return results

@router.get("/admin/users/recent")
async def get_recent_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    stmt = select(User).order_by(User.created_at.desc()).limit(20)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [{
        "id": u.id,
        "telegram_id": u.telegram_id,
        "username": u.username,
        "created_at": u.created_at
    } for u in users]

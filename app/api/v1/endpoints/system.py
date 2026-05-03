from __future__ import annotations
import os
import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.redis_cache import redis_service
from app.services.websocket import manager
from app.core.config import settings

router = APIRouter()

STARTED_AT = time.time()


@router.get("/health")
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """Lightweight health check.

    Returns:
      - status: operational | degraded
      - components: database/cache status + realtime user count
    """
    # Check Database
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"offline: {str(e)}"

    # Check Redis cache
    cache_status = "ok"
    try:
        await redis_service.set("health_check", {"ok": True}, expire=5)
    except Exception as e:
        cache_status = f"offline: {str(e)}"

    status = "operational"
    if db_status.startswith("offline") or cache_status.startswith("offline"):
        status = "degraded"

    return {
        "status": status,
        "components": {
            "database": db_status,
            "cache": cache_status,
            "realtime_users": len(manager.active_connections),
        },
    }

@router.get("/info")
async def get_system_info() -> dict:
    """Basic runtime info (safe to expose)."""
    uptime_s = int(time.time() - STARTED_AT)
    # Cache directory size (best-effort)
    cache_bytes = 0
    try:
        for root, _, files in os.walk(settings.CACHE_DIR):
            for f in files:
                try:
                    cache_bytes += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        cache_bytes = -1

    return {
        "ok": True,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_s,
        "realtime_users": len(manager.active_connections),
        "cache_dir": settings.CACHE_DIR,
        "cache_bytes": cache_bytes,
    }


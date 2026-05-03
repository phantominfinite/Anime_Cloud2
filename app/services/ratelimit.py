from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.redis_cache import redis_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_epoch: int


class RateLimiter:
    """Best-effort fixed-window rate limiter.

    Works with real Redis or the in-memory MockRedis (via redis_service.get/set).
    """

    def __init__(self, key_prefix: str = "rl"):
        self.key_prefix = key_prefix

    def _key(self, scope: str, identity: str) -> str:
        # Identity should already be normalized (e.g. ip, telegram_id)
        return f"{self.key_prefix}:{scope}:{identity}"

    async def hit(
        self,
        scope: str,
        identity: str,
        limit: int,
        window_seconds: int,
        is_authenticated: bool = False
    ) -> RateLimitResult:
        # Tiered limits: authenticated users get 2x higher limits
        effective_limit = limit * 2 if is_authenticated else limit

        now = int(time.time())
        key = self._key(scope, identity)

        raw = await redis_service.get(key)
        if raw:
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                payload = None
        else:
            payload = None

        if not payload or "reset" not in payload or "count" not in payload or payload["reset"] <= now:
            # Reset window
            payload = {"count": 0, "reset": now + window_seconds}

        payload["count"] += 1
        remaining = max(0, effective_limit - payload["count"])

        # TTL is managed by storing reset timestamp; keep a small buffer
        ttl = max(1, payload["reset"] - now + 5)
        try:
            await redis_service.set(key, payload, expire=ttl)
        except Exception as e:
            # If Redis is down, we don't want to block playback.
            logger.warning(f"RateLimiter: failed to write key {key}: {e}")
            return RateLimitResult(allowed=True, remaining=effective_limit, reset_epoch=now + window_seconds)

        allowed = payload["count"] <= effective_limit
        return RateLimitResult(allowed=allowed, remaining=remaining, reset_epoch=int(payload["reset"]))


rate_limiter = RateLimiter()

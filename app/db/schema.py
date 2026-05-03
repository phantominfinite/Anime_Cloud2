"""Best-effort schema alignment.

The project originally used `Base.metadata.create_all` at startup, which
doesn't apply schema changes to existing databases. For a production-grade
setup you should use Alembic migrations. Until migrations are in place, this
module performs a minimal, idempotent schema sync for newly added columns.
"""

from __future__ import annotations

import logging
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def ensure_schema(engine: AsyncEngine) -> None:
    """Add missing columns that the app relies on.

    Currently ensures:
    - user_animes.progress_time
    - user_animes.last_watched_at
    """

    async with engine.begin() as conn:
        dialect = conn.dialect.name

        def _get_cols(sync_conn):
            insp = inspect(sync_conn)
            return {c["name"] for c in insp.get_columns("user_animes")}

        try:
            cols = await conn.run_sync(_get_cols)
        except Exception as e:
            logger.warning("Schema inspection failed: %s", e)
            return

        stmts: list[str] = []
        if "progress_time" not in cols:
            stmts.append("ALTER TABLE user_animes ADD COLUMN progress_time INTEGER")
        if "last_watched_at" not in cols:
            if dialect == "postgresql":
                stmts.append("ALTER TABLE user_animes ADD COLUMN last_watched_at TIMESTAMP")
            else:
                stmts.append("ALTER TABLE user_animes ADD COLUMN last_watched_at DATETIME")

        for stmt in stmts:
            try:
                await conn.execute(text(stmt))
                logger.info("Applied schema patch: %s", stmt)
            except Exception as e:
                # Ignore if already exists or cannot be applied.
                logger.warning("Failed applying schema patch '%s': %s", stmt, e)

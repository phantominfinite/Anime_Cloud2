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
    - animes.search_vector
    """

    async with engine.begin() as conn:
        dialect = conn.dialect.name

        def _get_user_anime_cols(sync_conn):
            insp = inspect(sync_conn)
            return {c["name"] for c in insp.get_columns("user_animes")}

        def _get_anime_cols(sync_conn):
            insp = inspect(sync_conn)
            return {c["name"] for c in insp.get_columns("animes")}

        try:
            ua_cols = await conn.run_sync(_get_user_anime_cols)
            a_cols = await conn.run_sync(_get_anime_cols)
        except Exception as e:
            logger.warning("Schema inspection failed: %s", e)
            return

        stmts: list[str] = []
        if "progress_time" not in ua_cols:
            stmts.append("ALTER TABLE user_animes ADD COLUMN progress_time INTEGER")
        if "last_watched_at" not in ua_cols:
            if dialect == "postgresql":
                stmts.append("ALTER TABLE user_animes ADD COLUMN last_watched_at TIMESTAMP")
            else:
                stmts.append("ALTER TABLE user_animes ADD COLUMN last_watched_at DATETIME")

        if dialect == "postgresql":
            if "search_vector" not in a_cols:
                stmts.append("ALTER TABLE animes ADD COLUMN search_vector TSVECTOR")
                stmts.append("CREATE INDEX idx_anime_search_vector ON animes USING GIN (search_vector)")
                # Update existing rows
                stmts.append("UPDATE animes SET search_vector = to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))")
                # Trigger for automatic updates
                stmts.append("""
                    CREATE OR REPLACE FUNCTION anime_search_vector_update() RETURNS trigger AS $$
                    BEGIN
                        new.search_vector := to_tsvector('english', coalesce(new.title, '') || ' ' || coalesce(new.description, ''));
                        RETURN new;
                    END
                    $$ LANGUAGE plpgsql;
                """)
                stmts.append("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tsvectorupdate') THEN
                            CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
                            ON animes FOR EACH ROW EXECUTE FUNCTION anime_search_vector_update();
                        END IF;
                    END $$;
                """)

        for stmt in stmts:
            try:
                await conn.execute(text(stmt))
                logger.info("Applied schema patch: %s", stmt)
            except Exception as e:
                # Ignore if already exists or cannot be applied.
                logger.warning("Failed applying schema patch '%s': %s", stmt, e)

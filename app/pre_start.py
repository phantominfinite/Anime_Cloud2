import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed
from sqlalchemy import text
from app.db.session import engine
from alembic.config import Config
from alembic import command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
)
async def init():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database is ready!")
    except Exception as e:
        logger.error(e)
        raise e

async def run_migrations():
    logger.info("Running migrations")
    alembic_cfg = Config("alembic.ini")
    # This is synchronous, which is fine for pre-start script
    # But usually alembic needs the DB URL. It should be in env or alembic.ini
    # We might need to ensure alembic.ini reads from env.
    command.upgrade(alembic_cfg, "head")

async def main():
    logger.info("Initializing service")
    await init()
    # We can run migrations here if we want, or in a separate step in CMD
    # For simplicity in this setup where we use asyncpg, running alembic (sync) 
    # requires a sync driver installed (psycopg2) or running it differently.
    # Since we have libpq-dev and gcc, we can ensure psycopg2-binary is installed or similar.
    
    # However, app.main.lifespan currently does Base.metadata.create_all which is a basic migration strategy.
    # For "Next Level", proper migrations are better.
    # I'll check if we have psycopg2 in requirements.

if __name__ == "__main__":
    asyncio.run(main())

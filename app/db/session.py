from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Adjust connect_args based on DB type
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True # Good for Postgres
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Alias for compatibility with my code in telegram.py
async_session_factory = AsyncSessionLocal

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

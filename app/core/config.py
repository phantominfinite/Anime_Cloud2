from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # --- Runtime / environment ---
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")  # development | production
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # --- Telegram ---
    # Telegram credentials are optional for local/dev so the app can boot
    # without a .env file. Endpoints that require Telegram will return a
    # clear error when credentials are missing.
    API_ID: Optional[int] = Field(default=None, env="API_ID")
    API_HASH: Optional[str] = Field(default=None, env="API_HASH")
    BOT_TOKEN: Optional[str] = Field(default=None, env="BOT_TOKEN")

    # Comma-separated list of Telegram user IDs that can upload videos to the bot.
    ADMIN_IDS: str = Field("", env="ADMIN_IDS")

    # --- Security / admin ---
    # IMPORTANT: Do NOT ship with a default key. In production, this must be set.
    ADMIN_API_KEY: Optional[str] = Field(default=None, env="ADMIN_API_KEY")

    # Comma-separated origins. Use "*" only for development.
    CORS_ORIGINS: str = Field("*", env="CORS_ORIGINS")

    # --- Database / cache ---
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://anime:animepass@localhost:5432/anime_db",
        env="DATABASE_URL",
    )
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    CACHE_DIR: str = Field("cache", env="CACHE_DIR")
    CACHE_MAX_BYTES: int = Field(2 * 1024 * 1024 * 1024, env="CACHE_MAX_BYTES")  # 2GB

    # --- Streaming ---
    STREAM_CHUNK_SIZE: int = Field(1024 * 1024, env="STREAM_CHUNK_SIZE")  # 1MB
    STREAM_PREFETCH_CHUNKS: int = Field(5, env="STREAM_PREFETCH_CHUNKS")

    # --- Rate limiting (best-effort) ---
    RATE_LIMIT_ENABLED: bool = Field(True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_STREAM_RPM: int = Field(120, env="RATE_LIMIT_STREAM_RPM")  # per IP, per minute

    # --- Mini-app ---
    WEBAPP_URL: str = Field("https://google.com", env="WEBAPP_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @field_validator("RATE_LIMIT_STREAM_RPM")
    @classmethod
    def _rpm_positive(cls, v: int) -> int:
        return max(1, int(v))


settings = Settings()

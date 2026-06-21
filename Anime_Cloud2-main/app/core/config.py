from __future__ import annotations

from typing import List, Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Runtime / environment ---
    ENVIRONMENT: str = Field("development", validation_alias=AliasChoices("ENVIRONMENT"))  # development | production
    LOG_LEVEL: str = Field("INFO", validation_alias=AliasChoices("LOG_LEVEL"))

    # --- Telegram ---
    # Telegram credentials are optional for local/dev so the app can boot
    # without a .env file. Endpoints that require Telegram will return a
    # clear error when credentials are missing.
    API_ID: Optional[int] = Field(default=None, validation_alias=AliasChoices("API_ID"))
    API_HASH: Optional[str] = Field(default=None, validation_alias=AliasChoices("API_HASH"))
    BOT_TOKEN: Optional[str] = Field(default=None, validation_alias=AliasChoices("BOT_TOKEN"))

    # Comma-separated list of Telegram user IDs that can upload videos to the bot.
    ADMIN_IDS: str = Field("", validation_alias=AliasChoices("ADMIN_IDS"))

    # --- Security / admin ---
    # IMPORTANT: Do NOT ship with a default key. In production, this must be set.
    ADMIN_API_KEY: Optional[str] = Field(default=None, validation_alias=AliasChoices("ADMIN_API_KEY"))

    # In development/test, allow a safe local default so the app and tests can run
    # without extra environment bootstrapping. Production must still provide this.
    JWT_SECRET_KEY: str = Field("dev-only-change-me", validation_alias=AliasChoices("JWT_SECRET_KEY"))
    JWT_ALGORITHM: str = Field("HS256", validation_alias=AliasChoices("JWT_ALGORITHM"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES"))  # 7 days

    # Comma-separated origins. Use "*" only for development.
    CORS_ORIGINS: str = Field("*", validation_alias=AliasChoices("CORS_ORIGINS"))

    # --- Database / cache ---
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://anime:animepass@localhost:5432/anime_db",
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    REDIS_URL: str = Field("redis://localhost:6379/0", validation_alias=AliasChoices("REDIS_URL"))

    CACHE_DIR: str = Field("cache", validation_alias=AliasChoices("CACHE_DIR"))
    CACHE_MAX_BYTES: int = Field(2 * 1024 * 1024 * 1024, validation_alias=AliasChoices("CACHE_MAX_BYTES"))  # 2GB

    # --- Streaming ---
    STREAM_CHUNK_SIZE: int = Field(1024 * 1024, validation_alias=AliasChoices("STREAM_CHUNK_SIZE"))  # 1MB
    STREAM_PREFETCH_CHUNKS: int = Field(5, validation_alias=AliasChoices("STREAM_PREFETCH_CHUNKS"))

    # --- Rate limiting (best-effort) ---
    RATE_LIMIT_ENABLED: bool = Field(True, validation_alias=AliasChoices("RATE_LIMIT_ENABLED"))
    RATE_LIMIT_STREAM_RPM: int = Field(120, validation_alias=AliasChoices("RATE_LIMIT_STREAM_RPM"))  # per IP, per minute

    # --- Mini-app ---
    WEBAPP_URL: str = Field("https://google.com", validation_alias=AliasChoices("WEBAPP_URL"))

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

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _jwt_secret_required_in_production(cls, v: str, info) -> str:
        env = str(info.data.get("ENVIRONMENT", "development")).lower()
        if env == "production" and (not v or v == "dev-only-change-me"):
            raise ValueError("JWT_SECRET_KEY must be explicitly set in production")
        return v


settings = Settings()

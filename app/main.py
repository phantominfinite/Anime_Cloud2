from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import anime, system, user
from app.core.config import settings
from app.db.schema import ensure_schema
from app.db.session import Base, engine
from app.services.redis_cache import redis_service
from app.services.telegram import telegram_service

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("animecloud")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    if settings.is_production and not settings.ADMIN_API_KEY:
        raise RuntimeError("ADMIN_API_KEY must be set when ENVIRONMENT=production")

    logger.info("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_schema(engine)

    logger.info("Initializing Redis...")
    try:
        await redis_service.connect()
    except Exception as e:
        logger.warning(f"Redis unavailable at startup: {e}")

    logger.info("Initializing Telegram Service...")
    telegram_enabled = bool(settings.API_ID and settings.API_HASH and settings.BOT_TOKEN)
    if telegram_enabled:
        try:
            await telegram_service.start()
        except Exception as e:
            telegram_enabled = False
            logger.error(f"Failed to start Telegram Service: {e}")
    else:
        logger.warning("Telegram credentials not found. Running without Telegram streaming/upload.")

    yield

    # --- Shutdown ---
    logger.info("Shutting down...")
    if telegram_enabled:
        await telegram_service.stop()
    try:
        await redis_service.close()
    except Exception:
        pass


app = FastAPI(title="AnimeCloud Advanced", version="2.1.0", lifespan=lifespan)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_and_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception:
        status_code = "500"
        duration_ms = (time.perf_counter() - start) * 1000.0
        logger.info("%s %s -> %s (%.1fms) rid=%s", request.method, request.url.path, status_code, duration_ms, request_id)
        raise
    else:
        duration_ms = (time.perf_counter() - start) * 1000.0
        logger.info("%s %s -> %s (%.1fms) rid=%s", request.method, request.url.path, status_code, duration_ms, request_id)

    # Correlation + basic hardening headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global error: %s", exc, exc_info=True)

    # Avoid leaking internals in production
    detail = str(exc) if not settings.is_production else "Unexpected server error"
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": "Internal Server Error", "detail": detail},
    )

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"ok": False, "error": "Validation Error", "detail": exc.errors()},
    )


# API Routers
app.include_router(anime.router, prefix="/api", tags=["api"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(user.router, prefix="/api", tags=["user"])

# Static Files (Frontend) - mount last
# We need to serve index.html for 404s to support SPA routing (React Router)
app.mount("/", StaticFiles(directory="app/static", html=True, check_dir=False), name="static")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Fallback for SPA routing: return index.html if path not found."""
    if request.url.path.startswith("/api"):
        return JSONResponse({"ok": False, "error": "Not Found"}, status_code=404)
    return FileResponse("app/static/index.html")

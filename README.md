# AnimeCloud Advanced — Telegram Stream Proxy + Bot + Mini App

> **راهنمای سریع (فارسی):**
> 1) فایل `.env.example` را کپی کنید و به `.env` تبدیل کنید  
> 2) اگر می‌خواهید تلگرام فعال باشد: `API_ID / API_HASH / BOT_TOKEN` را پر کنید  
> 3) اجرا: `uvicorn app.main:app --reload`  
> 4) فرانت‌اند: داخل پوشه `frontend` → `npm i` → `npm run dev` (پروکسی `/api` از قبل تنظیم شده)

---

## What this is
A production-grade-ish stack for streaming Telegram-hosted video files **with seek support** (HTTP Range), plus:
- Telegram bot ingest workflow (forward videos, attach MAL metadata)
- Mini app frontend (Vite + React) to browse and watch
- Local chunk cache + Redis-backed LRU eviction
- WebSocket rooms for realtime activity

## Key features
- **Range streaming** (`/api/stream/{file_id}`) for fast seeking in players
- **Smart downloader** with prefetch to reduce buffering
- **Disk cache** with **LRU eviction** (Redis ZSET) + configurable max size
- **Best-effort rate limiting** for stream endpoint to protect bandwidth
- **Health endpoint**: `GET /api/system/health`
- **Frontend dev proxy**: Vite proxies `/api` → `http://localhost:8000`

## Configuration
Copy:
```bash
cp .env.example .env
```

Important vars:
- `ENVIRONMENT=production` → requires `ADMIN_API_KEY`
- `CORS_ORIGINS` (comma-separated; use `*` only in development)
- `CACHE_MAX_BYTES` (default 2GB)
- `STREAM_CHUNK_SIZE`, `STREAM_PREFETCH_CHUNKS`
- `RATE_LIMIT_STREAM_RPM` (requests/min per IP)

## Run (backend)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run (frontend)
```bash
cd frontend
npm install
npm run dev
```

To build:
```bash
npm run build
```
Then serve the built assets (or copy build into `app/static` depending on your deployment strategy).

## Bot usage
1) Send `/start` to the bot  
2) Forward a video/document to the bot  
3) Reply with metadata:
```
mal_id episode label [quality]
```
Example:
```
52991 1 Episode-1 1080p
```

## Notes
- If Telegram credentials are not present, the backend still boots (useful for local UI work).
- If Redis is unavailable, the system falls back to an in-memory mock (fine for dev, not recommended for production).
---

## What’s improved in this upgraded version (high-level)

### Backend
- Robust `Range` parsing + `HEAD` support for `/api/stream/{file_id}` (better seeking behavior)
- Adds `ETag` and conservative caching headers
- Fixes SPA fallback (`FileResponse` import) and relaxes `X-Frame-Options` to `SAMEORIGIN` (safer for webviews)
- Adds `/api/system/info` for uptime + cache size (best-effort)

### Frontend
- Fixes broken JSX in Home and refreshes the Home UI
- Adds Profile page and wires Navbar correctly
- Library now pulls from backend when running inside Telegram Mini App
- Watch page upgraded: cleaner layout, comments UI, progress saving (best-effort)

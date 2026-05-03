import logging
import asyncio
from typing import AsyncGenerator, Dict, Any
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
from pyrogram.errors import RPCError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pyrogram.handlers import MessageHandler, InlineQueryHandler, CallbackQueryHandler

from app.core.config import settings
from app.services.cache import cache_service
from app.services.downloader import init_downloader, downloader
from app.services.websocket import manager
from app.services.jikan import jikan_service
from app.services.redis_cache import redis_service
from app.services.parser import parse_filename
from app.db.session import async_session_factory
from app.db.models import Anime, Episode
import json

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.api_id = settings.API_ID
        self.api_hash = settings.API_HASH
        self.bot_token = settings.BOT_TOKEN
        self.client = None
        self.chunk_size = int(getattr(settings, "STREAM_CHUNK_SIZE", 1024 * 1024))  # bytes
        if hasattr(settings, "ADMIN_IDS") and settings.ADMIN_IDS:
             self.admin_ids = [int(x) for x in settings.ADMIN_IDS.split(",") if x.strip().isdigit()]
        else:
             self.admin_ids = []

    async def start(self):
        if not self.client:
            logger.info("Starting Telegram Client...")
            self.client = Client(
                "bot_session", 
                api_id=self.api_id, 
                api_hash=self.api_hash, 
                bot_token=self.bot_token, 
                in_memory=True
            )
            
            self.client.add_handler(MessageHandler(self.handle_start, filters.command("start")))
            self.client.add_handler(MessageHandler(self.handle_search_cmd, filters.command("search")))
            self.client.add_handler(MessageHandler(self.handle_forwarded_video, filters.video | filters.document))
            self.client.add_handler(MessageHandler(self.handle_text, filters.text & ~filters.command(["start", "search"])))
            self.client.add_handler(InlineQueryHandler(self.handle_inline_query))
            self.client.add_handler(CallbackQueryHandler(self.handle_callback))

            await self.client.start()
            init_downloader(self.client)
            logger.info("Telegram Client Started")

    async def stop(self):
        if self.client:
            await self.client.stop()
            logger.info("Telegram Client Stopped")

    # ... (Keep existing stream_file method)
    async def stream_file(self, file_id: str, offset: int = 0, limit: int = 0) -> AsyncGenerator[bytes, None]:
        if not self.client: raise RuntimeError("Client not initialized")
        if not downloader: raise RuntimeError("Downloader not initialized")

        start_chunk_idx = offset // self.chunk_size
        start_byte_in_chunk = offset % self.chunk_size
        current_chunk_idx = start_chunk_idx
        bytes_yielded = 0
        
        await downloader.prefetch_chunks(file_id, current_chunk_idx, count=int(getattr(settings, "STREAM_PREFETCH_CHUNKS", 5)))
        
        while True:
            if limit > 0 and bytes_yielded >= limit: break
            chunk_data = await downloader.get_chunk(file_id, current_chunk_idx)
            if not chunk_data: break
            chunk = chunk_data
            if current_chunk_idx == start_chunk_idx and start_byte_in_chunk > 0:
                chunk = chunk[start_byte_in_chunk:]
            if limit > 0:
                remaining = limit - bytes_yielded
                if len(chunk) > remaining: chunk = chunk[:remaining]
            yield chunk
            bytes_yielded += len(chunk)
            current_chunk_idx += 1

    # --- BOT HANDLERS ---

    async def handle_start(self, client: Client, message: Message):
        webapp_url = settings.WEBAPP_URL if hasattr(settings, "WEBAPP_URL") else "https://google.com"
        await message.reply(
            f"Hello {message.from_user.first_name}! 👋\nClick below to open the Anime App.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📺 Open AnimeCloud", web_app=WebAppInfo(url=webapp_url))]
            ])
        )

    async def handle_inline_query(self, client: Client, inline_query: InlineQuery):
        query = inline_query.query.strip()
        if len(query) < 3: return

        results = await jikan_service.search_anime(query)
        webapp_url = settings.WEBAPP_URL if hasattr(settings, "WEBAPP_URL") else "https://google.com"

        articles = []
        for anime in results:
            articles.append(
                InlineQueryResultArticle(
                    title=anime["title"],
                    description=f"{anime.get('type', '?')} • {anime.get('year', '?')} • ⭐ {anime.get('score', 'N/A')}",
                    thumb_url=anime["images"]["jpg"]["image_url"],
                    input_message_content=InputTextMessageContent(f"🎬 **{anime['title']}**\n\n{anime.get('synopsis', '')[:200]}..."),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📺 Watch Now", web_app=WebAppInfo(url=f"{webapp_url}#anime_{anime['mal_id']}"))]
                    ])
                )
            )
        await inline_query.answer(articles, cache_time=300)

    async def handle_search_cmd(self, client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply("Usage: `/search <anime name>`")
            return
        query = " ".join(message.command[1:])
        await self.perform_search(message, query)

    async def perform_search(self, message: Message, query: str):
        await message.reply(f"🔎 Searching for: {query}...")
        results = await jikan_service.search_anime(query)
        if not results:
            await message.reply("❌ No results found.")
            return

        # Create Buttons
        buttons = []
        for anime in results[:5]: # Top 5
             buttons.append([InlineKeyboardButton(
                 f"{anime['title']} ({anime.get('year', '?')})", 
                 callback_data=f"sel_anime_{anime['mal_id']}"
             )])
        
        await message.reply("🎯 **Select Anime:**", reply_markup=InlineKeyboardMarkup(buttons))

    async def get_state(self, user_id: int) -> Dict[str, Any]:
        data = await redis_service.get(f"upload_state:{user_id}")
        return data or {}

    async def set_state(self, user_id: int, data: Dict[str, Any]):
        await redis_service.set(f"upload_state:{user_id}", data, expire=3600)

    async def clear_state(self, user_id: int):
        await redis_service.delete(f"upload_state:{user_id}")

    async def handle_forwarded_video(self, client: Client, message: Message):
        if message.from_user.id not in self.admin_ids: return

        file = message.video or message.document
        if not file: return

        # Auto-detect metadata
        filename = file.file_name if hasattr(file, "file_name") else "video.mp4"
        parsed = parse_filename(filename)
        
        state_data = {
            "file_id": file.file_id,
            "file_unique_id": file.file_unique_id,
            "file_size": file.file_size,
            "mime_type": file.mime_type,
            "stage": "anime_search",
            "detected_quality": parsed["quality"]
        }
        
        await self.set_state(message.from_user.id, state_data)

        msg_text = "✅ File received.\n"
        if parsed["title"]:
            msg_text += f"🧐 Detected: **{parsed['title']}** - Ep **{parsed['episode']}**\n"
            # If detected, we could offer a "Yes, use this" button, but for now lets keep search flow
            # or pre-fill search.
        
        msg_text += "⬇️ Send the **Anime Name** to search (or MAL ID)."
        
        await message.reply(msg_text)
        
        if parsed["title"]:
             # Automatically search if title is detected
             await self.perform_search(message, parsed["title"])

    async def handle_text(self, client: Client, message: Message):
        user_id = message.from_user.id
        state = await self.get_state(user_id)
        if not state: return
        
        if state["stage"] == "anime_search":
            # User sent anime name
            await self.perform_search(message, message.text)
            
        elif state["stage"] == "episode_num":
            # User sent episode number
            ep_num = message.text.strip()
            state["episode"] = ep_num
            state["stage"] = "quality_select"
            await self.set_state(user_id, state)
            
            # Ask for Quality
            buttons = [
                [InlineKeyboardButton("1080p", callback_data="qual_1080p"),
                 InlineKeyboardButton("720p", callback_data="qual_720p"),
                 InlineKeyboardButton("480p", callback_data="qual_480p")],
                [InlineKeyboardButton("Skip (Use Detected/HD)", callback_data="qual_skip")]
            ]
            await message.reply("🎞 **Select Quality:**", reply_markup=InlineKeyboardMarkup(buttons))

    async def handle_callback(self, client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        user_id = callback_query.from_user.id
        state = await self.get_state(user_id)
        
        if not state:
            await callback_query.answer("Session expired.", show_alert=True)
            return

        if data.startswith("sel_anime_"):
            mal_id = data.split("_")[2]
            
            state["mal_id"] = mal_id
            state["stage"] = "episode_num"
            await self.set_state(user_id, state)
            
            # Fetch info to confirm
            details = await jikan_service.get_anime(int(mal_id))
            title = details.get('title') if details else mal_id
            
            await callback_query.message.edit_text(
                f"✅ Selected: **{title}**\n\n🔢 Now send the **Episode Number** (e.g., 1, 02, 12.5)"
            )
        
        elif data.startswith("qual_"):
            quality = data.split("_")[1]
            if quality == "skip":
                quality = state.get("detected_quality", "HD")
            
            state["quality"] = quality
            await self.save_episode(callback_query.message, state)
            await self.clear_state(user_id)

    async def save_episode(self, message: Message, data: Dict[str, Any]):
        mal_id = data["mal_id"]
        episode_number = data["episode"]
        
        async with async_session_factory() as session:
            # Check/Create Anime
            result = await session.execute(select(Anime).filter(Anime.mal_id == mal_id))
            anime = result.scalars().first()
            
            if not anime:
                await message.reply(f"⏳ Fetching full metadata...")
                details = await jikan_service.get_anime(int(mal_id))
                
                if details:
                    anime = Anime(
                        mal_id=mal_id, 
                        title=details.get("title"),
                        description=details.get("synopsis"),
                        image_url=details.get("images", {}).get("jpg", {}).get("large_image_url"),
                        genres=json.dumps(details.get("genres", [])),
                        score=details.get("score"),
                        status=details.get("status"),
                        studios=json.dumps(details.get("studios", [])),
                        type=details.get("type"),
                        year=details.get("year"),
                        season=details.get("season"),
                        rating=details.get("rating"),
                        duration=details.get("duration"),
                        trailer_url=details.get("trailer", {}).get("embed_url"),
                        rank=details.get("rank")
                    )
                else:
                    anime = Anime(mal_id=mal_id, title=f"Anime {mal_id}")
                
                session.add(anime)
                await session.commit()
            
            # Create Episode
            episode = Episode(
                anime_mal_id=mal_id,
                episode_number=episode_number,
                label=f"Episode {episode_number}",
                quality="HD", # Default for now
                file_id=data["file_id"],
                file_unique_id=data["file_unique_id"],
                file_size=data["file_size"],
                mime_type=data.get("mime_type", "video/mp4")
            )
            session.add(episode)
            await session.commit()
            
        await message.reply(f"✅ **Saved!**\nAnime: {mal_id}\nEpisode: {episode_number}")

telegram_service = TelegramService()

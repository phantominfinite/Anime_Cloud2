import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Dict, Any
from app.db.models import Anime, UserAnime, User

class RecommendationService:
    async def get_recommendations(self, db: AsyncSession, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        # 1. Get user's favorites and highly rated anime
        stmt = select(UserAnime).filter(
            UserAnime.user_id == user_id,
            or_(UserAnime.is_favorite == True, UserAnime.score >= 8)
        )
        res = await db.execute(stmt)
        user_animes = res.scalars().all()

        if not user_animes:
            # Fallback: Popular/Top rated anime
            stmt = select(Anime).order_by(Anime.score.desc()).limit(limit)
            res = await db.execute(stmt)
            animes = res.scalars().all()
            return self._format(animes)

        # 2. Extract genres from these animes
        mal_ids = [ua.anime_mal_id for ua in user_animes]
        stmt = select(Anime).filter(Anime.mal_id.in_(mal_ids))
        res = await db.execute(stmt)
        liked_animes = res.scalars().all()

        genres = set()
        for anime in liked_animes:
            if anime.genres:
                try:
                    g_list = json.loads(anime.genres)
                    genres.update(g_list)
                except:
                    pass

        if not genres:
             # Fallback
            stmt = select(Anime).order_by(Anime.score.desc()).limit(limit)
            res = await db.execute(stmt)
            animes = res.scalars().all()
            return self._format(animes)

        # 3. Find other animes with similar genres, excluding already watched
        # Simple content-based filtering: find animes that share at least one genre
        watched_stmt = select(UserAnime.anime_mal_id).filter(UserAnime.user_id == user_id)
        watched_res = await db.execute(watched_stmt)
        watched_ids = watched_res.scalars().all()

        # Build a query to search by genres
        genre_filters = [Anime.genres.ilike(f"%{g}%") for g in genres]
        stmt = (
            select(Anime)
            .filter(or_(*genre_filters))
            .filter(~Anime.mal_id.in_(watched_ids))
            .order_by(Anime.score.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        recommendations = res.scalars().all()

        return self._format(recommendations)

    def _format(self, animes: List[Anime]) -> List[Dict[str, Any]]:
        return [{
            "mal_id": a.mal_id,
            "title": a.title,
            "image_url": a.image_url,
            "score": a.score,
            "type": a.type,
            "year": a.year
        } for a in animes]

recommendation_service = RecommendationService()

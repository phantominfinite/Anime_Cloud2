from typing import Any, Dict, List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Anime, UserAnime


class RecommendationService:
    async def get_recommendations(self, db: AsyncSession, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        liked_stmt = select(UserAnime).filter(
            UserAnime.user_id == user_id,
            or_(UserAnime.is_favorite.is_(True), UserAnime.score >= 8),
        )
        user_animes = (await db.execute(liked_stmt)).scalars().all()

        if not user_animes:
            return await self._top_rated(db, limit)

        mal_ids = [ua.anime_mal_id for ua in user_animes]
        liked_animes = (await db.execute(select(Anime).filter(Anime.mal_id.in_(mal_ids)))).scalars().all()

        genre_names: set[str] = set()
        for anime in liked_animes:
            if not isinstance(anime.genres, list):
                continue
            for genre in anime.genres:
                if isinstance(genre, dict) and genre.get("name"):
                    genre_names.add(str(genre["name"]))
                elif isinstance(genre, str):
                    genre_names.add(genre)

        if not genre_names:
            return await self._top_rated(db, limit)

        watched_ids = (await db.execute(select(UserAnime.anime_mal_id).filter(UserAnime.user_id == user_id))).scalars().all()

        genre_filters = [Anime.genres.contains([{"name": name}]) for name in genre_names]
        stmt = (
            select(Anime)
            .filter(or_(*genre_filters))
            .filter(~Anime.mal_id.in_(watched_ids))
            .order_by(Anime.score.desc())
            .limit(limit)
        )
        recommendations = (await db.execute(stmt)).scalars().all()
        return self._format(recommendations)

    async def _top_rated(self, db: AsyncSession, limit: int) -> List[Dict[str, Any]]:
        animes = (await db.execute(select(Anime).order_by(Anime.score.desc()).limit(limit))).scalars().all()
        return self._format(animes)

    def _format(self, animes: List[Anime]) -> List[Dict[str, Any]]:
        return [{
            "mal_id": a.mal_id,
            "title": a.title,
            "image_url": a.image_url,
            "score": a.score,
            "type": a.type,
            "year": a.year,
        } for a in animes]


recommendation_service = RecommendationService()

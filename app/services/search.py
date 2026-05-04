from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Anime


class SearchService:
    async def search_anime(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20,
        offset: int = 0,
        min_rating: Optional[float] = None,
        year: Optional[int] = None,
        season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filters = []
        if min_rating is not None:
            filters.append(Anime.score >= min_rating)
        if year is not None:
            filters.append(Anime.year == year)
        if season:
            filters.append(Anime.genres.contains([{"name": season}]))

        if db.bind.dialect.name == "postgresql":
            q = (
                select(Anime)
                .filter(func.to_tsvector('english', Anime.title).op('@@')(func.plainto_tsquery('english', query)))
                .filter(and_(*filters) if filters else text('TRUE'))
                .order_by(func.ts_rank(func.to_tsvector('english', Anime.title), func.plainto_tsquery('english', query)).desc())
                .distinct(Anime.id)
                .offset(offset)
                .limit(limit)
                
            )
        else:
            q = (
                select(Anime)
                .filter(Anime.title.ilike(f"%{query}%"))
                .filter(and_(*filters) if filters else text('TRUE'))
                .distinct(Anime.id)
                .offset(offset)
                .limit(limit)
            )

        results = (await db.execute(q)).scalars().all()
        return [{"mal_id": a.mal_id, "title": a.title, "image_url": a.image_url, "score": a.score, "type": a.type, "year": a.year} for a in results]


search_service = SearchService()

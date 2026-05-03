from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, text
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
                .filter(Anime.search_vector.op("@@")(text("plainto_tsquery('english', :q)")))
                .filter(and_(*filters) if filters else text('TRUE'))
                .order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC"))
                .distinct(Anime.id)
                .offset(offset)
                .limit(limit)
                .params(q=query)
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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text
from typing import List, Dict, Any
from app.db.models import Anime, Episode

class SearchService:
    async def search_anime(self, db: AsyncSession, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Enhanced "Smart" Search using PostgreSQL Full-Text Search
        
        results = []
        
        # 1. ID Match (High priority)
        if query.isdigit():
            id_stmt = select(Anime).filter(Anime.mal_id == query)
            id_res = await db.execute(id_stmt)
            anime = id_res.scalars().first()
            if anime:
                results.append(anime)
        
        # 2. Full-Text Search (PostgreSQL)
        if db.bind.dialect.name == "postgresql":
            # Use search_vector with rank
            fts_stmt = (
                select(Anime)
                .filter(Anime.search_vector.op("@@")(text("plainto_tsquery('english', :q)")) )
                .order_by(text("ts_rank(search_vector, plainto_tsquery('english', :q)) DESC"))
                .limit(limit)
                .params(q=query)
            )
            res = await db.execute(fts_stmt)
            for row in res.scalars().all():
                if row.id not in [r.id for r in results]:
                    results.append(row)
        else:
            # Fallback for SQLite/others
            stmt = select(Anime).filter(Anime.title.ilike(f"%{query}%")).limit(limit)
            res = await db.execute(stmt)
            for row in res.scalars().all():
                if row.id not in [r.id for r in results]:
                    results.append(row)
                
        # Format results
        data = []
        for anime in results:
            data.append({
                "mal_id": anime.mal_id,
                "title": anime.title,
                "image_url": anime.image_url,
                "score": anime.score,
                "type": anime.type,
                "year": anime.year
            })
            
        return data

search_service = SearchService()

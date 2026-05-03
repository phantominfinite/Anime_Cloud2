from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text
from typing import List, Dict, Any
from app.db.models import Anime, Episode

class SearchService:
    async def search_anime(self, db: AsyncSession, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Check if we can use postgres full text search
        # Using a simple ILIKE for now but structured for easy upgrade
        # To really upgrade, we would add a TSVECTOR column.
        
        # Enhanced "Smart" Search:
        # 1. Exact MAL ID match
        # 2. Title ILIKE match
        
        results = []
        
        # 1. ID Match
        if query.isdigit():
            id_stmt = select(Anime).filter(Anime.mal_id == query)
            id_res = await db.execute(id_stmt)
            anime = id_res.scalars().first()
            if anime:
                results.append(anime)
        
        # 2. Title Match
        stmt = select(Anime).filter(Anime.title.ilike(f"%{query}%")).limit(limit)
        res = await db.execute(stmt)
        for row in res.scalars().all():
            if row not in results:
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

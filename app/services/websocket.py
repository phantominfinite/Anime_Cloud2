from fastapi import WebSocket
from typing import List, Dict, Set
import json
import logging
import asyncio
from app.services.redis_cache import redis_service

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Global connection list
        self.active_connections: List[WebSocket] = []
        # Rooms: anime_mal_id -> Set[WebSocket]
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, anime_mal_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if anime_mal_id:
            if anime_mal_id not in self.rooms:
                self.rooms[anime_mal_id] = set()
            self.rooms[anime_mal_id].add(websocket)
            await self.update_room_count(anime_mal_id)
        
        await self.broadcast_user_count()

    async def disconnect(self, websocket: WebSocket, anime_mal_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if anime_mal_id and anime_mal_id in self.rooms:
            if websocket in self.rooms[anime_mal_id]:
                self.rooms[anime_mal_id].remove(websocket)
                if not self.rooms[anime_mal_id]:
                    del self.rooms[anime_mal_id]
                else:
                    await self.update_room_count(anime_mal_id)

        await self.broadcast_user_count()

    async def broadcast(self, message: dict):
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                to_remove.append(connection)
        
        for conn in to_remove:
            # We don't know which room they were in easily here without tracking
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    async def broadcast_room(self, anime_mal_id: str, message: dict):
        """Send a message to connections that joined a given anime room."""
        if not anime_mal_id or anime_mal_id not in self.rooms:
            # Fallback to global broadcast if no room is known.
            await self.broadcast(message)
            return

        to_remove = []
        for ws in list(self.rooms[anime_mal_id]):
            try:
                await ws.send_json(message)
            except Exception:
                to_remove.append(ws)

        for ws in to_remove:
            try:
                self.rooms[anime_mal_id].discard(ws)
            except Exception:
                pass

    async def broadcast_user_count(self):
        count = len(self.active_connections)
        await self.broadcast({"type": "online_count", "count": count})

    async def update_room_count(self, anime_mal_id: str):
        if anime_mal_id in self.rooms:
            count = len(self.rooms[anime_mal_id])
            message = {"type": "room_count", "anime_mal_id": anime_mal_id, "count": count}
            
            # Broadcast to everyone in the room
            to_remove = []
            for ws in self.rooms[anime_mal_id]:
                try:
                    await ws.send_json(message)
                except:
                    to_remove.append(ws)
            
            for ws in to_remove:
                self.rooms[anime_mal_id].remove(ws)

manager = ConnectionManager()

from fastapi import WebSocket
from typing import Set
import json
import logging
import asyncio
from app.services.redis_cache import redis_service

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # We still need to track local connections to send messages to them
        self.local_connections: Set[WebSocket] = set()
        # Local rooms mapping: anime_mal_id -> Set[WebSocket]
        self.local_rooms: dict[str, Set[WebSocket]] = {}
        self.pubsub_task = None

    async def _setup_pubsub(self):
        if self.pubsub_task:
            return

        if redis_service.is_mock:
            logger.warning("WebSocket scaling disabled: using MockRedis (no Pub/Sub)")
            return

        async def listen():
            while True:
                pubsub = None
                try:
                    pubsub = redis_service.client.pubsub()
                    await pubsub.subscribe("ws_broadcast", "ws_room_broadcast")
                    async for message in pubsub.listen():
                        if message["type"] == "message":
                            try:
                                data = json.loads(message["data"])
                                target_room = data.get("_room")
                                payload = data.get("payload")

                                if target_room:
                                    await self._send_to_local_room(target_room, payload)
                                else:
                                    await self._send_to_all_local(payload)
                            except Exception as e:
                                logger.error(f"Error in pubsub message handling: {e}")
                except Exception as e:
                    logger.exception(f"Pub/Sub listener crashed, retrying in 5 seconds: {e}")
                    await asyncio.sleep(5)
                finally:
                    if pubsub is not None:
                        try:
                            await pubsub.close()
                        except Exception:
                            pass

        self.pubsub_task = asyncio.create_task(listen())

    async def connect(self, websocket: WebSocket, anime_mal_id: str = None):
        await websocket.accept()
        self.local_connections.add(websocket)
        await self._setup_pubsub()
        
        if anime_mal_id:
            if anime_mal_id not in self.local_rooms:
                self.local_rooms[anime_mal_id] = set()
            self.local_rooms[anime_mal_id].add(websocket)
            await self._broadcast_room_count(anime_mal_id)

        await self.broadcast_user_count()

    async def disconnect(self, websocket: WebSocket, anime_mal_id: str = None):
        self.local_connections.discard(websocket)
        if anime_mal_id and anime_mal_id in self.local_rooms:
            self.local_rooms[anime_mal_id].discard(websocket)
            if not self.local_rooms[anime_mal_id]:
                del self.local_rooms[anime_mal_id]
            await self._broadcast_room_count(anime_mal_id)

        await self.broadcast_user_count()

    async def _send_to_all_local(self, message: dict):
        for ws in list(self.local_connections):
            try:
                await ws.send_json(message)
            except:
                self.local_connections.discard(ws)

    async def _send_to_local_room(self, anime_mal_id: str, message: dict):
        if anime_mal_id in self.local_rooms:
            for ws in list(self.local_rooms[anime_mal_id]):
                try:
                    await ws.send_json(message)
                except:
                    self.local_rooms[anime_mal_id].discard(ws)

    async def _broadcast_room_count(self, anime_mal_id: str):
        count = len(self.local_rooms.get(anime_mal_id, set()))
        await self.broadcast_room(anime_mal_id, {"type": "watching_count", "anime_mal_id": anime_mal_id, "count": count})

    async def broadcast(self, message: dict):
        """Global broadcast via Redis Pub/Sub."""
        if redis_service.is_mock:
            await self._send_to_all_local(message)
            return
            
        await redis_service.client.publish("ws_broadcast", json.dumps({
            "payload": message
        }))

    async def broadcast_room(self, anime_mal_id: str, message: dict):
        """Room broadcast via Redis Pub/Sub."""
        if redis_service.is_mock:
            await self._send_to_local_room(anime_mal_id, message)
            return

        await redis_service.client.publish("ws_room_broadcast", json.dumps({
            "_room": anime_mal_id,
            "payload": message
        }))

    async def broadcast_user_count(self):
        # This is tricky across instances without a global counter
        # For simplicity, we just use local count or a redis counter
        if not redis_service.is_mock:
            count = len(self.local_connections)
            # In a real app we'd aggregate counts from all nodes in Redis
            await self.broadcast({"type": "online_count", "count": count})
        else:
            await self._send_to_all_local({"type": "online_count", "count": len(self.local_connections)})

manager = ConnectionManager()

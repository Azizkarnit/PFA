import json
import logging
import asyncio
import threading
from typing import Dict, Set
from fastapi import WebSocket

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps user_id to a set of active WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.loop = None

    def start_redis_listener(self):
        """Starts a background thread to listen to Redis PubSub for notifications."""
        self.loop = asyncio.get_running_loop()
        thread = threading.Thread(target=self._listen_to_redis, daemon=True)
        thread.start()

    def _listen_to_redis(self):
        try:
            redis_client = get_redis_client()
            pubsub = redis_client.pubsub()
            pubsub.subscribe("notifications_channel")
            logger.info("Subscribed to Redis notifications_channel")
            for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    if user_id and user_id in self.active_connections:
                        # Schedule the async send in the main event loop
                        asyncio.run_coroutine_threadsafe(
                            self.send_personal_message(data, user_id),
                            self.loop
                        )
        except Exception as e:
            logger.error(f"Redis PubSub listener error: {e}")

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected to WebSocket. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket.")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            dead_sockets = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {e}")
                    dead_sockets.add(websocket)
            
            for ws in dead_sockets:
                self.disconnect(ws, user_id)

manager = ConnectionManager()

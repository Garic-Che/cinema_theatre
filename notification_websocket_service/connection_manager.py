import asyncio
from typing import Dict
from weakref import WeakSet

from websockets.exceptions import ConnectionClosed

from core.logger import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WeakSet] = {}
        self.lock = asyncio.Lock()
        self.logger = logger

    async def connect(self, websocket, user_id: str):
        async with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = WeakSet()
            self.active_connections[user_id].add(websocket)
        await self.logger.info(f"User {user_id} connected. Connections: {len(self.active_connections[user_id])}")

    async def disconnect(self, websocket, user_id: str):
        async with self.lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        await self.logger.info(f"User {user_id} disconnected. Remaining connections: {len(self.active_connections.get(user_id, []))}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id not in self.active_connections:
            await self.logger.warning(f"No active connections for user {user_id}")
            return False

        successful_send = False
        dead_connections = []

        async with self.lock:
            connections = list(self.active_connections.get(user_id, []))

        for connection in connections:
            try:
                await connection.send_text(message)
                successful_send = True
            except ConnectionClosed:
                dead_connections.append(connection)
            except Exception as e:
                await self.logger.error(f"Error sending to connection for user {user_id}: {str(e)}")

        if dead_connections:
            async with self.lock:
                for connection in dead_connections:
                    self.active_connections[user_id].discard(connection)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

        return successful_send
# websocket_manager.py
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import logging

logger = logging.getLogger("websocket")

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"Client connected: {websocket.client}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"Client disconnected: {websocket.client}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Send failed, removing client {websocket.client}: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: str):
        to_remove = []
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Broadcast failed to {connection.client}: {e}")
                    to_remove.append(connection)
            for conn in to_remove:
                self.active_connections.remove(conn)

    async def keep_alive(self, websocket: WebSocket):
        # Optionnel : ping loop
        while True:
            try:
                await websocket.send_text("__ping__")
                await asyncio.sleep(10)
            except Exception as e:
                logger.warning(f"Ping failed for {websocket.client}: {e}")
                await self.disconnect(websocket)
                break

ws_manager = WebSocketManager()

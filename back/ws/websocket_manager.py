# websocket_manager.py
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import logging
from utils.logger import logger

import json
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()
        self.loop: asyncio.AbstractEventLoop = None  # par défaut

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

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

    async def send_personal_message(self, message:  Dict[str, any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Send failed, removing client {websocket.client}: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, any]):
        to_remove = []
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))  # sérialisation en JSON
                except Exception as e:
                    logger.warning(f"Broadcast failed to {connection.client}: {e}")
                    to_remove.append(connection)
            for conn in to_remove:
                self.active_connections.remove(conn)


    def broadcast_sync(self, message: Dict[str, any]):
        if not self.loop or not self.loop.is_running():
            raise RuntimeError("Boucle asyncio non disponible ou arrêtée.")
        asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)


    def format_message(self, sender: str, message: str, data: any = None):
        return { "sender":sender, "message":message, "data":data }
    
    async def keep_alive(self, websocket: WebSocket):
        # Optionnel : ping loop
        while True:
            try:
                await self.broadcast(self.format_message("system","ping",None))
                await asyncio.sleep(60)
            except Exception as e:
                logger.warning(f"Ping failed for {websocket.client}: {e}")
                await self.disconnect(websocket)
                break

ws_manager = WebSocketManager()

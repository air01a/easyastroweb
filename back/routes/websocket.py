from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.websocket_manager import ws_manager
import asyncio

router = APIRouter(prefix="/ws",tags=["websocket"])

@router.websocket("/observation")
async def websocket_observation(websocket: WebSocket):
    await ws_manager.connect(websocket)
    ping_task = asyncio.create_task(ws_manager.keep_alive(websocket))

    try:
        while True:
            message = await websocket.receive_text()
            await ws_manager.send_personal_message(f"Message reçu: {message}", websocket)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    finally:
        ping_task.cancel()

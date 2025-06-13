# routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.websocket_manager import ws_manager
from services.alpaca_client import alpaca_telescope_client, alpaca_camera_client
#from alpaca_client import AlpacaClient  # Ou indi_client si tu pilotes INDI
import asyncio

router = APIRouter()
#alpaca = AlpacaClient("http://localhost:11111/api/v1")  # adapte l'URL

# ======== ROUTES REST (React appelle ça) ========
@router.get("/telescope/config")
async def get_config():
    return await alpaca_telescope_client.get_telescope_info()

@router.get("/camera/config")
async def get_config():
    return await alpaca_camera_client.get_camera_info()

@router.get('/telescope/test')
async def get_test():
    await alpaca_telescope_client.set_tracking(True)
    #return await alpaca_telescope_client.slew_to_coordinates_async(23.1111,80)
    await alpaca_telescope_client.move_axis(1,0)
    
"""
@router.get("/alpaca/position")
async def get_position():
    return await alpaca.get_position()

@router.post("/alpaca/slew")
async def slew_to_target(ra: float, dec: float):
    success = await alpaca.slew_to(ra, dec)
    if success:
        await ws_manager.broadcast(f"Télescope en déplacement vers RA={ra}, DEC={dec}")
    return {"status": "ok" if success else "error"}

@router.post("/observation/start")
async def start_observation():
    # Lancement d'une observation (simplifié)
    await ws_manager.broadcast("Observation démarrée.")
    # ici, tu pourrais lancer une coroutine qui prend des photos, gère le suivi, etc.
    return {"status": "started"}


# ======== WEBSOCKET POUR LES CLIENTS FRONTEND ========
"""
@router.websocket("/ws/observation")
async def websocket_observation(websocket: WebSocket):
    await ws_manager.connect(websocket)
    ping_task = asyncio.create_task(ws_manager.keep_alive(websocket))

    try:
        while True:
            message = await websocket.receive_text()
            # Ici tu pourrais gérer des commandes côté client
            await ws_manager.send_personal_message(f"Message reçu: {message}", websocket)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    finally:
        ping_task.cancel()

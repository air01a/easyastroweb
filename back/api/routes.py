# routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

from ws.websocket_manager import ws_manager
from services.alpaca_client import alpaca_telescope_client, alpaca_camera_client
#from alpaca_client import AlpacaClient  # Ou indi_client si tu pilotes INDI
import asyncio
from services.skymap import generate_dso_image, generate_map

from datetime import datetime, timezone

router = APIRouter()
#alpaca = AlpacaClient("http://localhost:11111/api/v1")  # adapte l'URL

# ======== ROUTES REST  ========
@router.get("/telescope/config")
async def get_config():
    return await alpaca_telescope_client.get_telescope_info()

@router.get("/camera/config")
async def get_config():
    return await alpaca_camera_client.get_camera_info()

@router.get('/telescope/test')
async def get_test():
    await alpaca_telescope_client.set_tracking(True)
    await alpaca_telescope_client.slew_to_coordinates_async(23.1111,80)
    #await alpaca_telescope_client.move_axis(1,0)

@router.get("/plot")
def get_dso_image(object: str = Query(..., description="Nom ou identifiant de l'objet (ex: M31, NGC 7000)")):
    #image_stream = generate_dso_image(object)
    image_stream = generate_map(object)
    return StreamingResponse(image_stream, media_type="image/png")

def get_utc_timestamp_precise():
    now = datetime.now(timezone.utc)
    # Obtenir les 6 chiffres de microsecondes
    micro = now.microsecond  # entre 0 et 999999
    # Ajouter un chiffre supplémentaire (ex: 0) pour avoir 7 chiffres
    fraction = f"{micro:06d}"
    return now.strftime(f"%Y-%m-%dT%H:%M:%SZ") #.{fraction}Z

@router.get("/telescope/setdate")
async def set_date():
    print(get_utc_timestamp_precise())
    test =await alpaca_telescope_client.set_utc_date(get_utc_timestamp_precise())
    print(test.body)

@router.get("/telescope/getdate")
async def get_date():
    test =await alpaca_telescope_client.get_utc_date()
    return test


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

# ======== Websocket  ========

@router.websocket("/ws/observation")
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

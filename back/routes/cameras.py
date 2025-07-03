from fastapi import APIRouter, Body, HTTPException
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone
from services.config import check_data_format, get_cameras, get_cameras_schema,save_cameras, set_default_camera, find_item_from_name
from models.api import ConfigPayload
from services.config import TELESCOPE

from typing import Dict, Union, List, Any

router = APIRouter(prefix="/cameras", tags=["camera"])

@router.get("/")
async def api_get_cameras():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await get_cameras()

@router.post("/")
async def api_set_cameras(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    schema = await get_cameras_schema()
    for item in payload:
        error = await check_data_format(item, schema)
        if error:
            raise HTTPException(status_code=500, detail=error)
    await save_cameras(payload)
    return {"ok"}


@router.get("/schema")
async def api_get_cameras_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await get_cameras_schema()

@router.get("/current")
async def get_current_camera():
    return ""

@router.put("/current")
async def api_set_current_camera(camera: str = Body(..., embed=True)):
    await set_default_camera(camera)
    return camera
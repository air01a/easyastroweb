from fastapi import APIRouter, Body, HTTPException
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone
from services.config import check_data_format, FILTERWHEEL, get_filterwheels, get_filterwheels_schema, save_filterwheels, set_default_filterwheel
from models.api import ConfigPayload
from services.config import TELESCOPE

from typing import Dict, Union, List, Any

router = APIRouter(prefix="/filterwheels", tags=["Filter Wheels"])

@router.get("/")
async def api_get_filterwheels():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await get_filterwheels()

@router.post("/")
async def api_set_filterwheels(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    schema = await get_filterwheels_schema()
    for item in payload:
        error = await check_data_format(item, schema)
        if error:
            raise HTTPException(status_code=500, detail=error)
    await save_filterwheels(payload)
    return {"ok"}


@router.get("/schema")
async def api_get_filterwheels_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await get_filterwheels_schema()

@router.get("/current")
async def get_current_camera():
    return FILTERWHEEL

@router.put("/current")
async def api_set_current_camera(wheel: str = Body(..., embed=True)):
    await set_default_filterwheel(wheel)
    return FILTERWHEEL
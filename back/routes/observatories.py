
from fastapi import APIRouter, Body,HTTPException
from services.config import get_observatories as root_observatories, get_observatory_schema as root_observatory_schema, save_observatories
router = APIRouter(prefix="/observatories", tags=["observatories"])
from typing import List
from models.api import ConfigPayload
from services.config import OBSERVATORY, set_default_observatory, check_data_format

@router.get("/")
async def get_observatories():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_observatories()

@router.post("/")
async def set_observatories(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    schema = await get_observatory_schema()
    for item in payload : 
        error = await check_data_format(item, schema)
        if error:
            raise HTTPException(status_code=500, detail=error)
    await save_observatories(payload)
    return {"ok"}

@router.get("/schema")
async def get_observatory_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_observatory_schema()

@router.get("/current")
async def get_current_observatory():
    return OBSERVATORY

@router.put("/current")
async def set_current_observatory(observatory: str = Body(..., embed=True)):
    await set_default_observatory(observatory)
    return OBSERVATORY
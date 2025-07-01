from fastapi import APIRouter, Body, HTTPException
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone
from services.config import check_data_format, save_telescopes, get_telescopes as root_get_telescopes, get_telescope_schema as root_get_telescope_schema, set_default_telescope
from typing import List
from models.api import ConfigPayload
from services.config import TELESCOPE


router = APIRouter(prefix="/telescopes", tags=["telescope"])

@router.get("/config")
async def get_telescope_config():
    return await alpaca_telescope_client.get_telescope_info()

@router.get('/test')
async def test_telescope():
    await alpaca_telescope_client.set_tracking(True)
    await alpaca_telescope_client.slew_to_coordinates_async(23.1111, 80)

def get_utc_timestamp_precise():
    now = datetime.now(timezone.utc)
    micro = now.microsecond
    return now.strftime(f"%Y-%m-%dT%H:%M:%SZ")

@router.get("/setdate")
async def set_telescope_date():
    print(get_utc_timestamp_precise())
    test = await alpaca_telescope_client.set_utc_date(get_utc_timestamp_precise())
    print(test.body)
    return {"status": "date_set"}

@router.get("/getdate")
async def get_telescope_date():
    test = await alpaca_telescope_client.get_utc_date()
    return test


@router.get("/")
async def get_telescope():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_get_telescopes()

@router.post("/")
async def set_telescope(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    schema = await get_telescope_schema()
    for item in payload:
        error = await check_data_format(item, schema)
        if error:
            raise HTTPException(status_code=500, detail=error)
    await save_telescopes(payload)
    return {"ok"}


@router.get("/schema")
async def get_telescope_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_get_telescope_schema()

@router.get("/current")
async def get_current_observatory():
    return TELESCOPE

@router.put("/current")
async def set_current_observatory(telescope: str = Body(..., embed=True)):
    await set_default_telescope(telescope)
    return TELESCOPE
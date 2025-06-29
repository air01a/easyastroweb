from fastapi import APIRouter
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone
from .models import ConfigPayload
from services.config import CONFIG, CONFIG_SCHEME, save_config as root_save_config, load_config_async, get_observatory as root_observatory, get_observatory_schema as root_observatory_schema, save_observatory, save_telescope, get_telescope as root_get_telescope, get_telescope_schema as root_get_telescope_schema
from typing import List, Union, Dict

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/")
async def save_config(payload: ConfigPayload):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    print("Configuration reçue:", payload['fits_process_dir'])

    await root_save_config(payload)
    await load_config_async()
    print(CONFIG)
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return {"message": "Configuration enregistrée avec succès."}

@router.get("/")
async def get_config():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    
    return CONFIG


@router.get("/scheme")
async def get_config_scheme():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return CONFIG_SCHEME


@router.get("/observatory")
async def get_observatory():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_observatory()

@router.post("/observatory")
async def set_observatory(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    await save_observatory(payload)
    return {"ok"}

@router.get("/observatory/schema")
async def get_observatory_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_observatory_schema()


@router.get("/telescope")
async def get_telescope():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_get_telescope()

@router.post("/telescope")
async def set_telescope(payload: List[ConfigPayload]):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...
    await save_telescope(payload)
    return {"ok"}

@router.get("/telescope/schema")
async def get_telescope_schema():
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    
    # Ici tu peux persister en base de données ou autre traitement
    # ...

    return await root_get_telescope_schema()
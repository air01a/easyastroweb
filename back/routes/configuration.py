from fastapi import APIRouter
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone
from .models import ConfigPayload
from services.config import CONFIG, CONFIG_SCHEME, save_config as root_save_config, load_config

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/")
async def save_config(payload: ConfigPayload):
    """
    Endpoint qui reçoit une configuration sous forme de dict[str, Any]
    """
    # Tu peux faire ici ce que tu veux avec payload.config
    # Par exemple, l'afficher dans la console
    print("Configuration reçue:", payload['fits_process_dir'])

    root_save_config(payload)
    load_config()
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
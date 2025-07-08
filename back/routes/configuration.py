from fastapi import APIRouter
from models.api import ConfigPayload
from services.configurator import CONFIG, CONFIG_SCHEME,  save_config as root_save_config, load_config_async

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
    
    return CONFIG['global']


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



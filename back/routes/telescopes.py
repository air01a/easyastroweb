""" EasyAstroWeb telescopes API Routes
This module defines the API routes for managing camera configurations in the EasyAstro application."""

from fastapi import APIRouter, Body, HTTPException
from services.configurator import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, TELESCOPE_PATH, TELESCOPE_SCHEMA_PATH
from models.api import ConfigPayload, ConfigAllowedValue
from typing import Dict, List, Any

router = APIRouter(prefix="/telescopes", tags=["telescopes"])

@router.get("/")
async def api_get_telescopes() -> List[ConfigPayload]:
    """Retrieve the list of telescopes."""
    return await get_telescope_config(TELESCOPE_PATH)

@router.post("/")
async def api_set_telescopes(payload: List[ConfigPayload]):
    """Set the list of telescopes."""
    (error, error_str) = await save_telescope_config(TELESCOPE_PATH, payload, 'telescope',TELESCOPE_SCHEMA_PATH)
    if not error:
        raise HTTPException(status_code=500, detail=error_str)

    return {"ok"}


@router.get("/schema")
async def api_get_telescopes_schema() -> List[Dict[str, ConfigAllowedValue]]:
    """Retrieve the schema for telescopes configuration."""
    return await get_telescope_config_schema(TELESCOPE_SCHEMA_PATH)

@router.get("/current")
async def get_current_camera() -> Dict[str, Any]:
    """Retrieve the current observatory configuration."""
    return CONFIG.get("telescope",{})


@router.put("/current")
async def api_set_current_camera(telescope: str = Body(..., embed=True)):
    """Set the current filterwheel configuration."""
    await set_default_telescope_config(telescope, "telescope", TELESCOPE_SCHEMA_PATH)
    return telescope
""" EasyAstroWeb observatories API Routes
This module defines the API routes for managing camera configurations in the EasyAstro application."""

from fastapi import APIRouter, Body, HTTPException
from services.config import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, OBSERVATORY_PATH, OBSERVATORY_SCHEMA_PATH
from models.api import ConfigPayload, ConfigAllowedValue
from typing import Dict, List, Any

router = APIRouter(prefix="/observatories", tags=["observatories"])

@router.get("/")
async def api_get_observatories() -> List[ConfigPayload]:
    """Retrieve the list of observatories."""
    return await get_telescope_config(OBSERVATORY_PATH)

@router.post("/")
async def api_set_observatories(payload: List[ConfigPayload]):
    """Set the list of observatories."""
    (error, error_str) = await save_telescope_config(OBSERVATORY_PATH, payload, 'observatory',OBSERVATORY_SCHEMA_PATH)
    if not error:
        raise HTTPException(status_code=500, detail=error_str)

    return {"ok"}


@router.get("/schema")
async def api_get_observatories_schema() -> List[Dict[str, ConfigAllowedValue]]:
    """Retrieve the schema for observatories configuration."""
    return await get_telescope_config_schema(OBSERVATORY_SCHEMA_PATH)

@router.get("/current")
async def get_current_camera() -> Dict[str, Any]:
    """Retrieve the current observatory configuration."""
    return CONFIG.get("observatory",{})


@router.put("/current")
async def api_set_current_camera(observatory: str = Body(..., embed=True)):
    """Set the current filterwheel configuration."""
    await set_default_telescope_config(observatory, "observatory", OBSERVATORY_SCHEMA_PATH)
    return observatory
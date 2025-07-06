""" EasyAstroWeb filterwheels API Routes
This module defines the API routes for managing camera configurations in the EasyAstro application."""

from fastapi import APIRouter, Body, HTTPException
from services.config import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, FILTERWHEELS_PATH, FILTERWHEELS_SCHEMA_PATH
from models.api import ConfigPayload, ConfigAllowedValue
from typing import Dict, List, Any

router = APIRouter(prefix="/filterwheels", tags=["filterwheels"])

@router.get("/")
async def api_get_filterwheels() -> List[ConfigPayload]:
    """Retrieve the list of filterwheels."""
    return await get_telescope_config(FILTERWHEELS_PATH)

@router.post("/")
async def api_set_filterwheels(payload: List[ConfigPayload]):
    """Set the list of filterwheels."""
    (error, error_str) = await save_telescope_config(FILTERWHEELS_PATH, payload, 'filterwheel',FILTERWHEELS_SCHEMA_PATH)
    if not error:
        raise HTTPException(status_code=500, detail=error_str)

    return {"ok"}


@router.get("/schema")
async def api_get_filterwheels_schema() -> List[Dict[str, ConfigAllowedValue]]:
    """Retrieve the schema for filterwheels configuration."""
    return await get_telescope_config_schema(FILTERWHEELS_SCHEMA_PATH)

@router.get("/current")
async def get_current_camera() -> Dict[str, Any]:
    """Retrieve the current filterwheel configuration."""
    return CONFIG.get("filterwheel",{})


@router.put("/current")
async def api_set_current_camera(wheel: str = Body(..., embed=True)):
    """Set the current filterwheel configuration."""
    await set_default_telescope_config(wheel, "filterwheel", FILTERWHEELS_SCHEMA_PATH)
    return wheel
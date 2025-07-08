""" EasyAstroWeb Cameras API Routes
This module defines the API routes for managing camera configurations in the EasyAstro application."""

from fastapi import APIRouter, Body, HTTPException
from services.configurator import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, CAMERAS_PATH, CAMERAS_SCHEMA_PATH
from models.api import ConfigPayload, ConfigAllowedValue
from typing import Dict, List, Any

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.get("/")
async def api_get_cameras() -> List[ConfigPayload]:
    """Retrieve the list of cameras."""
    return await get_telescope_config(CAMERAS_PATH)

@router.post("/")
async def api_set_cameras(payload: List[ConfigPayload]):
    """Set the list of cameras."""
    (error, error_str) = await save_telescope_config(CAMERAS_PATH, payload, 'camera', CAMERAS_SCHEMA_PATH)
    if not error:
        raise HTTPException(status_code=500, detail=error_str)

    return {"ok"}


@router.get("/schema")
async def api_get_cameras_schema() -> List[Dict[str, ConfigAllowedValue]]:
    """Retrieve the schema for cameras configuration."""
    return await get_telescope_config_schema(CAMERAS_SCHEMA_PATH)

@router.get("/current")
async def get_current_camera() -> Dict[str, Any]:
    """Retrieve the current camera configuration."""
    return CONFIG.get("camera",{})


@router.put("/current")
async def api_set_current_camera(camera: str = Body(..., embed=True)):
    """Set the current camera configuration."""
    await set_default_telescope_config(camera, "camera", CAMERAS_PATH)
    return camera
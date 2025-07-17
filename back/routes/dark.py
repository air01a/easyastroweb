""" EasyAstroWeb Dark API Routes
This module defines the API routes for managing darks."""

from fastapi import APIRouter, Body, HTTPException
from services.configurator import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, CAMERAS_PATH, CAMERAS_SCHEMA_PATH
from models.api import DarkLibraryType, DarkLibraryProcessType
from typing import Dict, List, Any
from models.state import telescope_state

router = APIRouter(prefix="/dark", tags=["Dark library"])

@router.get("/current_process")
async def current_process() -> List[DarkLibraryProcessType]:
    """Retrieve the list of darks for a camera."""
    return telescope_state.dark_processor

@router.get("/{numero_camera}")
async def get_dark(numero_camera: str) -> List[DarkLibraryType]:
    """Retrieve the list of darks for a camera."""
    return     [{ "temperature": 10, "exposition": 10, "gain": 10, "count": 5 },
    { "temperature": 20, "exposition": 20, "gain": 10, "count": 3 }]

def _to_process_list(plans: List[DarkLibraryType]) -> List[DarkLibraryProcessType]:
    return [
        DarkLibraryProcessType(
            **plan.model_dump(),
            done=False,
            eta=30,
            in_progress=True # ou une estimation calculée si besoin
        )
        for plan in plans
    ]

@router.put("/{numero_camera}")
async def create_dark(numero_camera: str, plan: List[DarkLibraryType] = Body(...)) -> bool:
    """Retrieve the list of darks for a camera."""
    newPlan= _to_process_list(plan)
    print(newPlan)
    telescope_state.dark_processor=newPlan
    return    True

@router.put("/stop")
async def stop_dark(_: dict = Body(default={})) -> bool:
    """Retrieve the list of darks for a camera."""
    telescope_state.dark_processor = []
    return True





""" EasyAstroWeb Dark API Routes
This module defines the API routes for managing darks."""

from fastapi import APIRouter, Body, HTTPException
from services.configurator import save_telescope_config, get_telescope_config, get_telescope_config_schema, set_default_telescope_config, CONFIG, CAMERAS_PATH, CAMERAS_SCHEMA_PATH
from models.api import DarkLibraryType, DarkLibraryProcessType, DarkLibraryItem
from typing import Dict, List, Any
from models.state import telescope_state
from pathlib import Path
import json
from services.dark_manager import DarkManager
from services.telescope_interface import telescope_interface

router = APIRouter(prefix="/dark", tags=["Dark library"])

@router.get("/current_process")
async def current_process() -> List[DarkLibraryProcessType]:
    """Retrieve the list of darks for a camera."""
    if telescope_state.dark_processor:
        return telescope_state.dark_processor.plan
    return []

@router.get("/{numero_camera}")
async def get_dark(numero_camera: str) -> List[DarkLibraryItem]:
    """Retrieve the list of darks for a camera."""

    config = Path(CONFIG['global'].get("dark_directory")) / Path("config.json")
    data = DarkManager.get_dark_config(config, False)

    if numero_camera in data.keys():
        return data[numero_camera]
    return []

@router.delete("/{numero_camera}/{date}")
async def delete_dark(numero_camera: str, date: str) -> List[DarkLibraryItem]:
    """Retrieve the list of darks for a camera."""

    config = Path(CONFIG['global'].get("dark_directory")).resolve() / Path("config.json")
    dark_data = DarkManager.get_dark_config(config, False)
    if numero_camera in dark_data:
        dark = DarkManager.get_dark_item_by_camera_and_date(dark_data, numero_camera, date)
        if dark:
            file = Path(dark.filename)
            file.unlink(missing_ok=True)
        dark_data[numero_camera] = [
            entry for entry in dark_data[numero_camera] if entry['date'] != date
        ]
        

    DarkManager.save_dark_config(config, dark_data, already_serialized=True)
    return await get_dark(numero_camera)


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
    camera = CONFIG.get("camera",None)
    if not camera:
        raise HTTPException(status_code=500, detail="No camera found")

    telescope_state.dark_processor=DarkManager(telescope_interface, camera=camera['id'], plan=newPlan)
    telescope_state.dark_processor.start()
    return    True

@router.post("/stop")
async def stop_dark(body: dict = Body(default={}, embed=False)) -> bool:
    """Retrieve the list of darks for a camera."""
    telescope_state.dark_processor = []
    return True





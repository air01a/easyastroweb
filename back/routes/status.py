from fastapi import APIRouter, Body, HTTPException
from typing import Dict
from models.state import telescope_state
from services.telescope_interface import telescope_interface
from services.configurator import CONFIG


router = APIRouter(prefix="/status", tags=["status"])


@router.get("/is_running")
def is_running() -> bool:
    print(telescope_state)
    if telescope_state.plan_active and telescope_state.scheduler and telescope_state.scheduler.is_alive():
        return True
    return False


@router.get("/is_connected")
async def is_connected() -> Dict[str, bool]:
    """
    Check if the telescope interface is connected.
    """
    return {"telescope_connected": telescope_state.is_telescope_connected, "camera_connected": telescope_state.is_camera_connected, "filter_wheel_connected": telescope_state.is_fw_connected, "focuser_connected": telescope_state.is_focuser_connected}

@router.post("/connect_hardware")
def connect_telescope() -> Dict[str, bool]:
    """
    Connect the telescope interface.
    """

    try:

        telescope_interface.connect()
        return {"telescope_connected": telescope_state.is_telescope_connected, "camera_connected": telescope_state.is_camera_connected, "filter_wheel_connected": telescope_state.is_fw_connected, "focuser_connected": telescope_state.is_focuser_connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/set_telescope_date")
def set_telescope_date(date: str = Body(..., embed=True)) -> Dict[str, str]:
    """
    Set the date for the telescope.
    """
    if CONFIG['telescope'].get('has_gps', False):
        return {"date": telescope_interface.get_utc_date()}
    try:
        telescope_interface.set_utc_date(date)
        return {"date": date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/connected_hardware")
def get_connected_hardware() -> Dict[str, str]:
    """
    Get the names of connected hardware components.
    """

    return {
        "mount_name": telescope_interface.mount_name,
        "fw_name": telescope_interface.fw_name,
        "focuser_name": telescope_interface.focuser_name,
        "camera_name": telescope_interface.camera_name,
        "telescope_location": telescope_interface.get_telescope_location(),
        "utc_date": telescope_interface.get_utc_date()
    }

@router.get("/operation_status")
def get_operation_status():
    if telescope_state.scheduler:
        return telescope_state.scheduler.automate_step
    else:
        return -1
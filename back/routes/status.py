from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Dict
from models.api import PlanType
from models.state import telescope_state
from services.telescope_interface import telescope_interface


router = APIRouter(prefix="/status", tags=["status"])


@router.get("/is_running")
def is_running() -> bool:
    print(telescope_state)
    if telescope_state.plan_active and telescope_state.scheduler and telescope_state.scheduler.is_alive():
        return True
    return False


@router.get("/isçconnected")
async def is_connected() -> Dict[str, bool]:
    """
    Check if the telescope interface is connected.
    """
    return {"telescope_connected": telescope_state.is_telescope_connected, "camera_connected": telescope_state.is_camera_connected, "filter_wheel_connected": telescope_state.is_fw_connected, "focuser_connected": telescope_state.is_focuser_connected}

@router.post("/connect")
def connect_telescope() -> Dict[str, bool]:
    """
    Connect the telescope interface.
    """
    try:
        telescope_interface.connect()
        return {"telescope_connected": telescope_state.is_telescope_connected, "camera_connected": telescope_state.is_camera_connected, "filter_wheel_connected": telescope_state.is_fw_connected, "focuser_connected": telescope_state.is_focuser_connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Query, HTTPException
from models.state import telescope_state

from services.telescope_interface import telescope_interface


router = APIRouter(prefix="/focuser", tags=["focuser"])
lock_focuser = False


@router.get('/')
def get_focuser_position():
    if telescope_state.is_focuser_connected:
        return telescope_interface.focuser_get_current_position()
    raise HTTPException(status_code=503, detail="No Focuser")


@router.post('/{position}')
def move_focuser(position: int) -> int:
    global lock_focuser
    if lock_focuser:
        raise HTTPException(status_code=503, detail="Focuser Busy")
    if telescope_state.is_focuser_connected:
        lock_focuser=True
        telescope_interface.move_focuser(position)
        lock_focuser=False
        return telescope_interface.focuser_get_current_position()
    raise HTTPException(status_code=503, detail="No Focuser")

@router.get('/max')
def get_focuser_position():
    if telescope_state.is_focuser_connected:
        return telescope_interface.get_max_focuser_step()
    raise HTTPException(status_code=503, detail="No Focuser")


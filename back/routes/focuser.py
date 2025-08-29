from fastapi import APIRouter, Query, HTTPException
from models.state import telescope_state
from typing import List,  Dict, Any

from services.telescope_interface import telescope_interface
from services.focuser_automate import FocuserAutomate

router = APIRouter(prefix="/focuser", tags=["focuser"])
lock_focuser = False


@router.get('/')
def get_focuser_position():
    if telescope_state.is_focuser_connected:
        return telescope_interface.focuser_get_current_position()
    raise HTTPException(status_code=503, detail="No Focuser")


@router.post('/stop')
def get_focuser_position():
    if telescope_state.is_focuser_connected:
        telescope_interface.focuser_halt()
        return True
    raise HTTPException(status_code=503, detail="No Focuser")


@router.get('/max')
def get_focuser_position():
    if telescope_state.is_focuser_connected:
        return telescope_interface.get_max_focuser_step()
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

@router.get('/lastfocus')
def get_last_focus() :
    return telescope_state.last_focus

@router.put('/autofocus')
def start_autofocus():
    if telescope_state.scheduler and telescope_state.scheduler.is_alive():
        raise HTTPException(status_code=500, detail="Plan already runnning")
    telescope_state.scheduler = FocuserAutomate(telescope_interface)
    telescope_state.scheduler.start()
    telescope_state.plan_active=True
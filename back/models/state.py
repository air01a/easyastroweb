from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class TelescopeState:
    is_slewing: bool = False
    is_capturing: bool = False
    is_focusing: bool = False
    is_focused: bool = False
    is_telescope_connected : bool = False
    is_fw_connected : bool = False
    is_camera_connected: bool = False
    is_focuser_connected: bool = False
    plan_active : bool = False
    scheduler = None
    last_picture: np.ndarray = None
    last_stacked_picture : Path = Path("C:/Users/eniquet/Documents/dev/easyastroweb/back/services/astro_session/final/livestack.jpg")


    
telescope_state = TelescopeState()


from dataclasses import dataclass
from pathlib import Path
import numpy as np
from services.configurator import CONFIG
from models.api import ImageSettings
from typing import List, Dict, Any

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
    last_stacked_picture : np.ndarray = None
    dark_processor = None
    image_settings = ImageSettings(stretch=CONFIG['global'].get('initial_stretch',0.15), black_point=CONFIG['global'].get('initial_black_point',80))
    last_focus = [None,None]
    last_analyzed_image = None
telescope_state = TelescopeState()


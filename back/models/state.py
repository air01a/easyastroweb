from dataclasses import dataclass

@dataclass
class TelescopeState:
    is_slewing: bool = False
    is_capturing: bool = False
    is_focusing: bool = False
    is_focused: bool = False

telescope_state = TelescopeState()


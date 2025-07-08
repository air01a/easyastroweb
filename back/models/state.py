from dataclasses import dataclass

@dataclass
class TelescopeState:
    is_slewing: bool
    is_capturing: bool
    is_focusing: bool
    is_focused: bool

telescope_state = TelescopeState()


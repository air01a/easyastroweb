from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class SchedulerStatus:
    is_running: bool
    is_paused: bool
    current_observation: Optional['Observation'] = None
    queue: List['Observation'] = None
    next_observation: Optional['Observation'] = None
    last_observation: Optional['Observation'] = None
    error: Optional[str] = None
    stop_scheduler: bool = False
    retry: int = 0

@dataclass
class Observation:
    start: float  # Heure décimale UTC
    expo: float
    number: int
    ra: float
    dec: float
    filter: str
    object: str
    

class StopScheduler:
    pass
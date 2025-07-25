from dataclasses import dataclass
from typing import Optional, List, Union
from pathlib import Path
from pydantic import BaseModel


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

class Observation(BaseModel):
    start: float  # Heure décimale UTC
    expo: float
    number: int
    ra: float
    dec: float
    filter: str
    object: str
    focus: bool
    gain: int

class PlanExecutionType(Observation):
    real_start: Union[str, None]
    end: Union[str, None]
    images: int
    jpg: Union[str, None]

PlansExecutionType = List[PlanExecutionType]

class StopScheduler:
    pass
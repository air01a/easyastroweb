from pydantic import BaseModel
from typing import List, Union, Dict
from pathlib import Path

class PlanType(BaseModel):
    start: float
    expo: int
    nExpo : int
    ra: float
    dec: float
    filter: str
    object: str
    focus: bool
    gain: int


ConfigAllowedValue = Union[str, int, float, bool, List[bool], List[str]]

ConfigPayload = Dict[str, ConfigAllowedValue]

class KeyValuePayload(BaseModel):
    key: str
    value: ConfigAllowedValue


class DarkLibraryType(BaseModel):
    gain: int
    temperature: int
    exposition: int
    count: int

class DarkLibraryProcessType(DarkLibraryType):
    done: bool
    eta: int
    in_progress : bool
    progress: int=0
    
class DarkLibraryItem(BaseModel):
    gain: int
    temperature: int
    exposition: int
    count: int
    date: str
    filename:str


class ImageSettings(BaseModel):
    stretch: float
    black_point: int
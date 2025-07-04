from pydantic import BaseModel
from typing import List, Union, Dict

class PlanType(BaseModel):
    start: float
    expo: int
    ra: float
    dec: float
    filter: str
    object: str

ConfigAllowedValue = Union[str, int, float, bool, List[bool], List[str]]

ConfigPayload = Dict[str, ConfigAllowedValue]

class KeyValuePayload(BaseModel):
    key: str
    value: ConfigAllowedValue
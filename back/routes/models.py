from pydantic import BaseModel
from typing import List

class PlanType(BaseModel):
    start: float
    expo: int
    ra: float
    dec: float
    filter: str
    object: str
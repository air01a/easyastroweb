from services.configurator import CONFIG, CURRENT_DIR
from utils.json_load import load_array_form_json, save_json
from pathlib import Path
import json
from utils.logger import logger
from models.observation import Observation, PlansExecutionType,PlanExecutionType
from typing import Dict, List, Any
import time
class HistoryManager:

    def __init__(self):
        self.config_dir=CURRENT_DIR.parent / "config" / "history.json"
        self.current=None
        self.index=0
        self.history=None

    def open_history(self):
        history = load_array_form_json(self.config_dir)
        self.history=[]
        for obs in history:
            observation = PlanExecutionType(**obs)
            self.history.append(observation)

    def get_json(self):
        if not self.history:
            self.open_history()
        return [p.model_dump() for p in self.history]


    def new_obs(self):
        self.history[self.index].real_start=time.strftime('%Y-%m-%dT%H.%M.%S')

    def close_obs(self, capture:int=None):
        if (capture!=None):
            self.history[self.index].number=capture
        self.history[self.index].end=time.strftime('%Y-%m-%dT%H.%M.%S')
        self.index+=1
        
        self.save_history()

    def update_obs_image(self,  capture: int = None,image : Path=None):
        if (image!=None):
            self.history[self.index].jpg=str(image.resolve())
        if (capture!=None):
            self.history[self.index].images=capture

    def save_history(self):
        if save_json( [p.model_dump() for p in self.history], self.config_dir):
            logger.info("[HISTORY] - history saved")
        else:
            logger.error("[HISTORY] - Error while saving history")

    def _convert_to_execution(self, plans: List[Observation]) -> PlansExecutionType:
        result = []
        for plan in plans:
            exec_plan = PlanExecutionType(
                real_start =None,   # conversion float -> str
                end=None,
                images=0,
                jpg=None,
                start = plan.start,
                expo = plan.expo,
                number= plan.number,
                ra = plan.ra,
                dec = plan.dec,
                filter = plan.filter,
                object = plan.object,
                focus = plan.focus,
                gain = plan.gain           # ajoute tous les champs de PlanType
            )
            result.append(exec_plan)
        return result

    def add_plan(self, plan: List[Observation]):
        self.history=self._convert_to_execution(plan)





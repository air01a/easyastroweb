
from models.basic_automate import BasicAutomate
from models.state import telescope_state

class FocuserAutomate(BasicAutomate):
    def __init__(self, telescope_interface):
        super().__init__(telescope_interface, name="FOCUSER")
        
     

    def _execute_plan(self, plan):
        self.get_focus(None, None)


    def request_stop(self): 
        self._request_stop()
        telescope_state.plan_active=False

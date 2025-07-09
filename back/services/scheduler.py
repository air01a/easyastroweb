from datetime import datetime, timezone
import threading
import time
from models.observation import StopScheduler, Observation
from models.state import telescope_state
from utils.logger import logger
from services.configurator import CONFIG
from utils.calcul import get_solver

class Scheduler(threading.Thread):
    def __init__(self, telescope_interface):
        super().__init__(daemon=True)
        self.telescope_interface = telescope_interface
        self._stop_requested = False
        self.solver = get_solver(CONFIG)
        print("connected",self.telescope_interface.telescope_connect())
        self.telescope_interface.telescope_unpark()
        #self.telescope_interface.camera_connect()

    def run(self):
        logger.info("[Scheduler] Started in background thread.")
        self._execute_plan(self.plan)

    def slew_to_target(self, ra: float, dec:float):
        print(ra, dec)

        final=False
        while not final:
            self.telescope_interface.slew_to_target(ra, dec)
            print("-----")
            image = self.telescope_interface.capture_to_fit(3, ra, dec, "test", "ps")
            solution = self.solver.resolve(image, ra, dec, 90)
            print(solution, ra, dec)
            if solution['ra']==ra:
                final=True

    def _execute_plan(self, plan: list[Observation]):

        plan = sorted(self.plan, key=lambda obs: obs.start)
        for i, obs in enumerate(plan):
            if self._stop_requested:
                logger.info("[Scheduler] Stop during execution.")
                return
            now = datetime.now()
            start_hour = int(obs.start)
            start_minute = int((obs.start - start_hour) * 60)
            start_second = int((((obs.start - start_hour) * 60) - start_minute) * 60)
            start_time = datetime(
                year=now.year, month=now.month, day=now.day,
                hour=start_hour, minute=start_minute, second=start_second,
            )


            wait_seconds = (start_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.info(f"[Scheduler] Waiting {wait_seconds:.1f}s for {obs.object}")
                waited = 0
                while waited < wait_seconds:
                    if self._stop_requested:
                        return
                    time.sleep(min(1, wait_seconds - waited))
                    waited += 1

            captures_done = 0
            next_time = None

            if i + 1 < len(plan):
                inc = 0

                next_obs = plan[i + 1]
                if next_obs.start>24:
                    if datetime.now().hour > 12:
                        inc = 1
                    next_obs.start = next_obs.start - 24
                next_hour = int(next_obs.start)
                next_minute = int((next_obs.start - next_hour) * 60)
                next_second = int((((next_obs.start - next_hour) * 60) - next_minute) * 60)
                next_time = datetime(
                    year=now.year, month=now.month, day=now.day+inc,
                    hour=next_hour, minute=next_minute, second=next_second,
                    tzinfo=timezone.utc
                )

            #if not telescope_state.is_focused or obs.focus:
            #    self.telescope_interface.get_focus()
            #    telescope_state.is_focused = True
                
            self.slew_to_target(obs.ra, obs.dec)
            
            while captures_done < obs.number:
                if self._stop_requested:
                    return


                if next_time and datetime.now(timezone.utc) >= next_time:
                    logger.info(f"[Scheduler] Next observation time reached. Skipping remaining captures.")
                    break

                logger.info(f"[Scheduler] Capture {captures_done+1}/{obs.number} of {obs.object}")
                self.telescope_interface.capture_to_fit(
                    exposure=obs.expo,
                    ra=obs.ra,
                    dec=obs.dec,
                    filter_name=obs.filter,
                    target_name=obs.object
                )
                captures_done += 1

    def request_stop(self):
        self._stop_requested = True


def main():
    from services.telescope_interface import telescope_interface

    # Exemple d'utilisation
    scheduler = Scheduler(telescope_interface)

    # Envoi d'un plan d'observation
    plan = [
        Observation(start=0.5, expo=10, number=2, ra=10.684, dec=41.269, filter='R', object='Andromeda', focus=False),
        Observation(start=1.0, expo=5, number=3, ra=10.684, dec=41.269, filter='G', object='Andromeda',focus=False)
    ]
    scheduler.plan = plan
    scheduler.start()
    print("[Scheduler] Sending Plan  to scheduler.")

    print("[Scheduler] Plan sent to scheduler.")
    # Arrêt du scheduler après 5 secondes
    time.sleep(5)
    print("[Scheduler] stopping scheduler.")
    scheduler.request_stop()
    scheduler.join()


if __name__ == "__main__":
    main()

from queue import Queue, Empty
from datetime import datetime, timezone
import threading
import time
from models.observation import StopScheduler, Observation


class Scheduler(threading.Thread):
    def __init__(self, ascom_client):
        super().__init__(daemon=True)
        self.ascom_client = ascom_client
        self._stop_requested = False

    def run(self):
        print("[Scheduler] Started in background thread.")
        self._execute_plan(self.plan)

    def _execute_plan(self, plan: list[Observation]):
        plan = sorted(self.plan, key=lambda obs: obs.start)
        for i, obs in enumerate(plan):
            if self._stop_requested:
                print("[Scheduler] Stop during execution.")
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
                print(f"[Scheduler] Waiting {wait_seconds:.1f}s for {obs.object}")
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
            
            while captures_done < obs.number:
                if self._stop_requested:
                    return


                if next_time and datetime.now(timezone.utc) >= next_time:
                    print(f"[Scheduler] Next observation time reached. Skipping remaining captures.")
                    break

                print(f"[Scheduler] Capture {captures_done+1}/{obs.number} of {obs.object}")
                self.ascom_client.capture(
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
    
    class DummyASCOMClient:
        def capture(self, exposure, ra, dec, filter_name, target_name):
            print(f"[ASCOM] Capturing {exposure}s on {target_name}...")
            time.sleep(exposure)  # Simuler le temps d'expo
    # Exemple d'utilisation
    scheduler = Scheduler(DummyASCOMClient())

    # Envoi d'un plan d'observation
    plan = [
        Observation(start=0.5, expo=10, number=2, ra=10.684, dec=41.269, filter='R', object='Andromeda'),
        Observation(start=1.0, expo=5, number=3, ra=10.684, dec=41.269, filter='G', object='Andromeda')
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

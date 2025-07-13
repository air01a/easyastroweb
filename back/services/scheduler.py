from datetime import datetime, timezone
import threading
import time
from models.observation import StopScheduler, Observation
from models.state import telescope_state
from utils.logger import logger
from services.configurator import CONFIG
from utils.calcul import get_solver, get_slew_error
from pathlib import Path
from imageprocessing.fitsstacker import Config, LiveStacker
from imageprocessing.fitsprocessor import FitsImageManager
from imageprocessing.astrofilters import AstroFilters

class Scheduler(threading.Thread):
    def __init__(self, telescope_interface):
        super().__init__(daemon=True)
        self.telescope_interface = telescope_interface
        self._stop_requested = False
        self.solver = get_solver(CONFIG)
        self.has_fw = self.telescope_interface.filter_wheel_connect() if len(CONFIG['filterwheel'].get("filters", []))>1 else False
        self.stacker_config = Config()
        self.stacker = LiveStacker(self.stacker_config, self._on_image_stack)
        self.fit_path = Path(CONFIG['global'].get("fits_storage_dir")).resolve()
        self.fit_path.mkdir(parents=True, exist_ok=True)
        self.fits_manager=FitsImageManager()
        self.astro_filters=AstroFilters()
        self.is_running = False


    def run(self):
        logger.info("[SCHEDULER] Started in background thread.")
        self._execute_plan(self.plan)

    def slew_to_target(self, ra: float, dec: float):
        logger.info(f"[SCHEDULER] - Slewing to {ra}/{dec}")
        final=False
        retry=0
        while not final and retry < CONFIG['global']['astap_slew_max_retry'] and not self._stop_requested:
            try:
                self.telescope_interface.slew_to_target(ra, dec)
            except Exception as e:
                logger.error(f"[SCHEDULER] - Error while slewing {e}")
            image:Path = self.telescope_interface.capture_to_fit(3, ra, dec, "ps", "ps",self.fit_path)
            logger.info("[SCHEDULER] - Plate Solving")

            solution = self.solver.resolve(image, ra, dec, CONFIG['global'].get("astap_default_search_radius",10))
            if solution['error']==0:

                self.telescope_interface.sync_to_coordinates(ra, dec)
                error = get_slew_error(ra, dec, solution['ra'], solution['dec'])
                logger.info(f"[SCHEDULER] - Position error {error}")

                if error<CONFIG['global']['astap_acceptable_error']:
                    logger.info("[SCHEDULER] - slewing done")
                    final=True
            else:
                logger.error(f"[SCHEDULER] - Error Solving {image}")
             
            retry+=1
            try:
                for ext in ['.wcs', '.ini']:
                    wcs = image.with_suffix(ext)

                    if wcs.exists():
                        wcs.unlink()
                if image.exists():
                    image.unlink()
            except:
                pass
        self.telescope_interface.telescope_set_tracking(0)
        return final
    

    def _on_image_stack(self, path: Path):
        image = self.fits_manager.open_fits(f"{path}")
        image.data  = self.astro_filters.denoise_gaussian(self.astro_filters.replace_lowest_percent_by_zero(self.astro_filters.auto_stretch(image.data, 0.25, algo=1, shadow_clip=-2),80))
        self.fits_manager.save_as_image(image, output_filename=f"{path}".replace(".fit",".jpg"))
        telescope_state.last_stacked_picture = path.with_suffix(".jpg")
        

    def _execute_plan(self, plan: list[Observation]):
        plan = sorted(self.plan, key=lambda obs: obs.start)
        self.is_running=True
        for i, obs in enumerate(plan):
            if self._stop_requested:
                logger.info("[SCHEDULER] Stop during execution.")
                break
            
            if self.has_fw:
                logger.info("[SCHEDULER] - Changing filter")
                self.telescope_interface.change_filter(obs.filter)

            now = datetime.now()
            start_hour = int(obs.start)
            start_minute = int((obs.start - start_hour) * 60)
            start_second = int((((obs.start - start_hour) * 60) - start_minute) * 60)
            start_time = datetime(
                year=now.year, month=now.month, day=now.day,
                hour=start_hour, minute=start_minute, second=start_second,
            )

            wait_seconds = (start_time - datetime.now()).total_seconds()

            wait_seconds=0
            if wait_seconds > 0:
                logger.info(f"[SCHEDULER] Waiting {wait_seconds:.1f}s for {obs.object}")
                waited = 0
                while waited < wait_seconds:
                    if self._stop_requested:
                        logger.info("[SCHEDULER] Stop requested during wait.")
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
                )

            if CONFIG["telescope"].get("has_focuser", False) and (not telescope_state.is_focused or obs.focus):
                logger.info("[SCHEDULER] - FOCUS process")
                self.telescope_interface.get_focus()
                telescope_state.is_focused = True
                
            if not self.slew_to_target(obs.ra, obs.dec):
                logger.error("[SCHEDULER] - Failed to slew to target")
                continue
                
            self.stacker.start_live_stacking()
            while captures_done < obs.number:
                if self._stop_requested:
                    logger.info("[SCHEDULER] Stop requested during capture.")
                    break
                
                if next_time and datetime.now() >= next_time:
                    
                    logger.info(f"[SCHEDULER] Next observation time reached. Skipping remaining captures.")
                    break

                logger.info(f"[SCHEDULER] Capture {captures_done+1}/{obs.number} of {obs.object}")
                image= self.telescope_interface.capture_to_fit(
                    exposure=obs.expo,
                    ra=obs.ra,
                    dec=obs.dec,
                    filter_name=obs.filter,
                    target_name=obs.object,
                    path=self.fit_path
                )
                self.stacker.process_new_image(image)
                captures_done += 1
            self.stacker.stop_live_stacking()

        logger.info("[SCHEDULER] Execution completed.")
        self.is_running=False
        telescope_state.plan_active=False


    def request_stop(self): 
        self._stop_requested = True
        logger.info("[Scheduler] Stop requested.")
        self.is_running=False
        telescope_state.plan_active=False



def main():
    from services.telescope_interface import telescope_interface

    # Exemple d'utilisation
    scheduler = Scheduler(telescope_interface)
    try:
        # Envoi d'un plan d'observation
        plan = [
            Observation(start=15, expo=10, number=100, ra=10.684, dec=41.269, filter='Dual Band', object='Andromeda', focus=False),
            Observation(start=15.6, expo=10, number=30, ra=10.684, dec=41.269, filter='UV', object='Andromeda2',focus=False)
        ]
        scheduler.plan = plan
        scheduler.start()
        print("[SCHEDULER] Plan sent to scheduler.")
        
        # Attendre que le thread se termine ou qu'une interruption se produise
        while scheduler.is_alive():
            try:
                scheduler.join(timeout=1)  # Attendre 1 seconde
            except KeyboardInterrupt:
                print("\n[Main] Keyboard interrupt received. Stopping scheduler...")
                scheduler.request_stop()
                break
        
        # Attendre que le thread se termine proprement
        scheduler.join(timeout=5)
        if scheduler.is_alive():
            print("[Main] Warning: Scheduler thread did not stop within 5 seconds")
        else:
            print("[Main] Scheduler stopped successfully")
            
    except Exception as e:
        print(f"[Main] Error: {e}")
        scheduler.request_stop()
        scheduler.join(timeout=5)


if __name__ == "__main__":
    main()
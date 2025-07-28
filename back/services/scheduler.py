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
from services.dark_manager import DarkManager
from ws.websocket_manager import ws_manager
from services.history_manager import HistoryManager
from models.basic_automate import BasicAutomate

class Scheduler(BasicAutomate):
    def __init__(self, telescope_interface):
        super().__init__(telescope_interface, name="SCHEDULER")
        
        self.fit_path = Path(CONFIG['global'].get("fits_storage_dir")).resolve()
        self.fit_path.mkdir(parents=True, exist_ok=True)
        self.fits_manager=FitsImageManager(True, True)
        self.astro_filters=AstroFilters()
        self.dark_config = Path(CONFIG['global'].get("dark_directory")) / Path("config.json")
        self.history = HistoryManager()



    def _on_image_stack(self, path: Path):
        try:
            image = self.fits_manager.open_fits(f"{path}")
            image.data  = self.astro_filters.denoise_gaussian(self.astro_filters.replace_lowest_percent_by_zero(self.astro_filters.auto_stretch(image.data, 0.20, algo=1, shadow_clip=-2),80))
            self.fits_manager.save_as_image(image, output_filename=f"{path}".replace(".fit",".jpg"))
            telescope_state.last_stacked_picture = Path(path).with_suffix(".jpg")
            self.history.update_obs_image(None, telescope_state.last_stacked_picture)
            ws_manager.broadcast_sync(ws_manager.format_message("SCHEDULER","NEWIMAGE"))
        except Exception as ex: 
            logger.error("[SCHEDULER] - Error while transforming siril new image")
            """import traceback

            tb = traceback.extract_tb(ex.__traceback__)
            last_call = tb[-1]  # dernière ligne de la pile
            filename = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name

            logger.error(f"[FITSSTACKER] - Erreur dans {function_name}() ({filename}:{line_number}): {ex}")
            logger.debug("Traceback complet :\n" + "".join(traceback.format_tb(ex.__traceback__)))"""
        

    def _execute_plan(self, plan: list[Observation]):
        plan = sorted(self.plan, key=lambda obs: obs.start)
        self.history.add_plan(plan)
        self.is_running=True

        temperature, cooler_on = self.set_temperature()

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

            wait_seconds = (start_time - datetime.now()).total_seconds() if not CONFIG["global"].get("mode_debug", False) else 0


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
                self.set_status("focusing")
                self.telescope_interface.get_focus(obs.ra, obs.dec)
                telescope_state.is_focused = True
                
            if not self.slew_to_target(obs.ra, obs.dec):
                logger.error("[SCHEDULER] - Failed to slew to target")
                continue

            
            dark=DarkManager.choose_dark(self.dark_config, obs.expo, obs.gain, temperature, CONFIG.get('camera',{}).get("id",""))

            logger.info(f"[SCHEDULER] - Using Dark {dark}")
            
            directory = self.fit_path / Path(f"{time.strftime('%Y-%m-%d')}-{obs.object.replace(' ', '_')}")
            directory.mkdir(exist_ok=True)

            self.stacker_config = Config(directory / Path("session"), batch_size=CONFIG['global'].get('fits_batch_size',150), initial_batch_size=CONFIG['global'].get('initial_batch_size',140))
            self.stacker = LiveStacker(self.stacker_config, self._on_image_stack)
            self.stacker.add_dark(dark)

            self.stacker.start_live_stacking()
            self.history.new_obs()
            while captures_done < obs.number:
                self.set_status("capturing")
                if self._stop_requested:
                    logger.info("[SCHEDULER] Stop requested during capture.")
                    break
                
                if next_time and datetime.now() >= next_time:
                    
                    logger.info(f"[SCHEDULER] Next observation time reached. Skipping remaining captures.")
                    break

                logger.info(f"[SCHEDULER] Capture {captures_done+1}/{obs.number} of {obs.object}")
                image= self.telescope_interface.capture_to_fit(
                    exposure=obs.expo,
                    gain=obs.gain,
                    ra=obs.ra,
                    dec=obs.dec,
                    filter_name=obs.filter,
                    target_name=obs.object,
                    path=directory
                )
                self.stacker.process_new_image(image)
                captures_done += 1
                self.history.update_obs_image(captures_done)
            
            # Update History for plan information


            self.history.close_obs()
            self.history.save_history()
            ws_manager.broadcast_sync(ws_manager.format_message("SCHEDULER","REFRESHINFO"))
            self.stacker.stop_live_stacking()

        logger.info("[SCHEDULER] Execution completed.")
        if temperature:
            logger.info("[SCHEDULER] - Turning off cooler")
            self.telescope_interface.set_cooler(False)
        self.is_running=False
        telescope_state.plan_active=False
        ws_manager.broadcast_sync(ws_manager.format_message("SCHEDULER","REFRESHINFO"))
        self.set_status("finished")


    def request_stop(self): 
        self._request_stop()
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
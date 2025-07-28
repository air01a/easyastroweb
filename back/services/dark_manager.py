from datetime import datetime, timezone
import threading
import time
from models.state import telescope_state
from utils.logger import logger
from services.configurator import CONFIG
from pathlib import Path
from imageprocessing.fitsprocessor import FitsImageManager
from models.api import DarkLibraryProcessType, DarkLibraryItem
import numpy as np
import json
from typing import Optional, Union
from ws.websocket_manager import ws_manager
from models.basic_automate import BasicAutomate


class DarkManager(BasicAutomate):
    def __init__(self, telescope_interface, camera: str, plan: list[DarkLibraryProcessType]):
        super().__init__(telescope_interface, name="DARKMANAGER")
        self.fit_path = Path(CONFIG['global'].get("dark_directory")).resolve() / Path(camera)
        self.fit_config = Path(CONFIG['global'].get("dark_directory")).resolve() / Path("config.json")
        self.fit_path.mkdir(parents=True, exist_ok=True)
        self.fits_manager=FitsImageManager()
        self.plan = plan
        self.camera = camera


    def get_dark_config(fit_config: Path, transform_object=False):
        if not fit_config.exists():
            return {}
        
        with fit_config.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if transform_object:
            dark_dict_loaded = {
                key: [DarkLibraryItem(**item) for item in items]
                for key, items in data.items()
            }
            return dark_dict_loaded
        return data
        
    def choose_dark(config: Path, exposition: int, gain: int, temperature: Union[int,None], camera : str):
        config = DarkManager.get_dark_config(config, True)
        if not camera in config.keys():
            return None
        darks = config[camera]
        for dark in darks : 
            if dark.exposition==exposition and dark.gain==gain:
                if (not temperature) or (temperature and temperature==dark.temperature):
                    return Path(dark.filename)
            
        return None


    def save_dark_config(fit_config: Path, data, already_serialized: bool = False):
        if already_serialized:
            serializable_dict= data
        else:
            serializable_dict = {
                key: [item.dict() for item in items]
                for key, items in data.items()
            }
        with fit_config.open("w", encoding="utf-8") as f:
            json.dump(serializable_dict, f, indent=2)

    def get_dark_item_by_camera_and_date(
        dark_dict: dict[str, list[Union[DarkLibraryItem, dict]]],
        camera: str,
        date: str
    ) -> Optional[DarkLibraryItem]:
       
        items = dark_dict.get(camera, [])
        
        for item in items:
            try:
                item_obj = item if isinstance(item, DarkLibraryItem) else DarkLibraryItem(**item)
                if item_obj.date == date:
                    return item_obj
            except Exception as e:
                # log possible ou passer
                continue  # item mal formé, on ignore

        return None


    def add_to_config(self, obs: DarkLibraryProcessType, date: str, file:str):
        config = DarkManager.get_dark_config(self.fit_config, True)
        new_item = DarkLibraryItem(gain =obs.gain, temperature=obs.temperature, exposition=obs.exposition, count=obs.count, date=date, filename=file)
        if self.camera in config.keys():
            config[self.camera].append(new_item)
        else:
            config[self.camera]=[new_item]
        DarkManager.save_dark_config(self.fit_config, config)

        
    def _execute_plan(self, plan: list[DarkLibraryProcessType]):
        
        self.is_running=True
        self.plan = plan
        for i,_ in enumerate(plan):
            self.plan[i].eta = plan[i].exposition * plan[i].count


        temperature, cooler_on = self.set_temperature()

        for i, obs in enumerate(plan):
            self.plan[i].in_progress=True
            if self._stop_requested:
                logger.info("[DARKMANAGER] Stop during execution.")
                break

            captures_done = 0
                
            try:
                self.telescope_interface.set_camera_gain(obs.gain)
            except Exception as e:
                logger.error("[DARKMANAGER] Error setting gain")
            dark = None    
            self.set_status("CAPTURING")

            while captures_done < obs.count:

                if self._stop_requested:
                    logger.info("[DARKMANAGER] Stop requested during capture.")
                    break

                logger.info(f"[DARKMANAGER] Capture {captures_done+1}/{obs.count} for expo {obs.exposition}")
                image = self.telescope_interface.camera_capture(expo=obs.exposition, light=False)
                if dark:
                    dark.data += image.data.astype(np.float64) / obs.count
                else:
                    dark = image
                    dark.data = dark.data.astype(np.float64)
                    dark.data /= obs.count
                
                captures_done += 1
                ws_manager.broadcast_sync(ws_manager.format_message("DARKMANAGER","NEWIMAGE"))

                self.plan[i].eta = max(0, self.plan[i].eta-obs.exposition)
                self.plan[i].progress = captures_done
            if self._stop_requested:
                logger.info("[DARKMANAGER] Stop requested during capture.")
                break
            

            now = time.strftime('%Y-%m-%dT%H.%M.%S')
            filename = self.fit_path / Path(f"dark_{obs.exposition}_{obs.gain}_{obs.temperature}.fits")
            FitsImageManager.save_fits_from_array(image.data, filename, self.telescope_interface.get_fit_header(obs.exposition, obs.gain))
            ws_manager.broadcast_sync(ws_manager.format_message("DARKMANAGER","NEWIMAGE"))

            self.add_to_config(obs, now, f"{filename.resolve()}")
            self.plan[i].done=True

        self.set_status("finished")
        logger.info("[DARKMANAGER] Execution completed.")
        self.is_running=False
        telescope_state.dark_processor=None
        if cooler_on:
            logger.info("[DARKMANAGER] - Turning off cooler")
            self.telescope_interface.set_cooler(False)


    def request_stop(self): 
        self._request_stop()
        telescope_state.dark_processor=None



def main():
    from services.telescope_interface import telescope_interface

    # Exemple d'utilisation
    telescope_interface.connect()
    try:
        # Envoi d'un plan d'observation
        plan = [
            DarkLibraryProcessType(gain=100,temperature=10, exposition=30, count=1, eta=0, in_progress=False, done=False),
            DarkLibraryProcessType(gain=100,temperature=20, exposition=30, count=10, eta=0, in_progress=False, done=False),
        ]

        scheduler = DarkManager(telescope_interface, "AZZZ", plan)
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
    print(DarkManager.choose_dark(Path("../dark/config.json"),10,100,-15,"FHaUs3"))
    #main()
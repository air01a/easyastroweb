import threading
import time

from utils.logger import logger
from services.configurator import CONFIG
from utils.calcul import get_solver, get_slew_error
from pathlib import Path
from imageprocessing.fitsprocessor import FitsImageManager
from ws.websocket_manager import ws_manager

from abc import ABC, abstractmethod
from numpy import uint8
from services.focuser import AutoFocusLib


class BasicAutomate(threading.Thread, ABC):
    def __init__(self, telescope_interface, name: str):
        global CONFIG
        super().__init__(daemon=True)
        self.telescope_interface = telescope_interface
        self._stop_requested = False
        self.name = name
        self.solver = get_solver(CONFIG)
        self.has_fw = self.telescope_interface.filter_wheel_connect() if len(CONFIG['filterwheel'].get("filters", []))>1 else False
        self.status = "not_started"
        self.is_running = False
        self.autofocus = AutoFocusLib()


    def set_status(self,status:str, provider:str=None, type="STATUS"):
        if not provider:
            provider = self.name.upper()
        self.status = status
        ws_manager.broadcast_sync(ws_manager.format_message(provider,type,status))

    def run(self):
        logger.info("[SCHEDULER] Started in background thread.")
        self._execute_plan(self.plan)

    def slew_to_target(self, ra: float, dec: float):
        logger.info(f"[{self.name}] - Slewing to {ra}/{dec}")
        final=False
        retry=0
        self.set_status("slewing")
        while not final and retry < CONFIG['global']['astap_slew_max_retry'] and not self._stop_requested:
            try:
                self.telescope_interface.slew_to_target(ra, dec)
            except Exception as e:
                logger.error(f"[{self.name}] - Error while slewing {e}")
            image:Path = self.telescope_interface.capture_to_fit(3, ra, dec, "ps", "ps",self.fit_path, gain=CONFIG.get('camera',{}).get('default_gain',100))
            logger.info(f"[{self.name}] - Plate Solving")
            self.set_status("plate_solving")
            solution = self.solver.resolve(image, ra, dec, CONFIG['global'].get("astap_default_search_radius",10))
            if solution['error']==0:

                self.telescope_interface.sync_to_coordinates(ra, dec)
                error = get_slew_error(ra, dec, solution['ra'], solution['dec'])
                logger.info(f"[{self.name}] - Position error {error}")

                if error<CONFIG['global']['astap_acceptable_error']:
                    logger.info("[{self.name}] - slewing done")
                    final=True
            else:
                logger.error(f"[{self.name}] - Error Solving {image}")
             
            retry+=1
            try:
                if not CONFIG["global"].get("mode_debug", False):
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
    

    def set_temperature(self) -> tuple[int, bool]:
        if CONFIG.get('camera',{}).get("is_cooled", False):
            temperature = CONFIG.get('camera',{}).get("temperature",0)
            if temperature is not None:
                try:
                    logger.info(f"[{self.name}] - Setting camera temperature to {temperature}°C")
                    self.telescope_interface.set_ccd_temperature(temperature)
                    self.telescope_interface.set_cooler(True)

                    while True:
                        time.sleep(5)
                        current_temp = self.telescope_interface.get_ccd_temperature()
                        self.set_status(f"{self.telescope_interface.get_ccd_temperature()} / {temperature}°C", "SCHEDULER", "TEMPERATURE")
                        if self._stop_requested:
                            logger.info("[{self.name}] Stop during execution.")
                            return None, True
                        if abs(current_temp - temperature) < 1:
                            logger.info(f"[{self.name}] - Camera temperature reached {current_temp}°C")
                            return (temperature, True)
                except Exception as e:
                    logger.error(f"[{self.name}] - Error setting camera temperature: {e}")
                    return None, False
        return None, False


    @abstractmethod
    def _execute_plan(self,  *args, **kwargs):
       pass


    def _request_stop(self): 
        self._stop_requested = True
        logger.info("[Scheduler] Stop requested.")
        self.is_running=False
        self.set_status("stopped")


    def get_focus(self, ra: float, dec: float):
        self.set_status(f"Finding good stars area for focusing", "FOCUSER", "STATUS")
        dec = 70 + CONFIG['observatory'].get("latitude", 50) + dec - 90

        self.telescope_interface.telescope_set_tracking(0)
        stars=0
        while stars < 10:
            logger.info(f"[Focuser] - Slewing to RA: {ra}, DEC: {dec}")

            self.telescope_interface.slew_to_target(ra, dec)
            image = self.telescope_interface.camera_capture(CONFIG['global'].get("focuser_exposition", 4))
            if image is None:
                logger.error("[Focuser] - Error capturing image")
            image.data = (image.data / 255).astype(uint8)
            stars = self.autofocus.count_stars(image.data)
            logger.info(f"[Focuser] - Found {stars} stars in the image")
            ra = (ra+2) % 24

        self.set_status(f"Focusing", "FOCUSER", "STATUS")

        current_position = self.telescope_interface.focuser_get_current_position()
        focuser_range = CONFIG['camera'].get('focuser_range', 250)
        focuser_step = CONFIG['camera'].get('focuser_step', 50)
        positions = list(range(current_position-focuser_range, current_position+focuser_range, focuser_step))

        for position in positions:
            logger.info(f"[Focuser] - Moving to position {position}")

            self.telescope_interface.move_focuser(position)
            for i in range(CONFIG['global'].get('focuser_image_by_position',1)):
                logger.info(f"[Focuser] - MTaking picture {i}")
                try:
                    #image = (self.camera_capture(CONFIG['global'].get('focuser_exposition',4)).data/255).astype(np.uint8)
                    image=(FitsImageManager.quick_process(self.telescope_interface.capture_to_fit(CONFIG['global'].get('focuser_exposition',4),0,0,f"{position}","",Path(CONFIG['global'].get("fits_storage_dir")).resolve(),100)).data/255).astype(uint8)
                    ws_manager.broadcast_sync(ws_manager.format_message("FOCUSER","NEWIMAGE"))
                except Exception as e:
                    logger.error(f"[FOCUS] - Error capturing image {e}")
                result = self.autofocus.analyze_image(image,position)
                self.set_status(f"Focusing at {position}, FWHM : [{result['fwhm']}]", "FOCUSER", "STATUS")

                if not result['valid']:
                    logger.error("[Focuser] - Invalid capture for autofocus")

        best_position, best_method, details = self.autofocus.calculate_best_focus()
        logger.info(f"[Focuser] - Results {best_position}, method={best_method}")

        self.telescope_interface.move_focuser(best_position)

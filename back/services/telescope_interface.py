from services.alpaca_client import alpaca_camera_client, alpaca_focuser_client, alpaca_telescope_client, ExposureSettings, CameraState
from time import sleep
from abc import ABC, abstractmethod
from services.focuser import AutoFocusLib
import time
from imageprocessing.fitsprocessor import FitsImageManager
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from pathlib import Path

class TelescopeInterface(ABC):

    def __init__(self):
        self.autofocus = AutoFocusLib()
 
    @abstractmethod
    def camera_capture(self, expo: float):
        pass
    
    @abstractmethod
    def move_focuser(self, position: int):
        pass

    @abstractmethod
    def camera_connect(self):
        pass
    
    @abstractmethod
    def focuser_connect(self):
        pass

    @abstractmethod
    def focuser_get_current_position(self):
        pass

    @abstractmethod
    def slew_to_target(self, ra: float, dec: float):
        pass

    @abstractmethod
    def telescope_connect(self):
        pass
    
    @abstractmethod
    def telescope_unpark(self):
        pass

    @abstractmethod
    def sync_to_coordinates(ra: float, dec: float):
        pass

    def get_focus(self):
        current_position = self.focuser_get_current_position()
        focuser_range = CONFIG['global'].get('focuser_range', 250)
        focuser_step = CONFIG['global'].get('focuser_step', 50)
        positions = list(range(current_position-focuser_range, current_position+focuser_range, focuser_step))

        for position in positions:
            logger.info(f"[Focuser] - Moving to position {position}")
            self.move_focuser(position)
            for i in range(CONFIG['global'].get('focuser_image_by_position',1)):
                logger.info(f"[Focuser] - MTaking picture {i}")
                try:
                    image = (self.camera_capture(CONFIG['global']['focuser_exposition']).data/255).astype(np.uint8)
                except:
                    logger.error("[FOCUS] - Error capturing image")
                result = self.autofocus.analyze_image(image,position)
                if not result['valid']:
                    logger.error("[Focuser] - Invalid capture for autofocus")

        best_position, best_method, details = self.autofocus.calculate_best_focus()
        logger.info(f"[Focuser] - Results {best_position}, method={best_method}")
        self.move_focuser(best_position)

    def capture_to_fit(self, exposure, ra, dec, filter_name, target_name, path: Path) :

        image = self.camera_capture(exposure)
        header={}

        header["EXPTIME"] = 1
        header['DATE-OBS'] = time.strftime('%Y-%m-%dT%H.%M.%S')
        header['RA'] = ra
        header['DEC'] = dec
        file_name = path / f"capture-{target_name}-{filter_name}-{header['DATE-OBS']}.fits"
        FitsImageManager.save_fits_from_array(image.data, file_name, header)
        return file_name
    

    
class AlpacaTelescope(TelescopeInterface):
    def camera_capture(self, expo: float):
        try:
            expo = ExposureSettings(duration=expo)
            alpaca_camera_client.start_exposure(expo)
            while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
                sleep(1)
            image =  alpaca_camera_client.get_image_array()
            image.data = np.array(image.data)
            return image
        except Exception as e:
            print(e)
            return None

    def camera_connect(self):
        return alpaca_camera_client.connect()

    def move_focuser(self, position: int):
        alpaca_focuser_client.move_absolute(position)
        while alpaca_focuser_client.is_moving():
            sleep(1)
        sleep(1)

    def focuser_connect(self):
        alpaca_focuser_client.connect()

    def focuser_get_current_position(self):
        return alpaca_focuser_client.get_position()

    def telescope_connect(self):
        return alpaca_telescope_client.connect()

    def slew_to_target(self,ra: float, dec: float):
        print(ra, dec)
        alpaca_telescope_client.slew_to_coordinates(ra, dec)
        while alpaca_telescope_client.is_slewing():
            time.sleep(1)

    def sync_to_coordinates(self, ra:float, dec: float):
        alpaca_telescope_client.sync_to_coordinates(ra, dec)

    def telescope_unpark(self):
        alpaca_telescope_client.unpark()


telescope_interface = AlpacaTelescope()




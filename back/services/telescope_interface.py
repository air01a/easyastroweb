from services.alpaca_client import alpaca_camera_client, alpaca_focuser_client, alpaca_telescope_client, alpaca_fw_client, ExposureSettings, CameraState
from time import sleep
from abc import ABC, abstractmethod
from services.focuser import AutoFocusLib
import time
from imageprocessing.fitsprocessor import FitsImageManager
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from pathlib import Path
from models.state import telescope_state

class TelescopeInterface(ABC):
    def __init__(self):
        self.autofocus = AutoFocusLib()
        self.mount_name : str = "Not connected"
        self.fw_name : str = "Not connected"
        self.focuser_name : str = "Not connected"
        self.camera_name : str = "Not connected"
 
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
    def telescope_disconnect(self):
        pass

    @abstractmethod
    def telescope_set_tracking(self, rate : int):
        pass

    @abstractmethod
    def telescope_disconnect(self):
        pass
    
    @abstractmethod
    def telescope_unpark(self):
        pass

    @abstractmethod
    def sync_to_coordinates(ra: float, dec: float):
        pass

    @abstractmethod
    def filter_wheel_connect(self)-> bool:
        pass

    @abstractmethod
    def change_filter(self, filter)-> bool:
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

    def capture_to_fit(self, exposure : int, ra : float, dec : float, filter_name : str, target_name, path: Path) :

        image = self.camera_capture(exposure)
        header={}

        header["EXPTIME"] = 1
        header['DATE-OBS'] = time.strftime('%Y-%m-%dT%H.%M.%S')
        header['RA'] = ra
        header['DEC'] = dec
        file_name = path / f"capture-{target_name.replace(" ", "_")}-{filter_name.replace(" ", "_")}-{header['DATE-OBS']}.fits"
        if image is None:
            logger.error("[CAPTURE] - Error capturing image")
            return None
        FitsImageManager.save_fits_from_array(image.data, file_name, header)
        return file_name
    
    @abstractmethod
    def connect(self):
        pass
    

    
class AlpacaTelescope(TelescopeInterface):
    def camera_capture(self, expo: float):
        try:
            expo = ExposureSettings(duration=expo)
            alpaca_camera_client.start_exposure(expo)
            while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
                sleep(1)
            image =  alpaca_camera_client.get_image_array()
            image.data = np.array(image.data)
            telescope_state.last_picture = image.data
            return image
        except Exception as e:
            print(e)
            return None

    def camera_connect(self):
        self.camera_name = alpaca_camera_client.connect()
        return True

    def move_focuser(self, position: int):
        alpaca_focuser_client.move_absolute(position)
        while alpaca_focuser_client.is_moving():
            sleep(1)
        sleep(1)

    def focuser_connect(self):
        alpaca_focuser_client.connect()
        self.focuser_name = alpaca_focuser_client.get_name()

    def focuser_get_current_position(self):
        return alpaca_focuser_client.get_position()

    def telescope_connect(self):
        alpaca_telescope_client.connect()
        self.mount_name = alpaca_telescope_client.get_name()
        return True
    
    def telescope_disconnect(self):
        return alpaca_telescope_client.disconnect()

    def slew_to_target(self,ra: float, dec: float):
        alpaca_telescope_client.slew_to_coordinates(ra, dec)
        while alpaca_telescope_client.is_slewing():
            time.sleep(1)

    def sync_to_coordinates(self, ra:float, dec: float) -> bool:
        try:
            alpaca_telescope_client.sync_to_coordinates(ra, dec)
            return True
        except:
            return False

    def telescope_unpark(self):
        alpaca_telescope_client.unpark()

    def filter_wheel_connect(self)-> bool:
        try:
            alpaca_fw_client.connect()
            self.fw_name = alpaca_fw_client.get_name()
            return True
        except:
            return False

    def change_filter(self, filter)-> bool:
        #self.has_fw = self.telescope_interface.fw_connect() if len(CONFIG['filterwheel'].get("filters", []))>1 else False
        try:
            filters = CONFIG['filterwheel'].get("filters", [])
            index = filters.index(filter)
            logger.info(f"[FILTERWHEEL] - Moving to position {index}")

            alpaca_fw_client.set_position(index)
            return True
        except:
            logger.info(f"[FILTERWHEEL] - Error during filter change")
            return False

    def telescope_set_tracking(self, rate : int):
        alpaca_telescope_client.set_tracking_rate(rate)
        alpaca_telescope_client.set_tracking(True)
        
    def connect(self):
        try:
            telescope_interface.focuser_connect()
            telescope_state.is_focuser_connected = True
        except:
            telescope_state.is_focuser_connected = False
            
        try:
            telescope_interface.camera_connect()
            telescope_state.is_camera_connected = True
        except Exception as e:
            telescope_state.is_camera_connected = False
            print(f"[CAMERA] - Error connecting camera: {e}")

        try:
            telescope_interface.telescope_connect()
            telescope_state.is_telescope_connected = True
        except:
            telescope_state.is_telescope_connected = False  
        


telescope_interface = AlpacaTelescope()
telescope_interface.connect()








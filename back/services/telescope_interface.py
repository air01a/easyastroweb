from services.alpaca_client import alpaca_camera_client, alpaca_focuser_client, alpaca_telescope_client, alpaca_fw_client, ExposureSettings, CameraState
from time import sleep
import time
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from pathlib import Path
from models.state import telescope_state
from models.telescope_interface import TelescopeInterface

    
class AlpacaTelescope(TelescopeInterface):

    def __init__(self):
        super().__init__()
        self.fits_dir = Path("C:/Users/eniquet/Documents/dev/easyastroweb/utils/01-observation-m16/01-images-initial") #        "D:/Astronomie/observations/2024-02-12/DARK"

        self.fits_files =  (list(self.fits_dir.glob("*.fit")) + list(self.fits_dir.glob("*.fits")))
        self.index = 0

    def camera_capture(self, expo: float):
        try:
            expo = ExposureSettings(duration=expo)
            alpaca_camera_client.start_exposure(expo)
            while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
                sleep(1)
            image =  alpaca_camera_client.get_image_array()
            image.data = np.array(image.data)
            if image.data.ndim == 2:
                # Image en niveaux de gris : transposition classique
                image.data = np.array(image.data).T
            else:
                image.data = np.transpose(np.array(image.data), (1, 0, 2))
            telescope_state.last_picture = image.data
            #fits_manager = FitsImageManager(True, False)
        
            #new = fits_manager.open_fits(self.fits_files[self.index])
            #self.index=(self.index+1) % len(self.fits_files)
            #image.data=new.data
            return image
        except Exception as e:
            print(e)
            return None
        
    def set_gain(self, gain: int):
        logger.info(f"[CAMERA] - Setting gain to {gain}")
        alpaca_camera_client.set_camera_gain(gain)

    def set_camera_gain(self, gain: int):
        alpaca_camera_client.set_camera_gain(gain)
        return True

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
        try:
            alpaca_telescope_client.slew_to_coordinates(ra, dec)
            while alpaca_telescope_client.is_slewing():
                time.sleep(1)
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error slewing to target: {e}")
            return False

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
        

    def get_ccd_temperature(self)-> int:
        return round(alpaca_camera_client.get_ccd_temperature())

    def set_ccd_temperature(self, temperature:int)-> None:
        alpaca_camera_client.set_ccd_temperature(temperature)

    def set_cooler(self, cooler: bool):
        alpaca_camera_client.set_cooler_on(cooler)

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
if not CONFIG["global"].get("mode_debug", False):
    telescope_interface.connect()








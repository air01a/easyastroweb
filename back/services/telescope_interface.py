from services.alpaca_client import ImageData, alpaca_camera_client, alpaca_focuser_client, alpaca_telescope_client, alpaca_fw_client, ExposureSettings, CameraState
from time import sleep
import time
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from pathlib import Path
from models.state import telescope_state
from models.telescope_interface import TelescopeInterface
from imageprocessing.fitsprocessor import FitsImageManager
from utils.calcul import apply_focus_blur
from datetime import datetime, timezone

class AlpacaTelescope(TelescopeInterface):

    def __init__(self):
        super().__init__()


    def camera_capture(self, expo: float, light: bool = True):
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


    def sync_location(self, latitude: float, longitude : float, elevation: float):
        """
        Synchronize the telescope's location with the provided latitude, longitude, and elevation.
        """
        try:
            alpaca_telescope_client.set_elevation(elevation)
            alpaca_telescope_client.set_latitude(latitude)
            alpaca_telescope_client.set_longitude(longitude) 
            logger.info(f"[TELESCOPE] - Location synchronized to lat: {latitude}, lon: {longitude}, elev: {elevation}")
            return True
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error synchronizing location: {e}")
            return False

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

        if CONFIG["telescope"].get("has_gps", False):
            logger.info("[TELESCOPE] - Synchronizing location with GPS")
            self.sync_location(
                CONFIG["observatory"].get("latitude", 0.0), 
                CONFIG["observatory"].get("longitude", 0.0),
                CONFIG["observatory"].get("altitude", 0.0)
            )

    def get_bayer_pattern(self):
        sensor_type = alpaca_camera_client.camera_info.sensor_type
        
        if sensor_type == 0:
            return  'MONOCHROME', None, None
        elif sensor_type == 1:
            return  'COLOR', None, None
        elif sensor_type == 2:
            return  'RGGB', 'RGGB', 'BAYER'
        elif sensor_type == 3:
            return 'CMYG', 'CMYG', 'BAYER'

        elif sensor_type == 4:
            return 'CMYG2', 'CMYG2', 'BAYER'
        elif sensor_type == 5:
            return 'LRGB', None, None
        else:
            return 'UNKNOWN', None, None
        
    def set_utc_date(self, date: str):
        """ Set the date for the telescope.
        """

        logger.info(f"[TELESCOPE] - Setting date to {date}")
        alpaca_telescope_client.set_utc_date(date)

    def get_utc_date(self):
        return alpaca_telescope_client.get_utc_date()

    def get_telescope_location(self):
        return f"{alpaca_telescope_client.get_latitude()}°, {alpaca_telescope_client.get_longitude()}°, {alpaca_telescope_client.get_elevation()}m"


class SimulatorTelescope(TelescopeInterface):

    def __init__(self):
        super().__init__()
        self.fits_dir = Path(CONFIG["global"].get("simulator_light_directory",".")) #        "D:/Astronomie/observations/2024-02-12/DARK"
        self.fits_files =  (list(self.fits_dir.glob("*.fit")) + list(self.fits_dir.glob("*.fits")))
        self.fits_manager = FitsImageManager(auto_debayer=False)

        self.dark_dir = Path(CONFIG["global"].get("simulator_dark_directory",".")) #        "D:/Astronomie/observations/2024-02-12/DARK"
        self.dark_files =  (list(self.dark_dir.glob("*.fit")) + list(self.dark_dir.glob("*.fits")))
        logger.info(f"[SIMULATOR] - Found {len(self.fits_files)} FITS files in {self.fits_dir}")
        logger.info(f"[SIMULATOR] - Found {len(self.dark_files)} DARK FITS files in {self.dark_dir}")
        self.index = 0
        self.index_dark = 0
        self.focuser_name = "Simulator Focuser"
        self.focuser_position = 25000
        self.initial_temperature = 15
        self.target_temperature = 15
        self.bayer = None
        self.location = "0.0°, 0.0°, 0.0m"  # Default location

    def set_utc_date(self, date: str):
        """
        Set the date for the simulator.
        """
        logger.info(f"[SIMULATOR] - Setting date to {date}")
        # In a real implementation, this would set the date in the simulator environment.
        # Here we just log it for demonstration purposes.

    def camera_capture(self, expo: float, light: bool = True):
        try:
            if light:
        
                new = self.fits_manager.open_fits(self.fits_files[self.index])
                if self.focuser_position!=25000:
                    new.data = self.fits_manager.debayer(new.data, new.bayer_pattern)
                    new.data = apply_focus_blur(new.data, self.focuser_position, 25000, 0.01)
                    new.data = self.fits_manager._convert_to_bayer(new.data, new.bayer_pattern)
            
                self.index = (self.index + 1) % len(self.fits_files)

            else:
                new = self.fits_manager.open_fits(self.dark_files[self.index_dark])
                self.index_dark = (self.index_dark + 1) % len(self.dark_files)

            sleep(expo)
            self.bayer = new.bayer_pattern
            telescope_state.last_picture = new.data

            return new
        except Exception as e:
            print(e)
            return None
        
    def get_bayer_pattern(self):
        sensor_type = self.bayer
        
        if sensor_type == 'RGGB':
            return  'RGGB', 'RGGB', 'BAYER'
        elif sensor_type == 'CMYG':
            return 'CMYG', 'CMYG', 'BAYER'
        elif sensor_type == 'CMYG2':
            return 'CMYG2', 'CMYG2', 'BAYER'
        elif sensor_type == 'LRGB':
            return 'LRGB', None, None
        elif sensor_type == 'COLOR':
            return 'COLOR', None, None
        else:
            return 'MONOCHROME', None, None
        
    def set_gain(self, gain: int):
        logger.info(f"[CAMERA] - Setting gain to {gain}")

    def set_camera_gain(self, gain: int):
        return True

    def camera_connect(self):
        return True

    def move_focuser(self, position: int):
        self.focuser_position = position
        sleep(1)

    def focuser_connect(self):
        self.focuser_name = "test"

    def focuser_get_current_position(self):
        return self.focuser_position

    def telescope_connect(self):

        return True
    
    def telescope_disconnect(self):
        return True
    

    def sync_location(self, latitude: float, longitude : float, elevation: float):
        logger.info(f"[TELESCOPE] - Simulated location synchronized to lat: {latitude}, lon: {longitude}, elev: {elevation}")
        self.location = f"{latitude}°, {longitude}°, {elevation}m"


    def get_utc_date(self):
        return datetime.now(timezone.utc).isoformat()

    def get_telescope_location(self):
        return self.location


    def slew_to_target(self,ra: float, dec: float):
        try:

            time.sleep(1)
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error slewing to target: {e}")
            return False

    def sync_to_coordinates(self, ra:float, dec: float) -> bool:
        try:
            return True
        except:
            return False

    def telescope_unpark(self):
        pass

    def filter_wheel_connect(self)-> bool:
        try:
            return True
        except:
            return False

    def change_filter(self, filter)-> bool:
        try:
            filters = CONFIG['filterwheel'].get("filters", [])
            index = filters.index(filter)
            logger.info(f"[FILTERWHEEL] - Moving to position {index}")

            return True
        except:
            logger.info(f"[FILTERWHEEL] - Error during filter change")
            return False

    def telescope_set_tracking(self, rate : int):
        pass
        

    def get_ccd_temperature(self)-> int:
        if self.initial_temperature > self.target_temperature:
            self.initial_temperature -= 1
        else:
            self.initial_temperature += 1
        logger.info(f"[CCD] - Current temperature: {self.initial_temperature}°C")
        return self.initial_temperature

    def set_ccd_temperature(self, temperature:int)-> None:
        self.target_temperature = temperature
        pass
    def set_cooler(self, cooler: bool):
        pass


    def connect(self):
        try:
            telescope_state.is_focuser_connected = True
        except:
            telescope_state.is_focuser_connected = False
            
        try:
            telescope_state.is_camera_connected = True
        except Exception as e:
            telescope_state.is_camera_connected = False
            print(f"[CAMERA] - Error connecting camera: {e}")

        try:
            telescope_state.is_telescope_connected = True
        except:
            telescope_state.is_telescope_connected = False  
        try:
            self.sync_location(
                CONFIG["observatory"].get("latitude", 0.0),
                CONFIG["observatory"].get("longitude", 0.0),
                CONFIG["observatory"].get("altitude", 0.0)
            )
        
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error synchronizing location: {e}")
            
        self.mount_name = "Simulator Mount"
        self.fw_name = "Simulator Filter Wheel"
        self.camera_name = "Simulator Camera"
        self.focuser_name = "Simulator Focuser"

if CONFIG["global"].get("mode_simulator", False):
    logger.info("[TELESCOPE] - Running in simulator mode")
    telescope_interface = SimulatorTelescope()
else:
    telescope_interface = AlpacaTelescope()
if not CONFIG["global"].get("mode_debug", False):
    telescope_interface.connect()








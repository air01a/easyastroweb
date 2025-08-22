from services.drivers.alpaca_client import  alpaca_camera_client, alpaca_focuser_client, alpaca_telescope_client, alpaca_fw_client, ExposureSettings, CameraState
from time import sleep
import time
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from models.state import telescope_state
from models.telescope_interface import TelescopeInterface


class AlpacaTelescope(TelescopeInterface):

    def __init__(self):
        super().__init__()


    def camera_capture(self, expo: float, light: bool = True):
        try:
            expo_params = ExposureSettings(duration=expo)
            alpaca_camera_client.start_exposure(expo_params)
            sleep(expo)
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
            logger.error(f"[CAMERA] - Alpaca Error {e}")
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
        try:
            alpaca_telescope_client.connect()
            self.mount_name = alpaca_telescope_client.get_name()
            return True
        except Exception as e:
            logger.error(f"[TELESCOPE] - Connecting telescope: {e}")

    def get_max_focuser_step(self):
        try:
            return alpaca_focuser_client.get_max_step()
        except Exception as e:
            logger.error(f"[FOCUSER] - Focuser error: {e}")
            
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
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error slewing to target: {e}")
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

    def telescope_set_tracking(self, rate : int)->bool:
        try:
            alpaca_telescope_client.set_tracking_rate(rate)
            alpaca_telescope_client.set_tracking(True)
            return True
        except:
            logger.error("[TELESCOPE] - Error setting tracking")
            return False
        

    def get_ccd_temperature(self)-> int:
        return round(alpaca_camera_client.get_ccd_temperature())

    def set_ccd_temperature(self, temperature:int)-> bool:
        try:
            alpaca_camera_client.set_ccd_temperature(temperature)
            return True
        except Exception as e:
            logger.error('[CAMERA] - Error setting temperature')
            return False

    def set_cooler(self, cooler: bool)-> bool:
        try:
            alpaca_camera_client.set_cooler_on(cooler)
            return True
        except:
            logger.error('[CAMERA] - Error setting cooler on')



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
            self.focuser_connect()
            telescope_state.is_focuser_connected = True
        except:
            telescope_state.is_focuser_connected = False
            
        try:
            self.camera_connect()
            telescope_state.is_camera_connected = True
        except Exception as e:
            telescope_state.is_camera_connected = False
            logger.error(f"[CAMERA] - Error connecting camera: {e}")

        try:
            self.telescope_connect()
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
        try:
            return f"{alpaca_telescope_client.get_latitude()}°, {alpaca_telescope_client.get_longitude()}°, {alpaca_telescope_client.get_elevation()}m"
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error getting telescope location: {e}")



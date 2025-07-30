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
        self.mount_name : str = "Not connected"
        self.fw_name : str = "Not connected"
        self.focuser_name : str = "Not connected"
        self.camera_name : str = "Not connected"


    @abstractmethod
    def set_camera_gain(self, gain: int):
        pass
    
    @abstractmethod
    def camera_capture(self, expo: float, light: bool = True):
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
    def sync_location(self, latitude: float, longitude : float, elevation: float):
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

    @abstractmethod
    def get_ccd_temperature(self)-> int:
        pass

    @abstractmethod
    def set_ccd_temperature(self, temperature:int)-> int:
        pass

    @abstractmethod
    def get_bayer_pattern(self):
        pass

    @abstractmethod
    def set_utc_date(self, date: str):
        pass

    @abstractmethod
    def get_utc_date(self):
        pass

    @abstractmethod
    def get_telescope_location(self):
        pass


    def get_focus(self, ra: float, dec: float):

        dec = 70 + CONFIG['observatory'].get("latitude", 50) + dec - 90

        self.telescope_set_tracking(0)
        stars=0
        while stars < 10:
            logger.info(f"[Focuser] - Slewing to RA: {ra}, DEC: {dec}")

            self.slew_to_target(ra, dec)
            image = self.camera_capture(CONFIG['global'].get("focuser_exposition", 4))
            if image is None:
                logger.error("[Focuser] - Error capturing image")
            image.data = (image.data / 255).astype(np.uint8)
            stars = self.autofocus.count_stars(image.data)
            logger.info(f"[Focuser] - Found {stars} stars in the image")
            ra = (ra+2) % 24


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
                    image = (self.camera_capture(CONFIG['global'].get('focuser_exposition',4)).data/255).astype(np.uint8)
                except:
                    logger.error("[FOCUS] - Error capturing image")
                result = self.autofocus.analyze_image(image,position)
                if not result['valid']:
                    logger.error("[Focuser] - Invalid capture for autofocus")

        best_position, best_method, details = self.autofocus.calculate_best_focus()
        logger.info(f"[Focuser] - Results {best_position}, method={best_method}")
        self.move_focuser(best_position)
    
    def set_gain(self, gain: int):
        pass

    def get_fit_header(self, exposure: int, gain:int):
        sensor, bayer, color_type = self.get_bayer_pattern()
        header={}
        header['SENSOR'] = sensor
        if bayer:
            header['BAYERPAT']=bayer
        if color_type:
            header['COLORTYP']=color_type
        header["EXPTIME"] = exposure
        header["GAIN"] = gain
        header['DATE-OBS'] = time.strftime('%Y-%m-%dT%H.%M.%S')
        return header

    def capture_to_fit(self, exposure : int, ra : float, dec : float, filter_name : str, target_name, path: Path, gain : int) :
        self.set_gain(gain)
        image = self.camera_capture(exposure)
        header = self.get_fit_header(exposure, gain)
        header['RA'] = ra
        header['DEC'] = dec
        #header['NAXIS'] = image.data.ndim
        #header['NAXIS1'] = image.data.shape[1]  # largeur
        #header['NAXIS2'] = image.data.shape[0]  # hauteur

        #if (image.data.ndim==3):
        #    header['NAXIS3'] = image.data.shape[2]
        #header['CTYPE1'] = 'PIXELS'
        #header['CTYPE2'] = 'PIXELS'

        file_name = path / f"capture-{target_name.replace(' ', '_')}-{filter_name.replace(' ', '_')}-{header['DATE-OBS']}.fits"
        if image is None:
            logger.error("[CAPTURE] - Error capturing image")
            return None
        FitsImageManager.save_fits_from_array(image.data, file_name, header)
        return file_name
    
    @abstractmethod
    def connect(self):
        pass
    
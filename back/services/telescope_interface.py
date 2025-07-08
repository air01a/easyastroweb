from services.alpaca_client import alpaca_camera_client, alpaca_focuser_client, ExposureSettings, CameraState
from time import sleep
from abc import ABC, abstractmethod
from services.focuser import AutoFocusLib
import time
from imageprocessing.fitsprocessor import FitsImageManager

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
    def camera_connect():
        pass

    def get_focus(self):
        positions = list(range(24750, 25250, 50))

        for position in positions:
            self.move_focuser(position)
            for i in range(3):
                result = self.autofocus.analyze_image(self.camera_capture(2),position)

        final_result = self.autofocus.calculate_best_focus()
        self.move_focuser(final_result["best_position"])

    def capture_to_fit(self, exposure, ra, dec, filter_name, target_name) :
        image = self.camera_capture(exposure)

        header={}
        if self.camera_info:
            header['INSTRUME'] = self.camera_info.name
            header['XPIXSZ'] = self.camera_info.camera_x_size
            header['YPIXSZ'] = self.camera_info.camera_y_size
        header["EXPTIME"] = 1
        header['DATE-OBS'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        header['RA'] = ra
        header['DEC'] = dec
        FitsImageManager.save_fits_from_array(image.data, f"capture-{target_name}-{filter_name}-{header['DATE-OBS']}.fits", header)

class AlpacaTelescope(TelescopeInterface):
    def camera_capture(self, expo: float):
        try:
            expo = ExposureSettings(duration=expo)
            alpaca_camera_client.start_exposure()
            while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
                print("waiting end of exposure")
                sleep(1)
            return alpaca_camera_client.get_image_array()
        except Exception as e:
            return None

    def move_focuser(self, position: int):
        alpaca_focuser_client.move_absolute(position)
        while alpaca_focuser_client.is_moving():
            sleep(1)
        sleep(1)


telescope_interface = AlpacaTelescope()




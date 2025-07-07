from imageprocessing.fitsprocessor import FitsImageManager
from services.alpaca_client import alpaca_camera_client, ExposureSettings, CameraState
from astropy.io import fits 
import time
import numpy as np


def __main__():
    alpaca_camera_client.connect()
    print(alpaca_camera_client.device_type)
    print(alpaca_camera_client.start_exposure(ExposureSettings()))
    while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
        print("waiting end of exposure")
        time.sleep(1)

    print(alpaca_camera_client.get_camera_state())
    camera_info = alpaca_camera_client.get_camera_info()

    image=alpaca_camera_client.get_image_array()
    header={}
    if camera_info:
        header['INSTRUME'] = camera_info.name
        header['XPIXSZ'] = camera_info.camera_x_size
        header['YPIXSZ'] = camera_info.camera_y_size
    header["EXPTIME"] = 1
    header['DATE-OBS'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    FitsImageManager.save_fits_from_array(image.data, "test.fits",header)

if __name__ == "__main__":
    print("main")
    __main__()
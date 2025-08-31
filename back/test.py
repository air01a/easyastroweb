from services.telescope_interface import telescope_interface
from time import sleep
from imageprocessing.fitsprocessor import FitsImageManager
from PIL import Image
from utils.section_timer import SectionTimer

fits_manager = FitsImageManager()

telescope_interface.camera_connect()
#telescope_interface.set_fast_read_out(True)
print(telescope_interface.camera_name)
telescope_interface.set_bin_x(2)
telescope_interface.set_bin_y(2)
sleep(1)
timer = SectionTimer("capture")

image=(telescope_interface.camera_capture(2,True).data)
sensor, bayer, color_type = telescope_interface.get_bayer_pattern()
if bayer:
    print("debayer")
    image = fits_manager.debayer(image, bayer)
    timer.mark("debayer")
    timer.mark("cache_debayered_copy")
timer.end()
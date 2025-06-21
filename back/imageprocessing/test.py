
from fitsprocessor import FITSProcessor


fits='../../utils/01-observation-m16/01-images-initial/TargetSet.M27.8.00.LIGHT.329.2023-10-01_21-39-23.fits.fits'
fitsprocessor = FITSProcessor(fits)
fitsprocessor.save_rgb_fits_16bit('test.fit')
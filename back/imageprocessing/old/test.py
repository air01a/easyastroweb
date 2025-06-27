
import numpy as np
from scipy import stats
from fitsprocessor import FitsImageManager
from imageprocessing.astrofilters import AstroFilters


fits_manager = FitsImageManager(auto_normalize=True)
filters = AstroFilters()

image = fits_manager.open_fits(f"astro_session/final/final21.fit")
#image.data = filters.auto_stretch(image.data, 0.15, algo=1, shadow_clip=-2)
image.data = filters.stretch_mtf_luminance(image.data, 0.1, 0.8,0.3)
#optimal_clip_percent = filters.adaptive_clipping(image.data, method='auto')
#print("opti : ", optimal_clip_percent)
#image.data  = filters.denoise_gaussian(filters.replace_lowest_percent_by_zero(image.data,optimal_clip_percent))
#image.data = filters.denoise_bilateral(image.data)
fits_manager.save_as_image(image,"test2.jpg")

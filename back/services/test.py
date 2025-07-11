from imageprocessing.fitsprocessor import FitsImageManager
from imageprocessing.astrofilters import AstroFilters
from pathlib import Path
fits_manager  = FitsImageManager()
astro_filters = AstroFilters()

def _on_image_stack( path: Path):
    image = fits_manager.open_fits(f"{path}")
    image.data  = astro_filters.denoise_gaussian(astro_filters.replace_lowest_percent_by_zero(astro_filters.auto_stretch(image.data, 0.25, algo=1, shadow_clip=-2),80))
    fits_manager.save_as_image(image, output_filename=f"{path}".replace(".fit",".jpg"))

img = Path("C:/Users/eniquet/Documents/dev/easyastroweb/back/services/fits/capture-Andromeda2-UV-2025-07-11T16.04.28.fits")

_on_image_stack(img)
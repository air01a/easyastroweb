
from fitsprocessor import FitsImageManager
from filters import AstroFilters


fits = FitsImageManager()
astro_filter = AstroFilters()


fits.open_fits('test1baverage.fits')
fits.debayer()
fits.processed_data = astro_filter.stretch_histogram_asinh(fits.processed_data, 5000, 0.005)
fits.save_as_image("testfinal.jpg", stretch=False)
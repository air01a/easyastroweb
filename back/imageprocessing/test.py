
from fitsprocessor import FitsImageManager
from filters import AstroFilters

import tifffile as tiff
import numpy as np
from PIL import Image


fits = FitsImageManager()
astro_filter = AstroFilters()

def replace_lowest_percent_by_zero(array, percent):
    """
    Remplace les `percent`% des valeurs les plus basses de `array` par 0.
    
    Args:
        array (np.ndarray): tableau d'entrée
        percent (float): pourcentage entre 0 et 100

    Returns:
        np.ndarray: tableau avec les plus basses valeurs remplacées par 0
    """
    array = array.copy()
    threshold = np.percentile(array, percent)
    array[array <= threshold] = 0
    return array

# Lecture du fichier TIFF 16 bits
img = tiff.imread("test1baverage40.tif")/65535
data = astro_filter.denoise_gaussian(replace_lowest_percent_by_zero(astro_filter.auto_stretch(img, 0.3, algo=1, shadow_clip=-2),88))

# Vérification
print("Shape :", img.shape)     # (H, W) ou (H, W, C) ou (N, H, W)
print("Type  :", img.dtype)     # ex: uint16
print("Min   :", np.min(img))
print("Max   :", np.max(img))
data = (data * 255).astype(np.uint8)
img_pil = Image.fromarray(data)
img_pil.save("test.jpg", "JPEG")
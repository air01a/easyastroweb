
import numpy as np
from scipy import stats
from fitsprocessor import FitsImageManager
from filters import AstroFilters

def find_noise_level(image_data):
    """Trouve automatiquement le niveau de bruit de l'image"""
    # Utilise la médiane des déviations absolues (MAD) pour estimer le bruit
    median = np.median(image_data)
    mad = np.median(np.abs(image_data - median))
    noise_level = 1.4826 * mad  # Facteur de conversion pour distribution normale
    return noise_level

def adaptive_clipping_threshold(image_data, sigma_factor=3):
    """Calcule un seuil de clipping adaptatif basé sur le bruit"""
    noise_level = find_noise_level(image_data)
    # Clipping à n-sigma au-dessus du niveau de bruit
    threshold = noise_level * sigma_factor
    return threshold
from scipy.optimize import curve_fit
def sky_background_analysis(image_data, sample_size=1000):
    """Analyse le fond de ciel pour déterminer le niveau de clipping"""
    # Échantillonne des zones "vides" de l'image (coins par exemple)
    h, w = image_data.shape
    corners = [
        image_data[:h//10, :w//10],  # coin haut-gauche
        image_data[:h//10, -w//10:], # coin haut-droit
        image_data[-h//10:, :w//10], # coin bas-gauche
        image_data[-h//10:, -w//10:] # coin bas-droit
    ]
    
    sky_samples = np.concatenate([corner.flatten() for corner in corners])
    
    # Statistiques du fond de ciel
    sky_mean = np.mean(sky_samples)
    sky_std = np.std(sky_samples)
    
    # Le seuil de clipping = moyenne + n * écart-type
    clipping_threshold = sky_mean + 2 * sky_std
    return clipping_threshold
def gaussian(x, amp, mu, sigma):
    return amp * np.exp(-(x - mu)**2 / (2 * sigma**2))

def find_noise_peak(image_data, bins=1000):
    """Trouve le pic de bruit en ajustant une gaussienne sur l'histogramme"""
    hist, bin_edges = np.histogram(image_data.flatten(), bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Trouve le pic principal (supposé être le bruit)
    peak_idx = np.argmax(hist)
    peak_value = bin_centers[peak_idx]
    
    # Ajuste une gaussienne autour du pic
    try:
        # Prend une fenêtre autour du pic
        window = 50
        start_idx = max(0, peak_idx - window)
        end_idx = min(len(hist), peak_idx + window)
        
        x_data = bin_centers[start_idx:end_idx]
        y_data = hist[start_idx:end_idx]
        
        # Estimation initiale des paramètres
        initial_guess = [np.max(y_data), peak_value, np.std(image_data)]
        
        popt, _ = curve_fit(gaussian, x_data, y_data, p0=initial_guess)
        
        # Le seuil = moyenne + n * sigma de la gaussienne ajustée
        clipping_threshold = popt[1] + 3 * abs(popt[2])
        return clipping_threshold
        
    except:
        # Fallback sur une méthode plus simple
        return np.percentile(image_data, 99.5)

def adaptive_clipping(image_data, method='auto'):
    """
    Détermine automatiquement le niveau de clipping optimal
    
    Args:
        image_data: données de l'image
        method: 'noise_analysis', 'sky_background', 'gaussian_fit', ou 'auto'
    """
    
    if method == 'noise_analysis':
        threshold = adaptive_clipping_threshold(image_data)
        percent_to_clip = np.sum(image_data < threshold) / image_data.size * 100
        
    elif method == 'sky_background':
        threshold = sky_background_analysis(image_data)
        percent_to_clip = np.sum(image_data < threshold) / image_data.size * 100
        
    elif method == 'gaussian_fit':
        threshold = find_noise_peak(image_data)
        percent_to_clip = np.sum(image_data < threshold) / image_data.size * 100
        
    elif method == 'auto':
        # Combine plusieurs méthodes et prend la médiane
        thresholds = []
        try:
            thresholds.append(adaptive_clipping_threshold(image_data))
        except:
            pass
        try:
            thresholds.append(sky_background_analysis(image_data))
        except:
            pass
        try:
            thresholds.append(find_noise_peak(image_data))
        except:
            pass
            
        if thresholds:
            threshold = np.median(thresholds)
            percent_to_clip = np.sum(image_data < threshold) / image_data.size * 100
        else:
            # Fallback sur percentile
            percent_to_clip = 85
    
    return min(95, max(50, percent_to_clip))  # Limite entre 50% et 95%


fits_manager = FitsImageManager(auto_normalize=True)
filters = AstroFilters()

image = fits_manager.open_fits(f"astro_session/final/final21.fit")
image.data = filters.auto_stretch(image.data, 0.1, algo=1, shadow_clip=-2)
optimal_clip_percent = adaptive_clipping(image.data, method='auto')
print("opti : ", optimal_clip_percent)
#image.data  = filters.denoise_gaussian(filters.replace_lowest_percent_by_zero(image.data,optimal_clip_percent))
fits_manager.save_as_image(image,"test2.jpg")

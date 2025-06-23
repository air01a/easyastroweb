import numpy as np
from scipy import ndimage, signal
from scipy.fft import fft2, ifft2, fftfreq
from skimage import filters, restoration, exposure, morphology
from skimage.filters import gaussian, unsharp_mask
from skimage.restoration import denoise_wavelet, denoise_bilateral
import cv2
import warnings


import numpy as np


"""
This product is based on software from the PixInsight project, developed by
Pleiades Astrophoto and its contributors (http://pixinsight.com/).
"""


class Stretch:

    def __init__(self, target_bkg=0.25, shadows_clip=-2):
        self.shadows_clip = shadows_clip
        self.target_bkg = target_bkg

 
    def _get_avg_dev(self, data):
        """Return the average deviation from the median.

        Args:
            data (np.array): array of floats, presumably the image data
        """
        median = np.median(data)
        n = data.size
        median_deviation = lambda x: abs(x - median)
        avg_dev = np.sum( median_deviation(data) / n )
        return avg_dev

    def _mtf(self, m, x):
        """Midtones Transfer Function

        MTF(m, x) = {
            0                for x == 0,
            1/2              for x == m,
            1                for x == 1,

            (m - 1)x
            --------------   otherwise.
            (2m - 1)x - m
        }

        See the section "Midtones Balance" from
        https://pixinsight.com/doc/tools/HistogramTransformation/HistogramTransformation.html

        Args:
            m (float): midtones balance parameter
                       a value below 0.5 darkens the midtones
                       a value above 0.5 lightens the midtones
            x (np.array): the data that we want to copy and transform.
        """
        shape = x.shape
        x = x.flatten()
        zeros = x==0
        halfs = x==m
        ones = x==1
        others = np.logical_xor((x==x), (zeros + halfs + ones))

        x[zeros] = 0
        x[halfs] = 0.5
        x[ones] = 1
        x[others] = (m - 1) * x[others] / ((((2 * m) - 1) * x[others]) - m)
        return x.reshape(shape)

    def _get_stretch_parameters(self, data):
        """ Get the stretch parameters automatically.
        m (float) is the midtones balance
        c0 (float) is the shadows clipping point
        c1 (float) is the highlights clipping point
        """
        median = np.median(data)
        avg_dev = self._get_avg_dev(data)

        c0 = np.clip(median + (self.shadows_clip * avg_dev), 0, 1)
        m = self._mtf(self.target_bkg, median - c0)

        return {
            "c0": c0,
            "c1": 1,
            "m": m
        }

    def stretch(self, data):
        """ Stretch the image.

        Args:
            data (np.array): the original image data array.

        Returns:
            np.array: the stretched image data
        """

        # Normalize the data
        d = data / np.max(data)

        # Obtain the stretch parameters
        stretch_params = self._get_stretch_parameters(d)
        m = stretch_params["m"]
        c0 = stretch_params["c0"]
        c1 = stretch_params["c1"]

        # Selectors for pixels that lie below or above the shadows clipping point
        below = d < c0
        above = d >= c0

        # Clip everything below the shadows clipping point
        d[below] = 0

        # For the rest of the pixels: apply the midtones transfer function
        d[above] = self._mtf(m, (d[above] - c0)/(1 - c0))
        return d


class AstroFilters:
    """
    Librairie de filtres pour l'astronomie
    Compatible avec les images couleur (RGB) et noir et blanc
    Gère automatiquement la normalisation selon les besoins de chaque filtre
    """
    
    def __init__(self, auto_normalize=False):
        self.version = "1.0.0"
        self.auto_normalize = auto_normalize
        
    def _auto_normalize_input(self, image):
        """Normalise automatiquement l'image si nécessaire"""
        if not self.auto_normalize:
            return image, None, None
            
        if image.max() <= 1.0 and image.min() >= 0.0:
            return image, None, None  # Déjà normalisée
        
        # Sauvegarde des valeurs originales pour dénormalisation
        original_min = image.min()
        original_max = image.max()
        
        # Normalisation
        normalized = (image - original_min) / (original_max - original_min)
        return normalized, original_min, original_max
    
    def _denormalize_output(self, image, original_min, original_max):
        """Remet l'image dans son échelle originale"""
        if original_min is None or original_max is None:
            return image
        return image * (original_max - original_min) + original_min
    
    def _re_normalize_input(self, image, low=1, high=99):
        """
        Normalise dynamiquement une image, même si elle est déjà dans [0,1].
        Utilise les percentiles pour s'adapter au contenu utile.
        """
        image_f = image.astype(np.float32)

        # Calcul des bornes dynamiques réelles
        p_low = np.percentile(image_f, low)
        p_high = np.percentile(image_f, high)

        if p_high - p_low <= 0:
            return np.zeros_like(image_f), 0.0, 1.0

        norm = np.clip((image_f - p_low) / (p_high - p_low), 0, 1)
        return norm, p_low, p_high
    
    # ===========================================
    # ÉTIREMENT D'HISTOGRAMME
    # ===========================================
    
    def stretch_histogram_linear(self, image, percentile_low=1, percentile_high=99):
        """
        Étirement linéaire de l'histogramme
        FONCTIONNE avec valeurs RAW - pas besoin de normalisation
        
        Args:
            image: Image numpy array (2D ou 3D) - valeurs RAW acceptées
            percentile_low: Percentile bas pour l'étirement (%)
            percentile_high: Percentile haut pour l'étirement (%)
        """
        if len(image.shape) == 3:  # Image couleur
            result = np.zeros_like(image, dtype=np.float32)
            for i in range(image.shape[2]):
                channel = image[:, :, i].astype(np.float32)
                low = np.percentile(channel, percentile_low)
                high = np.percentile(channel, percentile_high)
                if high > low:  # Éviter division par zéro
                    result[:, :, i] = np.clip((channel - low) / (high - low), 0, 1)
                else:
                    result[:, :, i] = channel
        else:  # Image N&B
            image_f = image.astype(np.float32)
            low = np.percentile(image_f, percentile_low)
            high = np.percentile(image_f, percentile_high)
            if high > low:
                result = np.clip((image_f - low) / (high - low), 0, 1)
            else:
                result = image_f
        
        return result
    


    def stretch_histogram_asinh(self, image, beta=0.1, offset=0.0):
        """
        Applique un étirement d'histogramme utilisant la fonction asinh.
        
        Cette implémentation suit l'algorithme utilisé dans Siril pour l'étirement asinh.
        
        Parameters:
        -----------
        image : numpy.ndarray
            Image d'entrée (valeurs entre 0 et 1 typiquement)
        beta : float, default=0.1
            Paramètre de contrôle de l'intensité de l'étirement
            - Valeurs plus petites = étirement plus fort
            - Valeurs plus grandes = étirement plus doux
        offset : float, default=0.0
            Décalage appliqué avant l'étirement
        
        Returns:
        --------
        numpy.ndarray
            Image étirée avec les mêmes dimensions que l'entrée
        """
        
        # Conversion en float pour éviter les problèmes de précision
        img = image.astype(np.float64)
        
        # Application de l'offset
        img_offset = img + offset
        
        # Calcul de l'étirement asinh
        # Formule Siril: asinh(img_offset / beta) / asinh(1 / beta)
        stretched = np.arcsinh(img_offset / beta) / np.arcsinh(1.0 / beta)
        
        # Clamp des valeurs entre 0 et 1
        stretched = np.clip(stretched, 0.0, 1.0)
        
        return stretched
    



    def stretch_histogram_asinh_advanced(self, image, beta=0.1, offset=0.0, preserve_range=True):
        """
        Version avancée de l'étirement asinh avec gestion automatique des plages.
        
        Parameters:
        -----------
        image : numpy.ndarray
            Image d'entrée
        beta : float, default=0.1
            Paramètre de contrôle de l'intensité
        offset : float, default=0.0
            Décalage
        preserve_range : bool, default=True
            Si True, préserve la plage de valeurs originale de l'image
        
        Returns:
        --------
        numpy.ndarray
            Image étirée
        """
        
        # Sauvegarde du type et de la plage originale
        original_dtype = image.dtype
        original_min = np.min(image)
        original_max = np.max(image)
        
        # Normalisation vers [0, 1]
        if preserve_range and (original_min != 0 or original_max != 1):
            img_norm = (image.astype(np.float64) - original_min) / (original_max - original_min)
        else:
            img_norm = image.astype(np.float64)
        
        # Application de l'étirement
        stretched = self.stretch_histogram_asinh(img_norm, beta, offset)
        
        # Restauration de la plage originale si demandée
        if preserve_range and (original_min != 0 or original_max != 1):
            stretched = stretched * (original_max - original_min) + original_min
        
        # Restauration du type original si c'était un entier
        if np.issubdtype(original_dtype, np.integer):
            stretched = np.round(stretched).astype(original_dtype)
        
        return stretched


    def asinh_stretch_color(self, image, beta=0.1, offset=0.0, method='per_channel'):
        """
        Étirement asinh spécialisé pour les images couleur.
        
        Parameters:
        -----------
        image : numpy.ndarray
            Image couleur (H, W, C) où C est le nombre de canaux (3 pour RGB)
        beta : float or array-like, default=0.1
            Paramètre de contrôle. Peut être:
            - Un float: même valeur pour tous les canaux
            - Un array: valeur différente par canal [beta_R, beta_G, beta_B]
        offset : float or array-like, default=0.0
            Décalage par canal
        method : str, default='per_channel'
            Méthode d'étirement:
            - 'per_channel': étirement indépendant par canal
            - 'luminance': préserve les couleurs, étire seulement la luminance
            - 'saturation_preserve': préserve la saturation tout en étirant
        
        Returns:
        --------
        numpy.ndarray
            Image couleur étirée
        """
        
        if len(image.shape) < 3:
            # Image en niveaux de gris, utilise la fonction de base
            return self.stretch_histogram_asinh(image, beta, offset)
        
        img = image.astype(np.float64)
        
        if method == 'per_channel':
            # Étirement indépendant par canal (méthode par défaut de Siril)
            result = np.zeros_like(img)
            
            # Gestion des paramètres par canal
            if np.isscalar(beta):
                beta = [beta] * img.shape[2]
            if np.isscalar(offset):
                offset = [offset] * img.shape[2]
                
            for c in range(img.shape[2]):
                result[:, :, c] = self.stretch_histogram_asinh(img[:, :, c], beta[c], offset[c])
                
            return result
        
        elif method == 'luminance':
            # Conversion en YUV, étirement de la luminance Y seulement
            # Coefficients de luminance standard (Rec. 709)
            if img.shape[2] >= 3:
                Y = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]
                Y_stretched = self.stretch_histogram_asinh(Y, beta, offset)
                
                # Préservation des chrominances
                result = img.copy()
                for c in range(3):
                    # Évite la division par zéro
                    mask = Y > 1e-10
                    result[mask, c] = img[mask, c] * (Y_stretched[mask] / Y[mask])
                    result[~mask, c] = Y_stretched[~mask]
                
                return np.clip(result, 0, 1)
        
        elif method == 'saturation_preserve':
            # Méthode qui préserve mieux la saturation des couleurs
            if img.shape[2] >= 3:
                # Calcul de l'intensité maximale par pixel
                intensity = np.max(img[:, :, :3], axis=2)
                intensity_stretched = self.stretch_histogram_asinh(intensity, beta, offset)
                
                result = img.copy()
                mask = intensity > 1e-10
                ratio = np.zeros_like(intensity)
                ratio[mask] = intensity_stretched[mask] / intensity[mask]
                
                for c in range(img.shape[2]):
                    result[:, :, c] = img[:, :, c] * ratio
                
                return np.clip(result, 0, 1)
        
        # Fallback: étirement par canal
        return self.asinh_stretch_color(image, beta, offset, 'per_channel')

    def stretch_histogram_power(self, image, gamma=0.5):
        """
        Étirement par loi de puissance (gamma correction)
        
        Args:
            image: Image numpy array
            gamma: Exposant gamma (< 1 éclaircit, > 1 assombrit)
        """
        image_f = image.astype(np.float32)
        if image_f.max() > 1:
            image_f = image_f / image_f.max()
        
        return np.power(image_f, gamma)
    
    def stretch_histogram_log(self, image, scaling=1.0):
        """
        Étirement logarithmique
        
        Args:
            image: Image numpy array
            scaling: Facteur d'échelle
        """
        image_f = image.astype(np.float32)
        if image_f.max() > 1:
            image_f = image_f / image_f.max()
        
        result = scaling * np.log1p(image_f) / np.log1p(1.0)
        return np.clip(result, 0, 1)
    
    # ===========================================
    # CORRECTION DE GRADIENT
    # ===========================================
    
    def remove_gradient_polynomial(self, image, degree=2):
        """
        Suppression du gradient par ajustement polynomial
        FONCTIONNE avec valeurs RAW - garde l'échelle originale
        
        Args:
            image: Image numpy array (2D pour N&B) - valeurs RAW acceptées
            degree: Degré du polynôme
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image, dtype=np.float32)
            for i in range(image.shape[2]):
                result[:, :, i] = self._remove_gradient_2d(image[:, :, i], degree)
            return result
        else:
            return self._remove_gradient_2d(image, degree)
    
    def _remove_gradient_2d(self, image, degree):
        """Fonction auxiliaire pour la correction de gradient 2D"""
        h, w = image.shape
        y, x = np.mgrid[0:h, 0:w]
        
        # Création de la matrice des termes polynomiaux
        terms = []
        for i in range(degree + 1):
            for j in range(degree + 1 - i):
                terms.append((x**i * y**j).flatten())
        
        A = np.column_stack(terms)
        b = image.flatten()
        
        # Résolution des moindres carrés
        coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        
        # Reconstruction du gradient
        gradient = np.zeros_like(image)
        idx = 0
        for i in range(degree + 1):
            for j in range(degree + 1 - i):
                gradient += coeffs[idx] * (x**i * y**j)
                idx += 1
        
        return image - gradient
    
    def remove_gradient_median(self, image, kernel_size=51):
        """
        Suppression du gradient par filtrage médian
        
        Args:
            image: Image numpy array
            kernel_size: Taille du noyau de filtrage médian
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                background = ndimage.median_filter(image[:, :, i], size=kernel_size)
                result[:, :, i] = image[:, :, i] - background
            return result
        else:
            background = ndimage.median_filter(image, size=kernel_size)
            return image - background
    
    # ===========================================
    # FILTRES WAVELET
    # ===========================================
    
    def wavelet_sharpen(self, image, wavelet='db4', levels=3, sigma=1.0):
        """
        Amélioration par ondelettes
        
        Args:
            image: Image numpy array
            wavelet: Type d'ondelette ('db4', 'db8', 'haar', 'bior2.2')
            levels: Nombre de niveaux de décomposition
            sigma: Facteur d'amplification des détails
        """
        try:
            import pywt
        except ImportError:
            print("PyWavelets requis pour les filtres wavelet")
            return image
        
        if len(image.shape) == 3:
            result = np.zeros_like(image, dtype=np.float32)
            for i in range(image.shape[2]):
                result[:, :, i] = self._wavelet_sharpen_2d(image[:, :, i], wavelet, levels, sigma)
            return result
        else:
            return self._wavelet_sharpen_2d(image, wavelet, levels, sigma)
    
    def _wavelet_sharpen_2d(self, image, wavelet, levels, sigma):
        """Fonction auxiliaire pour l'amélioration wavelet 2D"""
        try:
            import pywt
            
            # Décomposition en ondelettes
            coeffs = pywt.wavedec2(image, wavelet, level=levels)
            
            # Amplification des coefficients de détail
            coeffs_enhanced = [coeffs[0]]  # Approximation
            for i in range(1, len(coeffs)):
                cH, cV, cD = coeffs[i]
                coeffs_enhanced.append((cH * sigma, cV * sigma, cD * sigma))
            
            # Reconstruction
            enhanced = pywt.waverec2(coeffs_enhanced, wavelet)
            
            # Combinaison avec l'image originale
            return np.clip(image + 0.5 * (enhanced - image), 0, 1)
            
        except Exception as e:
            print(f"Erreur wavelet: {e}")
            return image
    
    def wavelet_denoise(self, image, wavelet='db4', sigma=None, mode='soft'):
        """
        Débruitage par ondelettes
        
        Args:
            image: Image numpy array
            wavelet: Type d'ondelette
            sigma: Écart-type du bruit (auto si None)
            mode: Mode de seuillage ('soft' ou 'hard')
        """
        return denoise_wavelet(image, wavelet=wavelet, sigma=sigma, 
                             mode=mode, rescale_sigma=True)
    
    # ===========================================
    # DÉBRUITAGE
    # ===========================================
    
    def denoise_gaussian(self, image, sigma=1.0):
        """
        Débruitage gaussien
        
        Args:
            image: Image numpy array
            sigma: Écart-type du filtre gaussien
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = gaussian(image[:, :, i], sigma=sigma)
            return result
        else:
            return gaussian(image, sigma=sigma)
    
    def denoise_bilateral(self, image, sigma_color=0.1, sigma_spatial=15):
        """
        Débruitage bilatéral (préserve les contours)
        NÉCESSITE une normalisation automatique pour OpenCV
        
        Args:
            image: Image numpy array - valeurs RAW acceptées
            sigma_color: Écart-type pour les différences de couleur
            sigma_spatial: Écart-type spatial
        """
        # Normalisation automatique
        image_norm, orig_min, orig_max = self._auto_normalize_input(image)
        
        if len(image_norm.shape) == 3:
            # Conversion pour cv2
            img_8bit = (np.clip(image_norm, 0, 1) * 255).astype(np.uint8)
            denoised = cv2.bilateralFilter(img_8bit, -1, 
                                         sigma_color * 255, sigma_spatial)
            result = denoised.astype(np.float32) / 255.0
        else:
            # Pour image N&B, utilisation scikit-image
            result = denoise_bilateral(image_norm, sigma_color=sigma_color, 
                                   sigma_spatial=sigma_spatial)
        
        # Retour à l'échelle originale si pas de normalisation auto
        if not self.auto_normalize:
            return self._denormalize_output(result, orig_min, orig_max)
        return result
    
    def denoise_median(self, image, size=3):
        """
        Débruitage par filtre médian
        
        Args:
            image: Image numpy array
            size: Taille du noyau médian
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = ndimage.median_filter(image[:, :, i], size=size)
            return result
        else:
            return ndimage.median_filter(image, size=size)
    
    def denoise_nlm(self, image, h=0.1, template_window_size=7, search_window_size=21):
        """
        Débruitage Non-Local Means (très efficace mais lent)
        
        Args:
            image: Image numpy array
            h: Paramètre de filtrage
            template_window_size: Taille de la fenêtre template
            search_window_size: Taille de la fenêtre de recherche
        """
        if len(image.shape) == 3:
            img_8bit = (np.clip(image, 0, 1) * 255).astype(np.uint8)
            denoised = cv2.fastNlMeansDenoisingColored(img_8bit, None, h*255, h*255,
                                                      template_window_size, search_window_size)
            return denoised.astype(np.float32) / 255.0
        else:
            img_8bit = (np.clip(image, 0, 1) * 255).astype(np.uint8)
            denoised = cv2.fastNlMeansDenoising(img_8bit, None, h*255,
                                              template_window_size, search_window_size)
            return denoised.astype(np.float32) / 255.0
    
    # ===========================================
    # AMÉLIORATION DE LA NETTETÉ
    # ===========================================
    
    def unsharp_masking(self, image, radius=2.0, amount=1.0):
        """
        Masque flou (Unsharp Masking)
        
        Args:
            image: Image numpy array
            radius: Rayon du flou
            amount: Intensité de l'amélioration
        """
        return unsharp_mask(image, radius=radius, amount=amount)
    
    def laplacian_sharpen(self, image, alpha=0.2):
        """
        Amélioration par filtre laplacien
        
        Args:
            image: Image numpy array
            alpha: Intensité de l'amélioration
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                laplacian = ndimage.laplace(image[:, :, i])
                result[:, :, i] = image[:, :, i] - alpha * laplacian
            return np.clip(result, 0, 1)
        else:
            laplacian = ndimage.laplace(image)
            return np.clip(image - alpha * laplacian, 0, 1)
    
    def high_pass_sharpen(self, image, sigma=2.0, alpha=0.5):
        """
        Amélioration par filtre passe-haut
        
        Args:
            image: Image numpy array
            sigma: Écart-type du filtre gaussien
            alpha: Intensité de l'amélioration
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                blurred = gaussian(image[:, :, i], sigma=sigma)
                high_pass = image[:, :, i] - blurred
                result[:, :, i] = image[:, :, i] + alpha * high_pass
            return np.clip(result, 0, 1)
        else:
            blurred = gaussian(image, sigma=sigma)
            high_pass = image - blurred
            return np.clip(image + alpha * high_pass, 0, 1)
    
    # ===========================================
    # FILTRES MORPHOLOGIQUES
    # ===========================================
    
    def morphological_opening(self, image, disk_size=3):
        """
        Ouverture morphologique (supprime les petits objets brillants)
        
        Args:
            image: Image numpy array
            disk_size: Taille du élément structurant
        """
        selem = morphology.disk(disk_size)
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = morphology.opening(image[:, :, i], selem)
            return result
        else:
            return morphology.opening(image, selem)
    
    def morphological_closing(self, image, disk_size=3):
        """
        Fermeture morphologique (remplit les petits trous sombres)
        
        Args:
            image: Image numpy array
            disk_size: Taille du élément structurant
        """
        selem = morphology.disk(disk_size)
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = morphology.closing(image[:, :, i], selem)
            return result
        else:
            return morphology.closing(image, selem)
    
    def top_hat(self, image, disk_size=5):
        """
        Transformation top-hat (détecte les objets brillants)
        
        Args:
            image: Image numpy array
            disk_size: Taille du élément structurant
        """
        selem = morphology.disk(disk_size)
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = morphology.white_tophat(image[:, :, i], selem)
            return result
        else:
            return morphology.white_tophat(image, selem)
    
    # ===========================================
    # RÉDUCTION DU BRUIT PÉRIODIQUE
    # ===========================================
    
    def remove_periodic_noise(self, image, frequencies_to_remove=None, threshold=0.1):
        """
        Suppression du bruit périodique par filtrage fréquentiel
        
        Args:
            image: Image numpy array (2D seulement)
            frequencies_to_remove: Liste des fréquences à supprimer
            threshold: Seuil pour la détection automatique
        """
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(image.shape[2]):
                result[:, :, i] = self._remove_periodic_noise_2d(image[:, :, i], 
                                                               frequencies_to_remove, threshold)
            return result
        else:
            return self._remove_periodic_noise_2d(image, frequencies_to_remove, threshold)
    
    def _remove_periodic_noise_2d(self, image, frequencies_to_remove, threshold):
        """Fonction auxiliaire pour la suppression du bruit périodique 2D"""
        # Transformée de Fourier
        f_transform = fft2(image)
        f_shift = np.fft.fftshift(f_transform)
        
        # Si pas de fréquences spécifiées, détection automatique
        if frequencies_to_remove is None:
            magnitude = np.abs(f_shift)
            mean_mag = np.mean(magnitude)
            mask = magnitude < (mean_mag + threshold * np.max(magnitude))
        else:
            # Création du masque pour les fréquences spécifiées
            h, w = image.shape
            center_x, center_y = w // 2, h // 2
            y, x = np.ogrid[:h, :w]
            mask = np.ones((h, w), dtype=bool)
            
            for freq in frequencies_to_remove:
                # Suppression des fréquences spécifiées
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                freq_mask = np.abs(dist - freq) < 2
                mask = mask & ~freq_mask
        
        # Application du masque
        f_shift_filtered = f_shift * mask
        
        # Transformée inverse
        f_ishift = np.fft.ifftshift(f_shift_filtered)
        img_filtered = np.real(ifft2(f_ishift))
        
        return img_filtered
    
    # ===========================================
    # COMBINAISON D'IMAGES
    # ===========================================
    
    def combine_images_median(self, images_list):
        """
        Combinaison d'images par médiane (supprime les rayons cosmiques)
        
        Args:
            images_list: Liste d'images numpy array
        """
        return np.median(np.stack(images_list, axis=0), axis=0)
    
    def combine_images_mean(self, images_list, weights=None):
        """
        Combinaison d'images par moyenne pondérée
        
        Args:
            images_list: Liste d'images numpy array
            weights: Poids pour chaque image (optionnel)
        """
        if weights is None:
            return np.mean(np.stack(images_list, axis=0), axis=0)
        else:
            weights = np.array(weights)
            weighted_sum = np.sum([w * img for w, img in zip(weights, images_list)], axis=0)
            return weighted_sum / np.sum(weights)
    
    def combine_images_sigma_clip(self, images_list, sigma=2.0):
        """
        Combinaison avec rejet sigma (supprime les outliers)
        
        Args:
            images_list: Liste d'images numpy array
            sigma: Seuil de rejet en écarts-types
        """
        stack = np.stack(images_list, axis=0)
        mean = np.mean(stack, axis=0)
        std = np.std(stack, axis=0)
        
        # Masque pour les pixels à conserver
        mask = np.abs(stack - mean) <= sigma * std
        
        # Moyenne des pixels non rejetés
        masked_stack = np.where(mask, stack, np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            result = np.nanmean(masked_stack, axis=0)
        
        return result
    
    # ===========================================
    # UTILITAIRES
    # ===========================================
    
    def normalize_image(self, image, method='minmax'):
        """
        Normalisation d'image
        
        Args:
            image: Image numpy array
            method: 'minmax', 'zscore', 'percentile'
        """
        if method == 'minmax':
            return (image - image.min()) / (image.max() - image.min())
        elif method == 'zscore':
            return (image - image.mean()) / image.std()
        elif method == 'percentile':
            p1, p99 = np.percentile(image, [1, 99])
            return np.clip((image - p1) / (p99 - p1), 0, 1)
        else:
            raise ValueError("Méthode non reconnue")
    
    def apply_mask(self, image, mask):
        """
        Application d'un masque à une image
        
        Args:
            image: Image numpy array
            mask: Masque binaire
        """
        if len(image.shape) == 3:
            return image * mask[:, :, np.newaxis]
        else:
            return image * mask
    
    def get_image_statistics(self, image):
        """
        Calcul des statistiques d'une image
        
        Args:
            image: Image numpy array
        """
        stats = {
            'mean': np.mean(image),
            'std': np.std(image),
            'min': np.min(image),
            'max': np.max(image),
            'median': np.median(image),
            'percentile_1': np.percentile(image, 1),
            'percentile_99': np.percentile(image, 99)
        }
        return stats

    def auto_stretch(self, image , strength : float, shadow_clip : int = -2, algo: int =0):
        #n=1
        print(image.shape)
        if (algo==0): # algo stretch with clipping (strength 0:1, default = 0.1)
            # Best for stars imaging
            if (image.shape[2]>1):
                for i in range(0,image.data.shape[2]):
                    min_val = np.percentile(image[:,:,i], strength)
                    max_val = np.percentile(image[:,:,i], 100 - strength)
                    image[:,:,i] = np.clip((image[:,:,i] - min_val) * (1.0 / (max_val - min_val)), 0, 1)
            else:
                    min_val = np.percentile(image, strength)
                    max_val = np.percentile(image, 100 - strength)
                    image = np.clip((image - min_val) * (1.0 / (max_val - min_val)), 0, 1)
        elif (algo==1):
            # strength float : 0-1
            # Pixinsight MTF algorithm, best with nebula
            #image = np.interp(image,
            #                            (image.min(), image.max()),
            #                            (0, 1))
            if image.shape[2]>1:
                for channel in range(3):
                    image[:,:,channel] = Stretch(target_bkg=strength, shadows_clip=shadow_clip).stretch(image[:,:,channel])
                else:
                    image = Stretch(target_bkg=strength).stretch(image)

        elif (algo==2):
            # stddev method
            # strength between 0-8
            mean = np.mean(image)
            stddev = np.std(image)

            # Soustraire la moyenne et diviser par l'écart-type multiplié par le facteur de contraste
            contrast_factor = 1/(2000*strength)
            stretched_image = (image - mean) / (stddev * contrast_factor)

            # Tronquer les valeurs des pixels en dessous de zéro à zéro et au-dessus de 255 à 255
            stretched_image = np.clip(stretched_image, 0, 1)

            # Convertir les valeurs des pixels en entiers
            image = stretched_image
        return image
    
    def replace_lowest_percent_by_zero(self, image, percent):
        """
        Remplace les `percent`% des valeurs les plus basses de `array` par 0.
        
        Args:
            array (np.ndarray): tableau d'entrée
            percent (float): pourcentage entre 0 et 100

        Returns:
            np.ndarray: tableau avec les plus basses valeurs remplacées par 0
        """
        array = image.copy()
        threshold = np.percentile(array, percent)
        array[array <= threshold] = 0
        return array

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialisation du filtre
    from fitsprocessor import FitsImageManager

    fits_manager = FitsImageManager()

    fits_manager.open_fits("../../utils/01-observation-m16/01-images-initial/TargetSet.M27.8.00.LIGHT.329.2023-10-01_21-39-23.fits.fits")
    fits_manager.debayer()

    astro_filter = AstroFilters(auto_normalize=True)
    image= fits_manager.processed_data
    fits_manager.processed_data = astro_filter.stretch_histogram_asinh(image, 100, 0.005)
    fits_manager.save_as_image("test.jpg")

    fits_manager.save_fits("test.fit")


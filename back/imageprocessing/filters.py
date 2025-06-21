import numpy as np
from scipy import ndimage, signal
from scipy.fft import fft2, ifft2, fftfreq
from skimage import filters, restoration, exposure, morphology
from skimage.filters import gaussian, unsharp_mask
from skimage.restoration import denoise_wavelet, denoise_bilateral
import cv2
import warnings

class AstroFilters:
    """
    Librairie de filtres pour l'astronomie
    Compatible avec les images couleur (RGB) et noir et blanc
    Gère automatiquement la normalisation selon les besoins de chaque filtre
    """
    
    def __init__(self, auto_normalize=True):
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
    
    def stretch_histogram_asinh(self, image, stretch_factor=3.0, black_point=0.0):
        """
        Étirement asinh (arcsin hyperbolique) - très populaire en astronomie
        NÉCESSITE une normalisation automatique
        
        Args:
            image: Image numpy array - valeurs RAW acceptées
            stretch_factor: Facteur d'étirement
            black_point: Point noir (en valeurs normalisées 0-1)
        """
        # Normalisation automatique
        image_norm, orig_min, orig_max = self._auto_normalize_input(image)
        
        image_f = image_norm.astype(np.float32)
        image_f = np.maximum(image_f - black_point, 0)
        
        if len(image.shape) == 3:
            result = np.zeros_like(image_f)
            for i in range(image.shape[2]):
                channel = image_f[:, :, i]
                if stretch_factor > 0:
                    result[:, :, i] = np.arcsinh(stretch_factor * channel) / np.arcsinh(stretch_factor)
                else:
                    result[:, :, i] = channel
        else:
            if stretch_factor > 0:
                result = np.arcsinh(stretch_factor * image_f) / np.arcsinh(stretch_factor)
            else:
                result = image_f
        
        result = np.clip(result, 0, 1)
        
        # Retour à l'échelle originale si demandé
        if not self.auto_normalize:
            return self._denormalize_output(result, orig_min, orig_max)
        return result
    
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


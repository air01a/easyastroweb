import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
from scipy import ndimage
from typing import Tuple, Optional

class AutoHistogramStretch:
    """
    Algorithme d'étirement d'histogramme automatique pour images FITS stackées
    """
    
    def __init__(self):
        self.background_percentile = 1.0  # Percentile pour le fond du ciel
        self.highlight_percentile = 99.9  # Percentile pour les hautes lumières
        
    def estimate_background(self, data: np.ndarray, method: str = 'sigma_clip') -> float:
        """
        Estime le niveau de fond du ciel
        """
        if method == 'sigma_clip':
            # Méthode sigma-clipping (recommandée)
            valid_data = data[np.isfinite(data)]
            mean = np.mean(valid_data)
            std = np.std(valid_data)
            
            # Itération sigma-clipping (3 sigma)
            for _ in range(3):
                mask = np.abs(valid_data - mean) < 3 * std
                if np.sum(mask) < len(valid_data) * 0.1:
                    break
                valid_data = valid_data[mask]
                mean = np.mean(valid_data)
                std = np.std(valid_data)
                
            return mean
            
        elif method == 'percentile':
            return np.percentile(data[np.isfinite(data)], self.background_percentile)
        
        elif method == 'mode':
            # Approximation du mode via histogramme
            hist, bins = np.histogram(data[np.isfinite(data)], bins=1000)
            mode_idx = np.argmax(hist)
            return (bins[mode_idx] + bins[mode_idx + 1]) / 2
    
    def calculate_stretch_parameters(self, data: np.ndarray) -> Tuple[float, float, float]:
        """
        Calcule les paramètres d'étirement automatique
        """
        valid_data = data[np.isfinite(data)]
        
        # Estimation du fond du ciel
        background = self.estimate_background(data)
        
        # Soustraction du fond
        data_sub = valid_data - background
        data_sub = data_sub[data_sub > 0]  # Garde seulement les valeurs positives
        
        if len(data_sub) == 0:
            return background, np.max(valid_data), 1.0
        
        # Calcul des percentiles pour l'étirement
        shadows = np.percentile(data_sub, 10)  # Ombres
        highlights = np.percentile(data_sub, self.highlight_percentile)  # Hautes lumières
        
        # Calcul du gamma optimal (basé sur la médiane)
        median = np.median(data_sub)
        if highlights > shadows:
            # Gamma pour placer la médiane au milieu de l'histogramme étiré
            gamma = np.log(0.5) / np.log((median - shadows) / (highlights - shadows))
            gamma = np.clip(gamma, 0.3, 3.0)  # Limites raisonnables
        else:
            gamma = 1.0
            
        return background + shadows, background + highlights, gamma
    
    def apply_stretch(self, data: np.ndarray, 
                     black_point: float, 
                     white_point: float, 
                     gamma: float = 1.0,
                     stretch_type: str = 'linear') -> np.ndarray:
        """
        Applique l'étirement d'histogramme
        """
        # Normalisation entre 0 et 1
        stretched = (data - black_point) / (white_point - black_point)
        stretched = np.clip(stretched, 0, 1)
        
        if stretch_type == 'linear':
            pass  # Déjà fait
        elif stretch_type == 'gamma':
            stretched = np.power(stretched, 1.0 / gamma)
        elif stretch_type == 'log':
            # Étirement logarithmique
            stretched = np.log1p(stretched * 999) / np.log(1000)
        elif stretch_type == 'sqrt':
            # Étirement racine carrée
            stretched = np.sqrt(stretched)
        elif stretch_type == 'asinh':
            # Étirement asinh (bon pour les données avec large dynamique)
            beta = 0.1  # Paramètre de transition
            stretched = np.arcsinh(stretched / beta) / np.arcsinh(1.0 / beta)
        
        return stretched
    
    def auto_stretch(self, data: np.ndarray, 
                    stretch_type: str = 'gamma',
                    color_method: str = 'luminance_ratio') -> np.ndarray:
        """
        Applique l'étirement automatique complet
        
        color_method options:
        - 'luminance_ratio': Préserve les couleurs via ratios de luminance (recommandé)
        - 'lab_stretch': Étirement dans l'espace LAB
        - 'independent': Étirement indépendant par canal (altère les couleurs)
        """
        if data.ndim == 2:
            # Image monochrome
            black_point, white_point, gamma = self.calculate_stretch_parameters(data)
            return self.apply_stretch(data, black_point, white_point, gamma, stretch_type)
        
        elif data.ndim == 3:
            return self._stretch_color_image(data, stretch_type, color_method)
    
    def _stretch_color_image(self, data: np.ndarray, stretch_type: str, color_method: str) -> np.ndarray:
        """
        Étirement spécialisé pour images couleur
        """
        if color_method == 'luminance_ratio':
            return self._stretch_luminance_ratio(data, stretch_type)
        elif color_method == 'lab_stretch':
            return self._stretch_lab_space(data, stretch_type)
        elif color_method == 'independent':
            return self._stretch_independent_channels(data, stretch_type)
        else:
            raise ValueError(f"Méthode couleur inconnue: {color_method}")
    
    def _stretch_luminance_ratio(self, data: np.ndarray, stretch_type: str) -> np.ndarray:
        """
        Préserve les couleurs en gardant les ratios RGB constants par rapport à la luminance
        """
        # Calcul de la luminance (pondération ITU-R BT.709)
        luminance = 0.2126 * data[:,:,0] + 0.7152 * data[:,:,1] + 0.0722 * data[:,:,2]
        
        # Éviter la division par zéro
        luminance_safe = np.maximum(luminance, np.percentile(luminance[luminance > 0], 0.1))
        
        # Calcul des ratios couleur
        ratios = np.zeros_like(data)
        for i in range(3):
            ratios[:,:,i] = np.divide(data[:,:,i], luminance_safe, 
                                    out=np.zeros_like(data[:,:,i]), 
                                    where=luminance_safe != 0)
        
        # Étirement de la luminance seulement
        black_point, white_point, gamma = self.calculate_stretch_parameters(luminance)
        luminance_stretched = self.apply_stretch(luminance, black_point, white_point, gamma, stretch_type)
        
        # Reconstruction RGB en préservant les ratios
        result = np.zeros_like(data)
        for i in range(3):
            result[:,:,i] = luminance_stretched * ratios[:,:,i]
        
        # Clip et normalisation douce pour éviter la saturation
        result = np.clip(result, 0, 1)
        
        # Correction de saturation si nécessaire
        max_channel = np.max(result, axis=2)
        oversaturated = max_channel > 1
        if np.any(oversaturated):
            for i in range(3):
                result[:,:,i] = np.where(oversaturated, 
                                       result[:,:,i] / max_channel, 
                                       result[:,:,i])
        
        return result
    
    def _stretch_lab_space(self, data: np.ndarray, stretch_type: str) -> np.ndarray:
        """
        Étirement dans l'espace colorimétrique LAB (nécessite scikit-image)
        """
        try:
            from skimage import color
        except ImportError:
            print("Warning: scikit-image non disponible, utilisation de la méthode luminance_ratio")
            return self._stretch_luminance_ratio(data, stretch_type)
        
        # Conversion RGB -> LAB
        # Assurer que les données sont dans [0,1]
        data_norm = np.clip(data, 0, 1)
        lab = color.rgb2lab(data_norm)
        
        # Étirement seulement du canal L (luminance)
        L_channel = lab[:,:,0] / 100.0  # Normaliser L de [0,100] vers [0,1]
        
        # Calcul des paramètres sur le canal L
        black_point, white_point, gamma = self.calculate_stretch_parameters(L_channel)
        L_stretched = self.apply_stretch(L_channel, black_point, white_point, gamma, stretch_type)
        
        # Reconstruction LAB
        lab_stretched = lab.copy()
        lab_stretched[:,:,0] = L_stretched * 100.0  # Retour vers [0,100]
        
        # Conversion LAB -> RGB
        rgb_stretched = color.lab2rgb(lab_stretched)
        return np.clip(rgb_stretched, 0, 1)
    
    def _stretch_independent_channels(self, data: np.ndarray, stretch_type: str) -> np.ndarray:
        """
        Étirement indépendant par canal (altère les couleurs)
        """
        result = np.zeros_like(data)
        for i in range(data.shape[2]):
            black_point, white_point, gamma = self.calculate_stretch_parameters(data[:,:,i])
            result[:,:,i] = self.apply_stretch(data[:,:,i], black_point, white_point, gamma, stretch_type)
        return result
    
    def process_fits_file(self, input_file: str, 
                         output_file: Optional[str] = None,
                         stretch_type: str = 'gamma',
                         color_method: str = 'luminance_ratio',
                         bit_depth: int = 16) -> np.ndarray:
        """
        Traite un fichier FITS complet
        """
        # Lecture du fichier FITS
        with fits.open(input_file) as hdul:
            data = hdul[0].data.astype(np.float64)
            header = hdul[0].header
        
        # Application de l'étirement
        stretched = self.auto_stretch(data, stretch_type, color_method)
        
        # Conversion vers l'entier pour sauvegarde
        if bit_depth == 8:
            output_data = (stretched * 255).astype(np.uint8)
        elif bit_depth == 16:
            output_data = (stretched * 65535).astype(np.uint16)
        else:
            output_data = stretched.astype(np.float32)
        
        # Sauvegarde si demandée
        if output_file:
            # Mise à jour du header
            header['HISTORY'] = f'Auto histogram stretch applied ({stretch_type}, {color_method})'
            header['BITPIX'] = 8 if bit_depth == 8 else (16 if bit_depth == 16 else -32)
            
            fits.writeto(output_file, output_data, header, overwrite=True)
        
        return stretched
    
    def plot_histogram_comparison(self, original: np.ndarray, stretched: np.ndarray):
        """
        Affiche une comparaison des histogrammes avant/après
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Histogramme original
        axes[0,0].hist(original[np.isfinite(original)].flatten(), bins=256, alpha=0.7, color='blue')
        axes[0,0].set_title('Histogramme original')
        axes[0,0].set_xlabel('Intensité')
        axes[0,0].set_ylabel('Fréquence')
        axes[0,0].set_yscale('log')
        
        # Histogramme étiré
        axes[0,1].hist(stretched.flatten(), bins=256, alpha=0.7, color='red')
        axes[0,1].set_title('Histogramme étiré')
        axes[0,1].set_xlabel('Intensité')
        axes[0,1].set_ylabel('Fréquence')
        
        # Images
        axes[1,0].imshow(original, cmap='gray', vmin=np.percentile(original, 1), 
                        vmax=np.percentile(original, 99))
        axes[1,0].set_title('Image originale')
        axes[1,0].axis('off')
        
        axes[1,1].imshow(stretched, cmap='gray', vmin=0, vmax=1)
        axes[1,1].set_title('Image étirée')
        axes[1,1].axis('off')
        
        plt.tight_layout()
        plt.show()

# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation de l'algorithme"""
    
    from fitsprocessor import FitsImageManager
    fits_manager = FitsImageManager(auto_normalize=True)
    image_rgb = fits_manager.open_fits(f"astro_session/final/final21.fit").data

    stretcher = AutoHistogramStretch()
    
    methods = ['luminance_ratio', 'lab_stretch', 'independent']
    method_names = ['Luminance Ratio\n(Préserve couleurs)', 'LAB Space\n(Préserve couleurs)', 'Indépendant\n(Altère couleurs)']
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    # Image originale
    axes[0,0].imshow(np.clip(image_rgb * 3, 0, 1))  # Amplification pour visualisation
    axes[0,0].set_title('Image originale\n(amplifiée x3)')
    axes[0,0].axis('off')
    
    # Histogrammes originaux
    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        axes[1,0].hist(image_rgb[:,:,i].flatten(), bins=50, alpha=0.6, 
                      color=color, label=f'Canal {color.upper()}')
    axes[1,0].set_title('Histogrammes originaux')
    axes[1,0].legend()
    axes[1,0].set_yscale('log')
    
    # Test des méthodes
    for idx, (method, name) in enumerate(zip(methods, method_names)):
        try:
            stretched = stretcher.auto_stretch(image_rgb, 'gamma', method)
            
            # Affichage image
            axes[0, idx+1].imshow(stretched)
            axes[0, idx+1].set_title(name)
            axes[0, idx+1].axis('off')
            
            # Histogrammes étirés
            for i, color in enumerate(colors):
                axes[1, idx+1].hist(stretched[:,:,i].flatten(), bins=50, alpha=0.6, 
                                  color=color, label=f'Canal {color.upper()}')
            axes[1, idx+1].set_title(f'Histogrammes {method}')
            axes[1, idx+1].legend()
            
        except Exception as e:
            axes[0, idx+1].text(0.5, 0.5, f'Erreur:\n{str(e)}', 
                               ha='center', va='center', transform=axes[0, idx+1].transAxes)
            axes[0, idx+1].set_title(name)
    
    plt.tight_layout()
    plt.show()
    
    # Démonstration avec image plus réaliste
    print("\n=== Comparaison détaillée ===")
    
    # Méthode recommandée
    best_result = stretcher.auto_stretch(image_rgb, 'gamma', 'luminance_ratio')
    
    print("Méthode recommandée: 'luminance_ratio'")
    print("- Préserve l'équilibre des couleurs")
    print("- Évite les dominantes colorées")
    print("- Idéale pour l'astronomie couleur")
    
    # Analyse des couleurs
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Avant
    axes[0].imshow(np.clip(image_rgb * 3, 0, 1))
    axes[0].set_title('Avant étirement')
    axes[0].axis('off')
    
    # Après (méthode recommandée)
    axes[1].imshow(best_result)
    axes[1].set_title('Après (Luminance Ratio)')
    axes[1].axis('off')
    
    # Comparaison avec méthode indépendante
    independent_result = stretcher.auto_stretch(image_rgb, 'gamma', 'independent')
    axes[2].imshow(independent_result)
    axes[2].set_title('Méthode indépendante\n(couleurs altérées)')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    example_usage()
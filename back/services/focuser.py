import numpy as np
import cv2
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter
from photutils.detection import DAOStarFinder
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Callable
import time
import logging

class AutoFocusLib:
    """
    Bibliothèque pour l'autofocus astronomique basée sur l'analyse FWHM
    """
    
    def __init__(self, camera_capture_func: Callable, focuser_move_func: Callable):
        """
        Initialise la bibliothèque d'autofocus
        
        Args:
            camera_capture_func: Fonction pour capturer une image (doit retourner un array numpy)
            focuser_move_func: Fonction pour déplacer le focuser (prend une position en paramètre)
        """
        self.camera_capture = camera_capture_func
        self.focuser_move = focuser_move_func
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Paramètres par défaut
        self.star_detection_threshold = 3.0  # Seuil de détection des étoiles
        self.min_stars = 5  # Nombre minimum d'étoiles requises
        self.max_stars = 50  # Nombre maximum d'étoiles à analyser
        self.aperture_radius = 10  # Rayon d'ouverture pour l'analyse
        
    def detect_stars(self, image: np.ndarray) -> List[Tuple[float, float]]:
        """
        Détecte les étoiles dans une image
        
        Args:
            image: Image en niveaux de gris
            
        Returns:
            Liste des coordonnées (x, y) des étoiles détectées
        """
        # Normalisation de l'image
        if image.dtype != np.float32:
            image = image.astype(np.float32)
        
        # Estimation du bruit de fond
        mean_bg = np.median(image)
        std_bg = np.std(image)
        
        # Détection des étoiles avec DAOStarFinder
        daofind = DAOStarFinder(
            threshold=self.star_detection_threshold * std_bg,
            fwhm=6.0,
            brightest=self.max_stars
        )
        
        sources = daofind(image - mean_bg)
        
        if sources is None or len(sources) < self.min_stars:
            return []
            
        # Retourne les coordonnées des étoiles
        return [(s['xcentroid'], s['ycentroid']) for s in sources]
    
    def calculate_fwhm_single_star(self, image: np.ndarray, x: float, y: float) -> Optional[float]:
        """
        Calcule le FWHM d'une étoile unique
        
        Args:
            image: Image en niveaux de gris
            x, y: Coordonnées de l'étoile
            
        Returns:
            FWHM de l'étoile ou None si le calcul échoue
        """
        try:
            # Extraction d'une sous-image centrée sur l'étoile
            size = self.aperture_radius * 2
            x_int, y_int = int(x), int(y)
            
            # Vérification des limites
            if (x_int - size//2 < 0 or x_int + size//2 >= image.shape[1] or
                y_int - size//2 < 0 or y_int + size//2 >= image.shape[0]):
                return None
                
            subimage = image[y_int - size//2:y_int + size//2,
                           x_int - size//2:x_int + size//2]
            
            # Centrage précis en trouvant le maximum local
            max_pos = np.unravel_index(np.argmax(subimage), subimage.shape)
            center_y, center_x = float(max_pos[0]), float(max_pos[1])
            
            # Calcul du profil radial
            y_indices, x_indices = np.ogrid[:subimage.shape[0], :subimage.shape[1]]
            
            # Distance au centre
            distances = np.sqrt((x_indices - center_x)**2 + (y_indices - center_y)**2)
            
            # Profil radial moyenné
            max_radius = min(size//2 - 1, 10)
            radial_profile = []
            radii = []
            
            for r in range(max_radius):
                mask = (distances >= r) & (distances < r + 1)
                if np.any(mask):
                    radial_profile.append(np.mean(subimage[mask]))
                    radii.append(r)
            
            if len(radial_profile) < 3:
                return None
                
            # Ajustement gaussien du profil radial
            def gaussian_profile(r, amplitude, sigma, background):
                return amplitude * np.exp(-0.5 * (r / sigma)**2) + background
            
            try:
                # Estimation initiale des paramètres
                amplitude_init = max(radial_profile) - min(radial_profile)
                sigma_init = 2.0
                background_init = min(radial_profile)
                
                popt, _ = curve_fit(
                    gaussian_profile,
                    radii,
                    radial_profile,
                    p0=[amplitude_init, sigma_init, background_init],
                    maxfev=1000
                )
                
                # FWHM = 2.355 * sigma
                fwhm = 2.355 * abs(popt[1])
                
                # Validation du résultat
                if 0.5 <= fwhm <= 20:  # FWHM raisonnable pour l'astronomie
                    return fwhm
                    
            except:
                # Méthode de fallback : calcul FWHM simple
                return self._calculate_fwhm_fallback(subimage, center_x, center_y)
                
            return None
            
        except Exception as e:
            self.logger.warning(f"Erreur dans le calcul FWHM: {e}")
            return None
    
    def _calculate_fwhm_fallback(self, subimage: np.ndarray, center_x: float, center_y: float) -> Optional[float]:
        """
        Méthode de fallback pour calculer le FWHM quand l'ajustement gaussien échoue
        """
        try:
            # Profils horizontal et vertical passant par le centre
            center_x_int = int(center_x)
            center_y_int = int(center_y)
            
            if (0 <= center_x_int < subimage.shape[1] and 
                0 <= center_y_int < subimage.shape[0]):
                
                h_profile = subimage[center_y_int, :]
                v_profile = subimage[:, center_x_int]
                
                # Calcul FWHM sur les deux profils
                fwhm_h = self._calculate_fwhm_1d(h_profile)
                fwhm_v = self._calculate_fwhm_1d(v_profile)
                
                if fwhm_h is not None and fwhm_v is not None:
                    return (fwhm_h + fwhm_v) / 2.0
                elif fwhm_h is not None:
                    return fwhm_h
                elif fwhm_v is not None:
                    return fwhm_v
            
            return None
            
        except:
            return None
    
    def _calculate_fwhm_1d(self, profile: np.ndarray) -> Optional[float]:
        """
        Calcule le FWHM d'un profil 1D
        """
        try:
            # Lissage léger
            if len(profile) > 3:
                profile_smooth = gaussian_filter(profile.astype(np.float32), sigma=0.5)
            else:
                profile_smooth = profile.astype(np.float32)
            
            # Recherche du maximum
            max_idx = np.argmax(profile_smooth)
            max_val = profile_smooth[max_idx]
            
            # Estimation du fond (moyenne des extrémités)
            n_edge = min(3, len(profile_smooth) // 4)
            if n_edge > 0:
                background = (np.mean(profile_smooth[:n_edge]) + 
                             np.mean(profile_smooth[-n_edge:])) / 2.0
            else:
                background = np.min(profile_smooth)
            
            # Niveau à mi-hauteur
            half_max = background + (max_val - background) / 2.0
            
            # Recherche des points à mi-hauteur
            left_idx = max_idx
            right_idx = max_idx
            
            # Recherche vers la gauche
            for i in range(max_idx, 0, -1):
                if profile_smooth[i] <= half_max:
                    left_idx = i
                    break
            
            # Recherche vers la droite
            for i in range(max_idx, len(profile_smooth)):
                if profile_smooth[i] <= half_max:
                    right_idx = i
                    break
            
            # Calcul du FWHM
            if right_idx > left_idx:
                fwhm = right_idx - left_idx
                if 0.5 <= fwhm <= 20:  # Validation
                    return float(fwhm)
            
            return None
            
        except:
            return None
    
    def calculate_image_fwhm(self, image: np.ndarray) -> Optional[float]:
        """
        Calcule le FWHM moyen d'une image
        
        Args:
            image: Image en niveaux de gris
            
        Returns:
            FWHM moyen ou None si pas assez d'étoiles
        """
        # Détection des étoiles
        stars = self.detect_stars(image)
        
        if len(stars) < self.min_stars:
            self.logger.warning(f"Pas assez d'étoiles détectées: {len(stars)}")
            return None
        
        # Calcul du FWHM pour chaque étoile
        fwhm_values = []
        for x, y in stars:
            fwhm = self.calculate_fwhm_single_star(image, x, y)
            if fwhm is not None:
                fwhm_values.append(fwhm)
        
        if len(fwhm_values) < self.min_stars:
            self.logger.warning(f"Pas assez de mesures FWHM valides: {len(fwhm_values)}")
            return None
        
        # Filtrage des valeurs aberrantes (méthode IQR)
        q1, q3 = np.percentile(fwhm_values, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        filtered_fwhm = [f for f in fwhm_values if lower_bound <= f <= upper_bound]
        
        if len(filtered_fwhm) < 3:
            filtered_fwhm = fwhm_values
        
        return np.mean(filtered_fwhm)
    
    def parabolic_model(self, x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        """
        Modèle parabolique pour l'ajustement de courbe
        """
        return a * x**2 + b * x + c
    
    def hyperbolic_model(self, x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Modèle hyperbolique pour l'ajustement de courbe (souvent plus précis)
        """
        return a / np.sqrt((x - b)**2 + c) + d
    
    def find_best_focus(self, focus_positions: List[int], 
                       num_samples: int = 3, 
                       exposure_time: float = 1.0) -> Tuple[Optional[int], List[Tuple[int, float]]]:
        """
        Trouve la meilleure position de focus
        
        Args:
            focus_positions: Liste des positions de focus à tester
            num_samples: Nombre d'échantillons par position
            exposure_time: Temps d'exposition (si supporté par la caméra)
            
        Returns:
            Tuple (meilleure_position, données_mesures)
        """
        measurements = []
        
        self.logger.info(f"Début de la séquence d'autofocus sur {len(focus_positions)} positions")
        
        for position in focus_positions:
            self.logger.info(f"Test de la position {position}")
            
            # Déplacement du focuser
            try:
                self.focuser_move(position)
                time.sleep(0.1)# Attente de stabilisation
            except Exception as e:
                self.logger.error(f"Erreur lors du déplacement du focuser: {e}")
                continue
            
            # Capture et analyse de plusieurs images
            fwhm_samples = []
            
            for sample in range(num_samples):
                try:
                    # Capture d'image
                    image = self.camera_capture()
                    
                    # Conversion en niveaux de gris si nécessaire
                    if len(image.shape) == 3:
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    
                    # Calcul du FWHM
                    fwhm = self.calculate_image_fwhm(image)
                    
                    if fwhm is not None:
                        fwhm_samples.append(fwhm)
                        self.logger.debug(f"Position {position}, échantillon {sample + 1}: FWHM = {fwhm:.2f}")
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors de la capture/analyse: {e}")
                    continue
            
            # Moyenne des échantillons valides
            if fwhm_samples:
                avg_fwhm = np.mean(fwhm_samples)
                measurements.append((position, avg_fwhm))
                self.logger.info(f"Position {position}: FWHM moyen = {avg_fwhm:.2f}")
            else:
                self.logger.warning(f"Aucune mesure valide pour la position {position}")
        
        # Vérification des données
        if len(measurements) < 3:
            self.logger.error("Pas assez de mesures pour l'ajustement de courbe")
            return None, measurements
        
        # Extraction des données pour l'ajustement
        positions = np.array([m[0] for m in measurements])
        fwhm_values = np.array([m[1] for m in measurements])
        
        # Tentative d'ajustement avec différents modèles
        best_focus_pos = None
        best_model = None
        
        min_idx = np.argmin(fwhm_values)
        window_size = 2

        print(positions)
        print(fwhm_values)
        start_idx = max(min_idx - window_size, 0)
        end_idx = min(min_idx + window_size + 1, len(fwhm_values))
        subset_positions = positions[start_idx:end_idx]
        subset_fwhm = fwhm_values[start_idx:end_idx]
        # Modèle parabolique
        try:
            #popt_para, _ = curve_fit(self.parabolic_model, positions, fwhm_values)
            #a, b, c = popt_para
            coeffs = np.polyfit(subset_positions, subset_fwhm, 2)
            a, b, c = coeffs
            # Minimum de la parabole
            if a > 0:  # Parabole vers le haut
                min_pos = -b / (2 * a)
                if min(positions) <= min_pos <= max(positions):
                    best_focus_pos = int(round(min_pos))
                    best_model = "parabolic"
                    self.logger.info(f"Ajustement parabolique: position optimale = {best_focus_pos}")
        except Exception as e:
            self.logger.warning(f"Échec de l'ajustement parabolique: {e}")
        
        # Modèle hyperbolique (si le parabolique échoue)
        if best_focus_pos is None:
            try:
                # Estimation initiale pour le modèle hyperbolique
                min_idx = np.argmin(fwhm_values)
                init_b = positions[min_idx]
                init_a = np.max(fwhm_values) - np.min(fwhm_values)
                init_c = 1000
                init_d = np.min(fwhm_values)
                
                popt_hyp, _ = curve_fit(
                    self.hyperbolic_model, 
                    positions, 
                    fwhm_values,
                    p0=[init_a, init_b, init_c, init_d],
                    maxfev=2000
                )
                
                a, b, c, d = popt_hyp
                best_focus_pos = int(round(b))
                best_model = "hyperbolic"
                self.logger.info(f"Ajustement hyperbolique: position optimale = {best_focus_pos}")
                
            except Exception as e:
                self.logger.warning(f"Échec de l'ajustement hyperbolique: {e}")
        
        # Fallback: position avec le FWHM minimum
        if best_focus_pos is None:
            min_idx = np.argmin(fwhm_values)
            best_focus_pos = positions[min_idx]
            best_model = "minimum"
            self.logger.info(f"Utilisation du minimum direct: position = {best_focus_pos}")
        
        self.logger.info(f"Meilleure position de focus: {best_focus_pos} (méthode: {best_model})")
        return best_focus_pos, measurements
    
    def plot_focus_curve(self, measurements: List[Tuple[int, float]], 
                        best_position: Optional[int] = None) -> None:
        """
        Trace la courbe de focus
        
        Args:
            measurements: Liste des mesures (position, fwhm)
            best_position: Position optimale à marquer sur le graphique
        """
        if not measurements:
            return
            
        positions = [m[0] for m in measurements]
        fwhm_values = [m[1] for m in measurements]
        
        plt.figure(figsize=(10, 6))
        plt.plot(positions, fwhm_values, 'bo-', label='Mesures FWHM')
        
        if best_position is not None:
            plt.axvline(x=best_position, color='r', linestyle='--', 
                       label=f'Position optimale: {best_position}')
        
        plt.xlabel('Position du focuser')
        plt.ylabel('FWHM (pixels)')
        plt.title('Courbe d\'autofocus')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

# Exemple d'utilisation
def example_usage():
    from alpaca_client import alpaca_camera_client, ExposureSettings, CameraState, alpaca_focuser_client
    """
    Exemple d'utilisation de la version minimale
    """
    def mock_camera_capture():
        # Simulation d'une image avec étoiles
        alpaca_camera_client.start_exposure(ExposureSettings())
        while alpaca_camera_client.get_camera_state()==CameraState.EXPOSING:
            print("waiting end of exposure")
            time.sleep(1)

        image=alpaca_camera_client.get_image_array().data
        image = np.array(image)/255
        return image.astype(np.uint8)
    
    def mock_focuser_move(position):
        print(f"Déplacement du focuser vers la position {position}")
        alpaca_focuser_client.move_absolute(position)
        while alpaca_focuser_client.is_moving():
            print("focuser moving")
            time.sleep(1)
        print("focuser has settled")
    
    print("+++ Connections")
    alpaca_camera_client.connect()
    alpaca_focuser_client.connect()
    # Initialisation

    print("+++ FocusLib")

    autofocus = AutoFocusLib(mock_camera_capture, mock_focuser_move, )
    print("+++ FocusLib Config")

    # Configuration
    autofocus.star_detection_threshold = 3.0
    autofocus.min_stars = 3
    
    # Test de base
    print("+++ BaseTest")
    print("+++ Capture")

    test_image = mock_camera_capture()
    print("+++ fwhm")

    fwhm = autofocus.calculate_image_fwhm(test_image)
    print(f"FWHM test: {fwhm}")
    
    # Recherche de focus
    positions = list(range(24750, 25250, 50))
    best_pos, measurements = autofocus.find_best_focus(positions,num_samples=1)
    
    if best_pos is not None:
        print(f"Meilleure position: {best_pos}")
        autofocus.plot_focus_curve(measurements, best_pos)

if __name__ == "__main__":
    example_usage()
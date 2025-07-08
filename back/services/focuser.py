import numpy as np
import cv2
import logging
from typing import List, Tuple, Optional, Dict, Any
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from photutils.detection import DAOStarFinder
from photutils.psf import fit_fwhm

class AutoFocusLib:
    """
    Library for astronomical autofocus based on FWHM analysis
    """
    
    def __init__(self, star_detection_threshold=3, min_stars=5, max_stars = 50,  window_size=2):
        """
        Initializes the autofocus library
        """
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Paramètres par défaut
        self.star_detection_threshold = star_detection_threshold  # Seuil de détection des étoiles
        self.min_stars = min_stars  # Nombre minimum d'étoiles requises
        self.max_stars = max_stars  # Nombre maximum d'étoiles à analyser
        self.window_size=window_size
        # Stockage des mesures
        self.measurements: List[Dict[str, Any]] = []
        
    def clear_measurements(self) -> None:
        """
        Clears all stored measurements
        """
        self.measurements.clear()
        self.logger.info("Mesures effacées")
    
    def analyze_image(self, image: np.ndarray, focus_position: int) -> Dict[str, Any]:
        """
        Analyzes an image and stores the results

        Args:
            image: Grayscale or color image
            focus_position: Focus position corresponding to this image

        Returns:
            Dictionary containing the analysis results
        """ 
        # Convert to grayscale if necessary
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect stars and compute FWHM
        fwhm, num_stars = self._calculate_image_fwhm_detailed(image)
        
        # Create result
        result = {
            'focus_position': focus_position,
            'fwhm': fwhm,
            'num_stars': num_stars,
            'valid': fwhm is not None and num_stars >= self.min_stars
        }
        
        # Store measurement
        self.measurements.append(result)
        
        self.logger.info(f"Position {focus_position}: FWHM = {fwhm if fwhm else 'N/A'}, "
                        f"Étoiles = {num_stars}, Valide = {result['valid']}")
        
        return result
    


    def _calculate_image_fwhm_detailed(self, image: np.ndarray) -> Tuple[Optional[float], int]:
        """
        Calculates the average FWHM of an image with detailed information

        Args:
            image: Grayscale image

        Returns:
            Tuple (average FWHM, number of stars detected)
        """
        try:
            # Background estimation
            mean_bg = np.median(image)
            std_bg = np.std(image)
            
            # Stars detection with DAOStarFinder
            daofind = DAOStarFinder(
                threshold=self.star_detection_threshold * std_bg,
                fwhm=6.0,
                brightest=self.max_stars
            )
            
            sources = daofind(image - mean_bg)
            
            if sources is None or len(sources) < self.min_stars:
                return None, 0
            
            # FWHM calculation for all stars
            xypos = list(zip(sources['xcentroid'], sources['ycentroid']))
            fwhm_values = fit_fwhm(image, xypos=xypos, fit_shape=(5, 5), fwhm=2)

            # outliers filters
            q1, q3 = np.percentile(fwhm_values, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            filtered_fwhm = [f for f in fwhm_values if lower_bound <= f <= upper_bound]
            
            if len(filtered_fwhm) < 3:
                filtered_fwhm = fwhm_values
            
            return np.mean(filtered_fwhm), len(sources)
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul FWHM: {e}")
            return None, 0
    
    def get_measurements(self) -> List[Dict[str, Any]]:
        """
        Returns all stored measurements

        Returns:
            List of measurements
        """
        return self.measurements.copy()
    
    def get_valid_measurements(self) -> List[Dict[str, Any]]:
        """
        Returns only valid measurements

        Returns:
            List of valid measurements
        """
        return [m for m in self.measurements if m['valid']]
    
    def calculate_best_focus(self) -> Tuple[Optional[int], Optional[str], Dict[str, Any]]:
        """
        Calculates the best focus position based on stored measurements

        Returns:
            Tuple (best_position, method_used, detailed_information)
        """
        valid_measurements = self.get_valid_measurements()
        
        if len(valid_measurements) < 3:
            self.logger.error("Pas assez de mesures valides pour l'ajustement de courbe")
            return None, None, {
                'error': 'Pas assez de mesures valides',
                'total_measurements': len(self.measurements),
                'valid_measurements': len(valid_measurements)
            }
        
        # Data extraction
        positions = np.array([m['focus_position'] for m in valid_measurements])
        fwhm_values = np.array([m['fwhm'] for m in valid_measurements])
        

        sorted_indices = np.argsort(positions)
        x_sorted = positions[sorted_indices]
        y_sorted = fwhm_values[sorted_indices]

        # Manage duplicate focuser positions (calculate mean fhwm for this position)
        unique_x, inverse, counts = np.unique(x_sorted, return_inverse=True, return_counts=True)
        sum_y = np.bincount(inverse, weights=y_sorted)
        mean_y = sum_y / counts

        min_idx = np.argmin(mean_y)
        start_idx = max(min_idx - self.window_size, 0)
        end_idx = min(min_idx + self.window_size + 1, len(fwhm_values))
        subset_positions = unique_x[start_idx:end_idx]
        subset_fwhm = mean_y[start_idx:end_idx]

   
        # Try different models to find the best fitting curve
        best_focus_pos = None
        best_model = None
        fit_info = {}
        
        # Parabolic modek
        try:
            popt_para, pcov_para = curve_fit(self._parabolic_model, subset_positions, subset_fwhm)
            a, b, c = popt_para
            
            # Parabole minima
            if a > 0:  
                min_pos = -b / (2 * a)
                if min(positions) <= min_pos <= max(positions):
                    best_focus_pos = int(round(min_pos))
                    best_model = "parabolic"
                    fit_info = {
                        'coefficients': popt_para,
                        'covariance': pcov_para,
                        'r_squared': self._calculate_r_squared(positions, fwhm_values, 
                                                              self._parabolic_model, popt_para)
                    }
                    self.logger.info(f"Ajustement parabolique: position optimale = {best_focus_pos}")
        except Exception as e:
            self.logger.warning(f"Échec de l'ajustement parabolique: {e}")
        
        # Hyperbolic model (if parabolic fails)
        if best_focus_pos is None:
            try:
                # Initial guess for hyperbolic model
                min_idx = np.argmin(fwhm_values)
                init_b = positions[min_idx]
                init_a = np.max(fwhm_values) - np.min(fwhm_values)
                init_c = 1000
                init_d = np.min(fwhm_values)
                
                popt_hyp, pcov_hyp = curve_fit(
                    self._hyperbolic_model, 
                    positions, 
                    fwhm_values,
                    p0=[init_a, init_b, init_c, init_d],
                    maxfev=2000
                )
                
                a, b, c, d = popt_hyp
                best_focus_pos = int(round(b))
                best_model = "hyperbolic"
                fit_info = {
                    'coefficients': popt_hyp,
                    'covariance': pcov_hyp,
                    'r_squared': self._calculate_r_squared(positions, fwhm_values, 
                                                          self._hyperbolic_model, popt_hyp)
                }
                self.logger.info(f"Ajustement hyperbolique: position optimale = {best_focus_pos}")
                
            except Exception as e:
                self.logger.warning(f"Échec de l'ajustement hyperbolique: {e}")
        
        # Fallback: position with minimum FWHM
        if best_focus_pos is None:
            min_idx = np.argmin(fwhm_values)
            best_focus_pos = positions[min_idx]
            best_model = "minimum"
            fit_info = {'min_fwhm': fwhm_values[min_idx]}
            self.logger.info(f"Utilisation du minimum direct: position = {best_focus_pos}")
        
        detailed_info = {
            'method': best_model,
            'best_position': best_focus_pos,
            'fit_info': fit_info,
            'total_measurements': len(self.measurements),
            'valid_measurements': len(valid_measurements),
            'fwhm_range': (float(np.min(fwhm_values)), float(np.max(fwhm_values))),
            'position_range': (int(np.min(positions)), int(np.max(positions)))
        }
        
        self.logger.info(f"Meilleure position de focus: {best_focus_pos} (méthode: {best_model})")
        return best_focus_pos, best_model, detailed_info
    
    def _parabolic_model(self, x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        """
        Parabolic model for curve fitting
        """
        return a * x**2 + b * x + c
    
    def _hyperbolic_model(self, x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        Hyperbolic model for curve fitting (often more accurate)
        """
        return a / np.sqrt((x - b)**2 + c) + d
    
    def _calculate_r_squared(self, x: np.ndarray, y: np.ndarray, model_func, params) -> float:
        """
        Calculates the coefficient of determination R²
        """
        y_pred = model_func(x, *params)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - (ss_res / ss_tot)
    
    def plot_focus_curve(self, show_fit: bool = True) -> None:
        """
        Plots the focus curve based on stored measurements

        Args:
            show_fit: If True, also displays the fitted curve
        """
        valid_measurements = self.get_valid_measurements()
        
        if not valid_measurements:
            self.logger.warning("Aucune mesure valide à afficher")
            return
            
        positions = [m['focus_position'] for m in valid_measurements]
        fwhm_values = [m['fwhm'] for m in valid_measurements]
        
        plt.figure(figsize=(12, 8))
        
        # Points de mesure
        plt.subplot(2, 1, 1)
        plt.plot(positions, fwhm_values, 'bo-', label='Mesures FWHM', markersize=8)
        
        # Ajout de la courbe d'ajustement si demandé
        if show_fit and len(valid_measurements) >= 3:
            best_pos, method, info = self.calculate_best_focus()
            if best_pos is not None:
                plt.axvline(x=best_pos, color='r', linestyle='--', 
                           label=f'Position optimale: {best_pos} ({method})')
                
                # Courbe d'ajustement
                if method in ['parabolic', 'hyperbolic']:
                    x_fit = np.linspace(min(positions), max(positions), 100)
                    model_func = self._parabolic_model if method == 'parabolic' else self._hyperbolic_model
                    y_fit = model_func(x_fit, *info['fit_info']['coefficients'])
                    plt.plot(x_fit, y_fit, 'r-', alpha=0.7, label=f'Ajustement {method}')
        
        plt.xlabel('Position du focuser')
        plt.ylabel('FWHM (pixels)')
        plt.title('Courbe d\'autofocus')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Graphique du nombre d'étoiles
        plt.subplot(2, 1, 2)
        star_counts = [m['num_stars'] for m in valid_measurements]
        plt.plot(positions, star_counts, 'go-', label='Nombre d\'étoiles', markersize=6)
        plt.xlabel('Position du focuser')
        plt.ylabel('Nombre d\'étoiles détectées')
        plt.title('Nombre d\'étoiles par position')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def export_measurements(self, filename: str) -> None:
        """
        Exports measurements to a CSV file

        Args:
            filename: Output file name
        """
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['focus_position', 'fwhm', 'num_stars', 'valid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for measurement in self.measurements:
                writer.writerow(measurement)
        
        self.logger.info(f"Mesures exportées vers {filename}")
    
    def get_focus_statistics(self) -> Dict[str, Any]:
        """
        Returns statistics about the measurements

        Returns:
            Dictionary containing statistics
        """
        valid_measurements = self.get_valid_measurements()
        
        if not valid_measurements:
            return {'error': 'Aucune mesure valide'}
        
        fwhm_values = [m['fwhm'] for m in valid_measurements]
        star_counts = [m['num_stars'] for m in valid_measurements]
        
        return {
            'total_measurements': len(self.measurements),
            'valid_measurements': len(valid_measurements),
            'fwhm_stats': {
                'min': float(np.min(fwhm_values)),
                'max': float(np.max(fwhm_values)),
                'mean': float(np.mean(fwhm_values)),
                'std': float(np.std(fwhm_values)),
                'median': float(np.median(fwhm_values))
            },
            'star_count_stats': {
                'min': int(np.min(star_counts)),
                'max': int(np.max(star_counts)),
                'mean': float(np.mean(star_counts)),
                'median': float(np.median(star_counts))
            }
        }

# Exemple d'utilisation
def example_usage():
    from alpaca_client import alpaca_camera_client, ExposureSettings, CameraState, alpaca_focuser_client
    import time
    """
    Example usage of the minimal version
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
    autofocus = AutoFocusLib( )
    print("+++ FocusLib Config")

    
    print("+++ fwhm")
    
    # Recherche de focus
    positions = list(range(24750, 25250, 50))

    for position in positions:
        mock_focuser_move(position)
        for i in range(3):
            result = autofocus.analyze_image(mock_camera_capture(),position)

    final_result = autofocus.calculate_best_focus()

    print(final_result)
    autofocus.plot_focus_curve()

if __name__ == "__main__":
    example_usage()
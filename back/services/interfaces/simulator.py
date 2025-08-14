from time import sleep
import time
from utils.logger import logger
from services.configurator import CONFIG
import numpy as np
from pathlib import Path
from models.state import telescope_state
from models.telescope_interface import TelescopeInterface
from imageprocessing.fitsprocessor import FitsImageManager
from utils.calcul import apply_focus_blur
from datetime import datetime, timezone
import random

class SimulatorTelescope(TelescopeInterface):

    def __init__(self):
        super().__init__()
        self.fits_dir = Path(CONFIG["global"].get("simulator_light_directory",".")) #        "D:/Astronomie/observations/2024-02-12/DARK"
        self.fits_files =  self.fits_files = sorted(
            list(self.fits_dir.glob("*.fit")) + list(self.fits_dir.glob("*.fits")),
            key=lambda x: x.stat().st_mtime  # Tri par date de modification
        )
        self.fits_manager = FitsImageManager(auto_debayer=False)
        self.dark_dir = Path(CONFIG["global"].get("simulator_dark_directory",".")) #        "D:/Astronomie/observations/2024-02-12/DARK"
        self.dark_files =  (list(self.dark_dir.glob("*.fit")) + list(self.dark_dir.glob("*.fits")))
        logger.info(f"[SIMULATOR] - Found {len(self.fits_files)} FITS files in {self.fits_dir}")
        logger.info(f"[SIMULATOR] - Found {len(self.dark_files)} DARK FITS files in {self.dark_dir}")
        self.index = 0
        self.index_dark = 0
        self.focuser_name = "Simulator Focuser"
        self.focuser_position = 25000
        self.initial_temperature = 15
        self.target_temperature = 15
        self.bayer = None
        self.location = "0.0°, 0.0°, 0.0m"  # Default location

    def set_utc_date(self, date: str):
        """
        Set the date for the simulator.
        """
        logger.info(f"[SIMULATOR] - Setting date to {date}")
        # In a real implementation, this would set the date in the simulator environment.
        # Here we just log it for demonstration purposes.
    
    def _add_satellite_trail(self, image_data):
        """
        Ajoute une trace de satellite aléatoire sur l'image.
        
        Args:
            image_data: Données de l'image (numpy array)
            
        Returns:
            Image avec la trace de satellite ajoutée
        """

        
        # Copie pour ne pas modifier l'original
        modified_data = image_data.copy()
        
        # Déterminer les dimensions
        if len(modified_data.shape) == 2:  # Image en niveaux de gris
            h, w = modified_data.shape
        elif len(modified_data.shape) == 3:  # Image couleur
            h, w, c = modified_data.shape
        else:
            return modified_data  # Format non supporté
        
        # Générer une ligne qui traverse TOUT l'écran avec pente et position aléatoires
        
        # Générer une pente aléatoire (coefficient directeur)
        # Éviter les pentes trop verticales pour garder une ligne visible
        slope = random.uniform(-2.0, 2.0)  # Pente entre -2 et +2
        
        # Générer un point aléatoire au milieu de l'image par lequel la ligne passe
        center_x = random.randint(w // 4, 3 * w // 4)
        center_y = random.randint(h // 4, 3 * h // 4)
        
        # Calculer l'ordonnée à l'origine : y = slope * x + b  =>  b = y - slope * x
        b = center_y - slope * center_x
        
        # Trouver les points d'intersection avec les bords de l'image
        intersection_points = []
        
        # Intersection avec le bord gauche (x = 0)
        y_left = b
        if 0 <= y_left < h:
            intersection_points.append((0, int(y_left)))
        
        # Intersection avec le bord droit (x = w-1)
        y_right = slope * (w-1) + b
        if 0 <= y_right < h:
            intersection_points.append((w-1, int(y_right)))
        
        # Intersection avec le bord haut (y = 0)
        if slope != 0:
            x_top = -b / slope
            if 0 <= x_top < w:
                intersection_points.append((int(x_top), 0))
        
        # Intersection avec le bord bas (y = h-1)
        if slope != 0:
            x_bottom = (h-1 - b) / slope
            if 0 <= x_bottom < w:
                intersection_points.append((int(x_bottom), h-1))
        
        # Prendre les deux premiers points d'intersection (il devrait y en avoir exactement 2)
        if len(intersection_points) >= 2:
            start_x, start_y = intersection_points[0]
            end_x, end_y = intersection_points[1]
        else:
            # Fallback: ligne diagonale si problème de calcul
            start_x, start_y = 0, 0
            end_x, end_y = w-1, h-1
        
        # Générer une intensité et épaisseur aléatoires
        base_intensity = np.max(modified_data)
        brightness_factor = random.uniform(1.5, 3.0)  # Entre 1.5x et 3x plus brillant
        satellite_value = base_intensity * brightness_factor
        
        thickness = random.randint(1, 3)  # Épaisseur entre 1 et 3 pixels
        
        # Dessiner la ligne de Bresenham
        points = self._bresenham_line(start_x, start_y, end_x, end_y)
        
        # Appliquer la trace
        for x, y in points:
            if 0 <= x < w and 0 <= y < h:
                # Appliquer avec épaisseur
                for dx in range(-thickness, thickness + 1):
                    for dy in range(-thickness, thickness + 1):
                        px, py = x + dx, y + dy
                        if 0 <= px < w and 0 <= py < h:
                            # Calcul de l'atténuation basée sur la distance au centre
                            distance = np.sqrt(dx*dx + dy*dy)
                            if distance <= thickness:
                                attenuation = max(0.3, 1 - distance / (thickness + 1))
                                final_value = min(satellite_value * attenuation, 65535)
                                
                                if len(modified_data.shape) == 2:  # Niveaux de gris
                                    modified_data[py, px] = max(modified_data[py, px], final_value)
                                else:  # Couleur
                                    for channel in range(c):
                                        modified_data[py, px, channel] = max(
                                            modified_data[py, px, channel], 
                                            final_value
                                        )
        
        logger.info(f"[SIMULATION] Random satellite trail added: ({start_x},{start_y}) -> ({end_x},{end_y}), "
                    f"slope={slope:.2f}, brightness={brightness_factor:.1f}x, thickness={thickness}px")
        return modified_data

    def _bresenham_line(self, x0, y0, x1, y1):
        """
        Algorithme de Bresenham pour dessiner une ligne.
        
        Returns:
            Liste des points (x, y) de la ligne
        """
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            points.append((x, y))
            
            if x == x1 and y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return points


    def camera_capture(self, expo: float, light: bool = True):
        try:
            if light:
                
                new = self.fits_manager.open_fits(self.fits_files[self.index])
                if self.focuser_position!=25000:
                    new.data = self.fits_manager.debayer(new.data, new.bayer_pattern)
                    new.data = apply_focus_blur(new.data, self.focuser_position, 25000, 0.01)
                    new.data = self.fits_manager._convert_to_bayer(new.data, new.bayer_pattern)

                if random.random() < 1/10:
                    new.data = self._add_satellite_trail(new.data)
                    
                self.index = (self.index + 1) % len(self.fits_files)

            else:
                new = self.fits_manager.open_fits(self.dark_files[self.index_dark])
                self.index_dark = (self.index_dark + 1) % len(self.dark_files)



            sleep(expo)
            self.bayer = new.bayer_pattern
            telescope_state.last_picture = new.data

            return new
        except Exception as e:
            print(e)
            return None
        
    def get_bayer_pattern(self):
        sensor_type = self.bayer
        
        if sensor_type == 'RGGB':
            return  'RGGB', 'RGGB', 'BAYER'
        elif sensor_type == 'CMYG':
            return 'CMYG', 'CMYG', 'BAYER'
        elif sensor_type == 'CMYG2':
            return 'CMYG2', 'CMYG2', 'BAYER'
        elif sensor_type == 'LRGB':
            return 'LRGB', None, None
        elif sensor_type == 'COLOR':
            return 'COLOR', None, None
        else:
            return 'MONOCHROME', None, None
        
    def set_gain(self, gain: int):
        logger.info(f"[CAMERA] - Setting gain to {gain}")

    def set_camera_gain(self, gain: int):
        return True

    def camera_connect(self):
        return True

    def move_focuser(self, position: int):
        self.focuser_position = position
        sleep(1)

    def focuser_connect(self):
        self.focuser_name = "test"

    def focuser_get_current_position(self):
        return self.focuser_position

    def telescope_connect(self):

        return True
    
    def telescope_disconnect(self):
        return True
    

    def sync_location(self, latitude: float, longitude : float, elevation: float):
        logger.info(f"[TELESCOPE] - Simulated location synchronized to lat: {latitude}, lon: {longitude}, elev: {elevation}")
        self.location = f"{latitude}°, {longitude}°, {elevation}m"


    def get_utc_date(self):
        return datetime.now(timezone.utc).isoformat()

    def get_telescope_location(self):
        return self.location


    def slew_to_target(self,ra: float, dec: float):
        try:

            time.sleep(1)
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error slewing to target: {e}")
            return False

    def sync_to_coordinates(self, ra:float, dec: float) -> bool:
        try:
            return True
        except:
            return False

    def telescope_unpark(self):
        pass

    def filter_wheel_connect(self)-> bool:
        try:
            return True
        except:
            return False

    def change_filter(self, filter)-> bool:
        try:
            filters = CONFIG['filterwheel'].get("filters", [])
            index = filters.index(filter)
            logger.info(f"[FILTERWHEEL] - Moving to position {index}")

            return True
        except:
            logger.info(f"[FILTERWHEEL] - Error during filter change")
            return False

    def telescope_set_tracking(self, rate : int):
        pass
        

    def get_ccd_temperature(self)-> int:
        if self.initial_temperature > self.target_temperature:
            self.initial_temperature -= 1
        else:
            self.initial_temperature += 1
        logger.info(f"[CCD] - Current temperature: {self.initial_temperature}°C")
        return self.initial_temperature

    def set_ccd_temperature(self, temperature:int)-> None:
        self.target_temperature = temperature
        pass
    def set_cooler(self, cooler: bool):
        pass


    def connect(self):
        try:
            telescope_state.is_focuser_connected = True
        except:
            telescope_state.is_focuser_connected = False
            
        try:
            telescope_state.is_camera_connected = True
        except Exception as e:
            telescope_state.is_camera_connected = False
            print(f"[CAMERA] - Error connecting camera: {e}")

        try:
            telescope_state.is_telescope_connected = True
        except:
            telescope_state.is_telescope_connected = False  
        try:
            self.sync_location(
                CONFIG["observatory"].get("latitude", 0.0),
                CONFIG["observatory"].get("longitude", 0.0),
                CONFIG["observatory"].get("altitude", 0.0)
            )
        
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error synchronizing location: {e}")
            
        self.mount_name = "Simulator Mount"
        self.fw_name = "Simulator Filter Wheel"
        self.camera_name = "Simulator Camera"
        self.focuser_name = "Simulator Focuser"
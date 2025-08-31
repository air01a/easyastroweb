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
        # Path to the directory containing light FITS files for simulation
        self.fits_dir = Path(CONFIG["global"].get("simulator_light_directory",".")) 
        # Load FITS files (both .fit and .fits) sorted by modification time
        self.fits_files = sorted(
            list(self.fits_dir.glob("*.fit")) + list(self.fits_dir.glob("*.fits")),
            key=lambda x: x.stat().st_mtime
        )
        self.fits_manager = FitsImageManager(auto_debayer=False)
        # Path to the directory containing dark FITS files for simulation
        self.dark_dir = Path(CONFIG["global"].get("simulator_dark_directory",".")) 
        self.dark_files = (list(self.dark_dir.glob("*.fit")) + list(self.dark_dir.glob("*.fits")))
        logger.info(f"[SIMULATOR] - Found {len(self.fits_files)} FITS files in {self.fits_dir}")
        logger.info(f"[SIMULATOR] - Found {len(self.dark_files)} DARK FITS files in {self.dark_dir}")
        self.index = 0
        self.index_dark = 0
        self.focuser_position = 25000
        self.initial_temperature = 15
        self.target_temperature = 15
        self.bayer = None
        self.location = "0.0°, 0.0°, 0.0m"  # Default simulated location
        
        self.focuser_is_moving = False

    def set_utc_date(self, date: str):
        """
        Set the simulator date (for logging purposes only).
        """
        logger.info(f"[SIMULATOR] - Setting date to {date}")
        # In a real telescope, this would set the date in the system.
        # Here we simply log the date.

    def _add_satellite_trail(self, image_data):
        """
        Add a random simulated satellite trail to the image.

        Args:
            image_data: Image data (numpy array)

        Returns:
            Image with the satellite trail added
        """
        # Copy the image to avoid modifying the original
        modified_data = image_data.copy()
        
        # Determine image dimensions
        if len(modified_data.shape) == 2:  # Grayscale image
            h, w = modified_data.shape
        elif len(modified_data.shape) == 3:  # Color image
            h, w, c = modified_data.shape
        else:
            return modified_data  # Unsupported format
        
        # Generate a line crossing the entire image with a random slope and position
        
        # Random slope (avoiding very steep slopes to ensure visibility)
        slope = random.uniform(-2.0, 2.0)
        
        # Random point near the center of the image through which the line passes
        center_x = random.randint(w // 4, 3 * w // 4)
        center_y = random.randint(h // 4, 3 * h // 4)
        
        # Calculate y-intercept for line equation y = slope * x + b
        b = center_y - slope * center_x
        
        # Find intersection points with image borders
        intersection_points = []
        
        # Left border (x = 0)
        y_left = b
        if 0 <= y_left < h:
            intersection_points.append((0, int(y_left)))
        
        # Right border (x = w - 1)
        y_right = slope * (w-1) + b
        if 0 <= y_right < h:
            intersection_points.append((w-1, int(y_right)))
        
        # Top border (y = 0)
        if slope != 0:
            x_top = -b / slope
            if 0 <= x_top < w:
                intersection_points.append((int(x_top), 0))
        
        # Bottom border (y = h - 1)
        if slope != 0:
            x_bottom = (h-1 - b) / slope
            if 0 <= x_bottom < w:
                intersection_points.append((int(x_bottom), h-1))
        
        # Select first two intersection points (should always be 2)
        if len(intersection_points) >= 2:
            start_x, start_y = intersection_points[0]
            end_x, end_y = intersection_points[1]
        else:
            # Fallback: diagonal line
            start_x, start_y = 0, 0
            end_x, end_y = w-1, h-1
        
        # Random brightness and thickness for the trail
        base_intensity = np.max(modified_data)
        brightness_factor = random.uniform(1.5, 3.0)
        satellite_value = base_intensity * brightness_factor
        
        thickness = random.randint(1, 3)  # Thickness in pixels
        
        # Compute line points using Bresenham's algorithm
        points = self._bresenham_line(start_x, start_y, end_x, end_y)
        
        # Apply the satellite trail to the image
        for x, y in points:
            if 0 <= x < w and 0 <= y < h:
                # Apply thickness effect
                for dx in range(-thickness, thickness + 1):
                    for dy in range(-thickness, thickness + 1):
                        px, py = x + dx, y + dy
                        if 0 <= px < w and 0 <= py < h:
                            # Attenuate brightness based on distance from the center
                            distance = np.sqrt(dx*dx + dy*dy)
                            if distance <= thickness:
                                attenuation = max(0.3, 1 - distance / (thickness + 1))
                                final_value = min(satellite_value * attenuation, 65535)
                                
                                if len(modified_data.shape) == 2:  # Grayscale
                                    modified_data[py, px] = max(modified_data[py, px], final_value)
                                else:  # Color
                                    for channel in range(c):
                                        modified_data[py, px, channel] = max(
                                            modified_data[py, px, channel], 
                                            final_value
                                        )
        
        logger.info(f"[SIMULATION] Random satellite trail added: ({start_x},{start_y}) -> ({end_x},{end_y}), "
                    f"slope={slope:.2f}, brightness={brightness_factor:.1f}x, thickness={thickness}px")
        return modified_data


    def set_bin_x(self, binx):
        pass

    def set_bin_y(self, biny):
        pass

    def _bresenham_line(self, x0, y0, x1, y1):
        """
        Bresenham's line drawing algorithm.

        Returns:
            List of (x, y) points of the line
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
        """
        Simulate camera capture with optional satellite trails.
        """
        try:
            if light:
                # Load next light frame
                new = self.fits_manager.open_fits(self.fits_files[self.index])
                if self.focuser_position != 25000:
                    new.data = self.fits_manager.debayer(new.data, new.bayer_pattern)
                    new.data = apply_focus_blur(new.data, self.focuser_position, 25000, 0.01)
                    new.data = self.fits_manager._convert_to_bayer(new.data, new.bayer_pattern)

                # Add a satellite trail in 10% of captures
                if random.random() < 1/10:
                    new.data = self._add_satellite_trail(new.data)
                    
                self.index = (self.index + 1) % len(self.fits_files)
            else:
                # Load next dark frame
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
        """
        Return the Bayer pattern and color model information.
        """
        sensor_type = self.bayer
        
        if sensor_type == 'RGGB':
            return 'RGGB', 'RGGB', 'BAYER'
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
        """
        Move the simulated focuser to a new position.
        """
        number_step=20
        delta = position - self.focuser_position
        step = delta // number_step
        self.focuser_is_moving = True

        i=0
        while self.focuser_is_moving and i<number_step:
            self.focuser_position += step
            sleep(10/number_step)
            i+=1
        if self.focuser_is_moving:
            self.focuser_position=position
        self.focuser_is_moving = False


    def focuser_halt(self):
        try:
            self.focuser_is_moving = False
        except Exception as e:
            logger.error(f"[FOCUSER] - Focuser error: {e}")

    def focuser_connect(self):
        self.focuser_name = "test"

    def focuser_get_current_position(self):
        return self.focuser_position

    def telescope_connect(self):
        return True
    
    def telescope_disconnect(self):
        return True
    
    def sync_location(self, latitude: float, longitude: float, elevation: float):
        """
        Synchronize simulated telescope location.
        """
        if CONFIG['telescope'].get('has_gps', False):
            logger.info(f"[TELESCOPE] - GPS on telescope, no location sync")
            return True
        logger.info(f"[TELESCOPE] - Simulated location synchronized to lat: {latitude}, lon: {longitude}, elev: {elevation}")
        self.location = f"{latitude}°, {longitude}°, {elevation}m"

    def get_utc_date(self):
        """
        Return the current UTC date in ISO format.
        """
        return datetime.now(timezone.utc).isoformat()

    def get_telescope_location(self):
        return self.location

    def slew_to_target(self, ra: float, dec: float):
        """
        Simulate slewing the telescope to the given coordinates.
        """
        try:
            time.sleep(1)  # Simulate slewing time
        except Exception as e:
            logger.error(f"[TELESCOPE] - Error slewing to target: {e}")
            return False

    def sync_to_coordinates(self, ra: float, dec: float) -> bool:
        """
        Simulate syncing telescope coordinates.
        """
        try:
            return True
        except:
            return False

    def telescope_unpark(self):
        pass

    def filter_wheel_connect(self) -> bool:
        return True

    def change_filter(self, filter) -> bool:
        """
        Simulate changing the filter on the filter wheel.
        """
        try:
            filters = CONFIG['filterwheel'].get("filters", [])
            index = filters.index(filter)
            logger.info(f"[FILTERWHEEL] - Moving to position {index}")
            return True
        except:
            logger.info(f"[FILTERWHEEL] - Error during filter change")
            return False
    
    
    def get_max_focuser_step(self):
        return 40000
          
    def telescope_set_tracking(self, rate: int):
        pass

    def get_ccd_temperature(self) -> int:
        """
        Simulate CCD temperature stabilization toward target temperature.
        """
        if self.initial_temperature > self.target_temperature:
            self.initial_temperature -= 1
        else:
            self.initial_temperature += 1
        logger.info(f"[CCD] - Current temperature: {self.initial_temperature}°C")
        return self.initial_temperature

    def set_ccd_temperature(self, temperature: int) -> None:
        self.target_temperature = temperature

    def set_cooler(self, cooler: bool):
        pass

    def connect(self):
        """
        Simulate connecting all telescope components.
        """
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
            telescope_state.is_fw_connected = True
        except:
            telescope_state.is_fw_connected = False  

        # Sync simulated location with config
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

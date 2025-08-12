import multiprocessing as mp
import queue
import numpy as np
from typing import List, Optional, Tuple
import astroalign as aa
from scipy import stats
import logging
from pathlib import Path
import threading
from utils.logger import logger
from time import sleep
from imageprocessing.fitsprocessor import FitsImageManager

class ImageStacker:
    """
    Class for aligning and stacking FITS images in a separate process.
    Uses astroalign for alignment and winsorized sigma clipping for stacking.
    """
    
    def __init__(self, sigma_threshold: float = 4, max_history: int = 7, dark = None, target_width: int = 800):
        """
        Initialize the image stacker.
        
        Args:
            sigma_threshold: Threshold for sigma clipping
            max_history: Number of images to keep in history for sigma clipping
        """
        self.logger = logger

        self.sigma_threshold = sigma_threshold
        self.max_history = max_history
        self.callback = None  # Will be assigned after creation
        self.target_width = target_width
        # Instantiate FitsImageManager once
        self.fits_manager = FitsImageManager(auto_debayer=True, auto_normalize=True )
        self.sigma_history = []  # History of images for sigma clipping
        self.dark_file = dark
        if dark is not None:
            self.fits_manager.set_dark_from_file(dark)
        
        # Queues for inter-process communication
        self.input_queue = mp.Queue()
        self.output_queue = mp.Queue()
        self.control_queue = mp.Queue()
        
        # Queue for synchronization (replaces non-picklable locks)
        self.sync_queue = mp.Queue()
        
        # Thread to handle callbacks in a non-blocking manner
        self.callback_thread = None
        self.callback_stop_event = None
        
        # Worker process
        self.process = None
        self.is_running = False
        
        # Counters for synchronization (managed via sync_queue)
        self.images_added = 0
        self.images_processed = 0
        self.path = None
        # Logging configuration
    
    def start_live_stacking(self):
        """Start the stacking process."""
        if self.is_running:
            self.logger.warning("Process is already running")
            return
        
        self.process = mp.Process(target=self._worker_process)
        self.process.start()
        
        # Start the callback thread if a callback is provided
        if self.callback is not None:
            self.callback_stop_event = threading.Event()
            self.callback_thread = threading.Thread(target=self._callback_handler)
            self.callback_thread.daemon = True
            self.callback_thread.start()
        
        self.is_running = True
        self.logger.info("Stacking process started")
    
    def stop_live_stacking(self):
        """Stop the stacking process."""
        if not self.is_running:
            return
        
        # Stop the callback thread
        if self.callback_thread is not None:
            self.callback_stop_event.set()
            self.callback_thread.join(timeout=5)
        
        self.control_queue.put("STOP")
        self.process.join(timeout=10)
        
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        
        self.is_running = False
        self.logger.info("Stacking process stopped")
    
    def process_new_image(self, image_path: str):
        """
        Add an image to stack.
        
        Args:
            image_path: Path to the FITS file
        """
        if not self.is_running:
            raise RuntimeError("Process is not started. Call start() first.")
        
        self.images_added += 1
        self.input_queue.put(image_path)
        self.logger.info(f"Image added to queue: {image_path} (Total added: {self.images_added})")
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """
        Wait until all added images have been processed.
        
        Args:
            timeout: Timeout in seconds (None = no timeout)
            
        Returns:
            bool: True if all images have been processed, False if timeout
        """
        import time
        start_time = time.time()
        
        # Empty the sync_queue at the beginning
        while True:
            try:
                self.sync_queue.get_nowait()
            except queue.Empty:
                break
        
        while True:
            if self.images_processed >= self.images_added:
                self.logger.info(f"All images have been processed ({self.images_processed}/{self.images_added})")
                return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self.logger.warning(f"Timeout reached - {self.images_processed}/{self.images_added} images processed")
                    return False
            
            # Wait for a signal from sync_queue or timeout
            try:
                self.sync_queue.get(timeout=0.5)
            except queue.Empty:
                continue
    
    def get_processing_status(self) -> Tuple[int, int]:
        """
        Return the processing status.
        
        Returns:
            Tuple (images_processed, images_added)
        """
        return self.images_processed, self.images_added
    
    def _callback_handler(self):
        """Thread that handles callbacks in a non-blocking manner."""
        while not self.callback_stop_event.is_set():
            try:
                result = self.output_queue.get(timeout=1.0)
                if result is not None:
                    stacked_image, metadata = result
                    
                    # Increment the processed images counter
                    self.images_processed += 1
                    
                    # Signal via sync_queue for wait_for_completion
                    try:
                        self.sync_queue.put_nowait("PROCESSED")
                    except:
                        pass  # Queue full, not a problem
                    
                    try:
                        # Call the callback in a try/catch to avoid crashing
                        self.callback(stacked_image, metadata, self.path)
                    except Exception as e:
                        self.logger.error(f"Error in callback: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in callback handler: {e}")
                break


    def prepare_for_live_stacking(self, image):
        """Optimal size for live stacking """
        if self.target_width <= 0:
            return image
        h, w = image.shape[:2]
        bin_factor = max(1, w // self.target_width)
        logger.info(f"[Stacker] - Preparing image for live stacking: original size {w}x{h}, bin factor {bin_factor}")
        if bin_factor >= 2:
            return FitsImageManager.bin_image(image, bin_factor)  # ✅ BINNING
        else:
            return image  # Small enough, no binning needed
        

    def _worker_process(self):
        """Worker process that performs alignment and stacking."""
        stacked_image = None
        image_history = []  # History of recent images for sigma clipping
        reference_image = None
        total_images_processed = 0
        
        restack_done = False
        logger = logging.getLogger(f"{__name__}.worker")
        logger.info("Worker process started")
        image_batch = []

        while True:
            try:
                # Check control commands
                try:
                    control_msg = self.control_queue.get_nowait()
                    if control_msg == "STOP":
                        logger.info("Stopping worker process")
                        break
                except queue.Empty:
                    pass
                
                # Process new images

                while True:
                    try:
                        image_path = self.input_queue.get_nowait()
                        image_batch.append(image_path)
                    except queue.Empty:
                        break

                if len(image_batch)==0:
                    sleep(1)
                    continue

                image_path = image_batch.pop()
                logger.info(f"Processing image: {image_path}")
                
                # Load the image
                image_data, header = self._load_fits_image(image_path)
                image_data = self.prepare_for_live_stacking(image_data)
                if image_data is None:
                    continue
                if reference_image is None:
                    # First image = reference
                    reference_image = image_data.copy()
                    stacked_image = image_data.copy()
                    image_history = [image_data.copy()]
                    total_images_processed = 1
                    
                    metadata = {
                        'total_images': total_images_processed,
                        'last_image_path': image_path,
                        'shape': stacked_image.shape,
                        'image_type': 'color' if len(stacked_image.shape) == 3 else 'grayscale',
                        'channels': stacked_image.shape[2] if len(stacked_image.shape) == 3 else 1
                    }
                    
                    self.output_queue.put((stacked_image.copy(), metadata))
                    logger.info("[Stacker] - Reference image set and sent")
                    
                else:
                    # Align the image to the reference
                    aligned_image = self._align_image(image_data, reference_image)
                    if aligned_image is None:
                        logger.warning(f"[Stacker] - Unable to align image: {image_path}")
                        self.output_queue.put((stacked_image.copy(), {'error': 'Alignment failed', 'image_path': image_path}))
                        continue



                    # Restack first images for sigma clipping reference image
                    # This is done only once after the first images are processed
                    # Without this, the reference image (the first one) could lead to unwanted artefacts (satellite trails, etc.)
                    if not restack_done and total_images_processed == self.max_history:
                        logger.info("[Stacker] - Restacking images for sigma clipping reference")
                        stacked_image = None
                        images = image_history.copy()
                        for image in images:
                            processed_image = self._winsorized_sigma_clip(
                                image, image_history
                            )
                            # Update history
                            image_history.append(processed_image.copy())
                            if len(image_history) > self.max_history:
                                image_history.pop(0)
                            if stacked_image is None:
                                stacked_image = processed_image.copy()
                            else:
                                stacked_image = self._stack_images(stacked_image, processed_image, total_images_processed)
                        restack_done = True
                        logger.info("[Stacker] - Restacking images for sigma clipping reference done")

                    
                    if not restack_done:
                        # Apply winsorized sigma clipping
                        processed_image = self._winsorized_sigma_clip(
                            aligned_image, image_history
                        )
                    else:
                        # Apply simple outlier rejection
                        processed_image = self._simple_outlier_rejection(
                            aligned_image, stacked_image
                        )
                    
                    # Update history
                    image_history.append(processed_image.copy())
                    if len(image_history) > self.max_history:
                        image_history.pop(0)
                    
                    # Stack the image
                    stacked_image = self._stack_images(stacked_image, processed_image, total_images_processed)
                    total_images_processed += 1

                    self.output_queue.put((stacked_image.copy(), metadata))
                    logger.info(f"Image stacked ({total_images_processed} images total)")
                    
                    # Also save directly in the worker for debug
                    if total_images_processed <= 3:  # Save the first 3 for debug
                        logger.info(f"Debug - Min/Max in worker: {np.min(stacked_image):.6f}/{np.max(stacked_image):.6f}")
                    
                    metadata = {
                        'total_images': total_images_processed,
                        'last_image_path': image_path,
                        'shape': stacked_image.shape,
                        'clipped_pixels': np.sum(processed_image != aligned_image),
                        'image_type': 'color' if len(stacked_image.shape) == 3 else 'grayscale',
                        'channels': stacked_image.shape[2] if len(stacked_image.shape) == 3 else 1
                    }
                

                    
            except Exception as e:
                logger.error(f"Error in worker process: {e}")
                continue

    def set_callback(self, callback, path):
            """
            Assign a callback after starting the process.
            Useful to avoid pickle problems with object methods.
            """
            self.callback = callback
            self.path = path
            # Start callback thread if not done yet
            if self.is_running and self.callback_thread is None and callback is not None:
                self.callback_stop_event = threading.Event()
                self.callback_thread = threading.Thread(target=self._callback_handler)
                self.callback_thread.daemon = True
                self.callback_thread.start()
                self.logger.info("Callback thread started")


    def _load_fits_image(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[dict]]:
        """Load a FITS image."""
        try:
            fits_data = self.fits_manager.open_fits(image_path)
            
            # Assume the method returns an object with .data and .header
            if hasattr(fits_data, 'data') and hasattr(fits_data, 'header'):
                return fits_data.data.astype(np.float64), fits_data.header
            else:
                # If it's directly a numpy array
                return fits_data.astype(np.float64), {}
        except Exception as e:
            self.logger.error(f"Error loading {image_path}: {e}")
            return None, None
    
    def _align_image(self, image: np.ndarray, reference: np.ndarray) -> Optional[np.ndarray]:
        """Align an image to the reference using astroalign."""
        try:
            # For color images, use the luminance channel for alignment
            if len(image.shape) == 3 and len(reference.shape) == 3:
                # Convert to luminance (weighted average of RGB channels)
                image_gray = self._to_luminance(image)
                ref_gray = self._to_luminance(reference)
                
                # Calculate transformation on grayscale images
                aligned_gray, footprint = aa.register(image_gray, ref_gray)
                
                # For color images, we directly use aa.register on each channel
                # since aa.apply_transform can be complex depending on version
                aligned_image = np.zeros_like(image)
                for channel in range(image.shape[2]):
                    try:
                        aligned_channel, _ = aa.register(image[:, :, channel], reference[:, :, channel])
                        aligned_image[:, :, channel] = aligned_channel
                    except:
                        # Fallback: use alignment calculated on luminance
                        aligned_image[:, :, channel] = aligned_gray
                
                return aligned_image
            
            elif len(image.shape) == 2 and len(reference.shape) == 2:
                # Grayscale images
                aligned_image, footprint = aa.register(image, reference)
                return aligned_image
            
            else:
                raise ValueError("Image dimensions don't match")
                
        except Exception as e:
            self.logger.error(f"Alignment error: {e}")
            return None
    
    def _simple_outlier_rejection(self, new_image: np.ndarray, reference_image: np.ndarray, 
                            threshold_factor: float = 3.0) -> np.ndarray:
        """
        Rejette les pixels aberrants en comparant avec l'image de référence.
        
        Args:
            new_image: Nouvelle image à nettoyer
            reference_image: Image de référence
            threshold_factor: Facteur de seuil pour la détection d'outliers
            
        Returns:
            Image nettoyée
        """
        # Calcul de la différence absolue
        diff = np.abs(new_image.astype(np.float32) - reference_image.astype(np.float32))
        
        if len(new_image.shape) == 3:
            # Images couleur - traiter chaque canal
            cleaned_image = new_image.copy()
            
            for channel in range(new_image.shape[2]):
                # Seuil adaptatif basé sur les statistiques locales de la différence
                channel_diff = diff[:, :, channel]
                
                # Utiliser le percentile pour un seuil adaptatif
                threshold = np.percentile(channel_diff, 95) * threshold_factor
                
                # Alternative : seuil basé sur la médiane + MAD
                # median_diff = np.median(channel_diff)
                # mad_diff = np.median(np.abs(channel_diff - median_diff))
                # threshold = median_diff + threshold_factor * mad_diff * 1.4826
                
                outlier_mask = channel_diff > threshold
                
                # Remplacer les outliers par la valeur de référence
                cleaned_image[:, :, channel][outlier_mask] = reference_image[:, :, channel][outlier_mask]
                
                outlier_percent = np.sum(outlier_mask) / outlier_mask.size
                logger.info(f"[Stacker] - Channel {channel}: {outlier_percent:.1%} outliers rejected")
                
        else:
            # Images en niveaux de gris
            threshold = np.percentile(diff, 95) * threshold_factor
            outlier_mask = diff > threshold
            
            cleaned_image = new_image.copy()
            cleaned_image[outlier_mask] = reference_image[outlier_mask]
            
            outlier_percent = np.sum(outlier_mask) / outlier_mask.size
            logger.debug(f"[Stacker] - {outlier_percent:.1%} outliers rejected")
        
        return cleaned_image


    def _winsorized_sigma_clip(self, image: np.ndarray, history: List[np.ndarray]) -> np.ndarray:
        """
        Apply winsorized sigma clipping by comparing with image history.
        Compatible with both B&W and color images.
        
        Args:
            image: Image to process
            history: History of previous images
            
        Returns:
            Image with outlier pixels clipped
        """
        if len(history) < 3:  # Need at least 3 images for reliable clipping
            return image
        
        # Create a stack of images from history
        history_stack = np.stack(history, axis=0)
        
        if len(image.shape) == 3:
            # Color images - process each channel separately
            clipped_image = image.copy()
            
            for channel in range(image.shape[2]):
                # Extract channel for all images in history
                history_channel = history_stack[:, :, :, channel]
                
                # Use robust statistics
                median_channel = np.median(history_channel, axis=0)
                # MAD (Median Absolute Deviation) more robust than std
                mad_channel = np.median(np.abs(history_channel - median_channel), axis=0)
                # Convert MAD -> std equivalent (factor 1.4826 for normal distribution)
                robust_std = mad_channel * 1.4826
                
                # Avoid division by zero
                robust_std = np.maximum(robust_std, np.percentile(robust_std, 5))
                logger.info(f"[Stacker] - Channel {channel} robust std: {np.mean(robust_std):.6f}")
                # Identify outlier pixels for this channel
                deviation = np.abs(image[:, :, channel] - median_channel)
                outlier_mask = deviation > (self.sigma_threshold * robust_std)
                
                # Clip only if the percentage of outliers is reasonable (< 20%)
                outlier_percentage = np.sum(outlier_mask) / outlier_mask.size
                if outlier_percentage < 0.4:
                    logger.info(f"[Stacker] - Clipping percent {outlier_percentage}")
                    clipped_image[:, :, channel][outlier_mask] = median_channel[outlier_mask]
                else:
                    logger.info(f"[Stacker] - No clippign as Clipping percent too high : {outlier_percentage}")

                
        else:
            # Grayscale images
            median_image = np.median(history_stack, axis=0)
            # Use MAD instead of std for more robustness
            mad_image = np.median(np.abs(history_stack - median_image), axis=0)
            robust_std = mad_image * 1.4826
            
            # Avoid division by zero
            robust_std = np.maximum(robust_std, np.percentile(robust_std, 1))
            
            # Identify outlier pixels
            deviation = np.abs(image - median_image)
            outlier_mask = deviation > (self.sigma_threshold * robust_std)
            
            # Clip only if the percentage of outliers is reasonable
            outlier_percentage = np.sum(outlier_mask) / outlier_mask.size
            if outlier_percentage < 0.4:
                clipped_image = image.copy()
                clipped_image[outlier_mask] = median_image[outlier_mask]
            else:
                clipped_image = image.copy()  # No clipping if too many outliers
        """if outlier_percentage > 0.3:  # Si > 30%
            self.sigma_threshold *= 1.5  # Relâcher le seuil
            logger.info(f"[Stacker] - Adjusting sigma threshold: {self.sigma_threshold:.2f} (outlier percentage: {outlier_percentage:.2%})")
        elif outlier_percentage < 0.05:  # Si < 5%
            self.sigma_threshold *= 0.9  # Resserrer légèrement
            logger.info(f"[Stacker] - Adjusting sigma threshold: {self.sigma_threshold:.2f} (outlier percentage: {outlier_percentage:.2%})")"""
        self.sigma_history.append(outlier_percentage)
        if len(self.sigma_history) > self.max_history:
            self.sigma_history.pop(0)


        if len(self.sigma_history)>4:
            mean = sum(self.sigma_history)/len(self.sigma_history)
            if  mean > 0.3:
                self.sigma_threshold *= 1.2
                self.sigma_threshold = min(self.sigma_threshold, 5.0)  # Cap at 10
                self.logger.info(f"[Stacker] - Adjusting sigma threshold: {self.sigma_threshold:.2f} (mean outlier percentage: {mean:.2%})")

            elif mean < 0.05:
                self.sigma_threshold *= 0.9

        return clipped_image
    
    def _stack_images(self, stacked: np.ndarray, new_image: np.ndarray, count: int) -> np.ndarray:
        """
        Stack two images using a weighted average.
        
        Args:
            stacked: Current stacked image
            new_image: New image to add
            count: Number of images already stacked
            
        Returns:
            New stacked image
        """
        # Weighted average: (stacked * count + new_image) / (count + 1)
        return (stacked * count + new_image) / (count + 1)
    
    def _to_luminance(self, color_image: np.ndarray) -> np.ndarray:
        """
        Convert a color image to luminance for alignment.
        Uses standard ITU-R BT.709 coefficients.
        
        Args:
            color_image: Color image (H, W, C)
            
        Returns:
            Grayscale image (H, W)
        """
        if len(color_image.shape) != 3:
            raise ValueError("Image must be color (3 dimensions)")
        
        # ITU-R BT.709 luminance coefficients
        if color_image.shape[2] == 3:  # RGB
            weights = np.array([0.2126, 0.7152, 0.0722])
        elif color_image.shape[2] == 4:  # RGBA
            weights = np.array([0.2126, 0.7152, 0.0722, 0.0])
        else:
            # For other numbers of channels, use simple average
            weights = np.ones(color_image.shape[2]) / color_image.shape[2]
        
        return np.dot(color_image, weights)
    



fitsprocessor = FitsImageManager(auto_normalize=True)
index = 0

def my_callback(stacked_image, metadata):
    """Callback called for each new stacked image."""
    global index
    print(f"New stacked image! Total: {metadata['total_images']} images")
    print(f"Shape: {metadata['shape']}, Type: {metadata['image_type']}")
    FitsImageManager.save_fits_from_array(
        (stacked_image*65536).astype(np.int16), 
        f"stacked_image_{index:03d}.fits", 
        []
    )
    index += 1

# Usage example with callback
if __name__ == "__main__":
    # Create the stacker instance
    stacker = ImageStacker(sigma_threshold=3.0, max_history=5)
    

    # ✅ Assign callback AFTER creating the instance
    stacker.callback = my_callback

    from glob import glob
    from fitsprocessor import FitsImageManager
    from astrofilters import AstroFilters

    fits_files = sorted(glob("../../utils/01-observation-m16/01-images-initial/*.fits"))
    filters = AstroFilters()

    try:
        # Start the process
        stacker.start_live_stacking()
        
        print(f"Adding {len(fits_files)} images...")
        
        # Add all images
        for path in fits_files:
            stacker.process_new_image(path)
            
        print("All images added, waiting for processing...")
        
        # ✅ WAIT until all images are processed
        success = stacker.wait_for_completion(timeout=300)  # 5 minutes max
        
        if success:
            print("✅ All images have been processed successfully!")
        else:
            print("⚠️  Timeout - some images may not have been processed")
            processed, added = stacker.get_processing_status()
            print(f"Final status: {processed}/{added} images processed")
        
    finally:
        # Always stop the process
        stacker.stop()

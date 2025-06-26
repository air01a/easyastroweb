#!/usr/bin/env python3
"""
Live Astrophotography Stacking using PySiril
Hybrid approach: Siril for heavy processing, Python for orchestration
"""

import time
import threading
import queue
import logging
from pathlib import Path
from typing import Optional, List, Dict, Callable
import json
from datetime import datetime
import shutil

try:
    import pysiril
    from pysiril.wrapper import Wrapper
    from pysiril.siril import *
except ImportError:
    print("PySiril not found. Install with: pip install pysiril")
    exit(1)

# Configuration
class Config:
    def __init__(self):
        # Directories
        self.base_dir = Path(f"{Path.cwd()}/astro_session")
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "process"
        self.stack_result = self.base_dir / "processed"
        self.final_dir = self.base_dir / "final"
        self.log_dir = self.base_dir / "log"
        self.current_dir = Path.cwd()
        
        # Processing parameters
        self.batch_size = 5
        self.initial_batch_size = 10  # Smaller for first batch
        self.max_processed_batches = 40  # Keep last N batches for final stacking
        
        # File patterns
        self.image_extensions = ['.fit', '.fits', '.tif', '.tiff']
        
        # Siril settings
        self.siril_executable = "siril"  # Adjust path if needed
        
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories"""
        for dir_path in [self.raw_dir, self.processed_dir, self.final_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

class LiveStacker:
    def __init__(self, config: Config, on_image_processed: Optional[Callable[[Path], None]] = None,):
        self.config = config
        self.siril = None
        self.running = False
        self.on_image_processed = on_image_processed
        for path in [self.config.stack_result, self.config.raw_dir, self.config.processed_dir]:
            self.clear_directory(path)
        # Queues for inter-thread communication
        self.new_images_queue = queue.Queue()
        self.batch_ready_queue = queue.Queue()
        self.current_batch_files : List[Path] = []
        # Statistics
        self.stats = {
            'total_images': 0,
            'processed_batches': 0,
            'current_batch_count': 0,
            'session_start': datetime.now(),
            'last_batch_time': None
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_dir / 'stacking.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def initialize_siril(self) -> bool:
        """Initialize Siril connection"""
        try:
            self.app = Siril()
            self.siril = Wrapper(self.app)
            self.app.Open()
            

            self.logger.info("Siril initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Siril: {e}")
            return False
    
    
    def process_new_image(self, img_path: Path):
        """Process a new image from camera"""
        try:
            # Copy to raw directory
            raw_dest = self.config.raw_dir / img_path.name
            self.current_batch_files.append(raw_dest)
            shutil.copy2(f"{img_path}", f"{raw_dest}")
            

            self.stats['total_images'] += 1
            self.stats['current_batch_count'] += 1
            
            self.logger.info(f"New image: {img_path} (Total: {self.stats['total_images']})")
            
            # Check if batch is ready
            batch_size = self.config.initial_batch_size if self.stats['processed_batches'] == 0 else self.config.batch_size
            
            if self.stats['current_batch_count'] >= batch_size:
                self.batch_ready_queue.put(self.current_batch_files.copy())
                self.current_batch_files.clear()

                self.stats['current_batch_count'] = 0
                    
        except Exception as e:
            self.logger.error(f"Error processing new image {img_path}: {e}")
    
    
    
    def siril_batch_processor(self):
        """Process batches with Siril in separate thread"""
        while self.running:
            try:
                # Wait for batch to be ready
                if not self.batch_ready_queue.empty():
                    batch_images = self.batch_ready_queue.get(timeout=1)
                    if batch_images:
                        self.process_batch_with_siril(batch_images)
                    
                else:
                    time.sleep(1)
            
            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}")
    
    def process_batch_with_siril(self, batch_images: List[Path]):
        """Process a batch of images with Siril"""
        batch_id = f"batch_{self.stats['processed_batches']:03d}_{int(time.time())}"
        batch_dir = self.config.processed_dir / batch_id
        batch_dir.mkdir(exist_ok=True)
        
        try:
            self.logger.info(f"Processing batch {batch_id} with {len(batch_images)} images")

            result_path = self.stack_batch(batch_images, batch_dir)
            
            if result_path and result_path.exists():
                # Save batch metadata
                metadata = {
                    'batch_id': batch_id,
                    'image_count': len(batch_images),
                    'timestamp': datetime.now().isoformat(),
                    'result_path': str(result_path),
                    'source_images': [str(img) for img in batch_images]
                }
                
                with open(self.config.log_dir / f"{batch_id}.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.stats['processed_batches'] += 1
                self.stats['last_batch_time'] = datetime.now()
                
                self.logger.info(f"Batch {batch_id} completed successfully")
                self.stack_processed_batches()
            
        except Exception as e:
            self.logger.error(f"Error processing batch {batch_id}: {e}")
    
    def clear_directory(self, directory: Path):
        """Supprime le contenu avec gestion d'erreurs"""
        try:
            for item in directory.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)  # Plus efficace pour les dossiers
        except Exception as e:
            print(f"Erreur lors du nettoyage de {directory}: {e}")

    def stack_batch(self, batch_images: List[Path], output_dir: Path) -> Optional[Path]:
        """Stack a batch of images with Siril"""
        try:
            sequence_name = f"batch_{int(time.time())}"
            for file in batch_images:
                shutil.move(f"{file}",f"{output_dir}")
            # Prepare images
            self.siril.cd(f"{output_dir}")
            
            # Convert and register images
            self.siril.convert( 'light', out=f"{self.config.processed_dir}", debayer=True)
            self.siril.cd(f"{self.config.processed_dir}")
            self.siril.register('light')
            result_path = self.config.stack_result / f"{sequence_name}_stacked.fit"
            self.siril.stack('r_light', type='rej', sigma_low=3, sigma_high=3, norm='addscale', output_norm=True, out=f"{result_path}")
            # Stack with rejection

            self.clear_directory(self.config.processed_dir)
            return result_path if result_path.exists() else None
        
        except Exception as e:
            self.logger.error(f"Error stacking batch: {e}")
            return None
    

    
    def stack_processed_batches(self):
        """Stack the processed batch results"""
        try:
            # Find stacked results from each batch
            batch_results = []

            for result_file in self.config.stack_result.glob("*.fit"):
                batch_results.append(result_file)
            
            if len(batch_results) < 2:
                return
            
            self.logger.info(f"Stacking {len(batch_results)} processed batches")
            
            self.siril.cd(f"{self.config.stack_result}")
            
            # Convert and register images
            self.siril.convert( 'light', out=f"{self.config.processed_dir}", debayer=True)
            self.siril.cd(f"{self.config.processed_dir}")
            self.siril.register('light')
            result_path = f"{self.config.final_dir}/final{len(batch_results)}.fit"
            self.siril.stack('r_light', type='rej', sigma_low=3, sigma_high=3, norm='addscale', output_norm=True, out=f"{result_path}")
            # Stack with rejection
            if (self.on_image_processed):
                self.on_image_processed(result_path,)
            self.clear_directory(self.config.processed_dir)
            
            
            
        except Exception as e:
            self.logger.error(f"Error stacking processed batches: {e}")
    
    def get_status(self) -> Dict:
        """Get current status"""
        elapsed = datetime.now() - self.stats['session_start']
        
        return {
            'running': self.running,
            'total_images': self.stats['total_images'],
            'processed_batches': self.stats['processed_batches'],
            'current_batch_progress': self.stats['current_batch_count'],
            'session_duration': str(elapsed),
            'images_per_minute': self.stats['total_images'] / (elapsed.total_seconds() / 60) if elapsed.total_seconds() > 0 else 0,
            'last_batch_time': self.stats['last_batch_time'].isoformat() if self.stats['last_batch_time'] else None
        }
    
    def start_live_stacking(self, camera_dir: Path):
        """Start the live stacking process"""
        if not self.initialize_siril():
            return False
        
        self.running = True

        
        self.processor_thread = threading.Thread(
            target=self.siril_batch_processor,
            daemon=True
        )
        
        #monitor_thread.start()
        self.processor_thread.start()
        
        self.logger.info("Live stacking started")
        return True
    
    def stop_live_stacking(self):
        """Stop the live stacking process"""
        self.running = False
        
        # Final stack of remaining images
        if self.stats['current_batch_count'] > 0:
            remaining_images = self.current_batch_files
            if remaining_images:
                self.batch_ready_queue.put(remaining_images)
        
        # Close Siril
        if self.siril:
            self.siril.close()
        
       
        self.logger.info("Live stacking stopped")







def main():



    """Example usage"""

    from glob import glob
    from fitsprocessor import FitsImageManager
    from filters import AstroFilters

    fits_manager = FitsImageManager(auto_normalize=True)
    filters = AstroFilters()
    current_dir = f"{Path.cwd()}"
    
    def on_image_update(path : Path):
        print("===++++===++++ on image update")
        image = fits_manager.open_fits(f"{path}")
        image.data  = filters.denoise_gaussian(filters.replace_lowest_percent_by_zero(filters.auto_stretch(image.data, 0.15, algo=1, shadow_clip=-2),88))
        fits_manager.save_as_image(image, output_filename=f"{path}".replace(".fit",".jpg"))
        print("/===++++===++++ on image update")


    config = Config()
    stacker = LiveStacker(config, on_image_processed=on_image_update)
    # Replace with your camera output directory
    camera_dir = Path("../../utils/01-observation-m16/01-images-initial/")
    #fits_files = sorted(glob("../../utils/01-observation-m16/01-images-initial/*.fits"))  # Répertoire avec images FITS
    fits_dir = Path("C:/Users/eniquet/Documents/dev/easyastroweb/utils/01-observation-m16/01-images-initial")
    fits_files =  list(fits_dir.glob("*.fit")) + list(fits_dir.glob("*.fits"))
    print(fits_files)

    try:
        print("Starting live stacking...")
        print(f"Output: {config.final_dir}")
        
        if stacker.start_live_stacking(camera_dir):
            # Monitor status


            for file in fits_files:
                stacker.process_new_image(file)
                status = stacker.get_status()
                print(f"\rImages: {status['total_images']} | "
                      f"Batches: {status['processed_batches']} | "
                      f"Progress: {status['current_batch_progress']}/{config.batch_size}", 
                      end='', flush=True)
                
                time.sleep(2)
            stacker.stop_live_stacking()
        
    except KeyboardInterrupt:
        print("\nStopping...")
        stacker.stop_live_stacking()
        print("Stopped.")


if __name__ == "__main__":
    main()
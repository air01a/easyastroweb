import multiprocessing as mp
import queue
import numpy as np
from typing import List, Optional, Tuple
import astroalign as aa
from scipy import stats
import logging
from pathlib import Path
import threading

from imageprocessing.fitsprocessor import FitsImageManager

class ImageStacker:
    """
    Classe pour aligner et stacker des images FITS dans un processus séparé.
    Utilise astroalign pour l'alignement et un sigma clipping winsorisé pour le stacking.
    """
    
    def __init__(self, sigma_threshold: float = 3.0, max_history: int = 5):
        """
        Initialise le stacker d'images.
        
        Args:
            sigma_threshold: Seuil pour le sigma clipping
            max_history: Nombre d'images à garder en historique pour le sigma clipping
        """
        self.sigma_threshold = sigma_threshold
        self.max_history = max_history
        self.callback = None  # Sera assigné après création
        
        # Instancier FitsImageManager une seule fois
        self.fits_manager = FitsImageManager(auto_debayer=True, auto_normalize=True)
        
        # Queues pour communication inter-processus
        self.input_queue = mp.Queue()
        self.output_queue = mp.Queue()
        self.control_queue = mp.Queue()
        
        # Queue pour la synchronisation (remplace les locks non-picklable)
        self.sync_queue = mp.Queue()
        
        # Thread pour gérer les callbacks de manière non-bloquante
        self.callback_thread = None
        self.callback_stop_event = None
        
        # Process worker
        self.process = None
        self.is_running = False
        
        # Compteurs pour synchronisation (gérés via sync_queue)
        self.images_added = 0
        self.images_processed = 0
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Démarre le processus de stacking."""
        if self.is_running:
            self.logger.warning("Le processus est déjà en cours d'exécution")
            return
        
        self.process = mp.Process(target=self._worker_process)
        self.process.start()
        
        # Démarrer le thread de callback si un callback est fourni
        if self.callback is not None:
            self.callback_stop_event = threading.Event()
            self.callback_thread = threading.Thread(target=self._callback_handler)
            self.callback_thread.daemon = True
            self.callback_thread.start()
        
        self.is_running = True
        self.logger.info("Processus de stacking démarré")
    
    def stop(self):
        """Arrête le processus de stacking."""
        if not self.is_running:
            return
        
        # Arrêter le thread de callback
        if self.callback_thread is not None:
            self.callback_stop_event.set()
            self.callback_thread.join(timeout=5)
        
        self.control_queue.put("STOP")
        self.process.join(timeout=10)
        
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        
        self.is_running = False
        self.logger.info("Processus de stacking arrêté")
    
    def add_image(self, image_path: str):
        """
        Ajoute une image à stacker.
        
        Args:
            image_path: Chemin vers le fichier FITS
        """
        if not self.is_running:
            raise RuntimeError("Le processus n'est pas démarré. Appelez start() d'abord.")
        
        self.images_added += 1
        self.input_queue.put(image_path)
        self.logger.info(f"Image ajoutée à la queue: {image_path} (Total ajoutées: {self.images_added})")
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """
        Attend que toutes les images ajoutées soient traitées.
        
        Args:
            timeout: Timeout en secondes (None = pas de timeout)
            
        Returns:
            bool: True si toutes les images ont été traitées, False si timeout
        """
        import time
        start_time = time.time()
        
        # Vider la sync_queue au début
        while True:
            try:
                self.sync_queue.get_nowait()
            except queue.Empty:
                break
        
        while True:
            if self.images_processed >= self.images_added:
                self.logger.info(f"Toutes les images ont été traitées ({self.images_processed}/{self.images_added})")
                return True
            
            # Vérifier le timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self.logger.warning(f"Timeout atteint - {self.images_processed}/{self.images_added} images traitées")
                    return False
            
            # Attendre un signal de la sync_queue ou timeout
            try:
                self.sync_queue.get(timeout=0.5)
            except queue.Empty:
                continue
    
    def get_processing_status(self) -> Tuple[int, int]:
        """
        Retourne le statut du traitement.
        
        Returns:
            Tuple (images_traitées, images_ajoutées)
        """
        return self.images_processed, self.images_added
    
    def _callback_handler(self):
        """Thread qui gère les callbacks de manière non-bloquante."""
        while not self.callback_stop_event.is_set():
            try:
                result = self.output_queue.get(timeout=1.0)
                if result is not None:
                    stacked_image, metadata = result
                    
                    # Incrémenter le compteur d'images traitées
                    self.images_processed += 1
                    
                    # Signaler via sync_queue pour wait_for_completion
                    try:
                        self.sync_queue.put_nowait("PROCESSED")
                    except:
                        pass  # Queue pleine, pas grave
                    
                    try:
                        # Appeler le callback dans un try/catch pour éviter de crasher
                        self.callback(stacked_image, metadata)
                    except Exception as e:
                        self.logger.error(f"Erreur dans le callback: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erreur dans le callback handler: {e}")
                break
    
    def _worker_process(self):
        """Processus worker qui effectue l'alignement et le stacking."""
        stacked_image = None
        image_history = []  # Historique des dernières images pour sigma clipping
        reference_image = None
        total_images_processed = 0
        
        logger = logging.getLogger(f"{__name__}.worker")
        logger.info("Worker process démarré")
        
        while True:
            try:
                # Vérifier les commandes de contrôle
                try:
                    control_msg = self.control_queue.get_nowait()
                    if control_msg == "STOP":
                        logger.info("Arrêt du worker process")
                        break
                except queue.Empty:
                    pass
                
                # Traiter les nouvelles images
                try:
                    image_path = self.input_queue.get(timeout=1.0)
                    logger.info(f"Traitement de l'image: {image_path}")
                    
                    # Charger l'image
                    image_data, header = self._load_fits_image(image_path)
                    if image_data is None:
                        continue
                    
                    if reference_image is None:
                        # Première image = référence
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
                        logger.info("Image de référence définie et envoyée")
                        
                    else:
                        # Aligner l'image sur la référence
                        aligned_image = self._align_image(image_data, reference_image)
                        if aligned_image is None:
                            logger.warning(f"Impossible d'aligner l'image: {image_path}")
                            continue
                        
                        # Appliquer le sigma clipping winsorisé
                        processed_image = self._winsorized_sigma_clip(
                            aligned_image, image_history
                        )
                        
                        # Mettre à jour l'historique
                        image_history.append(processed_image.copy())
                        if len(image_history) > self.max_history:
                            image_history.pop(0)
                        
                        # Stacker l'image
                        stacked_image = self._stack_images(stacked_image, processed_image, total_images_processed)
                        total_images_processed += 1

                        self.output_queue.put((stacked_image.copy(), metadata))
                        logger.info(f"Image stackée ({total_images_processed} images au total)")
                        
                        # Également sauvegarder directement dans le worker pour debug
                        if total_images_processed <= 3:  # Sauver les 3 premières pour debug
                            logger.info(f"Debug - Min/Max dans worker: {np.min(stacked_image):.6f}/{np.max(stacked_image):.6f}")
                        
                        metadata = {
                            'total_images': total_images_processed,
                            'last_image_path': image_path,
                            'shape': stacked_image.shape,
                            'clipped_pixels': np.sum(processed_image != aligned_image),
                            'image_type': 'color' if len(stacked_image.shape) == 3 else 'grayscale',
                            'channels': stacked_image.shape[2] if len(stacked_image.shape) == 3 else 1
                        }
                
                except queue.Empty:
                    continue
                    
            except Exception as e:
                logger.error(f"Erreur dans le worker process: {e}")
                continue
    
    def _load_fits_image(self, image_path: str) -> Tuple[Optional[np.ndarray], Optional[dict]]:
        """Charge une image FITS."""
        try:
            fits_data = self.fits_manager.open_fits(image_path)
            
            # Supposons que la méthode retourne un objet avec .data et .header
            if hasattr(fits_data, 'data') and hasattr(fits_data, 'header'):
                return fits_data.data.astype(np.float64), fits_data.header
            else:
                # Si c'est directement un array numpy
                return fits_data.astype(np.float64), {}
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de {image_path}: {e}")
            return None, None
    
    def _align_image(self, image: np.ndarray, reference: np.ndarray) -> Optional[np.ndarray]:
        """Aligne une image sur la référence avec astroalign."""
        try:
            # Pour les images couleurs, utiliser le canal de luminance pour l'alignement
            if len(image.shape) == 3 and len(reference.shape) == 3:
                # Convertir en luminance (moyenne pondérée des canaux RGB)
                image_gray = self._to_luminance(image)
                ref_gray = self._to_luminance(reference)
                
                # Calculer la transformation sur les images en niveaux de gris
                aligned_gray, footprint = aa.register(image_gray, ref_gray)
                
                # Pour les images couleurs, on utilise directement aa.register sur chaque canal
                # car aa.apply_transform peut être complexe selon la version
                aligned_image = np.zeros_like(image)
                for channel in range(image.shape[2]):
                    try:
                        aligned_channel, _ = aa.register(image[:, :, channel], reference[:, :, channel])
                        aligned_image[:, :, channel] = aligned_channel
                    except:
                        # Fallback: utiliser l'alignement calculé sur la luminance
                        aligned_image[:, :, channel] = aligned_gray
                
                return aligned_image
            
            elif len(image.shape) == 2 and len(reference.shape) == 2:
                # Images en niveaux de gris
                aligned_image, footprint = aa.register(image, reference)
                return aligned_image
            
            else:
                raise ValueError("Les dimensions des images ne correspondent pas")
                
        except Exception as e:
            self.logger.error(f"Erreur d'alignement: {e}")
            return None
    
    def _winsorized_sigma_clip(self, image: np.ndarray, history: List[np.ndarray]) -> np.ndarray:
        """
        Applique un sigma clipping winsorisé en comparant avec l'historique des images.
        Compatible avec les images N&B et couleurs.
        
        Args:
            image: Image à traiter
            history: Historique des images précédentes
            
        Returns:
            Image avec pixels déviants clippés
        """
        if len(history) < 3:  # Besoin d'au moins 3 images pour un clipping fiable
            return image
        
        # Créer un stack des images de l'historique
        history_stack = np.stack(history, axis=0)
        
        if len(image.shape) == 3:
            # Images couleurs - traiter chaque canal séparément
            clipped_image = image.copy()
            
            for channel in range(image.shape[2]):
                # Extraire le canal pour toutes les images de l'historique
                history_channel = history_stack[:, :, :, channel]
                
                # Utiliser des statistiques robustes
                median_channel = np.median(history_channel, axis=0)
                # MAD (Median Absolute Deviation) plus robuste que std
                mad_channel = np.median(np.abs(history_channel - median_channel), axis=0)
                # Conversion MAD -> équivalent std (facteur 1.4826 pour distribution normale)
                robust_std = mad_channel * 1.4826
                
                # Éviter division par zéro
                robust_std = np.maximum(robust_std, np.percentile(robust_std, 1))
                
                # Identifier les pixels déviants pour ce canal
                deviation = np.abs(image[:, :, channel] - median_channel)
                outlier_mask = deviation > (self.sigma_threshold * robust_std)
                
                # Clipper seulement si le pourcentage d'outliers est raisonnable (< 20%)
                outlier_percentage = np.sum(outlier_mask) / outlier_mask.size
                if outlier_percentage < 0.2:
                    clipped_image[:, :, channel][outlier_mask] = median_channel[outlier_mask]
                
        else:
            # Images en niveaux de gris
            median_image = np.median(history_stack, axis=0)
            # Utiliser MAD au lieu de std pour plus de robustesse
            mad_image = np.median(np.abs(history_stack - median_image), axis=0)
            robust_std = mad_image * 1.4826
            
            # Éviter division par zéro
            robust_std = np.maximum(robust_std, np.percentile(robust_std, 1))
            
            # Identifier les pixels déviants
            deviation = np.abs(image - median_image)
            outlier_mask = deviation > (self.sigma_threshold * robust_std)
            
            # Clipper seulement si le pourcentage d'outliers est raisonnable
            outlier_percentage = np.sum(outlier_mask) / outlier_mask.size
            if outlier_percentage < 0.2:
                clipped_image = image.copy()
                clipped_image[outlier_mask] = median_image[outlier_mask]
            else:
                clipped_image = image.copy()  # Pas de clipping si trop d'outliers
        
        return clipped_image
    
    def _stack_images(self, stacked: np.ndarray, new_image: np.ndarray, count: int) -> np.ndarray:
        """
        Stack deux images en utilisant une moyenne pondérée.
        
        Args:
            stacked: Image stackée actuelle
            new_image: Nouvelle image à ajouter
            count: Nombre d'images déjà stackées
            
        Returns:
            Nouvelle image stackée
        """
        # Moyenne pondérée: (stacked * count + new_image) / (count + 1)
        return (stacked * count + new_image) / (count + 1)
    
    def _to_luminance(self, color_image: np.ndarray) -> np.ndarray:
        """
        Convertit une image couleur en luminance pour l'alignement.
        Utilise les coefficients standards ITU-R BT.709.
        
        Args:
            color_image: Image couleur (H, W, C)
            
        Returns:
            Image en niveaux de gris (H, W)
        """
        if len(color_image.shape) != 3:
            raise ValueError("L'image doit être en couleur (3 dimensions)")
        
        # Coefficients de luminance ITU-R BT.709
        if color_image.shape[2] == 3:  # RGB
            weights = np.array([0.2126, 0.7152, 0.0722])
        elif color_image.shape[2] == 4:  # RGBA
            weights = np.array([0.2126, 0.7152, 0.0722, 0.0])
        else:
            # Pour d'autres nombres de canaux, utiliser une moyenne simple
            weights = np.ones(color_image.shape[2]) / color_image.shape[2]
        
        return np.dot(color_image, weights)
    



fitsprocessor = FitsImageManager(auto_normalize=True)
index = 0

def my_callback(stacked_image, metadata):
    """Callback appelé à chaque nouvelle image stackée."""
    global index
    print(f"Nouvelle image stackée ! Total: {metadata['total_images']} images")
    print(f"Forme: {metadata['shape']}, Type: {metadata['image_type']}")
    FitsImageManager.save_fits_from_array(
        (stacked_image*65536).astype(np.int16), 
        f"stacked_image_{index:03d}.fits", 
        []
    )
    index += 1

# Exemple d'utilisation avec callback
if __name__ == "__main__":
    # Créer l'instance du stacker
    stacker = ImageStacker(sigma_threshold=3.0, max_history=5)
    

    # ✅ Assigner le callback APRÈS création de l'instance
    stacker.callback = my_callback

    from glob import glob
    from fitsprocessor import FitsImageManager
    from astrofilters import AstroFilters

    fits_files = sorted(glob("../../utils/01-observation-m16/01-images-initial/*.fits"))
    filters = AstroFilters()

    try:
        # Démarrer le processus
        stacker.start()
        
        print(f"Ajout de {len(fits_files)} images...")
        
        # Ajouter toutes les images
        for path in fits_files:
            stacker.add_image(path)
            
        print("Toutes les images ajoutées, attente du traitement...")
        
        # ✅ ATTENDRE que toutes les images soient traitées
        success = stacker.wait_for_completion(timeout=300)  # 5 minutes max
        
        if success:
            print("✅ Toutes les images ont été traitées avec succès !")
        else:
            print("⚠️  Timeout - certaines images n'ont peut-être pas été traitées")
            processed, added = stacker.get_processing_status()
            print(f"Status final: {processed}/{added} images traitées")
        
    finally:
        # Toujours arrêter le processus
        print("Arrêt du processus...")
        stacker.stop()
        print("Terminé !")
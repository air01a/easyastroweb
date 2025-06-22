import numpy as np
from collections import deque
from astropy.io import fits
from astropy.stats import sigma_clip
import astroalign as aa
import cv2
import time

class LiveStacker:
    def __init__(self, max_images=20, mode="sigma", clip_extremes=False, extreme_min=5, extreme_max=65500, epsilon=1e-6, clip_threshold=0.2):
        self.max_images = max_images
        self.mode = mode
        self.clip_extremes = clip_extremes
        self.extreme_min = extreme_min
        self.extreme_max = extreme_max

        self.image_queue = deque(maxlen=max_images) if mode == "sigma" or "hybrid" else None
        self.quality_weights = deque(maxlen=max_images) if mode == "sigma" or "hybrid" else None
        self.stack = None
        self.weight_sum = 0
        self.reference_image = None
        self.stacked_images = 0
        self.epsilon = epsilon
        self.clip_threshold = clip_threshold



    def mask_extremes(self, image):
        if image.ndim == 2:
            mask = (image >= self.extreme_min) & (image <= self.extreme_max)
        elif image.ndim == 3 and image.shape[2] == 3:
            mask = (image >= self.extreme_min) & (image <= self.extreme_max)
            mask = np.all(mask, axis=-1)  # Mask 2D commun pour tous les canaux
        else:
            raise ValueError("Image dimensions not supported.")

        if image.ndim == 2:
            return np.where(mask, image, np.nan)
        else:
            # Applique le même masque sur chaque canal
            masked = np.zeros_like(image, dtype=np.float32)
            for c in range(3):
                masked[..., c] = np.where(mask, image[..., c], np.nan)
            return masked

    def compute_noise_level(self, image):
        clipped = sigma_clip(image, sigma=3)
        return np.std(clipped)

    def reduce_image(self, image, scale=0.25):
        """Reduit la taille de l'image pour alignement rapide."""
        height, width = image.shape
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    def align_image(self, image):
        if self.reference_image is None:
            self.reference_image = image
            return image
        try:
            reduced_ref = self.reduce_image(self.reference_image)
            reduced_img = self.reduce_image(image)
            matrix, _ = aa.find_transform(reduced_img, reduced_ref)
            aligned = aa.apply_transform(matrix, image, self.reference_image)
            return aligned
        except Exception as e:
            print(f"Erreur d'alignement : {e}")
            return None

    def add_frame(self, image):
        image = image.astype(np.float32)
        start_total = time.perf_counter()

        t0 = time.perf_counter()

        if image.ndim == 3 and image.shape[2] == 3:
            gray_for_align = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray_for_align = image
        print(f"[Timer] Conversion grayscale : {time.perf_counter() - t0:.3f} sec")
        
        t0 = time.perf_counter()

        aligned_gray = self.align_image(gray_for_align)
        if aligned_gray is None:
            return self.stack

        if image.ndim == 3 and image.shape[2] == 3:
            aligned_rgb, _ = aa.register(image, self.reference_image)
            aligned = aligned_rgb
        else:
            aligned = aligned_gray
        print(f"[Timer] Alignement : {time.perf_counter() - t0:.3f} sec")
        t0 = time.perf_counter()

        noise = self.compute_noise_level(aligned_gray)
        weight = 1.0 / (noise ** 2 + 1e-8)
        weight=1.0


        print(f"[Timer] Calcul bruit : {time.perf_counter() - t0:.3f} sec")
        t0 = time.perf_counter()
        if self.mode == "sigma" or (self.mode=="hybrid" and self.stacked_images<self.max_images):
            print("+++++++++++ Sigma clipping use")
            self.image_queue.append(aligned)
            self.quality_weights.append(weight)

            stack_array = np.array(self.image_queue)
            weights_array = np.array(self.quality_weights)

            if aligned.ndim == 2:
                clipped = sigma_clip(stack_array, sigma=2.5, axis=0)
                mean = np.ma.average(clipped, axis=0, weights=weights_array)
                self.stack = mean.filled(0)
            else:
                clipped_r = sigma_clip(stack_array[:, :, :, 0], sigma=2.5, axis=0)
                clipped_g = sigma_clip(stack_array[:, :, :, 1], sigma=2.5, axis=0)
                clipped_b = sigma_clip(stack_array[:, :, :, 2], sigma=2.5, axis=0)

                mean_r = np.ma.average(clipped_r, axis=0, weights=weights_array)
                mean_g = np.ma.average(clipped_g, axis=0, weights=weights_array)
                mean_b = np.ma.average(clipped_b, axis=0, weights=weights_array)

                self.stack = np.stack([
                    mean_r.filled(0),
                    mean_g.filled(0),
                    mean_b.filled(0)
                ], axis=-1)

        elif self.mode == "average" or self.stack is None:
            print("+++++++++++ average use")

            image_to_add = aligned
            if self.clip_extremes:
                image_to_add = self.mask_extremes(image_to_add)

            if self.stack is None:
                self.stack = np.nan_to_num(image_to_add)
                self.weight_sum = weight
            else:
                self.stack = np.nan_to_num((self.stack * self.weight_sum + np.nan_to_num(image_to_add) * weight) / (self.weight_sum + weight))
                self.weight_sum += weight
        elif self.mode == "hybrid":
            print("+++++++++++ Hybrid use after sigma")

            relative_diff = np.abs(aligned - self.stack) / (self.stack + self.epsilon)
            mask = relative_diff < self.clip_threshold
            print("Valeur true : ", mask.sum(), "Valeur false", (~mask).sum())

            # Étape 1 : calculer la moyenne locale
            from scipy.ndimage import uniform_filter

            def local_mean(image, size=3):
                if image.ndim == 2:
                    return uniform_filter(image, size=size, mode='reflect')
                else:
                    return np.stack([uniform_filter(image[:, :, i], size=size, mode='reflect') for i in range(3)], axis=-1)

            local_avg = local_mean(aligned, size=3)

            # Étape 2 : pixels à utiliser
            blended_input = np.where(mask, aligned, local_avg)

            # Étape 3 : update stack
            alpha = weight / (self.weight_sum + weight)
            self.stack = (1 - alpha) * self.stack + alpha * blended_input
            self.weight_sum += weight

            #self.stack = (self.stack * self.weight_sum + blended_input * weight) / (self.weight_sum + weight)
            #self.weight_sum += weight


        self.stacked_images+=1
        print(f"###################################################################")
        print(f"[Timer] Sigma clipping / moyenne : {time.perf_counter() - t0:.3f} sec")
        print(f"[Timer] Total add_frame : {time.perf_counter() - start_total:.3f} sec")

        return self.stack


def load_fits_image(path):
    with fits.open(path) as hdul:
        return hdul[0].data.astype(np.float32)

# Exemple d'utilisation
if __name__ == "__main__":
    from glob import glob
    from fitsprocessor import FitsImageManager
    from filters import AstroFilters


    fits_files = sorted(glob("../../utils/01-observation-m16/01-images-initial/*.fits"))  # Répertoire avec images FITS
    stacker = LiveStacker(max_images=10, mode="hybrid",clip_extremes=True, extreme_min=10, extreme_max=64000, clip_threshold=0.2)
    fits = FitsImageManager(auto_normalize=True)
    filters = AstroFilters()
    index=0
    for path in fits_files:
        print(f"Empile {path}")
        image = fits.open_fits(path)
        img = image.data
        result = stacker.add_frame(img)
        if index % 30==0:
            fits.save_as_image(image, f"test1baverage{index}.tif")
            image.data = filters.auto_stretch(result, 0.2, algo=1, shadow_clip=-2)
            fits.save_as_image(image, f"test1baverage{index}.jpg")

        index+=1
    fits.processed_data=result
    fits.save_as_image("test1baverage.jpg")
    fits.save_fits("test1baverage.fits")



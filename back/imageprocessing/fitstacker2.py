import numpy as np
import astroalign as aa
from scipy.ndimage import generic_filter
import cv2

class LiveStacker:
    def __init__(self, shape, color=False, sigma_clip=3.0):
        self.color = color
        self.sigma_clip = sigma_clip
        self.shape = shape  # (H, W) ou (H, W, 3)

        if self.color:
            self.count = np.zeros((*shape[:2], 3), dtype=np.uint16)
            self.mean = np.zeros((*shape[:2], 3), dtype=np.float32)
            self.M2 = np.zeros((*shape[:2], 3), dtype=np.float32)
            self.stack = np.zeros((*shape[:2], 3), dtype=np.float32)
        else:
            self.count = np.zeros(shape[:2], dtype=np.uint16)
            self.mean = np.zeros(shape[:2], dtype=np.float32)
            self.M2 = np.zeros(shape[:2], dtype=np.float32)
            self.stack = np.zeros(shape[:2], dtype=np.float32)

        self.reference_image = None  # Pour alignement avec astroalign

    def align_frame(self, image):
        """
        Aligne une image (grayscale ou RGB) sur la référence.
        """
        if self.reference_image is None:
            self.reference_image = image.copy()
            return image

        try:
            aligned_image, _ = aa.register(image, self.reference_image)
            return aligned_image
        except Exception as e:
            print(f"[Erreur alignement] {e}")
            return None

    def _spatial_replace(self, channel, valid_mask):
        def replace_func(values):
            center = values[4]
            neighbors = np.delete(values, 4)
            valids = neighbors[neighbors >= 0]
            return np.mean(valids) if len(valids) >= 3 else center

        safe = np.where(valid_mask, channel, -1)
        repaired = generic_filter(safe, replace_func, size=3, mode='mirror')
        return repaired

    def _process_channel(self, chan_idx, frame_chan, mean, M2, count, stack):
        mask = count > 0
        delta = frame_chan - mean
        std = np.sqrt(M2 / np.maximum(count, 1))
        clip_mask = (np.abs(delta) <= self.sigma_clip * std)
        valid = (~mask) | clip_mask

        # Update Welford
        count[valid] += 1
        delta_valid = frame_chan[valid] - mean[valid]
        mean[valid] += delta_valid / count[valid]
        M2[valid] += delta_valid * (frame_chan[valid] - mean[valid])
        stack[valid] += frame_chan[valid]

        # Rejet spatial
        invalid = ~valid
        if np.any(invalid):
            repaired = self._spatial_replace(frame_chan, valid)
            count[invalid] += 1
            delta_valid = repaired[invalid] - mean[invalid]
            mean[invalid] += delta_valid / count[invalid]
            M2[invalid] += delta_valid * (repaired[invalid] - mean[invalid])
            stack[invalid] += repaired[invalid]

    def add_frame(self, frame):
        """
        Ajoute une frame au stacking (frame = HxW ou HxWx3, float32 ou équivalent)
        """
        aligned = self.align_frame(frame)
        if aligned is None:
            return self.get_current_stack()

        if self.color:
            for c in range(3):
                self._process_channel(
                    c,
                    aligned[..., c],
                    self.mean[..., c],
                    self.M2[..., c],
                    self.count[..., c],
                    self.stack[..., c]
                )
        else:
            self._process_channel(
                0,
                aligned,
                self.mean,
                self.M2,
                self.count,
                self.stack
            )

        return self.get_current_stack()

    def get_current_stack(self):
        if self.color:
            valid = self.count > 0
            result = np.zeros_like(self.stack)
            result[valid] = self.stack[valid] / self.count[valid]
            return np.clip(result, 0, 255).astype(np.uint8)
        else:
            valid = self.count > 0
            result = np.zeros_like(self.stack)
            result[valid] = self.stack[valid] / self.count[valid]
            return np.clip(result, 0, 65535).astype(np.uint16)



# Exemple d'utilisation
if __name__ == "__main__":
    from glob import glob
    from fitsprocessor import FitsImageManager
    from filters import AstroFilters


    fits_files = sorted(glob("../../utils/01-observation-m16/01-images-initial/*.fits"))  # Répertoire avec images FITS
    stacker = LiveStacker(shape=(1096, 1936, 3), color=True)
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

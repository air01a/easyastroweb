import numpy as np
from astropy.io import fits
from astropy.time import Time
import os
from typing import Optional, Tuple,  Dict, Any
import warnings
from PIL import Image
import tifffile as tiff
from pathlib import Path

try:
    from colour_demosaicing import demosaicing_CFA_Bayer_bilinear, demosaicing_CFA_Bayer_Malvar2004
    DEBAYER_AVAILABLE = True
except ImportError:
    DEBAYER_AVAILABLE = False
    warnings.warn("colour_demosaicing non disponible. Le debayering ne sera pas possible.")


class FitsImage:
    def __init__(self, 
                data: np.ndarray, 
                header: fits.Header, 
                is_color: bool, 
                bayer_pattern: Optional[str], 
                filename: Optional[str] = None, 
                is_debayered: Optional[bool]=False, 
                is_normalized: Optional[bool]=False, 
                has_dark: Optional[bool]=False, 
                is_inversed: Optional[bool]=False,
                ):
        

        self.data = data
        self.header = header
        self.filename = filename
        self.bayer_pattern = bayer_pattern
        self.is_color = is_color
        self.is_debayered = is_debayered
        self.is_normalized = is_normalized
        self.is_inversed = is_inversed
        self.has_dark = has_dark    



    def copy(self) -> 'FitsImage':
        return FitsImage(self.data.copy(), self.header.copy(), self.filename)

    def get_info(self) -> Dict[str, Any]:
        if self.data is None:
            return {"status": "Aucune image chargée"}
        
        return {
            "filename": self.filename,
            "shape": self.data.shape,
            "dtype": str(self.data.dtype),
            "bayer_pattern": self.bayer_pattern,
            "is_color": self.is_color,
            "is_debayered": self.is_debayered,
            "data_range": (self.data.min(), self.data.max())
        }

class FitsImageManager:

    
    # Patterns Bayer supportés
    BAYER_PATTERNS = {
        'RGGB': 'RGGB',
        'BGGR': 'BGGR', 
        'GRBG': 'GRBG',
        'GBRG': 'GBRG'
    }
    
    def __init__(self, auto_debayer: Optional[bool]=True, auto_normalize: Optional[bool]=False):
        self.auto_normalize = auto_normalize
        self.auto_debayer = auto_debayer
        self.dark = None
        
    def set_dark(self, dark: np.ndarray):
        self.dark = dark
 
    def open_fits(self, filename: str, hdu_index: int = 0) -> FitsImage:
        """
        Ouvre un fichier FITS et charge les données.
        
        Args:
            filename: Chemin vers le fichier FITS
            hdu_index: Index de l'HDU à charger (défaut: 0)
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Fichier non trouvé: {filename}")
        is_debayerd = False
        inversed=False
        dark_applied = False

        with fits.open(filename) as hdul:
            # Vérifier que l'HDU existe
            if hdu_index >= len(hdul):
                raise IndexError(f"HDU index {hdu_index} non valide. Le fichier a {len(hdul)} HDU(s)")
            
            hdu = hdul[hdu_index]
            original_data = hdu.data.copy()
            header = hdu.header.copy()
            original_shape = original_data.shape

        if self.dark and self.dark.shape == original_shape:
            original_data -= self.dark
            dark_applied=True
            print("dark applied")

        if len(original_shape)==3:
            is_color=True
            bayer_pattern=""
            if original_shape[0]==3:
                original_data = np.moveaxis(original_data, 0, -1)
                inversed = True
        else:
        # Détecter le pattern Bayer
            (is_color, bayer_pattern)=self._detect_bayer_pattern(header, original_shape)
            if (is_color and self.auto_debayer and bayer_pattern!=None):
                original_data = self.debayer(original_data, bayer_pattern)
                is_debayerd=True

        
        print(f"Fichier ouvert: {filename}")
        print(f"Dimensions: {original_shape}")
        print(f"Type de données: {original_data.dtype}")
        if bayer_pattern:
            print(f"Pattern Bayer détecté: {bayer_pattern}")
        else:
            print("Aucun pattern Bayer détecté (image couleur ou monochrome)")

        if self.auto_normalize:
            return FitsImage(self.normalize(original_data), header = header, is_color=is_color, bayer_pattern=bayer_pattern, filename = filename, is_debayered=is_debayerd, is_normalized=True, has_dark=dark_applied, is_inversed=inversed)
        else:
            return FitsImage(original_data, header = header, is_color=is_color, bayer_pattern=bayer_pattern, filename = filename, is_debayered=is_debayerd, is_normalized=False, has_dark=dark_applied, is_inversed=inversed)
    
    def normalize(self, image: np.ndarray, clip: bool = True) -> np.ndarray:
        """
        Normalise une image dans l'intervalle [0, 1].

        Args:
            image: tableau numpy (2D ou 3D)
            clip: si True, force le résultat à rester dans [0, 1] après normalisation

        Returns:
            Image normalisée (float32)
        """
        image = image.astype(np.float32)

        # Cas entiers : on divise par le max possible selon le type
        if np.issubdtype(image.dtype, np.integer):
            max_val = np.iinfo(image.dtype).max
            norm = image / max_val
        else:
            # Cas float : normaliser par les valeurs min/max réelles
            min_val = np.min(image)
            max_val = np.max(image)
            if max_val - min_val > 0:
                norm = (image - min_val) / (max_val - min_val)
            else:
                norm = np.zeros_like(image)

        return np.clip(norm, 0, 1) if clip else norm
    
    def _detect_bayer_pattern(self, header, original_shape) -> None:
        """Détecte le pattern Bayer à partir des métadonnées du header."""
        bayer_pattern = None
        is_color = False

        if len(original_shape)>2 : 
            return (True, None)
        
        # Rechercher dans différents champs possibles
        bayer_keys = ['BAYERPAT', 'COLORTYP', 'XBAYROFF', 'YBAYROFF']
        
        # Méthode 1: Pattern Bayer explicite
        if 'BAYERPAT' in header:
            pattern = header['BAYERPAT'].upper()
            if pattern in self.BAYER_PATTERNS:
                bayer_pattern = pattern
                return (True, bayer_pattern)
        
        # Méthode 2: Offsets Bayer (XBAYROFF, YBAYROFF)
        if 'XBAYROFF' in header and 'YBAYROFF' in header:
            x_offset = header['XBAYROFF']
            y_offset = header['YBAYROFF']
            
            # Déduire le pattern à partir des offsets
            if x_offset == 0 and y_offset == 0:
                bayer_pattern = 'RGGB'
            elif x_offset == 1 and y_offset == 0:
                bayer_pattern = 'GRBG'
            elif x_offset == 0 and y_offset == 1:
                bayer_pattern = 'GBRG'
            elif x_offset == 1 and y_offset == 1:
                bayer_pattern = 'BGGR'
        
        # Méthode 3: Détection basée sur la géométrie
        if bayer_pattern is None and len(original_shape) == 2:
            # Si c'est une image 2D, c'est probablement une image Bayer
            # Pattern par défaut (peut être modifié manuellement)
            bayer_pattern = 'RGGB'
        
        # Vérifier si c'est déjà une image couleur
        if len(original_shape) == 3 and original_shape[2] == 3:
            is_color = True
            bayer_pattern = None

        return (is_color, bayer_pattern)
    
    def set_bayer_pattern(self, pattern: str) -> None:
        """
        Définit manuellement le pattern Bayer.
        
        Args:
            pattern: Pattern Bayer ('RGGB', 'BGGR', 'GRBG', 'GBRG')
        """
        pattern = pattern.upper()
        if pattern not in self.BAYER_PATTERNS:
            raise ValueError(f"Pattern non supporté: {pattern}. Utilisez: {list(self.BAYER_PATTERNS.keys())}")
        
        self.bayer_pattern = pattern
        print(f"Pattern Bayer défini: {pattern}")
    
    def debayer(self, data, bayer_pattern, algorithm: str = 'bilinear') -> np.ndarray:
        """
        Effectue le debayering de l'image.
        
        Args:
            algorithm: Algorithme de debayering ('bilinear' ou 'malvar')
            
        Returns:
            Image debayerisée (H, W, 3)
        """
        if not DEBAYER_AVAILABLE:
            raise ImportError("Le module colour_demosaicing n'est pas installé")
        
        if bayer_pattern is None:
            raise ValueError("Aucun pattern Bayer défini. Utilisez set_bayer_pattern() ou vérifiez que l'image est bien une image Bayer")

        # Normaliser les données pour le debayering (0-1)
        data_normalized = data.astype(np.float64)
        data_min, data_max = data_normalized.min(), data_normalized.max()
        if data_max > data_min:
            data_normalized = (data_normalized - data_min) / (data_max - data_min)
        
        # Effectuer le debayering
        if algorithm == 'bilinear':
            debayered = demosaicing_CFA_Bayer_bilinear(data_normalized, bayer_pattern)
        elif algorithm == 'malvar':
            debayered = demosaicing_CFA_Bayer_Malvar2004(data_normalized, bayer_pattern)
        else:
            raise ValueError("Algorithme non supporté. Utilisez 'bilinear' ou 'malvar'")
        
        # Remettre à l'échelle originale
        debayered = debayered * (data_max - data_min) + data_min
        debayered = debayered.astype(data.dtype)
        

        
        print(f"Debayering effectué avec l'algorithme: {algorithm}")
        print(f"Nouvelles dimensions: {debayered.shape}")
        
        return debayered
    
    
    
    def save_fits(self, image : FitsImage, output_filename: str, preserve_original_format: bool = True) -> None:
        """
        Sauvegarde l'image traitée au format FITS.
        
        Args:
            output_filename: Nom du fichier de sortie
            preserve_original_format: Si True, convertit l'image couleur en Bayer si l'original était Bayer
        """
        if image.data is None:
            raise ValueError("Aucune donnée à sauvegarder")
        
            

        # Préparer les données à sauvegarder
        data_to_save = image.data.copy()
        header_to_save = image.header.copy()
        if image.is_normalized:
            data_to_save = (data_to_save* 65535).astype(np.uint16)
        if image.is_inversed: 
            data_to_save =  np.moveaxis(data_to_save, -1, 0)

        # Si on veut préserver le format original et que l'image était Bayer
        if preserve_original_format and image.bayer_pattern and image.is_debayered:
            data_to_save = self._convert_to_bayer(data_to_save, image.bayer_pattern)
            print(f"Image convertie au format Bayer original: {image.bayer_pattern}")
        
        # Mettre à jour le header
        header_to_save['HISTORY'] = f'Processed with FitsImageManager on {Time.now().iso}'
        
        # Créer le HDU et sauvegarder
        hdu = fits.PrimaryHDU(data=data_to_save, header=header_to_save)
        hdu.writeto(output_filename, overwrite=True)
        
        print(f"Fichier sauvegardé: {output_filename}")
        print(f"Dimensions: {data_to_save.shape}")
    
    def _convert_to_bayer(self, color_image: np.ndarray, bayer_pattern: str) -> np.ndarray:
        """
        Convertit une image couleur RGB vers le format Bayer original.
        Cette fonction simule un capteur Bayer en échantillonnant les canaux appropriés.
        """
        if len(color_image.shape) != 3 or color_image.shape[2] != 3:
            return color_image
        
        h, w, _ = color_image.shape
        bayer_image = np.zeros((h, w), dtype=color_image.dtype)
        
        # Extraire les canaux RGB
        r_channel = color_image[:, :, 0]
        g_channel = color_image[:, :, 1] 
        b_channel = color_image[:, :, 2]
        
        # Appliquer le pattern Bayer
        if bayer_pattern == 'RGGB':
            bayer_image[0::2, 0::2] = r_channel[0::2, 0::2]  # R
            bayer_image[0::2, 1::2] = g_channel[0::2, 1::2]  # G
            bayer_image[1::2, 0::2] = g_channel[1::2, 0::2]  # G
            bayer_image[1::2, 1::2] = b_channel[1::2, 1::2]  # B
        elif bayer_pattern == 'BGGR':
            bayer_image[0::2, 0::2] = b_channel[0::2, 0::2]  # B
            bayer_image[0::2, 1::2] = g_channel[0::2, 1::2]  # G
            bayer_image[1::2, 0::2] = g_channel[1::2, 0::2]  # G
            bayer_image[1::2, 1::2] = r_channel[1::2, 1::2]  # R
        elif bayer_pattern == 'GRBG':
            bayer_image[0::2, 0::2] = g_channel[0::2, 0::2]  # G
            bayer_image[0::2, 1::2] = r_channel[0::2, 1::2]  # R
            bayer_image[1::2, 0::2] = b_channel[1::2, 0::2]  # B
            bayer_image[1::2, 1::2] = g_channel[1::2, 1::2]  # G
        elif bayer_pattern == 'GBRG':
            bayer_image[0::2, 0::2] = g_channel[0::2, 0::2]  # G
            bayer_image[0::2, 1::2] = b_channel[0::2, 1::2]  # B
            bayer_image[1::2, 0::2] = r_channel[1::2, 0::2]  # R
            bayer_image[1::2, 1::2] = g_channel[1::2, 1::2]  # G
        
        return bayer_image
    
    def save_as_image(
        self,
        image: FitsImage,
        output_filename: str,
        format: str = 'auto',
        quality: int = 95,
        stretch: bool = False,
        stretch_percentiles: Tuple[float, float] = (1.0, 99.0)
    ) -> None:
        

        print(image)
        if image.data is None:
            raise ValueError("Image vide")

        # Auto-détection du format
        if format == 'auto':
            ext = os.path.splitext(output_filename)[1].lower()
            format = {
                '.jpg': 'jpeg',
                '.jpeg': 'jpeg',
                '.png': 'png',
                '.tif': 'tiff',
                '.tiff': 'tiff'
            }.get(ext, 'png')  # par défaut PNG

            if not output_filename.endswith(ext):
                output_filename += f".{format}"

        data = image.data.copy()

        # Stretch pour l'affichage
        def stretch_data(d):
            p_low = np.percentile(d, stretch_percentiles[0])
            p_high = np.percentile(d, stretch_percentiles[1])
            return np.clip((d - p_low) / (p_high - p_low), 0, 1) if p_high > p_low else d

        if stretch:
            if len(data.shape) == 3 and data.shape[2] == 3:
                for c in range(3):
                    data[:, :, c] = stretch_data(data[:, :, c])
            else:
                data = stretch_data(data)

        # Détection profondeur
        is_color = len(data.shape) == 3 and data.shape[2] == 3
        dtype = data.dtype

        # Convertir pour PIL si nécessaire
        if format in ['jpeg', 'png']:
            # PIL ne gère que 8 bits pour PNG/JPEG en RGB/L
            data_normalized = data.astype(np.float64)
            if dtype.kind in ['u', 'i']:
                data_normalized /= np.iinfo(dtype).max
            elif dtype.kind == 'f' and data_normalized.max() > 1.0:
                data_normalized /= data_normalized.max()

            data_uint8 = (np.clip(data_normalized, 0, 1) * 255).astype(np.uint8)
            pil_mode = 'RGB' if is_color else 'L'
            pil_image = Image.fromarray(data_uint8, mode=pil_mode)
        elif format == 'tiff':
            # PIL supporte RGB et L en 16 bits pour TIFF
            if dtype != np.uint16:
                # Convertir en uint16 si autre chose (ex : float32)
                if data.dtype.kind == 'f':
                    #data = np.clip(data, 0, 1)
                    data = (data * 65535).astype(np.uint16)
                else:
                    data = data.astype(np.uint16)

            tiff.imwrite(output_filename, data)
            return

        else:
            raise ValueError(f"Format non supporté : {format}")

        # Sauvegarde
        save_params = {}
        if format == 'jpeg':
            save_params = {'format': 'JPEG', 'quality': quality, 'optimize': True}
        elif format == 'png':
            save_params = {'format': 'PNG', 'optimize': True}
        elif format == 'tiff':
            save_params = {'format': 'TIFF'}

        pil_image.save(output_filename, **save_params)

        print(f"[✔] Image sauvegardée : {output_filename}")
        print(f"     Format : {format.upper()}")
        print(f"     Mode   : {pil_image.mode}")
        print(f"     Taille : {pil_image.size}")

    def save_fits_from_array(array, filename:Path, headers: Dict[str,str]):
        image=np.array(array,dtype=np.uint16)
        if image.ndim==3 : 
            image = np.transpose(image, (2, 0, 1))
        hdu = fits.PrimaryHDU(image)
        if headers:
            for key, value in headers.items():
                hdu.header[key]= value
        
        hdul = fits.HDUList([hdu])
        hdul.writeto(filename, overwrite=True)


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du gestionnaire
    fits_manager = FitsImageManager(auto_normalize=True, auto_debayer=True)
    file="..\\..\\utils\\01-observation-m16\\01-images-initial\\TargetSet.M27.6.00.LIGHT.215.2023-10-01_22-01-54.fits.fits"
    file="./astro_session/final/final2.fit"
    import matplotlib.pyplot as plt

    #try:
        # Ouvrir un fichier FITS
    image = fits_manager.open_fits(file)
    plt.imshow(np.clip(image.data / np.max(image.data), 0, 1),  origin='upper')
    print()

    plt.colorbar()
    plt.title("Image FITS")
    plt.show()
        # Afficher les informations
        #print("\nInformations sur l'image:")
        #info = fits_manager.get_info()
        #for key, value in info.items():
        #    print(f"  {key}: {value}")
        
        # Définir le pattern Bayer si nécessaire
        # fits_manager.set_bayer_pattern('RGGB')
        
        # Debayeriser l'image si c'est une image Bayer
        #if fits_manager.bayer_pattern:
        #    fits_manager.debayer(algorithm='bilinear')
        
        # Appliquer des modifications
        #fits_manager.adjust_brightness(1.2)
        #fits_manager.adjust_contrast(1.1)
        
        # Sauvegarder le résultat
        #fits_manager.save_fits(image, "resultat.fits", preserve_original_format=True)
    print(image)
    fits_manager.save_as_image(image, "resultat.tif", stretch=False)
    fits_manager.save_as_image(image, "resultat.jpg", stretch=False)
        
    #except Exception as e:
    #    print(f"Erreur: {e}")
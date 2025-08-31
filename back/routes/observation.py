from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.responses import StreamingResponse, FileResponse
from typing import List
from models.api import PlanType, ImageSettings
from services.skymap import generate_dso_image, generate_map
from models.state import telescope_state
from services.scheduler import Scheduler
from services.telescope_interface import telescope_interface
from models.observation import Observation,PlansExecutionType
from imageprocessing.astrofilters import AstroFilters
import numpy as np
import io
from PIL import Image
from services.configurator import CURRENT_DIR
from pathlib import Path
from services.history_manager import HistoryManager
from imageprocessing.fitsprocessor import FitsImageManager
from services.configurator import CONFIG
from services.focuser import AutoFocusLib
from utils.section_timer import SectionTimer
from time import sleep

router = APIRouter(prefix="/observation", tags=["observation"])
astro_filters = AstroFilters()
fits_manager = FitsImageManager()
autofocus = AutoFocusLib( )

@router.get("/plot")
def get_dso_image(object: str = Query(..., description="Nom ou identifiant de l'objet (ex: M31, NGC 7000)")):
    image_stream = generate_map(object)
    return StreamingResponse(image_stream, media_type="image/png")


async def return_image(image_path: Path):
    if not image_path or not image_path.exists():
        return FileResponse(
            path=(CURRENT_DIR.parent / Path("assets") /  Path("stacking_waiting.png")).resolve(),
            media_type="image/png",  # Adapter selon le type d'image
            filename=image_path.name
        )
        
    
    
    # Vérifier que c'est bien un fichier (pas un dossier)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Chemin invalide")
    
    # Retourner le fichier avec le bon Content-Type
    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",  # Adapter selon le type d'image
        filename=image_path.name
    )

def transform_to_jpg(image):
    try:

        if image is None:
            return FileResponse(
                path=(CURRENT_DIR.parent / Path("assets") /  Path("image_waiting.png")).resolve(),
                media_type="image/png",  # Adapter selon le type d'image
                filename="image_waiting.png"
            )


        
        image = fits_manager.normalize(image)
        processed_image =  astro_filters.replace_lowest_percent_by_zero(astro_filters.auto_stretch(image, telescope_state.image_settings.stretch, algo=0, shadow_clip=-2),telescope_state.image_settings.black_point)
        #processed_image = astro_filters.asinh_stretch_color(image, 0.2)

        #astro_filters.denoise_gaussian()
        #astro_filters.replace_lowest_percent_by_zero(
        #, 
        #        80
        #    )
        # Convertir en format PIL Image
        # Supposons que processed_image est un array numpy
        if isinstance(processed_image, np.ndarray):
            # Normaliser les valeurs entre 0 et 255 si nécessaire
            if processed_image.dtype != np.uint8:
                # Normaliser entre 0 et 1 puis convertir en uint8
                processed_image = ((processed_image - processed_image.min()) / 
                                (processed_image.max() - processed_image.min()) * 255).astype(np.uint8)
            
            # Créer une image PIL
            if len(processed_image.shape) == 3:  # Image couleur
                pil_image = Image.fromarray(processed_image, mode='RGB')
            else:  # Image en niveaux de gris
                pil_image = Image.fromarray(processed_image, mode='L')
        else:
            # Si l'image est déjà au format PIL
            pil_image = processed_image
        
        # Convertir en JPG et sauvegarder dans un buffer
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        

        # Retourner la réponse streaming
        return StreamingResponse(
            io.BytesIO(img_buffer.read()),
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline; filename=last_image.jpg"}
        )
    except Exception as e:
        
        return FileResponse(
            path=(CURRENT_DIR.parent / Path("assets") /  Path("image_waiting.png")).resolve(),
            media_type="image/png",  # Adapter selon le type d'image
            filename="image_waiting.png"
        )


@router.get('/image_settings')
def get_image_settings() -> ImageSettings:
    return telescope_state.image_settings

@router.put('/image_settings')
def set_image_settings(settings: ImageSettings) -> ImageSettings:
    telescope_state.image_settings = settings
    return get_image_settings()



@router.get("/last_stacked_image")
def get_last_stacked_image():
    """
    Retourne une image depuis le dossier images/
    """
    # Définir le chemin du dossier d'images
    image = telescope_state.last_stacked_picture
    return transform_to_jpg(image)


@router.get("/last_image")
def get_last_image():
    """
    Return the last image taken by the telescope
    If the image is not set, return a waiting image
    The binning is done here instead just after the image is taken for performance reasons
    """
    timer = SectionTimer("get_last_image")
    try:
        if telescope_state.last_picture is not None:
            image = telescope_state.last_picture.copy()
            timer.mark("copy last_picture")

            if len(image.shape) < 3:
                sensor, bayer, color_type = telescope_interface.get_bayer_pattern()
                timer.mark("get_bayer_pattern")

                if bayer:
                    image = fits_manager.debayer(image, bayer)
                    timer.mark("debayer")
                    telescope_state.last_picture = image.copy()
                    timer.mark("cache_debayered_copy")

            target_width = CONFIG['global'].get("live_stacking_image_size", 800)
            if target_width > 0:
                h, w = image.shape[:2]
                if w > target_width:
                    bin_factor = max(1, w // target_width)
                    timer.mark("compute_bin_factor")
                    if bin_factor >= 2:
                        image = FitsImageManager.bin_image(image, bin_factor)
                        timer.mark(f"bin_image x{bin_factor}")
                        telescope_state.last_picture = image.copy()
                        timer.mark("cache_binned_copy")
        else:
            image = None
            timer.mark("no_last_picture")

        jpg = transform_to_jpg(image)
        timer.mark("transform_to_jpg")
        return jpg

    finally:
        timer.end()


@router.get("/history")
def get_history() -> PlansExecutionType:
    if is_running():
        return telescope_state.scheduler.history.history
    else:
        history = HistoryManager()
        history.open_history()
        return history.history
        
@router.get("/history/{index}")
def get_history_image(index: int):
    history = get_history()
    if index<len(history):
        image = history[index].jpg
        try:
            image = fits_manager.open_fits(image)
        except:
            raise HTTPException(status_code=404, detail="Chemin invalide")
        if image!=None:
            return transform_to_jpg(image.data)
    raise HTTPException(status_code=404, detail="Chemin invalide")

@router.post("/start")
def receive_plans(plans: List[PlanType]):
    """
    Endpoint pour recevoir un tableau de plans d'observation
    """
    if telescope_state.scheduler and telescope_state.scheduler.is_alive():
        raise HTTPException(status_code=500, detail="Plan already runnning")

    telescope_state.scheduler = Scheduler(telescope_interface)
    plans_for_scheduler = []
    for plan in plans: 
        if not isinstance(plan, PlanType):
            plan = PlanType(**plan)
        obs = Observation(
            start=plan.start,
            expo=plan.expo,
            number=plan.nExpo,
            ra=plan.ra,
            dec=plan.dec,
            filter=plan.filter,
            object=plan.object,
            focus=plan.focus,
            gain=plan.gain,
        )
        plans_for_scheduler.append(obs)

    telescope_state.scheduler.plan = plans_for_scheduler
    telescope_state.scheduler.start()
    telescope_state.plan_active=True
    # Logique de traitement ici
    # Par exemple, sauvegarder en base de données, valider les données, etc.
    
    return {
        "status": "success",
        "message": f"Reçu et traité {len(plans)} plans",
        "plans_count": len(plans)
    }

@router.get("/is_running")
def is_running() -> bool:
    if telescope_state.plan_active and telescope_state.scheduler and telescope_state.scheduler.is_alive():
        return True
    return False

@router.post("/stop")
def stop_observation():
    """
    Démarre une observation
    """
    # Logique pour démarrer l'observation
    if not telescope_state.scheduler or not telescope_state.scheduler.is_alive():
        raise HTTPException(status_code=500, detail="No plan is running")
    telescope_state.scheduler.request_stop()
    telescope_state.scheduler.join(timeout=5)
    telescope_state.scheduler=None
    telescope_state.plan_active=False

    return {"status": "stopped", "message": "Observation stopped"}


@router.post('/capture')
def get_capture(exposition: int = Body(..., embed=True)):
    global autofocus
    if (telescope_state.bin_x!=CONFIG['camera'].get("binx_focuser",1)):
        telescope_state.bin_x = CONFIG['camera'].get("binx_focuser",1)
        telescope_state.bin_y=CONFIG['camera'].get("biny_focuser",1)
        telescope_interface.set_bin_x(CONFIG['camera'].get("binx_focuser",1))
        telescope_interface.set_bin_y(CONFIG['camera'].get("biny_focuser",1))

        sleep(0.5)

    timer = SectionTimer("get_capture")

    if telescope_state.scheduler and telescope_state.scheduler.is_alive():
        return get_last_image()
    if telescope_state.dark_processor and telescope_state.dark_processor.is_running:
        return get_last_image()
    timer.mark("check")

    if CONFIG['global'].get('debug', False):
        telescope_interface.capture_to_fit(exposition, 0, 0, "", "", Path(CONFIG['global'].get("fits_storage_dir")),100)
    else:
        telescope_interface.camera_capture(exposition,True)
    timer.mark("capture")

    #telescope_state.last_analyzed_image=autofocus.analyze_image(telescope_state.last_picture,None)
    autofocus.set_buffer_image(telescope_state.last_picture)
    timer.mark("fhwm")
    timer.end()
    return get_last_image()

@router.get('/last_analyzed')
def get_last_fhwm():
    return telescope_state.last_analyzed_image

@router.get('/fwhm')
def get_fhwm():
    telescope_state.last_analyzed_image=autofocus.analyze_buffer_image()
    return get_last_fhwm()
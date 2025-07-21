from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import List
from models.api import PlanType
from services.skymap import generate_dso_image, generate_map
from models.state import telescope_state
from services.scheduler import Scheduler
from services.telescope_interface import telescope_interface
from models.observation import Observation
from imageprocessing.astrofilters import AstroFilters
import numpy as np
import io
from PIL import Image


router = APIRouter(prefix="/observation", tags=["observation"])
astro_filters = AstroFilters()

@router.get("/plot")
def get_dso_image(object: str = Query(..., description="Nom ou identifiant de l'objet (ex: M31, NGC 7000)")):
    image_stream = generate_map(object)
    return StreamingResponse(image_stream, media_type="image/png")


@router.get("/last_stacked_image")
async def get_last_stacked_image():
    """
    Retourne une image depuis le dossier images/
    """
    # Définir le chemin du dossier d'images
    image_path = telescope_state.last_stacked_picture
    if not image_path:
        raise HTTPException(status_code=404, detail="Chemin invalide")
    
    # Vérifier que le fichier existe
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Vérifier que c'est bien un fichier (pas un dossier)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Chemin invalide")
    
    # Retourner le fichier avec le bon Content-Type
    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",  # Adapter selon le type d'image
        filename=image_path.name
    )



@router.get("/last_image")
def get_last_image():
    """
    Retourne une image depuis le dossier images/ au format JPG
    """
    # Récupérer l'image depuis telescope_state
    image = telescope_state.last_picture
    if image is None:
        raise HTTPException(status_code=404, detail="Aucune image capturée")
    
    # Appliquer les filtres 
    processed_image = astro_filters.denoise_gaussian(
        astro_filters.replace_lowest_percent_by_zero(
            astro_filters.auto_stretch(image, 0.25, algo=1, shadow_clip=-2), 
            80
        )
    )
    
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
        obs = Observation(plan.start, plan.expo,plan.nExpo, plan.ra, plan.dec, plan.filter, plan.object, plan.focus, plan.gain)
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



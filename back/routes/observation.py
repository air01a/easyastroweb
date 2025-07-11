from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import List
from models.api import PlanType
from services.skymap import generate_dso_image, generate_map
from models.state import telescope_state
from services.scheduler import Scheduler
from services.telescope_interface import telescope_interface
from models.observation import Observation


router = APIRouter(prefix="/observation", tags=["observation"])

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


@router.post("/start")
def receive_plans(plans: List[PlanType]):
    """
    Endpoint pour recevoir un tableau de plans d'observation
    """
    if telescope_state.scheduler and telescope_state.scheduler.is_alive():
        raise HTTPException(status_code=500, detail="Plan already runnning")
    print(plans)

    telescope_state.scheduler = Scheduler(telescope_interface)
    plans_for_scheduler = []
    for plan in plans: 
        if not isinstance(plan, PlanType):
            plan = PlanType(**plan)
        obs = Observation(plan.start, plan.expo,plan.nExpo, plan.ra, plan.dec, plan.filter, plan.object, plan.focus)
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
    print(telescope_state)
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
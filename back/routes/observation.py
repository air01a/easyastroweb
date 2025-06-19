from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import List
from .models import PlanType
from services.skymap import generate_dso_image, generate_map

router = APIRouter(prefix="/observation", tags=["observation"])

@router.get("/plot")
def get_dso_image(object: str = Query(..., description="Nom ou identifiant de l'objet (ex: M31, NGC 7000)")):
    image_stream = generate_map(object)
    return StreamingResponse(image_stream, media_type="image/png")

@router.post("/plans")
async def receive_plans(plans: List[PlanType]):
    """
    Endpoint pour recevoir un tableau de plans d'observation
    """
    print(f"Reçu {len(plans)} plans:")
    for i, plan in enumerate(plans):
        print(f"Plan {i+1}: {plan}")
    
    # Logique de traitement ici
    # Par exemple, sauvegarder en base de données, valider les données, etc.
    
    return {
        "status": "success",
        "message": f"Reçu et traité {len(plans)} plans",
        "plans_count": len(plans)
    }

@router.post("/start")
async def start_observation():
    """
    Démarre une observation
    """
    # Logique pour démarrer l'observation
    return {"status": "started", "message": "Observation démarrée"}
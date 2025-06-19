from fastapi import APIRouter
from . import telescope, camera, observation, websocket

# Router principal qui combine tous les sous-routers
api_router = APIRouter()

# Inclusion des routers
api_router.include_router(telescope.router)
api_router.include_router(camera.router)
api_router.include_router(observation.router)
api_router.include_router(websocket.router)

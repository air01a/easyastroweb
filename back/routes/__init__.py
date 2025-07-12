from fastapi import APIRouter
from . import configuration,  observation, telescopes, websocket, observatories, cameras, filter_wheels, status
# Router principal qui combine tous les sous-routers
api_router = APIRouter()

# Inclusion des routers
api_router.include_router(telescopes.router)
api_router.include_router(cameras.router)
api_router.include_router(observation.router)
api_router.include_router(websocket.router)
api_router.include_router(configuration.router)
api_router.include_router(observatories.router)
api_router.include_router(cameras.router)
api_router.include_router(filter_wheels.router)
api_router.include_router(status.router)
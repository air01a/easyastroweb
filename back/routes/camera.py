from fastapi import APIRouter
from services.alpaca_client import alpaca_camera_client

router = APIRouter(prefix="/camera", tags=["camera"])

@router.get("/config")
async def get_camera_config():
    return await alpaca_camera_client.get_camera_info()
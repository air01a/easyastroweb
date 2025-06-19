from fastapi import APIRouter
from services.alpaca_client import alpaca_telescope_client
from datetime import datetime, timezone

router = APIRouter(prefix="/telescope", tags=["telescope"])

@router.get("/config")
async def get_telescope_config():
    return await alpaca_telescope_client.get_telescope_info()

@router.get('/test')
async def test_telescope():
    await alpaca_telescope_client.set_tracking(True)
    await alpaca_telescope_client.slew_to_coordinates_async(23.1111, 80)

def get_utc_timestamp_precise():
    now = datetime.now(timezone.utc)
    micro = now.microsecond
    return now.strftime(f"%Y-%m-%dT%H:%M:%SZ")

@router.get("/setdate")
async def set_telescope_date():
    print(get_utc_timestamp_precise())
    test = await alpaca_telescope_client.set_utc_date(get_utc_timestamp_precise())
    print(test.body)
    return {"status": "date_set"}

@router.get("/getdate")
async def get_telescope_date():
    test = await alpaca_telescope_client.get_utc_date()
    return test
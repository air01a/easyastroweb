# alpaca_client.py
import httpx

class AlpacaClient:
    def __init__(self, base_url: str = "http://localhost:11111/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_configuration(self):
        r = await self.client.get(f"{self.base_url}/telescope/0/configured")
        return r.json()

    async def get_position(self):
        r = await self.client.get(f"{self.base_url}/telescope/0/rightascension")
        ra = r.json()
        r = await self.client.get(f"{self.base_url}/telescope/0/declination")
        dec = r.json()
        return {"ra": ra, "dec": dec}

    async def slew_to(self, ra: float, dec: float):
        r = await self.client.put(f"{self.base_url}/telescope/0/movera", params={"RightAscension": ra})
        r = await self.client.put(f"{self.base_url}/telescope/0/movedec", params={"Declination": dec})
        return r.status_code == 200


alpaca_client = AlpacaClient()
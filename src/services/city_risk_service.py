import httpx
from src.core.logger import logger

class CityRiskService:
    BASE_URL = 'https://nag.sofia.bg/RegisterExpropriation'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://nag.sofia.bg'
    }

    def __init__(self, client: httpx.AsyncClient = None):
        self.client = client

    async def check_expropriation(self, cadastre_id: str, district: str = "") -> dict:
        log = logger.bind(cadastre_id=cadastre_id)
        if not cadastre_id: return {"is_expropriated": False}

        local_client = self.client if self.client else httpx.AsyncClient(headers=self.HEADERS, timeout=10.0)

        try:
            # 1. Set Context
            await local_client.post(f"{self.BASE_URL}/Search", data={'CadNumber': cadastre_id, 'RegionName': district})
            
            # 2. Fetch
            res = await local_client.post(f"{self.BASE_URL}/Read", data={'page': '1', 'pageSize': '10'})
            res.raise_for_status()
            data = res.json()

            is_risk = data and data.get("Data") and len(data["Data"]) > 0
            
            if is_risk:
                log.critical("expropriation_risk_found", details=str(data["Data"][0]))
                return {
                    "is_expropriated": True, 
                    "details": str(data["Data"][0]),
                    "risk_level": "CRITICAL",
                    "registry_status": "LIVE"
                }
            
            return {"is_expropriated": False, "registry_status": "LIVE"}

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            log.warning("registry_down", error=str(e))
            return {"is_expropriated": False, "registry_status": "OFFLINE"}
        finally:
            if not self.client:
                await local_client.aclose()

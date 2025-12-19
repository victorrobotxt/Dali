import logging
import httpx

logger = logging.getLogger("city_risk")

class CityRiskService:
    """
    Checks if the property is on the Expropriation List (Seizure Risk).
    Handles Registry connection failures gracefully.
    """
    
    BASE_URL = 'https://nag.sofia.bg/RegisterExpropriation'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://nag.sofia.bg'
    }

    async def check_expropriation(self, cadastre_id: str, district: str = "") -> dict:
        if not cadastre_id: return {"is_expropriated": False}

        async with httpx.AsyncClient(headers=self.HEADERS, timeout=8.0, verify=False) as client:
            try:
                # 1. Set Context
                await client.post(f"{self.BASE_URL}/Search", data={'CadNumber': cadastre_id, 'RegionName': district})
                
                # 2. Fetch
                res = await client.post(f"{self.BASE_URL}/Read", data={'page': '1', 'pageSize': '10'})
                res.raise_for_status()
                data = res.json()

                if data and data.get("Data") and len(data["Data"]) > 0:
                    return {
                        "is_expropriated": True, 
                        "details": str(data["Data"][0]),
                        "risk_level": "CRITICAL",
                        "registry_status": "LIVE"
                    }
                
                return {"is_expropriated": False, "registry_status": "LIVE"}

            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                logger.warning(f"Expropriation Registry is DOWN: {e}")
                return {
                    "is_expropriated": False, 
                    "registry_status": "OFFLINE",
                    "details": "Expropriation Register Unavailable (NAG Down)"
                }
            except Exception as e:
                logger.error(f"Expropriation check error: {e}")
                return {"is_expropriated": False, "error": str(e), "registry_status": "ERROR"}

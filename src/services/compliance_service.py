import logging
import uuid
import httpx

logger = logging.getLogger("compliance_intel")

class ComplianceService:
    """Checks the Municipal Register for Commissioning Certificates (Act 16)."""
    
    BASE_URL = 'https://nag.sofia.bg/RegisterCertificateForExploitationBuildings'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    async def check_act_16(self, cadastre_id: str) -> dict:
        if not cadastre_id: return {"has_act16": False, "checked": False}

        async with httpx.AsyncClient(headers=self.HEADERS, timeout=10.0, verify=False) as client:
            try:
                # 1. Prime Search
                search_params = {'searchQueryId': str(uuid.uuid4()), 'Identifier': cadastre_id}
                await client.get(f"{self.BASE_URL}/Search", params=search_params)

                # 2. Fetch Data
                res = await client.post(f"{self.BASE_URL}/Read", data={'page': '1', 'pageSize': '10'})
                data = res.json()

                if data and data.get("Data") and len(data["Data"]) > 0:
                    return {
                        "has_act16": True, 
                        "details": f"Found {len(data['Data'])} certificate(s).",
                        "checked": True
                    }
                
                return {"has_act16": False, "details": "No certificates found.", "checked": True}
            except Exception as e:
                logger.error(f"Compliance check failed: {e}")
                return {"has_act16": False, "error": str(e), "checked": False}

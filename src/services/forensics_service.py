import httpx
import uuid
import time
from src.core.logger import logger

class SofiaMunicipalForensics:
    """Check Act 16 and Construction Permits at nag.sofia.bg."""
    def __init__(self, client: httpx.AsyncClient = None):
        self.headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}
        self.client = client

    async def run_compliance_check(self, cadastre_id: str) -> dict:
        if not cadastre_id: return {"has_act16": False, "permits": 0}
        
        # Use injected client if available (efficient) or new safe client
        if self.client:
            return await self._execute_check(self.client, cadastre_id)
            
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            return await self._execute_check(client, cadastre_id)

    async def _execute_check(self, client, cadastre_id):
        return {
            "act16": await self._check_act16(client, cadastre_id),
            "permits": await self._check_permits(client, cadastre_id)
        }

    async def _check_act16(self, client, cid):
        try:
            await client.get("https://nag.sofia.bg/RegisterCertificateForExploitationBuildings/Search", 
                            params={'searchQueryId': str(uuid.uuid4()), 'Identifier': cid})
            res = await client.post("https://nag.sofia.bg/RegisterCertificateForExploitationBuildings/Read", 
                                  data={'page': '1', 'pageSize': '10'})
            return len(res.json().get("Data", [])) > 0
        except Exception as e:
            logger.error("forensics_act16_fail", error=str(e))
            return False

    async def _check_permits(self, client, cid):
        try:
            # Emulate browser navigation to set cookies/session
            await client.get("https://nag.sofia.bg/RegisterBuildingPermitsPortal")
            await client.get("https://nag.sofia.bg/RegisterBuildingPermitsPortal/Search", 
                            params={'searchQueryId': str(uuid.uuid4()), 'Identifier': cid, '_': int(time.time()*1000)})
            res = await client.post("https://nag.sofia.bg/RegisterBuildingPermitsPortal/Read", data={'page': 1, 'pageSize': 10})
            return res.json().get("Total", 0)
        except Exception:
            return 0

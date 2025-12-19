import httpx
import uuid
import time

class SofiaMunicipalForensics:
    """Check Act 16 and Construction Permits at nag.sofia.bg."""
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}

    async def run_compliance_check(self, cadastre_id: str) -> dict:
        if not cadastre_id: return {"has_act16": False, "permits": 0}
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=15.0) as client:
            return {
                "act16": await self._check_act16(client, cadastre_id),
                "permits": await self._check_permits(client, cadastre_id)
            }

    async def _check_act16(self, client, cid):
        await client.get("https://nag.sofia.bg/RegisterCertificateForExploitationBuildings/Search", 
                         params={'searchQueryId': str(uuid.uuid4()), 'Identifier': cid})
        res = await client.post("https://nag.sofia.bg/RegisterCertificateForExploitationBuildings/Read", data={'page': '1', 'pageSize': '10'})
        return len(res.json().get("Data", [])) > 0

    async def _check_permits(self, client, cid):
        await client.get("https://nag.sofia.bg/RegisterBuildingPermitsPortal")
        await client.get("https://nag.sofia.bg/RegisterBuildingPermitsPortal/Search", 
                         params={'searchQueryId': str(uuid.uuid4()), 'Identifier': cid, '_': int(time.time()*1000)})
        res = await client.post("https://nag.sofia.bg/RegisterBuildingPermitsPortal/Read", data={'page': 1, 'pageSize': 10})
        return res.json().get("Total", 0)

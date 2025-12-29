import asyncio, re, httpx
from bs4 import BeautifulSoup
from src.schemas import CadastreData
from src.core.logger import logger

class CadastreService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Referer': 'https://kais.cadastre.bg/bg/Map'}

    async def get_official_details(self, address: str) -> CadastreData:
        log = logger.bind(target_address=address)
        try:
            # 1. Handshake & Search
            resp = await self.client.get("https://kais.cadastre.bg/bg/Map")
            token = BeautifulSoup(resp.text, 'html.parser').find('input', {'name': '__RequestVerificationToken'}).get('value')
            await self.client.get("https://kais.cadastre.bg/bg/Map/FastSearch", params={'KeyWords': address})
            await asyncio.sleep(0.7) 
            
            # 2. Results
            res = await self.client.post("https://kais.cadastre.bg/bg/Map/ReadFoundObjects", data={'page': 1, 'pageSize': 5}, headers={**self.headers, 'X-CSRF-TOKEN': token})
            data = res.json()
            if not data.get('Data'): return CadastreData(status="NOT_FOUND")

            obj = data['Data'][0]
            info = await self.client.get("https://kais.cadastre.bg/bg/Map/GetObjectInfo", params=obj)
            
            area_match = re.search(r"площ(?: по документ)?\s*([\d,\.]+)\s*кв\.?\s*м", info.text, re.IGNORECASE)
            area = float(area_match.group(1).replace(',', '.')) if area_match else 0.0
            
            # 3. DIRTY COP: Calculate Municipal Ownership Ratio
            # (Check surrounding units in the same building)
            social_ratio = 0.0
            if obj.get('Number'):
                social_ratio = await self._calculate_social_density(obj.get('Number'), token)

            return CadastreData(cadastre_id=obj.get('Number'), official_area=area, address_found=obj.get('Address'), status="LIVE", social_risk_ratio=social_ratio)
        except Exception as e:
            log.error("cadastre_failed", error=str(e))
            return CadastreData(status="ERROR")

    async def _calculate_social_density(self, cad_id: str, token: str) -> float:
        """Scan building neighbors to detect social housing clusters (Municipal Ownership)."""
        building_id = ".".join(cad_id.split(".")[:3])
        try:
            res = await self.client.post("https://kais.cadastre.bg/bg/Map/ReadFoundObjects", data={'page': 1, 'pageSize': 40, 'KeyWords': building_id}, headers={**self.headers, 'X-CSRF-TOKEN': token})
            units = res.json().get('Data', [])
            if not units: return 0.0
            
            # Count municipal keywords in unit descriptions
            municipal_count = sum(1 for u in units if any(k in u.get('DisplayText', '').lower() for k in ['община', 'общинска', 'държавна']))
            return municipal_count / len(units)
        except: return 0.0

import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from src.schemas import CadastreData
from src.core.logger import logger

class CadastreService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://kais.cadastre.bg/bg/Map'
        }

    async def get_official_details(self, address: str) -> CadastreData:
        log = logger.bind(target_address=address)
        try:
            resp = await self.client.get("https://kais.cadastre.bg/bg/Map", headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            token = soup.find('input', {'name': '__RequestVerificationToken'}).get('value')
            
            await self.client.get("https://kais.cadastre.bg/bg/Map/FastSearch", params={'KeyWords': address})
            await asyncio.sleep(0.7) 
            
            res = await self.client.post(
                "https://kais.cadastre.bg/bg/Map/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 5}, 
                headers={**self.headers, 'X-CSRF-TOKEN': token}
            )
            data = res.json()
            if not data.get('Data'): return CadastreData(status="NOT_FOUND")

            obj = data['Data'][0]
            info = await self.client.get("https://kais.cadastre.bg/bg/Map/GetObjectInfo", params=obj)
            
            # FIX: Handle Bulgarian comma decimals
            area_match = re.search(r"площ(?: по документ)?\s*([\d,\.]+)\s*кв\.?\s*м", info.text, re.IGNORECASE)
            area = 0.0
            if area_match:
                area_str = area_match.group(1).replace(',', '.')
                area = float(area_str)
            
            return CadastreData(cadastre_id=obj.get('Number'), official_area=area, address_found=obj.get('Address'), status="LIVE")
        except Exception as e:
            log.error("cadastre_failed", error=str(e))
            return CadastreData(status="ERROR")

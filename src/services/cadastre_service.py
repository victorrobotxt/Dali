import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from src.schemas import CadastreData

class CadastreService:
    """Registry Forensics: human address -> Official registry truth."""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/142.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://kais.cadastre.bg/bg/Map'
        }

    async def get_official_details(self, address: str) -> CadastreData:
        try:
            # Handshake 1: CSRF
            resp = await self.client.get("https://kais.cadastre.bg/bg/Map", headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            token_tag = soup.find('input', {'name': '__RequestVerificationToken'})
            
            if not token_tag:
                return CadastreData(status="ERROR", official_area=0.0)
                
            token = token_tag.get('value')
            
            # Handshake 2: Strike
            await self.client.get("https://kais.cadastre.bg/bg/Map/FastSearch", 
                                  params={'KeyWords': address}, headers=self.headers)
            await asyncio.sleep(0.6) # Compliance Delay
            
            # Handshake 3: Read
            read_headers = {**self.headers, 'X-CSRF-TOKEN': token}
            res = await self.client.post("https://kais.cadastre.bg/bg/Map/ReadFoundObjects", 
                                   data={'page': 1, 'pageSize': 5}, headers=read_headers)
            data = res.json()
            
            if not data.get('Data'): 
                return CadastreData(status="NOT_FOUND", official_area=0.0)

            # Handshake 4: Detail Parse
            obj = data['Data'][0]
            info = await self.client.get("https://kais.cadastre.bg/bg/Map/GetObjectInfo", 
                                         params=obj, headers=self.headers)
            
            # Handshake 5: Regex extraction
            area_match = re.search(r"площ(?: по документ)?\s*([\d\.]+)\s*кв\.м", info.text)
            area = float(area_match.group(1)) if area_match else 0.0
            
            return CadastreData(
                cadastre_id=obj.get('Number'),
                official_area=area,
                address_found=obj.get('Address'),
                status="LIVE"
            )
        except Exception as e:
            return CadastreData(status="ERROR", official_area=0.0)

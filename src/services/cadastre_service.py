import asyncio
import re
import httpx
from bs4 import BeautifulSoup

class CadastreService:
    """Registry Forensics: human address -> Official registry truth."""
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/142.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://kais.cadastre.bg/bg/Map'
        }

    async def get_official_details(self, address: str) -> dict:
        async with httpx.AsyncClient(headers=self.headers, verify=False, timeout=30.0) as client:
            try:
                # Handshake 1: CSRF
                resp = await client.get("https://kais.cadastre.bg/bg/Map")
                soup = BeautifulSoup(resp.text, 'html.parser')
                token = soup.find('input', {'name': '__RequestVerificationToken'}).get('value')
                
                # Handshake 2: Strike
                await client.get("https://kais.cadastre.bg/bg/Map/FastSearch", params={'KeyWords': address})
                await asyncio.sleep(0.6) # Critical delay
                
                # Handshake 3: Read
                read_headers = {**self.headers, 'X-CSRF-TOKEN': token}
                res = await client.post("https://kais.cadastre.bg/bg/Map/ReadFoundObjects", 
                                       data={'page': 1, 'pageSize': 5}, headers=read_headers)
                data = res.json()
                if not data.get('Data'): return {"official_area": 0, "status": "NOT_FOUND"}

                # Handshake 4: Detail Parse
                obj = data['Data'][0]
                info = await client.get("https://kais.cadastre.bg/bg/Map/GetObjectInfo", params=obj)
                
                # Handshake 5: Bulgarian Regex extraction
                area_match = re.search(r"площ(?: по документ)?\s*([\d\.]+)\s*кв\. м", info.text)
                area = float(area_match.group(1)) if area_match else 0.0
                
                return {
                    "cadastre_id": obj.get('Number'),
                    "official_area": area,
                    "address": obj.get('Address'),
                    "status": "LIVE"
                }
            except Exception as e:
                return {"official_area": 0, "status": "ERROR", "error": str(e)}

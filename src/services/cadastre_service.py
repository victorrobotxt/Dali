import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from src.schemas import CadastreData
from src.core.logger import logger

class CadastreService:
    """Registry Forensics: human address -> Official registry truth (KAIS)."""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://kais.cadastre.bg/bg/Map'
        }

    async def get_official_details(self, address: str) -> CadastreData:
        """
        Executes a 5-step handshake with the Cadastre registry to bypass CSRF 
        and extract official area data.
        """
        log = logger.bind(target_address=address)
        
        try:
            # Handshake 1: Initialize Session and Grab CSRF Token
            resp = await self.client.get("https://kais.cadastre.bg/bg/Map", headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            token_tag = soup.find('input', {'name': '__RequestVerificationToken'})
            
            if not token_tag:
                log.error("kais_csrf_token_missing")
                return CadastreData(status="ERROR", official_area=0.0)
                
            token = token_tag.get('value')
            
            # Handshake 2: Execute "FastSearch" (primes the server-side result state)
            await self.client.get(
                "https://kais.cadastre.bg/bg/Map/FastSearch", 
                params={'KeyWords': address}, 
                headers=self.headers
            )
            # Essential delay to prevent rate-limiting/bot detection
            await asyncio.sleep(0.6) 
            
            # Handshake 3: Read the primed search results
            read_headers = {**self.headers, 'X-CSRF-TOKEN': token}
            res = await self.client.post(
                "https://kais.cadastre.bg/bg/Map/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 5}, 
                headers=read_headers
            )
            data = res.json()
            
            if not data.get('Data') or len(data['Data']) == 0: 
                log.warning("cadastre_not_found")
                return CadastreData(status="NOT_FOUND", official_area=0.0)

            # Handshake 4: Fetch detailed info for the first (best) match
            obj = data['Data'][0]
            info_resp = await self.client.get(
                "https://kais.cadastre.bg/bg/Map/GetObjectInfo", 
                params=obj, 
                headers=self.headers
            )
            
            # Handshake 5: Extract official area using Bulgarian regex
            # Looks for "площ [number] кв.м" or "площ по документ [number] кв.м"
            area_match = re.search(r"площ(?: по документ)?\s*([\d\.]+)\s*кв\.?\s*м", info_resp.text, re.IGNORECASE)
            area = float(area_match.group(1)) if area_match else 0.0
            
            log.info("cadastre_resolved", id=obj.get('Number'), area=area)

            return CadastreData(
                cadastre_id=obj.get('Number'),
                official_area=area,
                address_found=obj.get('Address'),
                status="LIVE"
            )
            
        except (httpx.TimeoutException, httpx.ConnectError):
            log.warning("cadastre_registry_timeout")
            return CadastreData(status="OFFLINE", official_area=0.0)
        except Exception as e:
            log.error("cadastre_analysis_failed", error=str(e))
            return CadastreData(status="ERROR", official_area=0.0)

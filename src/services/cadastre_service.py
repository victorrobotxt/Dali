import logging
import asyncio
import re
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("cadastre_intel")

class CadastreService:
    """
    Interface for the Official Property Registry (Cadastre).
    Includes resiliency logic (Soft Circuit Breaker) for government downtime.
    """
    BASE_URL = "https://kais.cadastre.bg/bg/Map"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://kais.cadastre.bg/bg/Map',
        'Origin': 'https://kais.cadastre.bg'
    }

    async def get_official_details(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Orchestrates the search: Address -> Cadastral ID -> Property Details.
        Returns 'registry_status': 'OFFLINE' if government servers are down.
        """
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=8.0, verify=False) as client:
            try:
                # 1. Resolve Address to Identifier
                identifier = await self._resolve_address_to_id(client, address)
                if identifier == "OFFLINE":
                     return {"cadastre_id": None, "official_area": 0.0, "registry_status": "OFFLINE", "error": "KAIS Timeout"}
                
                if not identifier:
                    logger.warning(f"Cadastre resolution failed for: {address}")
                    return {"cadastre_id": None, "official_area": 0.0, "registry_status": "NOT_FOUND"}

                # 2. Fetch Details using Identifier
                details = await self._fetch_property_data(client, identifier)
                return details

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.error(f"Cadastre connection failed (Down/Slow): {e}")
                return {"cadastre_id": None, "official_area": 0.0, "registry_status": "OFFLINE", "error": "Connection Timeout"}
            except Exception as e:
                logger.error(f"Cadastre lookup error: {e}")
                return {"cadastre_id": None, "official_area": 0.0, "registry_status": "ERROR", "error": str(e)}

    async def _resolve_address_to_id(self, client: httpx.AsyncClient, address: str) -> Optional[str]:
        try:
            # A. Initialize Session (CSRF Token)
            page = await client.get(self.BASE_URL)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token_input: return None
            csrf_token = token_input.get('value')

            # B. Execute Search
            await client.get(f"{self.BASE_URL}/FastSearch", params={'KeyWords': address})
            await asyncio.sleep(0.5)

            # C. Retrieve Results
            read_headers = {**self.HEADERS, 'X-CSRF-TOKEN': csrf_token}
            res = await client.post(
                f"{self.BASE_URL}/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 5}, 
                headers=read_headers
            )
            
            data = res.json()
            if data.get('Data'):
                return data['Data'][0].get('Number') # Return first match
            return None
        except (httpx.TimeoutException, httpx.ConnectError):
            return "OFFLINE"
        except Exception:
            return None

    async def _fetch_property_data(self, client: httpx.AsyncClient, identifier: str) -> Dict[str, Any]:
        try:
            # Re-init session for object lookup
            page = await client.get(self.BASE_URL)
            soup = BeautifulSoup(page.text, 'html.parser')
            csrf_token = soup.find('input', {'name': '__RequestVerificationToken'})['value']

            await client.get(f"{self.BASE_URL}/FastSearch", params={'KeyWords': identifier})
            await asyncio.sleep(0.2)

            read_headers = {**self.HEADERS, 'X-CSRF-TOKEN': csrf_token}
            res = await client.post(
                f"{self.BASE_URL}/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 1}, 
                headers=read_headers
            )
            json_data = res.json()
            
            if not json_data.get('Data'):
                return {"official_area": 0.0, "type": "Unknown", "cadastre_id": identifier, "registry_status": "LIVE"}

            object_params = json_data['Data'][0]
            info_res = await client.get(f"{self.BASE_URL}/GetObjectInfo", params=object_params)
            
            info_soup = BeautifulSoup(info_res.text, 'html.parser')
            raw_text = info_soup.get_text(" ", strip=True)

            area_match = re.search(r"площ(?:\s*по\s*документ)?\s*([\d\.]+)", raw_text, re.IGNORECASE)
            area = float(area_match.group(1)) if area_match else 0.0
            
            return {
                "cadastre_id": identifier,
                "official_area": area,
                "raw_registry_text": raw_text[:300],
                "registry_status": "LIVE"
            }
        except Exception as e:
            return {"official_area": 0.0, "cadastre_id": identifier, "error": str(e), "registry_status": "ERROR"}

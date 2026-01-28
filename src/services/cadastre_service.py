import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from src.schemas import CadastreData
from src.core.logger import logger

class CadastreService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        # 1. Base Identity (Chrome 120 on Linux)
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.base_url = "https://kais.cadastre.bg"

    async def get_official_details(self, address: str) -> CadastreData:
        log = logger.bind(target_address=address)
        
        try:
            # --- STEP 0: SESSION PRIMING (The Fix) ---
            # Hit the root first to get F5 Load Balancer cookies (TS01...)
            # The firewall often blocks direct access to /bg/Map without this "visit"
            await self.client.get(
                self.base_url, 
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive'
                }
            )
            await asyncio.sleep(0.5) # Wait for cookies to settle

            # --- STEP 1: HANDSHAKE (Fetch Map) ---
            # Now we ask for the Map. The cookies from Step 0 are automatically included by httpx.
            resp_init = await self.client.get(
                f"{self.base_url}/bg/Map", 
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Referer': self.base_url + '/',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # --- FORENSIC DEBUG: Save HTML if failed ---
            if "RequestVerificationToken" not in resp_init.text:
                # If we fail, dump the page title to see what we hit (e.g., "Bot Detection")
                page_title = re.search(r'<title>(.*?)</title>', resp_init.text, re.IGNORECASE)
                title_text = page_title.group(1) if page_title else "No Title Found"
                log.error("cadastre_blocked", title=title_text, status=resp_init.status_code)
                return CadastreData(status="ERROR")

            # Extract Token (Soup or Regex fallback)
            soup = BeautifulSoup(resp_init.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            
            if token_input:
                csrf_token = token_input.get('value')
            else:
                # Fallback regex for when Soup fails on malformed HTML
                match = re.search(r'__RequestVerificationToken["\']\s*value=["\']([^"\']+)["\']', resp_init.text)
                csrf_token = match.group(1) if match else None

            if not csrf_token:
                log.error("cadastre_token_missing")
                return CadastreData(status="ERROR")
            
            # --- STEP 2: SEARCH (API MODE) ---
            api_headers = {
                'User-Agent': self.user_agent,
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': csrf_token,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': f"{self.base_url}/bg/Map",
                'Origin': self.base_url
            }

            # 2a. Initialize Search Context
            await self.client.get(f"{self.base_url}/bg/Map/FastSearch", params={'KeyWords': address}, headers=api_headers)
            await asyncio.sleep(0.2)
            
            # 2b. Execute Search
            res_search = await self.client.post(
                f"{self.base_url}/bg/Map/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 10, 'KeyWords': address}, 
                headers=api_headers
            )
            
            if not res_search.json().get('Data'):
                return CadastreData(status="NOT_FOUND")

            obj = res_search.json()['Data'][0]

            # --- STEP 3: FETCH DETAILS ---
            # Parallel fetch
            task_info = self.client.get(f"{self.base_url}/bg/Map/GetObjectInfo", params=obj, headers=api_headers)
            task_desc = self.client.get(f"{self.base_url}/bg/Map/GetObjectDescription", params=obj, headers=api_headers)
            
            res_info, res_desc = await asyncio.gather(task_info, task_desc)

            # Parse Data
            area_match = re.search(r"площ(?: по документ)?\s*([\d,\.]+)\s*кв\.?\s*м", res_info.text, re.IGNORECASE)
            official_area = float(area_match.group(1).replace(',', '.')) if area_match else 0.0
            
            # Helper to strip HTML from description
            addr_soup = BeautifulSoup(res_desc.text, 'html.parser')
            official_address = addr_soup.get_text().strip()

            # --- STEP 4: DIRTY COP SCAN ---
            social_ratio = 0.0
            if obj.get('Number'):
                social_ratio = await self._calculate_social_density(obj.get('Number'), api_headers)

            return CadastreData(
                cadastre_id=obj.get('Number'),
                official_area=official_area,
                address_found=official_address,
                status="LIVE",
                social_risk_ratio=social_ratio
            )

        except Exception as e:
            log.error("cadastre_exception", error=str(e))
            return CadastreData(status="ERROR")

    async def _calculate_social_density(self, cad_id: str, headers: dict) -> float:
        parts = cad_id.split(".")
        if len(parts) < 4: return 0.0
        building_id = ".".join(parts[:4])
        try:
            res = await self.client.post(
                f"{self.base_url}/bg/Map/ReadFoundObjects", 
                data={'page': 1, 'pageSize': 50, 'KeyWords': building_id}, 
                headers=headers
            )
            units = res.json().get('Data', [])
            risk_keywords = ['община', 'общинска', 'държавна', 'софийски имоти', 'жилфонд']
            municipal_count = sum(1 for u in units if any(k in (u.get('DisplayText', '') + u.get('Title', '')).lower() for k in risk_keywords))
            return round(municipal_count / len(units), 2) if units else 0.0
        except: return 0.0

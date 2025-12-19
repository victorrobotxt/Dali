import os

# 1. Update Utils (ID Extraction & Normalization)
with open("src/core/utils.py", "w") as f:
    f.write('''import re
import hashlib
from urllib.parse import urlparse

def extract_imot_id(url: str) -> str:
    """Extracts unique listing ID to prevent duplicates."""
    match = re.search(r'(?:adv=|obiava-)([a-z0-9]+)', url)
    return match.group(1) if match else "unknown"

def normalize_url(url: str) -> str:
    """Force mobile subdomain to reduce WAF friction."""
    if "imot.bg" in url:
        return url.replace("www.imot.bg", "m.imot.bg")
    return url

def calculate_content_hash(text: str, price: float) -> str:
    clean_text = re.sub(r'\\s+', ' ', text).strip().lower()
    raw = f"{clean_text}{price}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
''')

# 2. Hardened Cadastre Service (The LexSofia 5-Step Handshake)
with open("src/services/cadastre_service.py", "w") as f:
    f.write('''import asyncio
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
                area_match = re.search(r"площ(?: по документ)?\\s*([\\d\\.]+)\\s*кв\\. м", info.text)
                area = float(area_match.group(1)) if area_match else 0.0
                
                return {
                    "cadastre_id": obj.get('Number'),
                    "official_area": area,
                    "address": obj.get('Address'),
                    "status": "LIVE"
                }
            except Exception as e:
                return {"official_area": 0, "status": "ERROR", "error": str(e)}
''')

# 3. New Forensics Service (Act 16 & Permit Checkers)
with open("src/services/forensics_service.py", "w") as f:
    f.write('''import httpx
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
''')

# 4. Hardened Scraper Service (Windows-1251 & Mobile Identity)
with open("src/services/scraper_service.py", "w") as f:
    f.write('''import httpx
from bs4 import BeautifulSoup
import re

class ScraperService:
    def __init__(self, simulation_mode=False):
        self.simulation = simulation_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1",
            "Accept-Language": "bg-BG,bg;q=0.9"
        }

    def scrape_url(self, url: str) -> dict:
        # Standard cleaning
        url = url.replace("www.imot.bg", "m.imot.bg")
        
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                # Bulgarian Encoding Solve
                content = resp.content.decode('windows-1251', errors='ignore')
                
                if "captcha" in content.lower():
                    return {"error": "WAF_BLOCKED", "raw_text": "Captcha Triggered"}

                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(" ", strip=True)
                
                # Regex for Price with spaces (570 000)
                p_match = re.search(r'([\\d\\s\\.,]+)\\s?(?:EUR|€|лв)', text)
                price = float(re.sub(r'[^\\d]', '', p_match.group(1))) if p_match else 0
                
                return {
                    "source_url": url,
                    "raw_text": text,
                    "price_predicted": price,
                    "image_urls": [img.get('src') for img in soup.find_all('img') if 'imot.bg' in (img.get('src') or "")]
                }
        except Exception as e:
            return {"error": str(e)}
''')

# 5. Apex Predator AI Engine
with open("src/services/ai_engine.py", "w") as f:
    f.write('''import google.generativeai as genai
from pydantic import BaseModel, Field

class AIAnalysisSchema(BaseModel):
    address_prediction: str
    neighborhood: str
    is_atelier: bool
    net_living_area: float
    construction_year: int
    confidence: int

class GeminiService:
    def __init__(self, api_key: str):
        if api_key != "mock-key":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else: self.model = None

    async def analyze_text(self, text: str) -> dict:
        if not self.model: return {"address_prediction": "Simulated", "confidence": 0, "neighborhood": "Unknown", "is_atelier": False, "net_living_area": 0, "construction_year": 2024}
        
        mandate = """
        [ROLE] APEX PREDATOR REAL ESTATE ANALYST.
        [OBJECTIVE] Extract forensic ground truth from listing. 
        [RULES] Compare price vs neighborhood. Detect 'Ателие' (workspace) status. 
        Identify 'Net Living Area' (чиста площ). 
        """
        prompt = f"{mandate}\\n\\nListing Data: {text[:5000]}"
        resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "response_json_schema": AIAnalysisSchema.model_json_schema()})
        return AIAnalysisSchema.model_validate_json(resp.text).model_dump()
''')

print(">>> GLASHAUS HARDENING COMPLETE. READY FOR FORENSIC TASKS. <<<")

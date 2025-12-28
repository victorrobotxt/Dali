import httpx
import uuid
import time
import asyncio
from src.core.logger import logger
from typing import Optional, Dict, Any

class SofiaMunicipalForensics:
    """
    Direct interface to Sofia Municipality (NAG) Registries.
    Implements the "Nuclear Option" (Expropriation) and "Green Light" (Act 16) checks.
    """
    
    BASE_URL = "https://nag.sofia.bg"
    
    # Headers exactly as captured in curl (User-Agent + X-Requested-With are critical)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    def __init__(self, client: httpx.AsyncClient = None):
        self.client = client

    async def run_full_audit(self, cadastre_id: str) -> Dict[str, Any]:
        """
        Runs the 3-Dimensional Audit:
        1. Expropriation (The "Death List")
        2. Act 16 (The "Green List")
        3. Permits (The "Construction History")
        """
        if not cadastre_id:
            return {"error": "No Cadastre ID provided"}

        # Use injected client or create a new ephemeral one
        local_client = self.client if self.client else httpx.AsyncClient(headers=self.HEADERS, timeout=20.0, follow_redirects=True)

        try:
            # Run all 3 checks in parallel for speed
            expropriation, act16, permits = await asyncio.gather(
                self._check_expropriation(local_client, cadastre_id),
                self._check_act16(local_client, cadastre_id),
                self._check_permits(local_client, cadastre_id)
            )

            return {
                "expropriation": expropriation,
                "compliance_act16": act16,
                "building_permits": permits,
                "audit_timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"audit_failed_fatal: {e}")
            return {"error": str(e)}
        finally:
            if not self.client:
                await local_client.aclose()

    async def _check_expropriation(self, client, cid: str) -> Dict:
        """
        Checks 'RegisterExpropriation' (The Death List).
        """
        # 1. SEARCH: Sets the server-side session state
        search_id = str(uuid.uuid4())
        params = {
            'searchQueryId': search_id,
            'RegionName': '', 'RegPlan': '', 'Quarter': '', 'Upi': '',
            'CadNumber': cid,  # <--- TARGET
            'Area': '', 'Obj': '', 'GroupType': '', 'Typology': '', 'StructureZone': '',
            'ApprYear': '', 'X-Requested-With': 'XMLHttpRequest',
            '_': int(time.time() * 1000)
        }
        
        try:
            # Step A: Prime the search
            await client.get(f"{self.BASE_URL}/RegisterExpropriation/Search", params=params)
            
            # Step B: Read the results (Page 1)
            # The server expects a POST to /Read after the GET /Search
            res = await client.post(f"{self.BASE_URL}/RegisterExpropriation/Read", data={'page': 1, 'pageSize': 10})
            data = res.json()
            
            hits = data.get("Data", [])
            is_fatal = len(hits) > 0
            
            return {
                "is_expropriated": is_fatal,
                "risk_level": "CRITICAL" if is_fatal else "NONE",
                "details": hits[0] if is_fatal else None,
                "found_count": len(hits)
            }
        except Exception as e:
            logger.error(f"expropriation_check_failed: {e}")
            return {"error": str(e), "is_expropriated": False}

    async def _check_act16(self, client, cid: str) -> Dict:
        """
        Checks 'RegisterCertificateForExploitationBuildings' (The Green List).
        """
        search_id = str(uuid.uuid4())
        params = {
            'searchQueryId': search_id,
            'IssuedById': '', 'FromDate': '', 'ToDate': '', 'StatusId': '',
            'DocumentTypeName': '', 'Number': '', 'Status': '', 'Issuer': '',
            'Employer': '', 'ConstructionalOversightName': '', 'Object': '',
            'Region': '', 'Terrain': '', 'RegulationNeighbourhood': '', 'Upi': '',
            'Identifier': cid, # <--- TARGET
            'Address': '', 'RegionId': '', 'TakeEffectFilter': '', 
            'MapOfRestoredProperty': '', 'AdditionalDescriptionEstate': '',
            'AdditionalDescriptionAdministrativeAddress': '', 'Scope': '',
            'X-Requested-With': 'XMLHttpRequest',
            '_': int(time.time() * 1000)
        }

        try:
            await client.get(f"{self.BASE_URL}/RegisterCertificateForExploitationBuildings/Search", params=params)
            res = await client.post(f"{self.BASE_URL}/RegisterCertificateForExploitationBuildings/Read", data={'page': 1, 'pageSize': 10})
            data = res.json()
            
            hits = data.get("Data", [])
            has_cert = len(hits) > 0
            
            # Extract description if found (e.g. "Energy Efficiency" vs "New Building")
            cert_desc = hits[0].get("Строеж/Обект", "N/A") if has_cert else None
            
            return {
                "has_act16": has_cert,
                "description": cert_desc,
                "raw_hits": len(hits)
            }
        except Exception as e:
            logger.error(f"act16_check_failed: {e}")
            return {"error": str(e), "has_act16": False}

    async def _check_permits(self, client, cid: str) -> Dict:
        """
        Checks 'RegisterBuildingPermitsPortal' (Construction History).
        """
        search_id = str(uuid.uuid4())
        params = {
            'searchQueryId': search_id,
            'IssuedById': '', 'FromDate': '', 'ToDate': '', 'TakeEffectFrom': '',
            'TakeEffectTo': '', 'StatusId': '', 'DocumentTypeName': '', 'Number': '',
            'Status': '', 'Issuer': '', 'Employer': '', 'ConstructionalOversightName': '',
            'Object': '', 'Region': '', 'Terrain': '', 'RegulationNeighbourhood': '',
            'Upi': '', 
            'Identifier': cid, # <--- TARGET
            'Address': '', 'RegionId': '', 'TakeEffectFilter': '', 
            'MapOfRestoredProperty': '', 'AdditionalDescriptionEstate': '',
            'AdditionalDescriptionAdministrativeAddress': '', 'Scope': '',
            'X-Requested-With': 'XMLHttpRequest',
            '_': int(time.time() * 1000)
        }

        try:
            await client.get(f"{self.BASE_URL}/RegisterBuildingPermitsPortal/Search", params=params)
            res = await client.post(f"{self.BASE_URL}/RegisterBuildingPermitsPortal/Read", data={'page': 1, 'pageSize': 10})
            data = res.json()
            
            return {
                "total_permits": data.get("Total", 0),
                "latest_permit": data.get("Data", [])[0] if data.get("Data") else None
            }
        except Exception as e:
            return {"error": str(e), "total_permits": 0}

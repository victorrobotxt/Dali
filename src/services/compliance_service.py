import httpx
import uuid
from src.core.logger import logger

class ComplianceService:
    BASE_URL = 'https://nag.sofia.bg/RegisterCertificateForExploitationBuildings'
    
    def __init__(self, client: httpx.AsyncClient = None):
        self.client = client

    async def check_act_16(self, cadastre_id: str) -> dict:
        log = logger.bind(cadastre_id=cadastre_id)
        if not cadastre_id: 
            return {"has_act16": False, "checked": False}

        # Use injected client (preferred) or create ephemeral one
        # REMOVED verify=False. Production requires valid SSL or mounted CAs.
        local_client = self.client if self.client else httpx.AsyncClient(timeout=10.0)
        
        try:
            search_params = {'searchQueryId': str(uuid.uuid4()), 'Identifier': cadastre_id}
            
            # 1. Search
            await local_client.get(f"{self.BASE_URL}/Search", params=search_params)
            
            # 2. Read
            res = await local_client.post(f"{self.BASE_URL}/Read", data={'page': '1', 'pageSize': '10'})
            res.raise_for_status()
            data = res.json()
            
            has_cert = len(data.get("Data", [])) > 0
            log.info("compliance_check", found=has_cert)
            
            return {
                "has_act16": has_cert, 
                "checked": True,
                "registry_status": "LIVE"
            }

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            log.warning("registry_down", error=str(e))
            return {"has_act16": False, "checked": False, "registry_status": "OFFLINE"}
            
        finally:
            # Only close if we created it locally
            if not self.client:
                await local_client.aclose()

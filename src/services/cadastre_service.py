from typing import Optional, Dict

class CadastreService:
    """
    Interface for the Official Property Registry (Cadastre).
    In a real deployment, this would use the official API or a headless browser.
    """
    def __init__(self):
        # In the future, API keys for the government portal go here
        pass

    def fetch_details(self, address: str) -> Optional[Dict[str, float]]:
        """
        Simulates a lookup in the national registry.
        Returns: { "official_area": 85.0, "year_built": 2005 }
        """
        print(f"[CADASTRE] Querying registry for: {address}")
        
        # MOCK LOGIC: 
        # For now, we return 'None' to simulate that most addresses 
        # cannot be perfectly matched automatically yet.
        # This prevents the Risk Engine from throwing false positives 
        # until the real integration is ready.
        
        return None 
        
        # EXAMPLE REAL IMPLEMENTATION STUB:
        # response = requests.get(f"https://kais.cadastre.bg/api/search?q={address}")
        # if response.status_code == 200:
        #     return response.json()
        # return None

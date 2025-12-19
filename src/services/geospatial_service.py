from typing import Optional, Dict

class GeospatialService:
    """
    Handles Google Maps / Street View verification.
    """
    def __init__(self, api_key: str = "mock-key"):
        self.api_key = api_key

    def verify_location(self, address: str) -> Dict[str, any]:
        """
        TODO: Implement Google Maps Geocoding API.
        Should return { "lat": float, "lng": float, "street_view_exists": bool }
        """
        if self.api_key == "mock-key":
            return {"lat": 42.6977, "lng": 23.3219, "verified": False}
        
        # Real implementation will go here
        return {}

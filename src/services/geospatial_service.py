import httpx
from src.core.logger import logger
from src.schemas import GeoVerification
from typing import Optional

class GeospatialService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    async def verify_neighborhood(self, ai_prediction: str, ai_landmarks: list, claimed_kvartal: str) -> GeoVerification:
        if self.api_key == "mock-key":
            return GeoVerification(match=True, detected_neighborhood="Mock", confidence=100)

        # Build a search query prioritizing specific clues from Gemini
        search_query = f"{ai_prediction} {' '.join(ai_landmarks)}, Sofia, Bulgaria"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.base_url, params={"address": search_query, "key": self.api_key})
            data = resp.json()

            if data["status"] != "OK" or not data["results"]:
                return GeoVerification(match=True, detected_neighborhood="Not Found", confidence=0)

            result = data["results"][0]
            lat_lng = result["geometry"]["location"]
            formatted_address = result.get("formatted_address", "")
            
            # Extract neighborhood from Google components
            detected = ""
            for comp in result["address_components"]:
                if any(t in comp["types"] for t in ["sublocality", "neighborhood", "political"]):
                    detected = comp["long_name"]
                    break
            
            # Cross-reference
            claimed_norm = claimed_kvartal.lower().replace("гр.", "").strip()
            detected_norm = detected.lower().strip()
            
            # Match if strings overlap (e.g., "Krastova Vada" vs "Manastirski Livadi - East")
            is_match = claimed_norm in detected_norm or detected_norm in claimed_norm
            
            return GeoVerification(
                match=is_match,
                detected_neighborhood=detected,
                confidence=90,
                lat=lat_lng["lat"],
                lng=lat_lng["lng"],
                warning=None if is_match else f"LOCATION FRAUD: Ad claims {claimed_kvartal}, but Vision/Maps identifies {detected}.",
                best_address=formatted_address
            )

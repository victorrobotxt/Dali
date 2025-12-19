import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
from PIL import Image
import os
from src.core.logger import logger

class AIAnalysisSchema(BaseModel):
    address_prediction: str = Field(description="Predicted address or neighborhood based on text/visual landmarks")
    neighborhood: str
    is_atelier: bool = Field(description="True if building style or text suggests non-residential status")
    net_living_area: float
    construction_year: int
    building_type: str = Field(description="Panel, Brick, EPC, or New Construction")
    confidence: int
    visual_red_flags: List[str] = Field(default=[], description="Physical discrepancies like windowless kitchens or office-style windows")

class GeminiService:
    def __init__(self, api_key: str):
        if api_key != "mock-key":
            genai.configure(api_key=api_key)
            # Upgrading to 1.5-flash which supports high-volume vision for low cost
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def analyze_listing_multimodal(self, text: str, image_paths: List[str]) -> dict:
        """
        Implements the Vision AI forensics suggested by Google Cloud.
        Combines raw text with visual evidence from archived listing photos.
        """
        if not self.model:
            return {
                "address_prediction": "Simulated", 
                "confidence": 0, 
                "neighborhood": "Unknown", 
                "is_atelier": False, 
                "net_living_area": 0, 
                "construction_year": 2024,
                "building_type": "Unknown"
            }
        
        # Load and validate images for the Vision API
        visual_inputs = []
        for path in image_paths[:5]: # Use top 5 images to optimize tokens
            if os.path.exists(path):
                try:
                    visual_inputs.append(Image.open(path))
                except Exception as e:
                    logger.warning("image_load_failed", path=path, error=str(e))

        prompt = f"""
        [ROLE] SENIOR REAL ESTATE FORENSIC DETECTIVE (SOFIA, BULGARIA)
        [OBJECTIVE] Extract ground truth from these photos and the listing text.
        
        [TASKS]
        1. Compare visual building style with the described neighborhood (e.g. Panel in Lozenets?).
        2. Inspect 'Atelier' signs: office-style glass, lack of balconies, or commercial ground floors.
        3. Detect 'Space Hacks': kitchens in hallways, beds in windowless rooms.
        4. Look for landmarks/shop signs in the background to pin-point the address.
        
        [LISTING TEXT]
        {text[:4000]}
        """
        
        # Merge text and images into a single multimodal request
        content = [prompt] + visual_inputs
        
        try:
            resp = self.model.generate_content(
                content, 
                generation_config={
                    "response_mime_type": "application/json", 
                    "response_json_schema": AIAnalysisSchema.model_json_schema()
                }
            )
            return AIAnalysisSchema.model_validate_json(resp.text).model_dump()
        except Exception as e:
            logger.error("ai_multimodal_failed", error=str(e))
            # Fallback to a basic structure
            return {"address_prediction": "Error", "neighborhood": "Unknown", "confidence": 0}


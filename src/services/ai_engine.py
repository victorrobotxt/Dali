import google.generativeai as genai
import json
import httpx
import io
from PIL import Image
from typing import Dict, Any, List, Optional
from src.core.config import settings
from pydantic import BaseModel, Field

# --- PYDANTIC SCHEMA ---
class AIAnalysisSchema(BaseModel):
    address_prediction: str = Field(description="The deduced street address")
    confidence: int = Field(ge=0, le=100, description="Confidence score 0-100")
    reasoning_steps: List[str] = Field(description="Bullet points explaining the deduction")
    neighborhood: str = Field(description="Inferred neighborhood")
    is_atelier: bool = Field(description="True if property is legally an Atelier/Studio")

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        if self.api_key != "mock-key":
            genai.configure(api_key=self.api_key)
            self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
            self.model_pro = genai.GenerativeModel('gemini-1.5-pro-vision')
        else:
            self.model_flash = None
            self.model_pro = None

    def _load_prompt(self, raw_text: str) -> str:
        return f"""
        Analyze this real estate listing text.
        Extract the address, neighborhood, and verify if it is an Atelier.
        LISTING TEXT:
        {raw_text}
        """

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        if not self.model_flash:
            return {
                "address_prediction": "Simulated Address", 
                "confidence": 0, 
                "reasoning_steps": ["Mock Mode"],
                "is_atelier": False
            }

        try:
            prompt = self._load_prompt(text)
            response = self.model_flash.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_json_schema": AIAnalysisSchema.model_json_schema()
                }
            )
            structured_data = AIAnalysisSchema.model_validate_json(response.text)
            return structured_data.model_dump()

        except Exception as e:
            print(f"[AI ENGINE] Text Error: {e}")
            return {"error": str(e), "confidence": 0}

    async def analyze_images(self, image_urls: list[str]) -> Dict[str, Any]:
        """
        Downloads images and performs Visual Detective analysis.
        """
        if not self.model_pro:
            return {"confidence": 0, "reasoning": "Vision Mock Mode"}

        images_payload = []
        
        # 1. Download images into memory
        async with httpx.AsyncClient() as client:
            for url in image_urls:
                try:
                    # Filter out empty or invalid URLs
                    if not url or not url.startswith('http'): continue
                    
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        img = Image.open(io.BytesIO(resp.content))
                        images_payload.append(img)
                except Exception as e:
                    print(f"[AI VISION] Download failed for {url}: {e}")

        if not images_payload:
            return {"confidence": 0, "reasoning": "No valid images downloaded"}

        # 2. Prompt Gemini Pro Vision
        prompt = """
        Act as a geospatial detective. Analyze these real estate photos.
        1. Identify any unique landmarks (View from window).
        2. Estimate building era based on facade/balcony style.
        3. Look for street signs or shop names.
        Return JSON with 'facade_era', 'landmarks_detected', and 'estimated_location_confidence'.
        """
        
        try:
            # Gemini Pro Vision handles list of [Prompt, Image, Image...]
            response = self.model_pro.generate_content(
                contents=[prompt, *images_payload],
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[AI VISION ERROR] {e}")
            return {"confidence": 0, "error": str(e)}

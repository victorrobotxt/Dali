from google import genai
from google.genai import types
from typing import Dict, Any, List
import json
import asyncio
from src.core.logger import logger
from src.core.config import settings
from src.schemas import AIAnalysisResult

class GeminiService:
    def __init__(self, api_key: str):
        # New SDK uses an instance-based Client, not global configuration
        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.GEMINI_MODEL

    async def analyze_listing_multimodal(self, text_content: str, image_paths: List[str]) -> AIAnalysisResult:
        # --- OPTIMIZATION: Limit to 3 images max ---
        selected_images = image_paths[:3]
        
        log = logger.bind(model=self.model_name)
        log.info("starting_multimodal_analysis", image_count=len(selected_images), total_found=len(image_paths))
        
        # --- FIX: Define the schema explicitly in the prompt ---
        # This prevents Gemini from wrapping the result in random keys like 'listing_data'
        schema_def = """
        {
          "address_prediction": "str",
          "landmarks": ["str"],
          "neighborhood_match": "Confident/Suspicious/Inconsistent",
          "building_type": "str",
          "is_panel_block": bool,
          "construction_year_est": int,
          "room_count": int,
          "ceiling_height": float,
          "has_storage": bool,
          "heating_inventory": {
            "ac_units": int, "radiators": int, "has_central_heating": bool
          },
          "net_area_sqm": float,
          "act16_due_date": "YYYY-MM or 'Ready'",
          "visual_red_flags": ["str"],
          "light_exposure": "str"
        }
        """
        
        prompt = f"Analyze this listing. Return valid JSON ONLY matching this exact schema:\n{schema_def}\n\nTEXT DATA:\n{text_content}"
        
        uploaded_files = []
        try:
            # 1. Upload files using the new Client
            for path in selected_images:
                # Wrap sync call in asyncio.to_thread to keep app async
                file_ref = await asyncio.to_thread(
                    self.client.files.upload, 
                    file=path
                )
                uploaded_files.append(file_ref)

            # 2. Configure for JSON
            # We explicitly tell Gemini to return JSON
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

            # 3. Generate Content
            # The new SDK accepts a list of [prompt, file_ref, file_ref...]
            contents = [prompt, *uploaded_files]
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # 4. Cleanup remote files immediately
            # (Crucial to avoid hitting storage quotas on Google's side)
            for f in uploaded_files:
                await asyncio.to_thread(self.client.files.delete, name=f.name)

            # 5. Parse JSON
            # Since we requested MIME type application/json, response.text is clean JSON
            data = json.loads(response.text)
            
            # STRICT VALIDATION via Pydantic
            return AIAnalysisResult(**data)
            
        except Exception as e:
            log.error("ai_analysis_failed", error=str(e))
            # Fallback to empty validated object to prevent pipeline crash
            return AIAnalysisResult(address_prediction="Unknown", landmarks=[])
        
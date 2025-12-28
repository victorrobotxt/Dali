import google.generativeai as genai
from typing import Dict, Any, List
import json
import time
from src.core.logger import logger
from src.core.config import settings

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use the config value (defaults to gemini-3.0-flash)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def analyze_listing_multimodal(self, text_content: str, image_paths: List[str]) -> Dict[str, Any]:
        """
        Analyzes listing text + images to find discrepancies and specific visual risks.
        """
        logger.info(f"Analyzing listing with {settings.GEMINI_MODEL}...")
        
        # Construct the prompt for the Digital Attorney
        prompt = f"""
        You are an expert Real Estate Forensic Auditor in Sofia, Bulgaria.
        Analyze this listing text and the attached images.
        
        TEXT:
        {text_content}
        
        TASK:
        1. Extract the likely address (Street, Number, Neighborhood).
        2. Estimate construction year based on visual style (Panel vs Brick).
        3. Detect "Atelier" status traps (North facing, small windows).
        4. Identify "Visual Lies": Does the text say "Luxury" but images show "Panel"?
        
        Return JSON only:
        {{
            "address_prediction": "str",
            "construction_year_est": int,
            "is_panel_block": bool,
            "is_atelier_trap": bool,
            "visual_defects": ["str"],
            "landmarks": ["str"]
        }}
        """
        
        try:
            # Prepare parts: Text + Images
            parts = [prompt]
            
            # TODO: Append actual image data here in production
            
            response = self.model.generate_content(parts)
            cleaned_text = response.text.replace('', '')
            return json.loads(cleaned_text)
            
        except Exception as e:
            logger.error(f"AI Analysis Failed: {e}")
            return {
                "address_prediction": "Unknown",
                "error": str(e)
            }

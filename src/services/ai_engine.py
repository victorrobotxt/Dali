import google.generativeai as genai
import json
import os
from typing import Dict, Any, List
from src.core.config import settings

class AIEngineInterface:
    async def analyze_listing(self, text: str, images: List[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

class GeminiService(AIEngineInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.prompt_path = "prompts/detective_prompt_v1.md"
        
        # Configure Gemini if Key is real
        if self.api_key != "mock-key":
            genai.configure(api_key=self.api_key)
            # Tier 1: Fast & Cheap (Text Only) - approx /data/data/com.termux/files/usr/bin/bash.04/M tokens
            self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
            # Tier 2: Expensive (Multimodal / Vision) - approx /data/data/com.termux/files/usr/bin/bash.22/M tokens
            self.model_pro = genai.GenerativeModel('gemini-1.5-pro-vision')
        else:
            self.model_flash = None
            self.model_pro = None

    def _load_prompt(self, raw_text: str) -> str:
        """Loads the system prompt and injects the raw listing text."""
        # Fallback for Docker/Path issues
        if not os.path.exists(self.prompt_path):
            return f"Analyze this real estate listing and return JSON: {raw_text}"
            
        with open(self.prompt_path, "r") as f:
            template = f.read()
            
        # Inject the raw text into the {text_raw} slot defined in prompts/detective_prompt_v1.md
        # Defaulting neighborhood to 'Unknown' if not provided by scraper yet
        return template.replace("{text_raw}", raw_text).replace("{neighborhood}", "Unknown")

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Orchestrates the Tier 1 Analysis.
        Maps to 'Analysis Tier 1 (Cheap)' in ARCHITECTURE.md.
        """
        if not self.model_flash:
            # Simulation Response for Dev Mode
            return {
                "address_prediction": "Simulated Address", 
                "confidence": 0.0, 
                "reasoning": "Mock Mode Active"
            }

        try:
            prompt = self._load_prompt(text)
            
            # Force JSON mode for structured data extraction
            response = self.model_flash.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse the JSON output
            result = json.loads(response.text)
            
            # Ensure confidence is an integer for the Logic Gate
            if "confidence" not in result:
                result["confidence"] = 0
                
            return result

        except Exception as e:
            print(f"[AI ENGINE] Error: {e}")
            return {"error": str(e), "confidence": 0.0}

    async def analyze_images(self, image_urls: list[str]) -> Dict[str, Any]:
        # Placeholder for Tier 2 Logic
        return {"building_id": "UNKNOWN", "risk_factors": ["Vision implementation pending"]}

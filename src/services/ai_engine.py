import google.generativeai as genai
import json
import os
from typing import Dict, Any, List, Optional
from src.core.config import settings
from pydantic import BaseModel, Field

# --- PYDANTIC SCHEMA FOR GUARDRAILS ---
class AIAnalysisSchema(BaseModel):
    """
    Enforces structure on the LLM output.
    Ref: Google GenAI SDK Docs
    """
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
        # Simplified prompt construction, relying on Schema for formatting
        return f"""
        Analyze this real estate listing text. Extract the address, neighborhood, and verify if it is an Atelier.
        
        LISTING TEXT:
        {raw_text}
        """

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Uses Structured Outputs (JSON Schema) to guarantee valid data.
        """
        if not self.model_flash:
            return {
                "address_prediction": "Simulated Address", 
                "confidence": 0, 
                "reasoning_steps": ["Mock Mode"],
                "is_atelier": False
            }

        try:
            prompt = self._load_prompt(text)
            
            # --- GUARDRAIL IMPLEMENTATION ---
            # We pass the Pydantic schema to the API configuration
            response = self.model_flash.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_json_schema": AIAnalysisSchema.model_json_schema() #
                }
            )
            
            # Validate response against our model
            # This ensures we never crash downstream due to malformed keys
            structured_data = AIAnalysisSchema.model_validate_json(response.text)
            
            return structured_data.model_dump()

        except Exception as e:
            print(f"[AI ENGINE] Error: {e}")
            return {"error": str(e), "confidence": 0}

    async def analyze_images(self, image_urls: list[str]) -> Dict[str, Any]:
        # Placeholder
        return {"confidence": 0, "reasoning": "Vision Not Implemented"}

import google.generativeai as genai
from pydantic import BaseModel, Field
from src.core.config import settings

class AIAnalysisSchema(BaseModel):
    address_prediction: str = Field(description="Extracted address")
    confidence: int = Field(description="0-100 score")
    neighborhood: str = Field(description="Rayon name")
    is_atelier: bool = Field(description="Legal status is atelier")
    net_living_area: float = Field(description="Usable square meters")
    construction_year: int = Field(description="Finish year")

class GeminiService:
    def __init__(self, api_key: str):
        if api_key != "mock-key":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else: self.model = None

    async def analyze_text(self, text: str) -> dict:
        if not self.model: return {"address_prediction": "Mock", "confidence": 0, "neighborhood": "Unknown", "is_atelier": False, "net_living_area": 0, "construction_year": 2024}
        prompt = f"Perform forensic property analysis on: {text}"
        resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "response_json_schema": AIAnalysisSchema.model_json_schema()})
        return AIAnalysisSchema.model_validate_json(resp.text).model_dump()

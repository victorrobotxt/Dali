import google.generativeai as genai
from pydantic import BaseModel, Field
from src.core.config import settings

class AIAnalysisSchema(BaseModel):
    address_prediction: str = Field(description="Deduced address")
    confidence: int = Field(description="Confidence score")
    neighborhood: str = Field(description="Neighborhood name")
    is_atelier: bool = Field(description="Is it an Atelier?")
    net_living_area: float = Field(description="Extracted Net usable area in sq.m")
    construction_stage: str = Field(description="Akt 14, 15, or 16")
    construction_year: int = Field(description="Estimated or stated building finish year")
    exposure: str = Field(description="Exposure like Sever, Yug, Iztok, Zapad")

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key != "mock-key":
            genai.configure(api_key=self.api_key)
            self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model_flash = None

    async def analyze_text(self, text: str) -> dict:
        if not self.model_flash:
            return {"address_prediction": "Mock", "confidence": 0, "neighborhood": "Unknown", 
                    "is_atelier": False, "net_living_area": 0, "construction_stage": "Unknown", 
                    "construction_year": 2024, "exposure": "Unknown"}
        
        prompt = f"Perform forensic analysis on this property ad and return JSON schema: {text}"
        response = self.model_flash.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json", "response_json_schema": AIAnalysisSchema.model_json_schema()}
        )
        return AIAnalysisSchema.model_validate_json(response.text).model_dump()

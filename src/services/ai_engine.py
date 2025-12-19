import google.generativeai as genai
from pydantic import BaseModel, Field

class AIAnalysisSchema(BaseModel):
    address_prediction: str
    neighborhood: str
    is_atelier: bool
    net_living_area: float
    construction_year: int
    confidence: int

class GeminiService:
    def __init__(self, api_key: str):
        if api_key != "mock-key":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else: self.model = None

    async def analyze_text(self, text: str) -> dict:
        if not self.model: return {"address_prediction": "Simulated", "confidence": 0, "neighborhood": "Unknown", "is_atelier": False, "net_living_area": 0, "construction_year": 2024}
        
        mandate = """
        [ROLE] APEX PREDATOR REAL ESTATE ANALYST.
        [OBJECTIVE] Extract forensic ground truth from listing. 
        [RULES] Compare price vs neighborhood. Detect 'Ателие' (workspace) status. 
        Identify 'Net Living Area' (чиста площ). 
        """
        prompt = f"{mandate}\n\nListing Data: {text[:5000]}"
        resp = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "response_json_schema": AIAnalysisSchema.model_json_schema()})
        return AIAnalysisSchema.model_validate_json(resp.text).model_dump()

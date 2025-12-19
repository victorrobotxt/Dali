import google.generativeai as genai
from PIL import Image
import os
from src.core.logger import logger
from src.schemas import AIAnalysisResult

class GeminiService:
    def __init__(self, api_key: str):
        if api_key != "mock-key":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def analyze_listing_multimodal(self, text: str, image_paths: List[str]) -> dict:
        if not self.model:
            return {"address_prediction": "Mock", "confidence_score": 0, "neighborhood_match": "Unverified"}
        
        visual_inputs = []
        for path in image_paths[:8]:
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((1024, 1024))
                    visual_inputs.append(img)
                except Exception:
                    continue

        with open("prompts/detective_prompt_v1.md", "r") as f:
            system_prompt = f.read()

        content = [f"{system_prompt}\n\n[TEXT]:\n{text[:4000]}", *visual_inputs]
        
        try:
            resp = self.model.generate_content(
                content, 
                generation_config={
                    "response_mime_type": "application/json", 
                    "response_json_schema": AIAnalysisResult.model_json_schema()
                }
            )
            return AIAnalysisResult.model_validate_json(resp.text).model_dump()
        except Exception as e:
            logger.error("ai_failed", error=str(e))
            return {"address_prediction": "Error", "confidence_score": 0}

import google.generativeai as genai
from typing import Dict, Any, List
import json
import asyncio
from src.core.logger import logger
from src.core.config import settings
from src.schemas import AIAnalysisResult

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def analyze_listing_multimodal(self, text_content: str, image_paths: List[str]) -> AIAnalysisResult:
        log = logger.bind(model=settings.GEMINI_MODEL)
        log.info("starting_multimodal_analysis", image_count=len(image_paths))
        
        prompt = f"Analyze this listing text and images. Return JSON ONLY matching our forensic schema.\nTEXT:\n{text_content}"
        
        uploaded_files = []
        try:
            for path in image_paths:
                file_ref = await asyncio.to_thread(genai.upload_file, path=path)
                uploaded_files.append(file_ref)

            parts = [prompt, *uploaded_files]
            response = await asyncio.to_thread(self.model.generate_content, parts)
            
            # Cleanup remote files
            for f in uploaded_files:
                await asyncio.to_thread(genai.delete_file, f.name)

            # JSON Sanitization
            raw_json = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_json)
            
            # STRICT VALIDATION
            return AIAnalysisResult(**data)
            
        except Exception as e:
            log.error("ai_analysis_failed", error=str(e))
            # Fallback to empty validated object
            return AIAnalysisResult(address_prediction="Unknown", landmarks=[])

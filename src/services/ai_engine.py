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
        log = logger.bind(model=self.model_name)
        log.info("starting_multimodal_analysis", image_count=len(image_paths))
        
        prompt = f"Analyze this listing text and images. Return JSON ONLY matching our forensic schema.\nTEXT:\n{text_content}"
        
        uploaded_files = []
        try:
            # 1. Upload files using the new Client
            for path in image_paths:
                # Wrap sync call in asyncio.to_thread to keep app async
                file_ref = await asyncio.to_thread(
                    self.client.files.upload, 
                    file=path
                )
                uploaded_files.append(file_ref)

            # 2. Prepare content and configuration
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
            
            # 4. Cleanup remote files
            for f in uploaded_files:
                await asyncio.to_thread(self.client.files.delete, name=f.name)

            # 5. Parse JSON
            # Since we requested MIME type application/json, we don't need manual stripping
            # response.text should be clean JSON.
            data = json.loads(response.text)
            
            # STRICT VALIDATION via Pydantic
            return AIAnalysisResult(**data)
            
        except Exception as e:
            log.error("ai_analysis_failed", error=str(e))
            # Fallback to empty validated object
            return AIAnalysisResult(address_prediction="Unknown", landmarks=[])
        
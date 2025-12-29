import google.generativeai as genai
from typing import Dict, Any, List
import json
import asyncio
from src.core.logger import logger
from src.core.config import settings

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use the config value (defaults to gemini-3.0-flash)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def analyze_listing_multimodal(self, text_content: str, image_paths: List[str]) -> Dict[str, Any]:
        """
        Analyzes listing text + images using the Gemini File API.
        Uploads images -> Analyzes -> Cleans up remote files.
        """
        log = logger.bind(model=settings.GEMINI_MODEL)
        log.info("starting_multimodal_analysis", image_count=len(image_paths))
        
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
        5. Heating Inventory: Count visible AC units and Radiators.

        Return JSON only:
        {{
            "address_prediction": "str",
            "construction_year_est": int,
            "is_panel_block": bool,
            "is_atelier_trap": bool,
            "visual_defects": ["str"],
            "landmarks": ["str"],
            "heating_inventory": {{
                "ac_units": int,
                "radiators": int
            }}
        }}
        """
        
        uploaded_files = []
        
        try:
            # A. UPLOAD PHASE
            # We use asyncio.to_thread because the Google SDK upload is blocking I/O
            for path in image_paths:
                try:
                    log.debug("uploading_image", path=path)
                    # Upload using the File API (handles < 20MB constraint of inline)
                    file_ref = await asyncio.to_thread(genai.upload_file, path=path)
                    uploaded_files.append(file_ref)
                except Exception as upload_err:
                    log.error("image_upload_failed", path=path, error=str(upload_err))

            if not uploaded_files:
                log.warning("no_images_uploaded_proceeding_text_only")

            # B. INFERENCE PHASE
            # Combine prompt + file handles
            parts = [prompt, *uploaded_files]
            
            response = await asyncio.to_thread(self.model.generate_content, parts)
            
            # C. CLEANUP PHASE
            # Delete files from Google's servers immediately after use
            for f in uploaded_files:
                try:
                    await asyncio.to_thread(genai.delete_file, f.name)
                except Exception as cleanup_err:
                    log.warning("cleanup_failed", file=f.name, error=str(cleanup_err))

            # D. PARSING
            cleaned_text = response.text.replace('```json', '').replace('```', '')
            return json.loads(cleaned_text)
            
        except Exception as e:
            log.error("ai_analysis_failed_fatal", error=str(e))
            return {
                "address_prediction": "Unknown",
                "error": str(e)
            }

from abc import ABC, abstractmethod
from typing import Dict, Any

class AIEngineInterface(ABC):
    """
    Abstract Base Class ensuring our AI implementation is decoupled from the vendor.
    If we switch from Gemini to OpenAI later, we only change the implementation, not the logic.
    """
    
    @abstractmethod
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def analyze_images(self, image_urls: list[str]) -> Dict[str, Any]:
        pass

class GeminiService(AIEngineInterface):
    """
    Concrete implementation utilizing Google Gemini APIs.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: Initialize Gemini Client
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # Placeholder for Gemini Flash Logic ($0.04 Tier)
        print(f"DEBUG: Analyze text with Gemini Flash: {text[:50]}...")
        return {"address_found": False, "confidence": 0.0}

    async def analyze_images(self, image_urls: list[str]) -> Dict[str, Any]:
        # Placeholder for Gemini Pro Vision Logic ($0.22 Tier)
        print(f"DEBUG: Analyze {len(image_urls)} images with Gemini Pro Vision...")
        return {"building_id": "UNKNOWN", "risk_factors": []}

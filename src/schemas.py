from pydantic import BaseModel, Field, condecimal
from decimal import Decimal
from typing import List, Optional, Literal

class ScrapedListing(BaseModel):
    source_url: str
    raw_text: str
    price_predicted: condecimal(max_digits=12, decimal_places=2) 
    
    # PRECISION FIX: Area is now strictly Decimal
    area_sqm: condecimal(max_digits=10, decimal_places=2)
    
    image_urls: List[str] = []
    
    class Config:
        json_encoders = {Decimal: str}

class AIAnalysisResult(BaseModel):
    address_prediction: str
    neighborhood: str
    is_atelier: bool
    net_living_area: float
    construction_year: int
    confidence_score: int = Field(default=0, ge=0, le=100)

class RegistryCheck(BaseModel):
    registry_status: Literal["LIVE", "OFFLINE", "ERROR"] = "LIVE"
    details: str = ""
    is_risk_detected: bool = False
    checked: bool = False

class CadastreData(BaseModel):
    official_area: float = 0.0
    cadastre_id: Optional[str] = None
    status: Literal["LIVE", "OFFLINE", "NOT_FOUND", "ERROR"] = "NOT_FOUND"
    address_found: Optional[str] = None

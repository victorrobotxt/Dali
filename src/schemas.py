from pydantic import BaseModel, Field, condecimal
from decimal import Decimal
from typing import List, Optional, Literal

class ScrapedListing(BaseModel):
    source_url: str
    raw_text: str
    # Precision Fix: Ensure financial math uses Decimal
    price_predicted: condecimal(max_digits=12, decimal_places=2) 
    area_sqm: float
    image_urls: List[str] = []
    
    class Config:
        # Ensures Decimal objects serialize to JSON strings correctly
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

class RiskAssessment(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    verdict: Literal["CLEAN", "WARNING", "CRITICAL", "FATAL"] = "CLEAN"
    flags: List[str] = []
    is_fatal: bool = False

class ConsolidatedAudit(BaseModel):
    scraped: ScrapedListing
    ai: AIAnalysisResult
    cadastre: CadastreData
    compliance: RegistryCheck
    city_risk: RegistryCheck
    risk_assessment: RiskAssessment

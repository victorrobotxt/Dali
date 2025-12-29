from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional, Literal

class ScrapedListing(BaseModel):
    source_url: str
    raw_text: str
    price_predicted: Decimal
    area_sqm: Decimal
    neighborhood: str 
    image_urls: List[str] = []
    
    # New Forensic Fields
    is_vat_excluded: bool = False
    is_direct_owner: bool = False
    price_correction_note: Optional[str] = None

class HeatingInventory(BaseModel):
    ac_units: int = 0
    radiators: int = 0
    has_central_heating: bool = False

class AIAnalysisResult(BaseModel):
    address_prediction: str
    landmarks: List[str] = []
    neighborhood_match: str
    building_type: str
    heating_inventory: HeatingInventory
    visual_red_flags: List[str] = []
    light_exposure: str
    confidence_score: int = Field(default=0, ge=0, le=100)
    
    # New Valuation Fields
    net_area_sqm: float = 0.0
    act16_due_date: Optional[str] = None # e.g. "2027-04"
    is_panel_block: bool = False

class GeoVerification(BaseModel):
    match: bool
    detected_neighborhood: str
    confidence: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    warning: Optional[str] = None
    best_address: Optional[str] = None

class CadastreData(BaseModel):
    official_area: float = 0.0
    cadastre_id: Optional[str] = None
    status: Literal["LIVE", "OFFLINE", "NOT_FOUND", "ERROR"] = "NOT_FOUND"
    address_found: Optional[str] = None

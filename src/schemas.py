from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import List, Optional, Literal

class ScrapedListing(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    
    source_url: str
    raw_text: str
    price_predicted: Decimal
    area_sqm: Decimal
    neighborhood: str 
    image_urls: List[str] = Field(default_factory=list)
    is_vat_excluded: bool = False
    is_direct_owner: bool = False
    price_correction_note: Optional[str] = None

class HeatingInventory(BaseModel):
    ac_units: int = 0
    radiators: int = 0
    has_central_heating: bool = False

class AIAnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    address_prediction: str
    landmarks: List[str] = Field(default_factory=list)
    neighborhood_match: str = "Unknown"
    building_type: str = "Unknown"
    is_panel_block: bool = False
    heating_inventory: HeatingInventory = Field(default_factory=HeatingInventory)
    net_area_sqm: float = 0.0
    act16_due_date: Optional[str] = None
    visual_red_flags: List[str] = Field(default_factory=list)
    light_exposure: Optional[str] = None
    confidence_score: int = 0

class GeoVerification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    match: bool
    detected_neighborhood: str
    confidence: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    warning: Optional[str] = None
    best_address: Optional[str] = None

class CadastreData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    official_area: float = 0.0
    cadastre_id: Optional[str] = None
    status: Literal["LIVE", "OFFLINE", "NOT_FOUND", "ERROR"] = "NOT_FOUND"
    address_found: Optional[str] = None

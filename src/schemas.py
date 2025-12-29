from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Literal

@dataclass
class ScrapedListing:
    source_url: str
    raw_text: str
    price_predicted: Decimal
    area_sqm: Decimal
    neighborhood: str 
    image_urls: List[str] = field(default_factory=list)
    
    # Forensic Fields
    is_vat_excluded: bool = False
    is_direct_owner: bool = False
    price_correction_note: Optional[str] = None
    
    # Helper to mimic Pydantic's .model_dump()
    def model_dump(self):
        return {
            k: (float(v) if isinstance(v, Decimal) else v) 
            for k, v in self.__dict__.items()
        }

@dataclass
class HeatingInventory:
    ac_units: int = 0
    radiators: int = 0
    has_central_heating: bool = False

@dataclass
class AIAnalysisResult:
    address_prediction: str
    neighborhood_match: str
    building_type: str
    heating_inventory: HeatingInventory
    light_exposure: str
    landmarks: List[str] = field(default_factory=list)
    visual_red_flags: List[str] = field(default_factory=list)
    confidence_score: int = 0
    
    # Valuation Fields
    net_area_sqm: float = 0.0
    act16_due_date: Optional[str] = None
    is_panel_block: bool = False
    
    def get(self, key, default=None):
        return getattr(self, key, default)

@dataclass
class GeoVerification:
    match: bool
    detected_neighborhood: str
    confidence: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    warning: Optional[str] = None
    best_address: Optional[str] = None
    
    def model_dump(self):
        return self.__dict__

@dataclass
class CadastreData:
    official_area: float = 0.0
    cadastre_id: Optional[str] = None
    status: Literal["LIVE", "OFFLINE", "NOT_FOUND", "ERROR"] = "NOT_FOUND"
    address_found: Optional[str] = None
    
    def model_dump(self):
        return self.__dict__

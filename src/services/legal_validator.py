from typing import Dict, List, Optional
from src.core.legal_constants import LawOrd7, LawZUT
from src.core.logger import logger

class LegalValidator:
    def __init__(self):
        self.log = logger.bind(service="legal_validator")

    def validate_dwelling_status(self, 
                                 height: float, 
                                 exposures: List[str], 
                                 has_storage: bool, 
                                 room_count: int) -> Dict[str, any]:
        """
        Determines if a property can legally be sold as a 'Dwelling' (Apartment)
        or if it is effectively an 'Atelier' (Office/Studio).
        """
        flags = []
        is_atelier = False
        
        # 1. Height Check (The "Low Ceiling" Trap)
        if height > 0 and height < LawOrd7.MIN_HEIGHT_LIVING_ROOM:
            msg = f"ILLEGAL: Ceiling height {height}m < {LawOrd7.MIN_HEIGHT_LIVING_ROOM}m. Cannot be 'Dwelling'."
            flags.append(msg)
            is_atelier = True

        # 2. Exposure Check (The "North Face" Trap)
        # Normalize inputs to uppercase
        norm_exposures = [e.upper() for e in exposures]
        
        # If it's a 1-room unit (Studio), it cannot be entirely North
        if room_count == 1:
            # Check if ALL exposures are bad
            if all(exp in LawOrd7.FORBIDDEN_EXPOSURES for exp in norm_exposures):
                msg = f"ILLEGAL: Single-room dwelling cannot face purely {norm_exposures}. Violation of Ord.7 Art.78."
                flags.append(msg)
                is_atelier = True

        # 3. Storage Check
        if not has_storage:
            msg = "NON-COMPLIANT: Missing mandatory storage (Basement/Attic/Closet). Violation of Ord.7 Art.108."
            flags.append(msg)
            # This alone doesn't make it an Atelier, but it makes it "Not a valid Dwelling"
            
        return {
            "status": "ATELIER" if is_atelier else "DWELLING_COMPLIANT",
            "is_trap": is_atelier,
            "legal_flags": flags
        }

    def audit_area_efficiency(self, 
                              advertised_sqm: float, 
                              net_sqm: float, 
                              balcony_sqm: float) -> Dict[str, any]:
        """
        Calculates the 'Real Living Density' to expose Terrace Dilution.
        """
        if advertised_sqm <= 0: return {}
        
        # ZUT Rule: Balconies are 100% of their area in the "Gross" size.
        # We calculate the "Efficiency Ratio" = (Net - Balcony) / Advertised
        
        # If net_sqm is not provided or 0, we can't calculate efficiency
        if net_sqm <= 0:
             return {
                "efficiency_index": 0.0,
                "flags": ["WARN: Net area unknown. Cannot calculate efficiency."]
             }

        efficiency_index = net_sqm / advertised_sqm
        
        flags = []
        # If you pay for 100m but get <60m of indoor space -> SCAM.
        if efficiency_index < 0.60:
            flags.append(f"VALUATION WARNING: Terrace Dilution. Efficiency {efficiency_index:.0%} < 60%.")
            
        return {
            "efficiency_index": round(efficiency_index, 3),
            "true_indoor_sqm": net_sqm,
            "flags": flags
        }

    def check_habitability(self, floor_count: int, has_elevator: bool) -> Dict[str, any]:
        """
        Checks Act 16 prerequisites.
        """
        flags = []
        fatal = False
        
        # ZUT Art. 169
        if floor_count > LawZUT.ELEVATOR_MANDATORY_FLOORS and not has_elevator:
            msg = f"CRITICAL: Building has {floor_count} floors but NO ELEVATOR. Act 16 impossible."
            flags.append(msg)
            fatal = True
            
        return {"act16_blockers": flags, "is_fatal": fatal}

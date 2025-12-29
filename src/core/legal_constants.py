from typing import List

class LawOrd7:
    """
    Ordinance No. 7 on the Rules and Norms for the Design of Territories and Zones.
    """
    # Art. 72 (1) & (2) - Ceiling Heights
    MIN_HEIGHT_LIVING_ROOM: float = 2.60  # Meters (Absolute minimum for 'Living' status)
    MIN_HEIGHT_KITCHEN_DINING: float = 2.50
    MIN_HEIGHT_GROUND_FLOOR: float = 3.20 # Often shops/ateliers

    # Art. 78 - Exposure Rules (The "North Face" Trap)
    # A dwelling must have at least one room with "favorable" exposure.
    # Entirely Northern exposure is FORBIDDEN for 1-room apartments.
    FORBIDDEN_EXPOSURES: List[str] = ["NORTH", "NORTH-EAST", "NORTH-WEST"]
    
    # Art. 108 - Mandatory Storage
    REQUIRES_STORAGE: bool = True  # Basement, Attic, or Closet inside the unit is MANDATORY
    
    # Art. 110 - Atelier vs Dwelling
    # Ateliers are for "individual creative activity" and do not strictly require 
    # the favorable exposure or the 2.60m height (can be lower in parts).

class LawZUT:
    """
    Spatial Planning Act (ZUT).
    """
    # Art. 169 - Accessibility & Transport
    ELEVATOR_MANDATORY_FLOORS: int = 5 # If > 5 floors, Elevator is non-negotiable for Act 16.

    # Area Calculations (Supplement to Art. 17)
    BALCONY_AREA_WEIGHT: float = 1.00 # Balconies count 100% to Built-up Area (The Dilution Trap)
    ATTIC_AREA_CUTOFF: float = 1.50   # Area below 1.50m height is legally 0 sq.m.

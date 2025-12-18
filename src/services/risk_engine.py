from typing import Dict, Any, List

class RiskEngine:
    """
    Translates architectural and legal discrepancies into a 0-100 Risk Score.
    """
    def calculate_score(self, advertised_data: Dict, ai_insights: Dict) -> Dict[str, Any]:
        score = 0
        flags = []

        # 1. Legal Status Check (Atelier vs Apartment)
        raw_text = advertised_data.get("raw_text", "").upper()
        if "АТЕЛИЕ" in raw_text or "ATELIER" in raw_text:
            score += 30
            flags.append("LEGAL_STATUS_RISK: Property listed as Atelier (Possible industrial status)")

        # 2. Floor Logic
        if "ПОСЛЕДЕН" in raw_text or "TOP FLOOR" in raw_text:
            score += 15
            flags.append("MAINTENANCE_RISK: Top floor (Higher probability of roof leaks)")
        
        if "ПЪРВИ" in raw_text or "GROUND" in raw_text:
            score += 10
            flags.append("SECURITY_RISK: Ground floor/Low elevation")

        # 3. High Value Verification
        if advertised_data.get("price_predicted", 0) > 300000:
            score += 5
            flags.append("FINANCIAL: High-ticket verification required")

        return {
            "score": min(score, 100),
            "flags": flags
        }

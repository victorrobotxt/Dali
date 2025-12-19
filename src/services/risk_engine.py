from typing import Dict, Any, List, Optional

class RiskEngine:
    def calculate_score(self, advertised_data: Dict, ai_insights: Dict, cadastre_area: Optional[float] = None) -> Dict[str, Any]:
        score = 0
        flags = []
        
        raw_text = advertised_data.get("raw_text", "").upper()
        advertised_area = advertised_data.get("area", 0.0)

        # 1. LEGAL STATUS (Atelier)
        # Using the AI's structured output if available, else fallback to text
        is_atelier = ai_insights.get("is_atelier", False)
        if is_atelier or "АТЕЛИЕ" in raw_text or "ATELIER" in raw_text:
            score += 30
            flags.append("LEGAL_STATUS_RISK: Property is Atelier (Industrial/Non-residential status)")

        # 2. AREA MATH (Advertised vs Cadastre)
        # The Gap fix: Check if advertised area is suspicious compared to official records
        if cadastre_area and advertised_area > 0:
            if advertised_area > (cadastre_area * 1.15): # 15% tolerance
                score += 20
                flags.append(f"AREA_DISCREPANCY: Advertised ({advertised_area}) > Cadastre ({cadastre_area})")

        # 3. FLOOR RISKS
        if "ПОСЛЕДЕН" in raw_text or "TOP FLOOR" in raw_text:
            score += 15
            flags.append("MAINTENANCE_RISK: Top floor")
        
        if "ПЪРВИ" in raw_text or "GROUND" in raw_text:
            score += 10
            flags.append("SECURITY_RISK: Ground floor")

        # 4. PRICE ANOMALY
        if advertised_data.get("price_predicted", 0) > 300000:
            score += 5
            flags.append("FINANCIAL: High-ticket verification required")

        return {
            "score": min(score, 100),
            "flags": flags
        }

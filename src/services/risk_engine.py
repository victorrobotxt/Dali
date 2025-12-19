from typing import Dict, Any, Optional

class RiskEngine:
    def calculate_score(self, advertised: Dict, ai: Dict, cadastre_area: Optional[float] = None) -> Dict[str, Any]:
        score = 0
        flags = []
        is_fatal = False
        
        # 1. LEGAL / ATELIER
        if ai.get("is_atelier", False):
            score += 40
            flags.append("LEGAL: Property registered as Atelier (non-residential).")

        # 2. AREA SQUEEZING
        adv_area = advertised.get("area", 0)
        if cadastre_area and adv_area > 0:
            diff = (adv_area - cadastre_area) / cadastre_area
            if diff > 0.20:
                score += 30
                flags.append(f"AREA: Advertised area is {diff:.1%} larger than Cadastre record.")

        # 3. HEATING / UTILITIES
        vision = ai.get("vision_insights", {})
        heating = vision.get("heating_source", "unknown").lower()
        if "electricity" in heating or "air conditioning" in heating:
            score += 5
            flags.append("COST: Heating is electric (expected higher winter bills).")
        
        # 4. FATAL FLAGS (Override)
        raw_text = advertised.get("raw_text", "").lower()
        fatal_keywords = ["искова молба", "съдебен", "litigation", "distraint", "чси"]
        if any(x in raw_text for x in fatal_keywords):
            score = 100
            is_fatal = True
            flags.append("CRITICAL: Fatal legal defect detected (Litigation/Distraint).")

        # Normalize score to max 100
        final_score = 100 if is_fatal else min(score, 100)

        return {"score": final_score, "flags": flags}

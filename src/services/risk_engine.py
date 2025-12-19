from typing import Dict, Any

class RiskEngine:
    def calculate_score_v2(self, data: Dict) -> Dict[str, Any]:
        """
        Consolidated Risk Calculation using all 3 sources.
        """
        score = 0
        flags = []
        is_fatal = False
        
        ai = data.get("ai", {})
        cad = data.get("cadastre") or {}
        comp = data.get("compliance", {})
        risk = data.get("city_risk", {})
        
        # 1. EXPROPRIATION (The Nuke)
        if risk.get("is_expropriated"):
            score = 100
            is_fatal = True
            flags.append("CRITICAL: Property is listed for EXPROPRIATION (Seizure).")

        # 2. ACT 16 (The Ghost)
        # Only penalize if we actually checked and found nothing, and building year implies we should have it
        if comp.get("checked") and not comp.get("has_act16"):
            # If AI says it's old (pre-2000), missing record might just mean digitization lag.
            # If AI says it's new (post-2010), missing record is suspicious.
            year = ai.get("construction_year", 0)
            if year > 2010:
                score += 50
                flags.append("HIGH RISK: No Commissioning Certificate (Act 16) found for modern building.")
            else:
                score += 10
                flags.append("WARN: Act 16 not digitized or missing.")

        # 3. AREA FRAUD (The Squeeze)
        adv_area = data["scraped"].get("area", 0)
        off_area = cad.get("official_area", 0)
        
        if adv_area > 0 and off_area > 0:
            diff_ratio = (adv_area - off_area) / off_area
            if diff_ratio > 0.25: # >25% discrepancy
                score += 30
                flags.append(f"SCAM: Advertised area {adv_area}m is {diff_ratio:.1%} larger than Official {off_area}m.")
        
        # 4. LEGAL / ATELIER
        if ai.get("is_atelier", False):
            score += 25
            flags.append("LEGAL: Atelier status (Non-residential).")

        final_score = 100 if is_fatal else min(score, 100)
        return {"score": final_score, "flags": flags, "is_fatal": is_fatal}

    # Legacy V1 (Keep for backward compat if needed)
    def calculate_score(self, advertised, ai, cadastre_area=None):
        return self.calculate_score_v2({"scraped": advertised, "ai": ai, "cadastre": {"official_area": cadastre_area}})

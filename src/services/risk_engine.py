from typing import Dict, Any

class RiskEngine:
    def calculate_score_v2(self, data: Dict) -> Dict[str, Any]:
        score = 0
        flags = []
        is_fatal = False
        
        scraped = data.get("scraped", {})
        ai = data.get("ai", {})
        cad = data.get("cadastre") or {}
        comp = data.get("compliance", {})
        risk = data.get("city_risk", {})
        geo = data.get("geo", {})
        
        # 1. EXPROPRIATION (The Nuke)
        if risk.get("is_expropriated"):
            score = 100
            is_fatal = True
            flags.append("CRITICAL: Property is listed for EXPROPRIATION (Municipal Seizure).")

        # 2. LOCATION INTEGRITY
        if geo and not geo.get("match"):
            score += 40
            flags.append(geo.get("warning", "Location Fraud Detected."))

        # 3. CONSTRUCTION MATURITY (ACT 16 Logic)
        # Penalize if building is modern (>2010) but no cert is found in the registry
        est_year = ai.get("construction_year_est", 0)
        if est_year > 2010 and not comp.get("has_act16") and comp.get("checked"):
            score += 50
            flags.append(f"HIGH RISK: Building estimated from {est_year}, but no Act 16 found in NAG records.")

        # 4. INFRASTRUCTURE MISMATCH (TEC/Radiator Logic)
        raw_text = scraped.get("raw_text", "").upper()
        if "ТЕЦ" in raw_text or "ЦЕНТРАЛНО ОТОПЛЕНИЕ" in raw_text:
            inventory = ai.get("heating_inventory", {})
            if inventory.get("radiators", 0) == 0:
                score += 15
                flags.append("WARN: Listing claims Central Heating (TEC), but 0 radiators detected visually.")

        # 5. AREA FRAUD
        adv_area = float(scraped.get("area_sqm", 0))
        off_area = float(cad.get("official_area", 0))
        if adv_area > 0 and off_area > 0:
            diff_ratio = (adv_area - off_area) / off_area
            if diff_ratio > 0.25:
                score += 30
                flags.append(f"SCAM: Advertised area {adv_area}m is {diff_ratio:.1%} larger than Official {off_area}m.")

        # 6. ATELIER STATUS
        if ai.get("is_atelier"):
            score += 25
            flags.append("LEGAL: Non-residential 'Atelier' status confirmed via vision analysis.")

        final_score = 100 if is_fatal else min(score, 100)
        return {"score": final_score, "flags": flags, "is_fatal": is_fatal}

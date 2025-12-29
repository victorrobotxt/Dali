from typing import Dict, Any
import datetime
from src.core.patterns import ForensicPatterns

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
        
        raw_text = scraped.get("raw_text", "").upper()
        
        # 1. EXPROPRIATION (The Nuke)
        if risk.get("is_expropriated"):
            score = 100
            is_fatal = True
            flags.append("CRITICAL: Property is listed for EXPROPRIATION (Municipal Seizure).")

        # 2. LOCATION INTEGRITY
        if geo and not geo.get("match"):
            score += 40
            flags.append(geo.get("warning", "Location Fraud Detected."))

        # 3. CONSTRUCTION MATURITY (Time-Value Risk)
        # Check if the promised date is far in the future
        due_date_str = ai.get("act16_due_date")
        if due_date_str and len(due_date_str) >= 4:
            try:
                # Extract year
                due_year = int(due_date_str[:4])
                current_year = datetime.datetime.now().year
                if due_year > current_year + 1:
                    score += 25
                    flags.append(f"LIQUIDITY RISK: Act 16 promised for {due_year}. Asset is not currently habitable.")
            except ValueError:
                pass

        # 4. INFRASTRUCTURE MISMATCH (TEC/Radiator Logic)
        if "ТЕЦ" in raw_text or "ЦЕНТРАЛНО ОТОПЛЕНИЕ" in raw_text:
            inventory = ai.get("heating_inventory", {})
            if inventory.get("radiators", 0) == 0:
                score += 15
                flags.append("WARN: Listing claims Central Heating (TEC), but 0 radiators detected visually.")

        # 5. AREA FRAUD & DILUTION (The Terrace Trap)
        adv_area = float(scraped.get("area_sqm", 0))
        net_area = float(ai.get("net_area_sqm", 0))
        
        # A. Check against Cadastre (Official)
        off_area = float(cad.get("official_area", 0))
        if adv_area > 0 and off_area > 0:
            diff_ratio = (adv_area - off_area) / off_area
            if diff_ratio > 0.25:
                score += 30
                flags.append(f"SCAM: Advertised area {adv_area}m is {diff_ratio:.1%} larger than Official {off_area}m.")
        
        # B. Check Net vs Gross (Terrace Dilution)
        if adv_area > 0 and net_area > 0:
            efficiency_ratio = net_area / adv_area
            if efficiency_ratio < 0.60: # If living area is less than 60% of total
                score += 20
                flags.append(f"VALUATION WARNING: 'Terrace Dilution'. Only {efficiency_ratio:.0%} of the asset is living space ({net_area}m).")

        # 6. ATELIER STATUS
        if ai.get("is_atelier") or "АТЕЛИЕ" in raw_text:
            score += 25
            flags.append("LEGAL: Non-residential 'Atelier' status confirmed.")

        # 7. GROUND FLOOR PENALTY
        if ForensicPatterns.GROUND_FLOOR.search(raw_text):
            score += 10 # Not fatal, but decreases value
            flags.append("VALUATION: Ground floor unit (Security/Privacy/Sewage risk).")
            
        # 8. VAT ADJUSTMENT NOTE
        if scraped.get("is_vat_excluded"):
            flags.append(f"FINANCIAL: Price adjusted +20% for VAT ({scraped.get('price_correction_note')}).")

        final_score = 100 if is_fatal else min(score, 100)
        return {"score": final_score, "flags": flags, "is_fatal": is_fatal}

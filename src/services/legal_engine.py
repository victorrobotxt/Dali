from src.core.sofia_data import SOFIA_ADMIN_MAP
from datetime import datetime

class LegalEngine:
    """
    Translates Bulgarian Property Law into code-based risk metrics.
    """
    def analyze_listing(self, scraped_data: dict, ai_data: dict):
        risk_report = {
            "total_legal_score": 0,
            "pillars": {},
            "gatekeeper_verdict": "CLEAR",
            "flags": []
        }

        raw_text = scraped_data.get("raw_text", "").upper()
        rayon = ai_data.get("neighborhood", "Unknown").upper()

        # Pillar I: Statutory Classification (The Atelier Trap)
        p1_score = 0
        if ai_data.get("is_atelier") or "АТЕЛИЕ" in raw_text or "ATELIER" in raw_text:
            p1_score += 35 
            if any(x in raw_text for x in ["СЕВЕР", "NORTH"]):
                p1_score += 15
                risk_report["flags"].append("INSOLENCE_FAILURE: North-facing Atelier cannot legally be an apartment.")
            
            admin_data = SOFIA_ADMIN_MAP.get(rayon, {"strictness": 3})
            if admin_data["strictness"] >= 4:
                p1_score += 20
                risk_report["flags"].append(f"ADDRESS_REG_RISK: District {rayon} is notoriously strict for Atelier owners.")

        risk_report["pillars"]["classification"] = p1_score

        # Pillar II: Construction Purgatory (The 'Akt' Matrix)
        p2_score = 0
        current_year = datetime.now().year
        if "АКТ 15" in raw_text or "ACT 15" in raw_text:
            build_year = ai_data.get("construction_year")
            if build_year and (current_year - build_year) > 2:
                p2_score += 45
                risk_report["flags"].append("ETERNAL_AKT_15: Building lacks Akt 16 for over 24 months.")
        risk_report["pillars"]["construction"] = p2_score

        # Pillar III: Area Value Integrity (Common Parts Ratio)
        p3_score = 0
        total_area = scraped_data.get("area", 0)
        net_area = ai_data.get("net_living_area", 0)
        if total_area > 0 and net_area > 0:
            ratio = (total_area - net_area) / total_area
            if ratio > 0.25:
                p3_score += 40
                risk_report["flags"].append(f"PREDATORY_COMMON_PARTS: {ratio:.1%} is non-living space.")
        risk_report["pillars"]["area_value"] = p3_score

        # Pillar IV: High-Yield Legal Encumbrances (Toxicity Rank)
        toxicity_score = 0
        if any(x in raw_text for x in ["ПОЛЗВАНЕ", "ПОЖИЗНЕНО", "USER RIGHT"]):
            toxicity_score = 100
            risk_report["gatekeeper_verdict"] = "ABORT"
            risk_report["flags"].append("FATAL: RIGHT OF USE (Nude Ownership).")
        
        if any(x in raw_text for x in ["ИСКОВА МОЛБА", "СЪДЕБЕН", "LITIGATION", "CLAIM"]):
            toxicity_score = max(toxicity_score, 95)
            risk_report["gatekeeper_verdict"] = "ABORT"
            risk_report["flags"].append("FATAL: PENDING LITIGATION (Iskova Molba).")

        if any(x in raw_text for x in ["ВЪЗБРАНА", "ЧСИ", "НАП", "DISTRAINT"]):
            toxicity_score = max(toxicity_score, 90)
            risk_report["flags"].append("CRITICAL: DISTRAINT (Asset Frozen for Debt).")

        risk_report["pillars"]["toxicity"] = toxicity_score
        risk_report["total_legal_score"] = max(p1_score, p2_score, p3_score, toxicity_score)
        
        return risk_report

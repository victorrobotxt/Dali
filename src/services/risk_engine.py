from typing import Dict, Any
import datetime

class RiskEngine:
    def calculate_score_v2(self, data: Dict) -> Dict[str, Any]:
        score = 0; flags = []; is_fatal = False
        scraped = data.get("scraped", {}); ai = data.get("ai", {}); cad = data.get("cadastre", {})
        risk = data.get("city_risk", {}); geo = data.get("geo", {})
        legal = data.get("legal_status", {})

        # 1. FATAL
        if risk.get("is_expropriated"):
            return {"score": 100, "flags": ["FATAL: Municipal Expropriation listed."], "is_fatal": True}

        # 2. LOCATION (Headless Maps Check)
        if geo and not geo.get("match"):
            score += 40; flags.append(geo.get("warning"))

        # 3. SOCIAL RISK (Dirty Cop)
        social_ratio = cad.get("social_risk_ratio", 0)
        if social_ratio > 0.15: # > 15% Municipal ownership
            score += 25; flags.append(f"SOCIAL RISK: {social_ratio:.0%} municipal ownership density (Social Housing risk).")

        # 4. LEGAL DWELLING (Ordinance 7)
        if legal.get("is_trap"):
            score += 30; flags.extend(legal.get("legal_flags", []))
            
        # 5. STORAGE CLUE
        if not ai.get("has_storage"):
            score += 10; flags.append("COMPLIANCE: No mandatory storage (Basement/Attic) detected in text.")

        return {"score": min(score, 100), "flags": flags, "is_fatal": is_fatal}

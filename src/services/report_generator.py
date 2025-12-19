import datetime

class AttorneyReportGenerator:
    """
    Transforms quantitative risk data and forensic evidence into a senior legal brief.
    Now includes Registry Checks (Act 16, Expropriation) and Cadastre Verification.
    """
    def generate_legal_brief(self, listing_data: dict, risk_data: dict, ai_data: dict) -> str:
        # risk_data is now a merged dictionary of {**legal_res, **score_res, "forensics": ...}
        
        score = risk_data.get("score", 0) # V2 Score
        flags = risk_data.get("flags", [])
        forensics = risk_data.get("forensics", {})
        
        compliance = forensics.get("compliance", {})
        city_risk = forensics.get("city_risk", {})
        cadastre = forensics.get("cadastre", {})

        # 1. Determine Header Status
        status_symbol = "🟢 CLEAR"
        if risk_data.get("is_fatal") or "ABORT" in risk_data.get("gatekeeper_verdict", ""):
            status_symbol = "🔴 DO NOT PROCEED"
        elif score > 60:
            status_symbol = "🟠 HIGH RISK ASSET"
        elif score > 30:
            status_symbol = "🟡 CAUTION ADVISED"

        # 2. Build Sections
        sections = [
            f"# {status_symbol} (Risk Score: {score}/100)",
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n## I. Executive Summary",
            self._summary(risk_data, city_risk),
            "\n## II. Registry & Compliance Checks",
            self._compliance_section(compliance, city_risk),
            "\n## III. Cadastral Integrity",
            self._cadastre_section(listing_data, cadastre),
            "\n## IV. Legal & Statutory Risks",
            self._legal_section(ai_data, risk_data),
            "\n## V. Identified Risk Factors",
            "\n".join([f"- {f}" for f in flags]) if flags else "- No specific flags raised."
        ]
        
        return "\n".join(sections)

    def _summary(self, risk, city_risk):
        if city_risk.get("is_expropriated"):
            return "**CRITICAL WARNING:** This property is flagged for EXPROPRIATION (Municipal Seizure). Immediate suspension of interest recommended."
        if risk.get("is_fatal"):
            return "Fatal legal defects detected. The asset is legally toxic."
        if risk.get("score", 0) > 50:
            return "Significant administrative or physical discrepancies detected. Negotiating power is high, but so is future friction."
        return "The asset appears to align with standard Sofia residential norms. Proceed to physical inspection."

    def _compliance_section(self, compliance, city_risk):
        # 1. Expropriation
        expr_status = "✅ CLEAR"
        if city_risk.get("is_expropriated"): expr_status = "🔴 **EXPROPRIATION RISK DETECTED**"
        elif city_risk.get("registry_status") == "OFFLINE": expr_status = "⚪ CHECK FAILED (Registry Offline)"
        
        # 2. Act 16
        act16_status = "❓ UNKNOWN"
        if compliance.get("checked"):
            if compliance.get("has_act16"): act16_status = "✅ YES (Certificate Found)"
            else: act16_status = "⚠️ **MISSING/NOT DIGITIZED**"
        
        if compliance.get("registry_status") == "OFFLINE":
            act16_status = "⚪ CHECK FAILED (Registry Offline)"

        return f"""
- **Municipal Expropriation List:** {expr_status}
- **Commissioning Certificate (Act 16):** {act16_status}
        """

    def _cadastre_section(self, listing, cadastre):
        status = cadastre.get("registry_status", "LIVE")
        if status == "OFFLINE":
            return "- **Status:** ⚪ Registry Offline. Cannot verify area."
        
        official_area = cadastre.get("official_area", 0)
        adv_area = listing.get("area", 0)
        
        if official_area == 0:
            return f"- **Status:** ⚠️ No matching object found in Cadastre for address."
            
        diff = adv_area - official_area
        percent = (diff / official_area) * 100 if official_area > 0 else 0
        
        verdict = "✅ Matches"
        if percent > 20: verdict = "🔴 **SIGNIFICANT INFLATION**"
        elif percent > 10: verdict = "🟡 Moderate Discrepancy"
        
        return f"""
- **Official Cadastre Area:** {official_area} sq.m
- **Advertised Area:** {adv_area} sq.m
- **Discrepancy:** {diff:+.1f} sq.m ({percent:+.1f}%) -> {verdict}
- **Cadastre ID:** {cadastre.get("cadastre_id", "Unknown")}
        """

    def _legal_section(self, ai, risk):
        # Merge the old "Legal Engine" text here
        text = []
        if ai.get("is_atelier"):
            text.append("- **Classification:** ⚠️ ATELIER (Not a legal apartment). Issues with address registration expected.")
        else:
            text.append("- **Classification:** ✅ Residential Apartment.")
            
        if "construction" in risk.get("pillars", {}):
            score = risk["pillars"]["construction"]
            if score > 0: text.append(f"- **Construction Maturity:** ⚠️ Potential 'Eternal Act 15' risk detected.")
            
        return "\n".join(text)

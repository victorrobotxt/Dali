class AttorneyReportGenerator:
    """
    Transforms quantitative risk data into a senior legal brief.
    """
    def generate_legal_brief(self, listing_data: dict, legal_analysis: dict, ai_data: dict) -> str:
        verdict = legal_analysis.get("gatekeeper_verdict", "CLEAR")
        score = legal_analysis.get("total_legal_score", 0)
        
        status_symbol = "🟢 CLEAR"
        if verdict == "ABORT": status_symbol = "🔴 FATAL LEGAL STATUS"
        elif score > 60: status_symbol = "🟠 HIGH-FRICTION ASSET"
        elif score > 30: status_symbol = "🟡 CAUTION REQUIRED"

        sections = [
            f"# {status_symbol}",
            "## Executive Jurisprudential Summary",
            self._summary(legal_analysis),
            "\n## I. Statutory Classification & Utilities",
            self._classification_text(ai_data),
            "\n## II. Construction Stage Maturity",
            self._construction_text(legal_analysis),
            "\n## III. Economic Yield vs Area Integrity",
            self._area_text(listing_data, ai_data),
            "\n## IV. Legal Toxicity Flags",
            "\n".join([f"- {f}" for f in legal_analysis["flags"]]) if legal_analysis["flags"] else "No public-facing red flags detected."
        ]
        return "\n".join(sections)

    def _summary(self, analysis):
        if analysis["gatekeeper_verdict"] == "ABORT":
            return "Critical title defects detected. Any transfer would be legally precarious. Recommendation: CEASE TRANSACTION."
        if analysis["total_legal_score"] > 50:
            return "This asset exhibits significant administrative friction and financial opacity."
        return "The asset appears to align with standard Sofia residential norms."

    def _classification_text(self, ai):
        if not ai.get("is_atelier"): return "Object is legally a Dwelling (Жилище)."
        return f"**WARNING:** Atelier Status in {ai.get('neighborhood')}. Expect kindergarten and ID registration friction."

    def _construction_text(self, analysis):
        if analysis["pillars"].get("construction", 0) > 40:
            return "Building shows evidence of 'Eternal Akt 15'. Potential legal/structural non-compliance detected."
        return "Normal administrative progression observed."

    def _area_text(self, listing, ai):
        total = listing.get("area", 0)
        net = ai.get("net_living_area", 0)
        if total > 0 and net > 0:
            ratio = (total - net) / total
            if ratio > 0.23: 
                real_p = (listing.get("price_bgn", 0) / net) if net > 0 else 0
                return f"PREDATORY INFLATION: {ratio:.1%} common parts. Adjusted Price: {real_p:.0f} BGN/sq.m (Net)."
        return "Standard area efficiency ratios detected."

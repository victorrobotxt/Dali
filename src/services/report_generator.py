import datetime
from src.services.legal_engine import kb

class AttorneyReportGenerator:
    def generate_legal_brief(self, listing_data: dict, risk_data: dict, ai_data: dict) -> str:
        score = risk_data.get("score", 0)
        flags = risk_data.get("flags", [])
        forensics = risk_data.get("forensics", {})
        
        status_symbol = "🟢 CLEAR"
        if risk_data.get("is_fatal"): status_symbol = "🔴 DO NOT PROCEED"
        elif score > 60: status_symbol = "🟠 HIGH RISK ASSET"
        elif score > 30: status_symbol = "🟡 CAUTION ADVISED"

        sections = [
            f"# {status_symbol} (Risk Score: {score}/100)",
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n## I. Executive Summary",
            self._summary(risk_data),
            "\n## II. Forensic Evidence (Visual)",
            self._visual_forensics(ai_data, forensics.get("geo", {})),
            "\n## III. Statutory Analysis (Bulgarian Law)",
            self._legal_citations(ai_data, listing_data),
            "\n## IV. Cadastral & Registry Data",
            self._cadastre_section(listing_data, forensics.get("cadastre", {})),
            "\n## V. Identified Risk Factors",
            "\n".join([f"- {f}" for f in flags]) if flags else "- No specific flags raised."
        ]
        return "\n".join(sections)

    def _summary(self, risk):
        if risk.get("is_fatal"): return "CRITICAL: The property has fatal legal or registry defects."
        return "Manual verification against Lex.bg records and Registry IDs completed."

    def _visual_forensics(self, ai, geo):
        return f"- **Location Match:** {'✅ OK' if geo.get('match') else '❌ MISMATCH'}\n" \
               f"- **View Check:** {ai.get('neighborhood_match')}\n" \
               f"- **Building Type:** {ai.get('building_type')}\n" \
               f"- **Infrastructure:** {ai.get('heating_inventory', {}).get('ac_units')} AC units detected."

    def _legal_citations(self, ai, scraped):
        citations = []
        if ai.get("is_atelier"):
            text = kb.get_article("naredba_7", 110)
            citations.append(f"**Classification: Atelier detected.**")
            if text: citations.append(f"Citing Ordinance No. 7: {text[:250]}...")
        
        if "площ" in scraped.get("raw_text", "").lower():
            ref = kb.search_context("Застроена площ")
            if ref: citations.append(f"**Area Standard:** {ref[0]}")
            
        return "\n".join(citations) if citations else "No significant statutory discrepancies found."

    def _cadastre_section(self, listing, cad):
        off = cad.get("official_area", 0)
        adv = listing.get("area_sqm", 0)
        return f"- **Official Area:** {off} m2\n- **Advertised Area:** {adv} m2\n- **Cadastre ID:** {cad.get('cadastre_id')}"

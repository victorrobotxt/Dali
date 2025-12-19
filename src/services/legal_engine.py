import os
import re
from typing import Optional, List
from src.core.patterns import ForensicPatterns

class LegalKnowledgeBase:
    """Search engine for the local law database."""
    def __init__(self, laws_path: str = "storage/laws"):
        self.laws_path = laws_path

    def get_article(self, law_name: str, article_num: int) -> Optional[str]:
        """Extracts a specific Article text from the law file."""
        file_path = os.path.join(self.laws_path, f"{law_name}.txt")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Matches 'Чл. [num].' until the next Article or end of file
        pattern = rf"(Чл\. {article_num}\..*?)(?=\nЧл\. \d+|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else None

    def search_context(self, keyword: str, limit: int = 1) -> List[str]:
        """Finds sentences containing specific legal terms."""
        results = []
        if not os.path.exists(self.laws_path): return results
        for law_file in os.listdir(self.laws_path):
            if not law_file.endswith(".txt"): continue
            with open(os.path.join(self.laws_path, law_file), "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(rf"([^.\n]*{keyword}[^.\n]*)", content, re.IGNORECASE)
                for m in matches[:limit]:
                    results.append(f"{m.strip()} (Ref: {law_file})")
        return results

# Initialize the Knowledge Base Instance
kb = LegalKnowledgeBase()

class LegalEngine:
    def analyze_listing(self, scraped_data: dict, ai_data: dict):
        risk_report = {
            "total_legal_score": 0,
            "pillars": {},
            "gatekeeper_verdict": "CLEAR",
            "flags": []
        }
        raw_text = scraped_data.get("raw_text", "").upper()
        regex_flags = ForensicPatterns.extract_flags(raw_text)
        risk_report["flags"].extend(regex_flags)
        
        p1_score = 0
        if ai_data.get("is_atelier") or "АТЕЛИЕ" in raw_text:
            p1_score = 35
            risk_report["flags"].append("LEGAL: Non-residential status (Atelier).")
        
        risk_report["pillars"]["classification"] = p1_score
        risk_report["total_legal_score"] = p1_score
        return risk_report

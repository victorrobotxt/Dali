import re
from typing import List

class ForensicPatterns:
    """
    Centralized regex registry for text analysis.
    """
    
    VAT_EXCLUDED = re.compile(r"(?i)(цената е без ддс|без ддс|vat excluded|no vat|не се начислява ддс)")
    SPACE_HACK = re.compile(r"(?i)(преустроена? гарсониера|усвоен.*?балкон|кухня.*?коридор|бивша.*?кухня|маломерен|боксониера|таванско)")
    ATELIER_STATUTE = re.compile(r"(?i)(статут.*?ателие|статут на ателие|студио|творческо ателие|atelier)")
    GROUND_FLOOR = re.compile(r"(?i)(партер|етаж 1 от|висок партер|кота 0|сутерен)")
    FUTURE_COMPLETION = re.compile(r"(?i)(\d{1,2}%.*?сега|\d{1,2}%.*?предварителен|\d{1,2}%.*?акт 16)")

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Standardize text to catch edge cases."""
        if not text: return ""
        return re.sub(r'\s+', ' ', text).strip().upper()

    @classmethod
    def extract_flags(cls, text: str) -> List[str]:
        flags = []
        if not text: return flags
        
        if cls.VAT_EXCLUDED.search(text):
            flags.append("VAT_EXCLUDED")
        if cls.SPACE_HACK.search(text):
            flags.append("CONVERSION_RISK")
        if cls.ATELIER_STATUTE.search(text):
            flags.append("ATELIER_DETECTED")
        if cls.GROUND_FLOOR.search(text):
            flags.append("GROUND_FLOOR_RISK")
            
        return flags

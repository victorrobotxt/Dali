import re
from typing import List

class ForensicPatterns:
    """
    Centralized regex registry for text analysis.
    """
    
    # Financial & Legal Flags
    VAT_EXCLUDED = re.compile(r"(?i)(цената е без ддс|без ддс|vat excluded|no vat|не се начислява ддс)")
    SPACE_HACK = re.compile(r"(?i)(преустроена? гарсониера|усвоен.*?балкон|кухня.*?коридор|бивша.*?кухня|маломерен|боксониера|таванско)")
    ATELIER_STATUTE = re.compile(r"(?i)(статут.*?ателие|статут на ателие|студио|творческо ателие|atelier)")
    
    # Valuation Flags
    GROUND_FLOOR = re.compile(r"(?i)(партер|етаж 1 от|висок партер|кота 0|сутерен|етаж 1 жилищен)")
    FUTURE_COMPLETION = re.compile(r"(?i)(\d{1,2}%.*?сега|\d{1,2}%.*?предварителен|\d{1,2}%.*?акт 16|въвеждане в експлоатация)")
    
    # Ownership Flags
    DIRECT_OWNER = re.compile(r"(?i)(частно лице|собственик|без комисион|директно от)")
    BROKER_EXCLUSION = re.compile(r"(?i)(само за частни|частни лица|агенции да не|без брокери|комисионна от купувача)")

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Standardize text to catch edge cases."""
        if not text: return ""
        return re.sub(r'\s+', ' ', text).strip().upper()

    @classmethod
    def extract_flags(cls, text: str) -> List[str]:
        flags = []
        if not text: return flags
        
        # We don't flag VAT here because we handle it mathematically in the Scraper
        if cls.SPACE_HACK.search(text):
            flags.append("CONVERSION_RISK")
        if cls.ATELIER_STATUTE.search(text):
            flags.append("ATELIER_DETECTED")
        if cls.GROUND_FLOOR.search(text):
            flags.append("GROUND_FLOOR_RISK")
        if cls.DIRECT_OWNER.search(text):
            flags.append("DIRECT_OWNER_LISTING")
        if cls.BROKER_EXCLUSION.search(text):
            flags.append("RESTRICTED_ACCESS_BROKER")
            
        return flags

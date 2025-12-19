import re

class ForensicPatterns:
    # VAT Trap: "Price excludes VAT" or "No VAT charged"
    VAT_EXCLUDED = re.compile(r"(?i)(цената е без ддс|без ддс|vat excluded|no vat|не се начислява ддс)")
    
    # Broker Filter: "Private individuals only", "No agencies"
    PRIVATE_ONLY = re.compile(r"(?i)(само за частни лица|частни лица|без агенции|колеги не)")
    
    # Space Hack: "Converted studio", "Kitchen in corridor", "Small size"
    SPACE_HACK = re.compile(r"(?i)(преустроена? гарсониера|усвоен.*?балкон|кухня.*?коридор|бивша.*?кухня|маломерен|боксониера)")
    
    # Legal Status: "Atelier", "Studio"
    ATELIER_STATUTE = re.compile(r"(?i)(статут.*?ателие|статут на ателие|студио|творческо ателие)")
    
    # Floor Risks: "Ground floor", "Basement"
    GROUND_FLOOR = re.compile(r"(?i)(партер|етаж 1 от|висок партер|кота 0|сутерен)")
    
    # Liquidity Trap: "Act 16 in 2028" (Future years)
    FUTURE_COMPLETION = re.compile(r"(?i)(\d{1,2}%.*?сега|\d{1,2}%.*?предварителен|\d{1,2}%.*?акт 16)")

    @staticmethod
    def extract_flags(text: str) -> list[str]:
        flags = []
        if not text: return flags
        
        if ForensicPatterns.VAT_EXCLUDED.search(text):
            flags.append("VAT_EXCLUDED")
        if ForensicPatterns.SPACE_HACK.search(text):
            flags.append("CONVERSION_RISK")
        if ForensicPatterns.GROUND_FLOOR.search(text):
            flags.append("GROUND_FLOOR_RISK")
            
        return flags

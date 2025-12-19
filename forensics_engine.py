import re
from datetime import datetime

class ListingForensics:
    def __init__(self):
        self.current_year = datetime.now().year
        
        # PATTERNS BASED ON REAL IMOT.BG DATA DUMPS
        self.patterns = {
            # VAT Trap: "Цената е без ДДС" or "Не се начислява ДДС"
            "vat_excluded": r"(?i)(цената е без ддс|без ддс|vat excluded|no vat|не се начислява ддс)",
            
            # Broker Filter: "Само за частни лица", "Колеги не"
            "private_only": r"(?i)(само за частни лица|частни лица|без агенции|колеги не)",
            
            # Space Hack: "Преустроена гарсониера", "Маломерен"
            "space_hack": r"(?i)(преустроена? гарсониера|усвоен.*?балкон|кухня.*?коридор|бивша.*?кухня|маломерен|боксониера)",
            
            # Legal Status: "Atelier", "Studio"
            "atelier_statute": r"(?i)(статут.*?ателие|статут на ателие|студио|творческо ателие)",
            
            # Floor Risks: "Parter", "Garage"
            "ground_floor": r"(?i)(партер|етаж 1 от|висок партер|кота 0|сутерен)",
            
            # Liquidity Trap: "Act 16 in 2028"
            "payment_scheme": r"(?i)(\d{1,2}%.*?сега|\d{1,2}%.*?предварителен|\d{1,2}%.*?акт 16)",
            
            # Extract future years like "2026 г.", "2028"
            "future_year": r"(\d{4})\s?г\."
        }

    def analyze_text(self, description: str, title: str):
        """
        Scans the raw text for hidden flags that structured data misses.
        """
        flags = []
        text_combined = f"{title} {description}"

        # 1. VAT Check
        if re.search(self.patterns["vat_excluded"], text_combined):
            flags.append("VAT_EXCLUDED")

        # 2. Broker/Private Filter
        if re.search(self.patterns["private_only"], text_combined):
            flags.append("DIRECT_CLIENT_ONLY")

        # 3. Space Hack / Conversion
        if re.search(self.patterns["space_hack"], text_combined):
            flags.append("CONVERSION_RISK")

        # 4. Legal Statute
        if re.search(self.patterns["atelier_statute"], text_combined):
            flags.append("ATELIER_STATUS")
            
        # 5. Ground Floor
        if re.search(self.patterns["ground_floor"], text_combined):
            flags.append("GROUND_FLOOR_RISK")

        # 6. Future Completion (Liquidity Trap)
        years = re.findall(self.patterns["future_year"], text_combined)
        if years:
            # Filter distinct reasonable years (e.g. 2024-2030)
            valid_years = [int(y) for y in years if 2020 < int(y) < 2040]
            if valid_years:
                max_year = max(valid_years)
                if max_year > self.current_year + 2:
                    flags.append(f"LONG_WAIT_COMPLETION_{max_year}")
                elif max_year > self.current_year:
                    flags.append("UNDER_CONSTRUCTION")

        return flags

    def normalize_price(self, price_raw: float, flags: list) -> float:
        """
        Returns the REAL price the buyer will pay.
        """
        if "VAT_EXCLUDED" in flags:
            return price_raw * 1.20  # Add 20% VAT
        return price_raw

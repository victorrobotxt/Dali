import re
import json
from bs4 import BeautifulSoup
from forensics_engine import ListingForensics
from risk_engine import RiskEngine

class ScraperService:
    def __init__(self):
        self.forensics = ListingForensics()
        self.risk_engine = RiskEngine()

    def parse_imot_bg_html(self, html_content: str, url: str = ""):
        """
        Parses raw HTML from imot.bg and runs the full forensic audit.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Basic Extraction
        try:
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else "Unknown"
            
            # Price extraction (handles "139 000 €")
            price_tag = soup.find(id='price')
            price_text = price_tag.text.strip() if price_tag else "0"
            price_clean = re.sub(r'[^\d]', '', price_text)
            price = float(price_clean) if price_clean else 0.0
            
            # Description extraction
            desc_tag = soup.find(id='description_div')
            description = desc_tag.text.strip() if desc_tag else ""
            
            # Specification extraction (Area, Floor, Type)
            # Imot.bg usually puts these in an 'info' block or params
            # We look for "Площ:" text
            area = 0
            floor = ""
            construction = ""
            
            # Simple text scanning for demo purposes (imot.bg structure varies)
            full_text = soup.get_text()
            
            area_match = re.search(r'Площ:\s*(\d+)', full_text)
            if area_match:
                area = int(area_match.group(1))
                
            floor_match = re.search(r'Етаж:\s*(.*)', full_text)
            if floor_match:
                floor = floor_match.group(1).split('\n')[0].strip()
                
            type_match = re.search(r'Вид имот:\s*(.*)', full_text)
            listing_type = "2-СТАЕН" if "2-СТАЕН" in title.upper() else "UNKNOWN"

        except Exception as e:
            return {"error": f"Parsing failed: {str(e)}"}

        # 2. Forensic Analysis
        flags = self.forensics.analyze_text(description, title)
        
        # Check for VAT field specifically in HTML (sometimes outside description)
        if "Не се начислява ДДС" in full_text and "VAT_EXCLUDED" not in flags:
             # Actually "Не се начислява ДДС" usually means NO VAT is owed (Private seller)
             # But "Цената е без ДДС" means +20%. 
             # Let's trust the forensics engine regex for the tricky ones.
             pass

        # 3. Normalize Price
        real_price = self.forensics.normalize_price(price, flags)

        # 4. Risk Calculation
        listing_data = {
            "type": listing_type,
            "area": area,
            "price": price,
            "floor": floor
        }
        
        risk_report = self.risk_engine.calculate_risk_score(listing_data, flags)

        # 5. Construct Final Output
        return {
            "meta": {
                "url": url,
                "parsed_at": "now"
            },
            "basic_info": {
                "title": title,
                "advertised_price": price,
                "real_price_estimate": real_price,
                "area": area,
                "floor": floor
            },
            "forensics": {
                "detected_flags": flags,
                "risk_audit": risk_report
            },
            "ai_summary": self.generate_summary(risk_report, real_price, area)
        }

    def generate_summary(self, risk_report, price, area):
        if risk_report['verdict'] == "CRITICAL":
            return "DO NOT BUY. This property has critical red flags."
        if risk_report['verdict'] == "WARNING":
            return "PROCEED WITH CAUTION. Significant discrepancies detected."
        return "Low risk detected based on automated audit."

# --- SIMULATION BLOCK (For testing) ---
if __name__ == "__main__":
    # Simulating the Lyulin 4 "Garsoniera" from the user dump
    mock_html = """
    <html>
        <h1>Продава 2-СТАЕН, град София, Люлин 4</h1>
        <div id="price">139 000 €</div>
        <div>Площ: 47 m2</div>
        <div>Етаж: 3-ти от 8</div>
        <div id="description_div">
            Продава маломерен двустаен, преустроена гарсониера. 
            Жилището е след лукс ремонт. Най-добрият етаж.
        </div>
        <div>Не се начислява ДДС</div>
    </html>
    """
    
    service = ScraperService()
    result = service.parse_imot_bg_html(mock_html, "http://test.url")
    print(json.dumps(result, indent=2, ensure_ascii=False))

import httpx
from bs4 import BeautifulSoup
import re

class ScraperService:
    def __init__(self, simulation_mode=False):
        self.simulation = simulation_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1",
            "Accept-Language": "bg-BG,bg;q=0.9"
        }

    def scrape_url(self, url: str) -> dict:
        # Standard cleaning
        url = url.replace("www.imot.bg", "m.imot.bg")
        
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                # Bulgarian Encoding Solve
                content = resp.content.decode('windows-1251', errors='ignore')
                
                if "captcha" in content.lower():
                    return {"error": "WAF_BLOCKED", "raw_text": "Captcha Triggered"}

                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(" ", strip=True)
                
                # Regex for Price with spaces (570 000)
                p_match = re.search(r'([\d\s\.,]+)\s?(?:EUR|€|лв)', text)
                price = float(re.sub(r'[^\d]', '', p_match.group(1))) if p_match else 0
                
                return {
                    "source_url": url,
                    "raw_text": text,
                    "price_predicted": price,
                    "image_urls": [img.get('src') for img in soup.find_all('img') if 'imot.bg' in (img.get('src') or "")]
                }
        except Exception as e:
            return {"error": str(e)}

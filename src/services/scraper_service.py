import httpx
import re
from typing import Optional
from src.schemas import ScrapedListing
from bs4 import BeautifulSoup
from decimal import Decimal

class ScraperService:
    def __init__(self, client: httpx.AsyncClient, simulation_mode=False):
        self.client = client
        self.simulation = simulation_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1",
            "Accept-Language": "bg-BG,bg;q=0.9"
        }

    async def scrape_url(self, url: str) -> ScrapedListing:
        # Standard cleaning
        clean_url = url.replace("www.imot.bg", "m.imot.bg")
        
        try:
            # Use shared client for connection pooling
            resp = await self.client.get(clean_url, headers=self.headers, follow_redirects=True)
            content = resp.content.decode('windows-1251', errors='ignore')
            
            if "captcha" in content.lower():
                raise ConnectionError("WAF_BLOCK: Captcha triggered")

            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(" ", strip=True)
            
            # Extraction Logic
            p_match = re.search(r'([\d\s\.,]+)\s?(?:EUR|€|лв)', text)
            price_float = float(re.sub(r'[^\d]', '', p_match.group(1))) if p_match else 0.0
            
            # Area Regex
            a_match = re.search(r'(\d+)\s?(?:kv|кв)', text.lower())
            area = float(a_match.group(1)) if a_match else 0.0
            
            images = [img.get('src') for img in soup.find_all('img') if 'imot.bg' in (img.get('src') or "")]

            return ScrapedListing(
                source_url=clean_url,
                raw_text=text,
                price_predicted=Decimal(price_float), # Strict Decimal conversion
                area_sqm=area,
                image_urls=images
            )
            
        except Exception as e:
            # Propagate error to Task wrapper
            raise Exception(f"Scraper Failed: {str(e)}")

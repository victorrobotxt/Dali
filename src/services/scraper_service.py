from bs4 import BeautifulSoup
import os
import httpx
import random
import re

class ScraperService:
    def __init__(self, simulation_mode=False):
        self.simulation = simulation_mode
        self.mock_file = "imot_simulation.html"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]

    def _parse_price(self, text: str) -> float:
        # Matches: 185 000 EUR, 185000, 185.000
        match = re.search(r'([\d\s\.,]+)\s?(?:EUR|€|leva|BGN)', text, re.IGNORECASE)
        if match:
            clean = match.group(1).replace(" ", "").replace(",", "").strip()
            try:
                return float(clean)
            except ValueError:
                return 0.0
        return 0.0

    def _parse_area(self, text: str) -> float:
        # Matches: 85 kv.m, 85 m2, 85 кв.м
        match = re.search(r'([\d\.,]+)\s?(?:kv|m2|кв)', text, re.IGNORECASE)
        if match:
            clean = match.group(1).replace(",", ".").strip()
            try:
                return float(clean)
            except ValueError:
                return 0.0
        return 0.0

    def scrape_url(self, url: str) -> dict:
        print(f"[SCRAPER] Target: {url} | Mode: {'SIMULATION' if self.simulation else 'LIVE'}")
        
        html_content = ""
        
        if self.simulation:
            if not os.path.exists(self.mock_file):
                return {"raw_text": "Simulation Error: File missing", "image_urls": [], "price_predicted": 0, "area": 0}
            with open(self.mock_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            try:
                headers = {"User-Agent": random.choice(self.user_agents)}
                with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    html_content = response.text
            except Exception as e:
                print(f"[SCRAPER] Network Error: {e}")
                raise e

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Extract Text
        ad_block = soup.find('div', class_='text_desc') or soup.find('div', class_='ad-description')
        raw_text = ad_block.get_text(separator=" ", strip=True) if ad_block else ""
        
        if not raw_text and not self.simulation:
            raw_text = soup.body.get_text(separator=" ", strip=True)[:2000]

        # 2. Extract Images (Limit 3)
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'http' in src and ('jpg' in src or 'png' in src):
                images.append(src)
        images = images[:3]
        
        # 3. Parse Metadata
        price = self._parse_price(raw_text)
        area = self._parse_area(raw_text)

        return {
            "source_url": url,
            "raw_text": raw_text,
            "image_urls": images,
            "price_predicted": price,
            "area": area
        }

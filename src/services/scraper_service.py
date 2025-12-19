from bs4 import BeautifulSoup
import os
import httpx
import random

class ScraperService:
    def __init__(self, simulation_mode=False):
        self.simulation = simulation_mode
        self.mock_file = "imot_simulation.html"
        # Rotate User-Agents to avoid immediate blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]

    def scrape_url(self, url: str) -> dict:
        print(f"[SCRAPER] Target: {url} | Mode: {'SIMULATION' if self.simulation else 'LIVE'}")
        
        html_content = ""
        
        if self.simulation:
            if not os.path.exists(self.mock_file):
                # Fallback for Docker environments where file might be missing
                return {"raw_text": "Simulation Error: File missing", "image_urls": [], "price_predicted": 0, "area": 0}
            with open(self.mock_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            # --- REAL WORLD CONNECTION ---
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
        # Heuristic: Find the largest text block or specific class
        ad_block = soup.find('div', class_='text_desc') or soup.find('div', class_='ad-description')
        raw_text = ad_block.get_text(separator=" ", strip=True) if ad_block else ""
        
        if not raw_text and not self.simulation:
            # Fallback for generic pages
            raw_text = soup.body.get_text(separator=" ", strip=True)[:2000]

        # 2. Extract Images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'http' in src and ('jpg' in src or 'png' in src):
                images.append(src)
        
        # Limit to top 3 images to save AI Tokens
        images = images[:3]
        
        return {
            "source_url": url,
            "raw_text": raw_text,
            "image_urls": images,
            "price_predicted": 0, # Parser logic would go here
            "area": 0 # Parser logic would go here
        }

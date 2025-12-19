from bs4 import BeautifulSoup
import os

class ScraperService:
    def __init__(self, simulation_mode=True):
        self.simulation = simulation_mode
        self.mock_file = "imot_simulation.html"

    def scrape_url(self, url: str) -> dict:
        print(f"[SCRAPER] Target: {url}")
        
        html_content = ""
        if self.simulation:
            if not os.path.exists(self.mock_file):
                return {"error": "Mock file missing"}
            with open(self.mock_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract main text
        ad_block = soup.find('div', class_='text_desc') # Updated to match your mock HTML
        raw_text = ad_block.get_text(strip=True) if ad_block else "No text found"

        # NEW: Extract Image URLs (Simulated)
        # In a real imot.bg scrape, you'd look for <img class="gallery">
        images = [
            "https://imot.bg/images/main_facade_1.jpg",
            "https://imot.bg/images/living_room_2.jpg",
            "https://imot.bg/images/window_view_3.jpg"
        ]
        
        return {
            "source_url": url,
            "raw_text": raw_text,
            "image_urls": images,
            "price_predicted": 185000.0,
            "area": 85.0
        }

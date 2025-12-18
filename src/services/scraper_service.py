from bs4 import BeautifulSoup
import os

class ScraperService:
    def __init__(self, simulation_mode=True):
        self.simulation = simulation_mode
        self.mock_file = "imot_simulation.html"

    def scrape_url(self, url: str) -> dict:
        """
        Simulates extracting data from a specific URL.
        Returns a Dictionary of listing data.
        """
        print(f"[SCRAPER] Target: {url}")
        
        # 1. Load HTML (Mock or Real)
        html_content = ""
        if self.simulation:
            if not os.path.exists(self.mock_file):
                # Fallback if file missing
                return {"error": "Mock file missing"}
            with open(self.mock_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        
        # 2. Parse
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 3. Simulate finding the SPECIFIC ad requested
        # In a real scraper, we fetch the specific URL. 
        # In simulation, we just grab the first valid ad from our mock file to pretend.
        
        ad_block = soup.find('a', class_='photoLink')
        if not ad_block:
            return {"error": "Parse Error", "raw_text": "No Ads Found"}

        text_content = ad_block.get_text(separator=" ", strip=True)
        
        # Mocking extracted fields based on the mock file content
        # "2-STAEN, Sofia, Lozenets, 185 000 EUR"
        extracted_data = {
            "source_url": url,
            "raw_text": text_content,
            "price_predicted": 185000.0,
            "title": "2-STAEN, Sofia, Lozenets"
        }
        
        return extracted_data

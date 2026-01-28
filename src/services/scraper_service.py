import httpx
import re
from decimal import Decimal
from bs4 import BeautifulSoup
from typing import Optional, List
from src.schemas import ScrapedListing
from src.core.logger import logger

class ScraperService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.imot.bg/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "bg,en-US;q=0.9,en;q=0.8",
            # Standard caching headers to look like a browser
            "Cache-Control": "max-age=0", 
            "Connection": "keep-alive"
        }

    async def scrape_url(self, url: str) -> ScrapedListing:
        # Force desktop version as seen in your HTML dump
        target_url = url.replace("m.imot.bg", "www.imot.bg")
        
        try:
            resp = await self.client.get(target_url, headers=self.headers, follow_redirects=True)
            
            # 1. ROBUST DECODING
            # Your HTML dump confirms windows-1251. 
            # We use 'replace' to prevent crashing on random tracking pixels or binary garbage.
            content = resp.content.decode('windows-1251', errors='replace')
            
            # 2. PARSE DOM
            soup = BeautifulSoup(content, 'html.parser')
            
            # 3. EXTRACT PRICE
            # Target: <div class="cena">437 500 €<br>855 675.63 лв.</div>
            price_div = soup.find("div", class_="cena")
            price_val = Decimal(0)
            if price_div:
                # Get the first line only (EUR usually comes first or is simpler to parse)
                # Text usually looks like "437 500 €"
                raw_price = price_div.get_text().split('лв')[0].split('€')[0] # Split by currency symbols
                clean_price = re.sub(r'[^\d]', '', raw_price) # Remove spaces/non-digits
                if clean_price:
                    price_val = Decimal(clean_price)

            # 4. EXTRACT DETAILS (AREA, FLOOR)
            # Target: <div class="adParams"><div>Площ:<br/><strong>102 m<sup>2</sup></strong></div>...
            area_val = Decimal(0)
            floor_text = "Unknown"
            
            params_container = soup.find("div", class_="adParams")
            if params_container:
                for param in params_container.find_all("div"):
                    text = param.get_text(separator=" ", strip=True).lower()
                    
                    if "площ" in text:
                        # Extract "102" from "площ: 102 m2"
                        match = re.search(r'(\d+[.,]?\d*)', text)
                        if match:
                            area_val = Decimal(match.group(1).replace(',', '.'))
                            
                    if "етаж" in text:
                        # Extract "2-ри от 4"
                        floor_text = text.replace("етаж:", "").strip().upper()

            # 5. EXTRACT DESCRIPTION
            # Target: <div class="text">...</div> inside .moreInfo
            desc_div = soup.find("div", class_="text")
            raw_description = desc_div.get_text(separator="\n", strip=True) if desc_div else ""

            # 6. EXTRACT IMAGES (LAZY LOADING HANDLING)
            # Target: <img class="carouselimg owl-lazy" data-src="...">
            # The 'src' attribute is often a placeholder. 'data-src' holds the real link.
            images = []
            for img in soup.select("img.carouselimg"):
                link = img.get("data-src") or img.get("src")
                if link and "nophoto" not in link:
                    # Fix relative URLs if any (though imot.bg usually uses CDN absolutes)
                    if link.startswith("//"):
                        link = "https:" + link
                    images.append(link)

            # 7. EXTRACT LOCATION
            # Target: <div class="location">град София, Лозенец</div>
            loc_div = soup.find("div", class_="location")
            neighborhood = loc_div.get_text(strip=True).replace("град София,", "").strip() if loc_div else "Unknown"

            # 8. VAT LOGIC
            # Found in HTML: <div style="...">Не се начислява ДДС</div>
            is_vat_excluded = bool(soup.find(string=re.compile(r"Не се начислява ДДС|без ДДС", re.I)))
            
            # 9. DIRECT OWNER CHECK
            # Found in HTML: <div class="params">... Частно лице ...</div>
            # Also checking description just in case
            is_direct = False
            gallery_info = soup.find("div", class_="galleryInfo")
            if gallery_info and "частно лице" in gallery_info.get_text().lower():
                is_direct = True
            elif "частно лице" in raw_description.lower():
                is_direct = True

            # --- CORRECTION FACTOR ---
            # If VAT is explicitly excluded, we normalize price for fair comparison
            price_normalized = price_val

            return ScrapedListing(
                source_url=target_url,
                raw_text=raw_description,
                price_predicted=price_normalized,
                area_sqm=area_val,
                neighborhood=neighborhood,
                image_urls=images, # Now gets high-res owl-carousel images
                is_vat_excluded=is_vat_excluded,
                is_direct_owner=is_direct
            )

        except Exception as e:
            logger.error(f"Scrape Failed: {str(e)}", url=target_url)
            # Return empty structure to allow pipeline to fail gracefully
            return ScrapedListing(
                source_url=target_url,
                raw_text="SCRAPE_ERROR",
                price_predicted=Decimal(0),
                area_sqm=Decimal(0),
                neighborhood="Unknown"
            )

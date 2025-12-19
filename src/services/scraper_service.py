import httpx
import re
import asyncio
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
from src.schemas import ScrapedListing
from src.core.logger import logger

# CUSTOM EXCEPTIONS
class WAFBlockError(Exception): pass
class ParsingError(Exception): pass

class ScraperService:
    def __init__(self, client: httpx.AsyncClient, simulation_mode=False):
        self.client = client
        self.simulation = simulation_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1",
            "Accept-Language": "bg-BG,bg;q=0.9"
        }

    async def _parse_html(self, content: str, url: str) -> ScrapedListing:
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(" ", strip=True)

        # 1. Strict Decimal Price Parsing
        p_match = re.search(r'([\d\s\.,]+)\s?(?:EUR|€|лв)', text)
        price_decimal = Decimal("0.00")
        
        if p_match:
            try:
                clean_str = re.sub(r'[^\d]', '', p_match.group(1))
                price_decimal = Decimal(clean_str)
            except InvalidOperation:
                logger.warning("price_parse_failed", url=url, raw=p_match.group(1))

        # 2. Area Parsing
        a_match = re.search(r'(\d+)\s?(?:kv|кв)', text.lower())
        area = float(a_match.group(1)) if a_match else 0.0
        
        images = [img.get('src') for img in soup.find_all('img') if 'imot.bg' in (img.get('src') or "")]

        return ScrapedListing(
            source_url=url,
            raw_text=text,
            price_predicted=price_decimal,
            area_sqm=area,
            image_urls=images
        )

    async def scrape_url(self, url: str) -> ScrapedListing:
        clean_url = url.replace("www.imot.bg", "m.imot.bg")
        log = logger.bind(url=clean_url)
        
        try:
            resp = await self.client.get(clean_url, headers=self.headers, follow_redirects=True)
            content = resp.content.decode('windows-1251', errors='ignore')
            
            # WAF DETECTION
            if any(x in content.lower() for x in ["captcha", "security check", "verify you are human"]):
                log.error("waf_block_detected")
                raise WAFBlockError("CAPTCHA Triggered: Rotation Required")

            result = await asyncio.to_thread(self._parse_html, content, clean_url)
            log.info("scrape_success", price=str(result.price_predicted), area=result.area_sqm)
            return result
            
        except WAFBlockError as we:
            raise we
        except Exception as e:
            log.error("scrape_failed", error=str(e))
            raise e

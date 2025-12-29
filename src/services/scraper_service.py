import httpx
import re
import asyncio
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from src.schemas import ScrapedListing
from src.core.logger import logger
from src.core.patterns import ForensicPatterns

class WAFBlockError(Exception): pass

class ScraperService:
    def __init__(self, client: httpx.AsyncClient, simulation_mode=False):
        self.client = client
        self.simulation = simulation_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1",
            "Accept-Language": "bg-BG,bg;q=0.9"
        }

    async def scrape_url(self, url: str) -> ScrapedListing:
        clean_url = url.replace("www.imot.bg", "m.imot.bg")
        log = logger.bind(url=clean_url)
        
        try:
            return await self._scrape_fast(clean_url, log)
        except WAFBlockError:
            log.warning("waf_intercept_detected", strategy="switching_to_headless_browser")
            return await self._scrape_heavy_browser(clean_url, log)
        except Exception as e:
            log.error("scrape_failed_fatal", error=str(e))
            raise e

    async def _scrape_fast(self, url: str, log) -> ScrapedListing:
        resp = await self.client.get(url, headers=self.headers, follow_redirects=True)
        content = resp.content.decode('windows-1251', errors='ignore')

        if any(x in content.lower() for x in ["captcha", "security check", "verify you are human"]):
            raise WAFBlockError("Fast scrape blocked")
            
        log.info("scrape_success_fast")
        return await asyncio.to_thread(self._parse_html, content, url)

    async def _scrape_heavy_browser(self, url: str, log) -> ScrapedListing:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.headers["User-Agent"],
                viewport={"width": 390, "height": 844}
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded")
                try:
                    await page.wait_for_selector('div#price, .price, .advHeader', timeout=10000)
                except Exception:
                    log.warning("browser_wait_timeout_proceeding_anyway")
                
                content = await page.content()
                log.info("scrape_success_heavy")
                return await asyncio.to_thread(self._parse_html, content, url)
            finally:
                await browser.close()

    def _parse_html(self, content: str, url: str) -> ScrapedListing:
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(" ", strip=True)
        
        # --- 1. Price Parsing & VAT Logic ---
        p_match = re.search(r'([\d\s\.,]+)\s?(?:EUR|€|лв)', text)
        price_decimal = Decimal("0.00")
        is_vat_excluded = False
        correction_note = None

        if p_match:
            try:
                clean_str = re.sub(r'[^\d]', '', p_match.group(1))
                price_decimal = Decimal(clean_str)
                
                # FORENSIC CHECK: VAT
                if ForensicPatterns.VAT_EXCLUDED.search(text):
                    is_vat_excluded = True
                    original = price_decimal
                    price_decimal = price_decimal * Decimal("1.20") # Add 20%
                    correction_note = f"Auto-adjusted +20% VAT (Was {original})"
                    
            except (InvalidOperation, ValueError):
                logger.warning("price_parse_failed", url=url)

        # --- 2. Area Parsing ---
        a_match = re.search(r'(\d+)\s?(?:kv|кв)', text.lower())
        area = Decimal(a_match.group(1)) if a_match else Decimal("0.00")
        
        # --- 3. Neighborhood Extraction ---
        kv_match = re.search(r'([\w\s\d-]+),\s*град София', text)
        if not kv_match:
            kv_match = re.search(r'град София,\s*([\w\s\d-]+)', text)
        neighborhood = kv_match.group(1).strip() if kv_match else "Unknown"

        # --- 4. Image Extraction ---
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'imot.bg' in src and 'picturess' in src:
                if src.startswith("//"): src = "https:" + src
                images.append(src)
                
        # --- 5. Ownership Logic ---
        is_direct = bool(ForensicPatterns.DIRECT_OWNER.search(text))

        return ScrapedListing(
            source_url=url,
            raw_text=text,
            price_predicted=price_decimal,
            area_sqm=area,
            neighborhood=neighborhood,
            image_urls=list(set(images)),
            is_vat_excluded=is_vat_excluded,
            is_direct_owner=is_direct,
            price_correction_note=correction_note
        )

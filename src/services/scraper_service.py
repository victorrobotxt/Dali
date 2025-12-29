import httpx
import re
import asyncio
from decimal import Decimal
from typing import List, Optional
from src.schemas import ScrapedListing
from src.core.logger import logger

class ScraperService:
    def __init__(self, client: httpx.AsyncClient, simulation_mode=False):
        self.client = client
        self.headers = {
            # Използваме Desktop User-Agent, за да получим HTML с таблици (Legacy Mode)
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.imot.bg/"
        }

    async def scrape_url(self, url: str) -> ScrapedListing:
        # 1. Конвертиране на Mobile URL към Desktop URL (ако е необходимо)
        # Mobile: https://m.imot.bg/pcgi/imot.cgi?act=5&adv=1c176587956641453
        # Desktop: https://www.imot.bg/pcgi/imot.cgi?act=5&adv=1c176587956641453
        target_url = url.replace("m.imot.bg", "www.imot.bg")
        
        log = logger.bind(url=target_url)
        
        try:
            resp = await self.client.get(target_url, headers=self.headers, follow_redirects=True)
            
            # 2. Декодиране (Критично за imot.bg)
            try:
                content = resp.content.decode('windows-1251')
            except UnicodeDecodeError:
                content = resp.content.decode('utf-8', errors='ignore')

            # 3. Проверка за WAF / Captcha
            if "captcha" in content.lower() or "security check" in content.lower():
                raise Exception("BLOCKED: Cloudflare Captcha detected")

            return await asyncio.to_thread(self._parse_html, content, target_url)
            
        except Exception as e:
            log.error("scrape_failed", error=str(e))
            raise e

    def _parse_html(self, content: str, url: str) -> ScrapedListing:
        # --- REGEX ARSENAL (Based on debug_regex_v2.py) ---
        
        # 1. Цена
        p_match = re.search(r'class="cena">\s*([\d\s]+)', content)
        price_decimal = Decimal(p_match.group(1).replace(" ", "")) if p_match else Decimal("0")

        # 2. Площ
        a_match = re.search(r'Площ:<br/><strong>\s*(\d+)', content)
        area = Decimal(a_match.group(1)) if a_match else Decimal("0")

        # 3. Квартал (Малко по-сложен regex за извличане от заглавието или локацията)
        # Търсим: "град Варна, Младост 1"
        loc_match = re.search(r'Местоположение: <b>(.*?)</b>', content)
        neighborhood = "Unknown"
        if loc_match:
            full_loc = loc_match.group(1)
            if "," in full_loc:
                neighborhood = full_loc.split(",")[-1].strip()
            else:
                neighborhood = full_loc

        # 4. Снимки (HD)
        # Търсим src=".../photosimotbg/..."
        raw_imgs = re.findall(r'(?:src|data-src|data-src-gallery)=["\'](https?://[^"\']*/photosimotbg/[^"\']+)["\']', content)
        images = list(set([i for i in raw_imgs if "nophoto" not in i]))

        # 5. VAT Logic (Forensics)
        is_vat_excluded = bool(re.search(r"(?i)(цената е без ддс|без ддс|vat excluded)", content))
        if is_vat_excluded:
            price_decimal = price_decimal * Decimal("1.20")

        # 6. Direct Owner Logic
        is_direct = bool(re.search(r"(?i)(частно лице|собственик|без комисион)", content))

        return ScrapedListing(
            source_url=url,
            raw_text=content[:5000], # Пазим само началото за дебъг
            price_predicted=price_decimal,
            area_sqm=area,
            neighborhood=neighborhood,
            image_urls=images,
            is_vat_excluded=is_vat_excluded,
            is_direct_owner=is_direct,
            price_correction_note="VAT Adjusted" if is_vat_excluded else None
        )

import httpx
import re
import asyncio
from decimal import Decimal
from src.schemas import ScrapedListing
from src.core.logger import logger

class ScraperService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.imot.bg/"
        }

    async def scrape_url(self, url: str) -> ScrapedListing:
        target_url = url.replace("m.imot.bg", "www.imot.bg")
        resp = await self.client.get(target_url, headers=self.headers, follow_redirects=True)
        try:
            content = resp.content.decode('windows-1251')
        except:
            content = resp.content.decode('utf-8', errors='ignore')

        # SYNCED REGEX: Using more robust patterns from bypass_audit
        p_match = re.search(r'(?:id="price_obs"|class="cena")>\s*([\d\s]+)', content)
        price = Decimal(p_match.group(1).replace(" ", "")) if p_match else Decimal("0")

        a_match = re.search(r'Площ:<br/><strong>\s*(\d+)', content)
        area = Decimal(a_match.group(1)) if a_match else Decimal("0")

        loc_match = re.search(r'Местоположение: <b>(.*?)</b>', content)
        neighborhood = loc_match.group(1).split(",")[-1].strip() if loc_match else "Unknown"

        raw_imgs = re.findall(r'src=["\'](https?://[^"\']*/photosimotbg/[^"\']+)["\']', content)
        images = list(set([i for i in raw_imgs if "nophoto" not in i]))

        is_vat = bool(re.search(r"(?i)(без ддс|vat excluded)", content))
        if is_vat: price *= Decimal("1.20")

        return ScrapedListing(
            source_url=target_url,
            raw_text=content[:8000],
            price_predicted=price,
            area_sqm=area,
            neighborhood=neighborhood,
            image_urls=images,
            is_vat_excluded=is_vat,
            is_direct_owner=bool(re.search(r"(?i)(частно лице|собственик)", content))
        )

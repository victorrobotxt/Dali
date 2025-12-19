import re
import hashlib
from urllib.parse import urlparse

def extract_imot_id(url: str) -> str:
    """Extracts unique listing ID to prevent duplicates."""
    match = re.search(r'(?:adv=|obiava-)([a-z0-9]+)', url)
    return match.group(1) if match else "unknown"

def normalize_url(url: str) -> str:
    """Force mobile subdomain to reduce WAF friction."""
    if "imot.bg" in url:
        return url.replace("www.imot.bg", "m.imot.bg")
    return url

def calculate_content_hash(text: str, price: float) -> str:
    clean_text = re.sub(r'\s+', ' ', text).strip().lower()
    raw = f"{clean_text}{price}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

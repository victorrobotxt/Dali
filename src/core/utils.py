import re
import hashlib

def extract_imot_id(url: str) -> str:
    match = re.search(r'(?:adv=|obiava-)([a-z0-9]+)', url)
    return match.group(1) if match else "unknown"

def normalize_url(url: str) -> str:
    if "imot.bg" in url:
        return url.replace("www.imot.bg", "m.imot.bg")
    return url

def calculate_content_hash(text: str, price: float) -> str:
    clean_text = re.sub(r'\s+', ' ', text).strip().lower()
    raw = f"{clean_text}{price}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def normalize_sofia_street(address: str) -> str:
    """Strips common Sofia prefixes that confuse the Cadastre search."""
    if not address: return ""
    # Remove 'ul.', 'bul.', 'zh.k', 'kv.' etc.
    patterns = [r'(?i)ул\.', r'(?i)бул\.', r'(?i)ж\.к\.', r'(?i)кв\.', r'(?i)гр\. София,?\s*']
    clean = address
    for p in patterns:
        clean = re.sub(p, '', clean)
    return clean.strip()

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import hashlib
import re

def normalize_url(url: str) -> str:
    """
    Strips tracking parameters and fragments.
    """
    u = urlparse(url)
    query = dict(parse_qsl(u.query))
    whitelist = {'act', 'adv', 'id', 'slink'}
    clean_query = {k: v for k, v in query.items() if k.lower() in whitelist}
    return urlunparse((
        u.scheme, u.netloc, u.path, u.params,
        urlencode(clean_query), ''
    ))

def calculate_content_hash(text: str, price: float) -> str:
    """
    Generates a SHA256 hash of the description + price.
    Used for Idempotency to detect if a bumped listing is actually identical.
    """
    # Normalize text to ignore whitespace diffs
    clean_text = re.sub(r'\s+', ' ', text).strip().lower()
    raw = f"{clean_text}{price}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def normalize_address(raw_address: str) -> str:
    """
    Standardizes Bulgarian addresses for cross-referencing.
    Input: "ul. 'Pirotska' No 5, et. 2" -> "PIROTSKA 5"
    """
    if not raw_address:
        return "UNKNOWN"
        
    # 1. Transliterate/Cleanup (Simplified for this example)
    clean = raw_address.lower()
    
    # 2. Remove common prefixes
    prefixes = [r"ul\.", r"ulitsa", r"str\.", r"street", r"bulevard", r"bul\.", r"bl\.", r"block"]
    for p in prefixes:
        clean = re.sub(p, "", clean)
        
    # 3. Remove punctuation
    clean = re.sub(r"[,'\"\.]", " ", clean)
    
    # 4. Extract Street Name and Number
    # Looking for: (Text) ... (Number)
    # This is a heuristic; production needs a better geocoder
    match = re.search(r"([a-z\s]+)\s+(\d+)", clean)
    if match:
        street = match.group(1).strip().upper()
        number = match.group(2)
        return f"{street} {number}"
        
    return clean.strip().upper()

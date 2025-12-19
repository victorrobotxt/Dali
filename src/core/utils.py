from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_url(url: str) -> str:
    """
    Strips tracking parameters and fragments from real estate URLs.
    Example: ...imot.cgi?act=5&adv=123&utm_medium=fb -> ...imot.cgi?act=5&adv=123
    """
    u = urlparse(url)
    query = dict(parse_qsl(u.query))
    
    # Keep only essential keys for imot.bg and similar
    # act=5 is common for search results, adv=ID is the unique ad identifier
    whitelist = {'act', 'adv', 'id', 'slink'}
    clean_query = {k: v for k, v in query.items() if k.lower() in whitelist}
    
    # Reconstruct
    return urlunparse((
        u.scheme,
        u.netloc,
        u.path,
        u.params,
        urlencode(clean_query),
        '' # Strip fragments (#)
    ))

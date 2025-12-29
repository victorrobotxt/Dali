# Scraper Protocol V2 (Desktop/Legacy)

## Problem
The previous scraper targeted `m.imot.bg` (Mobile), which uses:
1.  **Empty HTML Shells:** Content is loaded via JavaScript/XHR, breaking standard parsers.
2.  **Strict WAF:** Cloudflare aggressively challenges TLS fingerprints on mobile endpoints.
3.  **Hidden Data:** Phone numbers and broker details are obfuscated.

## Solution: The "Desktop Fallback" Strategy
We switched the scraper to target `www.imot.bg` (Desktop) with specific headers to force the **Legacy HTML** version.

### Key Specs
* **Target:** `https://www.imot.bg/pcgi/imot.cgi?act=5&adv=...`
* **Encoding:** `windows-1251` (Critical: UTF-8 decoding causes mojibake).
* **Parsing:** Pure **Regex** (No `BeautifulSoup` or `Pydantic` needed).
    * *Reason:* The desktop site uses nested `<table>` structures ("Table Soup") which are hard to traverse with DOM parsers but easy to scrape with loose Regex patterns.

### Extracted Fields
* **Price:** Regex scan for `class="cena"`.
* **Images:** Extracted from `bigPicture()` JS calls (High-Res).
* **Phone:** Scanned from the entire body (bypasses "Show Phone" clicks).
* **Description:** Extracted from `#description_div`.

### Termux Compatibility
* Removed `pydantic` and `playwright` dependencies.
* Scraper is now 100% standard library + `httpx`.

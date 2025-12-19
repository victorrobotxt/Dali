import httpx
from bs4 import BeautifulSoup
import re
import sys

def forensic_audit(url):
    # High-fidelity mobile headers to bypass basic WAF
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "bg-BG,bg;q=0.9",
        "Referer": "https://www.google.bg/",
        "Connection": "keep-alive"
    }

    print(f"\n[*] INITIATING DEEP AUDIT: {url}")
    
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
            resp = client.get(url)
            
            # IMOT handles encoding via windows-1251. 
            # We decode manually to prevent iconv-style crashes.
            raw_content = resp.content.decode('windows-1251', errors='replace')
            
            # Save for your manual inspection
            with open("forensics_dump.html", "w", encoding="utf-8") as f:
                f.write(raw_content)

            # --- BOT/WAF DETECTION ---
            if any(term in raw_content.lower() for term in ["captcha", "robot", "security check", "verify you are human"]):
                print("!!! [BLOCKER] WAF CHALLENGE DETECTED. Page is a Captcha wall. !!!")
                return

            soup = BeautifulSoup(raw_content, 'html.parser')

            # --- TITLE & STATUS ---
            title = soup.find('title')
            print(f"[+] Page Title: {title.text.strip() if title else 'N/A'}")
            print(f"[+] HTTP Status: {resp.status_code}")

            # --- PILLAR I: PRICE EXTRACTION ---
            print("\n[*] PILLAR I: PRICE RECONNAISSANCE")
            # Common IMOT ID for price
            price_obs = soup.find(id='price_obs')
            if price_obs:
                print(f"    [FOUND] ID='price_obs': {price_obs.text.strip()}")
            else:
                # Fallback: Look for large font tags which Imot often uses
                big_text = soup.find_all(style=re.compile("font-size:30px|font-size:25px"))
                for bt in big_text:
                    print(f"    [FOUND] Large Font Element: {bt.text.strip()}")

            # --- PILLAR II: AREA & LOCATION ---
            print("\n[*] PILLAR II: METADATA SCRAPING")
            text_body = soup.get_text(" ", strip=True)
            
            # Search for Price + Currency pattern in decoded text
            # This detects if the price is just raw text or obfuscated
            price_matches = re.findall(r'(\d+[\s\d\.]*)\s?(EUR|€|лв|BGN|EUR)', text_body)
            print(f"    [TEXT SEARCH] Price matches found: {price_matches[:3]}")
            
            # Search for Area pattern
            area_matches = re.findall(r'(\d+)\s?(кв\.м|кв|sq\.m|m2)', text_body, re.IGNORECASE)
            print(f"    [TEXT SEARCH] Area matches found: {area_matches[:3]}")

            # --- PILLAR III: IMAGE AUDIT ---
            print("\n[*] PILLAR III: IMAGE ASSET AUDIT")
            images = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)
            
            print(f"    [COUNT] Total Images: {len(images)}")
            print("    [SAMPLE] First 3 Image Sources:")
            for img in images[:3]:
                print(f"      - {img}")

            print("\n[+] Audit Complete. Data saved to forensics_dump.html")

    except Exception as e:
        print(f"[!] SYSTEM FAILURE: {str(e)}")

if __name__ == "__main__":
    # Test with the specific listing you provided
    forensic_audit("https://www.imot.bg/pcgi/imot.cgi?act=5&adv=1c171899111")

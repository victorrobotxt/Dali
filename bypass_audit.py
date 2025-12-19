import httpx
from bs4 import BeautifulSoup
import time
import re

def bypass_audit(url):
    # Professional Browser Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.bg/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }

    # Use a Client to maintain Cookies
    with httpx.Client(headers=headers, follow_redirects=True, timeout=20.0) as client:
        print("[*] STEP 1: Handshake with Home Page...")
        home_resp = client.get("https://www.imot.bg")
        print(f"[+] Home Page Status: {home_resp.status_code}")
        print(f"[+] Cookies Acquired: {list(client.cookies.keys())}")

        print("[*] STEP 2: Waiting (Simulating Human)...")
        time.sleep(2.5)

        print(f"[*] STEP 3: Attempting to access target: {url}")
        # Update Referer to look like we clicked from the home page
        client.headers.update({"Referer": "https://www.imot.bg/"})
        
        resp = client.get(url)
        content = resp.content.decode('windows-1251', errors='replace')

        if any(term in content.lower() for term in ["captcha", "robot", "security check"]):
            print("!!! [FAIL] Still Blocked by WAF. They require JavaScript execution. !!!")
            
            # Save the failure page to see what the challenge looks like
            with open("waf_challenge.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("[i] Challenge page saved to waf_challenge.html. Check if it's Cloudflare or internal.")
            return

        print(f"[SUCCESS] Content Length: {len(content)} chars")
        
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.find('title')
        print(f"[+] Listing Title: {title.text.strip() if title else 'N/A'}")

        # Look for the price to confirm success
        price = soup.find(id='price_obs')
        if price:
            print(f"[!!!] PRICE DETECTED: {price.text.strip()}")
        else:
            print("[?] Price tag not found. Listing might be hidden in script tags.")

if __name__ == "__main__":
    bypass_audit("https://www.imot.bg/pcgi/imot.cgi?act=5&adv=1c171899111")

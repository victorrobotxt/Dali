import httpx
from bs4 import BeautifulSoup

def manual_audit(url, cookie_string):
    # This cookie_string you will copy from your real phone browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Cookie": cookie_string,
        "Accept-Language": "bg-BG,bg;q=0.9",
        "Referer": "https://www.imot.bg/"
    }

    with httpx.Client(headers=headers, timeout=15.0) as client:
        resp = client.get(url)
        content = resp.content.decode('windows-1251', errors='replace')
        
        if "captcha" in content.lower():
            print("[-] FAIL: Cookie was rejected or expired.")
        else:
            print("[+] SUCCESS: Bypass confirmed via Session Injection.")
            soup = BeautifulSoup(content, 'html.parser')
            price = soup.find(id='price_obs')
            if price:
                print(f"    [!!!] REVEALED PRICE: {price.text.strip()}")

if __name__ == "__main__":
    # YOU NEED TO FILL THIS FROM YOUR BROWSER
    MY_COOKIE = "imot_session_redirect=...; sid=...;" 
    manual_audit("https://www.imot.bg/pcgi/imot.cgi?act=5&adv=1c171899111", MY_COOKIE)

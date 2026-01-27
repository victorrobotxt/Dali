import httpx
from bs4 import BeautifulSoup
import os
import re
import sys

def scrape_law(url: str, filename: str):
    print(f"[*] Targeting Lex.bg: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile Safari/604.1"
    }

    try:
        # 1. Fetch raw bytes to handle encoding manually
        with httpx.Client(headers=headers, timeout=60.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            
            # Decode using windows-1251 as identified in our curl test
            content = resp.content.decode('windows-1251', errors='replace')
            
        # 2. Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # 3. Clean up the DOM (Remove ads, menus, scripts)
        # We saw these in your 'cnt' div test
        for noise in soup(["script", "style", "iframe", "ins"]):
            noise.decompose()
            
        ad_patterns = [r"adocean", r"mobileMenu", r"tma-ad", r"h-cnt"]
        for div in soup.find_all("div"):
            div_id = div.get("id", "")
            div_class = " ".join(div.get("class", []))
            if any(re.search(p, div_id) or re.search(p, div_class) for p in ad_patterns):
                div.decompose()

        # 4. Target the Law Body
        # Based on your grep, 'cnt' is the wrapper and 'boxi' is the inner content
        law_body = soup.find("div", class_="boxi") or soup.find("div", class_="cnt")
        
        if not law_body:
            print("[!] Could not find law container. Saving whole page.")
            law_body = soup.body

        # 5. Extract text with formatting
        # We use a separator to keep Articles (Чл.) on new lines
        raw_text = law_body.get_text(separator="\n")
        
        # 6. Post-Processing Cleanup
        # Remove massive gaps of whitespace
        clean_text = re.sub(r'\n\s*\n', '\n\n', raw_text)
        # Standardize the 'Article' prefix for easier RAG searching later
        clean_text = re.sub(r'(?m)^Чл\.', '\nЧл.', clean_text)

        # 7. Save to disk
        os.makedirs("storage/laws", exist_ok=True)
        path = f"storage/laws/{filename}.txt"
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"SOURCE: {url}\n")
            f.write("-" * 30 + "\n\n")
            f.write(clean_text)
            
        print(f"[SUCCESS] {filename}.txt created ({len(clean_text)} characters)")

    except Exception as e:
        print(f"[FATAL] Error during scraping: {str(e)}")

if __name__ == "__main__":
    # Link 1: Ordinance No. 7 (Crucial for Atelier vs Apartment height/light rules)
    ORD_7_URL = "https://lex.bg/mobile/ldoc/2135476546"
    scrape_law(ORD_7_URL, "naredba_7")

    # Link 2: ZUT (The Foundation)
    ZUT_URL = "https://lex.bg/mobile/ldoc/2135163904"
    scrape_law(ZUT_URL, "zut_law")


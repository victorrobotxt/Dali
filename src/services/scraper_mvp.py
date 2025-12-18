from bs4 import BeautifulSoup
import os

# CONFIG
SIMULATION_MODE = True
MOCK_FILE = "imot_simulation.html"

def run_recon():
    print("[*] INTEL: Starting Reconnaissance Protocol...")
    
    html_content = ""
    
    if SIMULATION_MODE:
        print(f"[*] MODE: SIMULATION (Bypassing WAF)")
        if not os.path.exists(MOCK_FILE):
            print(f"[!] Error: Mock file {MOCK_FILE} not found.")
            return
            
        with open(MOCK_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        # Network logic removed for Termux Safety
        pass

    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)
    
    print("[*] Parsing DOM Structure...")
    
    count = 0
    listings_found = []
    
    for link in links:
        href = link['href']
        
        if 'act=5' in href:
            # Normalize URL
            full_url = "https:" + href if href.startswith("//") else href
            
            if full_url in listings_found:
                continue
                
            listings_found.append(full_url)
            text_content = link.get_text(separator=" ", strip=True)
            
            count += 1
            print(f"\n[TARGET #{count}]")
            print(f"   URL: {full_url}")
            print(f"   RAW: {text_content}")

    print(f"\n[*] Mission Complete. {count} mock targets extracted.")

if __name__ == "__main__":
    run_recon()

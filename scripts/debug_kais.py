import requests
from bs4 import BeautifulSoup
import time
import re
import argparse
import sys
import json

# CONFIG
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://kais.cadastre.bg/bg/Map"

def run_forensics(args):
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest"
    })

    print("[1] HANDSHAKE...")
    try:
        resp = session.get(BASE_URL)
        soup = BeautifulSoup(resp.text, 'html.parser')
        token_el = soup.find('input', {'name': '__RequestVerificationToken'})
        if not token_el:
            print("FAILED: No token found. KAIS might be blocking.")
            return
        token = token_el.get('value')
    except Exception as e:
        print(f"Handshake Failed: {e}")
        return

    # --- QUERY CONSTRUCTION ---
    if args.query:
        search_kw = args.query
    else:
        # Construct "Google-style" query for FastSearch
        parts = []
        if args.district: parts.append(args.district)
        if args.street:   parts.append(args.street)
        if args.block:    parts.append(f"бл {args.block}")
        if args.number:   parts.append(args.number)
        if args.entrance: parts.append(f"вх {args.entrance}")
        search_kw = " ".join(parts)

    print(f"[2] TARGETING: '{search_kw}'...")
    
    # Always use FastSearch (more reliable than Detailed)
    session.get(f"{BASE_URL}/FastSearch", params={"KeyWords": search_kw})
    time.sleep(0.5)

    print("[3] FETCHING LIST...")
    headers = {"X-CSRF-TOKEN": token, "Referer": BASE_URL}

    # Fetch enough results to filter client-side
    resp = session.post(
        f"{BASE_URL}/ReadFoundObjects",
        data={"page": 1, "pageSize": args.limit * 5}, 
        headers=headers
    )

    data = resp.json()
    all_objects = data.get("Data", [])
    print(f"    -> Hits: {len(all_objects)}")

    # --- INTELLIGENT FILTERING ---
    filtered_objects = []
    for obj in all_objects:
        raw_display = f"{obj.get('DisplayText', '')} {obj.get('Address', '')}".lower()
        cad_num = obj.get('Number', '')
        
        # Filter: Exclude Apartments if requested (finding plots/buildings only)
        if args.plots_only:
             # PI (2 dots) or Building (3 dots). Apartments have 4+.
            if cad_num.count('.') > 3: continue 

        match = True
        
        # Filter: Strict Number Match
        if args.number and not args.query:
            # Regex for " 10 ", "No 10", "№10"
            pattern = r'(?:№|no\.?|\s|^)' + re.escape(args.number) + r'(?:\s|$|,|\.)'
            if not re.search(pattern, raw_display):
                match = False

        if match:
            filtered_objects.append(obj)

    target_list = filtered_objects[:args.limit]
    print(f"    -> Relevant Matches: {len(target_list)}")
    print(f"\n[4] FORENSIC SCANNING...")

    for obj in target_list:
        cad_num = obj.get('Number') or "N/A"
        
        try:
            info_url = f"{BASE_URL}/GetObjectInfo"
            resp_deep = session.get(info_url, params=obj)
            full_text = BeautifulSoup(resp_deep.text, 'html.parser').get_text(" ", strip=True)
            
            # --- PARSING LOGIC ---
            
            # Area
            area_m = re.search(r'площ\s*([\d\.]+)\s*кв', full_text, re.IGNORECASE)
            if not area_m: area_m = re.search(r'([\d\.]+)\s*кв\.\s*м', full_text, re.IGNORECASE)
            area = area_m.group(1) if area_m else "?"

            # Floor
            floor_m = re.search(r'(?:етаж|ет\.)\s*(\d+)', full_text, re.IGNORECASE)
            floor = floor_m.group(1) if floor_m else "-"

            # Ownership
            own_m = re.search(r'вид собств\.\s*([^,]+)', full_text, re.IGNORECASE)
            ownership = own_m.group(1).strip() if own_m else "?"

            # Neighbors (Crucial for Triangulation)
            neighbors_m = re.search(r'Съседи\s*:?\s*([\d\.,\s]+)', full_text, re.IGNORECASE)
            neighbors = neighbors_m.group(1).strip() if neighbors_m else "NONE"

            # Property Type Classification
            ft_lower = full_text.lower()
            if "пи " in ft_lower[:20] or "поземлен" in ft_lower: ptype = "LAND (ПИ)"
            elif "сграда" in ft_lower: ptype = "BUILDING"
            elif "жилище" in ft_lower or "апартамент" in ft_lower: ptype = "APARTMENT"
            else: ptype = "UNKNOWN"

            # --- REPORT ---
            print(f"\n--- {cad_num} ---")
            print(f"TYPE:  {ptype}")
            print(f"OWNER: {ownership}")
            print(f"AREA:  {area} m2")
            print(f"FLOOR: {floor}")
            if args.verbose:
                print(f"NEIGHBORS: {neighbors}")
            
            # If specifically looking for ownership/plot info, dump raw text
            if args.dump or ownership == "?" or "Няма данни" in ownership:
                print(f"RAW DUMP: {full_text[:500]}...")

        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(0.2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KAIS Forensic Tool')
    
    # Flexible Input
    parser.add_argument('-q', '--query', help='Direct query string (e.g. ID or Address)')
    
    # Structured Input
    parser.add_argument('-d', '--district', help='District name')
    parser.add_argument('-b', '--block', help='Block number')
    parser.add_argument('-s', '--street', help='Street name')
    parser.add_argument('-n', '--number', help='Street number')
    parser.add_argument('-e', '--entrance', help='Entrance')
    
    # Toggles
    parser.add_argument('--plots-only', action='store_true', help='Ignore apartments, find land/buildings')
    parser.add_argument('--verbose', action='store_true', help='Show neighbors and extra details')
    parser.add_argument('--dump', action='store_true', help='Always dump raw text')
    parser.add_argument('--limit', type=int, default=15, help='Max results')

    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    run_forensics(args)


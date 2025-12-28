import sys
import os
import argparse
Ensure src is in pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(file), '..')))
from src.services.cadastre_service import CadastreForensicsService
def run_audit(target: str, mode: str):
service = CadastreForensicsService()
print(f"--- GLASHAUS FORENSICS: {target} ---")

if mode == "scan":
    # Standard Scan
    results = service.search_object(target)
    print(f"[*] Found {len(results)} matches. Analyzing...")
    
    for obj in results[:20]: # Limit default view to 20
        data = service.deep_scan_unit(obj)
        print(f"\nUNIT: {data.get('cadastre_id')}")
        print(f"  TYPE:  {data.get('type')}")
        print(f"  OWNER: {data.get('ownership')}")
        print(f"  AREA:  {data.get('area')} m2")
        if data.get('floor'):
            print(f"  FLOOR: {data.get('floor')}")
        
        # If finding plots, show neighbors
        if data.get('type') == 'LAND':
            print(f"  NEIGHBORS: {data.get('neighbors')}")

elif mode == "social_check":
    # The Social Housing Audit
    report = service.analyze_social_risk(target)
    print("\n--- SOCIAL RISK REPORT ---")
    print(f"TOTAL UNITS SCANNED: {report['total_units']}")
    print(f"PRIVATE OWNED:       {report['private_units']}")
    print(f"MUNICIPAL (SOCIAL):  {report['municipal_units']}")
    print(f"RATIO:               {report['social_housing_ratio']:.2%}")
    print(f"VERDICT:             {report['risk_verdict']}")
    print("--------------------------")

if name == "main":
parser = argparse.ArgumentParser()
parser.add_argument("target", help="Query (Address or ID)")
parser.add_argument("--mode", choices=["scan", "social_check"], default="scan")
args = parser.parse_args()
run_audit(args.target, args.mode)


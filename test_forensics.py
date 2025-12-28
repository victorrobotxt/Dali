import asyncio
import sys
import json
from src.services.forensics_service import SofiaMunicipalForensics

# The identifier found in your curl examples (Bankya/Verdikal)
TEST_ID = "02659.2196.1102"

async def main():
    print(f"[*] Starting Forensic Audit for Cadastre ID: {TEST_ID}...")
    
    service = SofiaMunicipalForensics()
    try:
        results = await service.run_full_audit(TEST_ID)
        
        print("\n--- AUDIT RESULTS ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Validation Logic
        if results.get("expropriation", {}).get("is_expropriated"):
            print("\n[!] CRITICAL ALERT: Property is flagged for Expropriation!")
        
        if results.get("compliance_act16", {}).get("has_act16"):
            print("\n[+] SUCCESS: Act 16 Certificate Found.")
        else:
            print("\n[-] WARNING: No Act 16 found.")
            
    except Exception as e:
        print(f"\n[!] FATAL ERROR: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

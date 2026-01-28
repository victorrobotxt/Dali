import asyncio
import httpx
import sys
import os

# Add src to path so we can import the service
sys.path.append(os.getcwd())

from src.services.cadastre_service import CadastreService

# TARGET: Use the address from your curl example
TARGET_ADDRESS = "68134.4091.84.3.1" 
# Or use a text address: "гр. София, ж.к. Младост 2, бл. 219Б"

async def main():
    print(f"🕵️  STARTING FORENSIC AUDIT ON: {TARGET_ADDRESS}")
    print("-" * 50)
    
    # Initialize Client with HTTP/2 enabled if possible, standard timeouts
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        service = CadastreService(client)
        
        # Run the Audit
        result = await service.get_official_details(TARGET_ADDRESS)
        
        print("\n✅ AUDIT COMPLETE")
        print("-" * 50)
        print(f"🆔 Cadastre ID:    {result.cadastre_id}")
        print(f"📏 Official Area:  {result.official_area} sq.m")
        print(f"🏢 Official Addr:  {result.address_found}")
        print(f"⚠️ Social Risk:    {result.social_risk_ratio * 100}% (Municipal Density)")
        print(f"📡 Status:         {result.status}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
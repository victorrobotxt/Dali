# System Architecture

## Core Logic Flow (Cost Optimized)
1. **Ingest:** Scraper Service fetches URL.
2. **Analysis Tier 1 (Cheap):** Text Extraction (Gemini Flash).
   - *Goal:* Find Address in text.
   - *Cost:* ~$0.04/run.
3. **Gatekeeper:** Confidence Check (>90%).
4. **Analysis Tier 2 (Expensive):** Visual Detective (Gemini Pro).
   - *Trigger:* Only if Tier 1 fails.
   - *Goal:* Identify building via Facade/Landmarks/Geofencing.
   - *Cost:* ~$0.22/run.
5. **Verification:** Cross-reference extracted Address vs Cadastre API.

## Tech Stack
- **Lang:** Python (FastAPI) or Java (Spring Boot) - TBD
- **DB:** PostgreSQL + PostGIS (Geospatial extensions)
- **Queue:** Redis (Task offloading)

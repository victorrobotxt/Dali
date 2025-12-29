# System Architecture

## Core Logic Flow (Forensic Loop)
The system uses an Event-Driven architecture to orchestrate parallel forensic checks.

1. **Ingest & Normalize:**
   - Scraper Service fetches URL (handling `windows-1251` encoding).
   - URLs are normalized and deduplicated via content hash.

2. **The "Forensic Audit" Task (Celery Worker):**
   - **Step A: Multimodal AI Analysis (Gemini File API):**
     - **Ingest:** Images are downloaded locally, then uploaded to Google Gemini via the **File API** (bypassing inline payload limits).
     - **Vision:** Detects "Atelier" traps, estimates construction year, and performs inventory counts (AC/Radiators).
     - **Cleanup:** Remote file handles are deleted immediately after inference.
     - **Text:** Extracts unstructured data (Address, Construction Year, Heating types).

   - **Step B: Geospatial Triangulation:**
     - Cross-references AI-detected landmarks against the claimed neighborhood using Google Maps Geocoding.

   - **Step C: Unified Municipal Audit (NAG Registry):**
     - **Expropriation Check (The "Death List"):** Checks for municipal seizure plans.
     - **Compliance Check (The "Green List"):** Verifies "Act 16" status.
     - **Permit History:** Scans for valid building permits.

   - **Step D: Risk Engine V2:**
     - Merges all data points to calculate a composite `Risk Score` (0-100).

3. **Report Generation:**
   - `AttorneyReportGenerator` synthesizes a human-readable legal brief.

## Tech Stack
- **Service Layer:** Python 3.11 (FastAPI)
- **Asynchronous Task Queue:** Celery + Redis
- **Database:** PostgreSQL + PostGIS (Spatial data)
- **AI Model:** Google Gemini 3.0 Flash (Multimodal via File API)

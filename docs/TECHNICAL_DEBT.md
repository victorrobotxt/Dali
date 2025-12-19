# TECHNICAL DEBT LOG

## Critical Severity (Must Fix Before Beta)

### 1. Hardcoded Secrets (Config)
- **Location:** `src/core/config.py`
- **Issue:** `GEMINI_API_KEY` defaults to "mock-key". While validated at runtime, this is bad practice.
- **Fix:** Remove default value entirely and force `.env` loading.

### 2. Scraper Fragility (DOM Coupling)
- **Location:** `src/services/scraper_service.py` & `forensic_check.py`
- **Issue:** Logic relies on specific HTML IDs (e.g., `id='price'`, `id='description_div'`).
- **Risk:** High. If `imot.bg` updates their frontend classes, the "Space Hack" and Price normalization logic will fail silently.
- **Fix:** Implement multi-selector fallbacks or move strictly to Visual DOM analysis (Gemini Vision) for extraction.

## Moderate Severity (Optimization)

### 3. Synchronous Registry Calls in Loops
- **Location:** `src/services/forensics_service.py`
- **Issue:** While the task itself is async, some specialized sub-checks might still block the event loop if not strictly awaited.
- **Fix:** Audit all `httpx` calls to ensure `await` is used consistently across the `gather()` chain.

## Resolved Items (Fixed)

### ✅ Database Session Scope in Background Tasks
- **Fix:** `src/tasks.py` now explicitly initializes a thread-safe session using `with SessionLocal() as db:` inside the Celery worker.

### ✅ Risk Scoring Algorithm
- **Fix:** `RiskEngine` (V2) is implemented (`src/services/risk_engine.py`). It now calculates scores based on Expropriation (Fatal), Act 16 status, and Area discrepancy > 25%.

### ✅ Listing Normalization
- **Fix:** `RealEstateRepository` now normalizes URLs (forcing mobile subdomains) and checks for duplicates before insertion.

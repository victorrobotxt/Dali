# TECHNICAL DEBT LOG

## Critical Severity (Must Fix Before Beta)

### 1. Database Session Scope in Background Tasks
- **Location:** `src/api/routes.py` -> `initiate_audit`
- **Issue:** Passing the dependency-injected `db` session to `BackgroundTasks` causes `DetachedInstanceError` because the session closes when the HTTP response returns.
- **Fix:** Refactor `process_audit_task` to instantiate a fresh `SessionLocal()` context manager internally.
- **Reference:** SQLAlchemy Thread-Safety docs.

### 2. AI Service Implementation
- **Location:** `src/services/ai_engine.py`
- **Issue:** Currently returns mock dictionary `{"confidence": 0.0}`.
- **Fix:** 
    - Initialize `genai.configure(api_key=...)`.
    - Implement `generate_content` call for Gemini Flash (Text).
    - Implement `generate_content` with Image inputs for Gemini Pro (Vision).
    - Add Error Handling for "Safety Filters" or API Quotas.

## Moderate Severity (Logic Gaps)

### 3. Risk Scoring Algorithm
- **Location:** Database Schema exists (`risk_score`), but logic is missing.
- **Issue:** No calculator exists to translate discrepancies into a 0-100 integer.
- **Fix:** Create `src/services/risk_engine.py`.
    - Base Score: 0
    - If `advertised_area` > `cadastre_area` (+20 pts).
    - If `type` mismatch (Atelier vs Apt) (+30 pts).
    - If `price_per_sqm` > 1.5x avg (+15 pts).

### 4. Hardcoded Secrets
- **Location:** `src/core/config.py`
- **Issue:** Default "mock-key" risks silent failure in prod.
- **Fix:** Implement `pydantic` validation to raise `ValueError` on startup if `GEMINI_API_KEY` is missing in production environment.

## Low Severity (Optimization)

### 5. Listing Normalization
- **Location:** `src/services/repository.py`
- **Issue:** Duplicate URLs might occur if query params differ (e.g., `?adv=1` vs `?adv=1&utm=facebook`).
- **Fix:** Implement a URL cleaner utility to strip tracking parameters before hashing/storing.

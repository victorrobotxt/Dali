# TECHNICAL DEBT LOG

## Critical Severity (Must Fix Before Beta)

### 1. Scraper Fragility (DOM Coupling)
- **Location:** `src/services/scraper_service.py`
- **Issue:** Logic relies on specific HTML IDs or classes (e.g., `.price`).
- **Risk:** High. If `imot.bg` updates their frontend classes, extraction fails.
- **Fix:** Implement multi-selector fallbacks or move strictly to Visual DOM analysis (Gemini Vision) for extraction.
- **[span_54](start_span)[span_55](start_span)Update:** Mobile subdomain enforcement (`m.imot.bg`) has improved stability[span_54](end_span)[span_55](end_span).

### 2. Hardcoded Secrets (Config)
- **Location:** `src/core/config.py`
- **[span_56](start_span)[span_57](start_span)Issue:** `GEMINI_API_KEY` type hint implies no default, but mock keys or defaults exist in code logic[span_56](end_span)[span_57](end_span).
- **Fix:** Ensure strict environment variable enforcement in production Docker builds.

## Resolved Items (Fixed)

### ✅ Synchronous Registry Calls
- **[span_58](start_span)Fix:** `SofiaMunicipalForensics` (`src/services/forensics_service.py`) now uses `asyncio.gather` to run Expropriation, Act 16, and Permit checks in parallel[span_58](end_span).

### ✅ Database Session Scope in Background Tasks
- **[span_59](start_span)[span_60](start_span)Fix:** `src/tasks.py` explicitly initializes thread-safe sessions using `with SessionLocal() as db:`[span_59](end_span)[span_60](end_span).

### ✅ Risk Scoring Algorithm
- **[span_61](start_span)[span_62](start_span)Fix:** `RiskEngine` (V2) implemented in `src/services/risk_engine.py`[span_61](end_span)[span_62](end_span). [span_63](start_span)[span_64](start_span)Includes checks for "Infrastructure Mismatch" (Radiators) and "Location Fraud"[span_63](end_span)[span_64](end_span).

### ✅ Financial & Area Precision
- **[span_65](start_span)Fix:** Database schema migrated to `NUMERIC(12,2)` for price and `NUMERIC(10,2)` for area (Migration 002 & 003)[span_65](end_span).

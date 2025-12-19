# System Architecture

## Core Logic Flow (Forensic Loop)
The system uses an Event-Driven architecture to orchestrate parallel forensic checks.

1. **Ingest & Normalize:** - Scraper Service fetches URL (handling `windows-1251` encoding).
   - URLs are normalized (mobile subdomain enforcement) and deduplicated via content hash.

2. **The "Forensic Audit" Task (Celery Worker):**
   Unlike the initial design, the system now runs a **consolidated parallel audit** rather than a tiered fallback.
   - **Step A: Text Analysis (Gemini Flash):** Extracts unstructured data (Address, Construction Year, Atelier status).
   - **Step B: Official Registry Checks (Async/Parallel):**
     - **Cadastre Service:** Verifies official area vs advertised area using the extracted address.
     - **City Risk Service (NAG):** Checks Sofia Municipal records for Expropriation (seizure) risks.
     - **Compliance Service:** Verifies "Act 16" (Commissioning Certificate) status against the cadastral ID.
   - **Step C: Risk Engine V2:**
     - Merges all data points to calculate a composite `Risk Score` (0-100).
     - Identifies "Fatal" flags (e.g., Expropriation = 100% Risk).

3. **Report Generation:** - `AttorneyReportGenerator` synthesizes a human-readable legal brief from the structured forensic data.

## Tech Stack
- **Service Layer:** Python 3.11 (FastAPI)
- **Asynchronous Task Queue:** Celery + Redis
- **Database:** PostgreSQL + PostGIS (Spatial data)
- **Resilience:** Circuit Breakers implemented for Government Registry downtime (handling `httpx.ConnectError`).

## Critical Components
| Component | Function | Status |
| :--- | :--- | :--- |
| **Risk Engine** | Calculates score based on Area Fraud, Legal Status (Atelier), and Expropriation. | ✅ Implemented (V2) |
| **Forensics Service** | Manages sessions with `nag.sofia.bg` and `kais.cadastre.bg`. | ✅ Implemented |
| **Storage Service** | Archives listing images to disk/S3 for evidence preservation. | ✅ Implemented |

## Database Schema (Live State)
*Synced with `src/db/models.py` and Alembic Migrations 001-003.*

### 1. Listings Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | PK |
| `source_url` | String | Unique Index |
| `content_hash` | String(64) | **Idempotency**: SHA256(text + price) |
| `price_bgn` | **Numeric(12,2)** | Financial precision (e.g., 150000.00) |
| `advertised_area_sqm` | **Numeric(10,2)** | Area precision (e.g., 65.50) |
| `description_raw` | Text | Full ad body |

### 2. Reports Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | PK |
| `listing_id` | Integer | FK -> Listings |
| `status` | Enum | `PENDING`, `PROCESSING`, `VERIFIED`, `MANUAL_REVIEW`, `REJECTED` |
| `risk_score` | Integer | 0-100 (100 = Fatal) |
| `ai_confidence_score` | Integer | 0-100 (Hallucination check) |
| `cost_to_generate` | **Numeric(10,4)** | API Cost tracking (e.g., 0.0045 BGN) |
| `discrepancy_details` | JSON | Specific flags (e.g. "Area mismatch > 25%") |

### 3. Buildings Table (Registry Truth)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | PK |
| `cadastre_id` | String | Unique Official ID |
| `construction_year` | Integer | Registry confirmed year |
| `latitude/longitude` | Float | Geocoded coordinates |

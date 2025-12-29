# System Architecture

## Core Logic Flow (Forensic Loop)
The system uses an Event-Driven architecture to orchestrate parallel forensic checks.

1. **Ingest & Normalize:**
   - [span_0](start_span)Scraper Service fetches URL (handling `windows-1251` encoding)[span_0](end_span).
   - [span_1](start_span)[span_2](start_span)URLs are normalized (mobile subdomain enforcement) and deduplicated via content hash[span_1](end_span)[span_2](end_span).

2. **The "Forensic Audit" Task (Celery Worker):**
   [span_3](start_span)[span_4](start_span)The system runs a **consolidated parallel audit** combining OSINT and Official Registry data[span_3](end_span)[span_4](end_span).
   
   - **Step A: Multimodal AI Analysis (Gemini 3.0 Flash):**
     - **[span_5](start_span)[span_6](start_span)[span_7](start_span)Vision:** Detects "Atelier" traps, estimates construction year, and performs inventory counts (AC/Radiators)[span_5](end_span)[span_6](end_span)[span_7](end_span).
     - **[span_8](start_span)Text:** Extracts unstructured data (Address, Construction Year, Heating types)[span_8](end_span).
   
   - **Step B: Geospatial Triangulation:**
     - [span_9](start_span)[span_10](start_span)Cross-references AI-detected landmarks against the claimed neighborhood using Google Maps Geocoding[span_9](end_span)[span_10](end_span).
   
   - **Step C: Unified Municipal Audit (NAG Registry):**
     - **[span_11](start_span)[span_12](start_span)Expropriation Check (The "Death List"):** Checks for municipal seizure plans[span_11](end_span)[span_12](end_span).
     - **[span_13](start_span)[span_14](start_span)Compliance Check (The "Green List"):** Verifies "Act 16" (Commissioning Certificate) status[span_13](end_span)[span_14](end_span).
     - **[span_15](start_span)Permit History:** Scans for valid building permits[span_15](end_span).
   
   - **Step D: Risk Engine V2:**
     - [span_16](start_span)[span_17](start_span)Merges all data points to calculate a composite `Risk Score` (0-100)[span_16](end_span)[span_17](end_span).
     - **[span_18](start_span)Fatal Flags:** Immediate rejection (e.g., Active Expropriation)[span_18](end_span).
     - **[span_19](start_span)[span_20](start_span)Discrepancy Flags:** Area Fraud (>25%), Missing Radiators vs. Central Heating claims[span_19](end_span)[span_20](end_span).

3. **Report Generation:**
   - [span_21](start_span)[span_22](start_span)`AttorneyReportGenerator` synthesizes a human-readable legal brief from the structured forensic data[span_21](end_span)[span_22](end_span).

## Tech Stack
- **[span_23](start_span)Service Layer:** Python 3.11 (FastAPI)[span_23](end_span)
- **[span_24](start_span)Asynchronous Task Queue:** Celery + Redis[span_24](end_span)
- **[span_25](start_span)Database:** PostgreSQL + PostGIS (Spatial data)[span_25](end_span)
- **[span_26](start_span)[span_27](start_span)AI Model:** Google Gemini 3.0 Flash (Multimodal)[span_26](end_span)[span_27](end_span)
- **[span_28](start_span)[span_29](start_span)Resilience:** Circuit Breakers implemented for Government Registry downtime[span_28](end_span)[span_29](end_span).

## Critical Components
| Component | Function | Status |
| :--- | :--- | :--- |
| **Risk Engine** | Calculates score based on Area Fraud, Legal Status (Atelier), Expropriation, and Radiator/Heating mismatches. | [span_30](start_span)[span_31](start_span)✅ Implemented (V2)[span_30](end_span)[span_31](end_span) |
| **SofiaMunicipalForensics** | Unified interface for `nag.sofia.bg` registries (Expropriation, Permits, Act 16). | [span_32](start_span)✅ Implemented[span_32](end_span) |
| **CadastreForensics** | Handles "Social Housing" risk detection and ownership ratio scanning. | [span_33](start_span)✅ Implemented[span_33](end_span) |

## Database Schema (Live State)
*Synced with `src/db/models.py` and Alembic Migrations 001-003.*

### 1. Listings Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | [span_34](start_span)PK[span_34](end_span) |
| `source_url` | String | [span_35](start_span)Unique Index[span_35](end_span) |
| `content_hash` | String(64) | **[span_36](start_span)Idempotency**: SHA256(text + price)[span_36](end_span) |
| `price_bgn` | **Numeric(12,2)** | [span_37](start_span)[span_38](start_span)Financial precision (e.g., 150000.00)[span_37](end_span)[span_38](end_span) |
| `advertised_area_sqm` | **Numeric(10,2)** | [span_39](start_span)[span_40](start_span)Area precision (e.g., 65.50)[span_39](end_span)[span_40](end_span) |
| `description_raw` | Text | [span_41](start_span)Full ad body[span_41](end_span) |

### 2. Reports Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | [span_42](start_span)PK[span_42](end_span) |
| `listing_id` | Integer | [span_43](start_span)FK -> Listings[span_43](end_span) |
| `status` | Enum | [span_44](start_span)`PENDING`, `PROCESSING`, `VERIFIED`, `MANUAL_REVIEW`, `REJECTED`[span_44](end_span) |
| `risk_score` | Integer | [span_45](start_span)0-100 (100 = Fatal)[span_45](end_span) |
| `ai_confidence_score` | Integer | [span_46](start_span)0-100 (Hallucination check)[span_46](end_span) |
| `cost_to_generate` | **Numeric(10,4)** | [span_47](start_span)[span_48](start_span)API Cost tracking (e.g., 0.0045 BGN)[span_47](end_span)[span_48](end_span) |
| `discrepancy_details` | JSON | [span_49](start_span)Specific flags (e.g. "Area mismatch > 25%")[span_49](end_span) |

### 3. Buildings Table (Registry Truth)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | [span_50](start_span)PK[span_50](end_span) |
| `cadastre_id` | String | [span_51](start_span)Unique Official ID[span_51](end_span) |
| `construction_year` | Integer | [span_52](start_span)Registry confirmed year[span_52](end_span) |
| `latitude/longitude` | Float | [span_53](start_span)Geocoded coordinates[span_53](end_span) |

from asgiref.sync import async_to_sync
from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.legal_engine import LegalEngine
from src.services.report_generator import AttorneyReportGenerator
from src.services.storage_service import StorageService
from src.services.repository import RealEstateRepository
from src.services.cadastre_service import CadastreService
from src.services.compliance_service import ComplianceService
from src.services.city_risk_service import CityRiskService
from src.services.risk_engine import RiskEngine
from src.core.utils import calculate_content_hash
from src.core.config import settings
from src.schemas import ScrapedListing, AIAnalysisResult, RegistryCheck
from src.core.logger import logger
import asyncio
import httpx

@celery_app.task(name="src.tasks.audit_listing", bind=True, 
                 autoretry_for=(Exception,), 
                 retry_backoff=True, max_retries=3)
def audit_listing_task(self, listing_id: int):
    """Bridge sync Celery worker to async pipeline safely."""
    return async_to_sync(run_audit_pipeline)(listing_id)

async def run_audit_pipeline(listing_id: int):
    log = logger.bind(listing_id=listing_id)
    log.info("audit_started")

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        with SessionLocal() as db:
            try:
                # 1. Init Services
                repo = RealEstateRepository(db)
                scraper = ScraperService(client=http_client, simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
                ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
                
                cadastre = CadastreService(client=http_client)
                compliance = ComplianceService(client=http_client)
                city_risk = CityRiskService(client=http_client)
                
                storage = StorageService()
                legal_engine = LegalEngine()
                brief_gen = AttorneyReportGenerator()
                risk_engine = RiskEngine()

                listing = db.query(Listing).get(listing_id)
                if not listing: return "Error: Listing not found"

                # 2. Scrape
                scraped_data: ScrapedListing = await scraper.scrape_url(listing.source_url)
                
                # 3. Idempotency
                current_hash = calculate_content_hash(scraped_data.raw_text, float(scraped_data.price_predicted))
                if listing.content_hash == current_hash and listing.reports:
                    log.info("audit_skipped_unchanged")
                    return "Audit Skipped: Content Unchanged"

                # 4. AI Analysis
                ai_raw = await ai_engine.analyze_text(scraped_data.raw_text)
                ai_data = AIAnalysisResult(**ai_raw)

                # 5. Forensics (Parallel)
                cad_task = cadastre.get_official_details(ai_data.address_prediction)
                
                cad_data, comp_raw, risk_raw, archived_paths = await asyncio.gather(
                    cad_task, 
                    compliance.check_act_16(None), 
                    city_risk.check_expropriation(None),
                    storage.archive_images(listing_id, scraped_data.image_urls)
                )
                
                comp_data = RegistryCheck(**comp_raw)
                risk_data = RegistryCheck(**risk_raw)

                # 6. Update Listing Meta
                repo.update_listing_data(
                    listing_id, 
                    scraped_data.price_predicted,
                    scraped_data.area_sqm, 
                    scraped_data.raw_text, 
                    current_hash
                )

                # 7. Scoring
                forensic_dict = {
                    "scraped": scraped_data.model_dump(),
                    "ai": ai_data.model_dump(),
                    "cadastre": cad_data.model_dump(),
                    "compliance": comp_data.model_dump(),
                    "city_risk": risk_data.model_dump()
                }

                score_res = risk_engine.calculate_score_v2(forensic_dict)
                legal_res = legal_engine.analyze_listing(scraped_data.model_dump(), ai_data.model_dump())
                final_score = max(score_res["score"], legal_res["total_legal_score"])
                
                consolidated_risk = {**legal_res, **score_res, "forensics": forensic_dict}
                brief = brief_gen.generate_legal_brief(scraped_data.model_dump(), consolidated_risk, ai_data.model_dump())

                status = ReportStatus.VERIFIED if final_score < 40 else ReportStatus.MANUAL_REVIEW
                if score_res.get("is_fatal") or legal_res.get("gatekeeper_verdict") == "ABORT":
                    status = ReportStatus.REJECTED

                report = Report(
                    listing_id=listing_id,
                    status=status,
                    risk_score=final_score,
                    ai_confidence_score=ai_data.confidence_score,
                    legal_brief=brief,
                    discrepancy_details=consolidated_risk,
                    image_archive_urls=archived_paths,
                    cost_to_generate=0.04
                )
                db.add(report)
                db.commit()
                
                return f"Audit Complete: {status}"

            except Exception as exc:
                db.rollback()
                log.exception("audit_crashed")
                raise exc

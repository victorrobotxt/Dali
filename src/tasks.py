from asgiref.sync import async_to_sync
from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.storage_service import StorageService
from src.services.repository import RealEstateRepository
from src.services.cadastre_service import CadastreService
from src.services.compliance_service import ComplianceService
from src.services.city_risk_service import CityRiskService
from src.services.risk_engine import RiskEngine
from src.services.legal_engine import LegalEngine
from src.services.report_generator import AttorneyReportGenerator
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
    return async_to_sync(run_audit_pipeline)(listing_id)

async def run_audit_pipeline(listing_id: int):
    log = logger.bind(listing_id=listing_id)
    log.info("audit_started_multimodal")

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        with SessionLocal() as db:
            try:
                # 1. Init Services
                repo = RealEstateRepository(db)
                scraper = ScraperService(client=http_client)
                ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
                storage = StorageService()
                risk_engine = RiskEngine()
                legal_engine = LegalEngine()
                brief_gen = AttorneyReportGenerator()

                listing = db.query(Listing).get(listing_id)
                if not listing: return "Error: Listing not found"

                # 2. Scrape Data
                scraped_data: ScrapedListing = await scraper.scrape_url(listing.source_url)
                
                # 3. Archive Images FIRST (to enable Vision AI)
                archived_paths = await storage.archive_images(listing_id, scraped_data.image_urls)
                
                # 4. Multimodal AI Analysis (The "Vision AI" Update)
                ai_raw = await ai_engine.analyze_listing_multimodal(
                    scraped_data.raw_text, 
                    archived_paths
                )
                ai_data = AIAnalysisResult(**ai_raw)

                # 5. Parallel Forensic Registry Striking
                cadastre = CadastreService(client=http_client)
                compliance = ComplianceService(client=http_client)
                city_risk = CityRiskService(client=http_client)

                cad_data, comp_raw, risk_raw = await asyncio.gather(
                    cadastre.get_official_details(ai_data.address_prediction), 
                    compliance.check_act_16(None), # Cadastre ID needed here for real prod
                    city_risk.check_expropriation(None)
                )

                # 6. Final Risk Scoring & Brief Generation
                forensic_dict = {
                    "scraped": scraped_data.model_dump(),
                    "ai": ai_data.model_dump(),
                    "cadastre": cad_data.model_dump(),
                    "compliance": comp_raw,
                    "city_risk": risk_raw
                }
                
                score_res = risk_engine.calculate_score_v2(forensic_dict)
                legal_res = legal_engine.analyze_listing(scraped_data.model_dump(), ai_data.model_dump())
                final_score = max(score_res["score"], legal_res["total_legal_score"])
                
                report = Report(
                    listing_id=listing_id,
                    status=ReportStatus.VERIFIED if final_score < 40 else ReportStatus.MANUAL_REVIEW,
                    risk_score=final_score,
                    ai_confidence_score=ai_data.confidence_score,
                    legal_brief=brief_gen.generate_legal_brief(scraped_data.model_dump(), {**score_res, "forensics": forensic_dict}, ai_data.model_dump()),
                    discrepancy_details=forensic_dict,
                    image_archive_urls=archived_paths
                )
                db.add(report)
                db.commit()
                
                return f"Audit Complete: Score {final_score}"

            except Exception as exc:
                db.rollback()
                log.exception("audit_pipeline_failed")
                raise exc

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
import asyncio

@celery_app.task(name="src.tasks.audit_listing", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def audit_listing_task(self, listing_id: int):
    with SessionLocal() as db:
        try:
            repo = RealEstateRepository(db)
            scraper = ScraperService(simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
            ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
            storage = StorageService()
            legal_engine = LegalEngine()
            brief_gen = AttorneyReportGenerator()
            risk_engine = RiskEngine()
            
            cadastre = CadastreService()
            compliance = ComplianceService()
            city_risk = CityRiskService()

            listing = db.query(Listing).get(listing_id)
            if not listing: return "Error: Listing not found"

            # 1. Scrape
            scraped_data = scraper.scrape_url(listing.source_url)
            
            # 2. Async Forensics
            async def run_forensics():
                ai_res = await ai_engine.analyze_text(scraped_data["raw_text"])
                address_pred = ai_res.get("address_prediction", "")
                
                cad_res = await cadastre.get_official_details(address_pred) if address_pred else None
                cad_id = cad_res.get("cadastre_id") if cad_res else None
                
                tasks = [storage.archive_images(listing_id, scraped_data["image_urls"])]
                comp_task = compliance.check_act_16(cad_id)
                risk_task = city_risk.check_expropriation(cad_id)
                
                results = await asyncio.gather(tasks[0], comp_task, risk_task)
                return ai_res, cad_res, results[1], results[2], results[0]

            ai_data, cad_data, comp_data, risk_data, archived_paths = asyncio.run(run_forensics())

            # 3. Update Meta
            chash = calculate_content_hash(scraped_data["raw_text"], scraped_data["price_predicted"])
            repo.update_listing_data(listing_id, scraped_data["price_predicted"], scraped_data["area"], scraped_data["raw_text"], chash)

            # 4. Consolidate & Score
            forensic_data = {
                "scraped": scraped_data,
                "ai": ai_data,
                "cadastre": cad_data,
                "compliance": comp_data,
                "city_risk": risk_data
            }

            score_res = risk_engine.calculate_score_v2(forensic_data)
            legal_res = legal_engine.analyze_listing(scraped_data, ai_data)
            
            # MERGE DATA FOR LAWYER
            # This is the key fix: We pass everything to the generator
            consolidated_risk = {**legal_res, **score_res, "forensics": forensic_data}
            
            final_score = max(score_res["score"], legal_res["total_legal_score"])
            
            # Generate Brief
            brief = brief_gen.generate_legal_brief(scraped_data, consolidated_risk, ai_data)
            
            status = ReportStatus.VERIFIED if final_score < 40 else ReportStatus.MANUAL_REVIEW
            if score_res.get("is_fatal") or legal_res.get("gatekeeper_verdict") == "ABORT":
                status = ReportStatus.REJECTED

            # 5. Save
            report = Report(
                listing_id=listing_id,
                status=status,
                risk_score=final_score,
                ai_confidence_score=ai_data.get("confidence", 0),
                legal_brief=brief,
                discrepancy_details=consolidated_risk,
                image_archive_urls=archived_paths,
                cost_to_generate=0.04
            )
            db.add(report)
            db.commit()
            
            return f"Audit Complete: {status} (Score: {final_score})"

        except Exception as exc:
            db.rollback()
            raise exc

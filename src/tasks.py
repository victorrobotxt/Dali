from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.legal_engine import LegalEngine
from src.services.report_generator import AttorneyReportGenerator
from src.services.storage_service import StorageService
from src.services.repository import RealEstateRepository
from src.core.utils import calculate_content_hash
from src.core.config import settings
import asyncio

@celery_app.task(
    name="src.tasks.audit_listing",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5
)
def audit_listing_task(self, listing_id: int):
    # FIX: Use Context Manager for robust session handling to prevent connection leaks
    with SessionLocal() as db:
        try:
            # Initialize services that require DB access inside the context
            repo = RealEstateRepository(db)
            
            # Initialize stateless services
            scraper = ScraperService(simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
            ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
            storage = StorageService()
            legal_engine = LegalEngine()
            brief_gen = AttorneyReportGenerator()

            listing = db.query(Listing).get(listing_id)
            if not listing:
                return "Error: Listing not found"

            # 1. Scrape (Synchronous)
            scraped_data = scraper.scrape_url(listing.source_url)
            
            # 2. Async Wrapper for I/O bound tasks (Archive + AI)
            async def run_async_tasks():
                # Parallelize where possible
                images_task = storage.archive_images(listing_id, scraped_data["image_urls"])
                ai_task = ai_engine.analyze_text(scraped_data["raw_text"])
                return await asyncio.gather(images_task, ai_task)

            # Execute Async Block
            archived_paths, ai_data = asyncio.run(run_async_tasks())

            # 3. Update Listing Metadata
            chash = calculate_content_hash(scraped_data["raw_text"], scraped_data["price_predicted"])
            repo.update_listing_data(
                listing_id, 
                scraped_data["price_predicted"], 
                scraped_data["area"], 
                scraped_data["raw_text"], 
                chash
            )

            # 4. Legal Logic & Verdict
            legal_res = legal_engine.analyze_listing(scraped_data, ai_data)
            brief = brief_gen.generate_legal_brief(scraped_data, legal_res, ai_data)

            # Logic: Automatic rejection if specific fatal flags exist
            status = ReportStatus.VERIFIED if legal_res["total_legal_score"] < 40 else ReportStatus.MANUAL_REVIEW
            if legal_res.get("gatekeeper_verdict") == "ABORT":
                status = ReportStatus.REJECTED

            # 5. Final Report
            report = Report(
                listing_id=listing_id,
                status=status,
                risk_score=legal_res["total_legal_score"],
                ai_confidence_score=ai_data.get("confidence", 0),
                legal_brief=brief,
                discrepancy_details=legal_res,
                image_archive_urls=archived_paths,
                cost_to_generate=0.04
            )
            db.add(report)
            db.commit()
            
            return f"Audit Complete: {status} (Score: {legal_res['total_legal_score']})"

        except Exception as exc:
            db.rollback()
            # Re-raise to trigger Celery's autoretry
            raise exc

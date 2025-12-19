from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.repository import RealEstateRepository
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.risk_engine import RiskEngine
from src.services.storage_service import StorageService
from src.core.config import settings
from src.core.utils import calculate_content_hash
import asyncio

@celery_app.task(
    name="src.tasks.audit_listing",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def audit_listing_task(self, listing_id: int):
    # Context Manager for DB session
    with SessionLocal() as db:
        try:
            repo = RealEstateRepository(db)
            scraper = ScraperService(simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
            ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
            risk_engine = RiskEngine()
            storage = StorageService()

            listing = db.query(Listing).get(listing_id)
            if not listing: return "Error: Missing ID"

            # 1. SCRAPE & ARCHIVE
            data = scraper.scrape_url(listing.source_url)
            
            # Run async image archival
            loop = asyncio.get_event_loop()
            archived_images = loop.run_until_complete(storage.archive_images(listing_id, data["image_urls"]))

            # 2. IDEMPOTENCY & UPDATE
            chash = calculate_content_hash(data["raw_text"], data["price_predicted"])
            repo.update_listing_data(listing_id, data["price_predicted"], data["area"], data["raw_text"], chash)

            # 3. AI TIERS
            tier1 = loop.run_until_complete(ai_engine.analyze_text(data["raw_text"]))
            confidence = tier1.get("confidence", 0)
            total_cost = 0.04

            if (confidence < 85 or tier1.get("is_atelier")) and settings.GEMINI_API_KEY != "mock-key":
                tier2 = loop.run_until_complete(ai_engine.analyze_images(data["image_urls"]))
                tier1["vision_insights"] = tier2
                total_cost += 0.22
                if tier2.get("estimated_location_confidence", 0) > 60:
                    confidence = max(confidence, 90)

            # 4. RISK
            # Official Registry (Placeholder - logic stays same, data fetched via Repo later)
            report_data = risk_engine.calculate_score(data, tier1)
            
            repo.create_report(
                listing_id=listing_id,
                risk=report_data["score"],
                details={"flags": report_data["flags"], "ai": tier1},
                cost=total_cost,
                confidence=confidence,
                images=archived_images
            )
            return f"Audit Complete for {listing_id}"

        except Exception as exc:
            print(f"[RETRYING] Task failed: {exc}")
            raise self.retry(exc=exc)


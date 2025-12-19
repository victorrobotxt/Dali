from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing
from src.services.repository import RealEstateRepository
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.risk_engine import RiskEngine
from src.core.config import settings
import asyncio

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    """
    Background Task to scrape, analyze, and rate a listing.
    Replaces the previous BackgroundTasks implementation to ensure scalability.
    """
    db = SessionLocal()
    try:
        repo = RealEstateRepository(db)
        scraper = ScraperService(simulation_mode=True)
        ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
        risk_engine = RiskEngine()

        listing = db.query(Listing).get(listing_id)
        if not listing:
            return "Listing not found"

        # 1. SCRAPE
        print(f"[TASK] Scraping listing {listing_id}...")
        scraped_data = scraper.scrape_url(listing.source_url)
        listing.description_raw = scraped_data["raw_text"]
        db.commit()

        # 2. AI EXECUTION (Async Bridge)
        # Celery runs in sync mode, but GeminiService is async.
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        print(f"[TASK] Running AI Tier 1 (Text)...")
        tier1_result = loop.run_until_complete(ai_engine.analyze_text(scraped_data["raw_text"]))
        confidence = tier1_result.get("confidence", 0)
        final_ai_data = tier1_result
        total_cost = 0.04

        # 3. TIER 2: VISION ESCALATION
        if confidence < 80 and settings.GEMINI_API_KEY != "mock-key":
            print(f"[TASK] Escalating to Tier 2 (Vision)...")
            tier2_result = loop.run_until_complete(ai_engine.analyze_images(scraped_data["image_urls"]))
            final_ai_data["vision_insights"] = tier2_result
            total_cost += 0.22
            confidence = max(confidence, tier2_result.get("confidence", 0))

        # 4. RISK CALCULATION & REPORT
        report_data = risk_engine.calculate_score(scraped_data, final_ai_data)
        
        repo.create_report(
            listing_id=listing.id,
            risk=report_data["score"],
            details={"flags": report_data["flags"], "ai_meta": final_ai_data},
            cost=total_cost,
            confidence=confidence
        )
        return "Audit Complete"

    except Exception as e:
        print(f"[TASK_ERROR] {str(e)}")
        return f"Failed: {str(e)}"
    finally:
        db.close()

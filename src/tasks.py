from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing
from src.services.repository import RealEstateRepository
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.risk_engine import RiskEngine
from src.core.config import settings
from src.core.utils import calculate_content_hash
import asyncio

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    db = SessionLocal()
    try:
        repo = RealEstateRepository(db)
        scraper = ScraperService(simulation_mode=True)
        ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
        risk_engine = RiskEngine()

        listing = db.query(Listing).get(listing_id)
        if not listing: return "Listing not found"

        # 1. SCRAPE
        print(f"[TASK] Scraping listing {listing_id}...")
        scraped_data = scraper.scrape_url(listing.source_url)
        
        # 2. IDEMPOTENCY CHECK (Content Hashing)
        # We calculate hash NOW that we have the text
        current_hash = calculate_content_hash(scraped_data["raw_text"], listing.price_bgn or 0)
        
        # Check if this exact content exists elsewhere
        duplicate_id = repo.check_content_duplication(current_hash)
        
        if duplicate_id and duplicate_id != listing.id:
            print(f"[TASK] Duplicate content detected (matches Listing {duplicate_id}). Aborting AI.")
            # We mark it as processed but duplicate (logic could vary)
            repo.update_listing_content(listing.id, scraped_data["raw_text"], current_hash)
            return "Aborted: Duplicate Content"

        # Save hash and text
        repo.update_listing_content(listing.id, scraped_data["raw_text"], current_hash)

        # 3. AI EXECUTION (Guardrails Active)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        print(f"[TASK] Running AI Tier 1 (Text)...")
        tier1_result = loop.run_until_complete(ai_engine.analyze_text(scraped_data["raw_text"]))
        
        confidence = tier1_result.get("confidence", 0)
        final_ai_data = tier1_result
        total_cost = 0.04

        # 4. TIER 2 ESCALATION
        if confidence < 80 and settings.GEMINI_API_KEY != "mock-key":
            tier2_result = loop.run_until_complete(ai_engine.analyze_images(scraped_data["image_urls"]))
            final_ai_data["vision_insights"] = tier2_result
            total_cost += 0.22
            confidence = max(confidence, tier2_result.get("confidence", 0))

        # 5. RISK CALCULATION (With Area Math Support)
        # Note: We pass None for cadastre_area as we don't have the connector yet,
        # but the engine is now ready for it.
        report_data = risk_engine.calculate_score(scraped_data, final_ai_data, cadastre_area=None)
        
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

from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.repository import RealEstateRepository
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.risk_engine import RiskEngine
from src.services.cadastre_service import CadastreService
from src.services.geospatial_service import GeospatialService
from src.core.config import settings
from src.core.utils import calculate_content_hash, normalize_address
import asyncio

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    db = SessionLocal()
    try:
        repo = RealEstateRepository(db)
        
        # Initialize Services
        scraper = ScraperService(simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
        ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
        risk_engine = RiskEngine()
        cadastre_service = CadastreService()
        geo_service = GeospatialService() # Ready for future use

        listing = db.query(Listing).get(listing_id)
        if not listing: return "Listing not found"

        # 1. SCRAPE
        print(f"[TASK] Scraping listing {listing_id}...")
        scraped_data = scraper.scrape_url(listing.source_url)
            
        # 2. IDEMPOTENCY
        current_hash = calculate_content_hash(scraped_data["raw_text"], listing.price_bgn or 0)
        duplicate_id = repo.check_content_duplication(current_hash)
        if duplicate_id and duplicate_id != listing.id:
            repo.update_listing_content(listing.id, scraped_data["raw_text"], current_hash)
            return "Aborted: Duplicate Content"
        repo.update_listing_content(listing.id, scraped_data["raw_text"], current_hash)

        # 3. AI ANALYSIS (Async in Sync Worker)
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        print(f"[TASK] Running AI Tier 1...")
        tier1_result = loop.run_until_complete(ai_engine.analyze_text(scraped_data["raw_text"]))
        
        # 4. EXTERNAL DATA (Cadastre)
        address_found = tier1_result.get("address_prediction", "")
        clean_address = normalize_address(address_found)
        cadastre_data = cadastre_service.fetch_details(clean_address)
        
        official_area = cadastre_data.get("official_area") if cadastre_data else None

        # 5. TIER 2 VISION (Conditional)
        confidence = tier1_result.get("confidence", 0)
        final_ai_data = tier1_result
        total_cost = 0.04

        # Trigger Vision if confidence is low OR if it looks like an Atelier
        if (confidence < 80 or final_ai_data.get("is_atelier")) and settings.GEMINI_API_KEY != "mock-key":
            print(f"[TASK] Escalating to Tier 2 Vision...")
            tier2_result = loop.run_until_complete(ai_engine.analyze_images(scraped_data["image_urls"]))
            final_ai_data["vision_insights"] = tier2_result
            total_cost += 0.22
            # Boost confidence if vision found landmarks
            if tier2_result.get("estimated_location_confidence", 0) > 50:
                confidence = max(confidence, 85)

        # 6. RISK CALCULATION
        report_data = risk_engine.calculate_score(
            scraped_data, 
            final_ai_data, 
            cadastre_area=official_area
        )
        
        repo.create_report(
            listing_id=listing.id,
            risk=report_data["score"],
            details={"flags": report_data["flags"], "ai_meta": final_ai_data, "cadastre_match": bool(cadastre_data)},
            cost=total_cost,
            confidence=confidence
        )
        return "Audit Complete"

    except Exception as e:
        print(f"[TASK_ERROR] {str(e)}")
        # FAIL-SAFE: Update DB to REJECTED so UI doesn't hang
        try:
            # Re-connect in case main session is dead
            error_db = SessionLocal()
            error_report = error_db.query(Report).filter(Report.listing_id == listing_id).first()
            if not error_report:
                error_report = Report(listing_id=listing_id, status=ReportStatus.REJECTED)
                error_db.add(error_report)
            else:
                error_report.status = ReportStatus.REJECTED
            
            error_report.manual_review_notes = f"System Error: {str(e)}"
            error_db.commit()
            error_db.close()
        except Exception as db_e:
            print(f"[CRITICAL DB ERROR] {db_e}")
            
        return f"Failed: {str(e)}"
    finally:
        db.close()

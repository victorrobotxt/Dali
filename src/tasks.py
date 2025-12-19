from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.legal_engine import LegalEngine
from src.services.report_generator import AttorneyReportGenerator
from src.core.config import settings
import asyncio

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    db = SessionLocal()
    try:
        scraper = ScraperService(simulation_mode=(settings.GEMINI_API_KEY == "mock-key"))
        ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
        legal_engine = LegalEngine()
        brief_gen = AttorneyReportGenerator()

        listing = db.query(Listing).get(listing_id)
        if not listing: return "Listing not found"

        # 1. Scraping
        scraped_data = scraper.scrape_url(listing.source_url)
        
        # 2. Tier 1 AI Forensic Analysis
        loop = asyncio.get_event_loop()
        ai_data = loop.run_until_complete(ai_engine.analyze_text(scraped_data["raw_text"]))

        # 3. Apply Professional Legal Logic
        legal_results = legal_engine.analyze_listing(scraped_data, ai_data)
        legal_brief = brief_gen.generate_legal_brief(scraped_data, legal_results, ai_data)

        # 4. Status Determination (The "Kill Switch")
        status = ReportStatus.VERIFIED if legal_results["total_legal_score"] < 40 else ReportStatus.MANUAL_REVIEW
        if legal_results["gatekeeper_verdict"] == "ABORT":
            status = ReportStatus.REJECTED

        # 5. Commit Audit Report
        report = Report(
            listing_id=listing.id,
            status=status,
            risk_score=legal_results["total_legal_score"],
            ai_confidence_score=ai_data["confidence"],
            manual_review_notes=legal_brief,
            discrepancy_details=legal_results
        )
        db.add(report)
        db.commit()
        return f"Audit Complete: Verdict {status}"

    except Exception as e:
        print(f"[TASK_ERROR] {str(e)}")
        return f"Failed: {str(e)}"
    finally:
        db.close()

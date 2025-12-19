from asgiref.sync import async_to_sync
from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.storage_service import StorageService
from src.services.geospatial_service import GeospatialService
from src.services.risk_engine import RiskEngine
from src.services.report_generator import AttorneyReportGenerator
from src.core.config import settings
from src.core.logger import logger
import httpx

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    return async_to_sync(run_audit_pipeline)(listing_id)

async def run_audit_pipeline(listing_id: int):
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        with SessionLocal() as db:
            listing = db.query(Listing).get(listing_id)
            
            # 1. Scrape
            scraper = ScraperService(client=http_client)
            scraped_data = await scraper.scrape_url(listing.source_url)
            
            # 2. Vision Analysis (Gemini)
            storage = StorageService()
            img_paths = await storage.archive_images(listing_id, scraped_data.image_urls)
            
            ai_service = GeminiService(api_key=settings.GEMINI_API_KEY)
            ai_data = await ai_service.analyze_listing_multimodal(scraped_data.raw_text, img_paths)
            
            # 3. Google Maps Verification (Location Forensics)
            geo_service = GeospatialService(api_key=settings.GOOGLE_MAPS_API_KEY)
            geo_report = await geo_service.verify_neighborhood(
                ai_data["address_prediction"], 
                ai_data["landmarks"], 
                scraped_data.neighborhood
            )
            
            # 4. Final Scoring
            risk_engine = RiskEngine()
            forensic_data = {
                "scraped": scraped_data.model_dump(),
                "ai": ai_data,
                "geo": geo_report.model_dump()
            }
            
            score_res = risk_engine.calculate_score_v2(forensic_data)
            
            # Overwrite risk if Location Fraud is detected
            if not geo_report.match:
                score_res["score"] = max(score_res["score"], 70)
                score_res["flags"].append(geo_report.warning)

            # 5. Generate Report
            report_gen = AttorneyReportGenerator()
            report_text = report_gen.generate_legal_brief(scraped_data.model_dump(), score_res, ai_data)
            
            new_report = Report(
                listing_id=listing_id,
                risk_score=score_res["score"],
                legal_brief=report_text,
                discrepancy_details=forensic_data,
                status=ReportStatus.VERIFIED if score_res["score"] < 40 else ReportStatus.MANUAL_REVIEW
            )
            db.add(new_report)
            db.commit()
            return f"Audit Done: {score_res['score']}"

from asgiref.sync import async_to_sync
import asyncio
import httpx
from src.worker import celery_app
from src.db.session import SessionLocal
from src.db.models import Listing, Report, ReportStatus, Building
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.storage_service import StorageService
from src.services.geospatial_service import GeospatialService
from src.services.cadastre_service import CadastreService
from src.services.compliance_service import ComplianceService
from src.services.city_risk_service import CityRiskService
from src.services.risk_engine import RiskEngine
from src.services.report_generator import AttorneyReportGenerator
from src.core.config import settings
from src.core.logger import logger
from src.core.utils import normalize_sofia_street

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    return async_to_sync(run_audit_pipeline)(listing_id)

async def run_audit_pipeline(listing_id: int):
    log = logger.bind(listing_id=listing_id)
    
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        with SessionLocal() as db:
            listing = db.query(Listing).get(listing_id)
            if not listing: return "Error: Listing not found"

            # 1. SCRAPE
            scraper = ScraperService(client=http_client)
            scraped_data = await scraper.scrape_url(listing.source_url)
            
            # 2. VISION
            storage = StorageService()
            img_paths = await storage.archive_images(listing_id, scraped_data.image_urls)
            ai_service = GeminiService(api_key=settings.GEMINI_API_KEY)
            ai_data = await ai_service.analyze_listing_multimodal(scraped_data.raw_text, img_paths)
            
            # 3. GEO TRIANGULATION
            geo_service = GeospatialService(api_key=settings.GOOGLE_MAPS_API_KEY)
            geo_report = await geo_service.verify_neighborhood(
                ai_data.get("address_prediction"), 
                ai_data.get("landmarks", []), 
                scraped_data.neighborhood
            )
            
            # 4. REGISTRY (LINEAR)
            cadastre = CadastreService(client=http_client)
            best_address = normalize_sofia_street(geo_report.best_address or ai_data.get("address_prediction"))
            cad_data = await cadastre.get_official_details(best_address)
            
            comp_raw = {"checked": False, "has_act16": False}
            risk_raw = {"is_expropriated": False}
            building_id = None
            
            if cad_data.cadastre_id:
                # Parallel Municipal Strike
                compliance = ComplianceService(client=http_client)
                city_risk = CityRiskService(client=http_client)
                comp_raw, risk_raw = await asyncio.gather(
                    compliance.check_act_16(cad_data.cadastre_id),
                    city_risk.check_expropriation(cad_data.cadastre_id)
                )
                
                # Persist Building Context
                existing_building = db.query(Building).filter(Building.cadastre_id == cad_data.cadastre_id).first()
                if not existing_building:
                    new_building = Building(
                        cadastre_id=cad_data.cadastre_id,
                        address_full=cad_data.address_found or geo_report.best_address,
                        latitude=geo_report.lat,
                        longitude=geo_report.lng,
                        construction_year=ai_data.get("construction_year_est")
                    )
                    db.add(new_building)
                    db.flush()
                    building_id = new_building.id
                else:
                    building_id = existing_building.id

            # 5. SCORING
            forensic_data = {
                "scraped": scraped_data.model_dump(),
                "ai": ai_data,
                "geo": geo_report.model_dump(),
                "cadastre": cad_data.model_dump(),
                "compliance": comp_raw,
                "city_risk": risk_raw
            }
            risk_engine = RiskEngine()
            score_res = risk_engine.calculate_score_v2(forensic_data)
            
            # 6. REPORTING
            report_gen = AttorneyReportGenerator()
            report_text = report_gen.generate_legal_brief(scraped_data.model_dump(), {**score_res, "forensics": forensic_data}, ai_data)
            
            new_report = Report(
                listing_id=listing_id,
                building_id=building_id,
                risk_score=score_res["score"],
                legal_brief=report_text,
                discrepancy_details=forensic_data,
                status=ReportStatus.VERIFIED if score_res["score"] < 40 else ReportStatus.MANUAL_REVIEW
            )
            db.add(new_report)
            db.commit()
            
            return f"Audit Done: {score_res['score']}"

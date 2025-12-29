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
from src.services.forensics_service import SofiaMunicipalForensics
from src.services.risk_engine import RiskEngine
from src.services.legal_validator import LegalValidator
from src.services.report_generator import AttorneyReportGenerator
from src.core.config import settings
from src.core.logger import logger
from src.core.utils import normalize_sofia_street

@celery_app.task(name="src.tasks.audit_listing")
def audit_listing_task(listing_id: int):
    return async_to_sync(run_audit_pipeline)(listing_id)

async def run_audit_pipeline(listing_id: int):
    log = logger.bind(listing_id=listing_id)
    async with httpx.AsyncClient(timeout=40.0) as http_client:
        with SessionLocal() as db:
            listing = db.query(Listing).get(listing_id)
            if not listing: return

            # 1. Pipeline execution
            scraped = await ScraperService(http_client).scrape_url(listing.source_url)
            paths = await StorageService().archive_images(listing_id, scraped.image_urls)
            ai_data = await GeminiService(settings.GEMINI_API_KEY).analyze_listing_multimodal(scraped.raw_text, paths)
            geo = await GeospatialService(settings.GOOGLE_MAPS_API_KEY).verify_neighborhood(
                ai_data.address_prediction, ai_data.landmarks, scraped.neighborhood
            )
            
            # 2. Registry Logic
            addr = normalize_sofia_street(geo.best_address or ai_data.address_prediction)
            cad = await CadastreService(http_client).get_official_details(addr)
            
            mun_report = {"expropriation": {}, "compliance_act16": {}}
            b_id = None
            if cad.cadastre_id:
                mun_report = await SofiaMunicipalForensics(http_client).run_full_audit(cad.cadastre_id)
                # PERSIST Building with AI Construction Year
                b = db.query(Building).filter(Building.cadastre_id == cad.cadastre_id).first()
                if not b:
                    b = Building(
                        cadastre_id=cad.cadastre_id,
                        address_full=cad.address_found or geo.best_address,
                        latitude=geo.lat, longitude=geo.lng,
                        construction_year=ai_data.construction_year_est
                    )
                    db.add(b); db.flush(); b_id = b.id
                else: b_id = b.id

            # 3. DETERTMINISTIC LEGAL AUDIT
            lv = LegalValidator()
            dwelling_check = lv.validate_dwelling_status(
                height=ai_data.ceiling_height,
                exposures=[ai_data.light_exposure] if ai_data.light_exposure else [],
                has_storage=True, # Default until extracted
                room_count=1 # Default
            )
            efficiency_check = lv.audit_area_efficiency(float(scraped.area_sqm), ai_data.net_area_sqm, 0)

            # 4. SCORING & REPORTING
            forensic_bundle = {
                "scraped": scraped.model_dump(),
                "ai": ai_data.model_dump(),
                "geo": geo.model_dump(),
                "cadastre": cad.model_dump(),
                "compliance": mun_report.get("compliance_act16", {}),
                "city_risk": mun_report.get("expropriation", {}),
                "legal_status": dwelling_check,
                "area_efficiency": efficiency_check
            }
            
            res = RiskEngine().calculate_score_v2(forensic_bundle)
            report_text = AttorneyReportGenerator().generate_legal_brief(scraped.model_dump(), {**res, "forensics": forensic_bundle}, ai_data.model_dump())
            
            db.add(Report(
                listing_id=listing_id, building_id=b_id, risk_score=res["score"],
                legal_brief=report_text, discrepancy_details=forensic_bundle,
                status=ReportStatus.VERIFIED if res["score"] < 40 else ReportStatus.MANUAL_REVIEW
            ))
            db.commit()
            return f"Final Score: {res['score']}"

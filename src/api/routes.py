from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.session import get_db, SessionLocal
from src.db.models import Listing
from src.services.repository import RealEstateRepository
from src.services.scraper_service import ScraperService
from src.services.ai_engine import GeminiService
from src.services.risk_engine import RiskEngine
from src.core.config import settings

router = APIRouter()

class AuditRequest(BaseModel):
    url: str
    price_override: float = 0.0
    
class AuditResponse(BaseModel):
    listing_id: int
    source_url: str
    status: str
    note: str

async def process_audit_task(listing_id: int):
    """
    Background worker that runs the scrape -> AI -> Risk calculation.
    Uses its own SessionLocal to remain thread-safe.
    """
    db = SessionLocal()
    try:
        repo = RealEstateRepository(db)
        scraper = ScraperService(simulation_mode=True)
        ai_engine = GeminiService(api_key=settings.GEMINI_API_KEY)
        risk_engine = RiskEngine()

        listing = db.query(Listing).get(listing_id)
        if not listing: return

        # Execute Pipeline
        scraped_data = scraper.scrape_url(listing.source_url)
        listing.description_raw = scraped_data.get("raw_text", "Scrape failed")
        db.commit()

        ai_insights = await ai_engine.analyze_text(listing.description_raw)
        report_data = risk_engine.calculate_score(scraped_data, ai_insights)

        repo.create_report(
            listing_id=listing.id,
            risk=report_data["score"],
            details={"flags": report_data["flags"], "ai_meta": ai_insights},
            cost=0.04
        )
    except Exception as e:
        print(f"CRITICAL_WORKER_ERROR: {str(e)}")
    finally:
        db.close()

@router.post("/audit", response_model=AuditResponse)
async def initiate_audit(
    request: AuditRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    repo = RealEstateRepository(db)
    
    listing = repo.create_listing(
        url=str(request.url),
        price=request.price_override, 
        area=0.0, 
        desc="Pending Processing"
    )
    
    background_tasks.add_task(process_audit_task, listing.id)
    
    return {
        "listing_id": listing.id,
        "source_url": listing.source_url,
        "status": "QUEUED",
        "note": "The Siege Tower is advancing."
    }

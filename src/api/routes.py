from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from src.db.session import get_db
from src.services.repository import RealEstateRepository
from src.services.ai_engine import GeminiService # We will hook this up later
from src.core.config import settings

router = APIRouter()

# DTOs (Data Transfer Objects)
class AuditRequest(BaseModel):
    url: str # Pydantic v2 url validation is strict, keeping string for MVP input
    price_override: float = 0.0
    
class AuditResponse(BaseModel):
    listing_id: int
    source_url: str
    status: str
    note: str

# Background Task (The Worker Simulation)
async def process_audit_task(listing_id: int, db: Session):
    """
    This runs AFTER the response is sent to the user.
    It simulates the heavy lifting (Scraping + AI).
    """
    print(f"WORKER: Starting AI Pipeline for Listing ID {listing_id}...")
    # 1. Scrape (Future)
    # 2. AI Analyze (Future)
    # 3. Update Report in DB
    print(f"WORKER: Finished processing listing {listing_id}.")

@router.post("/audit", response_model=AuditResponse)
async def initiate_audit(
    request: AuditRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    1. Receives URL.
    2. Writes to DB (Idempotent).
    3. Spawns Background Worker.
    4. Returns 200 OK immediately.
    """
    repo = RealEstateRepository(db)
    
    # Create the Listing Record (The "Files" are opened)
    listing = repo.create_listing(
        url=str(request.url),
        price=request.price_override, 
        area=0.0, # Placeholder
        desc="Pending Scrape"
    )
    
    # Offload the heavy work to background task
    # We pass the db session to the background worker (Warning: Thread scope issues in prod, ok for MVP)
    background_tasks.add_task(process_audit_task, listing.id, db)
    
    return {
        "listing_id": listing.id,
        "source_url": listing.source_url,
        "status": "QUEUED",
        "note": "The Siege Tower is processing your request."
    }

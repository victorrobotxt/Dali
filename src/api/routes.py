from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.db.models import Listing, Report, ReportStatus
from src.services.repository import RealEstateRepository
from src.tasks import audit_listing_task
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AuditRequest(BaseModel):
    url: str
    price_override: float = 0.0

class ReportUpdate(BaseModel):
    status: str
    manual_notes: Optional[str] = None

@router.post("/audit")
async def initiate_audit(request: AuditRequest, db: Session = Depends(get_db)):
    """
    Submits a URL for auditing via the Celery Worker queue.
    """
    repo = RealEstateRepository(db)
    # Create listing immediately to return ID
    listing = repo.create_listing(url=request.url, price=request.price_override, area=0.0, desc="Queued")
    
    # Offload to Redis/Celery
    audit_listing_task.delay(listing.id)
    
    return {"listing_id": listing.id, "status": "QUEUED_IN_REDIS"}

@router.get("/reports/{listing_id}")
def get_report(listing_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the report status and details for a listing.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    report = db.query(Report).filter(Report.listing_id == listing_id).first()
    if not report:
        # If no report exists yet, the worker is likely still processing
        return {"status": "PROCESSING", "details": "Audit is currently in the queue."}
        
    return {
        "report_id": report.id,
        "status": report.status,
        "risk_score": report.risk_score,
        "ai_confidence": report.ai_confidence_score,
        "discrepancies": report.discrepancy_details,
        "manual_notes": report.manual_review_notes,
        "cost": report.cost_to_generate,
        "created_at": report.created_at
    }

@router.patch("/reports/{report_id}")
def update_report_status(report_id: int, update: ReportUpdate, db: Session = Depends(get_db)):
    """
    Manual Review Action.
    Updates status (e.g., MANUAL_REVIEW -> VERIFIED).
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        # Validate that the string provided matches the Enum
        new_status = ReportStatus(update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Status Enum")

    report.status = new_status
    if update.manual_notes:
        report.manual_review_notes = update.manual_notes
        
    db.commit()
    return {"id": report.id, "new_status": report.status}

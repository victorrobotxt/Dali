from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

router = APIRouter()

class AuditRequest(BaseModel):
    url: HttpUrl

class AuditResponse(BaseModel):
    report_id: str
    risk_score: int
    status: str

@router.post("/audit", response_model=AuditResponse)
async def initiate_audit(request: AuditRequest):
    """
    Receives a Listing URL and triggers the Intelligence Pipeline.
    """
    print(f"--> Ingesting Target: {request.url}")
    
    # TODO: Connect to Redis Queue here
    # TODO: Connect to Scraper Service
    
    return {
        "report_id": "REQ-12345", 
        "risk_score": 0, 
        "status": "PROCESSING_STARTED"
    }

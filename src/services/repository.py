from sqlalchemy.orm import Session
from src.db.models import Listing, Report, ReportStatus
from src.core.utils import normalize_url
from typing import Optional

class RealEstateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_listing(self, url: str, price: float, area: float, desc: str) -> Listing:
        clean_url = normalize_url(url)
        # 1. URL Check (Fastest)
        existing = self.get_listing_by_url(clean_url)
        if existing:
            return existing
            
        new_listing = Listing(
            source_url=clean_url,
            price_bgn=price,
            advertised_area_sqm=area,
            description_raw=desc
        )
        self.db.add(new_listing)
        self.db.commit()
        self.db.refresh(new_listing)
        return new_listing

    def get_listing_by_url(self, url: str) -> Optional[Listing]:
        return self.db.query(Listing).filter(Listing.source_url == url).first()

    def check_content_duplication(self, content_hash: str) -> Optional[int]:
        """
        Returns the ID of an existing listing if the content hash matches.
        """
        existing = self.db.query(Listing).filter(Listing.content_hash == content_hash).first()
        return existing.id if existing else None

    def update_listing_content(self, listing_id: int, description: str, content_hash: str):
        listing = self.db.query(Listing).get(listing_id)
        if listing:
            listing.description_raw = description
            listing.content_hash = content_hash
            self.db.commit()

    def create_report(self, listing_id: int, risk: int, details: dict, cost: float, confidence: int = 0) -> Report:
        status = ReportStatus.VERIFIED if confidence >= 70 else ReportStatus.MANUAL_REVIEW
        
        report = Report(
            listing_id=listing_id,
            risk_score=risk,
            ai_confidence_score=confidence,
            status=status,
            discrepancy_details=details,
            cost_to_generate=cost
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

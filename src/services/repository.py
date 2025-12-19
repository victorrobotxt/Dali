from sqlalchemy.orm import Session
from src.db.models import Listing, Report, ReportStatus, PriceHistory
from src.core.utils import normalize_url
from typing import Optional, List

class RealEstateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_listing_initial(self, url: str) -> Listing:
        """Atomic create or return existing by URL."""
        clean_url = normalize_url(url)
        existing = self.db.query(Listing).filter(Listing.source_url == clean_url).first()
        if existing:
            return existing
            
        new_listing = Listing(source_url=clean_url)
        self.db.add(new_listing)
        self.db.commit()
        self.db.refresh(new_listing)
        return new_listing

    def update_listing_data(self, listing_id: int, price: float, area: float, desc: str, chash: str):
        listing = self.db.query(Listing).get(listing_id)
        if listing:
            # Price History Logic
            if listing.price_bgn and listing.price_bgn != price:
                history = PriceHistory(listing_id=listing_id, price_bgn=listing.price_bgn)
                self.db.add(history)
            
            listing.price_bgn = price
            listing.advertised_area_sqm = area
            listing.description_raw = desc
            listing.content_hash = chash
            self.db.commit()

    def create_report(self, listing_id: int, risk: int, details: dict, cost: float, confidence: int, images: List[str]) -> Report:
        status = ReportStatus.VERIFIED if confidence >= 85 else ReportStatus.MANUAL_REVIEW
        if risk > 60: status = ReportStatus.MANUAL_REVIEW # High risk always needs eyes
        
        report = Report(
            listing_id=listing_id,
            risk_score=risk,
            ai_confidence_score=confidence,
            status=status,
            discrepancy_details=details,
            cost_to_generate=cost,
            image_archive_urls=images
        )
        self.db.add(report)
        self.db.commit()
        return report

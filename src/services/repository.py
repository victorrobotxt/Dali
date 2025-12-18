from sqlalchemy.orm import Session
from src.db.models import Listing, Report
from typing import Optional

class RealEstateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_listing(self, url: str, price: float, area: float, desc: str) -> Listing:
        """
        Idempotent creation: If URL exists, return existing.
        """
        existing = self.get_listing_by_url(url)
        if existing:
            return existing
            
        new_listing = Listing(
            source_url=url,
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

    def create_report(self, listing_id: int, risk: int, details: dict, cost: float) -> Report:
        report = Report(
            listing_id=listing_id,
            risk_score=risk,
            discrepancy_details=details,
            cost_to_generate=cost
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

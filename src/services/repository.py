from decimal import Decimal
from sqlalchemy.orm import Session
from src.db.models import Listing, PriceHistory
from src.core.utils import normalize_url

class RealEstateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_listing_initial(self, url: str) -> Listing:
        clean_url = normalize_url(url)
        existing = self.db.query(Listing).filter(Listing.source_url == clean_url).first()
        if existing: return existing
        new_l = Listing(source_url=clean_url)
        self.db.add(new_l)
        self.db.commit()
        self.db.refresh(new_l)
        return new_l

    # TYPE SAFETY FIX: price is now Decimal
    def update_listing_data(self, listing_id: int, price: Decimal, area: float, desc: str, chash: str):
        listing = self.db.query(Listing).get(listing_id)
        if listing:
            # SQLAlchemy handles Decimal comparison correctly here
            if listing.price_bgn is not None and listing.price_bgn != price:
                history = PriceHistory(listing_id=listing_id, price_bgn=listing.price_bgn)
                self.db.add(history)
            
            listing.price_bgn = price
            listing.advertised_area_sqm = area
            listing.description_raw = desc
            listing.content_hash = chash
            self.db.commit()

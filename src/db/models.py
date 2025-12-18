from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.session import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    cadastre_id = Column(String, unique=True, nullable=False, index=True)
    address_street = Column(String)
    address_number = Column(String)
    neighborhood = Column(String)
    # Note: GeoAlchemy2 would be needed for real Point types, using String for MVP placeholder
    gps_coordinates = Column(String) 
    construction_year = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("Report", back_populates="building")

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, unique=True, nullable=False, index=True)
    price_bgn = Column(Float)
    advertised_area_sqm = Column(Float)
    description_raw = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("Report", back_populates="listing")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    risk_score = Column(Integer)  # 0-100
    is_address_verified = Column(Boolean, default=False)
    discrepancy_details = Column(JSON) # Stores "Apartment vs Atelier" logic
    cost_to_generate = Column(Float)

    listing = relationship("Listing", back_populates="reports")
    building = relationship("Building", back_populates="reports")

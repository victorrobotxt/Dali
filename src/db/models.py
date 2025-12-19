import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.session import Base

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    VERIFIED = "VERIFIED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, unique=True, nullable=False, index=True)
    content_hash = Column(String(64), index=True)
    price_bgn = Column(Float)
    advertised_area_sqm = Column(Float)
    description_raw = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("Report", back_populates="listing")
    price_history = relationship("PriceHistory", back_populates="listing")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    price_bgn = Column(Float)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    listing = relationship("Listing", back_populates="price_history")

class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True)
    cadastre_id = Column(String, unique=True, index=True)
    address_full = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    construction_year = Column(Integer)
    
    reports = relationship("Report", back_populates="building")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    risk_score = Column(Integer)
    ai_confidence_score = Column(Integer, default=0)
    
    discrepancy_details = Column(JSON)
    image_archive_urls = Column(JSON) # Store URLs of backed-up images
    cost_to_generate = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    listing = relationship("Listing", back_populates="reports")
    building = relationship("Building", back_populates="reports")

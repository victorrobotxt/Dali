import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text, Enum, Numeric
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
    
    # FINANCIAL FIX: Use Numeric for precise currency handling
    price_bgn = Column(Numeric(12, 2)) 
    advertised_area_sqm = Column(Float)
    description_raw = Column(Text)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    reports = relationship("Report", back_populates="listing", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="listing")

class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True)
    cadastre_id = Column(String, unique=True, index=True)
    address_full = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    construction_year = Column(Integer)
    reports = relationship("Report", back_populates="building")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    price_bgn = Column(Numeric(12, 2))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    listing = relationship("Listing", back_populates="price_history")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    risk_score = Column(Integer)
    ai_confidence_score = Column(Integer, default=0)
    legal_brief = Column(Text)
    discrepancy_details = Column(JSON)
    image_archive_urls = Column(JSON)
    
    # COST FIX: Track API usage precisely
    cost_to_generate = Column(Numeric(10, 4)) 
    
    manual_review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    listing = relationship("Listing", back_populates="reports")
    building = relationship("Building", back_populates="reports")

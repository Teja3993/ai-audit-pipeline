"""
SQLAlchemy ORM models representing the database schema.
Defines how lead data and pipeline states are stored in SQLite.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base

class LeadState(Base):
    """Tracks the lifecycle of a lead through the automation pipeline."""
    
    __tablename__ = "lead_states"

    id = Column(Integer, primary_key=True, index=True)
    prospect_name = Column(String, index=True)
    prospect_email = Column(String, index=True)
    company_name = Column(String)
    company_url = Column(String)
    
    # State Machine Tracker: RECEIVED -> SCRAPED -> ENRICHED -> GENERATED -> DELIVERED (or FAILED)
    status = Column(String, default="RECEIVED", index=True) 
    
    # Captures the exact exception string if the background task fails
    error_message = Column(Text, nullable=True) 
    
    # Auditing timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
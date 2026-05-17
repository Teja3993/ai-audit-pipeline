"""
Database configuration and session management.
Sets up the SQLite connection engine and provides session generators.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Local SQLite database file path
SQLALCHEMY_DATABASE_URL = "sqlite:///./leads_state.db"

# 'check_same_thread=False' is strictly required for FastAPI background tasks 
# so different threads can safely read/write to the SQLite file.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Factory for generating new, isolated database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

def get_db():
    """Yields a database session and safely closes it when the operation finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
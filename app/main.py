"""
Main application entry point.
Configures logging, initializes the database, and registers FastAPI routes.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models import domain  # Required for SQLAlchemy to register tables

import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("app").setLevel(logging.INFO)


noisy_loggers = ["fontTools", "fontTools.subset", "weasyprint", "urllib3", "httpx"]

for logger_name in noisy_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)
    logger.propagate = False

# Create SQLite database tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize FastAPI server
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated AI Workflow for Lead Enrichment and PDF Generation",
    version="1.0.0"
)

@app.get("/health", tags=["System"])
def health_check():
    """Basic health check to verify server uptime."""
    return {
        "status": "online", 
        "project": settings.PROJECT_NAME,
        "message": "System is operational. Ready to receive leads."
    }

# Register core API endpoints
from app.api.routes import router as api_router
app.include_router(api_router, prefix="/api")
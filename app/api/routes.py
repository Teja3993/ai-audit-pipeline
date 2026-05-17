"""
API Routing and Pipeline Orchestration.

Defines the FastAPI endpoints and the asynchronous background worker 
that executes the end-to-end automation workflow.
"""

import os
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.schemas import LeadRequest, LeadResponse
from app.models.domain import LeadState

from app.services.scraper import scrape_company_data
from app.services.llm_engine import enrich_company_data
from app.services.pdf_generator import generate_audit_report
from app.services.email_service import send_audit_report_email
from app.services.workspace import log_lead_to_sheets, upload_pdf_to_drive

router = APIRouter()
logger = logging.getLogger(__name__)

# Google Workspace Identifiers
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1hM-e3G7J5e-vCwfIBPUT3xls-jPZ6gjI9e-3-dUQfyM")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1YpGQgVEcwinc7ehv_OYDoTD8S2gXMEVd")


def update_lead_state(db: Session, lead_id: int, status: str, error_msg: str = None):
    """Utility to update the lead's status in the SQLite tracking table."""
    update_data = {"status": status}
    if error_msg:
        update_data["error_message"] = error_msg
        
    db.query(LeadState).filter(LeadState.id == lead_id).update(update_data)
    db.commit()


def process_lead_pipeline(lead_id: int, lead_data: dict):
    """
    Background worker that executes the entire automation pipeline sequentially.
    Uses an isolated database session to prevent cross-thread contamination.
    """
    db = SessionLocal()
    company_name = lead_data["company_name"]
    company_url = str(lead_data["company_url"])
    prospect_email = lead_data["prospect_email"]
    prospect_name = lead_data["prospect_name"]

    try:
        logger.info(f"[Lead {lead_id}] Starting pipeline for {company_name}")

        # Phase 1: Data Acquisition
        scraped_text = scrape_company_data(company_url)
        update_lead_state(db, lead_id, "SCRAPED")

        # Phase 2: AI Synthesis
        enrichment_data = enrich_company_data(scraped_text)
        update_lead_state(db, lead_id, "ENRICHED")

        # Phase 3: Asset Generation
        pdf_path = generate_audit_report(company_name, enrichment_data)
        update_lead_state(db, lead_id, "GENERATED")

        # Phase 4: Delivery
        send_audit_report_email(
            prospect_email=prospect_email,
            prospect_name=prospect_name,
            company_name=company_name,
            pdf_path=pdf_path
        )

        # Phase 5: External Logging
        upload_pdf_to_drive(GOOGLE_DRIVE_FOLDER_ID, pdf_path, company_name)
        log_lead_to_sheets(GOOGLE_SHEET_ID, prospect_name, prospect_email, company_name, "SUCCESS")

        update_lead_state(db, lead_id, "DELIVERED")
        logger.info(f"[Lead {lead_id}] Pipeline completed successfully.")

    except Exception as e:
        error_details = str(e)
        logger.error(f"[Lead {lead_id}] Pipeline failed: {error_details}")
        
        # Ensure the failure is recorded in both SQLite and Google Sheets
        update_lead_state(db, lead_id, "FAILED", error_details)
        log_lead_to_sheets(GOOGLE_SHEET_ID, prospect_name, prospect_email, company_name, "FAILED")

    finally:
        db.close()


@router.post("/leads", response_model=LeadResponse, status_code=202)
def receive_lead(
    lead_in: LeadRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Ingestion endpoint. Validates payload, initializes the database tracker, 
    and delegates heavy processing to the background queue to ensure a fast response.
    """
    try:
        # Create initial tracker record
        new_lead = LeadState(
            prospect_name=lead_in.prospect_name,
            prospect_email=lead_in.prospect_email,
            company_name=lead_in.company_name,
            company_url=str(lead_in.company_url),
            status="RECEIVED"
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        
        # Dispatch to worker queue
        background_tasks.add_task(
            process_lead_pipeline, 
            lead_id=new_lead.id, 
            lead_data=lead_in.model_dump()
        )
        
        return LeadResponse(
            status="success", 
            message=f"Lead {new_lead.id} received. AI audit generation initiated."
        )

    except Exception as e:
        logger.error(f"Failed to ingest lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during ingestion.")
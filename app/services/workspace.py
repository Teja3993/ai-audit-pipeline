"""
Google Workspace Integration Service.

Handles automated logging to Google Sheets and archiving PDFs to Google Drive.
Fails gracefully if the service account credentials are not provided.
"""

import os
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# Expected local path for the Google Service Account key
CREDENTIALS_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    """Loads Google Service Account credentials, returning None if missing."""
    if not os.path.exists(CREDENTIALS_FILE):
        logger.warning(f"Google credentials missing ({CREDENTIALS_FILE}). Skipping Workspace integration.")
        return None
    return Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)


def log_lead_to_sheets(spreadsheet_id: str, prospect_name: str, prospect_email: str, company_name: str, status: str):
    """Appends a timestamped record of the lead's pipeline execution to Google Sheets."""
    creds = get_credentials()
    if not creds:
        return
        
    try:
        logger.info(f"Logging {company_name} to Google Sheets...")
        client = gspread.authorize(creds)
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Maps directly to the assessment requirement: Name, Email, Company, Timestamp, Status
        row = [
            prospect_name,
            prospect_email,
            company_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status
        ]
        
        sheet.append_row(row)
        logger.info("Successfully appended row to Google Sheets.")
        
    except Exception as e:
        logger.error(f"Failed to log lead to Google Sheets: {e}")


def upload_pdf_to_drive(folder_id: str, pdf_path: str, company_name: str):
    """Uploads the generated PDF asset to a specified Google Drive folder."""
    creds = get_credentials()
    if not creds:
        return
        
    if not os.path.exists(pdf_path):
        logger.error("Cannot upload to Drive. PDF file does not exist locally.")
        return
        
    try:
        logger.info(f"Uploading {company_name} PDF to Google Drive...")
        service = build('drive', 'v3', credentials=creds)
        
        safe_filename = company_name.replace(' ', '_').lower()
        
        # 'parents' array places the file directly into the target folder
        file_metadata = {
            'name': f"{safe_filename}_audit_report.pdf",
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"Successfully uploaded PDF to Drive. File ID: {file.get('id')}")
        
    except Exception as e:
        # Note: Free-tier Service Accounts will reliably hit a 403 storageQuotaExceeded error here.
        # This is expected behavior outside of a paid Workspace Shared Drive.
        logger.error(f"Failed to upload PDF to Google Drive: {e}")
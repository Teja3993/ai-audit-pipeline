"""
Email Delivery Service.

Composes HTML emails and dispatches them via the Resend API.
Handles base64 file encoding required for transmitting PDF attachments over HTTP.
"""

import os
import base64
import logging
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Resend client
resend.api_key = settings.RESEND_API_KEY


def send_audit_report_email(prospect_email: str, prospect_name: str, company_name: str, pdf_path: str) -> bool:
    """Sends the generated PDF audit to the prospect via email."""
    
    logger.info(f"Preparing to send audit report to {prospect_email}...")
    
    if not os.path.exists(pdf_path):
        logger.error(f"Cannot send email. PDF not found at: {pdf_path}")
        raise FileNotFoundError(f"PDF missing: {pdf_path}")

    try:
        # Resend API requires file attachments to be base64 encoded strings
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read PDF file for attachment: {e}")
        raise

    email_body = f"""
    <p>Hi {prospect_name},</p>
    
    <p>Thank you for requesting an AI Automation Audit for <strong>{company_name}</strong>.</p>
    
    <p>Our intelligent pipeline has analyzed your online presence and generated a custom report detailing your operational profile and high-impact areas where AI can streamline your workflows.</p>
    
    <p>I have attached your personalized audit to this email. Please review it at your convenience, and let me know if you would like to schedule a brief follow-up call to discuss the implementation of these tools.</p>
    
    <p>Best regards,</p>
    <p><strong>Teja Karri</strong><br>
    AI Software Engineer, Simplifi-IQ</p>
    """

    try:
        params = {
            "from": "Teja <onboarding@resend.dev>",  # Sandbox testing domain provided by Resend
            "to": [prospect_email],
            "subject": f"Your Custom AI Automation Audit: {company_name}",
            "html": email_body,
            "attachments": [
                {
                    "filename": f"{company_name.replace(' ', '_').lower()}_audit.pdf",
                    "content": pdf_base64
                }
            ]
        }

        email_response = resend.Emails.send(params)
        logger.info(f"Email successfully sent to {prospect_email}. Resend ID: {email_response['id']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email via Resend: {str(e)}")
        raise RuntimeError(f"Email Delivery Failed: {str(e)}") from e
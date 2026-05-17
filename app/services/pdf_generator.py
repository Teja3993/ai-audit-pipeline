"""
PDF Generation Service.

Merges structured AI data into an HTML template and compiles it into a PDF
using WeasyPrint. Manages dynamic path resolution for local assets.
"""

import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from app.models.schemas import CompanyEnrichment

logger = logging.getLogger(__name__)

# Dynamically resolve absolute paths to ensure the script runs correctly 
# regardless of the terminal's working directory.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "generated_reports")

# Ensure output directory exists before writing to it
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Jinja2 environment to target the templates folder
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_audit_report(company_name: str, enrichment_data: CompanyEnrichment) -> str:
    """
    Renders data into the HTML template and compiles the final PDF.
    Returns the absolute file path to the generated document.
    """
    try:
        logger.info(f"Generating PDF report for {company_name}...")
        
        # Load template and prepare payload
        template = env.get_template("report_template.html")
        template_vars = enrichment_data.model_dump()
        template_vars["company_name"] = company_name
        template_vars["date"] = datetime.now().strftime("%B %d, %Y")
        
        # Render HTML
        rendered_html = template.render(**template_vars)
        
        # Define safe output path
        safe_filename = company_name.replace(" ", "_").lower()
        pdf_filename = f"{safe_filename}_audit_report.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
        
        # Compile PDF (base_url is strictly required for WeasyPrint to locate local CSS)
        HTML(string=rendered_html, base_url=TEMPLATE_DIR).write_pdf(pdf_path)
        
        logger.info(f"PDF successfully generated at: {pdf_path}")
        return pdf_path

    except Exception as e:
        logger.error(f"Failed to generate PDF for {company_name}: {str(e)}")
        raise RuntimeError(f"PDF Generation Error: {str(e)}") from e
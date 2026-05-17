"""
API Unit Tests.

Verifies the ingestion endpoint's routing, Pydantic data validation, 
and background task delegation using FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

# Initialize the FastAPI Test Client
client = TestClient(app)

# Use @patch to intercept the background task. 
# This isolates the test to just the API layer without triggering the LLM or Scraper.
@patch("app.api.routes.process_lead_pipeline")
def test_receive_lead_valid_data(mock_pipeline):
    """Verifies that a valid payload returns a 202 and triggers the background worker."""
    valid_payload = {
        "prospect_name": "Jane Smith",
        "prospect_email": "jane.smith@example.com",
        "company_name": "Innovate AI",
        "company_url": "https://www.innovateai.com"
    }
    
    response = client.post("/api/leads", json=valid_payload)
    
    assert response.status_code == 202
    assert response.json()["status"] == "success"
    
    # Assert the orchestrator was successfully queued
    mock_pipeline.assert_called_once()


def test_receive_lead_invalid_url():
    """Verifies that Pydantic rejects malformed URLs before database insertion."""
    invalid_payload = {
        "prospect_name": "Jane Smith",
        "prospect_email": "jane.smith@example.com",
        "company_name": "Innovate AI",
        "company_url": "not-a-real-url"  # Fails HttpUrl validation
    }
    
    response = client.post("/api/leads", json=invalid_payload)
    
    # 422 Unprocessable Entity is FastAPI's standard response for schema failures
    assert response.status_code == 422
    
    # Verify the error detail correctly points to the company_url field
    error_detail = response.json()["detail"][0]
    assert error_detail["loc"] == ["body", "company_url"]


def test_receive_lead_missing_fields():
    """Verifies that the API rejects payloads missing required fields."""
    incomplete_payload = {
        "prospect_name": "Jane Smith",
        # Missing email, company_name, and URL
    }
    
    response = client.post("/api/leads", json=incomplete_payload)
    assert response.status_code == 422
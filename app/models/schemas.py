"""
Pydantic schemas for data validation and API contracts.
These models ensure strict type safety across the ingestion, LLM, and output layers.
"""

from typing import List
from pydantic import BaseModel, Field, HttpUrl

class LeadRequest(BaseModel):
    """Validates incoming lead data. Pydantic automatically rejects malformed URLs."""
    
    prospect_name: str = Field(..., description="Name of the prospect")
    prospect_email: str = Field(..., description="Email address of the prospect")
    company_name: str = Field(..., description="Name of the company")
    company_url: HttpUrl = Field(..., description="Valid URL of the company website")


class CompanyEnrichment(BaseModel):
    """Strict JSON schema enforced on the LLM to guarantee consistent PDF rendering."""
    
    company_summary: str = Field(
        ..., 
        description="A concise executive summary of what the company does."
    )
    industry: str = Field(
        ..., 
        description="The primary industry or sector the company operates in."
    )
    target_customers: str = Field(
        ..., 
        description="The inferred target audience or customer profile."
    )
    business_model: str = Field(
        ..., 
        description="The primary business model (e.g., B2B SaaS, Consulting, E-commerce)."
    )
    observed_services: List[str] = Field(
        ..., 
        description="A list of the core services or products offered."
    )
    ai_opportunities: List[str] = Field(
        ..., 
        description="3 to 5 highly specific, actionable AI integration opportunities tailored to their business."
    )


class LeadResponse(BaseModel):
    """Immediate API response format confirming background task initiation."""
    
    status: str = Field(default="success")
    message: str = Field(default="Lead received. Audit generation initiated in background.")
"""
AI Enrichment Service.

Passes scraped text to the LLM to extract structured business intelligence.
Enforces strict JSON outputs mapped directly to our Pydantic schemas.
"""

import json
import logging
from groq import Groq
from app.core.config import settings
from app.models.schemas import CompanyEnrichment

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=settings.GROQ_API_KEY)

# Llama 3.3 70B is chosen for its high reliability in strict JSON generation
MODEL_NAME = "llama-3.3-70b-versatile"


def enrich_company_data(scraped_text: str) -> CompanyEnrichment:
    """Extracts business insights from raw text and validates against the CompanyEnrichment schema."""
    
    logger.info("Initiating AI enrichment via Groq...")
    
    # Define persona and strict formatting rules
    system_prompt = (
        "You are an expert B2B business analyst and AI automation consultant. "
        "Your objective is to analyze raw website text and extract key business intelligence. "
        "You MUST respond ONLY with valid JSON. "
        "Do not include any conversational text, markdown formatting blocks, "
        "preambles, or postambles. Output the raw JSON object exclusively."
    )

    # Inject the exact Pydantic schema into the prompt so the LLM knows the required keys
    schema_definition = CompanyEnrichment.model_json_schema()
    
    user_prompt = f"""
    Analyze the following scraped website text and populate the required JSON schema.
    Ensure the 'ai_opportunities' are highly specific to their actual business operations.
    
    REQUIRED JSON SCHEMA:
    {json.dumps(schema_definition, indent=2)}
    
    SCRAPED TEXT:
    {scraped_text}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Force JSON mode and use low temperature for deterministic, analytical outputs
            response_format={"type": "json_object"}, 
            temperature=0.1,  
            max_tokens=2048
        )
        
        raw_output = response.choices[0].message.content
        parsed_json = json.loads(raw_output)
        
        # Pass the parsed dictionary into Pydantic. 
        # This instantly throws a validation error if the LLM hallucinated or missed keys.
        validated_data = CompanyEnrichment(**parsed_json)
        
        logger.info("AI enrichment successful and schema-validated.")
        return validated_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Groq returned invalid JSON: {e}")
        raise ValueError("LLM failed to return a valid JSON structure.") from e
    except Exception as e:
        logger.error(f"LLM Enrichment pipeline failed: {e}")
        raise RuntimeError(f"Enrichment Engine Error: {str(e)}") from e
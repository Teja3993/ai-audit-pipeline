from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Loads and validates environment variables from the .env file."""
    
    PROJECT_NAME: str = "Simplifi-IQ Automated Audit Pipeline"
    
    # Core API Keys (App will fail to start if these are missing)
    GROQ_API_KEY: str
    RESEND_API_KEY: str
    
    # Pydantic config to read the local .env file
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"  # Safely ignore any unmapped variables
    )

# Global settings instance to be imported across the app
settings = Settings()
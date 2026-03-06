from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings with validation"""
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Settings
    API_HOST: str = Field(default="0.0.0.0", description="API host address")
    API_PORT: int = Field(default=8000, ge=1, le=65535, description="API port")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    # LLM Settings
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenRouter API key - SENSITIVE: Do not log or expose"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        description="OpenRouter API endpoint"
    )
    LLM_MODEL: str = Field(
        default="google/gemini-2.5-flash-lite-preview-09-2025",
        description="LLM model to use"
    )

    # CORS Settings - Restrict to known origins
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Auth / JWT Settings
    JWT_SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_openssl_rand_-hex_32",
        description="Secret key for signing JWTs. MUST be changed in production."
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token TTL in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token TTL in days")

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/auth/google/callback",
        description="Google OAuth redirect URI registered in Google Cloud Console"
    )

    # Validation
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate LOG_LEVEL is a valid logging level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {v}")
        return v.upper()
    
    @field_validator('OPENROUTER_API_KEY', mode='after')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate API key format if provided.
        
        NOTE: This validation is just to catch obviously invalid values.
        The actual key is NOT logged or exposed anywhere.
        """
        if v is None:
            logger.warning("OPENROUTER_API_KEY not set - LLM features will be unavailable")
            return None
        
        if not isinstance(v, str):
            raise ValueError("OPENROUTER_API_KEY must be a string")
        
        if len(v.strip()) == 0:
            raise ValueError("OPENROUTER_API_KEY cannot be empty")
        
        # Basic length check (OpenRouter keys are typically 30+ chars)
        if len(v) < 10:
            raise ValueError("OPENROUTER_API_KEY appears invalid (too short)")
        
        # Log that key was loaded (but not the actual value)
        logger.info("OPENROUTER_API_KEY loaded successfully")
        return v.strip()
    
    @field_validator('ALLOWED_ORIGINS', mode='after')
    @classmethod
    def validate_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins are properly formatted"""
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        
        for origin in v:
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f"Origin must start with http:// or https://: {origin}")
        
        return v

def get_settings() -> Settings:
    """
    Get application settings.
    
    This function ensures settings are validated on startup.
    """
    try:
        settings = Settings()
        logger.info(f"Settings loaded: API at {settings.API_HOST}:{settings.API_PORT}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise

# Create settings instance with validation
settings = get_settings()

"""Application configuration using Pydantic settings."""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Content Automation Platform"
    app_version: str = "1.0.1"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./content_platform.db"
    
    # API
    api_prefix: str = "/api/v1"
    
    # Meta/Facebook OAuth (single App for entire SaaS; from env only)
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_redirect_uri: Optional[str] = None
    token_encryption_key: Optional[str] = None  # For encrypting tokens at rest (e.g. 32-byte base64)
    cron_secret: Optional[str] = None  # Secret for cron/run endpoint (server-side only)

    # Gemini API (optional) – for AI-generated content themes
    gemini_api_key: Optional[str] = None  # Get from https://aistudio.google.com/apikey
    gemini_model: str = "gemini-2.5-flash"
    gemini_input_cost_per_million_usd: float = 0.30
    gemini_output_cost_per_million_usd: float = 2.50

    # LinkedIn OAuth (Phase 6)
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_redirect_uri: Optional[str] = None

    # Celery (optional) – background task queue for scheduled Facebook posts
    celery_broker_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "supersecretkeychangeinproduction"  # In production, set this via env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    cors_origins: str = "*"  # Comma-separated list, e.g. "http://localhost:5173,https://app.example.com"

    # Storage ("local" or "gdrive")
    storage_backend: str = "local"
    media_dir: str = "data/media"  # Relative to project root, cross-platform
    
    # Google Drive Storage (Phase 6 Pivot)
    google_drive_credentials_json: Optional[str] = None  # JSON string or path to JSON
    google_drive_folder_id: Optional[str] = None

    # Stripe Billing (Phase 6)
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_pro_price_id: Optional[str] = None
    stripe_agency_price_id: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

"""
Centralized Configuration Management for AISpark Studio
All settings in one place for easy management
"""

import secrets as _secrets
import logging as _logging
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with validation and defaults"""
    
    # Core Settings
    secret_key: str = Field(default="")
    debug_mode: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # CORS — comma-separated allowed origins
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8501")
    
    # Database
    database_url: str = Field(default="sqlite:///./aispark_studio.db")
    
    # AI Configuration
    google_api_key: str = Field(default="")
    ai_model_name: str = Field(default="gemini-2.5-flash")
    ai_temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    ai_max_tokens: int = Field(default=2048, ge=1, le=8192)
    
    # RAG Configuration
    rag_mode: str = Field(default="vertex_first")
    
    # Google Search Configuration
    google_search_enabled: bool = Field(default=False)
    google_cse_api_key: str = Field(default="")
    google_cse_cx: str = Field(default="")
    
    # Vertex AI Search Configuration
    vertex_search_enabled: bool = Field(default=False)
    vertex_project_id: str = Field(default="")
    vertex_location: str = Field(default="global")
    vertex_data_store_id: str = Field(default="")
    vertex_engine_id: str = Field(default="")
    vertex_serving_config: str = Field(default="default_search")
    vertex_rag_corpus_id: str = Field(default="")
    vertex_gen_location: str = Field(default="us-central1")
    
    # Google Cloud Authentication
    google_application_credentials: str = Field(default="")
    google_cloud_project: str = Field(default="")
    
    # Feature Flags
    enable_rag: bool = Field(default=True)
    enable_diversity: bool = Field(default=True)
    enable_self_critique: bool = Field(default=True)

    # B2B Sandbox
    sandbox_api_key: Optional[str] = Field(default=None, description="Static API key for B2B sandbox access")

    # B2B Admin
    admin_api_key: Optional[str] = Field(default=None, description="Static API key for admin API access")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_delay: float = Field(default=2.0, ge=0.1, le=10.0)
    max_concurrent_requests: int = Field(default=5, ge=1, le=50)
    
    # Caching
    enable_cache: bool = Field(default=True)
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=1800, ge=60, le=86400)
    cache_max_size: int = Field(default=1000, ge=10, le=10000)

    # Redis
    redis_url: str = Field(default="")
    redis_password: str = Field(default="")
    redis_db: int = Field(default=0)
    redis_pool_size: int = Field(default=10)

    # Paths
    knowledge_base_path: str = Field(default="knowledge_base")
    master_prompt_file: str = Field(default="helios_master_prompt.txt")
    
    class Config:
        # default; overridden via instance _env_file below
        env_file = ".env"
        env_prefix = 'aispark_'
        case_sensitive = False

# Resolve .env from project root (.. / .env) or fallback to backend/.env or default
_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_ROOT_ENV = _PROJECT_ROOT / ".env"
_BACKEND_ENV = _BACKEND_DIR / ".env"

_env_file_path = None
if _ROOT_ENV.exists():
    _env_file_path = _ROOT_ENV
elif _BACKEND_ENV.exists():
    _env_file_path = _BACKEND_ENV

# Global settings instance (pydantic-settings v2 supports _env_file kwarg)
settings = Settings(_env_file=str(_env_file_path)) if _env_file_path else Settings()

# Enforce cryptographically secure secret key
_config_logger = _logging.getLogger("config")

if not settings.secret_key or settings.secret_key == "change-this-secret-key-in-production":
    settings.secret_key = _secrets.token_urlsafe(32)
    _config_logger.warning(
        "SECRET KEY: No secret_key configured. Generated an ephemeral key. "
        "Set AISPARK_SECRET_KEY in your .env for persistent sessions across restarts."
    )

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent

def get_knowledge_base_path() -> Path:
    """Get the knowledge base directory path"""
    return get_project_root() / settings.knowledge_base_path

def get_master_prompt_path() -> Path:
    """Get the master prompt file path"""
    # First try prompts directory (new location)
    prompts_path = get_project_root() / "backend" / "prompts" / settings.master_prompt_file
    if prompts_path.exists():
        return prompts_path
    # Fallback to old knowledge_base location
    return get_knowledge_base_path() / settings.master_prompt_file

def validate_api_key() -> bool:
    """Validate that Google API key or Vertex AI credentials are available"""
    # Check for Vertex AI service account (preferred)
    project = settings.vertex_project_id or settings.google_cloud_project
    if project and settings.google_application_credentials:
        if Path(settings.google_application_credentials).exists():
            return True
    # Fallback: legacy API key
    return bool(settings.google_api_key and settings.google_api_key != "your_google_api_key_here")

def get_safety_settings() -> List[dict]:
    """Get default safety settings for Google AI"""
    return [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH", 
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]

"""
Centralized Configuration Management for AISpark Studio
All settings in one place for easy management
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
import os

class Settings(BaseSettings):
    """Application settings with validation and defaults"""
    
    # Core Settings
    secret_key: str = Field(default="change-this-secret-key-in-production")
    debug_mode: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Database
    database_url: str = Field(default="sqlite:///./aispark_studio.db")
    
    # AI Configuration
    google_api_key: str = Field(default="")
    ai_model_name: str = Field(default="gemini-2.5-flash")
    ai_temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    ai_max_tokens: int = Field(default=2048, ge=1, le=8192)
    
    # Feature Flags
    enable_rag: bool = Field(default=True)
    enable_diversity: bool = Field(default=True)
    enable_self_critique: bool = Field(default=True)
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_delay: float = Field(default=2.0, ge=0.1, le=10.0)
    max_concurrent_requests: int = Field(default=5, ge=1, le=50)
    
    # Caching
    enable_cache: bool = Field(default=True)
    cache_ttl: int = Field(default=1800, ge=60, le=86400)
    cache_max_size: int = Field(default=1000, ge=10, le=10000)
    
    # Paths
    knowledge_base_path: str = Field(default="knowledge_base")
    master_prompt_file: str = Field(default="helios_master_prompt.txt")
    
    class Config:
        # default; overridden via instance _env_file below
        env_file = ".env"
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

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent

def get_knowledge_base_path() -> Path:
    """Get the knowledge base directory path"""
    return get_project_root() / settings.knowledge_base_path

def get_master_prompt_path() -> Path:
    """Get the master prompt file path"""
    return get_knowledge_base_path() / settings.master_prompt_file

def validate_api_key() -> bool:
    """Validate that Google API key is set"""
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

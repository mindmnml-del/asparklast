"""
AISpark Studio Configuration
Ensures compatibility with Helios and other systems
"""

import os
from typing import Optional

class AISpark_Config:
    """AISpark specific configuration to avoid conflicts"""
    
    # API Configuration
    API_BASE_URL = os.getenv("AISPARK_API_URL", "http://localhost:8001")
    API_PREFIX = "/api/v1/aispark"
    API_TIMEOUT = 30
    
    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv("AISPARK_PORT", "8502"))  # Different from Helios
    STREAMLIT_HOST = os.getenv("AISPARK_HOST", "0.0.0.0")
    BASE_PATH = "/aispark"  # Unique base path
    
    # Gemini 2.5 Flash Configuration
    GEMINI_MODEL = "gemini-2.5-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_TEMPERATURE = 0.7
    GEMINI_MAX_TOKENS = 8192
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("AISPARK_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - AISpark - %(levelname)s - %(message)s"
    
    # Session Configuration
    SESSION_PREFIX = "aispark_"
    SESSION_TIMEOUT = 3600  # 1 hour
    
    # Health Check
    HEALTH_CHECK_INTERVAL = 30  # seconds
    HEALTH_CHECK_ENDPOINT = "/health/aispark"
    
    # Helios Exclusions (avoid conflicts)
    HELIOS_EXCLUDED_ENDPOINTS = [
        "/health",
        "/status", 
        "/metrics",
        "/admin",
        "/api/v1/helios"
    ]
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL with AISpark prefix"""
        return f"{cls.API_BASE_URL}{cls.API_PREFIX}{endpoint}"
    
    @classmethod
    def is_helios_endpoint(cls, endpoint: str) -> bool:
        """Check if endpoint conflicts with Helios"""
        return any(endpoint.startswith(excluded) for excluded in cls.HELIOS_EXCLUDED_ENDPOINTS)
    
    @classmethod
    def get_session_key(cls, key: str) -> str:
        """Get namespaced session key"""
        return f"{cls.SESSION_PREFIX}{key}"

# Create global config instance
config = AISpark_Config()

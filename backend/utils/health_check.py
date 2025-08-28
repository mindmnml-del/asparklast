"""
Health Check Utilities for AISpark Studio
Simple health monitoring functions
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_health_status() -> Dict[str, Any]:
    """Get detailed health status"""
    try:
        from core.database import db_manager
        from services.unified_ai_service import ai_service
        
        health_data = {
            "status": "healthy",
            "database": db_manager.health_check(),
            "ai_service": ai_service.is_ready(),
            "timestamp": None  # Will be set by caller
        }
        
        # Overall status
        if not all([health_data["database"], health_data["ai_service"]]):
            health_data["status"] = "unhealthy"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": None
        }

def get_quick_health() -> Dict[str, str]:
    """Get quick health status"""
    try:
        return {"status": "ok", "message": "AISpark Studio is running"}
    except Exception as e:
        logger.error(f"Quick health check failed: {e}")
        return {"status": "error", "message": str(e)}

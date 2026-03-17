"""Vertex AI Search endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from core import models
from services.vertex_search_service import vertex_search_service
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


@router.get("/search/vertex")
async def vertex_search(
    q: str,
    limit: int = 10,
    filter: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
):
    """Vertex AI Search endpoint"""
    if not vertex_search_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Vertex AI Search service not available",
        )

    try:
        result = await vertex_search_service.search(
            query=q, max_results=limit, filter_expression=filter
        )

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Search failed"),
            )

        return result

    except Exception as e:
        logger.error(f"Vertex search error: {e}")
        raise HTTPException(status_code=500, detail="Search request failed")


@router.get("/search/vertex/status")
def vertex_search_status(current_user: models.User = Depends(get_current_user)):
    """Get Vertex AI Search service status"""
    return vertex_search_service.get_status()

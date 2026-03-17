"""Critic endpoints — prompt analysis and scoring."""

import logging

from fastapi import APIRouter, HTTPException, Depends

from core import models, schemas
from services.unified_critic_service import critic_service, AnalysisType
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Critic"])


@router.post("/critic/analyze")
async def analyze_prompt(
    request: schemas.CriticAnalysisRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Analyze prompt quality and suggest improvements"""
    try:
        analysis_type = getattr(
            AnalysisType, request.analysis_type.upper(), AnalysisType.PHOTO
        )

        result = critic_service.analyze_prompt(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            analysis_type=analysis_type,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except Exception as e:
        logger.error(f"Critic analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/critic/stats")
def critic_stats(current_user: models.User = Depends(get_current_user)):
    """Get critic service statistics"""
    return critic_service.get_stats()

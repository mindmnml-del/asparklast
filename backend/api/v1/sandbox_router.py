"""
B2B Sandbox API Gateway - Validation Gate 1 (Static Key)
Exposes /generate and /critic/analyze behind Bearer token auth.
"""

import asyncio
import logging
import secrets
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from core.schemas import GenerationRequest, CriticAnalysisRequest
from services.unified_ai_service import ai_service
from services.unified_critic_service import critic_service, AnalysisType

logger = logging.getLogger(__name__)

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


async def verify_sandbox_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Validate the Bearer token against the static sandbox API key.
    Returns the validated key string on success.
    """
    configured_key = settings.sandbox_api_key
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "sandbox_not_configured",
                "message": "B2B Sandbox API is not configured on this server.",
            },
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_credentials",
                "message": "Authorization header with Bearer token is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not secrets.compare_digest(credentials.credentials, configured_key):
        logger.warning("Sandbox auth failed: invalid Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid API key.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


@router.post("/generate", summary="Generate AI prompt")
async def sandbox_generate(
    request: GenerationRequest,
    _key: str = Depends(verify_sandbox_key),
) -> Dict[str, Any]:
    """
    Generate an AI-enhanced prompt using the AISpark generation engine.
    Does NOT consume user credits or require user authentication.
    """
    try:
        result = await ai_service.generate_response(request.model_dump())

        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "generation_failed",
                    "message": result.get("message", "AI generation service returned an error."),
                },
            )

        if isinstance(result, dict):
            result.pop("_metadata", None)

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error("Sandbox /generate error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during generation.",
            },
        )


@router.post("/critic/analyze", summary="Analyze prompt quality")
async def sandbox_critic_analyze(
    request: CriticAnalysisRequest,
    _key: str = Depends(verify_sandbox_key),
) -> Dict[str, Any]:
    """
    Analyze prompt quality and receive scoring, strengths/weaknesses,
    and an improved version.
    """
    try:
        analysis_type = getattr(
            AnalysisType, request.analysis_type.upper(), AnalysisType.PHOTO
        )

        result = await asyncio.to_thread(
            critic_service.analyze_prompt,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            analysis_type=analysis_type,
        )

        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "analysis_failed",
                    "message": result.get("message", "Critic service returned an error."),
                },
            )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error("Sandbox /critic/analyze error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during analysis.",
            },
        )

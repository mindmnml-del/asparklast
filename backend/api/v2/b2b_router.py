"""
B2B Core API (V2) -- Tenant-scoped AI generation and critic analysis.
Protected by per-tenant X-API-Key header (managed via Admin API).
"""

import asyncio
import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks

from core import models
from core.schemas import GenerationRequest, CriticAnalysisRequest
from core.api_key_auth import get_api_key_tenant
from core.usage_tracking import log_b2b_usage
from services.unified_ai_service import ai_service
from services.unified_critic_service import critic_service, AnalysisType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", summary="Generate AI prompt (B2B)")
async def b2b_generate(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    tenant: models.Tenant = Depends(get_api_key_tenant),
) -> Dict[str, Any]:
    """
    Generate an AI-enhanced prompt using the AISpark generation engine.
    Authenticated via X-API-Key header.
    """
    start_time = time.perf_counter()
    tracked_status = 200
    error_msg = None

    try:
        result = await ai_service.generate_response(request.model_dump())

        if isinstance(result, dict) and result.get("error"):
            tracked_status = 502
            error_msg = result.get("message", "AI generation service returned an error.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "generation_failed",
                    "message": error_msg,
                },
            )

        # Strip internal metadata before responding
        if isinstance(result, dict):
            result.pop("_metadata", None)

        return {
            "success": True,
            "data": result,
        }

    except HTTPException as exc:
        tracked_status = exc.status_code
        if error_msg is None:
            error_msg = str(exc.detail)
        raise
    except Exception:
        tracked_status = 500
        error_msg = "An unexpected error occurred during generation."
        logger.error("B2B /generate error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": error_msg,
            },
        )
    finally:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        background_tasks.add_task(
            log_b2b_usage,
            tenant_id=tenant.id,
            endpoint="/v2/b2b/generate",
            method="POST",
            status_code=tracked_status,
            response_time_ms=elapsed_ms,
            error_message=error_msg,
        )


@router.post("/critic/analyze", summary="Analyze prompt quality (B2B)")
async def b2b_critic_analyze(
    request: CriticAnalysisRequest,
    background_tasks: BackgroundTasks,
    tenant: models.Tenant = Depends(get_api_key_tenant),
) -> Dict[str, Any]:
    """
    Analyze prompt quality and receive scoring, strengths/weaknesses,
    and an improved version. Authenticated via X-API-Key header.
    """
    start_time = time.perf_counter()
    tracked_status = 200
    error_msg = None

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
            tracked_status = 502
            error_msg = result.get("message", "Critic service returned an error.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "analysis_failed",
                    "message": error_msg,
                },
            )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException as exc:
        tracked_status = exc.status_code
        if error_msg is None:
            error_msg = str(exc.detail)
        raise
    except Exception:
        tracked_status = 500
        error_msg = "An unexpected error occurred during analysis."
        logger.error("B2B /critic/analyze error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": error_msg,
            },
        )
    finally:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        background_tasks.add_task(
            log_b2b_usage,
            tenant_id=tenant.id,
            endpoint="/v2/b2b/critic/analyze",
            method="POST",
            status_code=tracked_status,
            response_time_ms=elapsed_ms,
            error_message=error_msg,
        )

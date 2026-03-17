"""Generation endpoints — prompt generation and Helios auto-generate."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from core import models, schemas, crud
from core.database import get_db
from services.unified_ai_service import ai_service
from core.helios_personalities import helios_system
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation"])


@router.post("/generate", response_model=schemas.GeneratedPrompt)
async def generate(
    request: schemas.StudioRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        if current_user.credits < 1:
            raise HTTPException(
                status_code=402,
                detail="Insufficient credits. Please purchase more credits to continue.",
            )

        # Extract token from Authorization header for RAG authentication
        user_token = None
        if authorization and authorization.startswith("Bearer "):
            user_token = authorization[7:]  # Remove "Bearer " prefix

        response = await ai_service.generate_response(request.dict(), user_token)

        if response.get("error"):
            raise HTTPException(status_code=500, detail=response.get("message"))

        prompt = crud.create_generated_prompt(db, response, current_user.id)
        if not prompt:
            raise HTTPException(status_code=500, detail="Failed to save prompt")

        # Deduct a credit
        current_user.credits -= 1
        db.commit()

        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail="Generation failed")


@router.post("/helios/auto-generate")
async def auto_generate_with_helios(
    generation_request: schemas.GenerationRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate prompt with automatic Helios personality selection"""
    try:
        if current_user.credits < 1:
            raise HTTPException(
                status_code=402,
                detail="Insufficient credits. Please purchase more credits to continue.",
            )

        # Analyze request for personality selection
        analysis = helios_system.analyze_request(
            generation_request.prompt,
            {
                "style": generation_request.style,
                "type": generation_request.type,
                "tool": generation_request.tool,
            },
        )

        # Select optimal personality
        primary, secondary, reasoning = helios_system.select_personality(analysis)

        # Enhance prompt with personality
        enhanced_prompt = helios_system.get_personality_prompt_enhancement(
            primary, generation_request.prompt
        )

        # Create enhanced generation request
        enhanced_request = schemas.GenerationRequest(
            prompt=enhanced_prompt,
            negative_prompt=generation_request.negative_prompt,
            style=generation_request.style,
            type=generation_request.type,
            tool=generation_request.tool,
            diversity_enabled=generation_request.diversity_enabled,
            rag_enabled=generation_request.rag_enabled,
        )

        # Generate with enhanced prompt
        result = await ai_service.generate_response(enhanced_request.model_dump())

        # Add Helios metadata
        if result.get("_metadata"):
            result["_metadata"]["helios"] = {
                "primary_personality": primary.value,
                "secondary_personalities": [p.value for p in secondary],
                "selection_reasoning": reasoning,
                "original_prompt": generation_request.prompt,
                "enhanced_prompt": enhanced_prompt,
            }

        # Save to database
        try:
            prompt_obj = crud.create_generated_prompt(db, result, current_user.id)
            logger.info(
                f"Helios-enhanced prompt created: ID {prompt_obj.id} for user {current_user.id}"
            )
            result["id"] = prompt_obj.id
            result["created_at"] = prompt_obj.created_at.isoformat()

            # Deduct credit
            current_user.credits -= 1
            db.commit()
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            db.rollback()

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Helios auto-generate error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate with Helios personality"
        )

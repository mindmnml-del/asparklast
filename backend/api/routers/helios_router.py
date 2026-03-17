"""Helios Master Prompt System endpoints — personality selection, enhancement, stats."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends

from core import models
from core.helios_personalities import helios_system, PersonalityType
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Helios"])


@router.post("/helios/analyze")
def analyze_prompt_request(
    prompt_request: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
):
    """Analyze user prompt request for optimal personality selection"""
    try:
        user_prompt = prompt_request.get("prompt", "")
        context = prompt_request.get("context", {})

        if not user_prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Analyze request
        analysis = helios_system.analyze_request(user_prompt, context)

        # Select personality
        primary, secondary, reasoning = helios_system.select_personality(analysis)

        return {
            "success": True,
            "analysis": analysis,
            "personality_selection": {
                "primary": {
                    "type": primary.value,
                    "profile": helios_system.personalities[primary].__dict__,
                },
                "secondary": [
                    {
                        "type": p.value,
                        "profile": helios_system.personalities[p].__dict__,
                    }
                    for p in secondary
                ],
                "reasoning": reasoning,
            },
        }
    except Exception as e:
        logger.error(f"Helios analysis error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to analyze prompt request"
        )


@router.post("/helios/enhance")
def enhance_with_personality(
    enhancement_request: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
):
    """Enhance prompt using specific Helios personality"""
    try:
        base_prompt = enhancement_request.get("prompt", "")
        personality_name = enhancement_request.get("personality", "athena")

        if not base_prompt:
            raise HTTPException(status_code=400, detail="Base prompt is required")

        # Convert personality name to enum
        try:
            personality = PersonalityType(personality_name.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid personality. Valid options: {[p.value for p in PersonalityType]}",
            )

        # Enhance prompt
        enhanced_prompt = helios_system.get_personality_prompt_enhancement(
            personality, base_prompt
        )
        signature_elements = helios_system.get_personality_signature_elements(
            personality
        )
        context = helios_system.generate_personality_context(personality)

        return {
            "success": True,
            "original_prompt": base_prompt,
            "enhanced_prompt": enhanced_prompt,
            "personality": {
                "name": personality.value,
                "profile": helios_system.personalities[personality].__dict__,
            },
            "signature_elements": signature_elements,
            "personality_context": context,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Helios enhancement error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enhance prompt")


@router.get("/helios/personalities")
def list_personalities(current_user: models.User = Depends(get_current_user)):
    """List all available Helios personalities"""
    try:
        personalities = {}
        for personality_type, profile in helios_system.personalities.items():
            personalities[personality_type.value] = {
                "name": profile.name,
                "symbol": profile.symbol,
                "title": profile.title,
                "specialization": profile.specialization,
                "traits": profile.traits,
                "signature_elements": profile.signature_elements,
                "language_style": profile.language_style,
                "strengths": profile.strengths,
            }

        return {
            "success": True,
            "personalities": personalities,
            "total_count": len(personalities),
        }
    except Exception as e:
        logger.error(f"Helios personalities listing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list personalities")


@router.get("/helios/personality/{personality_name}")
def get_personality_details(
    personality_name: str,
    current_user: models.User = Depends(get_current_user),
):
    """Get detailed information about specific personality"""
    try:
        try:
            personality = PersonalityType(personality_name.lower())
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Personality '{personality_name}' not found. Valid options: {[p.value for p in PersonalityType]}",
            )

        profile = helios_system.personalities[personality]

        return {
            "success": True,
            "personality": {
                "type": personality.value,
                "name": profile.name,
                "symbol": profile.symbol,
                "title": profile.title,
                "specialization": profile.specialization,
                "traits": profile.traits,
                "signature_elements": profile.signature_elements,
                "language_style": profile.language_style,
                "strengths": profile.strengths,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Helios personality details error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get personality details"
        )


@router.get("/helios/stats")
def get_helios_stats(current_user: models.User = Depends(get_current_user)):
    """Get Helios personality selection statistics"""
    try:
        stats = helios_system.get_selection_stats()

        return {
            "success": True,
            "stats": stats,
            "system_info": {
                "total_personalities": len(helios_system.personalities),
                "personality_names": [p.value for p in PersonalityType],
            },
        }
    except Exception as e:
        logger.error(f"Helios stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Helios stats")

"""Character Lock endpoints — CRUD, session lock/unlock, stats, trait extraction."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from core import models, schemas
from services.unified_ai_service import ai_service
from core.character_lock import character_manager, CharacterSheet
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Characters"])


@router.post("/characters/create")
def create_character(
    character_data: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
):
    """Create a new character for video consistency"""
    try:
        # Add user association
        character_data["created_by"] = current_user.id

        character = character_manager.create_character(character_data)
        return {
            "success": True,
            "character": character.to_dict(),
            "message": f"Character '{character.name}' created successfully",
        }
    except Exception as e:
        logger.error(f"Character creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create character")


@router.get("/characters/list")
def list_characters(current_user: models.User = Depends(get_current_user)):
    """List all available characters"""
    try:
        characters = character_manager.get_all_characters()
        return {
            "success": True,
            "characters": [char.to_dict() for char in characters],
            "total": len(characters),
        }
    except Exception as e:
        logger.error(f"Character listing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list characters")


@router.get("/characters/session/current")
def get_session_character(
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user),
):
    """Get currently locked character for session"""
    character = character_manager.get_session_character(session_id)
    if not character:
        return {
            "success": True,
            "character": None,
            "message": "No character locked for this session",
        }

    return {
        "success": True,
        "character": character.to_dict(),
        "session_id": session_id,
    }


@router.get("/characters/stats")
def get_character_stats(current_user: models.User = Depends(get_current_user)):
    """Get character usage statistics"""
    try:
        stats = character_manager.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Character stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get character stats")


@router.post("/characters/extract-from-prompt")
def extract_character_from_prompt(
    request: schemas.CharacterExtractionRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Extract character/environment traits from a prompt using AI"""
    try:
        result = ai_service.extract_character_traits(request.prompt)
        return {
            "success": True,
            "extracted": result,
            "is_character": result.get("is_character", False),
        }
    except Exception as e:
        logger.error(f"Character extraction error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to extract character traits"
        )


@router.get("/characters/{character_id}")
def get_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Get specific character details"""
    character = character_manager.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    return {"success": True, "character": character.to_dict()}


@router.put("/characters/{character_id}")
def update_character(
    character_id: str,
    updates: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
):
    """Update existing character"""
    try:
        character = character_manager.update_character(character_id, updates)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        return {
            "success": True,
            "character": character.to_dict(),
            "message": f"Character '{character.name}' updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update character")


@router.delete("/characters/{character_id}")
def delete_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Delete character"""
    try:
        success = character_manager.delete_character(character_id)
        if not success:
            raise HTTPException(status_code=404, detail="Character not found")

        return {"success": True, "message": "Character deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete character")


@router.post("/characters/{character_id}/lock")
def lock_character(
    character_id: str,
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user),
):
    """Lock character for session consistency"""
    try:
        success = character_manager.lock_character_for_session(session_id, character_id)
        if not success:
            raise HTTPException(status_code=404, detail="Character not found")

        character = character_manager.get_character(character_id)
        return {
            "success": True,
            "message": f"Character '{character.name}' locked for session",
            "session_id": session_id,
            "character_id": character_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character lock error: {e}")
        raise HTTPException(status_code=500, detail="Failed to lock character")


@router.delete("/characters/unlock")
def unlock_character(
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user),
):
    """Release character lock for session"""
    try:
        success = character_manager.release_session_lock(session_id)
        return {
            "success": True,
            "message": "Character lock released" if success else "No active lock found",
            "session_id": session_id,
        }
    except Exception as e:
        logger.error(f"Character unlock error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unlock character")

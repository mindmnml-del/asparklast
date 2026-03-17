"""Prompt CRUD endpoints — list, get, favorite, delete, export."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core import models, schemas, crud
from core.database import get_db
from services.export_service import export_service
from api.routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prompts"])


@router.get("/prompts", response_model=List[schemas.GeneratedPromptHistory])
def get_prompts(
    skip: int = 0,
    limit: int = 20,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_prompts_by_user(db, current_user.id, skip, limit, favorites_only)


@router.get("/prompts/export/{format}")
def export_prompts(
    format: str,
    skip: int = 0,
    limit: int = 1000,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Export user prompts in specified format (json, csv, txt)"""

    # Validate format
    if format.lower() not in ["json", "csv", "txt"]:
        raise HTTPException(
            status_code=400, detail="Invalid format. Use: json, csv, or txt"
        )

    try:
        # Get user's prompts with full data
        prompts = crud.get_prompts_by_user(
            db, current_user.id, skip, limit, favorites_only
        )

        if not prompts:
            raise HTTPException(status_code=404, detail="No prompts found to export")

        # Get full prompt data for export
        full_prompts = []
        for prompt_summary in prompts:
            full_prompt = crud.get_prompt_by_id(db, prompt_summary.id, current_user.id)
            if full_prompt:
                full_prompts.append(full_prompt)

        # Export based on format
        format_lower = format.lower()

        if format_lower == "json":
            content = export_service.export_to_json(full_prompts)
            media_type = "application/json"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.json"

        elif format_lower == "csv":
            content = export_service.export_to_csv(full_prompts)
            media_type = "text/csv"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.csv"

        elif format_lower == "txt":
            content = export_service.export_to_txt(full_prompts)
            media_type = "text/plain"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.txt"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": f"{media_type}; charset=utf-8",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/prompts/{prompt_id}", response_model=schemas.GeneratedPrompt)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prompt = crud.get_prompt_by_id(db, prompt_id, current_user.id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.put("/prompts/{prompt_id}/favorite", response_model=schemas.GeneratedPrompt)
def toggle_favorite(
    prompt_id: int,
    is_favorite: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    prompt = crud.update_prompt_favorite_status(
        db, prompt_id, current_user.id, is_favorite
    )
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.delete("/prompts/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    success = crud.delete_prompt(db, prompt_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"success": True}

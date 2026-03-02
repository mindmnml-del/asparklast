"""
AISpark Studio - Optimized FastAPI Application
Consolidated and optimized backend with unified services
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import Response
from sqlalchemy.orm import Session

from config import settings
from core import models, schemas, crud, auth
from core.database import get_db, create_tables
from services.unified_ai_service import ai_service
from services.unified_critic_service import critic_service, AnalysisType
from services.vertex_search_service import vertex_search_service
from services.export_service import export_service
from core.character_lock import character_manager, CharacterSheet
from core.helios_personalities import helios_system, PersonalityType
from utils.health_check import get_health_status, get_quick_health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("🚀 AISpark Studio starting...")
    
    try:
        create_tables()
        logger.info("✅ Database ready")
        
        if ai_service.ensure_ready():
            logger.info("✅ AI Service ready")
        
        logger.info("🎉 AISpark Studio ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    logger.info("🛑 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AISpark Studio API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = auth.decode_access_token(token)
        if not payload:
            raise credentials_exception
        
        email = payload.get("sub")
        if not email:
            raise credentials_exception
        
        user = crud.get_user_by_email(db, email=email)
        if not user or not user.is_active:
            raise credentials_exception
        
        return user
    except Exception:
        raise credentials_exception

# Endpoints
@app.get("/")
def root():
    return {"message": "AISpark Studio API v2.0", "docs": "/docs"}

@app.get("/health")
def health():
    return get_quick_health()

@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth.create_user_token(user.email)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/register", response_model=schemas.User)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = crud.create_user(db, user_data)
    if not user:
        raise HTTPException(status_code=500, detail="Registration failed")
    return user

@app.get("/users/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/generate", response_model=schemas.GeneratedPrompt)
async def generate(
    request: schemas.StudioRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        if current_user.credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient credits. Please purchase more credits to continue.")
            
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

@app.get("/prompts", response_model=List[schemas.GeneratedPromptHistory])
def get_prompts(
    skip: int = 0,
    limit: int = 20,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_prompts_by_user(db, current_user.id, skip, limit, favorites_only)

@app.get("/prompts/{prompt_id}", response_model=schemas.GeneratedPrompt)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prompt = crud.get_prompt_by_id(db, prompt_id, current_user.id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@app.put("/prompts/{prompt_id}/favorite", response_model=schemas.GeneratedPrompt)
def toggle_favorite(
    prompt_id: int,
    is_favorite: bool,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    prompt = crud.update_prompt_favorite_status(db, prompt_id, current_user.id, is_favorite)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@app.delete("/prompts/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    success = crud.delete_prompt(db, prompt_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"success": True}

@app.get("/search/vertex")
async def vertex_search(
    q: str,
    limit: int = 10,
    filter: Optional[str] = None,
    current_user: models.User = Depends(get_current_user)
):
    """Vertex AI Search endpoint"""
    if not vertex_search_service.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Vertex AI Search service not available"
        )
    
    try:
        result = await vertex_search_service.search(
            query=q,
            max_results=limit,
            filter_expression=filter
        )
        
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Search failed")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Vertex search error: {e}")
        raise HTTPException(status_code=500, detail="Search request failed")

@app.get("/search/vertex/status")
def vertex_search_status(current_user: models.User = Depends(get_current_user)):
    """Get Vertex AI Search service status"""
    return vertex_search_service.get_status()

@app.post("/critic/analyze")
async def analyze_prompt(
    request: schemas.CriticAnalysisRequest,
    current_user: models.User = Depends(get_current_user)
):
    """Analyze prompt quality and suggest improvements"""
    try:
        analysis_type = getattr(AnalysisType, request.analysis_type.upper(), 
                               AnalysisType.PHOTO)
        
        result = critic_service.analyze_prompt(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt or "",
            analysis_type=analysis_type
        )
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        return result
        
    except Exception as e:
        logger.error(f"Critic analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.get("/critic/stats")
def critic_stats(current_user: models.User = Depends(get_current_user)):
    """Get critic service statistics"""
    return critic_service.get_stats()

@app.get("/prompts/export/{format}")
def export_prompts(
    format: str,
    skip: int = 0,
    limit: int = 1000,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Export user prompts in specified format (json, csv, txt)"""
    
    # Validate format
    if format.lower() not in ['json', 'csv', 'txt']:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, csv, or txt")
    
    try:
        # Get user's prompts with full data
        prompts = crud.get_prompts_by_user(db, current_user.id, skip, limit, favorites_only)
        
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
        
        if format_lower == 'json':
            content = export_service.export_to_json(full_prompts)
            media_type = "application/json"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.json"
            
        elif format_lower == 'csv':
            content = export_service.export_to_csv(full_prompts)
            media_type = "text/csv"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.csv"
            
        elif format_lower == 'txt':
            content = export_service.export_to_txt(full_prompts)
            media_type = "text/plain"
            filename = f"aispark_prompts_{current_user.id}_{len(full_prompts)}.txt"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": f"{media_type}; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

# Character Lock System Endpoints

@app.post("/characters/create")
def create_character(
    character_data: Dict[str, Any],
    current_user: models.User = Depends(get_current_user)
):
    """Create a new character for video consistency"""
    try:
        # Add user association
        character_data["created_by"] = current_user.id
        
        character = character_manager.create_character(character_data)
        return {
            "success": True,
            "character": character.to_dict(),
            "message": f"Character '{character.name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Character creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create character")

@app.get("/characters/list")
def list_characters(current_user: models.User = Depends(get_current_user)):
    """List all available characters"""
    try:
        characters = character_manager.get_all_characters()
        return {
            "success": True,
            "characters": [char.to_dict() for char in characters],
            "total": len(characters)
        }
    except Exception as e:
        logger.error(f"Character listing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list characters")

@app.get("/characters/{character_id}")
def get_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Get specific character details"""
    character = character_manager.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "success": True,
        "character": character.to_dict()
    }

@app.put("/characters/{character_id}")
def update_character(
    character_id: str,
    updates: Dict[str, Any],
    current_user: models.User = Depends(get_current_user)
):
    """Update existing character"""
    try:
        character = character_manager.update_character(character_id, updates)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        return {
            "success": True,
            "character": character.to_dict(),
            "message": f"Character '{character.name}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update character")

@app.delete("/characters/{character_id}")
def delete_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Delete character"""
    try:
        success = character_manager.delete_character(character_id)
        if not success:
            raise HTTPException(status_code=404, detail="Character not found")
        
        return {
            "success": True,
            "message": "Character deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete character")

@app.post("/characters/{character_id}/lock")
def lock_character(
    character_id: str,
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user)
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
            "character_id": character_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Character lock error: {e}")
        raise HTTPException(status_code=500, detail="Failed to lock character")

@app.delete("/characters/unlock")
def unlock_character(
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user)
):
    """Release character lock for session"""
    try:
        success = character_manager.release_session_lock(session_id)
        return {
            "success": True,
            "message": "Character lock released" if success else "No active lock found",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Character unlock error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unlock character")

@app.get("/characters/session/current")
def get_session_character(
    session_id: str = Header(..., alias="X-Session-ID"),
    current_user: models.User = Depends(get_current_user)
):
    """Get currently locked character for session"""
    character = character_manager.get_session_character(session_id)
    if not character:
        return {
            "success": True,
            "character": None,
            "message": "No character locked for this session"
        }
    
    return {
        "success": True,
        "character": character.to_dict(),
        "session_id": session_id
    }

@app.get("/characters/stats")
def get_character_stats(current_user: models.User = Depends(get_current_user)):
    """Get character usage statistics"""
    try:
        stats = character_manager.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Character stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get character stats")

# Helios Master Prompt System Endpoints

@app.post("/helios/analyze")
def analyze_prompt_request(
    prompt_request: Dict[str, Any],
    current_user: models.User = Depends(get_current_user)
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
                    "profile": helios_system.personalities[primary].__dict__
                },
                "secondary": [
                    {
                        "type": p.value,
                        "profile": helios_system.personalities[p].__dict__
                    } for p in secondary
                ],
                "reasoning": reasoning
            }
        }
    except Exception as e:
        logger.error(f"Helios analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze prompt request")

@app.post("/helios/enhance")
def enhance_with_personality(
    enhancement_request: Dict[str, Any],
    current_user: models.User = Depends(get_current_user)
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
                detail=f"Invalid personality. Valid options: {[p.value for p in PersonalityType]}"
            )
        
        # Enhance prompt
        enhanced_prompt = helios_system.get_personality_prompt_enhancement(personality, base_prompt)
        signature_elements = helios_system.get_personality_signature_elements(personality)
        context = helios_system.generate_personality_context(personality)
        
        return {
            "success": True,
            "original_prompt": base_prompt,
            "enhanced_prompt": enhanced_prompt,
            "personality": {
                "name": personality.value,
                "profile": helios_system.personalities[personality].__dict__
            },
            "signature_elements": signature_elements,
            "personality_context": context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Helios enhancement error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enhance prompt")

@app.get("/helios/personalities")
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
                "strengths": profile.strengths
            }
        
        return {
            "success": True,
            "personalities": personalities,
            "total_count": len(personalities)
        }
    except Exception as e:
        logger.error(f"Helios personalities listing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list personalities")

@app.get("/helios/personality/{personality_name}")
def get_personality_details(
    personality_name: str,
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed information about specific personality"""
    try:
        try:
            personality = PersonalityType(personality_name.lower())
        except ValueError:
            raise HTTPException(
                status_code=404, 
                detail=f"Personality '{personality_name}' not found. Valid options: {[p.value for p in PersonalityType]}"
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
                "strengths": profile.strengths
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Helios personality details error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get personality details")

@app.get("/helios/stats")
def get_helios_stats(current_user: models.User = Depends(get_current_user)):
    """Get Helios personality selection statistics"""
    try:
        stats = helios_system.get_selection_stats()
        
        return {
            "success": True,
            "stats": stats,
            "system_info": {
                "total_personalities": len(helios_system.personalities),
                "personality_names": [p.value for p in PersonalityType]
            }
        }
    except Exception as e:
        logger.error(f"Helios stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Helios stats")

@app.post("/helios/auto-generate")
async def auto_generate_with_helios(
    generation_request: schemas.GenerationRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate prompt with automatic Helios personality selection"""
    try:
        if current_user.credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient credits. Please purchase more credits to continue.")
            
        # Analyze request for personality selection
        analysis = helios_system.analyze_request(generation_request.prompt, {
            "style": generation_request.style,
            "type": generation_request.type,
            "tool": generation_request.tool
        })
        
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
            rag_enabled=generation_request.rag_enabled
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
                "enhanced_prompt": enhanced_prompt
            }
        
        # Save to database
        try:
            prompt_obj = crud.create_generated_prompt(db, result, current_user.id)
            logger.info(f"✅ Helios-enhanced prompt created: ID {prompt_obj.id} for user {current_user.id}")
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
        raise HTTPException(status_code=500, detail="Failed to generate with Helios personality")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

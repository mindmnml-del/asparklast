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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_prompts_by_user(db, current_user.id, skip, limit)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

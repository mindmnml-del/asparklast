"""
AISpark Studio - Optimized FastAPI Application
Consolidated and optimized backend with unified services
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from core import models, schemas, crud, auth
from core.database import get_db, create_tables
from services.unified_ai_service import ai_service
from services.unified_critic_service import critic_service
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        response = await ai_service.generate_response(request.dict())
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

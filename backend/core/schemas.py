"""
Pydantic Schemas for AISpark Studio API
Request/response models with validation
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- Base and Create Schemas ---

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    liked: bool
    comment: Optional[str] = None

class StudioRequest(BaseModel):
    """Schema for AI prompt generation request"""
    # Core Concept
    subject_action: str = Field(..., min_length=3, description="Main subject and action")
    environment_setting: Optional[str] = ""

    # Technical & Artistic Details
    shot_type: Optional[str] = "Default"
    lighting: Optional[str] = ""
    mood: Optional[str] = "Default"
    color_palette: Optional[str] = ""
    artistic_styles: List[str] = []
    negative_prompts: Optional[str] = ""

    # Target & Configuration
    prompt_type: str = Field(default="image", pattern="^(image|video)$")
    target_model: str
    use_rag: bool = True
    user_language: str = 'en'

class GenerationRequest(BaseModel):
    """Schema for AI prompt generation request"""
    prompt: str = Field(..., min_length=3, description="User prompt for generation")
    negative_prompt: Optional[str] = ""
    style: str = "professional"
    type: str = Field(default="image", pattern="^(image|video|universal)$")
    tool: str = "Universal"
    diversity_enabled: bool = True
    rag_enabled: bool = True

class CriticAnalysisRequest(BaseModel):
    """Schema for critic analysis request"""
    prompt: str = Field(..., min_length=10)
    negative_prompt: Optional[str] = ""
    analysis_type: str = Field(default="photo", pattern="^(photo|video|both)$")

# --- Response Schemas ---

class User(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    credits: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Feedback(BaseModel):
    """Feedback response schema"""
    id: int
    liked: bool
    comment: Optional[str] = None
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GeneratedPrompt(BaseModel):
    """Generated prompt response schema"""
    id: int
    raw_response: Dict[str, Any]  # Full AI response
    title: Optional[str]
    is_favorite: bool
    created_at: datetime
    owner_id: int
    feedback: List[Feedback] = []

    model_config = ConfigDict(from_attributes=True)

class GeneratedPromptHistory(BaseModel):
    """Simplified prompt for history listing"""
    id: int
    title: Optional[str]
    is_favorite: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PromptStructure(BaseModel):
    """Structured prompt components"""
    subject: str
    setting: str
    lighting: str
    composition: str
    styleAndMedium: str
    technicalDetails: str
    mood: str

class AIResponse(BaseModel):
    """Complete AI generation response"""
    structuredPrompt: PromptStructure
    paragraphPrompt: str
    negativePrompt: str
    tool: str
    type: str
    _metadata: Optional[Dict[str, Any]] = None

class CriticAnalysis(BaseModel):
    """Critic analysis response"""
    overall_score: int
    category_scores: Dict[str, int]
    assessment: str
    strengths: List[str]
    weaknesses: List[str]
    top_suggestion: str
    improved_prompt: Optional[str] = None

class ServiceStatus(BaseModel):
    """Service status response"""
    configured: bool
    model_name: Optional[str] = None
    request_count: int = 0
    avg_response_time: float = 0.0
    cache_stats: Dict[str, Any] = {}
    last_error: Optional[str] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str

# --- Authentication Schemas ---

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None

# --- Error Schemas ---

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    message: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    invalid_value: Any

# --- Analytics Schemas ---

class UsageStats(BaseModel):
    """Usage statistics response"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    most_popular_styles: List[str]
    user_count: int

class CacheStats(BaseModel):
    """Cache statistics response"""
    enabled: bool
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    ttl_seconds: int

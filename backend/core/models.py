"""
Database Models for AISpark Studio
Optimized SQLAlchemy models with proper relationships
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for authentication and prompt ownership"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    credits = Column(Integer, default=3)  # Monetization: Free initial credits
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # B2B tenant association (nullable for existing B2C users)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    # Relationships
    generated_prompts = relationship("GeneratedPrompt", back_populates="owner", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self):
        return f"<User(email='{self.email}', active={self.is_active})>"

class GeneratedPrompt(Base):
    """Generated prompt storage with full AI response data"""
    __tablename__ = "generated_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    raw_response = Column(JSON, nullable=False)  # Complete AI response as JSON
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    # Relationships
    owner = relationship("User", back_populates="generated_prompts")
    feedback = relationship("Feedback", back_populates="prompt", cascade="all, delete-orphan")
    tenant = relationship("Tenant", back_populates="generated_prompts")
    
    def __repr__(self):
        return f"<GeneratedPrompt(id={self.id}, title='{self.title}', owner_id={self.owner_id})>"

class Feedback(Base):
    """User feedback on generated prompts"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    liked = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    prompt_id = Column(Integer, ForeignKey("generated_prompts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    # Relationships
    prompt = relationship("GeneratedPrompt", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
    tenant = relationship("Tenant", back_populates="feedback_items")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, liked={self.liked}, prompt_id={self.prompt_id})>"

class ApiUsage(Base):
    """Track API usage for analytics and rate limiting"""
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")
    tenant = relationship("Tenant", back_populates="api_usage_records")

    def __repr__(self):
        return f"<ApiUsage(user_id={self.user_id}, endpoint='{self.endpoint}', status={self.status_code})>"

class SystemMetrics(Base):
    """System performance and health metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    tags = Column(JSON, nullable=True)  # Additional metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(name='{self.metric_name}', value='{self.metric_value}')>"


class Character(Base):
    """Character sheet storage for visual consistency across generations"""
    __tablename__ = "characters"

    character_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, default="Unnamed Character")
    description = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=False, default="person")
    gender = Column(String(50), nullable=False, default="unspecified")
    age_range = Column(String(50), nullable=False, default="young adult (20-35)")
    build = Column(String(50), nullable=False, default="average")
    version = Column(String(20), nullable=False, default="1.0")

    # Ownership (nullable for backward compat with migrated data)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Usage statistics
    times_used = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    successful_generations = Column(Integer, nullable=False, default=0)

    # All remaining fields (eye_color, hair_style, etc.) as JSON blob
    attributes = Column(JSON, nullable=True, default=dict)

    # Relationships
    owner = relationship("User", backref="characters")
    tenant = relationship("Tenant", back_populates="characters")

    def __repr__(self):
        return f"<Character(id='{self.character_id}', name='{self.name}')>"


class Tenant(Base):
    """B2B tenant organization that owns API keys and groups users/data"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant")
    generated_prompts = relationship("GeneratedPrompt", back_populates="tenant")
    feedback_items = relationship("Feedback", back_populates="tenant")
    api_usage_records = relationship("ApiUsage", back_populates="tenant")
    characters = relationship("Character", back_populates="tenant")
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', active={self.is_active})>"


class ApiKey(Base):
    """Hashed API key for B2B tenant authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex digest
    prefix = Column(String(20), nullable=False)  # e.g. "aispark_abc12345" for display
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=True)  # human-friendly label
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

    def __repr__(self):
        return f"<ApiKey(prefix='{self.prefix}', tenant_id={self.tenant_id}, active={self.is_active})>"

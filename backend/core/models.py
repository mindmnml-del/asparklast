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
    
    # Relationships
    generated_prompts = relationship("GeneratedPrompt", back_populates="owner", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    
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
    
    # Relationships
    owner = relationship("User", back_populates="generated_prompts")
    feedback = relationship("Feedback", back_populates="prompt", cascade="all, delete-orphan")
    
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
    
    # Relationships
    prompt = relationship("GeneratedPrompt", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, liked={self.liked}, prompt_id={self.prompt_id})>"

class ApiUsage(Base):
    """Track API usage for analytics and rate limiting"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<ApiUsage(user_id={self.user_id}, endpoint='{self.endpoint}', status={self.status_code})>"

class SystemMetrics(Base):
    """System performance and health metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    tags = Column(JSON, nullable=True)  # Additional metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(name='{self.metric_name}', value='{self.metric_value}')>"

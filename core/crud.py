"""
CRUD Operations for AISpark Studio
Database operations with optimized queries and error handling
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func

from . import models, schemas, auth

logger = logging.getLogger(__name__)

# --- User CRUD Operations ---

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    try:
        return db.query(models.User).filter(models.User.email == email.lower()).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

def create_user(db: Session, user: schemas.UserCreate) -> Optional[models.User]:
    """Create a new user"""
    try:
        hashed_password = auth.get_password_hash(user.password)
        db_user = models.User(
            email=user.email.lower(),
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"✅ User created: {user.email}")
        return db_user
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating user {user.email}: {e}")
        db.rollback()
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate user with email and password"""
    try:
        user = get_user_by_email(db, email)
        if not user:
            logger.warning(f"Authentication failed: user not found {email}")
            return None
        
        if not auth.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: wrong password {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: inactive user {email}")
            return None
        
        logger.info(f"✅ User authenticated: {email}")
        return user
        
    except SQLAlchemyError as e:
        logger.error(f"Error authenticating user {email}: {e}")
        return None

def update_user(db: Session, user_id: int, user_update: Dict[str, Any]) -> Optional[models.User]:
    """Update user information"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return None
        
        for field, value in user_update.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"✅ User updated: {db_user.email}")
        return db_user
        
    except SQLAlchemyError as e:
        logger.error(f"Error updating user {user_id}: {e}")
        db.rollback()
        return None

def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user account"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return False
        
        db_user.is_active = False
        db.commit()
        
        logger.info(f"✅ User deactivated: {db_user.email}")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        db.rollback()
        return False

# --- Generated Prompt CRUD Operations ---

def create_generated_prompt(
    db: Session, 
    prompt_data: Dict[str, Any], 
    owner_id: int
) -> Optional[models.GeneratedPrompt]:
    """Create and save a generated prompt"""
    try:
        # Generate title from prompt data
        title = _generate_prompt_title(prompt_data)
        
        db_prompt = models.GeneratedPrompt(
            raw_response=prompt_data,
            title=title,
            owner_id=owner_id,
            is_favorite=False
        )
        
        db.add(db_prompt)
        db.commit()
        db.refresh(db_prompt)
        
        logger.info(f"✅ Prompt created: ID {db_prompt.id} for user {owner_id}")
        return db_prompt
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating prompt for user {owner_id}: {e}")
        db.rollback()
        return None

def get_prompts_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    favorites_only: bool = False
) -> List[models.GeneratedPrompt]:
    """Get prompts for a specific user with pagination"""
    try:
        query = db.query(models.GeneratedPrompt).filter(
            models.GeneratedPrompt.owner_id == user_id
        )
        
        if favorites_only:
            query = query.filter(models.GeneratedPrompt.is_favorite == True)
        
        query = query.order_by(desc(models.GeneratedPrompt.created_at))
        
        return query.offset(skip).limit(limit).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prompts for user {user_id}: {e}")
        return []

def get_prompt_by_id(
    db: Session, 
    prompt_id: int, 
    user_id: int
) -> Optional[models.GeneratedPrompt]:
    """Get a specific prompt, ensuring it belongs to the user"""
    try:
        return db.query(models.GeneratedPrompt).filter(
            models.GeneratedPrompt.id == prompt_id,
            models.GeneratedPrompt.owner_id == user_id
        ).first()
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prompt {prompt_id} for user {user_id}: {e}")
        return None

def update_prompt_favorite_status(
    db: Session, 
    prompt_id: int, 
    user_id: int, 
    is_favorite: bool
) -> Optional[models.GeneratedPrompt]:
    """Update the favorite status of a prompt"""
    try:
        db_prompt = get_prompt_by_id(db, prompt_id, user_id)
        if not db_prompt:
            return None
        
        db_prompt.is_favorite = is_favorite
        db.commit()
        db.refresh(db_prompt)
        
        logger.info(f"✅ Prompt {prompt_id} favorite status updated: {is_favorite}")
        return db_prompt
        
    except SQLAlchemyError as e:
        logger.error(f"Error updating favorite status for prompt {prompt_id}: {e}")
        db.rollback()
        return None

def delete_prompt(db: Session, prompt_id: int, user_id: int) -> bool:
    """Delete a prompt"""
    try:
        db_prompt = get_prompt_by_id(db, prompt_id, user_id)
        if not db_prompt:
            return False
        
        db.delete(db_prompt)
        db.commit()
        
        logger.info(f"✅ Prompt {prompt_id} deleted by user {user_id}")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error deleting prompt {prompt_id}: {e}")
        db.rollback()
        return False

# --- Feedback CRUD Operations ---

def create_prompt_feedback(
    db: Session, 
    feedback: schemas.FeedbackCreate, 
    prompt_id: int, 
    user_id: int
) -> Optional[models.Feedback]:
    """Create feedback for a specific prompt"""
    try:
        # Check if prompt exists and belongs to user
        prompt = get_prompt_by_id(db, prompt_id, user_id)
        if not prompt:
            logger.warning(f"Feedback creation failed: prompt {prompt_id} not found for user {user_id}")
            return None
        
        # Check if feedback already exists
        existing_feedback = db.query(models.Feedback).filter(
            models.Feedback.prompt_id == prompt_id,
            models.Feedback.user_id == user_id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.liked = feedback.liked
            existing_feedback.comment = feedback.comment
            db.commit()
            db.refresh(existing_feedback)
            
            logger.info(f"✅ Feedback updated for prompt {prompt_id}")
            return existing_feedback
        else:
            # Create new feedback
            db_feedback = models.Feedback(
                liked=feedback.liked,
                comment=feedback.comment,
                prompt_id=prompt_id,
                user_id=user_id
            )
            
            db.add(db_feedback)
            db.commit()
            db.refresh(db_feedback)
            
            logger.info(f"✅ Feedback created for prompt {prompt_id}")
            return db_feedback
            
    except SQLAlchemyError as e:
        logger.error(f"Error creating feedback for prompt {prompt_id}: {e}")
        db.rollback()
        return None

def get_feedback_by_prompt(db: Session, prompt_id: int) -> List[models.Feedback]:
    """Get all feedback for a specific prompt"""
    try:
        return db.query(models.Feedback).filter(
            models.Feedback.prompt_id == prompt_id
        ).order_by(desc(models.Feedback.created_at)).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching feedback for prompt {prompt_id}: {e}")
        return []

# --- Analytics and Stats ---

def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get statistics for a specific user"""
    try:
        total_prompts = db.query(models.GeneratedPrompt).filter(
            models.GeneratedPrompt.owner_id == user_id
        ).count()
        
        favorite_prompts = db.query(models.GeneratedPrompt).filter(
            models.GeneratedPrompt.owner_id == user_id,
            models.GeneratedPrompt.is_favorite == True
        ).count()
        
        total_feedback = db.query(models.Feedback).filter(
            models.Feedback.user_id == user_id
        ).count()
        
        positive_feedback = db.query(models.Feedback).filter(
            models.Feedback.user_id == user_id,
            models.Feedback.liked == True
        ).count()
        
        return {
            "total_prompts": total_prompts,
            "favorite_prompts": favorite_prompts,
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "feedback_ratio": positive_feedback / max(total_feedback, 1)
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting stats for user {user_id}: {e}")
        return {}

def get_system_stats(db: Session) -> Dict[str, Any]:
    """Get system-wide statistics"""
    try:
        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.is_active == True).count()
        total_prompts = db.query(models.GeneratedPrompt).count()
        total_feedback = db.query(models.Feedback).count()
        
        # Most popular artistic styles (simplified)
        # This would need more complex query for actual implementation
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_prompts": total_prompts,
            "total_feedback": total_feedback,
            "avg_prompts_per_user": total_prompts / max(active_users, 1)
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error getting system stats: {e}")
        return {}

# --- Utility Functions ---

def _generate_prompt_title(prompt_data: Dict[str, Any]) -> str:
    """Generate a title from prompt data"""
    try:
        structured = prompt_data.get('structuredPrompt', {})
        subject = structured.get('subject', '')
        
        if subject:
            # Truncate and clean up the subject for title
            title = subject[:75].strip()
            if len(subject) > 75:
                title += "..."
            return title
        
        # Fallback to paragraph prompt
        paragraph = prompt_data.get('paragraphPrompt', '')
        if paragraph:
            title = paragraph[:50].strip()
            if len(paragraph) > 50:
                title += "..."
            return title
        
        return "Untitled Prompt"
        
    except Exception as e:
        logger.warning(f"Error generating prompt title: {e}")
        return "Untitled Prompt"

def search_prompts(
    db: Session, 
    user_id: int, 
    search_term: str, 
    limit: int = 20
) -> List[models.GeneratedPrompt]:
    """Search user's prompts by text content"""
    try:
        # Simple text search in title and raw response
        # For production, consider full-text search or Elasticsearch
        
        search_pattern = f"%{search_term.lower()}%"
        
        return db.query(models.GeneratedPrompt).filter(
            models.GeneratedPrompt.owner_id == user_id,
            models.GeneratedPrompt.title.ilike(search_pattern)
        ).order_by(
            desc(models.GeneratedPrompt.created_at)
        ).limit(limit).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Error searching prompts for user {user_id}: {e}")
        return []

"""
Database Configuration and Connection Management
Optimized SQLAlchemy setup with connection pooling
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import settings

logger = logging.getLogger(__name__)

# Database URL from settings
DATABASE_URL = settings.database_url

# Create engine with optimized settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific optimizations
    # In-memory SQLite requires StaticPool to share one connection across threads.
    # File-based SQLite uses QueuePool to allow WAL-mode concurrent reads/writes.
    is_memory_db = ":memory:" in DATABASE_URL
    if is_memory_db:
        pool_kwargs: dict = {"poolclass": StaticPool}
    else:
        pool_kwargs = {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20,
        },
        echo=settings.debug_mode,
        **pool_kwargs,
    )
    
    # SQLite performance optimizations
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite performance pragmas"""
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Increase cache size (in KB)
        cursor.execute("PRAGMA cache_size=10000")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Synchronous = NORMAL for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
        
else:
    # PostgreSQL/MySQL optimizations
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug_mode,
    )

# Create sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Session:
    """
    Dependency for getting database session
    Ensures proper cleanup of connections
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all database tables (test fixtures; production uses Alembic)"""
    from .models import Base

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def drop_tables():
    """Drop all database tables (use with caution!)"""
    from .models import Base
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("⚠️ All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise

def get_db_info() -> dict:
    """Get database connection information"""
    return {
        "url": DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL,  # Hide credentials
        "dialect": engine.dialect.name,
        "driver": engine.dialect.driver,
        "pool_size": getattr(engine.pool, 'size', 'N/A'),
        "checked_out": getattr(engine.pool, 'checkedout', 'N/A'),
        "overflow": getattr(engine.pool, 'overflow', 'N/A'),
    }

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def health_check() -> bool:
        """Check database connection health"""
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    def get_stats() -> dict:
        """Get database statistics"""
        try:
            with SessionLocal() as db:
                from .models import User, GeneratedPrompt, Feedback
                
                stats = {
                    "users_count": db.query(User).count(),
                    "prompts_count": db.query(GeneratedPrompt).count(),
                    "feedback_count": db.query(Feedback).count(),
                    "connection_info": get_db_info()
                }
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def backup_database(backup_path: str) -> bool:
        """Backup database (SQLite only)"""
        if not DATABASE_URL.startswith("sqlite"):
            logger.warning("Backup only supported for SQLite databases")
            return False
        
        try:
            import shutil
            import sqlite3
            
            # Extract database file path from URL
            db_path = DATABASE_URL.replace("sqlite:///", "")
            
            # Create backup
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

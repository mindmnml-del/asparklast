"""
Pytest configuration and fixtures for AISpark Studio tests
"""

import pytest
import asyncio
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from main import app
from core.database import get_db
from core.models import Base
from core import models, auth

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        "test_user": {
            "username": "pytest_user",
            "email": "pytest@example.com",
            "password": "pytest_password_123"
        },
        "test_queries": [
            "photography lighting techniques",
            "video production workflow",
            "camera settings for portraits",
            "creative composition rules"
        ]
    }


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing"""
    return {
        "prompt": "A professional photographer in a modern studio, adjusting lighting equipment",
        "negative_prompt": "blurry, dark, unprofessional",
        "style": "professional",
        "analysis_type": "photo"
    }


def pytest_configure(config):
    """Pytest configuration hook"""
    print("AISpark Studio Test Suite")
    print("=" * 50)
    
    
def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    print("Testing existing functionality preservation...")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    if exitstatus == 0:
        print("All tests passed! Existing functionality preserved.")
    else:
        print("Some tests failed. Check results above.")


# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override for test database
def override_get_db():
    """Dependency override for test database sessions."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Mock vertex_search_service to be enabled and available for tests
from services.vertex_search_service import vertex_search_service
from unittest.mock import MagicMock

vertex_search_service._initialize = lambda: True
vertex_search_service.is_available = lambda: True
vertex_search_service.client = MagicMock()
vertex_search_service.get_status = lambda: {
    "service": "Vertex AI Search",
    "enabled": True,
    "configured": True,
    "initialized": True,
    "available": True,
    "project_id": "test-project",
    "data_store_id": "test-datastore",
    "engine_id": "test-engine",
    "location": "global",
    "serving_config": "default_search",
    "service_account_file": "test-key.json",
    "serving_config_path": "projects/test-project/locations/global/collections/default_collection/dataStores/test-datastore/servingConfigs/default_search"
}


@pytest.fixture(scope="function")
def db_session(request):
    """Fixture that creates and tears down the database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def teardown():
        Base.metadata.drop_all(bind=engine)
        db.close()

    request.addfinalizer(teardown)
    return db


@pytest.fixture(scope="function")
def authenticated_client(db_session):
    """Fixture to provide an authenticated test client."""

    # Create user directly in the test database
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    user = models.User(
        email=user_data["email"],
        hashed_password=auth.get_password_hash(user_data["password"]),
        full_name=user_data["full_name"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create token
    token = auth.create_user_token(user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a new client instance for each test to ensure isolation
    client = TestClient(app)
    client.headers = headers
    yield client
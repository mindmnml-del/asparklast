"""
Pytest configuration and fixtures for AISpark Studio tests
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

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
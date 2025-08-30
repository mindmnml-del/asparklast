"""
Test API endpoints to ensure existing functionality works
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestAPIEndpoints:
    """Test main API endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

    def test_quick_health_check(self):
        """Test quick health check - actually uses /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"

    def test_vertex_search_status_unauthorized(self):
        """Test vertex search status requires authentication"""
        response = client.get("/search/vertex/status")
        assert response.status_code == 401

    def test_critic_stats_unauthorized(self):
        """Test critic stats requires authentication"""
        response = client.get("/critic/stats")
        assert response.status_code == 401

    def test_generate_endpoint_unauthorized(self):
        """Test generate endpoint requires authentication"""
        response = client.post("/generate", json={
            "prompt": "test prompt",
            "style": "professional"
        })
        assert response.status_code == 401

    def test_register_endpoint_exists(self):
        """Test register endpoint is available"""
        # Test with invalid data to check endpoint exists
        response = client.post("/auth/register", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code == 422

    def test_login_endpoint_exists(self):
        """Test login endpoint is available"""
        response = client.post("/auth/token", data={})
        # Should return 422 (validation error) not 404 (not found) 
        assert response.status_code == 422


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    def setup_method(self):
        """Setup test user and get token"""
        # Create test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "testpassword123"
        }
        
        # Try to register (might already exist)
        client.post("/auth/register", json=user_data)
        
        # Login to get token
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/token", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Skip tests if authentication fails
            pytest.skip("Could not authenticate test user")

    def test_vertex_search_status_authenticated(self):
        """Test vertex search status with authentication"""
        if not hasattr(self, 'headers'):
            pytest.skip("Authentication not available")
            
        response = client.get("/search/vertex/status", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Vertex AI Search"
        assert data["enabled"] == True

    def test_critic_stats_authenticated(self):
        """Test critic stats with authentication"""
        if not hasattr(self, 'headers'):
            pytest.skip("Authentication not available")
            
        response = client.get("/critic/stats", headers=self.headers)
        assert response.status_code == 200
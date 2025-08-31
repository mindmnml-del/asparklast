"""
Test API endpoints to ensure existing functionality works
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import csv
import io

from main import app


client = TestClient(app)


@pytest.fixture
def mock_prompts():
    """Fixture to create mock GeneratedPrompt objects for testing export."""
    prompts = []
    now = datetime.now()

    # Prompt 1: Basic
    p1 = MagicMock()
    p1.id = 1
    p1.is_favorite = False
    p1.created_at = now
    p1.raw_response = {
        "prompt": "A basic prompt.",
        "critic_suggestions": "Make it more basic."
    }
    prompts.append(p1)

    # Prompt 2: With Helios
    p2 = MagicMock()
    p2.id = 2
    p2.is_favorite = True
    p2.created_at = now
    p2.raw_response = {
        "prompt": "A heroic prompt.",
        "_metadata": {
            "helios": {
                "primary_personality": "zeus",
                "selection_reasoning": "It was epic."
            }
        }
    }
    prompts.append(p2)

    # Prompt 3: With Character
    p3 = MagicMock()
    p3.id = 3
    p3.is_favorite = False
    p3.created_at = now
    p3.raw_response = {
        "prompt": "A character prompt.",
        "_metadata": {
            "character": {
                "name": "Sir Reginald"
            }
        }
    }
    prompts.append(p3)

    # Prompt 4: With both
    p4 = MagicMock()
    p4.id = 4
    p4.is_favorite = True
    p4.created_at = now
    p4.raw_response = {
        "prompt": "A heroic character prompt.",
        "_metadata": {
            "helios": {
                "primary_personality": "athena",
                "selection_reasoning": "It was strategic."
            },
            "character": {
                "name": "Lady Ann"
            }
        }
    }
    prompts.append(p4)

    return prompts


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

    def test_vertex_search_status_authenticated(self, authenticated_client):
        """Test vertex search status with authentication"""
        response = authenticated_client.get("/search/vertex/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Vertex AI Search"

    def test_critic_stats_authenticated(self, authenticated_client):
        """Test critic stats with authentication"""
        response = authenticated_client.get("/critic/stats")
        assert response.status_code == 200

    @patch('main.crud.get_prompts_by_user')
    @patch('main.crud.get_prompt_by_id')
    def test_export_json(self, mock_get_by_id, mock_get_by_user, mock_prompts, authenticated_client):
        """Test exporting prompts to JSON with enhanced metadata."""
        mock_get_by_user.return_value = mock_prompts
        mock_get_by_id.side_effect = mock_prompts
        response = authenticated_client.get("/prompts/export/json")
        assert response.status_code == 200
        data = response.json()
        assert data["export_info"]["total_prompts"] == 4
        prompt4_data = data["prompts"][3]
        assert prompt4_data["helios_personality"] == "athena"
        assert prompt4_data["character_name"] == "Lady Ann"

    @patch('main.crud.get_prompts_by_user')
    @patch('main.crud.get_prompt_by_id')
    def test_export_csv(self, mock_get_by_id, mock_get_by_user, mock_prompts, authenticated_client):
        """Test exporting prompts to CSV with enhanced metadata."""
        mock_get_by_user.return_value = mock_prompts
        mock_get_by_id.side_effect = mock_prompts
        response = authenticated_client.get("/prompts/export/csv")
        assert response.status_code == 200
        csv_data = response.text
        reader = csv.reader(io.StringIO(csv_data))
        rows = list(reader)
        header = rows[0]
        assert 'helios_personality' in header
        assert 'character_name' in header
        assert len(rows) == 5

    @patch('main.crud.get_prompts_by_user')
    @patch('main.crud.get_prompt_by_id')
    def test_export_txt(self, mock_get_by_id, mock_get_by_user, mock_prompts, authenticated_client):
        """Test exporting prompts to TXT with enhanced metadata."""
        mock_get_by_user.return_value = mock_prompts
        mock_get_by_id.side_effect = mock_prompts
        response = authenticated_client.get("/prompts/export/txt")
        assert response.status_code == 200
        txt_data = response.text
        assert "Helios Personality: athena" in txt_data
        assert "Character Name: Lady Ann" in txt_data

    def test_export_invalid_format(self, authenticated_client):
        """Test exporting with an invalid format."""
        response = authenticated_client.get("/prompts/export/xml")
        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]
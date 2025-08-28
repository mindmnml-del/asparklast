"""
API Client for AISpark Studio Frontend
Handles all backend communication
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class APIClient:
    """Centralized API client for backend communication"""
    
    def __init__(self, base_url: str | None = None):
        # Prefer env var AISPARK_API_URL, default to 8000
        import os as _os
        self.base_url = base_url or _os.getenv("AISPARK_API_URL", "http://localhost:8001")
        self.session = requests.Session()
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        headers: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Default headers
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=default_headers, timeout=timeout)
            elif method.upper() == "POST":
                if endpoint == "/auth/token":
                    # Special case for OAuth2 token endpoint
                    response = self.session.post(url, data=data, timeout=timeout)
                else:
                    response = self.session.post(url, json=data, headers=default_headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=default_headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=default_headers, timeout=timeout)
            else:
                return {"error": True, "message": f"Unsupported HTTP method: {method}"}
            
            # Check response status
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": True, "message": "Invalid JSON response"}
            elif response.status_code == 201:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"success": True, "message": "Created successfully"}
            elif response.status_code == 401:
                return {"error": True, "message": "Authentication failed", "auth_error": True}
            elif response.status_code == 403:
                return {"error": True, "message": "Access forbidden"}
            elif response.status_code == 404:
                return {"error": True, "message": "Resource not found"}
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    return {"error": True, "message": "Validation error", "details": error_data}
                except:
                    return {"error": True, "message": "Validation error"}
            elif response.status_code == 500:
                return {"error": True, "message": "Server error. Please try again later."}
            else:
                return {
                    "error": True, 
                    "message": f"Request failed with status {response.status_code}",
                    "details": response.text[:200]
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "error": True, 
                "message": "Cannot connect to server. Please ensure the backend is running.",
                "connection_error": True
            }
        except requests.exceptions.Timeout:
            return {"error": True, "message": "Request timed out. Please try again."}
        except requests.exceptions.RequestException as e:
            return {"error": True, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            return {"error": True, "message": f"Unexpected error: {str(e)}"}
    
    # Health and Status
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._make_request("GET", "/health", timeout=5)
    
    def detailed_health_check(self) -> Dict[str, Any]:
        """Get detailed health information"""
        return self._make_request("GET", "/health/detailed", timeout=10)
    
    # Authentication
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """User login"""
        data = {"username": email, "password": password}
        return self._make_request("POST", "/auth/token", data=data)
    
    def register(self, email: str, password: str, full_name: str = "") -> Dict[str, Any]:
        """User registration"""
        data = {
            "email": email,
            "password": password,
            "full_name": full_name if full_name else None
        }
        return self._make_request("POST", "/auth/register", data=data)
    
    def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user information"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("GET", "/users/me", headers=headers)
    
    # AI Generation
    def generate_prompt(self, prompt_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Generate AI prompt"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("POST", "/generate", data=prompt_data, headers=headers)
    
    # Prompt Management
    def get_prompts(
        self, 
        token: str, 
        skip: int = 0, 
        limit: int = 20, 
        favorites_only: bool = False
    ) -> Dict[str, Any]:
        """Get user's prompt history"""
        headers = {"Authorization": f"Bearer {token}"}
        params = f"?skip={skip}&limit={limit}"
        if favorites_only:
            params += "&favorites_only=true"
        return self._make_request("GET", f"/prompts{params}", headers=headers)
    
    def get_prompt_by_id(self, prompt_id: int, token: str) -> Dict[str, Any]:
        """Get specific prompt by ID"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("GET", f"/prompts/{prompt_id}", headers=headers)
    
    def toggle_favorite(self, prompt_id: int, is_favorite: bool, token: str) -> Dict[str, Any]:
        """Toggle prompt favorite status"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("PUT", f"/prompts/{prompt_id}/favorite", 
                                 data={"is_favorite": is_favorite}, headers=headers)
    
    def delete_prompt(self, prompt_id: int, token: str) -> Dict[str, Any]:
        """Delete a prompt"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("DELETE", f"/prompts/{prompt_id}", headers=headers)
    
    # Feedback
    def create_feedback(
        self, 
        prompt_id: int, 
        liked: bool, 
        comment: str, 
        token: str
    ) -> Dict[str, Any]:
        """Create feedback for a prompt"""
        headers = {"Authorization": f"Bearer {token}"}
        data = {"liked": liked, "comment": comment if comment else None}
        return self._make_request("POST", f"/prompts/{prompt_id}/feedback", 
                                 data=data, headers=headers)
    
    # Critic Analysis
    def analyze_prompt(
        self, 
        prompt: str, 
        negative_prompt: str = "", 
        analysis_type: str = "photo", 
        token: str = ""
    ) -> Dict[str, Any]:
        """Analyze prompt quality"""
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "analysis_type": analysis_type
        }
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self._make_request("POST", "/critic/analyze", data=data, headers=headers)
    
    # Statistics
    def get_user_stats(self, token: str) -> Dict[str, Any]:
        """Get user statistics"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("GET", "/stats/user", headers=headers)
    
    def get_service_stats(self, token: str) -> Dict[str, Any]:
        """Get service statistics"""
        headers = {"Authorization": f"Bearer {token}"}
        return self._make_request("GET", "/stats/services", headers=headers)
    
    # Search
    def search_prompts(self, query: str, token: str, limit: int = 20) -> Dict[str, Any]:
        """Search user's prompts"""
        headers = {"Authorization": f"Bearer {token}"}
        params = f"?q={query}&limit={limit}"
        return self._make_request("GET", f"/prompts/search{params}", headers=headers)
    
    # Utility methods
    def test_connection(self) -> bool:
        """Test if backend is accessible"""
        try:
            response = self.health_check()
            # Consider connected if we got a JSON dict without an explicit connection error
            if isinstance(response, dict):
                if response.get("error") and response.get("connection_error"):
                    return False
                # If health endpoint returned a status, backend is reachable
                if "status" in response:
                    return True
                # Fallback: no explicit error field -> assume reachable
                return True
            return False
        except:
            return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information"""
        return self._make_request("GET", "/")
    
    def clear_session(self):
        """Clear session data"""
        self.session.close()
        self.session = requests.Session()

# Global API client instance
api_client = APIClient()

# Convenience functions for common operations
def quick_health_check() -> bool:
    """Quick health check - returns True if backend is healthy"""
    try:
        result = api_client.health_check()
        return result.get("status") == "healthy"
    except:
        return False

def validate_token(token: str) -> bool:
    """Validate if token is still valid"""
    try:
        result = api_client.get_current_user(token)
        return not result.get("error", True)
    except:
        return False

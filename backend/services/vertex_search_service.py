"""
Vertex AI Search Service using Google Cloud Discovery Engine
Enterprise search solution with proper authentication and error handling
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

class VertexSearchService:
    """Vertex AI Search service using Google Cloud Discovery Engine"""
    
    def __init__(self):
        self.client = None
        self.serving_config_path = None
        self._initialized = False
        
    def _initialize(self) -> bool:
        """Initialize the Vertex AI Search client"""
        if self._initialized:
            return True
            
        try:
            if not settings.vertex_search_enabled:
                logger.info("Vertex AI Search is disabled in configuration")
                return False
                
            # Check required settings
            if not all([
                settings.vertex_project_id,
                settings.vertex_engine_id or settings.vertex_data_store_id
            ]):
                logger.warning("Vertex AI Search configuration incomplete")
                return False
            
            # Try to use Application Default Credentials first
            # This works if user has done: gcloud auth application-default login
            # If that fails, try service account key file
            service_account_path = Path("streamlit-vertex-key.json")
            if service_account_path.exists():
                # Set credentials environment variable
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(service_account_path.resolve())
                logger.info("Using service account key file for authentication")
            else:
                logger.info("Service account key file not found, trying Application Default Credentials")
            
            # Import and initialize the client with explicit service account
            from google.cloud import discoveryengine_v1 as discoveryengine
            from google.oauth2 import service_account
            
            # Force service account credentials
            service_account_path = Path("streamlit-vertex-key.json")
            if service_account_path.exists():
                credentials = service_account.Credentials.from_service_account_file(
                    str(service_account_path.resolve())
                )
                self.client = discoveryengine.SearchServiceClient(credentials=credentials)
                logger.info(f"Using service account: {credentials.service_account_email}")
            else:
                self.client = discoveryengine.SearchServiceClient()
                logger.info("Using default credentials")
            
            # Build serving config path - use engine_id if available, otherwise data_store_id
            engine_id = settings.vertex_engine_id or settings.vertex_data_store_id
            self.serving_config_path = (
                f"projects/{settings.vertex_project_id}"
                f"/locations/{settings.vertex_location}"
                f"/collections/default_collection"
                f"/engines/{engine_id}"
                f"/servingConfigs/{settings.vertex_serving_config}"
            )
            
            self._initialized = True
            logger.info("Vertex AI Search service initialized successfully")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import Discovery Engine client: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI Search: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Vertex AI Search is available"""
        return self._initialize()
    
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        filter_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform search using Vertex AI Search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            filter_expression: Optional filter expression
            
        Returns:
            Dict containing search results or error
        """
        if not self._initialize():
            return {
                "error": True,
                "message": "Vertex AI Search service not available",
                "results": []
            }
        
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            
            # Create search request with content extraction
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config_path,
                query=query,
                page_size=min(max_results, 50),  # Limit to reasonable size
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    ),
                    extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                        max_extractive_answer_count=1,
                        max_extractive_segment_count=1,
                        return_extractive_segment_score=True
                    )
                )
            )
            
            # Add filter if provided
            if filter_expression:
                request.filter = filter_expression
            
            # Perform search
            response = self.client.search(request=request)
            
            # Process results
            results = []
            for result in response.results:
                doc = result.document
                
                # Extract document information
                doc_data = {
                    "id": doc.id,
                    "score": getattr(result, 'relevance_score', 0.0),
                    "document": {
                        "id": doc.id,
                        "title": "",
                        "snippet": "",
                        "content": "",
                        "uri": getattr(doc, 'uri', '')
                    }
                }
                
                # Try to extract title from URI (filename)
                if doc_data["document"]["uri"]:
                    uri_parts = doc_data["document"]["uri"].split('/')
                    filename = uri_parts[-1] if uri_parts else ""
                    doc_data["document"]["title"] = filename.replace('.txt', '').replace('.gdoc', '').replace('_', ' ')
                
                # Extract structured data
                if hasattr(doc, 'struct_data') and doc.struct_data:
                    struct_data = dict(doc.struct_data)
                    doc_data["document"]["title"] = struct_data.get("title", doc_data["document"]["title"])
                    doc_data["document"]["content"] = struct_data.get("content", "")
                    doc_data["document"]["snippet"] = struct_data.get("snippet", "")
                
                # Extract derived struct data if available  
                if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                    derived_data = dict(doc.derived_struct_data)
                    if not doc_data["document"]["content"]:
                        doc_data["document"]["content"] = derived_data.get("content", "")
                    if not doc_data["document"]["snippet"]:
                        doc_data["document"]["snippet"] = derived_data.get("snippet", "")
                        
                # If still no snippet, create from content
                if doc_data["document"]["content"] and not doc_data["document"]["snippet"]:
                    content = doc_data["document"]["content"]
                    doc_data["document"]["snippet"] = content[:200] + "..." if len(content) > 200 else content
                    
                # Debug logging
                logger.debug(f"Document {doc.id}: title='{doc_data['document']['title']}', content_len={len(doc_data['document']['content'])}, uri='{doc_data['document']['uri']}'")
                
                # Try extractive answers if available
                if hasattr(result, 'document') and hasattr(result.document, 'derived_struct_data'):
                    extractive_answers = result.document.derived_struct_data.get('extractive_answers', [])
                    if extractive_answers:
                        doc_data["document"]["snippet"] = extractive_answers[0].get('content', doc_data["document"]["snippet"])
                
                results.append(doc_data)
            
            return {
                "error": False,
                "query": query,
                "total_results": len(results),
                "results": results,
                "search_type": "Vertex AI Search",
                "serving_config": self.serving_config_path
            }
            
        except Exception as e:
            logger.error(f"Vertex AI Search error: {e}")
            return {
                "error": True,
                "message": f"Search failed: {str(e)}",
                "results": []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "service": "Vertex AI Search",
            "enabled": settings.vertex_search_enabled,
            "configured": bool(
                settings.vertex_project_id and 
                settings.vertex_data_store_id
            ),
            "initialized": self._initialized,
            "available": self.is_available(),
            "project_id": settings.vertex_project_id,
            "data_store_id": settings.vertex_data_store_id,
            "engine_id": getattr(settings, 'vertex_engine_id', ''),
            "location": settings.vertex_location,
            "serving_config": settings.vertex_serving_config,
            "service_account_file": "streamlit-vertex-key.json",
            "serving_config_path": self.serving_config_path if self._initialized else None
        }

# Global service instance
vertex_search_service = VertexSearchService()
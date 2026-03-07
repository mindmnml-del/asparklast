"""
Vertex AI Search Service using Google Cloud Discovery Engine
Enterprise search solution with proper authentication and error handling
"""

import io
import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import docx as python_docx
except ImportError:
    python_docx = None

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
            service_account_path = None
            
            # Check for service account key file from settings
            if settings.google_application_credentials:
                service_account_path = Path(settings.google_application_credentials)
                
            # Fallback to old path
            if not service_account_path or not service_account_path.exists():
                service_account_path = Path("streamlit-vertex-key.json")
                
            # Fallback to different key file
            if not service_account_path.exists():
                service_account_path = Path("prompt-studio-final1-d373010defde.json")
            
            if service_account_path and service_account_path.exists():
                credentials = service_account.Credentials.from_service_account_file(
                    str(service_account_path.resolve())
                )
                self.credentials = credentials
                self.client = discoveryengine.SearchServiceClient(credentials=credentials)
                logger.info(f"Using service account: {credentials.service_account_email}")
            else:
                self.credentials = None
                self.client = discoveryengine.SearchServiceClient()
                logger.info("Using default credentials")
            
            # Build serving config path - try dataStores first, then engines
            if settings.vertex_engine_id:
                # Use engine_id if explicitly set
                self.serving_config_path = (
                    f"projects/{settings.vertex_project_id}"
                    f"/locations/{settings.vertex_location}"
                    f"/collections/default_collection"
                    f"/engines/{settings.vertex_engine_id}"
                    f"/servingConfigs/{settings.vertex_serving_config}"
                )
            else:
                # Use dataStores path with data_store_id
                self.serving_config_path = (
                    f"projects/{settings.vertex_project_id}"
                    f"/locations/{settings.vertex_location}"
                    f"/collections/default_collection"
                    f"/dataStores/{settings.vertex_data_store_id}"
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
            
            # Create minimal search request to avoid WhichOneof error
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config_path,
                query=query,
                page_size=min(max_results, 10)
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
                
                # Extract derived struct data - this is where the actual content is
                if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                    derived_data = dict(doc.derived_struct_data)
                    
                    # Extract title
                    if derived_data.get("title"):
                        doc_data["document"]["title"] = derived_data["title"]
                    
                    # Extract snippets (this contains the actual text content)
                    if derived_data.get("snippets"):
                        snippets = derived_data["snippets"]
                        if snippets:
                            snippet_texts = []
                            for snippet in snippets:
                                # Handle proto.marshal MapComposite objects
                                snippet_dict = dict(snippet) if hasattr(snippet, '__iter__') else {}
                                
                                if snippet_dict.get('snippet'):
                                    snippet_texts.append(snippet_dict['snippet'])
                                elif hasattr(snippet, 'snippet') and snippet.snippet:
                                    snippet_texts.append(snippet.snippet)
                                elif isinstance(snippet, dict) and snippet.get('snippet'):
                                    snippet_texts.append(snippet['snippet'])
                                elif isinstance(snippet, str):
                                    snippet_texts.append(snippet)
                            
                            if snippet_texts:
                                doc_data["document"]["content"] = " ".join(snippet_texts)
                                doc_data["document"]["snippet"] = snippet_texts[0][:500] if snippet_texts[0] else ""
                    
                    # Extract link/URI
                    if derived_data.get("link"):
                        doc_data["document"]["uri"] = derived_data["link"]
                        
                # If still no snippet, create from content
                if doc_data["document"]["content"] and not doc_data["document"]["snippet"]:
                    content = doc_data["document"]["content"]
                    doc_data["document"]["snippet"] = content[:200] + "..." if len(content) > 200 else content
                    
                # Debug logging
                logger.debug(f"Document {doc.id}: title='{doc_data['document']['title']}', content_len={len(doc_data['document']['content'])}, uri='{doc_data['document']['uri']}'")
                
                # Try extractive answers and segments if available
                if hasattr(result, 'document') and hasattr(result.document, 'derived_struct_data'):
                    derived_data = dict(result.document.derived_struct_data)
                    
                    # Get extractive answers
                    extractive_answers = derived_data.get('extractive_answers', [])
                    if extractive_answers:
                        answer_content = extractive_answers[0].get('content', '')
                        if answer_content:
                            doc_data["document"]["snippet"] = answer_content
                    
                    # Get extractive segments for more content
                    extractive_segments = derived_data.get('extractive_segments', [])
                    if extractive_segments:
                        segments = []
                        for segment in extractive_segments[:3]:  # Top 3 segments
                            segment_content = segment.get('content', '')
                            if segment_content:
                                segments.append(segment_content)
                        if segments:
                            doc_data["document"]["content"] = " ".join(segments)
                            if not doc_data["document"]["snippet"]:
                                doc_data["document"]["snippet"] = segments[0][:500]
                
                # Try to fetch full document content if URI is available
                if doc_data["document"]["uri"] and not doc_data["document"]["content"]:
                    full_content = await self._fetch_document_content(doc_data["document"]["uri"])
                    if full_content:
                        doc_data["document"]["content"] = full_content
                        # Update snippet from full content if needed
                        if not doc_data["document"]["snippet"] or len(doc_data["document"]["snippet"]) < 100:
                            doc_data["document"]["snippet"] = full_content[:500] + "..." if len(full_content) > 500 else full_content
                
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
    
    async def _fetch_document_content(self, uri: str) -> Optional[str]:
        """Fetch full document content from Google Cloud Storage or other sources"""
        try:
            # Handle different URI formats
            if uri.startswith('gs://'):
                return await self._fetch_from_gcs(uri)
            elif uri.startswith('https://docs.google.com/'):
                return await self._fetch_from_gdocs(uri)
            elif uri.startswith('http'):
                return await self._fetch_from_url(uri)
            else:
                logger.debug(f"Unsupported URI format: {uri}")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch document content from {uri}: {e}")
            return None
    
    async def _fetch_from_gcs(self, gs_uri: str) -> Optional[str]:
        """Fetch content from Google Cloud Storage"""
        try:
            from google.cloud import storage
            
            # Parse gs://bucket/path format
            if not gs_uri.startswith('gs://'):
                return None
            
            path_parts = gs_uri[5:].split('/', 1)  # Remove 'gs://' prefix
            if len(path_parts) != 2:
                return None
            
            bucket_name, blob_name = path_parts
            
            # Initialize storage client with same credentials
            project_id = settings.vertex_project_id or settings.google_cloud_project
            storage_client = storage.Client(credentials=self.credentials, project=project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Download content — handle .docx binary files vs plain text
            if gs_uri.lower().endswith('.docx') and python_docx is not None:
                try:
                    blob_bytes = blob.download_as_bytes()
                    doc = python_docx.Document(io.BytesIO(blob_bytes))
                    content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                    logger.info(f"Successfully parsed .docx ({len(content)} chars) from {gs_uri}")
                    return content
                except Exception as e:
                    logger.warning(f"Failed to parse .docx {gs_uri}: {e}, falling back to text")
                    return None
            else:
                content = blob.download_as_text(encoding='utf-8')
                logger.info(f"Successfully fetched {len(content)} chars from {gs_uri}")
                return content
            
        except Exception as e:
            logger.error(f"Failed to fetch from GCS {gs_uri}: {e}")
            return None
    
    async def _fetch_from_gdocs(self, gdocs_url: str) -> Optional[str]:
        """Fetch content from Google Docs"""
        try:
            # Extract document ID from Google Docs URL
            import re
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', gdocs_url)
            if not doc_id_match:
                return None
            
            doc_id = doc_id_match.group(1)
            
            # Use Google Docs API to fetch content
            from googleapiclient.discovery import build
            
            service = build('docs', 'v1', credentials=self.credentials)
            document = service.documents().get(documentId=doc_id).execute()
            
            # Extract text content
            content_parts = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for text_run in element['paragraph'].get('elements', []):
                        if 'textRun' in text_run:
                            content_parts.append(text_run['textRun']['content'])
            
            content = ''.join(content_parts)
            logger.info(f"Successfully fetched {len(content)} chars from Google Doc {doc_id}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch from Google Docs {gdocs_url}: {e}")
            return None
    
    async def _fetch_from_url(self, url: str) -> Optional[str]:
        """Fetch content from regular HTTP URL"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully fetched {len(content)} chars from {url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} from {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch from URL {url}: {e}")
            return None
    
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
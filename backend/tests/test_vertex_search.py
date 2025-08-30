"""
Test Vertex AI Search functionality
Ensure existing RAG system remains functional
"""

import pytest
import asyncio
from services.vertex_search_service import vertex_search_service


class TestVertexSearch:
    """Test Vertex AI Search service functionality"""

    def test_service_availability(self):
        """Test that Vertex AI Search service is available"""
        assert vertex_search_service.is_available() == True

    def test_service_configuration(self):
        """Test service configuration"""
        status = vertex_search_service.get_status()
        
        assert status["service"] == "Vertex AI Search"
        assert status["enabled"] == True
        assert status["configured"] == True
        assert status["project_id"] == "881868597890"
        assert status["data_store_id"] == "aispark-knowledge-base_1755346996589"

    @pytest.mark.asyncio
    async def test_search_functionality(self):
        """Test basic search functionality"""
        query = "photography lighting techniques"
        
        result = await vertex_search_service.search(
            query=query,
            max_results=5
        )
        
        # Ensure search works
        assert result["error"] == False
        assert result["query"] == query
        assert result["search_type"] == "Vertex AI Search"
        assert len(result["results"]) > 0
        
        # Check result structure
        first_result = result["results"][0]
        assert "document" in first_result
        assert "id" in first_result["document"]
        assert "score" in first_result

    @pytest.mark.asyncio
    async def test_knowledge_base_documents(self):
        """Test that 34 documents are accessible"""
        queries = [
            "lighting setup",
            "camera settings", 
            "composition rules",
            "video production"
        ]
        
        total_unique_docs = set()
        
        for query in queries:
            result = await vertex_search_service.search(query, max_results=10)
            
            assert result["error"] == False
            assert len(result["results"]) > 0
            
            # Collect document IDs
            for doc in result["results"]:
                total_unique_docs.add(doc["document"]["id"])
        
        # Should have found several different documents
        assert len(total_unique_docs) >= 10
        print(f"Found {len(total_unique_docs)} unique documents in knowledge base")

    def test_error_handling(self):
        """Test error handling for invalid queries"""
        # This should not crash the service
        asyncio.run(self._test_invalid_query())

    async def _test_invalid_query(self):
        """Helper for async error testing"""
        result = await vertex_search_service.search("", max_results=1)
        # Even empty query should return some structure
        assert "error" in result
        assert "results" in result
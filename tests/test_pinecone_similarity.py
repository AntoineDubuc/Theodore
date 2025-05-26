"""
Tests for Pinecone similarity relationship methods
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from src.pinecone_client import PineconeClient
from src.models import CompanySimilarity, CompanyIntelligenceConfig


class TestPineconeSimilarityMethods:
    """Test Pinecone client similarity relationship methods"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        return CompanyIntelligenceConfig()
    
    @pytest.fixture
    def mock_pinecone_index(self):
        """Mock Pinecone index"""
        mock_index = Mock()
        return mock_index
    
    @pytest.fixture 
    def pinecone_client(self, mock_config, mock_pinecone_index):
        """Create Pinecone client with mocked dependencies"""
        with patch('src.pinecone_client.Pinecone') as mock_pc:
            mock_pc.return_value.Index.return_value = mock_pinecone_index
            mock_pc.return_value.list_indexes.return_value = [Mock(name="test-index")]
            
            client = PineconeClient(
                config=mock_config,
                api_key="test-key",
                environment="test-env", 
                index_name="test-index"
            )
            client.index = mock_pinecone_index
            return client
    
    @pytest.fixture
    def sample_similarities(self):
        """Sample similarity relationships"""
        return [
            CompanySimilarity(
                original_company_id="company-a",
                similar_company_id="company-b",
                original_company_name="Company A",
                similar_company_name="Company B",
                similarity_score=0.8,
                confidence=0.9,
                discovery_method="llm_pipeline",
                validation_methods=["structured", "embedding"],
                relationship_type="competitor"
            ),
            CompanySimilarity(
                original_company_id="company-a",
                similar_company_id="company-c", 
                original_company_name="Company A",
                similar_company_name="Company C",
                similarity_score=0.7,
                confidence=0.8,
                discovery_method="llm_pipeline",
                validation_methods=["structured", "llm_judge"],
                relationship_type="adjacent"
            )
        ]
    
    def test_store_similarity_relationships_success(self, pinecone_client, mock_pinecone_index, sample_similarities):
        """Test successful storage of similarity relationships"""
        # Mock fetch responses for existing companies
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={"company_name": "Company A"}),
            "company-b": Mock(metadata={"company_name": "Company B"}),
            "company-c": Mock(metadata={"company_name": "Company C"})
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        # Mock successful updates
        mock_pinecone_index.update.return_value = None
        
        result = pinecone_client.store_similarity_relationships(sample_similarities)
        
        assert result == True
        
        # Should call fetch for each company involved
        expected_fetch_calls = ["company-a", "company-b", "company-c"]
        actual_fetch_calls = [call[1]['ids'][0] for call in mock_pinecone_index.fetch.call_args_list]
        assert set(actual_fetch_calls) == set(expected_fetch_calls)
        
        # Should call update for each relationship (bidirectional)
        assert mock_pinecone_index.update.call_count >= len(sample_similarities)
    
    def test_store_similarity_relationships_company_not_found(self, pinecone_client, mock_pinecone_index, sample_similarities):
        """Test storage when company not found in index"""
        # Mock fetch response with missing company
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {}  # No companies found
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.store_similarity_relationships(sample_similarities)
        
        # Should complete but log warnings about missing companies
        assert result == True
        mock_pinecone_index.update.assert_not_called()
    
    def test_add_similarity_to_company_metadata_new_similarity(self, pinecone_client, mock_pinecone_index):
        """Test adding similarity to company metadata (new similarity)"""
        # Mock company with no existing similarities
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={"company_name": "Company A"})
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        similarity = CompanySimilarity(
            original_company_id="company-a",
            similar_company_id="company-b",
            original_company_name="Company A",
            similar_company_name="Company B",
            similarity_score=0.8,
            confidence=0.9,
            discovery_method="test",
            validation_methods=["structured"],
            relationship_type="competitor"
        )
        
        result = pinecone_client._add_similarity_to_company_metadata("company-a", "company-b", similarity)
        
        assert result == True
        mock_pinecone_index.update.assert_called_once()
        
        # Check that update was called with correct metadata
        update_call = mock_pinecone_index.update.call_args
        updated_metadata = update_call[1]['set_metadata']
        assert "similar_companies" in updated_metadata
        
        # Parse and verify similarity data
        similar_companies = json.loads(updated_metadata["similar_companies"])
        assert len(similar_companies) == 1
        assert similar_companies[0]["company_id"] == "company-b"
        assert similar_companies[0]["similarity_score"] == 0.8
    
    def test_add_similarity_to_company_metadata_existing_similarities(self, pinecone_client, mock_pinecone_index):
        """Test adding similarity when company already has similarities"""
        # Mock company with existing similarities
        existing_similarities = [
            {
                "company_id": "existing-similar",
                "company_name": "Existing Similar",
                "similarity_score": 0.7,
                "confidence": 0.8,
                "discovery_method": "previous",
                "validation_methods": ["embedding"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            }
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(existing_similarities)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        similarity = CompanySimilarity(
            original_company_id="company-a",
            similar_company_id="company-b",
            original_company_name="Company A",
            similar_company_name="Company B",
            similarity_score=0.8,
            confidence=0.9,
            discovery_method="test",
            validation_methods=["structured"],
            relationship_type="competitor"
        )
        
        result = pinecone_client._add_similarity_to_company_metadata("company-a", "company-b", similarity)
        
        assert result == True
        
        # Verify that both old and new similarities are preserved
        update_call = mock_pinecone_index.update.call_args
        updated_metadata = update_call[1]['set_metadata']
        similar_companies = json.loads(updated_metadata["similar_companies"])
        
        assert len(similar_companies) == 2
        company_ids = [sim["company_id"] for sim in similar_companies]
        assert "existing-similar" in company_ids
        assert "company-b" in company_ids
    
    def test_add_similarity_to_company_metadata_duplicate_prevention(self, pinecone_client, mock_pinecone_index):
        """Test that duplicate similarities are not added"""
        # Mock company with existing similarity to same company
        existing_similarities = [
            {
                "company_id": "company-b",
                "company_name": "Company B",
                "similarity_score": 0.7,
                "confidence": 0.8,
                "discovery_method": "previous",
                "validation_methods": ["embedding"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            }
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(existing_similarities)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        similarity = CompanySimilarity(
            original_company_id="company-a",
            similar_company_id="company-b",  # Same as existing
            original_company_name="Company A",
            similar_company_name="Company B",
            similarity_score=0.9,  # Different score
            confidence=0.95,
            discovery_method="test",
            validation_methods=["structured"],
            relationship_type="competitor"
        )
        
        result = pinecone_client._add_similarity_to_company_metadata("company-a", "company-b", similarity)
        
        assert result == True
        
        # Should not add duplicate - no update call made
        mock_pinecone_index.update.assert_not_called()
    
    def test_find_similar_companies_success(self, pinecone_client, mock_pinecone_index):
        """Test successful retrieval of similar companies"""
        # Mock company with similarities
        similarities_data = [
            {
                "company_id": "similar-1",
                "company_name": "Similar Company 1",
                "similarity_score": 0.8,
                "confidence": 0.9,
                "discovery_method": "llm_pipeline",
                "validation_methods": ["structured", "embedding"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            },
            {
                "company_id": "similar-2",
                "company_name": "Similar Company 2", 
                "similarity_score": 0.7,
                "confidence": 0.8,
                "discovery_method": "llm_pipeline",
                "validation_methods": ["embedding"],
                "relationship_type": "adjacent",
                "discovered_at": datetime.now().isoformat()
            }
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(similarities_data)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.find_similar_companies("company-a", limit=10)
        
        assert len(result) == 2
        assert all(isinstance(sim, CompanySimilarity) for sim in result)
        
        # Check first similarity
        sim1 = result[0]
        assert sim1.original_company_id == "company-a"
        assert sim1.similar_company_id == "similar-1"
        assert sim1.similarity_score == 0.8
        assert sim1.confidence == 0.9
        assert sim1.relationship_type == "competitor"
    
    def test_find_similar_companies_with_limit(self, pinecone_client, mock_pinecone_index):
        """Test retrieval of similar companies with limit"""
        # Mock company with many similarities
        similarities_data = [
            {
                "company_id": f"similar-{i}",
                "company_name": f"Similar Company {i}",
                "similarity_score": 0.8 - (i * 0.1),
                "confidence": 0.9,
                "discovery_method": "llm_pipeline",
                "validation_methods": ["structured"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            }
            for i in range(5)  # 5 similarities
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(similarities_data)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.find_similar_companies("company-a", limit=3)
        
        assert len(result) == 3  # Should respect limit
    
    def test_find_similar_companies_company_not_found(self, pinecone_client, mock_pinecone_index):
        """Test retrieval when company not found"""
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {}  # No companies found
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.find_similar_companies("nonexistent-company")
        
        assert result == []
    
    def test_find_similar_companies_no_similarities(self, pinecone_client, mock_pinecone_index):
        """Test retrieval when company has no similarities"""
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A"
                # No similar_companies field
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.find_similar_companies("company-a")
        
        assert result == []
    
    def test_find_similar_companies_malformed_json(self, pinecone_client, mock_pinecone_index):
        """Test retrieval with malformed similarity JSON"""
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": "not valid json"
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        result = pinecone_client.find_similar_companies("company-a")
        
        assert result == []
    
    def test_get_similarity_score_found(self, pinecone_client, mock_pinecone_index):
        """Test getting similarity score between two companies"""
        similarities_data = [
            {
                "company_id": "company-b",
                "company_name": "Company B",
                "similarity_score": 0.8,
                "confidence": 0.9,
                "discovery_method": "llm_pipeline",
                "validation_methods": ["structured"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            }
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(similarities_data)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        score = pinecone_client.get_similarity_score("company-a", "company-b")
        
        assert score == 0.8
    
    def test_get_similarity_score_not_found(self, pinecone_client, mock_pinecone_index):
        """Test getting similarity score when relationship doesn't exist"""
        similarities_data = [
            {
                "company_id": "company-c",  # Different company
                "company_name": "Company C",
                "similarity_score": 0.8,
                "confidence": 0.9,
                "discovery_method": "llm_pipeline",
                "validation_methods": ["structured"],
                "relationship_type": "competitor",
                "discovered_at": datetime.now().isoformat()
            }
        ]
        
        mock_fetch_response = Mock()
        mock_fetch_response.vectors = {
            "company-a": Mock(metadata={
                "company_name": "Company A",
                "similar_companies": json.dumps(similarities_data)
            })
        }
        mock_pinecone_index.fetch.return_value = mock_fetch_response
        
        score = pinecone_client.get_similarity_score("company-a", "company-b")
        
        assert score is None
    
    def test_get_company_by_id_alias(self, pinecone_client):
        """Test that get_company_by_id is an alias for get_full_company_data"""
        with patch.object(pinecone_client, 'get_full_company_data', return_value=Mock()) as mock_get_full:
            result = pinecone_client.get_company_by_id("test-id")
            
            mock_get_full.assert_called_once_with("test-id")
            assert result == mock_get_full.return_value


if __name__ == "__main__":
    pytest.main([__file__])
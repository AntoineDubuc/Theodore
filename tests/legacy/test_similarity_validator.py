"""
Tests for SimilarityValidator
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.similarity_validator import SimilarityValidator, SimilarityScore, SimilarityResult
from src.models import CompanyData


class TestSimilarityValidator:
    """Test the SimilarityValidator class"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client for testing"""
        mock_client = Mock()
        mock_client.get_embeddings.return_value = [0.1] * 1536  # Mock embedding vector
        return mock_client
    
    @pytest.fixture
    def similarity_validator(self, mock_bedrock_client):
        """Create similarity validator with mocked dependencies"""
        return SimilarityValidator(mock_bedrock_client)
    
    @pytest.fixture
    def company_a(self):
        """Sample company A for testing"""
        return CompanyData(
            name="Acme Corp",
            website="https://acme.com",
            industry="Software",
            business_model="B2B SaaS",
            company_description="Enterprise CRM solutions",
            key_services=["CRM", "Analytics"],
            target_market="Enterprise",
            location="San Francisco",
            tech_stack=["React", "Python", "AWS"],
            company_size="startup"
        )
    
    @pytest.fixture
    def company_b_similar(self):
        """Sample company B that's similar to A"""
        return CompanyData(
            name="SalesForce Inc",
            website="https://salesforce.com",
            industry="Software", 
            business_model="B2B SaaS",
            company_description="Customer relationship management platform",
            key_services=["CRM", "Marketing Automation"],
            target_market="Enterprise",
            location="San Francisco",
            tech_stack=["React", "Java", "AWS"],
            company_size="startup"
        )
    
    @pytest.fixture
    def company_c_different(self):
        """Sample company C that's different from A"""
        return CompanyData(
            name="Local Bakery",
            website="https://bakery.com",
            industry="Food Service",
            business_model="B2C",
            company_description="Fresh baked goods daily",
            key_services=["Baking", "Catering"],
            target_market="Local consumers",
            location="Portland",
            tech_stack=["WordPress"],
            company_size="SMB"
        )
    
    def test_validate_similarity_high_similarity(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test validation of highly similar companies"""
        # Mock LLM judge response
        mock_bedrock_client.analyze_content.return_value = '''
        SCORE: 8/10
        REASONING: Both are B2B SaaS companies providing CRM solutions to enterprise customers
        SIMILAR: YES
        '''
        
        # Mock high embedding similarity
        mock_bedrock_client.get_embeddings.side_effect = [
            [0.8] * 1536,  # Company A embedding
            [0.9] * 1536   # Company B embedding (very similar)
        ]
        
        result = similarity_validator.validate_similarity(company_a, company_b_similar)
        
        assert isinstance(result, SimilarityResult)
        assert result.is_similar == True
        assert result.confidence > 0.5
        assert len(result.method_scores) >= 2  # At least structured + embedding
        assert "structured" in result.methods_used
        assert "embedding" in result.methods_used
    
    def test_validate_similarity_low_similarity(self, similarity_validator, company_a, company_c_different, mock_bedrock_client):
        """Test validation of dissimilar companies"""
        # Mock LLM judge response indicating low similarity
        mock_bedrock_client.analyze_content.return_value = '''
        SCORE: 2/10
        REASONING: Completely different industries - software vs food service
        SIMILAR: NO
        '''
        
        # Mock low embedding similarity
        mock_bedrock_client.get_embeddings.side_effect = [
            [0.8] * 1536,  # Company A embedding
            [-0.5] * 1536  # Company C embedding (very different)
        ]
        
        result = similarity_validator.validate_similarity(company_a, company_c_different)
        
        assert isinstance(result, SimilarityResult)
        assert result.is_similar == False
        assert len(result.votes) == 0  # No methods should vote similar
    
    def test_structured_comparison_exact_matches(self, similarity_validator, company_a, company_b_similar):
        """Test structured comparison with exact field matches"""
        score = similarity_validator._structured_comparison(company_a, company_b_similar)
        
        assert isinstance(score, SimilarityScore)
        assert score.method == "structured"
        assert score.score > 0.5  # Should have decent similarity
        assert score.is_similar  # Should pass threshold
        
        # Check that industry and business model matches contributed
        assert "industry_exact_match" in score.details
        assert "business_model_match" in score.details
    
    def test_structured_comparison_missing_fields(self, similarity_validator):
        """Test structured comparison with missing fields"""
        company_minimal_a = CompanyData(name="Test A", website="https://a.com")
        company_minimal_b = CompanyData(name="Test B", website="https://b.com")
        
        score = similarity_validator._structured_comparison(company_minimal_a, company_minimal_b)
        
        assert isinstance(score, SimilarityScore)
        assert score.score == 0.0  # No fields to compare
    
    def test_tech_stack_normalization(self, similarity_validator):
        """Test technology stack normalization"""
        tech_list = ["React.js", "Node.js", "ReactJS", "Python", "AWS", "py", "Google Cloud"]
        
        normalized = similarity_validator._normalize_tech_stack(tech_list)
        
        # Should normalize variations
        assert "react" in normalized  # React.js -> react
        assert "nodejs" in normalized  # Node.js -> nodejs
        assert "python" in normalized  # Both Python and py -> python
        assert "aws" in normalized
        assert "gcp" in normalized  # Google Cloud -> gcp
        
        # Should not have duplicates
        assert len([tech for tech in normalized if "react" in tech]) == 1
    
    def test_safe_field_comparison(self, similarity_validator):
        """Test safe field comparison with various inputs"""
        # Exact match
        result = similarity_validator._safe_field_comparison("Software", "Software", 0.5)
        assert result['score'] == 0.5
        assert len(result['details']) > 0
        
        # Partial match
        result = similarity_validator._safe_field_comparison(
            "Software Development", 
            "Software Testing", 
            0.5, 
            partial_weight=0.2
        )
        assert result['score'] == 0.2  # Partial match
        
        # No match
        result = similarity_validator._safe_field_comparison("Software", "Hardware", 0.5)
        assert result['score'] == 0.0
        
        # Missing fields
        result = similarity_validator._safe_field_comparison(None, "Software", 0.5)
        assert result['score'] == 0.0
        
        result = similarity_validator._safe_field_comparison("Software", "", 0.5)
        assert result['score'] == 0.0
    
    def test_embedding_similarity_calculation(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test embedding similarity calculation"""
        # Mock embeddings with known similarity
        embedding_a = [1.0, 0.0, 0.0]  # Simple 3D vector
        embedding_b = [0.8, 0.6, 0.0]  # Similar direction
        
        mock_bedrock_client.get_embeddings.side_effect = [embedding_a, embedding_b]
        
        score = similarity_validator._embedding_similarity(company_a, company_b_similar)
        
        assert isinstance(score, SimilarityScore)
        assert score.method == "embedding"
        assert 0 <= score.score <= 1  # Cosine similarity range
        assert "cosine_similarity" in score.details
    
    def test_embedding_caching(self, similarity_validator, mock_bedrock_client):
        """Test that embeddings are cached properly"""
        test_text = "Test company description"
        
        # First call
        embedding1 = similarity_validator._get_cached_embedding(test_text)
        
        # Second call with same text
        embedding2 = similarity_validator._get_cached_embedding(test_text)
        
        # Should return same result and only call bedrock once
        np.testing.assert_array_equal(embedding1, embedding2)
        assert mock_bedrock_client.get_embeddings.call_count == 1
    
    def test_llm_judge_similarity_parsing(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test LLM judge response parsing"""
        # Test various response formats
        test_cases = [
            {
                "response": "SCORE: 8/10\nREASONING: Both are CRM companies\nSIMILAR: YES",
                "expected_score": 8.0,
                "expected_similar": True
            },
            {
                "response": "SCORE: 3/10\nREASONING: Different industries\nSIMILAR: NO", 
                "expected_score": 3.0,
                "expected_similar": False
            },
            {
                "response": "SCORE: 7/10\nREASONING: Similar but different scale\nSIMILAR: YES",
                "expected_score": 7.0,
                "expected_similar": True
            }
        ]
        
        for test_case in test_cases:
            mock_bedrock_client.analyze_content.return_value = test_case["response"]
            
            score = similarity_validator._llm_judge_similarity(company_a, company_b_similar)
            
            assert score.method == "llm_judge"
            assert score.score == test_case["expected_score"]
            assert score.is_similar == test_case["expected_similar"]
            assert "reasoning" in score.details
    
    def test_llm_judge_malformed_response(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test LLM judge with malformed response"""
        mock_bedrock_client.analyze_content.return_value = "This is not a properly formatted response"
        
        score = similarity_validator._llm_judge_similarity(company_a, company_b_similar)
        
        assert score.method == "llm_judge"
        assert score.score == 0.0
        assert score.is_similar == False
        assert "error" in score.details
    
    def test_composite_score_calculation(self, similarity_validator):
        """Test weighted composite score calculation"""
        method_scores = [
            SimilarityScore(method="structured", score=0.8, is_similar=True, details={}),
            SimilarityScore(method="embedding", score=0.6, is_similar=True, details={}),
            SimilarityScore(method="llm_judge", score=9.0, is_similar=True, details={})
        ]
        
        composite_score = similarity_validator._calculate_composite_score(method_scores)
        
        # Should be weighted average based on configured weights
        expected = (0.8 * 0.4) + (0.6 * 0.4) + (9.0 * 0.2)  # weights from class
        assert abs(composite_score - expected) < 0.001
    
    def test_create_company_text_representation(self, similarity_validator, company_a):
        """Test company text representation creation"""
        text_repr = similarity_validator._create_company_text_representation(company_a)
        
        # Should include all key company information
        assert "Acme Corp" in text_repr
        assert "Software" in text_repr
        assert "B2B SaaS" in text_repr
        assert "CRM" in text_repr
        assert "San Francisco" in text_repr
        assert "React" in text_repr
    
    def test_voting_system_require_two_votes(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test that voting system requires minimum votes"""
        # Mock only embedding similarity to be high (1 vote)
        mock_bedrock_client.get_embeddings.side_effect = [
            [0.9] * 1536,  # High similarity embeddings
            [0.95] * 1536
        ]
        
        # Mock LLM judge to fail
        mock_bedrock_client.analyze_content.side_effect = Exception("LLM failed")
        
        result = similarity_validator.validate_similarity(
            company_a, 
            company_b_similar, 
            use_llm=True,
            require_votes=2
        )
        
        # Should not be similar with only 1 vote when 2 required
        assert result.is_similar == False
    
    def test_bedrock_client_error_handling(self, similarity_validator, company_a, company_b_similar, mock_bedrock_client):
        """Test error handling when Bedrock client fails"""
        mock_bedrock_client.get_embeddings.side_effect = Exception("Bedrock API error")
        mock_bedrock_client.analyze_content.side_effect = Exception("Bedrock API error")
        
        result = similarity_validator.validate_similarity(company_a, company_b_similar)
        
        # Should handle errors gracefully
        assert isinstance(result, SimilarityResult)
        assert result.is_similar == False
        # Should still have structured comparison if it doesn't require bedrock
        assert len(result.method_scores) >= 1


if __name__ == "__main__":
    pytest.main([__file__])
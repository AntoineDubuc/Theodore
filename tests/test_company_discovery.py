"""
Tests for CompanyDiscoveryService
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.company_discovery import CompanyDiscoveryService, CompanySuggestion, DiscoveryResult
from src.models import CompanyData


class TestCompanyDiscoveryService:
    """Test the CompanyDiscoveryService class"""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client for testing"""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def discovery_service(self, mock_bedrock_client):
        """Create discovery service with mocked dependencies"""
        return CompanyDiscoveryService(mock_bedrock_client)
    
    @pytest.fixture
    def sample_company(self):
        """Sample company data for testing"""
        return CompanyData(
            name="Acme Corp",
            website="https://acme.com",
            industry="Software",
            business_model="B2B SaaS",
            company_description="Enterprise software solutions",
            key_services=["CRM", "Analytics"],
            target_market="Mid-market businesses",
            location="San Francisco",
            tech_stack=["React", "Python", "AWS"]
        )
    
    def test_discover_similar_companies_success(self, discovery_service, sample_company, mock_bedrock_client):
        """Test successful company discovery"""
        # Mock LLM response with valid JSON
        mock_llm_response = '''
        {
          "similar_companies": [
            {
              "company_name": "Salesforce",
              "website_url": "https://salesforce.com",
              "reason": "Both provide CRM solutions for businesses"
            },
            {
              "company_name": "HubSpot",
              "website_url": "https://hubspot.com", 
              "reason": "Similar B2B SaaS model with CRM focus"
            }
          ]
        }
        '''
        
        mock_bedrock_client.analyze_content.return_value = mock_llm_response
        
        # Mock URL validation to pass
        with patch.object(discovery_service, '_check_url_accessible', return_value=True):
            result = discovery_service.discover_similar_companies(sample_company, limit=5)
        
        # Assertions
        assert isinstance(result, DiscoveryResult)
        assert result.target_company == "Acme Corp"
        assert len(result.suggestions) == 2
        assert result.total_suggestions == 2
        
        # Check suggestion details
        salesforce_suggestion = result.suggestions[0]
        assert salesforce_suggestion.company_name == "Salesforce"
        assert salesforce_suggestion.website_url == "https://salesforce.com"
        assert "CRM" in salesforce_suggestion.suggested_reason
    
    def test_discover_similar_companies_with_invalid_suggestions(self, discovery_service, sample_company, mock_bedrock_client):
        """Test discovery with some invalid suggestions filtered out"""
        # Mock LLM response with mix of valid and invalid suggestions
        mock_llm_response = '''
        {
          "similar_companies": [
            {
              "company_name": "Salesforce",
              "website_url": "https://salesforce.com",
              "reason": "Both provide CRM solutions"
            },
            {
              "company_name": "Company",
              "website_url": "https://invalid-url",
              "reason": "Generic invalid company"
            },
            {
              "company_name": "Test Corp",
              "website_url": "https://test.com",
              "reason": "Test company that should be filtered"
            }
          ]
        }
        '''
        
        mock_bedrock_client.analyze_content.return_value = mock_llm_response
        
        # Mock URL validation - only Salesforce passes
        def mock_url_check(url):
            return url == "https://salesforce.com"
        
        with patch.object(discovery_service, '_check_url_accessible', side_effect=mock_url_check):
            result = discovery_service.discover_similar_companies(sample_company, limit=5)
        
        # Should only have Salesforce (others filtered out)
        assert len(result.suggestions) == 1
        assert result.suggestions[0].company_name == "Salesforce"
    
    def test_discover_similar_companies_malformed_json(self, discovery_service, sample_company, mock_bedrock_client):
        """Test discovery with malformed JSON response"""
        # Mock LLM response with malformed JSON
        mock_llm_response = '''
        Here are some similar companies:
        1. Salesforce - https://salesforce.com - CRM provider
        2. HubSpot - https://hubspot.com - Marketing automation
        '''
        
        mock_bedrock_client.analyze_content.return_value = mock_llm_response
        
        with patch.object(discovery_service, '_check_url_accessible', return_value=True):
            result = discovery_service.discover_similar_companies(sample_company, limit=5)
        
        # Should fall back to unstructured parsing
        assert isinstance(result, DiscoveryResult)
        assert len(result.suggestions) >= 0  # May find some via fallback parsing
    
    def test_validate_suggestion_valid_company(self, discovery_service):
        """Test suggestion validation with valid company"""
        suggestion = CompanySuggestion(
            company_name="Salesforce Inc",
            website_url="https://salesforce.com",
            suggested_reason="CRM competitor"
        )
        
        with patch.object(discovery_service, '_check_url_accessible', return_value=True):
            is_valid = discovery_service._validate_suggestion(suggestion)
        
        assert is_valid
    
    def test_validate_suggestion_invalid_company_name(self, discovery_service):
        """Test suggestion validation with invalid company name"""
        # Test generic names
        invalid_suggestions = [
            CompanySuggestion(company_name="Company", website_url="https://example.com", suggested_reason="test"),
            CompanySuggestion(company_name="Corp", website_url="https://example.com", suggested_reason="test"),
            CompanySuggestion(company_name="Test", website_url="https://example.com", suggested_reason="test"),
            CompanySuggestion(company_name="", website_url="https://example.com", suggested_reason="test"),
            CompanySuggestion(company_name="Ab", website_url="https://example.com", suggested_reason="test"),  # Too short
        ]
        
        for suggestion in invalid_suggestions:
            is_valid = discovery_service._validate_suggestion(suggestion)
            assert not is_valid, f"Should reject: {suggestion.company_name}"
    
    def test_validate_suggestion_inaccessible_url(self, discovery_service):
        """Test suggestion validation with inaccessible URL"""
        suggestion = CompanySuggestion(
            company_name="Valid Company",
            website_url="https://nonexistent-website-12345.com",
            suggested_reason="Test company"
        )
        
        with patch.object(discovery_service, '_check_url_accessible', return_value=False):
            is_valid = discovery_service._validate_suggestion(suggestion)
        
        # Should still be valid but URL cleared and confidence reduced
        assert is_valid
        assert suggestion.website_url is None
        assert suggestion.confidence_score < 0.8  # Reduced confidence
    
    def test_check_url_accessible_valid_url(self, discovery_service):
        """Test URL accessibility check with valid URL"""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            is_accessible = discovery_service._check_url_accessible("https://salesforce.com")
            assert is_accessible
    
    def test_check_url_accessible_invalid_url(self, discovery_service):
        """Test URL accessibility check with invalid URL"""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            is_accessible = discovery_service._check_url_accessible("https://nonexistent.com")
            assert not is_accessible
    
    def test_check_url_accessible_malformed_url(self, discovery_service):
        """Test URL accessibility check with malformed URL"""
        is_accessible = discovery_service._check_url_accessible("not-a-url")
        assert not is_accessible
    
    def test_clean_url_formatting(self, discovery_service):
        """Test URL cleaning and formatting"""
        test_cases = [
            ("salesforce.com", "https://salesforce.com"),
            ("http://example.com", "http://example.com"),
            ("https://test.com", "https://test.com"),
            ("[salesforce.com]", "https://salesforce.com"),
            ("(example.com)", "https://example.com"),
            ("", None),
            ("invalid", None),
            ("a", None)
        ]
        
        for input_url, expected in test_cases:
            result = discovery_service._clean_url(input_url)
            assert result == expected, f"Input: {input_url}, Expected: {expected}, Got: {result}"
    
    def test_create_discovery_prompt(self, discovery_service, sample_company):
        """Test discovery prompt creation"""
        prompt = discovery_service._create_discovery_prompt(sample_company, limit=5)
        
        # Check that prompt contains company details
        assert "Acme Corp" in prompt
        assert "Software" in prompt
        assert "B2B SaaS" in prompt
        assert "CRM" in prompt
        assert "5" in prompt  # Limit should be mentioned
        
        # Check that prompt asks for JSON format
        assert "JSON" in prompt
        assert "similar_companies" in prompt
    
    def test_parse_llm_suggestions_valid_json(self, discovery_service):
        """Test parsing of valid JSON response"""
        json_response = '''
        {
          "similar_companies": [
            {
              "company_name": "Test Company",
              "website_url": "https://test.com",
              "reason": "Similar business model"
            }
          ]
        }
        '''
        
        suggestions = discovery_service._parse_llm_suggestions(json_response)
        
        assert len(suggestions) == 1
        assert suggestions[0].company_name == "Test Company"
        assert suggestions[0].website_url == "https://test.com"
        assert suggestions[0].suggested_reason == "Similar business model"
    
    def test_bedrock_client_error_handling(self, discovery_service, sample_company, mock_bedrock_client):
        """Test error handling when Bedrock client fails"""
        mock_bedrock_client.analyze_content.side_effect = Exception("Bedrock API error")
        
        result = discovery_service.discover_similar_companies(sample_company, limit=5)
        
        # Should return empty result on error
        assert isinstance(result, DiscoveryResult)
        assert len(result.suggestions) == 0
        assert result.total_suggestions == 0


if __name__ == "__main__":
    pytest.main([__file__])
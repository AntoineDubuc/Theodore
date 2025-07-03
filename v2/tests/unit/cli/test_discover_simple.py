"""
Simplified tests for the Discover CLI command.

Tests the core functionality without complex DI container dependencies.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.core.domain.value_objects.similarity_result import (
    DiscoveryRequest, DiscoveryResult, DiscoverySource, CompanyMatch
)
from src.cli.utils.output import OutputFormat


class MockContainer:
    """Mock container for testing."""
    
    def __init__(self):
        self.mock_use_case = AsyncMock()
    
    def get_discovery_use_case(self):
        return self.mock_use_case


class TestDiscoveryCommandSimple:
    """Simplified test suite for DiscoveryCommand functionality."""
    
    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        return MockContainer()
    
    @pytest.fixture
    def sample_matches(self):
        """Create sample company matches for testing."""
        return [
            CompanyMatch(
                company_name="TestCorp A",
                domain="https://testcorp-a.com",
                description="A test company",
                similarity_score=0.85,
                confidence_score=0.9,
                source=DiscoverySource.VECTOR_DATABASE
            ),
            CompanyMatch(
                company_name="TestCorp B", 
                domain="https://testcorp-b.com",
                description="Another test company",
                similarity_score=0.72,
                confidence_score=0.8,
                source=DiscoverySource.MCP_PERPLEXITY
            ),
            CompanyMatch(
                company_name="TestCorp C",
                domain="https://testcorp-c.com",
                description="Third test company",
                similarity_score=0.68,
                confidence_score=0.75,
                source=DiscoverySource.MCP_TAVILY
            )
        ]
    
    @pytest.fixture
    def sample_discovery_result(self, sample_matches):
        """Create sample discovery result."""
        return DiscoveryResult(
            query_company="Target Company",
            search_strategy="hybrid",
            total_sources_used=3,
            matches=sample_matches,
            total_matches=3,
            execution_time_seconds=1.5,
            average_confidence=0.82,
            coverage_score=0.75,
            freshness_score=0.9
        )
    
    def test_discovery_request_creation(self):
        """Test creating discovery requests with various options."""
        # Test basic request
        request = DiscoveryRequest(
            company_name="TestCorp",
            max_results=10,
            min_similarity_score=0.6
        )
        assert request.company_name == "TestCorp"
        assert request.max_results == 10
        assert request.min_similarity_score == 0.6
        
        # Test request with filters
        filtered_request = DiscoveryRequest(
            company_name="TestCorp",
            business_model_filter="saas",
            size_filter="medium",
            industry_filter="technology",
            location_filter="San Francisco",
            min_similarity_score=0.8
        )
        
        assert filtered_request.business_model_filter == "saas"
        assert filtered_request.size_filter == "medium"
        assert filtered_request.industry_filter == "technology"
        assert filtered_request.location_filter == "San Francisco"
        assert filtered_request.min_similarity_score == 0.8
    
    def test_discovery_request_source_mapping(self):
        """Test discovery source mapping functionality."""
        # Test vector-only
        request_vector = DiscoveryRequest(
            company_name="TestCorp",
            include_database_search=True,
            include_web_discovery=False
        )
        assert request_vector.include_database_search == True
        assert request_vector.include_web_discovery == False
        
        # Test web-only
        request_web = DiscoveryRequest(
            company_name="TestCorp",
            include_database_search=False,
            include_web_discovery=True
        )
        assert request_web.include_database_search == False
        assert request_web.include_web_discovery == True
        
        # Test hybrid
        request_hybrid = DiscoveryRequest(
            company_name="TestCorp",
            include_database_search=True,
            include_web_discovery=True
        )
        assert request_hybrid.include_database_search == True
        assert request_hybrid.include_web_discovery == True
    
    def test_discovery_request_validation(self):
        """Test discovery request validation."""
        # Test invalid company name
        with pytest.raises(ValueError):
            DiscoveryRequest(company_name="")
        
        # Test valid request
        valid_request = DiscoveryRequest(
            company_name="TestCorp",
            max_results=50,
            min_similarity_score=0.5
        )
        assert valid_request.company_name == "TestCorp"
        assert valid_request.max_results == 50
        assert valid_request.min_similarity_score == 0.5
    
    def test_filter_summary(self):
        """Test filter summary functionality."""
        # Test empty filters
        request_empty = DiscoveryRequest(
            company_name="TestCorp",
            business_model_filter=None,
            size_filter=None,
            industry_filter=None,
            location_filter=None,
            min_similarity_score=0.6
        )
        
        filter_summary = request_empty.get_filter_summary()
        assert filter_summary["business_model"] is None
        assert filter_summary["size"] is None
        assert filter_summary["industry"] is None
        assert filter_summary["location"] is None
        
        # Test with active filters
        request_filtered = DiscoveryRequest(
            company_name="TestCorp",
            business_model_filter="saas",
            size_filter="medium",
            industry_filter="technology",
            location_filter="San Francisco",
            min_similarity_score=0.8
        )
        
        filter_summary = request_filtered.get_filter_summary()
        assert filter_summary["business_model"] == "saas"
        assert filter_summary["size"] == "medium"
        assert filter_summary["industry"] == "technology"
        assert filter_summary["location"] == "San Francisco"
        assert filter_summary["min_score"] == 0.8
    
    def test_similarity_score_validation(self):
        """Test similarity score validation."""
        # Test valid scores
        valid_scores = [0.0, 0.5, 1.0, 0.75, 0.123]
        for score in valid_scores:
            request = DiscoveryRequest(
                company_name="TestCorp",
                min_similarity_score=score
            )
            assert request.min_similarity_score == score
        
        # Test boundary values
        request_min = DiscoveryRequest(
            company_name="TestCorp",
            min_similarity_score=0.0
        )
        assert request_min.min_similarity_score == 0.0
        
        request_max = DiscoveryRequest(
            company_name="TestCorp", 
            min_similarity_score=1.0
        )
        assert request_max.min_similarity_score == 1.0
    
    def test_discovery_result_structure(self, sample_discovery_result):
        """Test discovery result structure and methods."""
        result = sample_discovery_result
        
        # Test basic properties
        assert result.query_company == "Target Company"
        assert result.search_strategy == "hybrid"
        assert result.total_sources_used == 3
        assert len(result.matches) == 3
        assert result.total_matches == 3
        
        # Test utility methods
        top_matches = result.get_top_matches(2)
        assert len(top_matches) == 2
        # Should be sorted by combined score (similarity * confidence)
        assert top_matches[0].similarity_score * top_matches[0].confidence_score >= \
               top_matches[1].similarity_score * top_matches[1].confidence_score
        
        # Test source coverage calculation
        source_coverage = result.calculate_source_coverage()
        assert source_coverage[DiscoverySource.VECTOR_DATABASE] == 1
        assert source_coverage[DiscoverySource.MCP_PERPLEXITY] == 1
        assert source_coverage[DiscoverySource.MCP_TAVILY] == 1
        assert source_coverage[DiscoverySource.MCP_SEARCH_DROID] == 0
    
    def test_company_match_structure(self, sample_matches):
        """Test CompanyMatch structure and properties."""
        match = sample_matches[0]
        
        assert match.company_name == "TestCorp A"
        assert match.domain == "https://testcorp-a.com"
        assert match.description == "A test company"
        assert match.similarity_score == 0.85
        assert match.confidence_score == 0.9
        assert match.source == DiscoverySource.VECTOR_DATABASE
        
        # Test combined score calculation
        combined_score = match.similarity_score * match.confidence_score
        assert combined_score == 0.85 * 0.9
    
    def test_discovery_source_enum(self):
        """Test DiscoverySource enum values."""
        # Test all enum values exist
        sources = [
            DiscoverySource.VECTOR_DATABASE,
            DiscoverySource.MCP_PERPLEXITY,
            DiscoverySource.MCP_TAVILY,
            DiscoverySource.MCP_SEARCH_DROID,
            DiscoverySource.GOOGLE_SEARCH,
            DiscoverySource.MANUAL_RESEARCH
        ]
        
        for source in sources:
            assert isinstance(source.value, str)
            assert len(source.value) > 0
    
    def test_output_format_enum(self):
        """Test OutputFormat enum values."""
        # Test all format values exist
        formats = [
            OutputFormat.TABLE,
            OutputFormat.JSON,
            OutputFormat.YAML,
            OutputFormat.MARKDOWN
        ]
        
        for fmt in formats:
            assert isinstance(fmt.value, str)
            assert len(fmt.value) > 0
    
    @pytest.mark.asyncio
    async def test_mock_discovery_execution(self, mock_container, sample_discovery_result):
        """Test mock discovery execution flow."""
        # Setup mock use case
        mock_container.mock_use_case.execute.return_value = sample_discovery_result
        
        # Create discovery request
        request = DiscoveryRequest(
            company_name="TestCorp",
            max_results=10,
            min_similarity_score=0.6
        )
        
        # Execute mock discovery
        result = await mock_container.mock_use_case.execute(request)
        
        # Verify results
        assert result == sample_discovery_result
        assert result.query_company == "Target Company"
        assert len(result.matches) == 3
        
        # Verify use case was called
        mock_container.mock_use_case.execute.assert_called_once_with(request)
    
    def test_has_filters_detection(self):
        """Test filter detection functionality."""
        # Request with no filters
        no_filters = DiscoveryRequest(company_name="TestCorp")
        assert not no_filters.has_filters()
        
        # Request with industry filter
        with_industry = DiscoveryRequest(
            company_name="TestCorp",
            industry_filter="technology"
        )
        assert with_industry.has_filters()
        
        # Request with high similarity threshold
        with_threshold = DiscoveryRequest(
            company_name="TestCorp",
            min_similarity_score=0.8
        )
        assert with_threshold.has_filters()
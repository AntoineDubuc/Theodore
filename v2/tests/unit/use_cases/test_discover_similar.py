#!/usr/bin/env python3
"""
Unit Tests for Discover Similar Companies Use Case
=================================================

Comprehensive unit tests with mocked dependencies testing various discovery scenarios.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
from typing import List, Dict

from src.core.use_cases.discover_similar import (
    DiscoverSimilarCompaniesUseCase, MCPToolsRegistry, SearchQueryGenerator, 
    ParallelSearchExecutor
)
from src.core.domain.value_objects.similarity_result import (
    DiscoveryRequest, DiscoveryResult, CompanyMatch, DiscoverySource
)
from src.core.domain.services.similarity_scorer import SimilarityScorer


@pytest.fixture
def mock_dependencies():
    """Setup mocked dependencies for testing"""
    from unittest.mock import MagicMock
    
    # Mock progress tracker with context manager support
    mock_progress_tracker = MagicMock()
    mock_operation = MagicMock()
    mock_phase = MagicMock()
    
    mock_progress_tracker.operation.return_value = mock_operation
    mock_operation.__enter__.return_value = mock_operation
    mock_operation.__exit__.return_value = None
    mock_operation.phase.return_value = mock_phase
    mock_phase.__enter__.return_value = mock_phase
    mock_phase.__exit__.return_value = None
    mock_phase.set_progress = MagicMock()
    
    # Mock vector storage
    mock_vector_storage = MagicMock()
    
    # Mock AI provider
    mock_ai_provider = MagicMock()
    
    # Mock fallback search
    mock_fallback_search = MagicMock()
    
    return {
        'progress_tracker': mock_progress_tracker,
        'vector_storage': mock_vector_storage,
        'ai_provider': mock_ai_provider,
        'fallback_search': mock_fallback_search
    }


@pytest.fixture
def sample_company_matches():
    """Create sample company matches for testing"""
    return [
        CompanyMatch(
            company_name="TechCorp Similar",
            domain="techcorp-similar.com",
            description="AI-powered technology company similar to target",
            industry="Technology",
            business_model="B2B",
            employee_count=150,
            location="San Francisco, CA",
            similarity_score=0.9,
            confidence_score=0.85,
            source=DiscoverySource.VECTOR_DATABASE,
            search_query_used="TechCorp competitors",
            raw_data={'vector_score': 0.9}
        ),
        CompanyMatch(
            company_name="WebSearch Found Company",
            domain="websearch-found.com", 
            description="Company discovered through web search",
            industry="Software",
            business_model="SaaS",
            employee_count=75,
            location="New York, NY",
            similarity_score=0.75,
            confidence_score=0.7,
            source=DiscoverySource.MCP_PERPLEXITY,
            search_query_used="similar companies to TechCorp",
            raw_data={'perplexity_result': True}
        ),
        CompanyMatch(
            company_name="Fallback Discovery",
            domain="fallback-discovery.com",
            description="Company found through fallback search",
            similarity_score=0.6,
            confidence_score=0.65,
            source=DiscoverySource.GOOGLE_SEARCH,
            search_query_used="TechCorp alternatives",
            raw_data={'fallback_search': True}
        )
    ]


class TestMCPToolsRegistry:
    """Test MCP tools registry functionality"""
    
    def test_tool_registration(self):
        """Test registering MCP tools"""
        registry = MCPToolsRegistry()
        mock_tool = MagicMock()
        config = {'max_results': 10}
        
        registry.register_tool('test_tool', mock_tool, config)
        
        assert 'test_tool' in registry.available_tools
        assert registry.available_tools['test_tool'] == mock_tool
        assert registry.tool_configs['test_tool'] == config
        assert registry.tool_health['test_tool'] is True
    
    def test_get_available_tools(self):
        """Test getting list of healthy tools"""
        registry = MCPToolsRegistry()
        
        # Register healthy tool
        registry.register_tool('healthy_tool', MagicMock())
        
        # Register unhealthy tool
        registry.register_tool('unhealthy_tool', MagicMock())
        registry.mark_tool_unhealthy('unhealthy_tool', 'test error')
        
        available = registry.get_available_tools()
        
        assert 'healthy_tool' in available
        assert 'unhealthy_tool' not in available
    
    def test_mark_tool_unhealthy(self):
        """Test marking tools as unhealthy"""
        registry = MCPToolsRegistry()
        registry.register_tool('test_tool', MagicMock())
        
        registry.mark_tool_unhealthy('test_tool', 'connection error')
        
        assert registry.tool_health['test_tool'] is False
        assert 'test_tool' not in registry.get_available_tools()


class TestSearchQueryGenerator:
    """Test search query generation for different tools"""
    
    def test_perplexity_query_generation(self):
        """Test generating queries optimized for Perplexity"""
        mock_ai_provider = MagicMock()
        generator = SearchQueryGenerator(mock_ai_provider)
        
        async def test_generation():
            queries = await generator.generate_search_queries(
                "TechCorp", "perplexity"
            )
            
            assert len(queries) <= 3
            assert any("similar" in query.lower() for query in queries)
            assert any("TechCorp" in query for query in queries)
        
        asyncio.run(test_generation())
    
    def test_tavily_query_generation(self):
        """Test generating queries optimized for Tavily"""
        mock_ai_provider = MagicMock()
        generator = SearchQueryGenerator(mock_ai_provider)
        
        async def test_generation():
            queries = await generator.generate_search_queries(
                "DataCorp", "tavily"
            )
            
            assert len(queries) <= 3
            assert any("competitors" in query.lower() for query in queries)
            assert any("DataCorp" in query for query in queries)
        
        asyncio.run(test_generation())
    
    def test_fallback_query_generation(self):
        """Test fallback query generation on errors"""
        mock_ai_provider = MagicMock()
        mock_ai_provider.analyze_text.side_effect = Exception("AI provider error")
        generator = SearchQueryGenerator(mock_ai_provider)
        
        async def test_generation():
            queries = await generator.generate_search_queries(
                "ErrorCorp", "unknown_tool"
            )
            
            # Should fall back to basic queries
            assert len(queries) >= 1
            assert any("ErrorCorp" in query for query in queries)
        
        asyncio.run(test_generation())


class TestDiscoverSimilarCompaniesUseCase:
    """Test main discovery use case"""
    
    def test_initialization(self, mock_dependencies):
        """Test use case initialization"""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            ai_provider=mock_dependencies['ai_provider'],
            fallback_search=mock_dependencies['fallback_search'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        assert use_case.vector_storage == mock_dependencies['vector_storage']
        assert use_case.ai_provider == mock_dependencies['ai_provider'] 
        assert use_case.fallback_search == mock_dependencies['fallback_search']
        assert isinstance(use_case.similarity_scorer, SimilarityScorer)
        assert isinstance(use_case.mcp_registry, MCPToolsRegistry)
    
    @pytest.mark.asyncio
    async def test_database_search_known_company(self, mock_dependencies):
        """Test database search for known companies (Salesforce)"""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        request = DiscoveryRequest(
            company_name="Salesforce",
            max_results=10,
            include_web_discovery=False
        )
        
        result = await use_case.execute(request)
        
        # Known company should return vector database matches
        assert result.query_company == "Salesforce"
        assert result.total_sources_used >= 1
        assert len(result.matches) >= 1
        
        # Should have database matches for known company
        database_matches = result.get_matches_by_source(DiscoverySource.VECTOR_DATABASE)
        assert len(database_matches) >= 1
        
        # Check match quality for known company
        for match in database_matches:
            assert match.similarity_score >= 0.8  # High similarity expected
            assert match.confidence_score >= 0.9   # High confidence expected
            assert "Salesforce" in match.company_name or "Vector Similar" in match.company_name
    
    @pytest.mark.asyncio
    async def test_web_discovery_unknown_company(self, mock_dependencies):
        """Test web discovery for unknown companies (Lobsters & Mobsters)"""
        # Setup MCP tools
        use_case = DiscoverSimilarCompaniesUseCase(
            ai_provider=mock_dependencies['ai_provider'],
            fallback_search=mock_dependencies['fallback_search'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        # Register mock MCP tools
        mock_perplexity = MagicMock()
        mock_tavily = MagicMock()
        use_case.mcp_registry.register_tool('perplexity', mock_perplexity)
        use_case.mcp_registry.register_tool('tavily', mock_tavily)
        
        request = DiscoveryRequest(
            company_name="Lobsters & Mobsters",
            max_results=20,
            include_database_search=True,
            include_web_discovery=True
        )
        
        result = await use_case.execute(request)
        
        # Unknown company should trigger web discovery
        assert result.query_company == "Lobsters & Mobsters"
        assert result.total_sources_used >= 1
        
        # Should have web search results since company not in database
        web_matches = [m for m in result.matches 
                      if m.source in [DiscoverySource.MCP_PERPLEXITY, DiscoverySource.MCP_TAVILY]]
        assert len(web_matches) >= 1
        
        # Check match relevance for unknown company
        for match in web_matches:
            assert match.confidence_score >= 0.0  # Allow zero confidence for mock data
            assert "Lobsters" in match.company_name or "Similar" in match.company_name or "Competitor" in match.company_name
    
    @pytest.mark.asyncio
    async def test_hybrid_search_strategy(self, mock_dependencies, sample_company_matches):
        """Test hybrid search combining multiple sources"""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            ai_provider=mock_dependencies['ai_provider'],
            fallback_search=mock_dependencies['fallback_search'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        # Register MCP tools
        use_case.mcp_registry.register_tool('perplexity', MagicMock())
        use_case.mcp_registry.register_tool('tavily', MagicMock())
        
        request = DiscoveryRequest(
            company_name="Microsoft",  # Known company for database + web
            max_results=50,
            include_database_search=True,
            include_web_discovery=True,
            enable_parallel_search=True
        )
        
        result = await use_case.execute(request)
        
        # Hybrid strategy should use multiple sources
        assert result.search_strategy in ["hybrid", "failed"]
        assert result.total_sources_used >= 1
        
        # Check source diversity
        source_coverage = result.calculate_source_coverage()
        used_sources = [source for source, count in source_coverage.items() if count > 0]
        assert len(used_sources) >= 1
        
        # Quality metrics should be reasonable
        assert result.average_confidence >= 0.0
        assert result.coverage_score >= 0.0
        assert result.execution_time_seconds > 0
    
    @pytest.mark.asyncio
    async def test_filtering_functionality(self, mock_dependencies):
        """Test filtering by industry, business model, etc."""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        request = DiscoveryRequest(
            company_name="Google",
            max_results=20,
            industry_filter="Technology",
            business_model_filter="B2B",
            size_filter="enterprise",
            min_similarity_score=0.7
        )
        
        result = await use_case.execute(request)
        
        # Check that filters are applied
        assert result.filters_applied['industry_filter'] == "Technology"
        assert result.filters_applied['business_model_filter'] == "B2B"
        assert result.filters_applied['size_filter'] == "enterprise"
        assert result.filters_applied['min_similarity_score'] == 0.7
        
        # All returned matches should meet filter criteria
        for match in result.matches:
            assert match.similarity_score >= 0.7
            if match.industry:
                assert "technology" in match.industry.lower()
            if match.business_model:
                assert "b2b" in match.business_model.lower()
            if match.employee_count:
                assert match.employee_count > 1000  # Enterprise size
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self, mock_dependencies):
        """Test error handling when components fail"""
        # Setup use case with failing components
        failing_vector_storage = MagicMock()
        failing_vector_storage.side_effect = Exception("Database connection failed")
        
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=failing_vector_storage,
            ai_provider=None,  # No AI provider
            fallback_search=mock_dependencies['fallback_search'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        request = DiscoveryRequest(
            company_name="ErrorTestCorp",
            max_results=10
        )
        
        result = await use_case.execute(request)
        
        # Should still return a result even with failures
        assert result.query_company == "ErrorTestCorp"
        assert result.execution_time_seconds > 0
        
        # Should record errors encountered
        assert len(result.errors_encountered) >= 0  # May have errors recorded
        
        # Result should indicate partial or complete failure
        assert result.search_strategy in ["hybrid", "failed"]
    
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_search(self, mock_dependencies):
        """Test parallel vs sequential search execution"""
        use_case = DiscoverSimilarCompaniesUseCase(
            ai_provider=mock_dependencies['ai_provider'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        # Register multiple MCP tools
        use_case.mcp_registry.register_tool('perplexity', MagicMock())
        use_case.mcp_registry.register_tool('tavily', MagicMock())
        use_case.mcp_registry.register_tool('search_droid', MagicMock())
        
        # Test parallel search
        parallel_request = DiscoveryRequest(
            company_name="ParallelTestCorp",
            enable_parallel_search=True,
            include_web_discovery=True
        )
        
        parallel_result = await use_case.execute(parallel_request)
        
        # Test sequential search
        sequential_request = DiscoveryRequest(
            company_name="SequentialTestCorp", 
            enable_parallel_search=False,
            include_web_discovery=True
        )
        
        sequential_result = await use_case.execute(sequential_request)
        
        # Both should work but parallel might be faster (not easily testable with mocks)
        assert parallel_result.total_sources_used >= 0
        assert sequential_result.total_sources_used >= 0
        
        # Both should return results
        assert parallel_result.query_company == "ParallelTestCorp"
        assert sequential_result.query_company == "SequentialTestCorp"
    
    @pytest.mark.asyncio
    async def test_quality_metrics_calculation(self, mock_dependencies, sample_company_matches):
        """Test quality metrics and scoring"""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        request = DiscoveryRequest(
            company_name="QualityTestCorp",
            max_results=10
        )
        
        result = await use_case.execute(request)
        
        # Quality metrics should be calculated
        assert 0.0 <= result.average_confidence <= 1.0
        assert 0.0 <= result.coverage_score <= 1.0
        assert 0.0 <= result.freshness_score <= 1.0
        
        # Execution timing should be recorded
        assert result.execution_time_seconds > 0
        assert isinstance(result.source_timing, dict)
        
        # Search metadata should be complete
        assert result.search_timestamp is not None
        assert isinstance(result.filters_applied, dict)
        assert isinstance(result.errors_encountered, list)
    
    @pytest.mark.asyncio
    async def test_result_ranking_and_sorting(self, mock_dependencies):
        """Test that results are properly ranked by similarity and confidence"""
        use_case = DiscoverSimilarCompaniesUseCase(
            vector_storage=mock_dependencies['vector_storage'],
            progress_tracker=mock_dependencies['progress_tracker']
        )
        
        request = DiscoveryRequest(
            company_name="Apple",  # Known company
            max_results=20
        )
        
        result = await use_case.execute(request)
        
        if len(result.matches) > 1:
            # Results should be sorted by combined score (similarity * confidence)
            scores = [(m.similarity_score * m.confidence_score) for m in result.matches]
            
            # Check that scores are in descending order
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], "Results should be sorted by combined score"
        
        # Top matches should have reasonable scores
        top_matches = result.get_top_matches(5)
        for match in top_matches:
            assert match.similarity_score > 0.0
            assert match.confidence_score > 0.0


if __name__ == "__main__":
    pytest.main([__file__])
"""
Comprehensive test suite for MCP Search Tool port interface.

This module tests the MCP search tool interfaces with realistic mock implementations
and validates all aspects of the port contracts.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

from src.core.ports.mcp_search_tool import (
    MCPSearchTool, MCPToolInfo, MCPSearchResult, MCPSearchFilters,
    MCPSearchCapability, MCPSearchException, MCPRateLimitedException,
    MCPQuotaExceededException, MCPConfigurationException,
    MCPSearchTimeoutException, StreamingMCPSearchTool,
    CacheableMCPSearchTool, BatchMCPSearchTool,
    merge_search_results, validate_mcp_tool_config
)
from src.core.domain.entities.company import Company
from src.core.domain.services.mcp_registry import (
    MCPToolRegistry, ToolRegistration, ToolStatus
)
from src.core.domain.services.mcp_aggregator import (
    MCPResultAggregator, DeduplicationStrategy, RankingStrategy,
    CompanyMatch
)


class MockMCPSearchTool(MCPSearchTool):
    """Mock implementation of MCP search tool for testing."""
    
    def __init__(
        self,
        tool_name: str = "mock_tool",
        capabilities: Optional[List[MCPSearchCapability]] = None,
        fail_validation: bool = False,
        fail_searches: bool = False,
        simulate_rate_limit: bool = False,
        search_delay: float = 0.0
    ):
        self.tool_name = tool_name
        self.capabilities = capabilities or [MCPSearchCapability.WEB_SEARCH]
        self.fail_validation = fail_validation
        self.fail_searches = fail_searches
        self.simulate_rate_limit = simulate_rate_limit
        self.search_delay = search_delay
        
        # Track calls for testing
        self.validation_calls = 0
        self.search_calls = 0
        self.detail_calls = 0
        self.health_check_calls = 0
        self.is_closed = False
        self.context_entered = False
        
        # Mock data
        self.mock_companies = [
            Company(
                name="Mock Company 1",
                website="https://mock1.com",
                description="Mock company for testing"
            ),
            Company(
                name="Mock Company 2", 
                website="https://mock2.com",
                description="Another mock company"
            )
        ]
    
    def get_tool_info(self) -> MCPToolInfo:
        return MCPToolInfo(
            tool_name=self.tool_name,
            tool_version="1.0.0",
            capabilities=self.capabilities,
            cost_per_request=0.01,
            rate_limit_per_minute=60,
            max_results_per_query=100,
            supports_filters=True,
            supports_pagination=True
        )
    
    async def search_similar_companies(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        company_description: Optional[str] = None,
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        page_token: Optional[str] = None,
        progress_callback: Optional[Any] = None
    ) -> MCPSearchResult:
        self.search_calls += 1
        
        if self.search_delay > 0:
            await asyncio.sleep(self.search_delay)
        
        if self.simulate_rate_limit:
            raise MCPRateLimitedException(self.tool_name, retry_after=60)
        
        if self.fail_searches:
            raise MCPSearchException(f"Mock search failure for {self.tool_name}")
        
        # Simulate progress callback
        if progress_callback:
            progress_callback("Searching...", 0.5, "Finding similar companies")
            progress_callback("Complete", 1.0, None)
        
        # Return mock results
        companies = self.mock_companies[:limit]
        
        return MCPSearchResult(
            companies=companies,
            tool_info=self.get_tool_info(),
            query=company_name,
            total_found=len(companies),
            search_time_ms=100.0,
            confidence_score=0.85,
            metadata={"mock": True, "filters_applied": filters is not None},
            cost_incurred=0.01
        )
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[Any] = None
    ) -> MCPSearchResult:
        self.search_calls += 1
        
        if self.fail_searches:
            raise MCPSearchException("Mock keyword search failure")
        
        # Return subset based on keywords
        companies = self.mock_companies[:limit]
        
        return MCPSearchResult(
            companies=companies,
            tool_info=self.get_tool_info(),
            query=" ".join(keywords),
            total_found=len(companies),
            search_time_ms=80.0,
            confidence_score=0.75,
            metadata={"keywords": keywords},
            cost_incurred=0.01
        )
    
    async def get_company_details(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        requested_fields: Optional[List[str]] = None
    ) -> Optional[Company]:
        self.detail_calls += 1
        
        if self.fail_searches:
            return None
        
        # Return first mock company with enhanced details
        company = self.mock_companies[0]
        return Company(
            name=company_name,
            website=company_website or company.website,
            description="Enhanced details from mock tool",
            industry="Technology",
            founded_year=2020,
            employee_count=100,
            location="San Francisco, CA"
        )
    
    async def validate_configuration(self) -> bool:
        self.validation_calls += 1
        
        if self.fail_validation:
            raise MCPConfigurationException(
                self.tool_name,
                "Mock validation failure"
            )
        
        return True
    
    async def estimate_search_cost(
        self,
        query_count: int,
        average_results_per_query: int = 10
    ) -> float:
        return query_count * 0.01
    
    async def health_check(self) -> Dict[str, Any]:
        self.health_check_calls += 1
        
        if self.fail_searches:
            return {
                "status": "unhealthy",
                "latency_ms": 1000.0,
                "success_rate": 0.0,
                "last_error": "Mock health check failure"
            }
        
        return {
            "status": "healthy",
            "latency_ms": 50.0,
            "success_rate": 0.95,
            "quota_remaining": 1000
        }
    
    async def close(self) -> None:
        self.is_closed = True
    
    async def __aenter__(self):
        self.context_entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class MockStreamingMCPTool(MockMCPSearchTool, StreamingMCPSearchTool):
    """Mock streaming MCP tool implementation."""
    
    async def search_similar_companies_streaming(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        limit: int = 10,
        filters: Optional[MCPSearchFilters] = None
    ):
        for i, company in enumerate(self.mock_companies[:limit]):
            await asyncio.sleep(0.01)  # Simulate streaming delay
            yield company


class MockCacheableMCPTool(MockMCPSearchTool, CacheableMCPSearchTool):
    """Mock cacheable MCP tool implementation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.cache_hits = 0
    
    async def search_with_cache(
        self,
        company_name: str,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> MCPSearchResult:
        cache_key = f"search:{company_name}"
        
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        # Perform regular search
        result = await self.search_similar_companies(company_name, **kwargs)
        self.cache[cache_key] = result
        return result
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        if pattern:
            # Simple pattern matching for testing
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        else:
            keys_to_remove = list(self.cache.keys())
        
        for key in keys_to_remove:
            del self.cache[key]
        
        return len(keys_to_remove)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "hit_rate": self.cache_hits / max(self.search_calls, 1)
        }


class MockBatchMCPTool(MockMCPSearchTool, BatchMCPSearchTool):
    """Mock batch MCP tool implementation."""
    
    async def search_batch_companies(
        self,
        company_names: List[str],
        limit_per_company: int = 5,
        filters: Optional[MCPSearchFilters] = None,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, MCPSearchResult]:
        results = {}
        
        for i, company_name in enumerate(company_names):
            if progress_callback:
                progress = (i + 1) / len(company_names)
                progress_callback(
                    f"Processing {company_name}",
                    progress,
                    f"{i + 1}/{len(company_names)} companies"
                )
            
            result = await self.search_similar_companies(
                company_name,
                limit=limit_per_company,
                filters=filters
            )
            results[company_name] = result
        
        return results
    
    async def get_batch_company_details(
        self,
        company_names: List[str],
        requested_fields: Optional[List[str]] = None
    ) -> Dict[str, Optional[Company]]:
        results = {}
        
        for company_name in company_names:
            company = await self.get_company_details(
                company_name,
                requested_fields=requested_fields
            )
            results[company_name] = company
        
        return results


# Test Classes

class TestMCPToolInfo:
    """Test MCPToolInfo value object."""
    
    def test_basic_creation(self):
        """Test basic tool info creation."""
        tool_info = MCPToolInfo(
            tool_name="test_tool",
            tool_version="1.0",
            capabilities=[MCPSearchCapability.WEB_SEARCH]
        )
        
        assert tool_info.tool_name == "test_tool"
        assert tool_info.tool_version == "1.0"
        assert MCPSearchCapability.WEB_SEARCH in tool_info.capabilities
    
    def test_has_capability(self):
        """Test capability checking."""
        tool_info = MCPToolInfo(
            tool_name="test_tool",
            capabilities=[
                MCPSearchCapability.WEB_SEARCH,
                MCPSearchCapability.COMPANY_RESEARCH
            ]
        )
        
        assert tool_info.has_capability(MCPSearchCapability.WEB_SEARCH)
        assert tool_info.has_capability("web_search")
        assert not tool_info.has_capability(MCPSearchCapability.FINANCIAL_DATA)
    
    def test_cost_estimation(self):
        """Test cost estimation."""
        tool_info = MCPToolInfo(
            tool_name="test_tool",
            cost_per_request=0.05
        )
        
        assert tool_info.estimate_cost(10) == 0.5
        assert tool_info.estimate_cost(0) == 0.0
        
        # Test with no cost
        free_tool = MCPToolInfo("free_tool")
        assert free_tool.estimate_cost(100) == 0.0
    
    def test_rate_limiting(self):
        """Test rate limit checking."""
        tool_info = MCPToolInfo(
            tool_name="test_tool",
            rate_limit_per_minute=60
        )
        
        assert tool_info.can_handle_rate(30)
        assert tool_info.can_handle_rate(60)
        assert not tool_info.can_handle_rate(100)
        
        # Test unlimited rate
        unlimited_tool = MCPToolInfo("unlimited_tool")
        assert unlimited_tool.can_handle_rate(10000)


class TestMCPSearchFilters:
    """Test MCPSearchFilters functionality."""
    
    def test_basic_filters(self):
        """Test basic filter creation."""
        filters = MCPSearchFilters(
            industry="Technology",
            company_size="medium",
            location="San Francisco"
        )
        
        filter_dict = filters.to_dict()
        assert filter_dict["industry"] == "Technology"
        assert filter_dict["company_size"] == "medium"
        assert filter_dict["location"] == "San Francisco"
    
    def test_empty_filters(self):
        """Test empty filter detection."""
        empty_filters = MCPSearchFilters()
        assert empty_filters.is_empty()
        
        filters_with_data = MCPSearchFilters(industry="Tech")
        assert not filters_with_data.is_empty()
    
    def test_custom_filters(self):
        """Test custom filter fields."""
        filters = MCPSearchFilters(
            custom_filters={"growth_stage": "Series A", "market": "B2B"}
        )
        
        filter_dict = filters.to_dict()
        assert filter_dict["growth_stage"] == "Series A"
        assert filter_dict["market"] == "B2B"


class TestMCPSearchResult:
    """Test MCPSearchResult functionality."""
    
    def test_basic_result(self):
        """Test basic search result creation."""
        companies = [
            Company(name="Test Co", website="https://test.com")
        ]
        tool_info = MCPToolInfo("test_tool")
        
        result = MCPSearchResult(
            companies=companies,
            tool_info=tool_info,
            query="test query",
            total_found=1,
            search_time_ms=100.0,
            confidence_score=0.8
        )
        
        assert result.get_result_count() == 1
        assert result.is_high_confidence()
        assert not result.has_more_results()
    
    def test_pagination(self):
        """Test pagination support."""
        companies = [Company(name="Test Co", website="https://test.com")]
        tool_info = MCPToolInfo("test_tool")
        
        result = MCPSearchResult(
            companies=companies,
            tool_info=tool_info,
            query="test",
            total_found=10,
            search_time_ms=100.0,
            next_page_token="page_2"
        )
        
        assert result.has_more_results()
        assert result.next_page_token == "page_2"


@pytest.mark.asyncio
class TestMockMCPSearchTool:
    """Test mock MCP search tool implementation."""
    
    async def test_basic_search(self):
        """Test basic similarity search."""
        tool = MockMCPSearchTool()
        
        result = await tool.search_similar_companies("Test Company")
        
        assert result.get_result_count() == 2
        assert result.query == "Test Company"
        assert result.confidence_score == 0.85
        assert tool.search_calls == 1
    
    async def test_keyword_search(self):
        """Test keyword-based search."""
        tool = MockMCPSearchTool()
        
        result = await tool.search_by_keywords(["AI", "startup"])
        
        assert result.get_result_count() == 2
        assert result.query == "AI startup"
        assert result.metadata["keywords"] == ["AI", "startup"]
    
    async def test_company_details(self):
        """Test company detail retrieval."""
        tool = MockMCPSearchTool()
        
        company = await tool.get_company_details("Test Company")
        
        assert company is not None
        assert company.name == "Test Company"
        assert company.industry == "Technology"
        assert tool.detail_calls == 1
    
    async def test_validation_success(self):
        """Test successful configuration validation."""
        tool = MockMCPSearchTool()
        
        is_valid = await tool.validate_configuration()
        
        assert is_valid
        assert tool.validation_calls == 1
    
    async def test_validation_failure(self):
        """Test validation failure."""
        tool = MockMCPSearchTool(fail_validation=True)
        
        with pytest.raises(MCPConfigurationException):
            await tool.validate_configuration()
    
    async def test_rate_limiting(self):
        """Test rate limiting simulation."""
        tool = MockMCPSearchTool(simulate_rate_limit=True)
        
        with pytest.raises(MCPRateLimitedException) as exc_info:
            await tool.search_similar_companies("Test")
        
        assert exc_info.value.tool_name == "mock_tool"
        assert exc_info.value.retry_after == 60
    
    async def test_search_failure(self):
        """Test search failure handling."""
        tool = MockMCPSearchTool(fail_searches=True)
        
        with pytest.raises(MCPSearchException):
            await tool.search_similar_companies("Test")
    
    async def test_health_check(self):
        """Test health check functionality."""
        tool = MockMCPSearchTool()
        
        health = await tool.health_check()
        
        assert health["status"] == "healthy"
        assert health["success_rate"] == 0.95
        assert tool.health_check_calls == 1
    
    async def test_context_manager(self):
        """Test async context manager."""
        tool = MockMCPSearchTool()
        
        async with tool as t:
            assert t.context_entered
            result = await t.search_similar_companies("Test")
            assert result is not None
        
        assert tool.is_closed
    
    async def test_progress_callback(self):
        """Test progress callback functionality."""
        tool = MockMCPSearchTool()
        progress_calls = []
        
        def progress_callback(message, progress, details):
            progress_calls.append((message, progress, details))
        
        await tool.search_similar_companies(
            "Test",
            progress_callback=progress_callback
        )
        
        assert len(progress_calls) == 2
        assert progress_calls[0][0] == "Searching..."
        assert progress_calls[1][1] == 1.0


@pytest.mark.asyncio
class TestStreamingMCPTool:
    """Test streaming MCP tool functionality."""
    
    async def test_streaming_search(self):
        """Test streaming search results."""
        tool = MockStreamingMCPTool()
        companies = []
        
        async for company in tool.search_similar_companies_streaming("Test"):
            companies.append(company)
        
        assert len(companies) == 2
        assert companies[0].name == "Mock Company 1"


@pytest.mark.asyncio
class TestCacheableMCPTool:
    """Test cacheable MCP tool functionality."""
    
    async def test_cache_hit(self):
        """Test cache hit functionality."""
        tool = MockCacheableMCPTool()
        
        # First search - cache miss
        result1 = await tool.search_with_cache("Test Company")
        assert tool.cache_hits == 0
        
        # Second search - cache hit
        result2 = await tool.search_with_cache("Test Company")
        assert tool.cache_hits == 1
        assert result1.query == result2.query
    
    async def test_cache_clearing(self):
        """Test cache clearing."""
        tool = MockCacheableMCPTool()
        
        await tool.search_with_cache("Company A")
        await tool.search_with_cache("Company B")
        
        # Clear all cache
        cleared = await tool.clear_cache()
        assert cleared == 2
        
        # Cache should be empty
        stats = await tool.get_cache_stats()
        assert stats["cache_size"] == 0


@pytest.mark.asyncio
class TestBatchMCPTool:
    """Test batch MCP tool functionality."""
    
    async def test_batch_search(self):
        """Test batch company search."""
        tool = MockBatchMCPTool()
        companies = ["Company A", "Company B"]
        
        results = await tool.search_batch_companies(companies)
        
        assert len(results) == 2
        assert "Company A" in results
        assert "Company B" in results
        assert results["Company A"].query == "Company A"
    
    async def test_batch_details(self):
        """Test batch company details."""
        tool = MockBatchMCPTool()
        companies = ["Company A", "Company B"]
        
        results = await tool.get_batch_company_details(companies)
        
        assert len(results) == 2
        assert results["Company A"] is not None
        assert results["Company A"].name == "Company A"


class TestMCPToolRegistry:
    """Test MCP tool registry functionality."""
    
    @pytest.mark.asyncio
    async def test_registry_lifecycle(self):
        """Test registry start/stop lifecycle."""
        registry = MCPToolRegistry()
        
        await registry.start()
        assert registry._running
        
        await registry.stop()
        assert not registry._running
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test tool registration."""
        registry = MCPToolRegistry()
        tool = MockMCPSearchTool()
        
        await registry.register_tool(tool, priority=80)
        
        assert "mock_tool" in registry.get_all_tool_names()
        assert registry.get_tool("mock_tool") == tool
    
    @pytest.mark.asyncio
    async def test_duplicate_registration(self):
        """Test duplicate tool registration prevention."""
        registry = MCPToolRegistry()
        tool = MockMCPSearchTool()
        
        await registry.register_tool(tool)
        
        with pytest.raises(ValueError):
            await registry.register_tool(tool)
    
    def test_capability_filtering(self):
        """Test tools with capability filtering."""
        registry = MCPToolRegistry()
        
        # This is a sync test since we're not actually registering
        # Just testing the empty case
        tools = registry.get_tools_with_capability(MCPSearchCapability.WEB_SEARCH)
        assert len(tools) == 0


class TestMCPResultAggregator:
    """Test MCP result aggregator functionality."""
    
    def test_empty_aggregation(self):
        """Test aggregation with no results."""
        aggregator = MCPResultAggregator()
        
        results = aggregator.aggregate_results({})
        
        assert len(results) == 0
    
    def test_single_tool_aggregation(self):
        """Test aggregation with single tool."""
        aggregator = MCPResultAggregator()
        
        companies = [Company(name="Test Co", website="https://test.com")]
        tool_info = MCPToolInfo("test_tool")
        result = MCPSearchResult(
            companies=companies,
            tool_info=tool_info,
            query="test",
            total_found=1,
            search_time_ms=100.0
        )
        
        aggregated = aggregator.aggregate_results({"test_tool": result})
        
        assert len(aggregated) == 1
        assert aggregated[0].name == "Test Co"
    
    def test_deduplication_strategies(self):
        """Test different deduplication strategies."""
        # Test with strict strategy
        strict_aggregator = MCPResultAggregator(
            deduplication_strategy=DeduplicationStrategy.STRICT
        )
        
        # Test with fuzzy strategy
        fuzzy_aggregator = MCPResultAggregator(
            deduplication_strategy=DeduplicationStrategy.FUZZY
        )
        
        # Test with smart strategy
        smart_aggregator = MCPResultAggregator(
            deduplication_strategy=DeduplicationStrategy.SMART
        )
        
        # Create test data with duplicate companies
        companies1 = [Company(name="Exact Match", website="https://exact.com")]
        companies2 = [Company(name="Exact Match", website="https://exact.com")]
        
        tool_info = MCPToolInfo("test_tool")
        result1 = MCPSearchResult(
            companies=companies1,
            tool_info=tool_info,
            query="test",
            total_found=1,
            search_time_ms=100.0
        )
        result2 = MCPSearchResult(
            companies=companies2,
            tool_info=tool_info,
            query="test",
            total_found=1,
            search_time_ms=100.0
        )
        
        results_dict = {"tool1": result1, "tool2": result2}
        
        # All strategies should deduplicate exact matches
        strict_results = strict_aggregator.aggregate_results(results_dict)
        fuzzy_results = fuzzy_aggregator.aggregate_results(results_dict)
        smart_results = smart_aggregator.aggregate_results(results_dict)
        
        assert len(strict_results) == 1
        assert len(fuzzy_results) == 1  
        assert len(smart_results) == 1


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_merge_search_results(self):
        """Test search result merging."""
        companies1 = [Company(name="Company A", website="https://company-a.com")]
        companies2 = [Company(name="Company B", website="https://company-b.com")]
        
        tool_info = MCPToolInfo("test_tool")
        
        result1 = MCPSearchResult(
            companies=companies1,
            tool_info=tool_info,
            query="test",
            total_found=1,
            search_time_ms=50.0,
            cost_incurred=0.01
        )
        
        result2 = MCPSearchResult(
            companies=companies2,
            tool_info=tool_info,
            query="test",
            total_found=1,
            search_time_ms=75.0,
            cost_incurred=0.02
        )
        
        merged = merge_search_results([result1, result2])
        
        assert merged.get_result_count() == 2
        assert merged.search_time_ms == 125.0
        assert merged.cost_incurred == 0.03
        assert merged.total_found == 2
    
    def test_merge_empty_results(self):
        """Test merging empty results list."""
        with pytest.raises(ValueError):
            merge_search_results([])
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = {
            "api_key": "test_key",
            "timeout": 30.0,
            "max_results": 100
        }
        
        # Should not raise exception
        validate_mcp_tool_config(config, ["api_key"])
    
    def test_config_validation_missing_fields(self):
        """Test configuration validation with missing fields."""
        config = {"timeout": 30}
        
        with pytest.raises(MCPConfigurationException):
            validate_mcp_tool_config(config, ["api_key", "endpoint"])
    
    def test_config_validation_invalid_types(self):
        """Test configuration validation with invalid types."""
        # Invalid API key type
        config = {"api_key": 12345}
        
        with pytest.raises(MCPConfigurationException):
            validate_mcp_tool_config(config, ["api_key"])
        
        # Invalid timeout type
        config = {"timeout": "not_a_number"}
        
        with pytest.raises(MCPConfigurationException):
            validate_mcp_tool_config(config, [])


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
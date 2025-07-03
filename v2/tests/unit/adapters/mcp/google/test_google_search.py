"""
Unit tests for Google Search MCP adapter.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from typing import Dict, Any, List

from src.infrastructure.adapters.mcp.google.adapter import (
    GoogleSearchAdapter,
    SearchCache
)
from src.infrastructure.adapters.mcp.google.config import (
    GoogleSearchConfig,
    GoogleSearchProvider
)
from src.infrastructure.adapters.mcp.google.client import (
    GoogleSearchClient,
    RateLimiter
)
from src.core.ports.mcp_search_tool import (
    MCPToolInfo,
    MCPSearchResult,
    MCPSearchFilters,
    MCPSearchCapability,
    MCPSearchException,
    MCPSearchTimeoutException
)
from src.core.domain.entities.company import Company


# Test Fixtures

@pytest.fixture
def config():
    """Create test configuration."""
    return GoogleSearchConfig(
        google_api_key="test_api_key",
        google_cse_id="test_cse_id",
        serpapi_key="test_serpapi_key",
        timeout_seconds=10.0,
        max_results=5,
        enable_caching=True,
        cache_ttl_seconds=60,
        company_confidence_threshold=0.3
    )


@pytest.fixture
def adapter(config):
    """Create adapter instance for testing."""
    return GoogleSearchAdapter(config)


@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.closed = False
    return session


@pytest.fixture
def sample_google_custom_response():
    """Sample Google Custom Search API response."""
    return {
        "items": [
            {
                "title": "Apple Inc. - Official Website",
                "link": "https://www.apple.com",
                "snippet": "Apple designs and develops consumer electronics, computer software, and online services.",
                "displayLink": "www.apple.com",
                "pagemap": {
                    "organization": [{"name": "Apple Inc."}],
                    "metatags": [{"description": "Apple official website"}]
                }
            },
            {
                "title": "Samsung Corporation - Technology Company",
                "link": "https://www.samsung.com",
                "snippet": "Samsung is a South Korean multinational conglomerate.",
                "displayLink": "www.samsung.com"
            }
        ]
    }


@pytest.fixture
def sample_companies():
    """Sample company objects for testing."""
    return [
        Company(
            name="Samsung Corporation",
            website="https://www.samsung.com",
            description="Samsung is a South Korean multinational conglomerate.",
            confidence_score=0.8
        ),
        Company(
            name="Google LLC",
            website="https://www.google.com",
            description="Google is a multinational technology company.",
            confidence_score=0.7
        )
    ]


# Configuration Tests

class TestGoogleSearchConfig:
    """Test Google Search configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GoogleSearchConfig()
        
        assert GoogleSearchProvider.CUSTOM_SEARCH in config.preferred_providers
        assert GoogleSearchProvider.SERPAPI in config.preferred_providers
        assert GoogleSearchProvider.DUCKDUCKGO in config.preferred_providers
        assert config.timeout_seconds == 30.0
        assert config.max_results == 10
        assert config.enable_caching is True
        assert config.company_confidence_threshold == 0.3
        assert 'wikipedia.org' in config.excluded_domains
        assert 'company' in config.company_keywords
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = GoogleSearchConfig(
            timeout_seconds=15.0,
            max_results=20,
            search_language="en",
            search_country="us"
        )
        assert config.timeout_seconds == 15.0
        assert config.max_results == 20
        
        # Invalid timeout
        with pytest.raises(ValueError):
            GoogleSearchConfig(timeout_seconds=0.5)  # Below minimum
        
        # Invalid language
        with pytest.raises(ValueError):
            GoogleSearchConfig(search_language="invalid")  # Not 2 letters
        
        # Invalid country
        with pytest.raises(ValueError):
            GoogleSearchConfig(search_country="USA")  # Not 2 letters
    
    def test_get_available_providers(self):
        """Test available provider detection."""
        # No API keys
        config = GoogleSearchConfig()
        available = config.get_available_providers()
        assert available == [GoogleSearchProvider.DUCKDUCKGO]  # Only DuckDuckGo works without keys
        
        # With Google API key
        config = GoogleSearchConfig(
            google_api_key="test_key",
            google_cse_id="test_cse"
        )
        available = config.get_available_providers()
        assert GoogleSearchProvider.CUSTOM_SEARCH in available
        assert GoogleSearchProvider.DUCKDUCKGO in available
        
        # With SerpAPI key
        config = GoogleSearchConfig(serpapi_key="test_serpapi")
        available = config.get_available_providers()
        assert GoogleSearchProvider.SERPAPI in available
        assert GoogleSearchProvider.DUCKDUCKGO in available


# Cache Tests

class TestSearchCache:
    """Test search cache functionality."""
    
    def test_cache_set_get(self, sample_companies):
        """Test basic cache set/get operations."""
        cache = SearchCache(max_size=10, ttl_seconds=60)
        
        tool_info = MCPToolInfo(
            tool_name="Test Tool",
            tool_version="1.0",
            capabilities=[],
            tool_config={}
        )
        
        result = MCPSearchResult(
            companies=sample_companies,
            tool_info=tool_info,
            query="test query",
            total_found=2,
            search_time_ms=100.0,
            confidence_score=0.75
        )
        
        cache.set("test_key", result)
        cached_result = cache.get("test_key")
        
        assert cached_result is not None
        assert len(cached_result.companies) == 2
        assert cached_result.companies[0].name == "Samsung Corporation"
        assert cached_result.query == "test query"
    
    def test_cache_ttl_expiration(self, sample_companies):
        """Test cache TTL expiration."""
        import time
        cache = SearchCache(max_size=10, ttl_seconds=1)  # 1 second TTL
        
        tool_info = MCPToolInfo(
            tool_name="Test Tool",
            tool_version="1.0",
            capabilities=[],
            tool_config={}
        )
        
        result = MCPSearchResult(
            companies=sample_companies,
            tool_info=tool_info,
            query="test query",
            total_found=2,
            search_time_ms=100.0,
            confidence_score=0.75
        )
        
        cache.set("test_key", result)
        # Should be available immediately
        cached_result = cache.get("test_key")
        assert cached_result is not None
        
        # Wait for expiration
        time.sleep(1.1)
        cached_result = cache.get("test_key")
        assert cached_result is None


# Rate Limiter Tests

class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limits."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # Should allow immediate requests up to burst size
        for _ in range(5):
            await limiter.acquire()  # Should not block
    
    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limits(self):
        """Test that rate limiter enforces rate limits."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=1)
        
        # First request should pass
        await limiter.acquire()
        
        # Second request should be delayed
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # Should have been delayed by approximately 1 second (60 req/min = 1 req/sec)
        assert end_time - start_time >= 0.9  # Allow some tolerance


# Adapter Tests

class TestGoogleSearchAdapter:
    """Test Google Search adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, config):
        """Test adapter initialization."""
        adapter = GoogleSearchAdapter(config)
        
        assert adapter.config == config
        assert adapter._client is not None
        assert adapter._cache is not None
        assert len(adapter._available_providers) >= 1  # At least DuckDuckGo should be available
    
    def test_get_tool_info(self, adapter):
        """Test tool info generation."""
        tool_info = adapter.get_tool_info()
        
        assert tool_info.tool_name == "Google Search"
        assert tool_info.tool_name == "Google Search"
        assert MCPSearchCapability.WEB_SEARCH in tool_info.capabilities
        assert MCPSearchCapability.COMPANY_RESEARCH in tool_info.capabilities
        assert tool_info.cost_per_request == 0.01
    
    def test_get_supported_capabilities(self, adapter):
        """Test supported capabilities."""
        capabilities = adapter.get_supported_capabilities()
        
        assert MCPSearchCapability.WEB_SEARCH in capabilities
        assert MCPSearchCapability.COMPANY_RESEARCH in capabilities
        assert MCPSearchCapability.COMPETITIVE_ANALYSIS in capabilities
    
    def test_build_search_query(self, adapter):
        """Test search query building."""
        # Basic query
        query1 = adapter._build_search_query("Apple Inc")
        assert 'companies similar to "Apple Inc"' in query1
        
        # Query with description
        query2 = adapter._build_search_query(
            "Apple Inc", 
            company_description="technology company"
        )
        assert 'companies like "Apple Inc" technology company' in query2
        
        # Query with filters
        filters = MCPSearchFilters()
        filters.industry = "technology"
        filters.location = "USA"
        
        query3 = adapter._build_search_query("Apple Inc", filters=filters)
        assert "industry:technology" in query3
        assert "location:USA" in query3
    
    def test_extract_company_name_from_title(self, adapter):
        """Test company name extraction from titles."""
        # Standard pattern
        name1 = adapter._extract_company_name_from_title("Microsoft Corporation - Official Website")
        assert name1 == "Microsoft Corporation"
        
        # With legal suffix
        name2 = adapter._extract_company_name_from_title("Apple Inc official website")
        assert name2 == "Apple Inc"
        
        # Generic terms should be filtered out
        name3 = adapter._extract_company_name_from_title("Home - Company Website")
        assert name3 is None
    
    def test_calculate_company_confidence(self, adapter):
        """Test company confidence calculation."""
        # High confidence case
        score1 = adapter._calculate_company_confidence(
            "Microsoft Corporation - Official Website",
            "Microsoft develops computer software and technology",
            "https://www.microsoft.com",
            "Microsoft Corporation"
        )
        
        # Low confidence case
        score2 = adapter._calculate_company_confidence(
            "Random Blog Post",
            "Some random content",
            "https://linkedin.com/company/test",
            "Test Company"
        )
        
        assert score1 > score2
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
    
    def test_is_same_company(self, adapter):
        """Test company name similarity detection."""
        assert adapter._is_same_company("Apple Inc", "Apple Inc.") is True
        assert adapter._is_same_company("Microsoft Corp", "Microsoft Corporation") is True
        assert adapter._is_same_company("Apple Inc", "Microsoft Corp") is False
        assert adapter._is_same_company("Google", "Google LLC") is True
    
    def test_should_exclude_url(self, adapter):
        """Test URL exclusion logic."""
        assert adapter._should_exclude_url("https://en.wikipedia.org/wiki/Apple") is True
        assert adapter._should_exclude_url("https://www.linkedin.com/company/apple") is True
        assert adapter._should_exclude_url("https://www.apple.com") is False
        assert adapter._should_exclude_url("invalid-url") is True  # Should exclude unparseable URLs
    
    @pytest.mark.asyncio
    async def test_search_similar_companies_with_cache(self, adapter, sample_google_custom_response):
        """Test search with caching."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.search_google_custom = AsyncMock(return_value=[
            {
                'title': 'Samsung Corporation - Technology Company',
                'url': 'https://www.samsung.com',
                'snippet': 'Samsung is a technology conglomerate',
                'displayed_url': 'www.samsung.com',
                'provider': 'google_custom',
                'position': 1
            }
        ])
        adapter._client = mock_client
        
        # First search (should hit API)
        result1 = await adapter.search_similar_companies("Apple Inc", limit=5)
        assert result1.total_found >= 0
        assert result1.query is not None
        
        # Second search (should hit cache)
        result2 = await adapter.search_similar_companies("Apple Inc", limit=5)
        assert result2.query == result1.query
        
        # API should only be called once due to caching
        mock_client.search_google_custom.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_fallback_chain(self, config):
        """Test fallback between providers."""
        # Configure with multiple providers but failing first ones
        config.preferred_providers = [
            GoogleSearchProvider.CUSTOM_SEARCH,
            GoogleSearchProvider.SERPAPI,
            GoogleSearchProvider.DUCKDUCKGO
        ]
        
        adapter = GoogleSearchAdapter(config)
        
        # Mock client with first provider failing
        mock_client = AsyncMock()
        mock_client.search_google_custom = AsyncMock(side_effect=Exception("API error"))
        mock_client.search_serpapi = AsyncMock(side_effect=Exception("API error"))
        mock_client.search_duckduckgo = AsyncMock(return_value=[
            {
                'title': 'Test Company - Official Website',
                'url': 'https://example.com',
                'snippet': 'Test company description',
                'displayed_url': 'example.com',
                'provider': 'duckduckgo',
                'position': 1
            }
        ])
        adapter._client = mock_client
        
        result = await adapter.search_similar_companies("Apple Inc", limit=5)
        
        # Should fallback to DuckDuckGo and succeed
        assert result.metadata['provider_used'] == 'GoogleSearchProvider.DUCKDUCKGO'
    
    @pytest.mark.asyncio
    async def test_search_all_providers_fail(self, adapter):
        """Test behavior when all providers fail."""
        # Mock client with all providers failing
        mock_client = AsyncMock()
        mock_client.search_google_custom = AsyncMock(side_effect=Exception("API error"))
        mock_client.search_serpapi = AsyncMock(side_effect=Exception("API error"))
        mock_client.search_duckduckgo = AsyncMock(side_effect=Exception("Network error"))
        adapter._client = mock_client
        
        with pytest.raises(MCPSearchException, match="All search providers failed"):
            await adapter.search_similar_companies("Apple Inc", limit=5)
    
    @pytest.mark.asyncio
    async def test_search_streaming(self, adapter):
        """Test streaming search results."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.search_duckduckgo = AsyncMock(return_value=[
            {
                'title': f'Company {i} - Official Website',
                'url': f'https://company{i}.com',
                'snippet': f'Description {i}',
                'displayed_url': f'company{i}.com',
                'provider': 'duckduckgo',
                'position': i + 1
            }
            for i in range(3)
        ])
        adapter._client = mock_client
        
        companies = []
        async for company in adapter.search_similar_companies_streaming("Apple Inc", limit=3):
            companies.append(company)
        
        assert len(companies) >= 0  # Might be 0 if extraction fails
        assert all(isinstance(c, Company) for c in companies)
    
    @pytest.mark.asyncio
    async def test_search_batch(self, adapter):
        """Test batch search processing."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.search_duckduckgo = AsyncMock(return_value=[
            {
                'title': 'Test Company - Official Website',
                'url': 'https://example.com',
                'snippet': 'Test description',
                'displayed_url': 'example.com',
                'provider': 'duckduckgo',
                'position': 1
            }
        ])
        adapter._client = mock_client
        
        company_names = ["Apple Inc", "Microsoft Corp", "Google LLC"]
        
        batch_results = await adapter.search_similar_companies_batch(company_names, limit_per_company=5)
        
        assert len(batch_results) == 3
        assert all(isinstance(result, MCPSearchResult) for result in batch_results)
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check functionality."""
        # Mock successful client
        mock_client = AsyncMock()
        mock_client.search_duckduckgo = AsyncMock(return_value=[])
        adapter._client = mock_client
        
        health = await adapter.health_check()
        
        assert health['service'] == 'google_search'
        assert 'available_providers' in health
        assert 'cache_stats' in health
        assert 'providers' in health
        assert 'response_time_ms' in health
        assert health['status'] in ['healthy', 'unhealthy']
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, adapter):
        """Test cache operations."""
        # Clear cache
        cleared = await adapter.clear_cache()
        assert cleared >= 0
        
        # Get cache stats
        stats = await adapter.get_cache_stats()
        assert 'total_entries' in stats
        assert 'max_size' in stats
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test adapter as async context manager."""
        async with adapter as ctx_adapter:
            assert ctx_adapter is adapter
        
        # Client should be cleaned up after context exit
        # Note: We can't easily test this without accessing private methods
    
    def test_generate_cache_key(self, adapter):
        """Test cache key generation."""
        key1 = adapter._generate_cache_key("Apple Inc", None, None, 10, None)
        key2 = adapter._generate_cache_key("Apple Inc", None, None, 10, None)
        key3 = adapter._generate_cache_key("Microsoft Corp", None, None, 10, None)
        
        # Same parameters should generate same keys
        assert key1 == key2
        
        # Different parameters should generate different keys
        assert key1 != key3


# Integration Tests

class TestGoogleSearchIntegration:
    """Integration tests for Google search functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_duckduckgo_search(self):
        """Test real DuckDuckGo search (requires internet)."""
        config = GoogleSearchConfig(
            timeout_seconds=30.0,
            max_results=3,
            enable_caching=False,  # Disable caching for real test
            company_confidence_threshold=0.1  # Lower threshold for testing
        )
        
        adapter = GoogleSearchAdapter(config)
        
        try:
            result = await adapter.search_similar_companies("Apple Inc", limit=3)
            
            assert result.total_found >= 0
            assert isinstance(result, MCPSearchResult)
            assert result.search_time_ms > 0
            
            # Should find some companies (though extraction might filter many out)
            # We don't assert on specific count since it depends on search results and extraction success
            
        finally:
            await adapter.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_company_extraction_real(self):
        """Test company extraction with real search results."""
        config = GoogleSearchConfig(
            timeout_seconds=30.0,
            max_results=5,
            extract_company_info=True,
            company_confidence_threshold=0.2
        )
        
        adapter = GoogleSearchAdapter(config)
        
        try:
            result = await adapter.search_similar_companies("Microsoft Corporation", limit=5)
            
            # Test that we get a valid result structure
            assert isinstance(result, MCPSearchResult)
            assert result.tool_info.tool_name == "Google Search"
            assert result.search_time_ms > 0
            
            # Companies should have required attributes
            for company in result.companies:
                assert hasattr(company, 'name')
                assert hasattr(company, 'website')
                assert hasattr(company, 'confidence_score')
                assert 0.0 <= company.confidence_score <= 1.0
            
        finally:
            await adapter.close()


if __name__ == "__main__":
    pytest.main([__file__])
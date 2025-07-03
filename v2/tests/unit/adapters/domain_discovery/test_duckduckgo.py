"""
Unit tests for DuckDuckGo domain discovery adapter.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from typing import Dict, Any

from src.infrastructure.adapters.domain_discovery.duckduckgo import (
    DuckDuckGoAdapter,
    DomainCache,
    RateLimiter
)
from src.infrastructure.adapters.domain_discovery.config import DuckDuckGoConfig
from src.core.ports.domain_discovery import (
    DomainDiscoveryConfig,
    DomainDiscoveryResult,
    DiscoveryStrategy,
    DomainValidationLevel,
    DomainDiscoveryException,
    DomainDiscoveryTimeoutException,
    normalize_company_name,
    extract_domain_from_url,
    is_valid_domain_format
)


# Test Fixtures

@pytest.fixture
def config():
    """Create test configuration."""
    return DuckDuckGoConfig(
        timeout_seconds=5.0,
        max_retries=2,
        enable_caching=True,
        cache_ttl_seconds=60,
        enable_domain_validation=True,
        min_confidence_threshold=0.3
    )


@pytest.fixture
def adapter(config):
    """Create adapter instance for testing."""
    return DuckDuckGoAdapter(config)


@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.closed = False
    return session


@pytest.fixture
def sample_search_html():
    """Sample DuckDuckGo search results HTML."""
    return '''
    <html>
    <body>
        <div class="results">
            <div class="result">
                <a href="https://www.apple.com">Apple - Official Website</a>
                <span class="snippet">Apple designs and develops consumer electronics.</span>
            </div>
            <div class="result">
                <a href="https://en.wikipedia.org/wiki/Apple_Inc.">Apple Inc. - Wikipedia</a>
                <span class="snippet">Apple Inc. is an American multinational technology company.</span>
            </div>
            <div class="result">
                <a href="https://www.apple.com/support">Apple Support</a>
                <span class="snippet">Get help with your Apple products.</span>
            </div>
        </div>
    </body>
    </html>
    '''


# Utility Function Tests

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_normalize_company_name(self):
        """Test company name normalization."""
        assert normalize_company_name("Apple Inc.") == "Apple"
        assert normalize_company_name("Microsoft Corporation") == "Microsoft"
        assert normalize_company_name("Lobsters & Mobsters LLC") == "Lobsters Mobsters"  # & removed
        assert normalize_company_name("  Google Co.  ") == "Google"
        assert normalize_company_name("AT&T Corp") == "ATT"  # & removed
    
    def test_extract_domain_from_url(self):
        """Test domain extraction from URLs."""
        assert extract_domain_from_url("https://www.apple.com/products") == "apple.com"
        assert extract_domain_from_url("http://google.com") == "google.com"
        assert extract_domain_from_url("microsoft.com/about") == "microsoft.com"
        assert extract_domain_from_url("https://www.subdomain.example.org/path") == "subdomain.example.org"
        assert extract_domain_from_url("invalid-url") is None
    
    def test_is_valid_domain_format(self):
        """Test domain format validation."""
        assert is_valid_domain_format("example.com") is True
        assert is_valid_domain_format("subdomain.example.com") is True
        assert is_valid_domain_format("example.co.uk") is True
        assert is_valid_domain_format("invalid") is False
        assert is_valid_domain_format("") is False
        assert is_valid_domain_format("example.") is False


# Configuration Tests

class TestDuckDuckGoConfig:
    """Test DuckDuckGo configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DuckDuckGoConfig()
        
        assert config.timeout_seconds == 10.0
        assert config.max_retries == 3
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 86400
        assert config.min_confidence_threshold == 0.3
        assert 'linkedin.com' in config.excluded_domains
        assert '.com' in config.preferred_domains
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = DuckDuckGoConfig(timeout_seconds=5.0, max_retries=2)
        assert config.timeout_seconds == 5.0
        
        # Invalid timeout
        with pytest.raises(ValueError):
            DuckDuckGoConfig(timeout_seconds=0.5)  # Below minimum
        
        # Invalid retries
        with pytest.raises(ValueError):
            DuckDuckGoConfig(max_retries=-1)  # Below minimum
    
    def test_search_template_validation(self):
        """Test search template validation."""
        # Valid template
        config = DuckDuckGoConfig(search_query_template='"{company_name}" website')
        assert config.search_query_template == '"{company_name}" website'
        
        # Invalid template (missing placeholder)
        with pytest.raises(ValueError, match="must contain"):
            DuckDuckGoConfig(search_query_template='"company" website')
    
    def test_get_headers(self):
        """Test header generation."""
        config = DuckDuckGoConfig(
            user_agent="Test-Agent/1.0",
            custom_headers={"X-Custom": "value"}
        )
        headers = config.get_headers()
        
        assert headers["User-Agent"] == "Test-Agent/1.0"
        assert headers["X-Custom"] == "value"
        assert "Accept" in headers
    
    def test_should_exclude_domain(self):
        """Test domain exclusion logic."""
        config = DuckDuckGoConfig()
        
        assert config.should_exclude_domain("linkedin.com") is True
        assert config.should_exclude_domain("www.facebook.com") is True
        assert config.should_exclude_domain("example.com") is False
    
    def test_get_domain_preference_score(self):
        """Test domain preference scoring."""
        config = DuckDuckGoConfig()
        
        assert config.get_domain_preference_score("example.com") == 1.0  # .com is first
        assert config.get_domain_preference_score("example.net") == 0.9  # .net is second
        assert config.get_domain_preference_score("example.biz") == 0.5  # Not in preferences


# Cache Tests

class TestDomainCache:
    """Test domain cache functionality."""
    
    def test_cache_set_get(self):
        """Test basic cache set/get operations."""
        cache = DomainCache(max_size=10, ttl_seconds=60)
        
        result = DomainDiscoveryResult(
            company_name="Apple Inc",
            discovered_domain="apple.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        cache.set("test_key", result)
        cached_result = cache.get("test_key")
        
        assert cached_result is not None
        assert cached_result.discovered_domain == "apple.com"
        assert cached_result.confidence_score == 0.9
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        import time
        cache = DomainCache(max_size=10, ttl_seconds=1)  # 1 second expiration
        
        result = DomainDiscoveryResult(
            company_name="Apple Inc",
            discovered_domain="apple.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        cache.set("test_key", result)
        # Should be available immediately
        cached_result = cache.get("test_key")
        assert cached_result is not None
        
        # Wait for expiration
        time.sleep(1.1)
        cached_result = cache.get("test_key")
        assert cached_result is None
    
    def test_cache_max_size_eviction(self):
        """Test cache eviction when max size is reached."""
        cache = DomainCache(max_size=2, ttl_seconds=3600)
        
        result1 = DomainDiscoveryResult(
            company_name="Company 1",
            discovered_domain="company1.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        result2 = DomainDiscoveryResult(
            company_name="Company 2",
            discovered_domain="company2.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        result3 = DomainDiscoveryResult(
            company_name="Company 3",
            discovered_domain="company3.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        cache.set("key1", result1)
        cache.set("key2", result2)
        cache.set("key3", result3)  # Should evict oldest
        
        # key1 should be evicted, key2 and key3 should remain
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = DomainCache(max_size=10, ttl_seconds=3600)
        
        result = DomainDiscoveryResult(
            company_name="Apple Inc",
            discovered_domain="apple.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        cache.set("key1", result)
        cache.set("key2", result)
        
        # Clear all
        cleared = cache.clear()
        assert cleared == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = DomainCache(max_size=10, ttl_seconds=3600)
        
        result = DomainDiscoveryResult(
            company_name="Apple Inc",
            discovered_domain="apple.com",
            confidence_score=0.9,
            discovery_strategy=DiscoveryStrategy.SEARCH_ENGINE,
            validation_level=DomainValidationLevel.HTTP_CHECK,
            is_validated=True,
            search_time_ms=100.0,
            metadata={}
        )
        
        cache.set("key1", result)
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 1
        assert stats['max_size'] == 10
        assert stats['ttl_seconds'] == 3600


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

class TestDuckDuckGoAdapter:
    """Test DuckDuckGo adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, config):
        """Test adapter initialization."""
        adapter = DuckDuckGoAdapter(config)
        
        assert adapter.config == config
        assert adapter._cache is not None
        assert adapter._rate_limiter is not None
        assert adapter._session is None  # Not created until needed
    
    @pytest.mark.asyncio
    async def test_get_session(self, adapter):
        """Test HTTP session creation."""
        session = await adapter._get_session()
        
        assert session is not None
        assert not session.closed
        
        # Second call should return same session
        session2 = await adapter._get_session()
        assert session is session2
        
        await adapter.close()
    
    def test_parse_search_results(self, adapter, sample_search_html):
        """Test search results parsing."""
        results = adapter._parse_search_results(sample_search_html)
        
        assert len(results) >= 1
        
        # Should find Apple's official website
        apple_result = next((r for r in results if 'apple.com' in r['url']), None)
        assert apple_result is not None
        assert 'Apple' in apple_result['title']
    
    def test_extract_domain_candidates(self, adapter):
        """Test domain candidate extraction."""
        search_results = [
            {
                'url': 'https://www.apple.com',
                'title': 'Apple - Official Website',
                'description': 'Apple designs consumer electronics'
            },
            {
                'url': 'https://en.wikipedia.org/wiki/Apple_Inc.',
                'title': 'Apple Inc. - Wikipedia',
                'description': 'Apple Inc. is a technology company'
            },
            {
                'url': 'https://www.apple.com/support',
                'title': 'Apple Support',
                'description': 'Get help with Apple products'
            }
        ]
        
        candidates = adapter._extract_domain_candidates(search_results, "Apple")
        
        # Should exclude wikipedia (in excluded domains) but include apple.com
        assert len(candidates) >= 1
        assert any(c['domain'] == 'apple.com' for c in candidates)
        assert not any(c['domain'] == 'en.wikipedia.org' for c in candidates)
    
    def test_calculate_relevance_score(self, adapter):
        """Test relevance score calculation."""
        # High relevance: company name match, official keyword
        score1 = adapter._calculate_relevance_score(
            'apple.com',
            'Apple - Official Website',
            'Apple official homepage',
            'Apple'
        )
        
        # Low relevance: no match, negative keywords
        score2 = adapter._calculate_relevance_score(
            'example.com',
            'Random website',
            'Some random blog post',
            'Apple'
        )
        
        assert score1 > score2
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
    
    @pytest.mark.asyncio
    async def test_select_best_domain(self, adapter):
        """Test domain selection logic."""
        candidates = [
            {'domain': 'apple.com', 'relevance_score': 0.8},
            {'domain': 'example.com', 'relevance_score': 0.4},
            {'domain': 'test.com', 'relevance_score': 0.2}
        ]
        
        best_domain = await adapter._select_best_domain(candidates, "Apple")
        assert best_domain == 'apple.com'
        
        # Test with no valid candidates (below threshold)
        low_candidates = [
            {'domain': 'example.com', 'relevance_score': 0.1}
        ]
        best_domain = await adapter._select_best_domain(low_candidates, "Apple")
        assert best_domain is None
    
    def test_calculate_confidence(self, adapter):
        """Test confidence calculation."""
        candidates = [
            {'domain': 'apple.com', 'relevance_score': 0.8},
            {'domain': 'example.com', 'relevance_score': 0.4}
        ]
        
        # With validation
        confidence1 = adapter._calculate_confidence('apple.com', candidates, 'Apple', True)
        
        # Without validation
        confidence2 = adapter._calculate_confidence('apple.com', candidates, 'Apple', False)
        
        assert confidence1 > confidence2  # Validation should boost confidence
        assert 0.0 <= confidence1 <= 1.0
        assert 0.0 <= confidence2 <= 1.0
    
    @pytest.mark.asyncio
    async def test_validate_domain_basic(self, adapter):
        """Test basic domain validation."""
        # Valid format
        result = await adapter.validate_domain('example.com', DomainValidationLevel.BASIC)
        assert result is True
        
        # Invalid format
        result = await adapter.validate_domain('invalid', DomainValidationLevel.BASIC)
        assert result is False
        
        # No validation
        result = await adapter.validate_domain('anything', DomainValidationLevel.NONE)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_domain_http(self, adapter, mock_session):
        """Test HTTP domain validation."""
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.head.return_value = mock_response
        adapter._session = mock_session
        
        result = await adapter.validate_domain('example.com', DomainValidationLevel.HTTP_CHECK)
        assert result is True
        
        # Mock failed HTTP response
        mock_response.status = 404
        result = await adapter.validate_domain('example.com', DomainValidationLevel.HTTP_CHECK)
        assert result is False
    
    def test_get_supported_strategies(self, adapter):
        """Test supported strategies."""
        strategies = adapter.get_supported_strategies()
        assert DiscoveryStrategy.SEARCH_ENGINE in strategies
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter, mock_session):
        """Test health check functionality."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get.return_value = mock_response
        adapter._session = mock_session
        
        health = await adapter.health_check()
        
        assert health['status'] == 'healthy'
        assert 'response_time_ms' in health
        assert 'cache_stats' in health
        assert health['service'] == 'duckduckgo'
    
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
    async def test_discover_domain_with_cache(self, adapter, mock_session, sample_search_html):
        """Test domain discovery with caching."""
        # Mock search response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_search_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock validation response
        mock_validation_response = AsyncMock()
        mock_validation_response.status = 200
        mock_validation_response.__aenter__ = AsyncMock(return_value=mock_validation_response)
        mock_validation_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get.return_value = mock_response
        mock_session.head.return_value = mock_validation_response
        adapter._session = mock_session
        
        # First discovery (should hit search engine)
        result1 = await adapter.discover_domain("Apple Inc")
        
        assert result1.company_name == "Apple Inc"
        assert result1.discovered_domain is not None
        assert result1.confidence_score > 0
        assert result1.discovery_strategy == DiscoveryStrategy.SEARCH_ENGINE
        
        # Second discovery (should hit cache)
        result2 = await adapter.discover_domain("Apple Inc")
        
        # Results should be identical
        assert result1.discovered_domain == result2.discovered_domain
        assert result1.confidence_score == result2.confidence_score
    
    @pytest.mark.asyncio
    async def test_discover_domains_batch(self, adapter, mock_session, sample_search_html):
        """Test batch domain discovery."""
        # Mock responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_search_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_validation_response = AsyncMock()
        mock_validation_response.status = 200
        mock_validation_response.__aenter__ = AsyncMock(return_value=mock_validation_response)
        mock_validation_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get.return_value = mock_response
        mock_session.head.return_value = mock_validation_response
        adapter._session = mock_session
        
        companies = ["Apple Inc", "Microsoft Corp", "Google LLC"]
        results = await adapter.discover_domains_batch(companies)
        
        assert len(results) == 3
        assert all(isinstance(r, DomainDiscoveryResult) for r in results)
        assert all(r.company_name in companies for r in results)
    
    @pytest.mark.asyncio
    async def test_discover_domains_streaming(self, adapter, mock_session, sample_search_html):
        """Test streaming domain discovery."""
        # Mock responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_search_html)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_validation_response = AsyncMock()
        mock_validation_response.status = 200
        mock_validation_response.__aenter__ = AsyncMock(return_value=mock_validation_response)
        mock_validation_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get.return_value = mock_response
        mock_session.head.return_value = mock_validation_response
        adapter._session = mock_session
        
        companies = ["Apple Inc", "Microsoft Corp"]
        results = []
        
        async for result in adapter.discover_domains_streaming(companies):
            results.append(result)
        
        assert len(results) == 2
        assert all(isinstance(r, DomainDiscoveryResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, adapter, mock_session):
        """Test error handling in domain discovery."""
        # Mock network error
        mock_session.get.side_effect = aiohttp.ClientError("Network error")
        adapter._session = mock_session
        
        result = await adapter.discover_domain("Test Company")
        
        assert result.discovered_domain is None
        assert result.confidence_score == 0.0
        assert result.error_message is not None
        assert "Network error" in result.error_message
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, adapter, mock_session):
        """Test timeout handling in domain discovery."""
        # Mock timeout
        mock_session.get.side_effect = asyncio.TimeoutError()
        adapter._session = mock_session
        
        with pytest.raises(DomainDiscoveryTimeoutException):
            await adapter.discover_domain("Test Company")
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test adapter as async context manager."""
        async with adapter as ctx_adapter:
            assert ctx_adapter is adapter
        
        # Session should be closed after context exit
        if adapter._session:
            assert adapter._session.closed
    
    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test adapter cleanup."""
        # Create session
        await adapter._get_session()
        assert adapter._session is not None
        assert not adapter._session.closed
        
        # Close adapter
        await adapter.close()
        
        # Session should be closed
        assert adapter._session.closed


# Integration Tests

class TestDomainDiscoveryIntegration:
    """Integration tests for domain discovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_domain_discovery(self):
        """Test real domain discovery (requires internet)."""
        config = DuckDuckGoConfig(
            timeout_seconds=30.0,
            enable_domain_validation=True,
            min_confidence_threshold=0.1  # Lower threshold for testing
        )
        
        adapter = DuckDuckGoAdapter(config)
        
        try:
            # Test well-known company
            result = await adapter.discover_domain("Apple Inc")
            
            assert result.company_name == "Apple Inc"
            assert result.discovery_strategy == DiscoveryStrategy.SEARCH_ENGINE
            assert result.search_time_ms > 0
            
            # Should find apple.com or similar
            if result.discovered_domain:
                assert 'apple' in result.discovered_domain.lower()
                assert result.confidence_score > 0
            
        finally:
            await adapter.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nonexistent_company(self):
        """Test discovery for nonexistent company."""
        config = DuckDuckGoConfig(
            timeout_seconds=10.0,
            min_confidence_threshold=0.5
        )
        
        adapter = DuckDuckGoAdapter(config)
        
        try:
            result = await adapter.discover_domain("Nonexistent Company XYZ123")
            
            assert result.company_name == "Nonexistent Company XYZ123"
            assert result.discovered_domain is None or result.confidence_score < 0.5
            
        finally:
            await adapter.close()


if __name__ == "__main__":
    pytest.main([__file__])
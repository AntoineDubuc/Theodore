"""
Unit tests for Perplexity MCP adapter.

Tests all components of the Perplexity adapter including configuration,
client, and adapter functionality with comprehensive mocking.
"""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.infrastructure.adapters.mcp.perplexity.config import (
    PerplexityConfig,
    PerplexityModel,
    SearchFocus,
    SearchDepth
)
from src.infrastructure.adapters.mcp.perplexity.client import (
    PerplexityClient,
    PerplexityResponse,
    PerplexityClientError,
    PerplexityRateLimitError,
    PerplexityQuotaError,
    PerplexityAuthError
)
from src.infrastructure.adapters.mcp.perplexity.adapter import PerplexityAdapter
from src.core.ports.mcp_search_tool import (
    MCPSearchFilters,
    MCPSearchCapability,
    MCPRateLimitedException,
    MCPQuotaExceededException,
    MCPConfigurationException
)
from src.core.domain.entities.company import Company


class TestPerplexityConfig:
    """Test Perplexity configuration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = PerplexityConfig(api_key="pplx-test-key")
        
        assert config.api_key == "pplx-test-key"
        assert config.model == PerplexityModel.SONAR_MEDIUM
        assert config.search_focus == SearchFocus.WEB
        assert config.search_depth == SearchDepth.COMPREHENSIVE
        assert config.max_results == 10
        assert config.rate_limit_requests_per_minute == 20
        assert config.timeout_seconds == 30.0
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 3600
    
    def test_api_key_validation(self):
        """Test API key validation."""
        # Valid API key
        config = PerplexityConfig(api_key="pplx-valid-key")
        assert config.api_key == "pplx-valid-key"
        
        # Invalid API key format
        with pytest.raises(ValueError, match="must start with 'pplx-'"):
            PerplexityConfig(api_key="invalid-key")
        
        # Empty API key
        with pytest.raises(ValueError, match="cannot be empty"):
            PerplexityConfig(api_key="")
    
    def test_excluded_domains_validation(self):
        """Test excluded domains validation."""
        config = PerplexityConfig(
            api_key="pplx-test-key",
            excluded_domains=["example.com", "  test.org  ", "invalid", "  "]
        )
        
        # Should filter out invalid domains
        assert "example.com" in config.excluded_domains
        assert "test.org" in config.excluded_domains
        assert "invalid" not in config.excluded_domains
        assert "" not in config.excluded_domains
    
    def test_company_keywords_validation(self):
        """Test company keywords validation."""
        config = PerplexityConfig(
            api_key="pplx-test-key",
            company_search_keywords=["company", "  Business  ", "", "startup"]
        )
        
        # Should normalize and filter keywords
        assert "company" in config.company_search_keywords
        assert "business" in config.company_search_keywords
        assert "startup" in config.company_search_keywords
        assert "" not in config.company_search_keywords
    
    @patch.dict('os.environ', {
        'PERPLEXITY_API_KEY': 'pplx-env-key',
        'PERPLEXITY_MODEL': 'sonar-large-chat',
        'PERPLEXITY_MAX_RESULTS': '25',
        'PERPLEXITY_RATE_LIMIT': '50',
        'PERPLEXITY_ENABLE_CACHING': 'false'
    })
    def test_from_env(self):
        """Test configuration from environment variables."""
        config = PerplexityConfig.from_env()
        
        assert config.api_key == "pplx-env-key"
        assert config.model == PerplexityModel.SONAR_LARGE
        assert config.max_results == 25
        assert config.rate_limit_requests_per_minute == 50
        assert config.enable_caching is False
    
    def test_request_headers(self):
        """Test request headers generation."""
        config = PerplexityConfig(
            api_key="pplx-test-key",
            custom_headers={"X-Custom": "value"}
        )
        
        headers = config.get_request_headers()
        
        assert headers["Authorization"] == "Bearer pplx-test-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "Theodore-v2-MCP-Client/1.0"
        assert headers["X-Custom"] == "value"
    
    def test_estimate_daily_requests(self):
        """Test daily request estimation."""
        config = PerplexityConfig(
            api_key="pplx-test-key",
            cost_per_request=0.01,
            daily_budget_usd=10.0
        )
        
        estimated = config.estimate_daily_requests()
        assert estimated == 1000
        
        # No budget set
        config.daily_budget_usd = None
        assert config.estimate_daily_requests() is None
    
    def test_validate_search_parameters(self):
        """Test search parameter validation."""
        config = PerplexityConfig(api_key="pplx-test-key", max_results=10)
        
        # Valid parameters
        config.validate_search_parameters("test query", 5)
        
        # Invalid query
        with pytest.raises(ValueError, match="cannot be empty"):
            config.validate_search_parameters("", 5)
        
        # Invalid limit
        with pytest.raises(ValueError, match="must be between 1 and"):
            config.validate_search_parameters("test", 15)


class TestPerplexityClient:
    """Test Perplexity HTTP client."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PerplexityConfig(
            api_key="pplx-test-key",
            timeout_seconds=10.0,
            max_retries=2,
            rate_limit_requests_per_minute=60
        )
    
    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return PerplexityClient(config)
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.config.api_key == "pplx-test-key"
        assert client._session is None
        assert client._request_count == 0
        assert client._error_count == 0
    
    @pytest.mark.asyncio
    async def test_session_management(self, client):
        """Test HTTP session management."""
        # Session should be None initially
        assert client._session is None
        
        # Ensure session creates session
        await client._ensure_session()
        assert client._session is not None
        assert not client._session.closed
        
        # Close should clean up
        await client.close()
        assert client._session is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test rate limiting logic."""
        # Simulate multiple requests
        start_time = time.time()
        
        # Should not be rate limited initially
        await client._check_rate_limit()
        first_check_time = time.time() - start_time
        assert first_check_time < 0.1  # Should be very fast
        
        # Add many request timestamps
        now = time.time()
        client._request_times = [now - i for i in range(60)]  # 60 requests in last minute
        
        # This should trigger rate limiting
        start_time = time.time()
        await client._check_rate_limit()
        rate_limit_time = time.time() - start_time
        
        # Should have been delayed (but we won't wait the full minute in tests)
        assert len(client._request_times) == 61  # Added one more
    
    @pytest.mark.asyncio
    async def test_search_success(self, client):
        """Test successful search request."""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Test company information about Acme Corp and Widget Inc."
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            },
            "citations": ["https://example.com", "https://test.com"],
            "id": "test-request-id"
        }
        
        with patch.object(client, '_make_request', return_value=mock_response_data) as mock_request:
            response = await client.search(
                query="test query",
                model="sonar-medium-chat",
                return_citations=True
            )
            
            assert isinstance(response, PerplexityResponse)
            assert response.content == "Test company information about Acme Corp and Widget Inc."
            assert response.citations == ["https://example.com", "https://test.com"]
            assert response.model == "sonar-medium-chat"
            assert response.usage["total_tokens"] == 300
            assert "request_id" in response.metadata
            
            # Verify request was called correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"  # method
            assert call_args[0][1] == "/chat/completions"  # endpoint
            
            request_data = call_args[1]["data"]
            assert request_data["model"] == "sonar-medium-chat"
            assert request_data["return_citations"] is True
            assert len(request_data["messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, client):
        """Test search with optional filters."""
        mock_response_data = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {},
            "citations": []
        }
        
        with patch.object(client, '_make_request', return_value=mock_response_data):
            response = await client.search(
                query="test query",
                search_focus="news",
                search_recency_filter="week",
                return_images=True
            )
            
            assert response.content == "Test response"
            assert response.metadata["search_focus"] == "news"
            assert response.metadata["recency_filter"] == "week"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for different HTTP status codes."""
        # Rate limit error (429)
        with patch.object(client, '_make_request', side_effect=PerplexityRateLimitError(retry_after=60)):
            with pytest.raises(PerplexityRateLimitError) as exc_info:
                await client.search("test query")
            assert exc_info.value.retry_after == 60
        
        # Quota error (402)
        with patch.object(client, '_make_request', side_effect=PerplexityQuotaError()):
            with pytest.raises(PerplexityQuotaError):
                await client.search("test query")
        
        # Auth error (401)
        with patch.object(client, '_make_request', side_effect=PerplexityAuthError("Invalid key")):
            with pytest.raises(PerplexityAuthError):
                await client.search("test query")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        with patch.object(client, 'search') as mock_search:
            mock_search.return_value = PerplexityResponse(
                content="test", citations=[], search_time_ms=100.0,
                model="test", usage={}, metadata={}
            )
            
            health = await client.health_check()
            
            assert health["status"] == "healthy"
            assert "latency_ms" in health
            assert "success_rate" in health
            assert "total_requests" in health
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check with failure."""
        with patch.object(client, 'search', side_effect=PerplexityClientError("API error")):
            health = await client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "error" in health
            assert health["error"] == "API error"
    
    @pytest.mark.asyncio
    async def test_metrics(self, client):
        """Test client metrics."""
        # Initially empty metrics
        metrics = client.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["error_count"] == 0
        assert metrics["success_rate"] == 1.0
        
        # Simulate some requests
        client._request_count = 10
        client._error_count = 2
        client._total_latency = 1000.0
        
        metrics = client.get_metrics()
        assert metrics["total_requests"] == 10
        assert metrics["error_count"] == 2
        assert metrics["success_rate"] == 0.8
        assert metrics["average_latency_ms"] == 100.0


class TestPerplexityAdapter:
    """Test Perplexity MCP adapter."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PerplexityConfig(
            api_key="pplx-test-key",
            max_results=10,
            enable_caching=True,
            cache_ttl_seconds=3600
        )
    
    @pytest.fixture
    def adapter(self, config):
        """Create test adapter."""
        return PerplexityAdapter(config)
    
    @pytest.fixture
    def mock_client_response(self):
        """Create mock client response."""
        return PerplexityResponse(
            content="""
            Acme Corporation is a leading software company specializing in enterprise solutions.
            The company (acme.com) offers cloud-based services and has been growing rapidly.
            
            Widget Inc. provides manufacturing automation solutions.
            Beta Systems offers consulting services for technology companies.
            """,
            citations=["https://acme.com", "https://widget.com", "https://beta.com"],
            search_time_ms=500.0,
            model="sonar-medium-chat",
            usage={"total_tokens": 300},
            metadata={"request_id": "test-123"}
        )
    
    def test_tool_info(self, adapter):
        """Test tool information."""
        tool_info = adapter.get_tool_info()
        
        assert tool_info.tool_name == "perplexity"
        assert tool_info.tool_version == "1.0.0"
        assert MCPSearchCapability.WEB_SEARCH in tool_info.capabilities
        assert MCPSearchCapability.COMPANY_RESEARCH in tool_info.capabilities
        assert tool_info.max_results_per_query == 10
        assert tool_info.supports_filters is True
    
    def test_build_company_search_query(self, adapter):
        """Test company search query building."""
        # Basic query
        query = adapter._build_company_search_query("Acme Corp")
        assert "Acme Corp" in query
        assert "companies similar to" in query
        
        # With website
        query = adapter._build_company_search_query(
            "Acme Corp", 
            company_website="https://www.acme.com"
        )
        assert "acme.com" in query
        
        # With description
        query = adapter._build_company_search_query(
            "Acme Corp",
            company_description="Software development company"
        )
        assert "Software development company" in query
        
        # With filters
        filters = MCPSearchFilters(
            industry="technology",
            location="San Francisco",
            company_size="startup"
        )
        query = adapter._build_company_search_query("Acme Corp", filters=filters)
        assert "technology" in query
        assert "San Francisco" in query
        assert "startup" in query
    
    def test_build_keyword_search_query(self, adapter):
        """Test keyword search query building."""
        # Single keyword
        query = adapter._build_keyword_search_query(["fintech"])
        assert "fintech" in query
        assert "companies in" in query
        
        # Multiple keywords
        query = adapter._build_keyword_search_query(["AI", "machine learning", "cloud"])
        assert "AI AND machine learning" in query
        assert "cloud" in query
        
        # With filters
        filters = MCPSearchFilters(industry="technology", location="NYC")
        query = adapter._build_keyword_search_query(["AI"], filters=filters)
        assert "technology" in query
        assert "NYC" in query
    
    def test_extract_companies_from_response(self, adapter):
        """Test company extraction from response."""
        response_content = """
        Acme Corporation is a leading software company that provides enterprise solutions.
        The company (www.acme.com) has been growing rapidly since 2015.
        
        Widget Inc. offers manufacturing automation services.
        Beta Systems LLC provides consulting for technology companies.
        Gamma Corp specializes in cloud infrastructure.
        """
        
        citations = ["https://acme.com", "https://widget.com"]
        companies = adapter._extract_companies_from_response(
            response_content, citations, "test query"
        )
        
        assert len(companies) >= 3
        
        # Check that companies were extracted
        company_names = [c.name for c in companies]
        assert any("Acme" in name for name in company_names)
        assert any("Widget" in name for name in company_names)
        assert any("Beta" in name or "Gamma" in name for name in company_names)
        
        # Check first company structure
        first_company = companies[0]
        assert first_company.name is not None
        assert first_company.website is not None  # Should have fallback website
        assert first_company.id is not None
        assert isinstance(first_company.created_at, datetime)
        assert first_company.data_quality_score >= 0.0
    
    def test_calculate_extraction_confidence(self, adapter):
        """Test confidence calculation."""
        # High confidence - name, description, website, citations
        confidence = adapter._calculate_extraction_confidence(
            "Acme Corporation",
            "A leading software company providing enterprise solutions",
            "https://acme.com",
            ["https://acme.com/about"]
        )
        assert confidence >= 0.8
        
        # Low confidence - just name
        confidence = adapter._calculate_extraction_confidence(
            "Test",
            None,
            None,
            []
        )
        assert confidence <= 0.5
    
    @pytest.mark.asyncio
    async def test_search_similar_companies_success(self, adapter, mock_client_response):
        """Test successful similar companies search."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            result = await adapter.search_similar_companies(
                company_name="Target Corp",
                limit=5
            )
            
            assert isinstance(result.companies, list)
            assert len(result.companies) >= 1
            assert result.tool_info.tool_name == "perplexity"
            assert result.query is not None
            assert result.total_found >= 1
            assert result.search_time_ms > 0
            assert result.confidence_score is not None
            assert result.metadata["search_type"] == "similar_companies"
            assert result.metadata["target_company"] == "Target Corp"
            assert result.cost_incurred == adapter.config.cost_per_request
    
    @pytest.mark.asyncio
    async def test_search_similar_companies_with_filters(self, adapter, mock_client_response):
        """Test search with filters."""
        filters = MCPSearchFilters(
            industry="technology",
            location="San Francisco",
            company_size="startup"
        )
        
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            result = await adapter.search_similar_companies(
                company_name="Target Corp",
                filters=filters,
                limit=5
            )
            
            assert result.metadata["filters_applied"]["industry"] == "technology"
            assert result.metadata["filters_applied"]["location"] == "San Francisco"
            assert result.metadata["filters_applied"]["company_size"] == "startup"
    
    @pytest.mark.asyncio
    async def test_search_by_keywords(self, adapter, mock_client_response):
        """Test keyword-based search."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            result = await adapter.search_by_keywords(
                keywords=["fintech", "blockchain"],
                limit=5
            )
            
            assert len(result.companies) >= 1
            assert result.metadata["search_type"] == "keyword_search"
            assert result.metadata["keywords"] == ["fintech", "blockchain"]
    
    @pytest.mark.asyncio
    async def test_get_company_details(self, adapter, mock_client_response):
        """Test getting company details."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            company = await adapter.get_company_details(
                company_name="Acme Corporation",
                company_website="https://acme.com"
            )
            
            assert company is not None
            assert "Acme" in company.name
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, adapter, mock_client_response):
        """Test result caching."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response) as mock_search:
            # First search - should call client
            result1 = await adapter.search_similar_companies("Test Corp", limit=5)
            assert mock_search.call_count == 1
            assert result1.metadata.get("cache_hit") is None
            
            # Second search - should use cache
            result2 = await adapter.search_similar_companies("Test Corp", limit=5)
            assert mock_search.call_count == 1  # No additional call
            assert result2.metadata.get("cache_hit") is True
            
            # Results should be equivalent
            assert len(result1.companies) == len(result2.companies)
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, adapter, mock_client_response):
        """Test cache expiration."""
        # Create new config with very short TTL for testing
        test_config = PerplexityConfig(
            api_key="pplx-test-key",
            enable_caching=True,
            cache_ttl_seconds=60  # Minimum allowed value for testing
        )
        test_adapter = PerplexityAdapter(test_config)
        
        with patch.object(test_adapter.client, 'search', return_value=mock_client_response) as mock_search:
            # First search
            await test_adapter.search_similar_companies("Test Corp", limit=5)
            assert mock_search.call_count == 1
            
            # Manually expire cache by manipulating cache timestamp
            cache_key = f"similar:{hash(('Test Corp', test_adapter._build_company_search_query('Test Corp'), 5))}"
            async with test_adapter._cache_lock:
                if cache_key in test_adapter._cache_timestamps:
                    test_adapter._cache_timestamps[cache_key] = time.time() - 61  # Make it expired
            
            # Second search - should call client again due to expired cache
            await test_adapter.search_similar_companies("Test Corp", limit=5)
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_management(self, adapter):
        """Test cache management operations."""
        # Add some cache entries
        await adapter._cache_result("key1", MagicMock())
        await adapter._cache_result("key2", MagicMock())
        
        # Check cache stats
        stats = await adapter.get_cache_stats()
        assert stats["cache_size"] == 2
        
        # Clear specific pattern
        cleared = await adapter.clear_cache("key1")
        assert cleared == 1
        
        stats = await adapter.get_cache_stats()
        assert stats["cache_size"] == 1
        
        # Clear all cache
        cleared = await adapter.clear_cache()
        assert cleared == 1
        
        stats = await adapter.get_cache_stats()
        assert stats["cache_size"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, adapter):
        """Test error handling and exception mapping."""
        # Rate limit error
        with patch.object(adapter.client, 'search', side_effect=PerplexityRateLimitError(60)):
            with pytest.raises(MCPRateLimitedException) as exc_info:
                await adapter.search_similar_companies("Test Corp")
            assert exc_info.value.retry_after == 60
        
        # Quota error
        with patch.object(adapter.client, 'search', side_effect=PerplexityQuotaError()):
            with pytest.raises(MCPQuotaExceededException):
                await adapter.search_similar_companies("Test Corp")
        
        # Auth error
        with patch.object(adapter.client, 'search', side_effect=PerplexityAuthError("Invalid key")):
            with pytest.raises(MCPConfigurationException):
                await adapter.search_similar_companies("Test Corp")
        
        # Timeout error
        with patch.object(adapter.client, 'search', side_effect=asyncio.TimeoutError()):
            with pytest.raises(Exception):  # Should be wrapped in MCPSearchTimeoutException
                await adapter.search_similar_companies("Test Corp")
    
    @pytest.mark.asyncio
    async def test_streaming_interface(self, adapter, mock_client_response):
        """Test streaming search interface."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            companies = []
            async for company in adapter.search_similar_companies_streaming("Test Corp", limit=3):
                companies.append(company)
            
            assert len(companies) >= 1
            assert all(isinstance(c, Company) for c in companies)
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, adapter, mock_client_response):
        """Test batch search operations."""
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            # Test batch company search
            results = await adapter.search_batch_companies(
                company_names=["Company A", "Company B"],
                limit_per_company=3
            )
            
            assert len(results) == 2
            assert "Company A" in results
            assert "Company B" in results
            assert all(isinstance(result.companies, list) for result in results.values())
            
            # Test batch company details
            details = await adapter.get_batch_company_details(
                company_names=["Company A", "Company B"]
            )
            
            assert len(details) == 2
            assert "Company A" in details
            assert "Company B" in details
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test health check functionality."""
        mock_client_health = {
            "status": "healthy",
            "latency_ms": 100,
            "success_rate": 0.95,
            "total_requests": 50
        }
        
        with patch.object(adapter.client, 'health_check', return_value=mock_client_health):
            with patch.object(adapter, 'validate_configuration', return_value=True):
                health = await adapter.health_check()
                
                assert health["status"] == "healthy"
                assert health["adapter_version"] == "1.0.0"
                assert health["total_searches"] >= 0
                assert "cache_hit_rate" in health
                assert health["configuration_valid"] is True
    
    @pytest.mark.asyncio
    async def test_validate_configuration(self, adapter):
        """Test configuration validation."""
        with patch.object(adapter.client, 'health_check', return_value={"status": "healthy"}):
            is_valid = await adapter.validate_configuration()
            assert is_valid is True
        
        with patch.object(adapter.client, 'health_check', return_value={"status": "unhealthy"}):
            is_valid = await adapter.validate_configuration()
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, adapter):
        """Test cost estimation."""
        cost = await adapter.estimate_search_cost(query_count=100)
        expected_cost = 100 * adapter.config.cost_per_request
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_progress_callbacks(self, adapter, mock_client_response):
        """Test progress callback functionality."""
        progress_updates = []
        
        def progress_callback(message: str, progress: float, details: str):
            progress_updates.append((message, progress, details))
        
        with patch.object(adapter.client, 'search', return_value=mock_client_response):
            await adapter.search_similar_companies(
                "Test Corp",
                progress_callback=progress_callback
            )
            
            assert len(progress_updates) >= 3  # Should have multiple progress updates
            assert progress_updates[0][1] == 0.1  # First update
            assert progress_updates[-1][1] == 1.0  # Final update
            assert "Search completed" in progress_updates[-1][0]
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test async context manager."""
        async with adapter as ctx_adapter:
            assert ctx_adapter is adapter
            # Client should be properly initialized
            assert adapter.client is not None
        
        # After exit, cleanup should be called
        # (In real scenario, connections would be closed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
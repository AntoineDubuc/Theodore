"""
Unit tests for Tavily MCP Search Tool Adapter.

Comprehensive test suite covering all aspects of the Tavily adapter
with mocked responses and edge case handling.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Test imports
from src.infrastructure.adapters.mcp.tavily import (
    TavilyAdapter,
    TavilyConfig, 
    TavilyClient,
    TavilyResponse,
    TavilyClientError,
    TavilyRateLimitError,
    TavilyQuotaError,
    TavilyAuthError,
    TavilySearchDepth,
    TavilySearchType,
    create_tavily_adapter,
    get_tool_info
)

from src.core.ports.mcp_search_tool import (
    MCPSearchResult,
    MCPSearchFilters,
    MCPRateLimitedException,
    MCPQuotaExceededException,
    MCPConfigurationException,
    MCPSearchTimeoutException,
    MCPSearchException
)

from src.core.domain.entities.company import Company


@pytest.fixture
def tavily_config():
    """Create a test Tavily configuration."""
    return TavilyConfig(
        api_key="tvly-test-key-12345",
        search_depth=TavilySearchDepth.BASIC,
        max_results=10,
        timeout_seconds=30.0,
        rate_limit_requests_per_minute=100,
        enable_caching=True,
        cache_ttl_seconds=3600,
        include_raw_content=True,
        cost_per_request=0.001
    )


@pytest.fixture
def mock_tavily_response():
    """Create a mock Tavily API response."""
    return {
        "query": "companies similar to OpenAI",
        "answer": "Several companies are developing AI technology similar to OpenAI, including Anthropic, Cohere, and AI21 Labs.",
        "results": [
            {
                "title": "Anthropic - AI Safety Company",
                "url": "https://anthropic.com",
                "content": "Anthropic is an AI safety company founded by former OpenAI researchers. The company focuses on developing safe, beneficial AI systems.",
                "score": 0.95,
                "published_date": "2024-01-15"
            },
            {
                "title": "Cohere - Natural Language AI Platform", 
                "url": "https://cohere.ai",
                "content": "Cohere provides natural language processing APIs for businesses. Founded by former Google researchers.",
                "score": 0.88,
                "published_date": "2024-01-10"
            },
            {
                "title": "AI21 Labs - Language Model Company",
                "url": "https://ai21.com", 
                "content": "AI21 Labs develops large language models and natural language understanding technology for enterprise applications.",
                "score": 0.82,
                "published_date": "2024-01-05"
            }
        ],
        "images": [],
        "follow_up_questions": ["What are the main differences between these AI companies?"],
        "request_id": "test-request-123"
    }


@pytest.fixture
def mock_client(mock_tavily_response):
    """Create a mock Tavily client."""
    client = AsyncMock(spec=TavilyClient)
    
    # Mock search method
    client.search.return_value = TavilyResponse(
        query=mock_tavily_response["query"],
        answer=mock_tavily_response["answer"],
        results=mock_tavily_response["results"],
        response_time=0.5,
        images=mock_tavily_response["images"],
        follow_up_questions=mock_tavily_response["follow_up_questions"],
        search_depth="basic",
        request_id=mock_tavily_response["request_id"],
        search_metadata={"timestamp": "2024-01-01T00:00:00Z"}
    )
    
    # Mock health check
    client.health_check.return_value = {
        "status": "healthy",
        "latency_ms": 250.0,
        "api_accessible": True,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # Mock context manager
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    
    return client


@pytest.fixture 
def tavily_adapter(tavily_config, mock_client):
    """Create a Tavily adapter with mocked client."""
    adapter = TavilyAdapter(tavily_config)
    adapter.client = mock_client
    return adapter


class TestTavilyConfig:
    """Test Tavily configuration validation and creation."""
    
    def test_valid_config_creation(self):
        """Test creating a valid configuration."""
        config = TavilyConfig(
            api_key="tvly-valid-key",
            search_depth=TavilySearchDepth.ADVANCED,
            max_results=20,
            timeout_seconds=45.0
        )
        
        assert config.api_key == "tvly-valid-key"
        assert config.search_depth == TavilySearchDepth.ADVANCED
        assert config.max_results == 20
        assert config.timeout_seconds == 45.0
    
    def test_api_key_validation(self):
        """Test API key validation."""
        # Valid key
        config = TavilyConfig(api_key="tvly-valid-key-123")
        assert config.api_key == "tvly-valid-key-123"
        
        # Invalid keys
        with pytest.raises(ValueError, match="API key cannot be empty"):
            TavilyConfig(api_key="")
        
        with pytest.raises(ValueError, match="must start with 'tvly-'"):
            TavilyConfig(api_key="invalid-key")
    
    def test_domain_validation(self):
        """Test domain list validation and normalization."""
        config = TavilyConfig(
            api_key="tvly-test",
            include_domains=["https://example.com", "www.test.org", "company.co.uk"],
            exclude_domains=["http://spam.net", "bad-site.com"]
        )
        
        assert "example.com" in config.include_domains
        assert "test.org" in config.include_domains
        assert "company.co.uk" in config.include_domains
        assert "spam.net" in config.exclude_domains
        assert "bad-site.com" in config.exclude_domains
    
    def test_from_env_creation(self):
        """Test creating configuration from environment variables."""
        with patch.dict('os.environ', {
            'TAVILY_API_KEY': 'tvly-env-key',
            'TAVILY_SEARCH_DEPTH': 'advanced',
            'TAVILY_MAX_RESULTS': '15',
            'TAVILY_TIMEOUT': '45.0'
        }):
            config = TavilyConfig.from_env()
            
            assert config.api_key == "tvly-env-key"
            assert config.search_depth == TavilySearchDepth.ADVANCED
            assert config.max_results == 15
            assert config.timeout_seconds == 45.0
    
    def test_request_headers(self):
        """Test request header generation."""
        config = TavilyConfig(
            api_key="tvly-test-key",
            custom_headers={"X-Custom": "value"}
        )
        
        headers = config.get_request_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer tvly-test-key"
        assert headers["X-Custom"] == "value"
        assert "User-Agent" in headers
    
    def test_search_params_generation(self):
        """Test search parameters generation."""
        config = TavilyConfig(
            api_key="tvly-test",
            search_depth=TavilySearchDepth.ADVANCED,
            max_results=15,
            include_domains=["example.com"],
            exclude_domains=["spam.com"],
            days_back=7
        )
        
        params = config.get_search_params()
        
        assert params["search_depth"] == "advanced"
        assert params["max_results"] == 15
        assert params["include_domains"] == ["example.com"]
        assert params["exclude_domains"] == ["spam.com"]
        assert params["days"] == 7


class TestTavilyClient:
    """Test Tavily HTTP client functionality."""
    
    @pytest.fixture
    def client_config(self):
        """Client configuration for testing."""
        return TavilyConfig(
            api_key="tvly-test-key",
            timeout_seconds=30.0,
            rate_limit_requests_per_minute=60
        )
    
    def test_client_initialization(self, client_config):
        """Test client initialization."""
        client = TavilyClient(client_config)
        
        assert client.config == client_config
        assert client._session is None
        assert client._request_count == 0
        assert client._error_count == 0
    
    @pytest.mark.asyncio
    async def test_search_success(self, client_config, mock_tavily_response):
        """Test successful search operation."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Mock HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_tavily_response
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            client = TavilyClient(client_config)
            
            async with client:
                result = await client.search("test query", max_results=5)
                
                assert isinstance(result, TavilyResponse)
                assert result.query == "test query"
                assert result.answer == mock_tavily_response["answer"]
                assert len(result.results) == 3
                assert result.search_depth == "basic"
    
    @pytest.mark.asyncio
    async def test_search_authentication_error(self, client_config):
        """Test authentication error handling."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 401
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            client = TavilyClient(client_config)
            
            async with client:
                with pytest.raises(TavilyAuthError):
                    await client.search("test query")
    
    @pytest.mark.asyncio
    async def test_search_rate_limit_error(self, client_config):
        """Test rate limit error handling."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {"Retry-After": "60"}
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            client = TavilyClient(client_config)
            
            async with client:
                with pytest.raises(TavilyRateLimitError) as exc_info:
                    await client.search("test query")
                
                assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_search_quota_error(self, client_config):
        """Test quota exceeded error handling."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 402
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            client = TavilyClient(client_config)
            
            async with client:
                with pytest.raises(TavilyQuotaError):
                    await client.search("test query")
    
    @pytest.mark.asyncio
    async def test_health_check(self, client_config, mock_tavily_response):
        """Test health check functionality."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "query": "test health check",
                "results": [{"title": "test", "url": "http://test.com", "content": "test"}],
                "answer": None,
                "images": [],
                "follow_up_questions": []
            }
            
            mock_session = AsyncMock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            client = TavilyClient(client_config)
            
            async with client:
                health = await client.health_check()
                
                assert health["status"] == "healthy"
                assert "latency_ms" in health
                assert health["api_accessible"] is True


class TestTavilyAdapter:
    """Test Tavily adapter implementation."""
    
    def test_adapter_initialization(self, tavily_config):
        """Test adapter initialization."""
        adapter = TavilyAdapter(tavily_config)
        
        assert adapter.config == tavily_config
        assert adapter._search_count == 0
        assert adapter._cache_hits == 0
        assert adapter._cache_misses == 0
        
        tool_info = adapter.get_tool_info()
        assert tool_info.tool_name == "tavily"
        assert tool_info.tool_version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_search_similar_companies_success(self, tavily_adapter, mock_client):
        """Test successful similar company search."""
        result = await tavily_adapter.search_similar_companies(
            company_name="OpenAI",
            limit=10
        )
        
        assert isinstance(result, MCPSearchResult)
        assert len(result.companies) == 3
        assert result.query
        assert result.total_found == 3
        assert result.search_time_ms > 0
        
        # Check first company
        first_company = result.companies[0]
        assert first_company.name == "Anthropic"
        assert first_company.website == "https://anthropic.com"
        assert "AI safety company" in first_company.description
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, tavily_adapter, mock_client):
        """Test search with filters applied."""
        filters = MCPSearchFilters(
            industry="artificial intelligence",
            location="San Francisco",
            keywords=["machine learning", "nlp"]
        )
        
        result = await tavily_adapter.search_similar_companies(
            company_name="OpenAI",
            filters=filters,
            limit=5
        )
        
        assert isinstance(result, MCPSearchResult)
        assert result.metadata["filters_applied"] == filters.to_dict()
        
        # Verify client was called with correct parameters
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert "industry artificial intelligence" in call_args[1]["query"]
    
    @pytest.mark.asyncio
    async def test_search_by_keywords(self, tavily_adapter, mock_client):
        """Test keyword-based search."""
        keywords = ["artificial intelligence", "machine learning", "nlp"]
        
        result = await tavily_adapter.search_by_keywords(
            keywords=keywords,
            limit=10
        )
        
        assert isinstance(result, MCPSearchResult)
        assert result.metadata["search_type"] == "keyword_search"
        assert result.metadata["keywords"] == keywords
        
        # Verify query construction
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        query = call_args[1]["query"]
        assert "artificial intelligence" in query
        assert "companies" in query.lower()
    
    @pytest.mark.asyncio
    async def test_get_company_details(self, tavily_adapter, mock_client):
        """Test getting detailed company information."""
        company = await tavily_adapter.get_company_details(
            company_name="Anthropic",
            company_website="https://anthropic.com",
            requested_fields=["funding", "employees", "products"]
        )
        
        assert company is not None
        assert company.name == "Anthropic"
        assert company.website == "https://anthropic.com"
        
        # Verify client was called with detailed query
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        query = call_args[1]["query"]
        assert "detailed information" in query
        assert "Anthropic" in query
        assert "funding employees products" in query
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, tavily_adapter, mock_client):
        """Test result caching."""
        # First search - should cache result
        result1 = await tavily_adapter.search_similar_companies("OpenAI", limit=5)
        
        # Second identical search - should use cache
        result2 = await tavily_adapter.search_similar_companies("OpenAI", limit=5)
        
        # Client should only be called once
        assert mock_client.search.call_count == 1
        
        # Results should be identical
        assert len(result1.companies) == len(result2.companies)
        assert result2.metadata.get("cache_hit") is True
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, tavily_adapter, mock_client):
        """Test cache expiration functionality."""
        # Create a separate test config with short cache TTL for testing
        test_config = TavilyConfig(
            api_key="tvly-test",
            cache_ttl_seconds=60,  # Use minimum valid value
            enable_caching=True
        )
        test_adapter = TavilyAdapter(test_config)
        test_adapter.client = mock_client
        
        # Search and cache result
        await test_adapter.search_similar_companies("OpenAI", limit=5)
        
        # Simulate cache expiration by manipulating timestamp
        cache_key = list(test_adapter._cache_timestamps.keys())[0]
        test_adapter._cache_timestamps[cache_key] = time.time() - 120  # 2 minutes ago
        
        # Search again - should not use expired cache
        await test_adapter.search_similar_companies("OpenAI", limit=5)
        
        # Client should be called twice (cache miss)
        assert mock_client.search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_streaming_search(self, tavily_adapter, mock_client):
        """Test streaming search functionality."""
        companies = []
        
        async for company in tavily_adapter.search_similar_companies_streaming(
            company_name="OpenAI",
            limit=3
        ):
            companies.append(company)
        
        assert len(companies) == 3
        assert all(isinstance(c, Company) for c in companies)
        assert companies[0].name == "Anthropic"
    
    @pytest.mark.asyncio
    async def test_batch_search(self, tavily_adapter, mock_client):
        """Test batch company search."""
        company_names = ["OpenAI", "Anthropic", "Cohere"]
        
        results = await tavily_adapter.search_batch_companies(
            company_names=company_names,
            limit_per_company=5
        )
        
        assert len(results) == 3
        assert "OpenAI" in results
        assert "Anthropic" in results
        assert "Cohere" in results
        
        # Each result should be an MCPSearchResult
        for company_name, result in results.items():
            assert isinstance(result, MCPSearchResult)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tavily_adapter, mock_client):
        """Test error handling and exception mapping."""
        # Test rate limit error
        mock_client.search.side_effect = TavilyRateLimitError("Rate limited", 60)
        
        with pytest.raises(MCPRateLimitedException) as exc_info:
            await tavily_adapter.search_similar_companies("OpenAI")
        
        assert exc_info.value.tool_name == "tavily"
        assert exc_info.value.retry_after == 60
        
        # Test quota error
        mock_client.search.side_effect = TavilyQuotaError("Quota exceeded")
        
        with pytest.raises(MCPQuotaExceededException):
            await tavily_adapter.search_similar_companies("OpenAI")
        
        # Test auth error
        mock_client.search.side_effect = TavilyAuthError("Invalid API key")
        
        with pytest.raises(MCPConfigurationException):
            await tavily_adapter.search_similar_companies("OpenAI")
        
        # Test timeout error
        mock_client.search.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(MCPSearchTimeoutException):
            await tavily_adapter.search_similar_companies("OpenAI")
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, tavily_adapter):
        """Test cost estimation functionality."""
        cost = await tavily_adapter.estimate_search_cost(
            query_count=100,
            average_results_per_query=10
        )
        
        assert cost == 0.1  # 100 * 0.001
    
    @pytest.mark.asyncio
    async def test_health_check(self, tavily_adapter, mock_client):
        """Test adapter health check."""
        health = await tavily_adapter.health_check()
        
        assert health["status"] == "healthy"
        assert "adapter_version" in health
        assert "total_searches" in health
        assert "cache_hit_rate" in health
        assert "configuration_valid" in health
    
    @pytest.mark.asyncio
    async def test_cache_management(self, tavily_adapter):
        """Test cache management operations."""
        # Add some cached data first
        await tavily_adapter.search_similar_companies("OpenAI", limit=5)
        
        # Get cache stats
        stats = await tavily_adapter.get_cache_stats()
        assert stats["cache_size"] > 0
        assert stats["caching_enabled"] is True
        
        # Clear cache
        cleared = await tavily_adapter.clear_cache()
        assert cleared > 0
        
        # Verify cache is empty
        stats_after = await tavily_adapter.get_cache_stats()
        assert stats_after["cache_size"] == 0


class TestFactoryFunctions:
    """Test factory functions and utilities."""
    
    def test_create_tavily_adapter_from_env(self):
        """Test creating adapter from environment variables."""
        with patch.dict('os.environ', {
            'TAVILY_API_KEY': 'tvly-factory-test',
            'TAVILY_MAX_RESULTS': '15'
        }):
            adapter = create_tavily_adapter()
            
            assert adapter.config.api_key == "tvly-factory-test"
            assert adapter.config.max_results == 15
    
    def test_create_tavily_adapter_with_config(self):
        """Test creating adapter with explicit configuration."""
        config_dict = {
            "api_key": "tvly-explicit-config",
            "search_depth": "advanced",
            "max_results": 25
        }
        
        adapter = create_tavily_adapter(config_dict)
        
        assert adapter.config.api_key == "tvly-explicit-config"
        assert adapter.config.search_depth == TavilySearchDepth.ADVANCED
        assert adapter.config.max_results == 25
    
    def test_create_tavily_adapter_with_kwargs(self):
        """Test creating adapter with keyword arguments."""
        adapter = create_tavily_adapter(
            api_key="tvly-kwargs-test",
            timeout_seconds=45.0,
            enable_caching=False
        )
        
        assert adapter.config.api_key == "tvly-kwargs-test"
        assert adapter.config.timeout_seconds == 45.0
        assert adapter.config.enable_caching is False
    
    def test_get_tool_info(self):
        """Test getting tool information."""
        tool_info = get_tool_info()
        
        assert tool_info["name"] == "tavily"
        assert tool_info["version"] == "1.0.0"
        assert "capabilities" in tool_info
        assert "features" in tool_info
        assert "config_schema" in tool_info
        
        # Verify capabilities
        assert "web_search" in tool_info["capabilities"]
        assert "company_research" in tool_info["capabilities"]
        
        # Verify features
        assert "domain_filtering" in tool_info["features"]
        assert "caching" in tool_info["features"]


class TestCompanyExtraction:
    """Test company data extraction from search results."""
    
    @pytest.fixture
    def extraction_test_response(self):
        """Mock response with various company mention patterns."""
        return {
            "query": "AI companies",
            "answer": "Leading AI companies include Anthropic, founded by former OpenAI researchers, and Cohere Inc. which provides NLP APIs.",
            "results": [
                {
                    "title": "Anthropic - AI Safety Research Company",
                    "url": "https://anthropic.com",
                    "content": "Anthropic is a company focused on AI safety research. The company was founded in 2021 by Dario Amodei and Daniela Amodei.",
                    "score": 0.95
                },
                {
                    "title": "Enterprise AI Solutions by Cohere",
                    "url": "https://cohere.ai/enterprise",
                    "content": "Cohere provides enterprise-grade natural language processing APIs. The company offers powerful language models for business applications.",
                    "score": 0.87
                }
            ],
            "images": [],
            "follow_up_questions": []
        }
    
    def test_company_name_extraction(self, tavily_config, extraction_test_response):
        """Test extraction of company names from content."""
        adapter = TavilyAdapter(tavily_config)
        
        # Test various extraction patterns
        test_content = "Anthropic Inc. is a leading AI company. Google LLC provides search services. Microsoft Corporation offers cloud computing."
        
        names = adapter._extract_company_names("Test Title", test_content)
        
        assert "Anthropic" in names
        assert "Google" in names  
        assert "Microsoft" in names
    
    def test_website_extraction(self, tavily_config):
        """Test website extraction from URLs and content."""
        adapter = TavilyAdapter(tavily_config)
        
        # Direct URL extraction
        website = adapter._extract_website(
            "https://anthropic.com",
            "Some content",
            "Anthropic"
        )
        assert website == "https://anthropic.com"
        
        # Website from content
        website = adapter._extract_website(
            "",
            "Visit our website at anthropic.com for more information",
            "Anthropic"
        )
        assert website == "https://anthropic.com"
    
    def test_company_description_extraction(self, tavily_config):
        """Test extraction of company descriptions."""
        adapter = TavilyAdapter(tavily_config)
        
        content = "Anthropic is an AI safety company founded by former OpenAI researchers. The company focuses on developing safe AI systems. Anthropic has raised significant funding."
        
        description = adapter._extract_company_description(content, "Anthropic")
        
        assert "AI safety company" in description
        assert "founded by former OpenAI researchers" in description
    
    def test_confidence_calculation(self, tavily_config):
        """Test confidence score calculation."""
        adapter = TavilyAdapter(tavily_config)
        
        # High confidence case
        confidence = adapter._calculate_extraction_confidence(
            company_name="Anthropic",
            description="Anthropic is an AI safety company with advanced research capabilities",
            website="https://anthropic.com",
            search_score=0.95
        )
        assert confidence > 0.8
        
        # Low confidence case
        confidence = adapter._calculate_extraction_confidence(
            company_name="Unknown",
            description=None,
            website="https://example.com/Unknown",
            search_score=0.2
        )
        assert confidence < 0.6


class TestQueryBuilding:
    """Test search query construction."""
    
    def test_company_search_query_building(self, tavily_config):
        """Test building queries for company similarity search."""
        adapter = TavilyAdapter(tavily_config)
        
        # Basic query
        query = adapter._build_company_search_query("OpenAI")
        assert "companies similar to \"OpenAI\"" in query
        assert "competitors" in query
        
        # Query with website
        query = adapter._build_company_search_query(
            "OpenAI",
            company_website="https://openai.com"
        )
        assert "openai.com" in query
        
        # Query with description
        query = adapter._build_company_search_query(
            "OpenAI",
            company_description="AI research company developing large language models"
        )
        assert "AI research company" in query
    
    def test_keyword_search_query_building(self, tavily_config):
        """Test building queries for keyword-based search."""
        adapter = TavilyAdapter(tavily_config)
        
        # Single keyword
        query = adapter._build_keyword_search_query(["artificial intelligence"])
        assert "companies in \"artificial intelligence\" industry" in query
        
        # Multiple keywords
        query = adapter._build_keyword_search_query(
            ["machine learning", "natural language processing", "computer vision"]
        )
        assert "machine learning AND natural language processing" in query
        assert "computer vision" in query
        
        # Keywords with filters
        filters = MCPSearchFilters(
            industry="technology",
            location="Silicon Valley",
            company_size="startup"
        )
        
        query = adapter._build_keyword_search_query(
            ["AI", "ML"],
            filters=filters
        )
        assert "industry technology" in query
        assert "location Silicon Valley" in query
        assert "size startup" in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
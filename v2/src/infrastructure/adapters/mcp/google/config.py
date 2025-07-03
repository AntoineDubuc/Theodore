"""
Configuration for Google Search MCP adapter.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re


class GoogleSearchProvider(str, Enum):
    """Available Google search providers."""
    
    CUSTOM_SEARCH = "custom_search"
    SERPAPI = "serpapi"
    DUCKDUCKGO = "duckduckgo"
    

class GoogleSearchConfig(BaseModel):
    """Configuration for Google Search MCP adapter."""
    
    # Provider selection
    preferred_providers: List[GoogleSearchProvider] = Field(
        default=[
            GoogleSearchProvider.CUSTOM_SEARCH,
            GoogleSearchProvider.SERPAPI,
            GoogleSearchProvider.DUCKDUCKGO
        ],
        description="Ordered list of preferred search providers (fallback chain)"
    )
    
    # Google Custom Search API settings
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google Custom Search API key"
    )
    
    google_cse_id: Optional[str] = Field(
        default=None,
        description="Google Custom Search Engine ID"
    )
    
    # SerpAPI settings
    serpapi_key: Optional[str] = Field(
        default=None,
        description="SerpAPI key"
    )
    
    serpapi_engine: str = Field(
        default="google",
        description="SerpAPI search engine"
    )
    
    # Request settings
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    
    retry_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=30.0,
        description="Base delay between retries in seconds"
    )
    
    # Search settings
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of search results to return"
    )
    
    results_per_page: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results per API request"
    )
    
    search_language: str = Field(
        default="en",
        description="Language code for search results"
    )
    
    search_country: str = Field(
        default="us",
        description="Country code for search results"
    )
    
    # Company extraction settings
    company_keywords: List[str] = Field(
        default_factory=lambda: [
            "company", "corp", "corporation", "inc", "llc", "ltd",
            "business", "enterprise", "firm", "organization",
            "startup", "tech", "software", "services"
        ],
        description="Keywords that indicate company-related content"
    )
    
    excluded_domains: List[str] = Field(
        default_factory=lambda: [
            "wikipedia.org",
            "linkedin.com",
            "facebook.com",
            "twitter.com",
            "x.com",
            "instagram.com",
            "youtube.com",
            "reddit.com",
            "quora.com",
            "crunchbase.com",
            "glassdoor.com",
            "indeed.com",
            "bloomberg.com",
            "reuters.com",
            "techcrunch.com"
        ],
        description="Domains to exclude from company extraction"
    )
    
    # Company information extraction
    extract_company_info: bool = Field(
        default=True,
        description="Whether to extract company information from search results"
    )
    
    company_confidence_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for company extraction"
    )
    
    # Caching settings
    enable_caching: bool = Field(
        default=True,
        description="Whether to cache search results"
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,  # 1 hour
        ge=60,
        le=86400,  # 24 hours
        description="Cache TTL in seconds"
    )
    
    cache_max_size: int = Field(
        default=500,
        ge=10,
        le=5000,
        description="Maximum number of cached searches"
    )
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Maximum requests per minute"
    )
    
    rate_limit_burst_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Burst size for rate limiting"
    )
    
    # Custom headers
    user_agent: str = Field(
        default="Theodore-GoogleSearch/1.0 (+https://theodore.ai/bot)",
        description="User agent string for requests"
    )
    
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers to include in requests"
    )
    
    # Advanced settings
    enable_snippets: bool = Field(
        default=True,
        description="Whether to include search result snippets"
    )
    
    enable_safe_search: bool = Field(
        default=True,
        description="Whether to enable safe search filtering"
    )
    
    enable_image_search: bool = Field(
        default=False,
        description="Whether to include image search results"
    )
    
    enable_news_search: bool = Field(
        default=True,
        description="Whether to include news search results"
    )
    
    # DuckDuckGo fallback settings
    duckduckgo_region: str = Field(
        default="us-en",
        description="DuckDuckGo region setting"
    )
    
    duckduckgo_safe_search: str = Field(
        default="moderate",
        description="DuckDuckGo safe search setting (strict, moderate, off)"
    )
    
    # Performance settings
    concurrent_requests: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of concurrent requests"
    )
    
    connection_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="HTTP connection pool size"
    )
    
    @field_validator('preferred_providers')
    def validate_providers(cls, v):
        """Validate that at least one provider is specified."""
        if not v:
            raise ValueError('At least one search provider must be specified')
        return v
    
    @field_validator('search_language')
    def validate_language(cls, v):
        """Validate language code format."""
        if not re.match(r'^[a-z]{2}$', v):
            raise ValueError('Language code must be two lowercase letters (e.g., "en")')
        return v
    
    @field_validator('search_country')
    def validate_country(cls, v):
        """Validate country code format."""
        if not re.match(r'^[a-z]{2}$', v):
            raise ValueError('Country code must be two lowercase letters (e.g., "us")')
        return v
    
    @field_validator('excluded_domains')
    def validate_excluded_domains(cls, v):
        """Validate excluded domains format."""
        for domain in v:
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
                raise ValueError(f'Invalid domain format: {domain}')
        return v
    
    def get_headers(self) -> Dict[str, str]:
        """Get complete headers for requests."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': f'{self.search_language},en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        headers.update(self.custom_headers)
        return headers
    
    def should_exclude_domain(self, domain: str) -> bool:
        """Check if domain should be excluded from results."""
        domain_lower = domain.lower()
        return any(excluded in domain_lower for excluded in self.excluded_domains)
    
    def get_available_providers(self) -> List[GoogleSearchProvider]:
        """Get list of available providers based on API keys."""
        available = []
        
        for provider in self.preferred_providers:
            if provider == GoogleSearchProvider.CUSTOM_SEARCH:
                if self.google_api_key and self.google_cse_id:
                    available.append(provider)
            elif provider == GoogleSearchProvider.SERPAPI:
                if self.serpapi_key:
                    available.append(provider)
            elif provider == GoogleSearchProvider.DUCKDUCKGO:
                # DuckDuckGo doesn't require API keys
                available.append(provider)
        
        return available
    
    def get_provider_config(self, provider: GoogleSearchProvider) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        if provider == GoogleSearchProvider.CUSTOM_SEARCH:
            return {
                'api_key': self.google_api_key,
                'cse_id': self.google_cse_id,
                'language': self.search_language,
                'country': self.search_country,
                'safe_search': 'active' if self.enable_safe_search else 'off',
                'num_results': self.results_per_page
            }
        elif provider == GoogleSearchProvider.SERPAPI:
            return {
                'api_key': self.serpapi_key,
                'engine': self.serpapi_engine,
                'google_domain': f'google.{self.search_country}',
                'hl': self.search_language,
                'gl': self.search_country,
                'safe': 'active' if self.enable_safe_search else 'off',
                'num': self.results_per_page
            }
        elif provider == GoogleSearchProvider.DUCKDUCKGO:
            return {
                'region': self.duckduckgo_region,
                'safesearch': self.duckduckgo_safe_search,
                'max_results': self.results_per_page
            }
        else:
            return {}
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "preferred_providers": ["custom_search", "serpapi", "duckduckgo"],
                "google_api_key": "AIza...",
                "google_cse_id": "cx:...",
                "serpapi_key": "serpapi_key_...",
                "max_results": 10,
                "timeout_seconds": 30.0,
                "enable_caching": True,
                "cache_ttl_seconds": 3600,
                "company_confidence_threshold": 0.3
            }
        }
    )
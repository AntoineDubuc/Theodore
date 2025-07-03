"""
Configuration for DuckDuckGo domain discovery adapter.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class DuckDuckGoConfig(BaseModel):
    """Configuration for DuckDuckGo domain discovery adapter."""
    
    # Request settings
    timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
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
    
    retry_exponential_base: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Exponential backoff base for retries"
    )
    
    # Search settings
    search_query_template: str = Field(
        default='"{company_name}" official website',
        description="Template for search queries"
    )
    
    max_search_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of search results to analyze"
    )
    
    result_analysis_depth: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to analyze in detail"
    )
    
    # Domain validation settings
    enable_domain_validation: bool = Field(
        default=True,
        description="Whether to validate discovered domains"
    )
    
    validation_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Timeout for domain validation requests"
    )
    
    validate_ssl: bool = Field(
        default=False,
        description="Whether to validate SSL certificates during domain validation"
    )
    
    follow_redirects: bool = Field(
        default=True,
        description="Whether to follow redirects during validation"
    )
    
    max_redirects: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum number of redirects to follow"
    )
    
    # Caching settings
    enable_caching: bool = Field(
        default=True,
        description="Whether to cache discovery results"
    )
    
    cache_ttl_seconds: int = Field(
        default=86400,  # 24 hours
        ge=60,
        le=604800,  # 1 week
        description="Cache TTL in seconds"
    )
    
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum number of entries to cache"
    )
    
    # User agent and headers
    user_agent: str = Field(
        default="Theodore-DomainDiscovery/1.0 (+https://theodore.ai/bot)",
        description="User agent string for requests"
    )
    
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers to include in requests"
    )
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        description="Maximum requests per minute"
    )
    
    rate_limit_burst_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Burst size for rate limiting"
    )
    
    # Content filtering
    excluded_domains: list[str] = Field(
        default_factory=lambda: [
            'linkedin.com',
            'facebook.com', 
            'twitter.com',
            'x.com',
            'instagram.com',
            'youtube.com',
            'wikipedia.org',
            'bloomberg.com',
            'crunchbase.com',
            'glassdoor.com',
            'indeed.com'
        ],
        description="Domains to exclude from results"
    )
    
    preferred_domains: list[str] = Field(
        default_factory=lambda: ['.com', '.net', '.org', '.io', '.co'],
        description="Preferred domain extensions (in order of preference)"
    )
    
    # Confidence scoring
    confidence_boost_keywords: list[str] = Field(
        default_factory=lambda: [
            'official', 'homepage', 'website', 'corporate',
            'company', 'business', 'enterprise'
        ],
        description="Keywords that boost confidence scores"
    )
    
    confidence_penalty_keywords: list[str] = Field(
        default_factory=lambda: [
            'wikipedia', 'linkedin', 'facebook', 'twitter',
            'news', 'article', 'blog', 'forum', 'review'
        ],
        description="Keywords that reduce confidence scores"
    )
    
    min_confidence_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to return a result"
    )
    
    @field_validator('search_query_template')
    def validate_search_template(cls, v):
        """Validate that search template contains company_name placeholder."""
        if '{company_name}' not in v:
            raise ValueError('search_query_template must contain {company_name} placeholder')
        return v
    
    @field_validator('excluded_domains')
    def validate_excluded_domains(cls, v):
        """Validate excluded domains format."""
        for domain in v:
            if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
                raise ValueError(f'Invalid excluded domain format: {domain}')
        return v
    
    @field_validator('preferred_domains')
    def validate_preferred_domains(cls, v):
        """Validate preferred domains format."""
        for domain in v:
            if not domain.startswith('.') or len(domain) < 2:
                raise ValueError(f'Preferred domain must start with . and have valid format: {domain}')
        return v
    
    def get_headers(self) -> Dict[str, str]:
        """Get complete headers for requests."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        headers.update(self.custom_headers)
        return headers
    
    def should_exclude_domain(self, domain: str) -> bool:
        """Check if domain should be excluded from results."""
        domain_lower = domain.lower()
        return any(excluded in domain_lower for excluded in self.excluded_domains)
    
    def get_domain_preference_score(self, domain: str) -> float:
        """Get preference score for domain based on extension."""
        domain_lower = domain.lower()
        for i, preferred in enumerate(self.preferred_domains):
            if domain_lower.endswith(preferred):
                # Higher score for earlier preferences
                return 1.0 - (i * 0.1)
        return 0.5  # Neutral score for other extensions
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "timeout_seconds": 10.0,
                "max_retries": 3,
                "search_query_template": '"{company_name}" official website',
                "max_search_results": 10,
                "enable_domain_validation": True,
                "enable_caching": True,
                "cache_ttl_seconds": 86400,
                "min_confidence_threshold": 0.3
            }
        }
    )
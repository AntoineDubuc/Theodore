"""
Tavily AI MCP Search Tool Configuration.

Production-ready configuration for Tavily AI search integration with
comprehensive validation, environment loading, and performance optimization.
"""

import os
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging


class TavilySearchDepth(str, Enum):
    """Tavily search depth options."""
    BASIC = "basic"
    ADVANCED = "advanced"


class TavilySearchType(str, Enum):
    """Tavily search type options."""
    SEARCH = "search"
    NEWS = "news"


class TavilyIncludeFields(str, Enum):
    """Fields to include in Tavily responses."""
    ANSWER = "answer"
    RAW_CONTENT = "raw_content"
    IMAGES = "images"


class TavilyConfig(BaseModel):
    """
    Production configuration for Tavily AI MCP search adapter.
    
    Features:
    - Comprehensive API configuration with validation
    - Performance optimization settings
    - Enterprise caching and rate limiting
    - Search customization options
    - Cost management and monitoring
    """
    
    # Core API Configuration
    api_key: str = Field(..., description="Tavily API key")
    base_url: str = Field(
        default="https://api.tavily.com", 
        description="Tavily API base URL"
    )
    
    # Search Configuration
    search_depth: TavilySearchDepth = Field(
        default=TavilySearchDepth.BASIC,
        description="Search depth level"
    )
    search_type: TavilySearchType = Field(
        default=TavilySearchType.SEARCH,
        description="Type of search to perform"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
    
    # Content and Quality
    include_answer: bool = Field(
        default=True,
        description="Include AI-generated answer"
    )
    include_raw_content: bool = Field(
        default=True,
        description="Include raw page content"
    )
    include_images: bool = Field(
        default=False,
        description="Include image results"
    )
    include_domains: List[str] = Field(
        default_factory=list,
        description="Domains to include in search"
    )
    exclude_domains: List[str] = Field(
        default_factory=list,
        description="Domains to exclude from search"
    )
    
    # Performance and Rate Limiting
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    rate_limit_requests_per_minute: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Rate limit for requests per minute"
    )
    
    # Caching Configuration
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching"
    )
    cache_ttl_seconds: int = Field(
        default=1800,  # 30 minutes
        ge=60,
        le=86400,
        description="Cache TTL in seconds"
    )
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum number of cached entries"
    )
    
    # Search Enhancement
    company_search_keywords: List[str] = Field(
        default_factory=lambda: [
            "company", "business", "startup", "enterprise", "corporation",
            "founders", "team", "about us", "contact", "careers"
        ],
        description="Keywords to enhance company searches"
    )
    
    # Date and Recency
    days_back: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Limit results to last N days"
    )
    
    # Geographic and Language
    country: Optional[str] = Field(
        default=None,
        description="Country code for geographic filtering"
    )
    language: str = Field(
        default="en",
        description="Language code for results"
    )
    
    # Cost Management
    cost_per_request: float = Field(
        default=0.001,  # $0.001 per request
        ge=0.0,
        description="Estimated cost per API request in USD"
    )
    daily_budget_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Daily spending limit in USD"
    )
    
    # Monitoring and Logging
    enable_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Advanced Features
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers"
    )
    use_proxy: bool = Field(
        default=False,
        description="Use proxy for requests"
    )
    proxy_url: Optional[str] = Field(
        default=None,
        description="Proxy URL if enabled"
    )
    
    # Model Configuration
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "api_key": "tvly-xxxxxxxxxxxxxxxxxx",
                "search_depth": "basic",
                "max_results": 10,
                "include_raw_content": True,
                "enable_caching": True,
                "rate_limit_requests_per_minute": 100
            }
        }
    )
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate Tavily API key format."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        if not v.startswith('tvly-'):
            raise ValueError("Tavily API key must start with 'tvly-'")
        return v.strip()
    
    @field_validator('include_domains', 'exclude_domains')
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        """Validate and normalize domain lists."""
        if not v:
            return []
        
        normalized = []
        for domain in v:
            domain = domain.strip().lower()
            if not domain:
                continue
            # Remove protocol if present
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://', 1)[1]
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            # Basic domain validation
            if '.' in domain and len(domain) > 3:
                normalized.append(domain)
        
        return normalized
    
    @field_validator('company_search_keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and normalize company search keywords."""
        if not v:
            return []
        
        normalized = []
        for keyword in v:
            keyword = keyword.strip().lower()
            if keyword and len(keyword) > 1:
                normalized.append(keyword)
        
        return list(set(normalized))  # Remove duplicates
    
    @classmethod
    def from_env(cls) -> "TavilyConfig":
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv("TAVILY_API_KEY", ""),
            search_depth=TavilySearchDepth(
                os.getenv("TAVILY_SEARCH_DEPTH", "basic")
            ),
            max_results=int(os.getenv("TAVILY_MAX_RESULTS", "10")),
            timeout_seconds=float(os.getenv("TAVILY_TIMEOUT", "30.0")),
            rate_limit_requests_per_minute=int(
                os.getenv("TAVILY_RATE_LIMIT", "100")
            ),
            enable_caching=os.getenv("TAVILY_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("TAVILY_CACHE_TTL", "1800")),
            include_raw_content=os.getenv("TAVILY_RAW_CONTENT", "true").lower() == "true",
            cost_per_request=float(os.getenv("TAVILY_COST_PER_REQUEST", "0.001")),
            enable_monitoring=os.getenv("TAVILY_MONITORING", "true").lower() == "true"
        )
    
    def get_request_headers(self) -> Dict[str, str]:
        """Generate HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Theodore-v2-MCP-Client/1.0",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Add custom headers
        headers.update(self.custom_headers)
        
        return headers
    
    def estimate_daily_requests(self) -> Optional[int]:
        """Estimate maximum daily requests based on budget."""
        if not self.daily_budget_usd or self.cost_per_request <= 0:
            return None
        
        return int(self.daily_budget_usd / self.cost_per_request)
    
    def validate_search_parameters(self, query: str, max_results: int) -> None:
        """Validate search parameters against configuration limits."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        if max_results < 1 or max_results > self.max_results:
            raise ValueError(
                f"max_results must be between 1 and {self.max_results}, got {max_results}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return self.model_dump()
    
    def get_search_params(self, **overrides) -> Dict[str, Any]:
        """Get Tavily API search parameters with optional overrides."""
        params = {
            "search_depth": self.search_depth.value,
            "max_results": self.max_results,
            "include_answer": self.include_answer,
            "include_raw_content": self.include_raw_content,
            "include_images": self.include_images,
        }
        
        # Add optional parameters
        if self.include_domains:
            params["include_domains"] = self.include_domains
        
        if self.exclude_domains:
            params["exclude_domains"] = self.exclude_domains
        
        if self.days_back:
            params["days"] = self.days_back
        
        if self.country:
            params["country"] = self.country
        
        # Apply overrides
        params.update(overrides)
        
        return params
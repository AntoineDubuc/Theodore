"""
Perplexity AI adapter configuration.

Provides comprehensive configuration for Perplexity AI search operations with
enterprise-grade settings for rate limiting, caching, and search customization.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import os
from enum import Enum


class PerplexityModel(str, Enum):
    """Available Perplexity AI models."""
    
    SONAR_SMALL = "sonar-small-chat"
    SONAR_MEDIUM = "sonar-medium-chat"
    SONAR_LARGE = "sonar-large-chat"
    SONAR_HUGE = "sonar-huge-chat"


class SearchFocus(str, Enum):
    """Search focus options for Perplexity queries."""
    
    WEB = "web"
    NEWS = "news"
    ACADEMIC = "academic"
    SHOPPING = "shopping"
    GENERAL = "general"


class SearchDepth(str, Enum):
    """Search depth configuration."""
    
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"
    DEEP = "deep"


class PerplexityConfig(BaseModel):
    """
    Configuration for Perplexity AI MCP adapter.
    
    Provides comprehensive settings for search operations, rate limiting,
    caching, and result optimization.
    """
    
    # Authentication
    api_key: str = Field(
        description="Perplexity API key for authentication"
    )
    
    # Model Configuration
    model: PerplexityModel = Field(
        default=PerplexityModel.SONAR_MEDIUM,
        description="Perplexity model to use for searches"
    )
    
    # Search Configuration
    search_focus: SearchFocus = Field(
        default=SearchFocus.WEB,
        description="Primary search focus for queries"
    )
    
    search_depth: SearchDepth = Field(
        default=SearchDepth.COMPREHENSIVE,
        description="Depth of search analysis"
    )
    
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results per search"
    )
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum requests per minute"
    )
    
    rate_limit_burst_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum burst requests"
    )
    
    # Request Configuration
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
        description="Maximum retry attempts"
    )
    
    retry_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Base delay between retries"
    )
    
    retry_exponential_backoff: bool = Field(
        default=True,
        description="Use exponential backoff for retries"
    )
    
    # Caching Configuration
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching"
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache time-to-live in seconds"
    )
    
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum number of cached entries"
    )
    
    # Query Configuration
    query_language: str = Field(
        default="en",
        description="Query language code"
    )
    
    search_recency_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Limit search to recent content (days)"
    )
    
    include_citations: bool = Field(
        default=True,
        description="Include source citations in results"
    )
    
    # Company Search Specific
    company_search_keywords: List[str] = Field(
        default=[
            "company",
            "business",
            "corporation",
            "startup",
            "enterprise",
            "firm",
            "organization"
        ],
        description="Keywords to enhance company searches"
    )
    
    excluded_domains: List[str] = Field(
        default=[
            "wikipedia.org",
            "linkedin.com/company",
            "crunchbase.com"
        ],
        description="Domains to exclude from results"
    )
    
    # Quality Filtering
    min_confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for results"
    )
    
    enable_quality_filtering: bool = Field(
        default=True,
        description="Enable AI-powered quality filtering"
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
    
    # Cost Management
    cost_per_request: float = Field(
        default=0.005,
        ge=0.0,
        description="Estimated cost per API request in USD"
    )
    
    daily_budget_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Daily spending budget in USD"
    )
    
    # Advanced Configuration
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers for requests"
    )
    
    user_agent: str = Field(
        default="Theodore-v2-MCP-Client/1.0",
        description="User agent for API requests"
    )
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        if not v.startswith('pplx-'):
            raise ValueError("Perplexity API key must start with 'pplx-'")
        return v.strip()
    
    @field_validator('excluded_domains')
    @classmethod
    def validate_excluded_domains(cls, v):
        """Validate excluded domains format."""
        validated = []
        for domain in v:
            domain = domain.strip().lower()
            if domain and '.' in domain:
                validated.append(domain)
        return validated
    
    @field_validator('company_search_keywords')
    @classmethod
    def validate_company_keywords(cls, v):
        """Validate company search keywords."""
        return [kw.strip().lower() for kw in v if kw.strip()]
    
    @classmethod
    def from_env(cls) -> "PerplexityConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            PerplexityConfig with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            model=PerplexityModel(os.getenv("PERPLEXITY_MODEL", PerplexityModel.SONAR_MEDIUM)),
            search_focus=SearchFocus(os.getenv("PERPLEXITY_SEARCH_FOCUS", SearchFocus.WEB)),
            search_depth=SearchDepth(os.getenv("PERPLEXITY_SEARCH_DEPTH", SearchDepth.COMPREHENSIVE)),
            max_results=int(os.getenv("PERPLEXITY_MAX_RESULTS", "10")),
            rate_limit_requests_per_minute=int(os.getenv("PERPLEXITY_RATE_LIMIT", "20")),
            timeout_seconds=float(os.getenv("PERPLEXITY_TIMEOUT", "30.0")),
            enable_caching=os.getenv("PERPLEXITY_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("PERPLEXITY_CACHE_TTL", "3600")),
            search_recency_days=int(os.getenv("PERPLEXITY_RECENCY_DAYS")) if os.getenv("PERPLEXITY_RECENCY_DAYS") else None,
            enable_monitoring=os.getenv("PERPLEXITY_ENABLE_MONITORING", "true").lower() == "true",
            log_level=os.getenv("PERPLEXITY_LOG_LEVEL", "INFO"),
            daily_budget_usd=float(os.getenv("PERPLEXITY_DAILY_BUDGET")) if os.getenv("PERPLEXITY_DAILY_BUDGET") else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()
    
    def get_request_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent
        }
        headers.update(self.custom_headers)
        return headers
    
    def estimate_daily_requests(self) -> Optional[int]:
        """
        Estimate maximum daily requests based on budget.
        
        Returns:
            Estimated daily request limit, or None if no budget set
        """
        if not self.daily_budget_usd or self.cost_per_request <= 0:
            return None
        return int(self.daily_budget_usd / self.cost_per_request)
    
    def validate_search_parameters(self, query: str, limit: int) -> None:
        """
        Validate search parameters against configuration.
        
        Args:
            query: Search query to validate
            limit: Number of results requested
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        if limit <= 0 or limit > self.max_results:
            raise ValueError(f"Result limit must be between 1 and {self.max_results}")
    
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        validate_assignment=True
    )
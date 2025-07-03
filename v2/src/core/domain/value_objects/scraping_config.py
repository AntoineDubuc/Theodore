#!/usr/bin/env python3
"""
Theodore v2 Scraping Configuration Value Objects

Comprehensive configuration system for web scraping operations including
various modes, content types, performance settings, and provider-specific options.
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass


class ScrapingMode(str, Enum):
    """Different scraping operation modes"""
    SINGLE_PAGE = "single_page"
    MULTI_PAGE = "multi_page"
    RECURSIVE_CRAWL = "recursive_crawl"
    SITEMAP_BASED = "sitemap_based"


class ContentType(str, Enum):
    """Types of content to extract"""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    LINKS = "links"
    IMAGES = "images"
    STRUCTURED_DATA = "structured_data"
    METADATA = "metadata"


class UserAgentType(str, Enum):
    """Predefined user agent categories"""
    CHROME_DESKTOP = "chrome_desktop"
    FIREFOX_DESKTOP = "firefox_desktop"
    SAFARI_MOBILE = "safari_mobile"
    BOT_FRIENDLY = "bot_friendly"
    CUSTOM = "custom"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: float = 1.0
    burst_size: int = 5
    backoff_factor: float = 1.5
    max_delay: float = 60.0


@dataclass
class RetryConfig:
    """Retry configuration for failed requests"""
    max_attempts: int = 3
    base_delay: float = 1.0
    exponential_backoff: bool = True
    retry_on_status: List[int] = None
    
    def __post_init__(self):
        if self.retry_on_status is None:
            self.retry_on_status = [429, 500, 502, 503, 504]


class ScrapingConfig(BaseModel):
    """Comprehensive scraping configuration"""
    
    # Basic settings
    mode: ScrapingMode = ScrapingMode.SINGLE_PAGE
    content_types: List[ContentType] = Field(default_factory=lambda: [ContentType.TEXT])
    
    # Request settings
    timeout: float = Field(30.0, ge=1.0, le=300.0)
    user_agent_type: UserAgentType = UserAgentType.CHROME_DESKTOP
    custom_user_agent: Optional[str] = None
    
    # JavaScript and rendering
    enable_javascript: bool = True
    wait_for_selector: Optional[str] = None
    wait_time: Optional[float] = None
    
    # Content filtering
    max_content_length: int = Field(1_000_000, ge=1000)  # 1MB default
    exclude_selectors: List[str] = Field(default_factory=list)
    include_selectors: List[str] = Field(default_factory=list)
    
    # Multi-page settings
    max_pages: int = Field(50, ge=1, le=1000)
    max_depth: int = Field(3, ge=1, le=10)
    follow_external_links: bool = False
    
    # Performance and reliability
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    parallel_requests: int = Field(5, ge=1, le=20)
    
    # Content processing
    clean_html: bool = True
    extract_links: bool = True
    extract_images: bool = False
    respect_robots_txt: bool = True
    
    # Custom headers and cookies
    headers: Dict[str, str] = Field(default_factory=dict)
    cookies: Dict[str, str] = Field(default_factory=dict)
    
    # Advanced options
    proxy_config: Optional[Dict[str, Any]] = None
    custom_options: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('custom_user_agent')
    def validate_custom_user_agent(cls, v, values):
        if values.get('user_agent_type') == UserAgentType.CUSTOM and not v:
            raise ValueError('custom_user_agent required when user_agent_type is CUSTOM')
        return v
    
    @validator('wait_time')
    def validate_wait_time(cls, v):
        if v is not None and (v < 0 or v > 60):
            raise ValueError('wait_time must be between 0 and 60 seconds')
        return v
    
    def get_effective_user_agent(self) -> str:
        """Get the actual user agent string to use"""
        if self.user_agent_type == UserAgentType.CUSTOM:
            return self.custom_user_agent
        
        agents = {
            UserAgentType.CHROME_DESKTOP: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            UserAgentType.FIREFOX_DESKTOP: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            UserAgentType.SAFARI_MOBILE: "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            UserAgentType.BOT_FRIENDLY: "Mozilla/5.0 (compatible; TheodoreBot/2.0; +https://theodore.ai/bot)"
        }
        return agents[self.user_agent_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return self.dict()
    
    @classmethod
    def for_company_research(cls) -> 'ScrapingConfig':
        """Preset configuration optimized for company research"""
        return cls(
            mode=ScrapingMode.MULTI_PAGE,
            content_types=[ContentType.TEXT, ContentType.LINKS],
            enable_javascript=True,
            max_pages=50,
            max_depth=2,
            parallel_requests=10,
            rate_limit=RateLimitConfig(requests_per_second=2.0),
            exclude_selectors=["nav", "footer", ".sidebar", "#comments"],
            clean_html=True,
            respect_robots_txt=True
        )
    
    @classmethod
    def for_fast_preview(cls) -> 'ScrapingConfig':
        """Preset for quick page previews"""
        return cls(
            mode=ScrapingMode.SINGLE_PAGE,
            content_types=[ContentType.TEXT],
            timeout=10.0,
            enable_javascript=False,
            max_content_length=50_000,
            clean_html=True
        )
    
    @classmethod
    def for_comprehensive_crawl(cls) -> 'ScrapingConfig':
        """Preset for comprehensive website crawling"""
        return cls(
            mode=ScrapingMode.RECURSIVE_CRAWL,
            content_types=[ContentType.TEXT, ContentType.LINKS, ContentType.IMAGES, ContentType.METADATA],
            enable_javascript=True,
            max_pages=200,
            max_depth=4,
            parallel_requests=8,
            rate_limit=RateLimitConfig(requests_per_second=1.5),
            extract_images=True,
            respect_robots_txt=True,
            retry_config=RetryConfig(max_attempts=2)
        )
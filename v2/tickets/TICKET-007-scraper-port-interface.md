# TICKET-006: Web Scraper Port Definition

## Overview
Define the WebScraper port/interface that will be implemented by different scraping strategies (Crawl4AI, Playwright, etc).

## Acceptance Criteria
- [ ] Define WebScraper interface with clear method signatures
- [ ] Define ScrapingResult data structure
- [ ] Define ScrapingConfig for customization
- [ ] Support for progress callbacks
- [ ] Clear error types for different failure modes
- [ ] Support for both single page and multi-page scraping

## Technical Details
- Pure interface definition - no implementation
- Use Python Protocol or ABC
- Include type hints for all methods
- Design for async operations from the start
- Consider rate limiting in the interface

## Testing
- Create mock implementation for testing
- Verify interface completeness with stub adapter
- Document expected behavior for each method

## Estimated Time: 2 hours

## Dependencies
- TICKET-001 (for domain models)
- TICKET-004 (for progress tracking interface)

## Files to Create
- `v2/src/core/ports/web_scraper.py`
- `v2/src/core/domain/value_objects/scraping_config.py`
- `v2/src/core/domain/value_objects/scraping_result.py`
- `v2/tests/unit/ports/test_web_scraper_mock.py`

---

# Udemy Tutorial Script: Designing Extensible Web Scraper Interfaces

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Flexible Web Scraper Interfaces with Clean Architecture"]**

"Welcome to this crucial tutorial on designing extensible web scraper interfaces! Today we're going to create the foundation that allows Theodore to work with any scraping technology - from Crawl4AI to Playwright to future tools we haven't even invented yet.

By the end of this tutorial, you'll understand how to design interfaces that are powerful enough for complex scraping scenarios yet simple enough to implement. You'll learn about progress tracking, error handling, configuration management, and how to build systems that can evolve with changing requirements.

This is architecture that stands the test of time!"

## Section 1: Understanding the Scraping Interface Challenge (5 minutes)

**[SLIDE 2: The Interface Problem]**

"Let's start by understanding why scraping interfaces are challenging to design:

```python
# ❌ The NAIVE approach - tightly coupled to one library
import crawl4ai

def scrape_company_website(url):
    crawler = crawl4ai.AsyncWebCrawler()
    result = crawler.arun(url=url)
    return result.markdown

# Problems:
# 1. Locked into Crawl4AI forever
# 2. No progress tracking
# 3. No error handling
# 4. No configuration options
# 5. Can't test without real websites
```

This approach makes your application brittle and hard to evolve!"

**[SLIDE 3: Real-World Scraping Complexity]**

"Here's what we're actually dealing with in production:

```python
# Real scraping requirements:
scraping_scenarios = [
    {
        \"type\": \"single_page\",
        \"url\": \"https://company.com/about\",
        \"extract\": [\"text\", \"links\", \"images\"],
        \"javascript\": True,
        \"timeout\": 30
    },
    {
        \"type\": \"multi_page\",
        \"urls\": [\"about\", \"contact\", \"team\", \"careers\"],
        \"base_url\": \"https://company.com\",
        \"parallel\": True,
        \"rate_limit\": \"1 req/sec\"
    },
    {
        \"type\": \"recursive_crawl\",
        \"start_url\": \"https://company.com\",
        \"max_depth\": 3,
        \"max_pages\": 100,
        \"respect_robots\": True
    }
]
```

**[SLIDE 4: The Solution - Ports & Adapters]**

We need an interface that:
1. **Abstracts the complexity** of different scraping libraries
2. **Provides consistent APIs** regardless of implementation
3. **Supports progress tracking** for long-running operations
4. **Handles errors gracefully** with detailed failure information
5. **Stays configurable** for different scraping strategies
6. **Enables testing** with mock implementations

Let's design it!"

## Section 2: Designing Core Value Objects (10 minutes)

**[SLIDE 5: Scraping Configuration Design]**

"Let's start with our configuration value object:

```python
# v2/src/core/domain/value_objects/scraping_config.py

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass

class ScrapingMode(str, Enum):
    \"\"\"Different scraping operation modes\"\"\"
    SINGLE_PAGE = \"single_page\"
    MULTI_PAGE = \"multi_page\"
    RECURSIVE_CRAWL = \"recursive_crawl\"
    SITEMAP_BASED = \"sitemap_based\"

class ContentType(str, Enum):
    \"\"\"Types of content to extract\"\"\"
    TEXT = \"text\"
    MARKDOWN = \"markdown\"
    HTML = \"html\"
    LINKS = \"links\"
    IMAGES = \"images\"
    STRUCTURED_DATA = \"structured_data\"
    METADATA = \"metadata\"

class UserAgentType(str, Enum):
    \"\"\"Predefined user agent categories\"\"\"
    CHROME_DESKTOP = \"chrome_desktop\"
    FIREFOX_DESKTOP = \"firefox_desktop\"
    SAFARI_MOBILE = \"safari_mobile\"
    BOT_FRIENDLY = \"bot_friendly\"
    CUSTOM = \"custom\"

@dataclass
class RateLimitConfig:
    \"\"\"Rate limiting configuration\"\"\"
    requests_per_second: float = 1.0
    burst_size: int = 5
    backoff_factor: float = 1.5
    max_delay: float = 60.0

@dataclass
class RetryConfig:
    \"\"\"Retry configuration for failed requests\"\"\"
    max_attempts: int = 3
    base_delay: float = 1.0
    exponential_backoff: bool = True
    retry_on_status: List[int] = None
    
    def __post_init__(self):
        if self.retry_on_status is None:
            self.retry_on_status = [429, 500, 502, 503, 504]

class ScrapingConfig(BaseModel):
    \"\"\"Comprehensive scraping configuration\"\"\"
    
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
        \"\"\"Get the actual user agent string to use\"\"\"
        if self.user_agent_type == UserAgentType.CUSTOM:
            return self.custom_user_agent
        
        agents = {
            UserAgentType.CHROME_DESKTOP: \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\",
            UserAgentType.FIREFOX_DESKTOP: \"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0\",
            UserAgentType.SAFARI_MOBILE: \"Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1\",
            UserAgentType.BOT_FRIENDLY: \"Mozilla/5.0 (compatible; TheodoreBot/2.0; +https://theodore.ai/bot)\"
        }
        return agents[self.user_agent_type]
    
    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary for serialization\"\"\"
        return self.dict()
    
    @classmethod
    def for_company_research(cls) -> 'ScrapingConfig':
        \"\"\"Preset configuration optimized for company research\"\"\"
        return cls(
            mode=ScrapingMode.MULTI_PAGE,
            content_types=[ContentType.TEXT, ContentType.LINKS],
            enable_javascript=True,
            max_pages=50,
            max_depth=2,
            parallel_requests=10,
            rate_limit=RateLimitConfig(requests_per_second=2.0),
            exclude_selectors=[\"nav\", \"footer\", \".sidebar\", \"#comments\"],
            clean_html=True,
            respect_robots_txt=True
        )
    
    @classmethod
    def for_fast_preview(cls) -> 'ScrapingConfig':
        \"\"\"Preset for quick page previews\"\"\"
        return cls(
            mode=ScrapingMode.SINGLE_PAGE,
            content_types=[ContentType.TEXT],
            timeout=10.0,
            enable_javascript=False,
            max_content_length=50_000,
            clean_html=True
        )
```

**[SLIDE 6: Why This Configuration Design Works]**

"Notice the key design principles:

1. **Comprehensive but Sensible**: Covers all major scraping scenarios with good defaults
2. **Type-Safe**: Enums prevent invalid configurations
3. **Validated**: Pydantic ensures configurations are valid
4. **Preset-Friendly**: Factory methods for common use cases
5. **Extensible**: Custom options dict for future needs

**[HANDS-ON EXERCISE]** \"Create a configuration for scraping a news website vs an e-commerce site. Think about the different requirements!\"

## Section 3: Designing the Result Structure (8 minutes)

**[SLIDE 7: Scraping Result Design]**

"Now let's design our result value object:

```python
# v2/src/core/domain/value_objects/scraping_result.py

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from dataclasses import dataclass
import time

class ScrapingStatus(str, Enum):
    \"\"\"Status of scraping operation\"\"\"
    SUCCESS = \"success\"
    PARTIAL_SUCCESS = \"partial_success\"
    FAILED = \"failed\"
    TIMEOUT = \"timeout\"
    RATE_LIMITED = \"rate_limited\"
    BLOCKED = \"blocked\"

class PageStatus(str, Enum):
    \"\"\"Status of individual page scraping\"\"\"
    SUCCESS = \"success\"
    FAILED = \"failed\"
    SKIPPED = \"skipped\"
    TIMEOUT = \"timeout\"
    BLOCKED = \"blocked\"

@dataclass
class PageResult:
    \"\"\"Result for a single page\"\"\"
    url: str
    status: PageStatus
    content: Optional[str] = None
    html: Optional[str] = None
    links: List[str] = None
    images: List[str] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    status_code: Optional[int] = None
    content_length: int = 0
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    @property
    def is_successful(self) -> bool:
        return self.status == PageStatus.SUCCESS
    
    @property
    def has_content(self) -> bool:
        return self.content is not None and len(self.content.strip()) > 0

@dataclass
class ScrapingMetrics:
    \"\"\"Performance metrics for scraping operation\"\"\"
    total_pages_attempted: int = 0
    pages_successful: int = 0
    pages_failed: int = 0
    pages_skipped: int = 0
    total_content_size: int = 0
    average_response_time: float = 0.0
    total_duration: float = 0.0
    requests_per_second: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_pages_attempted == 0:
            return 0.0
        return self.pages_successful / self.total_pages_attempted
    
    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate

class ScrapingResult(BaseModel):
    \"\"\"Complete result of a scraping operation\"\"\"
    
    # Operation metadata
    operation_id: str = Field(..., description=\"Unique identifier for this operation\")
    status: ScrapingStatus = Field(..., description=\"Overall operation status\")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Configuration used
    config: 'ScrapingConfig' = Field(..., description=\"Configuration used for scraping\")
    
    # Results
    pages: List[PageResult] = Field(default_factory=list)
    primary_content: Optional[str] = Field(None, description=\"Main extracted content\")
    
    # Aggregated data
    all_links: List[str] = Field(default_factory=list)
    all_images: List[str] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance and diagnostics
    metrics: ScrapingMetrics = Field(default_factory=ScrapingMetrics)
    error_details: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Raw response data (optional)
    raw_responses: Dict[str, Any] = Field(default_factory=dict)
    
    def add_page_result(self, page_result: PageResult) -> None:
        \"\"\"Add a page result and update metrics\"\"\"
        self.pages.append(page_result)
        self._update_metrics(page_result)
        self._update_aggregated_data(page_result)
    
    def _update_metrics(self, page_result: PageResult) -> None:
        \"\"\"Update performance metrics\"\"\"
        self.metrics.total_pages_attempted += 1
        
        if page_result.status == PageStatus.SUCCESS:
            self.metrics.pages_successful += 1
        elif page_result.status == PageStatus.FAILED:
            self.metrics.pages_failed += 1
        elif page_result.status == PageStatus.SKIPPED:
            self.metrics.pages_skipped += 1
        
        # Update content size
        if page_result.content:
            self.metrics.total_content_size += len(page_result.content)
        
        # Update response time
        total_time = (self.metrics.average_response_time * 
                     (self.metrics.total_pages_attempted - 1) + 
                     page_result.response_time)
        self.metrics.average_response_time = total_time / self.metrics.total_pages_attempted
    
    def _update_aggregated_data(self, page_result: PageResult) -> None:
        \"\"\"Update aggregated links and images\"\"\"
        if page_result.links:
            self.all_links.extend(page_result.links)
        if page_result.images:
            self.all_images.extend(page_result.images)
        
        # Deduplicate
        self.all_links = list(set(self.all_links))
        self.all_images = list(set(self.all_images))
    
    def finalize(self) -> None:
        \"\"\"Finalize the result after all pages are processed\"\"\"
        self.completed_at = datetime.now()
        
        # Calculate total duration
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.metrics.total_duration = duration
            
            # Calculate requests per second
            if duration > 0:
                self.metrics.requests_per_second = self.metrics.total_pages_attempted / duration
        
        # Set primary content (combine successful pages)
        successful_content = []
        for page in self.pages:
            if page.is_successful and page.has_content:
                successful_content.append(page.content)
        
        self.primary_content = \"\\n\\n\".join(successful_content)
        
        # Determine overall status
        if self.metrics.pages_successful == 0:
            self.status = ScrapingStatus.FAILED
        elif self.metrics.success_rate >= 0.8:
            self.status = ScrapingStatus.SUCCESS
        else:
            self.status = ScrapingStatus.PARTIAL_SUCCESS
    
    @property
    def is_successful(self) -> bool:
        return self.status in [ScrapingStatus.SUCCESS, ScrapingStatus.PARTIAL_SUCCESS]
    
    @property
    def has_content(self) -> bool:
        return self.primary_content is not None and len(self.primary_content.strip()) > 0
    
    @property
    def successful_pages(self) -> List[PageResult]:
        return [page for page in self.pages if page.is_successful]
    
    @property
    def failed_pages(self) -> List[PageResult]:
        return [page for page in self.pages if page.status == PageStatus.FAILED]
    
    def get_content_by_url(self, url: str) -> Optional[str]:
        \"\"\"Get content for a specific URL\"\"\"
        for page in self.pages:
            if page.url == url and page.has_content:
                return page.content
        return None
    
    def to_summary_dict(self) -> Dict[str, Any]:
        \"\"\"Get a summary dictionary for logging/reporting\"\"\"
        return {
            \"operation_id\": self.operation_id,
            \"status\": self.status,
            \"pages_attempted\": self.metrics.total_pages_attempted,
            \"pages_successful\": self.metrics.pages_successful,
            \"success_rate\": self.metrics.success_rate,
            \"total_content_size\": self.metrics.total_content_size,
            \"duration\": self.metrics.total_duration,
            \"has_content\": self.has_content
        }
```

**[SLIDE 8: Result Design Benefits]**

"This design provides:

1. **Rich Metrics**: Detailed performance and success tracking
2. **Granular Status**: Know exactly what succeeded and what failed
3. **Aggregated Data**: Easy access to combined results
4. **Debugging Info**: Error details and warnings for troubleshooting
5. **Flexible Content**: Support for multiple content types and formats

**[PRACTICAL TIP]** \"The finalize() method is key - it calculates derived metrics and determines overall success status!\"

## Section 4: Designing the Port Interface (12 minutes)

**[SLIDE 9: Main WebScraper Port]**

"Now for the main event - our scraper port interface:

```python
# v2/src/core/ports/web_scraper.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
import asyncio
from contextlib import asynccontextmanager

from v2.src.core.domain.value_objects.scraping_config import ScrapingConfig
from v2.src.core.domain.value_objects.scraping_result import ScrapingResult, PageResult
from v2.src.core.interfaces.progress import ProgressTracker

# Type aliases for cleaner signatures
ProgressCallback = Callable[[str, float, Optional[str]], None]
ValidationCallback = Callable[[str], bool]

class WebScraperException(Exception):
    \"\"\"Base exception for all scraper-related errors\"\"\"
    pass

class ScrapingTimeoutException(WebScraperException):
    \"\"\"Raised when scraping operation times out\"\"\"
    pass

class RateLimitedException(WebScraperException):
    \"\"\"Raised when rate limited by target site\"\"\"
    pass

class BlockedException(WebScraperException):
    \"\"\"Raised when blocked by target site\"\"\"
    pass

class ConfigurationException(WebScraperException):
    \"\"\"Raised when scraper configuration is invalid\"\"\"
    pass

class WebScraper(ABC):
    \"\"\"Port interface for web scraping implementations\"\"\"
    
    @abstractmethod
    async def scrape_single_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PageResult:
        \"\"\"
        Scrape a single page.
        
        Args:
            url: The URL to scrape
            config: Scraping configuration (uses defaults if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            PageResult with scraped content and metadata
            
        Raises:
            ScrapingTimeoutException: If operation times out
            BlockedException: If blocked by target site
            ConfigurationException: If configuration is invalid
        \"\"\"
        pass
    
    @abstractmethod
    async def scrape_multiple_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        \"\"\"
        Scrape multiple pages.
        
        Args:
            urls: List of URLs to scrape
            config: Scraping configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScrapingResult with all pages and aggregated data
        \"\"\"
        pass
    
    @abstractmethod
    async def scrape_website(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None,
        url_filter: Optional[ValidationCallback] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        \"\"\"
        Scrape an entire website recursively.
        
        Args:
            base_url: Starting URL for crawling
            config: Scraping configuration
            url_filter: Optional function to filter URLs (return True to include)
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScrapingResult with all discovered and scraped pages
        \"\"\"
        pass
    
    @abstractmethod
    async def scrape_with_progress(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> ScrapingResult:
        \"\"\"
        Scrape with integrated progress tracking.
        
        Args:
            urls: URLs to scrape
            config: Scraping configuration
            progress_tracker: Progress tracking interface
            
        Returns:
            ScrapingResult with detailed progress information
        \"\"\"
        pass
    
    @abstractmethod
    async def validate_url(self, url: str, timeout: float = 5.0) -> bool:
        \"\"\"
        Check if a URL is accessible without full scraping.
        
        Args:
            url: URL to validate
            timeout: Maximum time to wait for response
            
        Returns:
            True if URL is accessible, False otherwise
        \"\"\"
        pass
    
    @abstractmethod
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        depth: int = 1
    ) -> List[str]:
        \"\"\"
        Discover links from a URL without full content extraction.
        
        Args:
            url: URL to discover links from
            config: Scraping configuration
            depth: How many levels deep to follow links
            
        Returns:
            List of discovered URLs
        \"\"\"
        pass
    
    @abstractmethod
    def get_supported_features(self) -> Dict[str, bool]:
        \"\"\"
        Get capabilities supported by this scraper implementation.
        
        Returns:
            Dictionary mapping feature names to support status
        \"\"\"
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        \"\"\"
        Get current health and performance status.
        
        Returns:
            Dictionary with health information
        \"\"\"
        pass
    
    # Context manager support for resource management
    @abstractmethod
    async def __aenter__(self):
        \"\"\"Async context manager entry\"\"\"
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        \"\"\"Async context manager exit\"\"\"
        pass

class StreamingWebScraper(WebScraper):
    \"\"\"Extended interface for streaming/real-time scraping\"\"\"
    
    @abstractmethod
    async def scrape_stream(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None
    ) -> AsyncIterator[PageResult]:
        \"\"\"
        Scrape pages and yield results as they complete.
        
        Args:
            urls: URLs to scrape
            config: Scraping configuration
            
        Yields:
            PageResult objects as they complete
        \"\"\"
        pass
    
    @abstractmethod
    async def scrape_with_discovery_stream(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None
    ) -> AsyncIterator[PageResult]:
        \"\"\"
        Discover and scrape pages, yielding results in real-time.
        
        Args:
            base_url: Starting URL
            config: Scraping configuration
            
        Yields:
            PageResult objects as pages are discovered and scraped
        \"\"\"
        pass

class CacheableWebScraper(WebScraper):
    \"\"\"Extended interface with caching capabilities\"\"\"
    
    @abstractmethod
    async def scrape_with_cache(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        cache_ttl: Optional[int] = None
    ) -> PageResult:
        \"\"\"
        Scrape with caching support.
        
        Args:
            url: URL to scrape
            config: Scraping configuration
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            PageResult (may be from cache)
        \"\"\"
        pass
    
    @abstractmethod
    async def clear_cache(self, url_pattern: Optional[str] = None) -> int:
        \"\"\"
        Clear cached results.
        
        Args:
            url_pattern: Optional pattern to match URLs (clears all if None)
            
        Returns:
            Number of cache entries cleared
        \"\"\"
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        \"\"\"
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics
        \"\"\"
        pass

# Factory interface for creating scrapers
class WebScraperFactory(ABC):
    \"\"\"Factory for creating web scraper instances\"\"\"
    
    @abstractmethod
    def create_scraper(
        self,
        scraper_type: str = \"default\",
        **kwargs
    ) -> WebScraperPort:
        \"\"\"
        Create a web scraper instance.
        
        Args:
            scraper_type: Type of scraper to create
            **kwargs: Additional configuration
            
        Returns:
            WebScraperPort implementation
        \"\"\"
        pass
    
    @abstractmethod
    def get_available_scrapers(self) -> List[str]:
        \"\"\"
        Get list of available scraper types.
        
        Returns:
            List of scraper type names
        \"\"\"
        pass
```

**[SLIDE 10: Interface Design Principles]**

"Key design decisions explained:

1. **Progressive Complexity**: Single page → Multiple pages → Recursive crawling
2. **Flexible Configuration**: Optional configs with sensible defaults
3. **Progress Integration**: Built-in support for progress tracking
4. **Error Granularity**: Specific exceptions for different failure types
5. **Feature Discovery**: Implementations can advertise their capabilities
6. **Resource Management**: Context manager support for cleanup

**[SLIDE 11: Extended Interfaces]**

"Notice the specialized interfaces:

- **StreamingWebScraper**: For real-time results as they arrive
- **CacheableWebScraper**: For performance optimization
- **WebScraperFactory**: For creating different scraper types

This allows implementations to opt into advanced features!"

## Section 5: Creating Mock Implementation for Testing (10 minutes)

**[SLIDE 12: Mock Implementation]**

"Let's create a mock implementation for testing:

```python
# v2/tests/unit/interfaces/test_web_scraper_mock.py

import asyncio
import pytest
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from unittest.mock import AsyncMock
import time
import random

from v2.src.core.interfaces.web_scraper import (
    WebScraperPort, StreamingWebScraperPort, 
    ScrapingTimeoutException, BlockedException
)
from v2.src.core.domain.value_objects.scraping_config import ScrapingConfig, ScrapingMode
from v2.src.core.domain.value_objects.scraping_result import (
    ScrapingResult, PageResult, PageStatus, ScrapingStatus
)

class MockWebScraper(StreamingWebScraperPort):
    \"\"\"Mock web scraper for testing\"\"\"
    
    def __init__(self, 
                 simulate_delays: bool = True,
                 failure_rate: float = 0.1,
                 blocked_domains: List[str] = None):
        self.simulate_delays = simulate_delays
        self.failure_rate = failure_rate
        self.blocked_domains = blocked_domains or [\"blocked-site.com\"]
        self.request_count = 0
        self.is_initialized = False
        
        # Mock content database
        self.mock_content = {
            \"https://apple.com\": \"Apple Inc. is a technology company...\",
            \"https://microsoft.com\": \"Microsoft Corporation develops software...\",
            \"https://google.com\": \"Google LLC is a search engine company...\",
            \"https://example.com/about\": \"About us page content...\",
            \"https://example.com/contact\": \"Contact information...\",
            \"https://slow-site.com\": \"This content loads slowly...\"
        }
        
        self.mock_links = {
            \"https://example.com\": [
                \"https://example.com/about\",
                \"https://example.com/contact\",
                \"https://example.com/products\"
            ]
        }
    
    async def __aenter__(self):
        self.is_initialized = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.is_initialized = False
    
    async def scrape_single_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[Callable] = None
    ) -> PageResult:
        \"\"\"Mock single page scraping\"\"\"
        
        if not self.is_initialized:
            raise RuntimeError(\"Scraper not initialized. Use 'async with' context.\")
        
        self.request_count += 1
        
        # Simulate progress
        if progress_callback:
            progress_callback(f\"Scraping {url}\", 0.0, \"Starting...\")
        
        # Simulate delay
        if self.simulate_delays:
            if \"slow-site.com\" in url:
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Check for blocked domains
        if any(blocked in url for blocked in self.blocked_domains):
            if progress_callback:
                progress_callback(f\"Scraping {url}\", 1.0, \"Blocked\")
            raise BlockedException(f\"Access blocked for {url}\")
        
        # Simulate random failures
        if random.random() < self.failure_rate:
            if progress_callback:
                progress_callback(f\"Scraping {url}\", 1.0, \"Failed\")
            return PageResult(
                url=url,
                status=PageStatus.FAILED,
                error_message=\"Simulated network error\",
                response_time=0.5
            )
        
        # Return mock content
        content = self.mock_content.get(url, f\"Mock content for {url}\")
        links = self.mock_links.get(url, [])
        
        if progress_callback:
            progress_callback(f\"Scraping {url}\", 1.0, \"Complete\")
        
        return PageResult(
            url=url,
            status=PageStatus.SUCCESS,
            content=content,
            links=links,
            metadata={\"mock\": True, \"request_count\": self.request_count},
            response_time=random.uniform(0.1, 2.0),
            status_code=200,
            content_length=len(content)
        )
    
    async def scrape_multiple_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[Callable] = None
    ) -> ScrapingResult:
        \"\"\"Mock multiple page scraping\"\"\"
        
        config = config or ScrapingConfig()
        operation_id = f\"mock_op_{int(time.time())}\"
        
        result = ScrapingResult(
            operation_id=operation_id,
            status=ScrapingStatus.SUCCESS,
            config=config
        )
        
        # Process pages
        for i, url in enumerate(urls):
            if progress_callback:
                progress = (i + 1) / len(urls)
                progress_callback(f\"Processing {url}\", progress, f\"Page {i+1}/{len(urls)}\")
            
            try:
                page_result = await self.scrape_single_page(url, config)
                result.add_page_result(page_result)
                
                # Respect rate limiting
                if config.rate_limit.requests_per_second > 0:
                    delay = 1.0 / config.rate_limit.requests_per_second
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                page_result = PageResult(
                    url=url,
                    status=PageStatus.FAILED,
                    error_message=str(e),
                    response_time=0.0
                )
                result.add_page_result(page_result)
        
        result.finalize()
        return result
    
    async def scrape_website(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None,
        url_filter: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ) -> ScrapingResult:
        \"\"\"Mock website scraping with discovery\"\"\"
        
        config = config or ScrapingConfig()
        
        # Discover URLs (mock)
        discovered_urls = [base_url]
        if base_url in self.mock_links:
            discovered_urls.extend(self.mock_links[base_url])
        
        # Apply filter
        if url_filter:
            discovered_urls = [url for url in discovered_urls if url_filter(url)]
        
        # Limit by config
        discovered_urls = discovered_urls[:config.max_pages]
        
        return await self.scrape_multiple_pages(discovered_urls, config, progress_callback)
    
    async def scrape_with_progress(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_tracker = None
    ) -> ScrapingResult:
        \"\"\"Mock scraping with progress tracker\"\"\"
        
        # Convert progress tracker to callback
        def progress_callback(message: str, progress: float, details: str):
            if progress_tracker:
                # Mock progress tracker update
                pass
        
        return await self.scrape_multiple_pages(urls, config, progress_callback)
    
    async def validate_url(self, url: str, timeout: float = 5.0) -> bool:
        \"\"\"Mock URL validation\"\"\"
        
        if any(blocked in url for blocked in self.blocked_domains):
            return False
        
        # Simulate timeout for slow sites
        if \"slow-site.com\" in url and timeout < 2.0:
            return False
        
        return random.random() > 0.05  # 5% failure rate
    
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        depth: int = 1
    ) -> List[str]:
        \"\"\"Mock link discovery\"\"\"
        
        links = self.mock_links.get(url, [])
        
        if depth > 1:
            # Recursively discover more links
            additional_links = []
            for link in links:
                sub_links = self.mock_links.get(link, [])
                additional_links.extend(sub_links)
            links.extend(additional_links)
        
        return list(set(links))  # Deduplicate
    
    def get_supported_features(self) -> Dict[str, bool]:
        \"\"\"Mock feature support\"\"\"
        return {
            \"javascript\": True,
            \"cookies\": True,
            \"custom_headers\": True,
            \"proxy_support\": False,
            \"streaming\": True,
            \"caching\": False,
            \"rate_limiting\": True
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        \"\"\"Mock health status\"\"\"
        return {
            \"status\": \"healthy\",
            \"requests_processed\": self.request_count,
            \"average_response_time\": 0.3,
            \"success_rate\": 1.0 - self.failure_rate,
            \"last_check\": time.time()
        }
    
    async def scrape_stream(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None
    ) -> AsyncIterator[PageResult]:
        \"\"\"Mock streaming scraper\"\"\"
        
        for url in urls:
            page_result = await self.scrape_single_page(url, config)
            yield page_result
    
    async def scrape_with_discovery_stream(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None
    ) -> AsyncIterator[PageResult]:
        \"\"\"Mock discovery and streaming\"\"\"
        
        # Discover URLs
        urls = await self.discover_links(base_url, config, depth=2)
        urls = [base_url] + urls
        
        # Stream results
        async for page_result in self.scrape_stream(urls, config):
            yield page_result

# Test cases using the mock
class TestWebScraperInterface:
    
    @pytest.fixture
    async def mock_scraper(self):
        async with MockWebScraper(failure_rate=0.0) as scraper:
            yield scraper
    
    @pytest.mark.asyncio
    async def test_single_page_scraping(self, mock_scraper):
        \"\"\"Test single page scraping\"\"\"
        result = await mock_scraper.scrape_single_page(\"https://apple.com\")
        
        assert result.status == PageStatus.SUCCESS
        assert \"Apple Inc.\" in result.content
        assert result.url == \"https://apple.com\"
        assert result.response_time > 0
    
    @pytest.mark.asyncio
    async def test_multiple_page_scraping(self, mock_scraper):
        \"\"\"Test multiple page scraping\"\"\"
        urls = [\"https://apple.com\", \"https://microsoft.com\", \"https://google.com\"]
        
        result = await mock_scraper.scrape_multiple_pages(urls)
        
        assert result.is_successful
        assert len(result.pages) == 3
        assert result.metrics.pages_successful == 3
        assert result.has_content
    
    @pytest.mark.asyncio
    async def test_website_scraping_with_discovery(self, mock_scraper):
        \"\"\"Test recursive website scraping\"\"\"
        result = await mock_scraper.scrape_website(\"https://example.com\")
        
        assert result.is_successful
        assert len(result.pages) > 1  # Should include discovered pages
        assert any(\"about\" in page.url for page in result.pages)
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, mock_scraper):
        \"\"\"Test progress tracking\"\"\"
        progress_updates = []
        
        def track_progress(message: str, progress: float, details: str):
            progress_updates.append((message, progress, details))
        
        await mock_scraper.scrape_single_page(
            \"https://apple.com\", 
            progress_callback=track_progress
        )
        
        assert len(progress_updates) >= 2  # Start and end
        assert progress_updates[0][1] == 0.0  # Start progress
        assert progress_updates[-1][1] == 1.0  # End progress
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        \"\"\"Test error scenarios\"\"\"
        async with MockWebScraper(blocked_domains=[\"blocked.com\"]) as scraper:
            
            # Test blocked domain
            with pytest.raises(BlockedException):
                await scraper.scrape_single_page(\"https://blocked.com\")
    
    @pytest.mark.asyncio
    async def test_streaming_interface(self, mock_scraper):
        \"\"\"Test streaming scraper\"\"\"
        urls = [\"https://apple.com\", \"https://microsoft.com\"]
        results = []
        
        async for page_result in mock_scraper.scrape_stream(urls):
            results.append(page_result)
        
        assert len(results) == 2
        assert all(result.is_successful for result in results)
    
    @pytest.mark.asyncio
    async def test_feature_discovery(self, mock_scraper):
        \"\"\"Test feature capability discovery\"\"\"
        features = mock_scraper.get_supported_features()
        
        assert isinstance(features, dict)
        assert \"javascript\" in features
        assert \"streaming\" in features
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, mock_scraper):
        \"\"\"Test health status reporting\"\"\"
        # Make some requests first
        await mock_scraper.scrape_single_page(\"https://apple.com\")
        
        health = await mock_scraper.get_health_status()
        
        assert health[\"status\"] == \"healthy\"
        assert health[\"requests_processed\"] > 0
        assert \"success_rate\" in health
    
    def test_configuration_validation(self):
        \"\"\"Test configuration validation\"\"\"
        config = ScrapingConfig(
            mode=ScrapingMode.SINGLE_PAGE,
            timeout=30.0,
            max_pages=10
        )
        
        assert config.mode == ScrapingMode.SINGLE_PAGE
        assert config.timeout == 30.0
        assert config.get_effective_user_agent().startswith(\"Mozilla\")
    
    def test_result_aggregation(self):
        \"\"\"Test result object behavior\"\"\"
        result = ScrapingResult(
            operation_id=\"test_123\",
            status=ScrapingStatus.SUCCESS,
            config=ScrapingConfig()
        )
        
        # Add some page results
        page1 = PageResult(url=\"https://example.com\", status=PageStatus.SUCCESS, content=\"Content 1\")
        page2 = PageResult(url=\"https://example.com/about\", status=PageStatus.SUCCESS, content=\"Content 2\")
        
        result.add_page_result(page1)
        result.add_page_result(page2)
        result.finalize()
        
        assert len(result.pages) == 2
        assert result.metrics.pages_successful == 2
        assert result.metrics.success_rate == 1.0
        assert \"Content 1\" in result.primary_content
        assert \"Content 2\" in result.primary_content
```

**[SLIDE 13: Testing Strategy Benefits]**

"This mock implementation provides:

1. **Deterministic Testing**: Predictable behavior for unit tests
2. **Error Simulation**: Test how your code handles failures
3. **Performance Testing**: Control timing and delays
4. **Feature Validation**: Verify interface contracts
5. **Progress Tracking**: Test UI update mechanisms

**[PRACTICAL EXERCISE]** \"Try creating a test that simulates a partially successful scraping operation where some pages fail!\"

## Section 6: Advanced Interface Patterns (8 minutes)

**[SLIDE 14: Composition and Decoration]**

"Let's explore advanced patterns for extending scrapers:

```python
# Decorator pattern for adding features
class RateLimitedWebScraper:
    \"\"\"Decorator that adds rate limiting to any scraper\"\"\"
    
    def __init__(self, scraper: WebScraperPort, rate_limit: float = 1.0):
        self.scraper = scraper
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
    
    async def scrape_single_page(self, url: str, config=None, progress_callback=None):
        # Apply rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < (1.0 / self.rate_limit):
            await asyncio.sleep((1.0 / self.rate_limit) - elapsed)
        
        self.last_request_time = time.time()
        return await self.scraper.scrape_single_page(url, config, progress_callback)

# Caching decorator
class CachedWebScraper:
    \"\"\"Decorator that adds caching to any scraper\"\"\"
    
    def __init__(self, scraper: WebScraperPort, cache_ttl: int = 3600):
        self.scraper = scraper
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    async def scrape_single_page(self, url: str, config=None, progress_callback=None):
        # Check cache
        cache_key = f\"{url}:{hash(str(config))}\"}
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        # Scrape and cache
        result = await self.scraper.scrape_single_page(url, config, progress_callback)
        self.cache[cache_key] = (result, time.time())
        return result

# Retry decorator
class RetryingWebScraper:
    \"\"\"Decorator that adds retry logic to any scraper\"\"\"
    
    def __init__(self, scraper: WebScraperPort, max_retries: int = 3):
        self.scraper = scraper
        self.max_retries = max_retries
    
    async def scrape_single_page(self, url: str, config=None, progress_callback=None):
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await self.scraper.scrape_single_page(url, config, progress_callback)
            except (ScrapingTimeoutException, RateLimitedException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(delay)
                continue
            except Exception:
                # Don't retry on other errors
                raise
        
        raise last_exception

# Usage example
async def create_production_scraper():
    base_scraper = SomeCrawl4AIAdapter()
    
    # Compose features
    scraper = RateLimitedWebScraper(
        CachedWebScraper(
            RetryingWebScraper(base_scraper, max_retries=3),
            cache_ttl=1800
        ),
        rate_limit=2.0
    )
    
    return scraper
```

**[SLIDE 15: Plugin Architecture]**

"Design for extensibility with plugins:

```python
class ScraperPlugin(ABC):
    \"\"\"Base class for scraper plugins\"\"\"
    
    @abstractmethod
    async def before_scrape(self, url: str, config: ScrapingConfig) -> ScrapingConfig:
        \"\"\"Called before scraping each page\"\"\"
        pass
    
    @abstractmethod
    async def after_scrape(self, url: str, result: PageResult) -> PageResult:
        \"\"\"Called after scraping each page\"\"\"
        pass

class MetricsPlugin(ScraperPlugin):
    \"\"\"Plugin that collects detailed metrics\"\"\"
    
    def __init__(self):
        self.metrics = {
            \"urls_processed\": 0,
            \"total_time\": 0.0,
            \"content_size_by_domain\": {}
        }
    
    async def before_scrape(self, url: str, config: ScrapingConfig) -> ScrapingConfig:
        self.start_time = time.time()
        return config
    
    async def after_scrape(self, url: str, result: PageResult) -> PageResult:
        duration = time.time() - self.start_time
        
        self.metrics[\"urls_processed\"] += 1
        self.metrics[\"total_time\"] += duration
        
        domain = urlparse(url).netloc
        if domain not in self.metrics[\"content_size_by_domain\"]:
            self.metrics[\"content_size_by_domain\"][domain] = 0
        self.metrics[\"content_size_by_domain\"][domain] += result.content_length
        
        return result

class PluginAwareWebScraper:
    \"\"\"Scraper that supports plugins\"\"\"
    
    def __init__(self, base_scraper: WebScraperPort):
        self.base_scraper = base_scraper
        self.plugins: List[ScraperPlugin] = []
    
    def add_plugin(self, plugin: ScraperPlugin):
        self.plugins.append(plugin)
    
    async def scrape_single_page(self, url: str, config=None, progress_callback=None):
        config = config or ScrapingConfig()
        
        # Run before_scrape plugins
        for plugin in self.plugins:
            config = await plugin.before_scrape(url, config)
        
        # Perform scraping
        result = await self.base_scraper.scrape_single_page(url, config, progress_callback)
        
        # Run after_scrape plugins
        for plugin in self.plugins:
            result = await plugin.after_scrape(url, result)
        
        return result
```

## Section 7: Real-World Integration Patterns (5 minutes)

**[SLIDE 16: Dependency Injection Integration]**

"How this fits into Theodore's dependency injection:

```python
# Container configuration
class ScrapingContainer:
    def __init__(self):
        self._scrapers = {}
        self._default_scraper = None
    
    def register_scraper(self, name: str, factory: Callable[[], WebScraperPort]):
        self._scrapers[name] = factory
    
    def set_default(self, name: str):
        self._default_scraper = name
    
    def get_scraper(self, name: Optional[str] = None) -> WebScraperPort:
        scraper_name = name or self._default_scraper
        if scraper_name not in self._scrapers:
            raise ValueError(f\"Unknown scraper: {scraper_name}\")
        return self._scrapers[scraper_name]()

# Usage in application
container = ScrapingContainer()
container.register_scraper(\"crawl4ai\", lambda: Crawl4AIAdapter())
container.register_scraper(\"playwright\", lambda: PlaywrightAdapter())
container.register_scraper(\"mock\", lambda: MockWebScraper())
container.set_default(\"crawl4ai\")

# In use cases
class ResearchCompanyUseCase:
    def __init__(self, scraper_container: ScrapingContainer):
        self.scraper_container = scraper_container
    
    async def execute(self, company_url: str, scraper_type: Optional[str] = None):
        scraper = self.scraper_container.get_scraper(scraper_type)
        
        async with scraper:
            config = ScrapingConfig.for_company_research()
            result = await scraper.scrape_website(company_url, config)
            return self._analyze_content(result)
```

**[SLIDE 17: CLI Integration]**

"Beautiful CLI integration:

```bash
# CLI commands using the interface
$ theodore scrape \"https://apple.com\" --scraper crawl4ai --config company_research

🕷️ Scraping with Crawl4AI
┌─────────────────────────────────────────────────────────────┐
│ Scraping Progress                                           │
├─────────────────────────────────────────────────────────────┤
│ URL: https://apple.com                                      │
│ Mode: Multi-page Discovery                                  │
│ Progress: ████████████████████ 100% │ 12/12 pages          │
│ Success Rate: 91.7%                                         │
│ Duration: 23.4s                                             │
└─────────────────────────────────────────────────────────────┘

Results:
✅ 11 pages scraped successfully
❌ 1 page failed (timeout)
📄 Content: 47,234 characters
🔗 Links: 156 discovered
💾 Saved to: apple_com_20240615.json

$ theodore scrape --help
Available scrapers: crawl4ai, playwright, mock
Available configs: company_research, fast_preview, comprehensive
```

## Conclusion (2 minutes)

**[SLIDE 18: What We Built]**

"Congratulations! You've designed a comprehensive web scraper interface that:

✅ **Supports multiple scraping strategies** through clean abstractions
✅ **Handles complex scenarios** from single pages to recursive crawling  
✅ **Integrates with progress tracking** for real-time user feedback
✅ **Provides rich error handling** with specific exception types
✅ **Enables testing** with comprehensive mock implementations
✅ **Supports extensibility** through plugins and decorators

**[SLIDE 19: Real-World Impact]**

"This interface design enables:
- **Technology flexibility**: Switch between Crawl4AI, Playwright, or future tools
- **Testing confidence**: Mock implementations for reliable unit tests
- **Progressive enhancement**: Add features like caching and rate limiting
- **Performance optimization**: Stream results and track metrics
- **Production readiness**: Comprehensive error handling and monitoring

**[FINAL THOUGHT]**
"Great interfaces are like great APIs - they hide complexity while exposing power. This scraper interface lets you build sophisticated web scraping systems while keeping implementations clean and testable.

Thank you for designing something that will serve as the foundation for countless scraping innovations!"

---

## Instructor Notes:
- Total runtime: ~53 minutes
- Emphasize the power of abstraction in enabling technology choice
- Live demo the mock implementation to show interface compliance
- Highlight how this enables both simple and complex scraping scenarios
- Show real examples of how decorators compose to add features
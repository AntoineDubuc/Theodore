#!/usr/bin/env python3
"""
Theodore v2 Web Scraper Port Interface

Defines the abstract interface for web scraping operations that can be implemented
by different scraping providers (Crawl4AI, Playwright, Beautiful Soup, etc).
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Dict, Any, Union, Callable
from urllib.parse import urljoin, urlparse
import asyncio
from contextlib import asynccontextmanager

from ..domain.value_objects.scraping_config import ScrapingConfig
from ..domain.value_objects.scraping_result import ScrapingResult, PageResult


class ProgressCallback:
    """Callback interface for scraping progress updates"""
    
    def __init__(self, callback_fn: Optional[Callable[[str, float, Dict[str, Any]], None]] = None):
        self.callback_fn = callback_fn
    
    def update(self, message: str, progress: float, metadata: Optional[Dict[str, Any]] = None):
        """Update progress with message and percentage (0.0 to 1.0)"""
        if self.callback_fn:
            self.callback_fn(message, progress, metadata or {})
    
    def __call__(self, message: str, progress: float, metadata: Optional[Dict[str, Any]] = None):
        self.update(message, progress, metadata)


class WebScraperError(Exception):
    """Base exception for web scraping errors"""
    pass


class ScrapingTimeoutError(WebScraperError):
    """Raised when scraping operation times out"""
    pass


class ScrapingRateLimitError(WebScraperError):
    """Raised when rate limits are exceeded"""
    pass


class ScrapingBlockedError(WebScraperError):
    """Raised when scraping is blocked by the target site"""
    pass


class ScrapingConfigError(WebScraperError):
    """Raised when scraping configuration is invalid"""
    pass


class WebScraper(ABC):
    """
    Abstract interface for web scraping operations.
    
    This interface supports:
    - Single page scraping with content extraction
    - Multi-page scraping with link discovery
    - Recursive website crawling
    - Progress tracking and real-time updates
    - Rate limiting and retry mechanisms
    - Content filtering and processing
    """
    
    @abstractmethod
    async def scrape_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PageResult:
        """
        Scrape a single page and extract content.
        
        Args:
            url: URL to scrape
            config: Scraping configuration (uses default if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            PageResult with extracted content and metadata
            
        Raises:
            ScrapingTimeoutError: If operation times out
            ScrapingBlockedError: If scraping is blocked
            WebScraperError: For other scraping failures
        """
        pass
    
    @abstractmethod
    async def scrape_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """
        Scrape multiple pages in parallel or sequence.
        
        Args:
            urls: List of URLs to scrape
            config: Scraping configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScrapingResult with all page results and aggregated data
        """
        pass
    
    @abstractmethod
    async def crawl_website(
        self,
        start_url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """
        Recursively crawl a website starting from the given URL.
        
        Args:
            start_url: Starting URL for crawling
            config: Scraping configuration (must include crawl settings)
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScrapingResult with all discovered and scraped pages
        """
        pass
    
    @abstractmethod
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[str]:
        """
        Discover and extract all links from a page without full content scraping.
        
        Args:
            url: URL to analyze for links
            config: Scraping configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of discovered URLs
        """
        pass
    
    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is accessible and scrapable.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and accessible
        """
        pass
    
    @abstractmethod
    async def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic page information without full content extraction.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary with page metadata (title, status, size, etc.)
        """
        pass
    
    @abstractmethod
    def supports_javascript(self) -> bool:
        """
        Check if this scraper implementation supports JavaScript execution.
        
        Returns:
            True if JavaScript is supported
        """
        pass
    
    @abstractmethod
    def get_supported_content_types(self) -> List[str]:
        """
        Get list of content types this scraper can extract.
        
        Returns:
            List of supported content type strings
        """
        pass


class StreamingWebScraper(WebScraper):
    """
    Extended interface for scrapers that support streaming results.
    
    Allows real-time processing of scraped content as it becomes available.
    """
    
    @abstractmethod
    async def scrape_page_stream(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> AsyncIterator[PageResult]:
        """
        Stream page scraping results as they become available.
        
        Args:
            url: URL to scrape
            config: Scraping configuration
            progress_callback: Optional callback for progress updates
            
        Yields:
            PageResult objects as content is extracted
        """
        pass
    
    @abstractmethod
    async def crawl_website_stream(
        self,
        start_url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> AsyncIterator[PageResult]:
        """
        Stream crawling results as pages are discovered and scraped.
        
        Args:
            start_url: Starting URL for crawling
            config: Scraping configuration
            progress_callback: Optional callback for progress updates
            
        Yields:
            PageResult objects as pages are scraped
        """
        pass


class DecoratedWebScraper(WebScraper):
    """
    Base class for decorator pattern implementations.
    
    Allows adding functionality like caching, rate limiting, retry logic,
    or content filtering on top of existing scrapers.
    """
    
    def __init__(self, wrapped_scraper: WebScraper):
        self.wrapped_scraper = wrapped_scraper
    
    async def scrape_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PageResult:
        return await self.wrapped_scraper.scrape_page(url, config, progress_callback)
    
    async def scrape_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        return await self.wrapped_scraper.scrape_pages(urls, config, progress_callback)
    
    async def crawl_website(
        self,
        start_url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        return await self.wrapped_scraper.crawl_website(start_url, config, progress_callback)
    
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[str]:
        return await self.wrapped_scraper.discover_links(url, config, progress_callback)
    
    async def validate_url(self, url: str) -> bool:
        return await self.wrapped_scraper.validate_url(url)
    
    async def get_page_info(self, url: str) -> Dict[str, Any]:
        return await self.wrapped_scraper.get_page_info(url)
    
    def supports_javascript(self) -> bool:
        return self.wrapped_scraper.supports_javascript()
    
    def get_supported_content_types(self) -> List[str]:
        return self.wrapped_scraper.get_supported_content_types()


class WebScraperFactory:
    """
    Factory for creating web scraper instances with different configurations.
    """
    
    @staticmethod
    def create_for_company_research() -> WebScraper:
        """
        Create a scraper optimized for company research.
        
        Returns:
            Configured WebScraper instance
        """
        raise NotImplementedError("Factory method must be implemented by concrete factory")
    
    @staticmethod
    def create_for_fast_preview() -> WebScraper:
        """
        Create a scraper optimized for fast page previews.
        
        Returns:
            Configured WebScraper instance
        """
        raise NotImplementedError("Factory method must be implemented by concrete factory")
    
    @staticmethod
    def create_with_config(config: ScrapingConfig) -> WebScraper:
        """
        Create a scraper with specific configuration.
        
        Args:
            config: Scraping configuration to use
            
        Returns:
            Configured WebScraper instance
        """
        raise NotImplementedError("Factory method must be implemented by concrete factory")


class WebScraperContext:
    """
    Context manager for web scraper operations with automatic cleanup.
    """
    
    def __init__(self, scraper: WebScraper):
        self.scraper = scraper
    
    @asynccontextmanager
    async def scraping_session(self):
        """
        Create a scraping session with automatic resource cleanup.
        
        Usage:
            async with WebScraperContext(scraper).scraping_session() as session:
                result = await session.scrape_page(url)
        """
        try:
            yield self.scraper
        finally:
            # Cleanup logic would go here
            # (close browser sessions, clear caches, etc.)
            pass


# Utility functions for working with scrapers

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is structurally valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL structure is valid
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize a URL, handling relative URLs if base is provided.
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized absolute URL
    """
    if base_url and not url.startswith(('http://', 'https://')):
        return urljoin(base_url, url)
    return url


def create_progress_callback(
    on_update: Optional[Callable[[str, float, Dict[str, Any]], None]] = None
) -> ProgressCallback:
    """
    Create a progress callback with optional custom handler.
    
    Args:
        on_update: Optional custom update handler
        
    Returns:
        ProgressCallback instance
    """
    return ProgressCallback(on_update)


# Type aliases for convenience
ScrapingOperation = Union[
    WebScraper.scrape_page,
    WebScraper.scrape_pages,
    WebScraper.crawl_website
]

ScrapingProvider = Union[WebScraper, StreamingWebScraper, DecoratedWebScraper]
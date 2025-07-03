#!/usr/bin/env python3
"""
Mock implementation of WebScraper for testing.

Provides a simple mock scraper that can be used for unit tests
without requiring actual web requests or browser automation.
"""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

from .web_scraper import (
    WebScraper, 
    ProgressCallback,
    WebScraperError,
    ScrapingTimeoutError,
    ScrapingBlockedError,
    ScrapingRateLimitError,
    is_valid_url
)
from ..domain.value_objects.scraping_config import ScrapingConfig, ContentType
from ..domain.value_objects.scraping_result import (
    ScrapingResult, 
    PageResult, 
    PageStatus,
    ScrapingStatus
)


class MockWebScraper(WebScraper):
    """
    Mock web scraper for testing.
    
    Simulates scraping behavior without making real HTTP requests.
    Useful for unit tests and development.
    """
    
    def __init__(self, 
                 base_delay: float = 0.1,
                 failure_rate: float = 0.0,
                 timeout_rate: float = 0.0,
                 block_rate: float = 0.0,
                 mock_content: Optional[Dict[str, str]] = None):
        """
        Initialize mock scraper.
        
        Args:
            base_delay: Base delay for simulating request time
            failure_rate: Probability (0.0-1.0) of random failures
            timeout_rate: Probability (0.0-1.0) of timeouts
            block_rate: Probability (0.0-1.0) of being blocked
            mock_content: Dictionary mapping URLs to mock content
        """
        self.base_delay = base_delay
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        self.block_rate = block_rate
        self.mock_content = mock_content or {}
        
        # Statistics tracking
        self.requests_processed = 0
        self.success_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        self._supported_content_types = [
            ContentType.TEXT.value,
            ContentType.MARKDOWN.value,
            ContentType.HTML.value,
            ContentType.LINKS.value,
            ContentType.IMAGES.value
        ]
    
    async def scrape_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PageResult:
        """Mock single page scraping"""
        
        if progress_callback:
            progress_callback("Starting page scrape", 0.0)
        
        # Validate URL
        if not is_valid_url(url):
            raise WebScraperError(f"Invalid URL: {url}")
        
        config = config or ScrapingConfig()
        
        # Simulate timeout
        if random.random() < self.timeout_rate:
            raise ScrapingTimeoutError(f"Mock timeout for {url}")
        
        # Simulate being blocked
        if random.random() < self.block_rate:
            raise ScrapingBlockedError(f"Mock blocking for {url}")
        
        # Simulate processing delay
        response_time = self.base_delay + random.uniform(0, self.base_delay)
        await asyncio.sleep(response_time)
        
        self.requests_processed += 1
        self.total_response_time += response_time
        
        # Simulate random failures
        if random.random() < self.failure_rate:
            self.error_count += 1
            return PageResult(
                url=url,
                status=PageStatus.FAILED,
                error_message="Mock failure scenario",
                response_time=response_time,
                status_code=500,
                scraped_at=datetime.now(timezone.utc)
            )
        
        # Generate mock content
        mock_content = self.mock_content.get(url, f"Mock content for {url}.\n\nThis is comprehensive mock content that simulates real webpage text extraction. The content includes various elements that might be found on a typical webpage.")
        
        # Generate mock links based on URL
        base_url = url.rstrip('/')
        mock_links = [
            f"{base_url}/about",
            f"{base_url}/contact", 
            f"{base_url}/services",
            f"{base_url}/products",
            f"{base_url}/team",
            f"{base_url}/careers"
        ]
        
        # Generate mock images
        mock_images = [
            f"{base_url}/images/logo.png",
            f"{base_url}/images/hero.jpg",
            f"{base_url}/images/team.jpg"
        ]
        
        if progress_callback:
            progress_callback("Extracting content", 0.5)
        
        # Create successful page result
        result = PageResult(
            url=url,
            status=PageStatus.SUCCESS,
            content=mock_content,
            html=f"<html><head><title>Mock Page - {url}</title></head><body>{mock_content}</body></html>",
            links=mock_links,
            images=mock_images,
            metadata={
                "title": f"Mock Page - {url}",
                "description": f"Mock description for {url}",
                "keywords": ["mock", "test", "scraping"],
                "language": "en",
                "author": "Mock Author"
            },
            response_time=response_time,
            status_code=200,
            content_length=len(mock_content),
            scraped_at=datetime.now(timezone.utc)
        )
        
        self.success_count += 1
        
        if progress_callback:
            progress_callback("Page scraping complete", 1.0)
        
        return result
    
    async def scrape_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """Mock multiple page scraping"""
        
        if not urls:
            raise WebScraperError("No URLs provided")
        
        config = config or ScrapingConfig()
        
        # Create result container
        operation_id = f"mock_scrape_{self.requests_processed}"
        result = ScrapingResult(
            operation_id=operation_id,
            status=ScrapingStatus.SUCCESS,
            config=config.to_dict()
        )
        
        total_urls = len(urls)
        
        # Process each URL
        for i, url in enumerate(urls):
            if progress_callback:
                progress = (i + 1) / total_urls
                progress_callback(f"Scraping {url}", progress)
            
            try:
                page_result = await self.scrape_page(url, config)
                result.add_page_result(page_result)
            except Exception as e:
                # Add failed page result
                failed_result = PageResult(
                    url=url,
                    status=PageStatus.FAILED,
                    error_message=str(e),
                    scraped_at=datetime.now(timezone.utc)
                )
                result.add_page_result(failed_result)
                result.error_details.append(str(e))
        
        # Finalize result
        result.finalize()
        
        if progress_callback:
            progress_callback("Scraping complete", 1.0)
        
        return result
    
    async def crawl_website(
        self,
        start_url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """Mock website crawling"""
        
        config = config or ScrapingConfig()
        
        # Generate mock URLs to crawl based on start_url
        base_url = start_url.rstrip('/')
        discovered_urls = [
            start_url,
            f"{base_url}/about",
            f"{base_url}/contact", 
            f"{base_url}/services",
            f"{base_url}/products",
            f"{base_url}/team",
            f"{base_url}/careers",
            f"{base_url}/blog",
            f"{base_url}/news",
            f"{base_url}/support"
        ]
        
        # Limit based on config
        max_pages = getattr(config, 'max_pages', 50)
        discovered_urls = discovered_urls[:max_pages]
        
        if progress_callback:
            progress_callback(f"Discovered {len(discovered_urls)} URLs", 0.1)
        
        # Use scrape_pages to process discovered URLs
        return await self.scrape_pages(discovered_urls, config, progress_callback)
    
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[str]:
        """Mock link discovery"""
        
        if progress_callback:
            progress_callback("Discovering links", 0.5)
        
        # Simulate delay
        await asyncio.sleep(self.base_delay * 0.5)
        
        # Generate mock links based on URL
        base_url = url.rstrip('/')
        mock_links = [
            url,  # Include the original URL
            f"{base_url}/about",
            f"{base_url}/contact",
            f"{base_url}/services", 
            f"{base_url}/products",
            f"{base_url}/team",
            f"{base_url}/careers",
            f"{base_url}/blog",
            f"{base_url}/news",
            f"{base_url}/support",
            f"{base_url}/privacy",
            f"{base_url}/terms"
        ]
        
        if progress_callback:
            progress_callback("Link discovery complete", 1.0)
        
        return mock_links
    
    async def validate_url(self, url: str) -> bool:
        """Mock URL validation"""
        
        # Basic validation
        if not is_valid_url(url):
            return False
        
        # Simulate some URLs as invalid
        invalid_patterns = ['/404', '/error', '/invalid', '/blocked']
        if any(pattern in url for pattern in invalid_patterns):
            return False
        
        return True
    
    async def get_page_info(self, url: str) -> Dict[str, Any]:
        """Mock page info retrieval"""
        
        return {
            "url": url,
            "title": f"Mock Page - {url}",
            "status_code": 200,
            "content_type": "text/html",
            "content_length": 1024,
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "accessible": True,
            "redirect_url": None,
            "response_time": self.base_delay
        }
    
    def supports_javascript(self) -> bool:
        """Mock JavaScript support check"""
        return True
    
    def get_supported_content_types(self) -> List[str]:
        """Mock supported content types"""
        return self._supported_content_types.copy()
    
    # Mock-specific methods for test control
    
    def set_mock_content(self, url: str, content: str) -> None:
        """Set mock content for a specific URL"""
        self.mock_content[url] = content
    
    def set_failure_rates(self, 
                         failure_rate: float = None,
                         timeout_rate: float = None,
                         block_rate: float = None) -> None:
        """Set failure rates for testing different scenarios"""
        if failure_rate is not None:
            self.failure_rate = max(0.0, min(1.0, failure_rate))
        if timeout_rate is not None:
            self.timeout_rate = max(0.0, min(1.0, timeout_rate))
        if block_rate is not None:
            self.block_rate = max(0.0, min(1.0, block_rate))


class MockWebScraperFactory:
    """Factory for creating mock scrapers with different configurations"""
    
    def create_scraper(self, scraper_type: str = "default", **kwargs) -> MockWebScraper:
        """
        Create a mock scraper instance.
        
        Args:
            scraper_type: Type of scraper ("default", "mock", "test")
            **kwargs: Additional configuration passed to scraper constructor
            
        Returns:
            MockWebScraper implementation
        """
        if scraper_type not in ["default", "mock", "test"]:
            raise ValueError(f"Unsupported scraper type: {scraper_type}")
        
        # Apply preset configurations based on type
        if scraper_type == "test":
            # Ultra-fast for testing
            kwargs.setdefault("base_delay", 0.001)
            kwargs.setdefault("failure_rate", 0.0)
        elif scraper_type == "mock":
            # Realistic simulation
            kwargs.setdefault("base_delay", 0.1)
            kwargs.setdefault("failure_rate", 0.05)
        
        return MockWebScraper(**kwargs)
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper types"""
        return ["default", "mock", "test"]
    
    def get_scraper_info(self, scraper_type: str) -> Dict[str, Any]:
        """Get information about a specific scraper type"""
        
        scraper_info = {
            "default": {
                "name": "Default Mock Scraper",
                "description": "Standard mock scraper with balanced settings",
                "features": ["javascript", "cookies", "parallel_processing"],
                "requirements": [],
                "performance": "Fast (mock)",
                "use_cases": ["Unit testing", "Development"]
            },
            "mock": {
                "name": "Realistic Mock Scraper", 
                "description": "Mock scraper with realistic delays and occasional failures",
                "features": ["javascript", "cookies", "parallel_processing", "rate_limiting"],
                "requirements": [],
                "performance": "Realistic simulation",
                "use_cases": ["Integration testing", "Performance testing"]
            },
            "test": {
                "name": "Ultra-Fast Test Scraper",
                "description": "Ultra-fast mock scraper for rapid unit testing",
                "features": ["javascript", "cookies"],
                "requirements": [],
                "performance": "Ultra-fast (0.001s)",
                "use_cases": ["Unit testing", "CI/CD pipelines"]
            }
        }
        
        if scraper_type not in scraper_info:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
        
        return scraper_info[scraper_type]


# Utility functions for testing

def create_test_config() -> ScrapingConfig:
    """Create a test scraping configuration"""
    return ScrapingConfig(
        content_types=[ContentType.TEXT, ContentType.LINKS],
        timeout=10.0,
        max_pages=5,
        parallel_requests=2
    )


def create_sample_urls() -> List[str]:
    """Create sample URLs for testing"""
    return [
        "https://example.com",
        "https://example.com/about",
        "https://example.com/contact",
        "https://example.com/services"
    ]


# Example usage for testing
async def example_usage():
    """Example of how to use the mock scraper"""
    
    # Create mock scraper with realistic settings
    scraper = MockWebScraper(base_delay=0.1, failure_rate=0.05)
    
    # Set custom content
    scraper.set_mock_content(
        "https://example.com", 
        "This is custom mock content for the homepage with detailed information about the company."
    )
    
    # Test single page scraping
    page_result = await scraper.scrape_page("https://example.com")
    print(f"Scraped: {page_result.url}")
    print(f"Content: {page_result.content[:50]}...")
    print(f"Links found: {len(page_result.links)}")
    
    # Test multiple page scraping
    urls = create_sample_urls()
    scraping_result = await scraper.scrape_pages(urls)
    print(f"Scraped {len(scraping_result.pages)} pages")
    print(f"Success rate: {scraping_result.metrics.success_rate:.2%}")


if __name__ == "__main__":
    asyncio.run(example_usage())
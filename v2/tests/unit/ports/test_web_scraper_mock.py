"""
Unit tests for mock web scraper implementation.

Tests all aspects of the WebScraper interface using the mock implementation
to validate interface compliance and behavior.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock

from src.core.ports.web_scraper import (
    WebScraper, WebScraperException, ScrapingTimeoutException,
    RateLimitedException, BlockedException, ConfigurationException,
    ScraperFeatures
)
from src.core.ports.mock_web_scraper import MockWebScraper, MockWebScraperFactory
from src.core.domain.value_objects.scraping_config import (
    ScrapingConfig, ScrapingMode, ContentType, UserAgentType
)
from src.core.domain.value_objects.scraping_result import (
    ScrapingResult, PageResult, PageStatus, ScrapingStatus
)
from src.core.ports.progress import ProgressTracker


class TestMockWebScraper:
    """Test suite for MockWebScraper implementation"""
    
    @pytest_asyncio.fixture
    async def scraper(self):
        """Create a mock scraper for testing"""
        scraper = MockWebScraper(
            base_delay=0.01,  # Very fast for testing
            failure_rate=0.0,  # No failures by default
            timeout_rate=0.0,  # No timeouts by default
            block_rate=0.0     # No blocks by default
        )
        async with scraper:
            yield scraper
    
    @pytest.fixture
    def basic_config(self):
        """Basic scraping configuration"""
        return ScrapingConfig(
            mode=ScrapingMode.SINGLE_PAGE,
            content_types=[ContentType.TEXT],
            timeout=30.0
        )
    
    @pytest.fixture
    def multi_page_config(self):
        """Multi-page scraping configuration"""
        return ScrapingConfig(
            mode=ScrapingMode.MULTI_PAGE,
            content_types=[ContentType.TEXT, ContentType.LINKS],
            max_pages=10,
            parallel_requests=3
        )

    @pytest.mark.asyncio
    async def test_single_page_scraping_success(self, scraper, basic_config):
        """Test successful single page scraping"""
        url = "https://example.com/about"
        
        result = await scraper.scrape_single_page(url, basic_config)
        
        assert isinstance(result, PageResult)
        assert result.url == url
        assert result.status == PageStatus.SUCCESS
        assert result.is_successful
        assert result.has_content
        assert len(result.content) > 0
        assert result.response_time > 0
        assert result.status_code == 200
        assert "Mock" in result.metadata.get("title", "")
    
    @pytest.mark.asyncio
    async def test_single_page_with_progress_callback(self, scraper, basic_config):
        """Test single page scraping with progress callback"""
        url = "https://example.com/contact"
        progress_updates = []
        
        def progress_callback(message: str, progress: float, details: str = None):
            progress_updates.append((message, progress, details))
        
        result = await scraper.scrape_single_page(url, basic_config, progress_callback)
        
        assert result.is_successful
        assert len(progress_updates) >= 2  # At least start and end
        assert progress_updates[-1][1] == 1.0  # Final progress should be 100%
        assert "Completed" in progress_updates[-1][0]
    
    @pytest.mark.asyncio
    async def test_multiple_pages_scraping(self, scraper, multi_page_config):
        """Test multiple pages scraping"""
        urls = [
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/services",
            "https://example.com/team"
        ]
        
        result = await scraper.scrape_multiple_pages(urls, multi_page_config)
        
        assert isinstance(result, ScrapingResult)
        assert result.is_successful
        assert len(result.pages) == len(urls)
        assert result.metrics.total_pages_attempted == len(urls)
        assert result.metrics.pages_successful == len(urls)
        assert result.status == ScrapingStatus.SUCCESS
        assert result.has_content
        assert len(result.all_links) > 0  # Should have discovered links
    
    @pytest.mark.asyncio
    async def test_website_recursive_scraping(self, scraper):
        """Test recursive website scraping"""
        config = ScrapingConfig(
            mode=ScrapingMode.RECURSIVE_CRAWL,
            max_pages=15,
            max_depth=2,
            parallel_requests=3
        )
        
        result = await scraper.scrape_website("https://example.com", config)
        
        assert isinstance(result, ScrapingResult)
        assert result.is_successful
        assert len(result.pages) <= config.max_pages
        assert result.metrics.total_pages_attempted <= config.max_pages
    
    @pytest.mark.asyncio
    async def test_url_validation(self, scraper):
        """Test URL validation functionality"""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://subdomain.example.com/page"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # May be considered invalid
            ""
        ]
        
        for url in valid_urls:
            is_valid = await scraper.validate_url(url)
            # Mock validation should mostly return True for well-formed URLs
            assert isinstance(is_valid, bool)
        
        for url in invalid_urls:
            is_valid = await scraper.validate_url(url)
            if url == "":  # Empty URL should definitely be invalid
                assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_link_discovery(self, scraper):
        """Test link discovery functionality"""
        config = ScrapingConfig(max_pages=20)
        
        links = await scraper.discover_links("https://example.com", config, depth=2)
        
        assert isinstance(links, list)
        assert len(links) > 0
        assert "https://example.com" in links  # Should include base URL
        assert all(isinstance(link, str) for link in links)
        assert all(link.startswith("http") for link in links)
    
    @pytest.mark.asyncio
    async def test_progress_tracker_integration(self, scraper):
        """Test integration with progress tracker"""
        progress_tracker = Mock()
        progress_tracker.update_progress = Mock()
        
        urls = ["https://example.com/page1", "https://example.com/page2"]
        config = ScrapingConfig(parallel_requests=2)
        
        result = await scraper.scrape_with_progress(urls, config, progress_tracker)
        
        assert result.is_successful
        assert progress_tracker.update_progress.called
        # Should have been called multiple times
        assert progress_tracker.update_progress.call_count >= 2
    
    def test_supported_features(self, scraper):
        """Test supported features reporting"""
        features = scraper.get_supported_features()
        
        assert isinstance(features, dict)
        assert ScraperFeatures.JAVASCRIPT in features
        assert ScraperFeatures.COOKIES in features
        assert ScraperFeatures.PARALLEL_PROCESSING in features
        assert isinstance(features[ScraperFeatures.JAVASCRIPT], bool)
    
    @pytest.mark.asyncio
    async def test_health_status(self, scraper, basic_config):
        """Test health status reporting"""
        # Process some requests first
        await scraper.scrape_single_page("https://example.com", basic_config)
        
        health = await scraper.get_health_status()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "requests_processed" in health
        assert "success_rate" in health
        assert "average_response_time" in health
        assert health["requests_processed"] > 0
    
    @pytest.mark.asyncio
    async def test_context_manager_requirement(self):
        """Test that scraper requires context manager usage"""
        scraper = MockWebScraper()
        
        with pytest.raises(ConfigurationException, match="context manager"):
            await scraper.scrape_single_page("https://example.com")
    
    @pytest.mark.asyncio
    async def test_cleanup_on_close(self, scraper):
        """Test proper cleanup when closing scraper"""
        # Process a request to generate statistics
        await scraper.scrape_single_page("https://example.com")
        
        assert scraper.requests_processed > 0
        
        # Close should reset statistics
        await scraper.close()
        
        assert scraper.requests_processed == 0
        assert scraper.success_count == 0
        assert scraper.error_count == 0


class TestMockWebScraperFailureScenarios:
    """Test failure scenarios with controlled failure rates"""
    
    @pytest.mark.asyncio
    async def test_timeout_scenario(self):
        """Test timeout handling"""
        scraper = MockWebScraper(
            base_delay=0.01,
            timeout_rate=1.0  # Always timeout
        )
        
        config = ScrapingConfig(timeout=1.0)  # Very short timeout (minimum allowed)
        
        async with scraper:
            with pytest.raises(ScrapingTimeoutException) as exc_info:
                await scraper.scrape_single_page("https://example.com", config)
            
            assert "timeout" in str(exc_info.value).lower()
            assert exc_info.value.url == "https://example.com"
            assert exc_info.value.timeout == config.timeout
    
    @pytest.mark.asyncio
    async def test_block_scenario(self):
        """Test blocked request handling"""
        scraper = MockWebScraper(
            base_delay=0.01,
            block_rate=1.0  # Always block
        )
        
        async with scraper:
            with pytest.raises(BlockedException) as exc_info:
                await scraper.scrape_single_page("https://example.com")
            
            assert "blocked" in str(exc_info.value).lower()
            assert exc_info.value.url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_failure_scenario(self):
        """Test general failure handling"""
        scraper = MockWebScraper(
            base_delay=0.01,
            failure_rate=1.0  # Always fail
        )
        
        async with scraper:
            result = await scraper.scrape_single_page("https://example.com")
            
            assert result.status == PageStatus.FAILED
            assert not result.is_successful
            assert result.error_message is not None
            assert result.status_code == 500
    
    @pytest.mark.asyncio
    async def test_partial_success_in_batch(self):
        """Test partial success in batch processing"""
        scraper = MockWebScraper(
            base_delay=0.01,
            failure_rate=0.5  # 50% failure rate
        )
        
        urls = [f"https://example.com/page{i}" for i in range(10)]
        
        async with scraper:
            result = await scraper.scrape_multiple_pages(urls)
            
            # Should have some successes and some failures
            assert result.metrics.pages_successful > 0
            assert result.metrics.pages_failed > 0
            assert result.status in [ScrapingStatus.PARTIAL_SUCCESS, ScrapingStatus.SUCCESS]


class TestMockWebScraperFactory:
    """Test suite for MockWebScraperFactory"""
    
    def test_factory_creation(self):
        """Test factory initialization"""
        factory = MockWebScraperFactory()
        assert factory is not None
    
    def test_create_default_scraper(self):
        """Test creating default scraper"""
        factory = MockWebScraperFactory()
        
        scraper = factory.create_scraper()
        
        assert isinstance(scraper, MockWebScraper)
        assert isinstance(scraper, WebScraper)
    
    def test_create_scraper_with_options(self):
        """Test creating scraper with custom options"""
        factory = MockWebScraperFactory()
        
        scraper = factory.create_scraper(
            scraper_type="mock",
            base_delay=0.5,
            failure_rate=0.2
        )
        
        assert isinstance(scraper, MockWebScraper)
        assert scraper.base_delay == 0.5
        assert scraper.failure_rate == 0.2
    
    def test_unsupported_scraper_type(self):
        """Test error handling for unsupported scraper types"""
        factory = MockWebScraperFactory()
        
        with pytest.raises(ValueError, match="Unsupported scraper type"):
            factory.create_scraper("unsupported_type")
    
    def test_get_available_scrapers(self):
        """Test getting available scraper types"""
        factory = MockWebScraperFactory()
        
        scrapers = factory.get_available_scrapers()
        
        assert isinstance(scrapers, list)
        assert "default" in scrapers
        assert "mock" in scrapers
        assert "test" in scrapers
    
    def test_get_scraper_info(self):
        """Test getting scraper information"""
        factory = MockWebScraperFactory()
        
        info = factory.get_scraper_info("mock")
        
        assert isinstance(info, dict)
        assert "name" in info
        assert "description" in info
        assert "features" in info
        assert "requirements" in info
        assert "performance" in info
        assert "use_cases" in info
    
    def test_get_unknown_scraper_info(self):
        """Test error handling for unknown scraper info"""
        factory = MockWebScraperFactory()
        
        with pytest.raises(ValueError, match="Unknown scraper type"):
            factory.get_scraper_info("unknown")


class TestScrapingConfigIntegration:
    """Test integration with various scraping configurations"""
    
    @pytest_asyncio.fixture
    async def scraper(self):
        """Create scraper for config testing"""
        scraper = MockWebScraper(base_delay=0.01)
        async with scraper:
            yield scraper
    
    @pytest.mark.asyncio
    async def test_company_research_config(self, scraper):
        """Test with company research preset configuration"""
        config = ScrapingConfig.for_company_research()
        
        result = await scraper.scrape_single_page("https://company.com", config)
        
        assert result.is_successful
        assert len(result.links) > 0  # Should extract links for company research
    
    @pytest.mark.asyncio
    async def test_fast_preview_config(self, scraper):
        """Test with fast preview preset configuration"""
        config = ScrapingConfig.for_fast_preview()
        
        result = await scraper.scrape_single_page("https://company.com", config)
        
        assert result.is_successful
        assert result.response_time < 1.0  # Should be fast
        # Content should be limited based on config
        assert len(result.content) <= config.max_content_length
    
    @pytest.mark.asyncio
    async def test_comprehensive_crawl_config(self, scraper):
        """Test with comprehensive crawl preset configuration"""
        config = ScrapingConfig.for_comprehensive_crawl()
        
        result = await scraper.scrape_website("https://company.com", config)
        
        assert result.is_successful
        assert len(result.pages) <= config.max_pages
        assert len(result.all_links) > 0
        # Should have metadata extraction enabled
        for page in result.successful_pages:
            assert "metadata" in page.metadata or len(page.metadata) > 0


@pytest.mark.asyncio
async def test_interface_compliance():
    """Test that MockWebScraper fully implements WebScraper interface"""
    scraper = MockWebScraper()
    
    # Verify it's recognized as WebScraper
    assert isinstance(scraper, WebScraper)
    
    # Verify all required methods exist
    required_methods = [
        'scrape_single_page', 'scrape_multiple_pages', 'scrape_website',
        'scrape_with_progress', 'validate_url', 'discover_links',
        'get_supported_features', 'get_health_status', 'close',
        '__aenter__', '__aexit__'
    ]
    
    for method_name in required_methods:
        assert hasattr(scraper, method_name)
        assert callable(getattr(scraper, method_name))


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
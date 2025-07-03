#!/usr/bin/env python3
"""
Unit Tests for Crawl4AI Scraper Adapter
=======================================

Comprehensive unit tests for the 4-phase intelligent scraping system
with mocked dependencies to ensure isolated component testing.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import List

from src.infrastructure.adapters.scrapers.crawl4ai.adapter import Crawl4AIScraper, ScrapingPhase, ScrapingProgress
from src.infrastructure.adapters.scrapers.crawl4ai.link_discovery import LinkDiscoveryService
from src.infrastructure.adapters.scrapers.crawl4ai.page_selector import LLMPageSelector
from src.infrastructure.adapters.scrapers.crawl4ai.content_extractor import ParallelContentExtractor, ExtractionResult
from src.infrastructure.adapters.scrapers.crawl4ai.aggregator import AIContentAggregator, CompanyIntelligence

from src.core.domain.value_objects.scraping_config import ScrapingConfig
from src.core.ports.web_scraper import PageResult, ScrapingResult


class MockAIProvider:
    """Mock AI provider for testing"""
    
    async def analyze_text(self, text: str, config: dict = None):
        """Mock AI analysis"""
        mock_response = Mock()
        
        # Simulate different responses based on text content
        if "select the" in text.lower() and "valuable pages" in text.lower():
            # Page selection response
            mock_response.content = '''```json
["https://example.com/about", "https://example.com/contact", "https://example.com/team"]
```'''
        elif "extract" in text.lower() and "company intelligence" in text.lower():
            # Intelligence aggregation response
            mock_response.content = '''{
  "company_name": "Example Corp",
  "description": "A leading technology company specializing in innovative solutions",
  "industry": "Technology",
  "business_model": "B2B SaaS",
  "target_market": "Enterprise clients",
  "value_proposition": "Cutting-edge technology solutions",
  "company_stage": "Growth",
  "tech_sophistication": "High-tech",
  "funding_stage": "Series B",
  "employee_count_estimate": "100-500",
  "founding_year": 2015,
  "headquarters": "San Francisco, CA",
  "key_products": ["Product A", "Product B"],
  "leadership_team": ["John Doe", "Jane Smith"],
  "recent_news": ["Recent partnership announcement"],
  "competitive_advantages": ["Advanced AI technology", "Strong team"],
  "raw_content_summary": "Comprehensive company information gathered",
  "confidence_score": 0.85
}'''
        else:
            mock_response.content = "Mock AI response"
        
        return mock_response


@pytest.fixture
def mock_ai_provider():
    """Provide mock AI provider for testing"""
    return MockAIProvider()


@pytest.fixture
def scraping_config():
    """Provide test scraping configuration"""
    return ScrapingConfig.for_company_research()


@pytest.fixture
def crawl4ai_scraper(mock_ai_provider, scraping_config):
    """Provide Crawl4AI scraper instance for testing"""
    return Crawl4AIScraper(mock_ai_provider, scraping_config)


class TestLinkDiscoveryService:
    """Test the link discovery service component"""
    
    @pytest.fixture
    def link_discovery(self):
        return LinkDiscoveryService(max_links=100)
    
    @pytest.mark.asyncio
    async def test_discover_all_links_basic(self, link_discovery):
        """Test basic link discovery functionality"""
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock robots.txt response
            mock_robots_response = Mock()
            mock_robots_response.status = 200
            mock_robots_response.text = AsyncMock(return_value="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml")
            
            # Mock sitemap response
            mock_sitemap_response = Mock()
            mock_sitemap_response.status = 200
            mock_sitemap_response.text = AsyncMock(return_value='''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/about</loc></url>
    <url><loc>https://example.com/contact</loc></url>
</urlset>''')
            
            # Mock HTML page response
            mock_html_response = Mock()
            mock_html_response.status = 200
            mock_html_response.headers = {'content-type': 'text/html'}
            mock_html_response.text = AsyncMock(return_value='<html><a href="/team">Team</a><a href="/careers">Careers</a></html>')
            
            # Configure mock session
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.get.return_value.__aenter__.side_effect = [
                mock_robots_response,  # robots.txt
                mock_sitemap_response,  # sitemap.xml
                mock_html_response     # base page crawl
            ]
            
            # Execute discovery
            discovered_links = await link_discovery.discover_all_links("https://example.com")
            
            # Verify results
            assert len(discovered_links) > 0
            assert "https://example.com/about" in discovered_links
            assert "https://example.com/contact" in discovered_links
    
    @pytest.mark.asyncio 
    async def test_discover_links_with_error_handling(self, link_discovery):
        """Test error handling during link discovery"""
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock network error
            mock_session.return_value.__aenter__.side_effect = Exception("Network error")
            
            # Execute discovery (should not raise exception)
            discovered_links = await link_discovery.discover_all_links("https://example.com")
            
            # Should return at least the base URL as fallback
            assert len(discovered_links) >= 1
            assert "https://example.com" in discovered_links
    
    def test_url_scoring(self, link_discovery):
        """Test URL scoring algorithm"""
        
        # High-value URLs should score higher
        contact_score = link_discovery._calculate_url_score("https://example.com/contact")
        about_score = link_discovery._calculate_url_score("https://example.com/about")
        blog_score = link_discovery._calculate_url_score("https://example.com/blog/post/123")
        
        assert contact_score > blog_score
        assert about_score > blog_score
        assert contact_score >= 8.0  # Contact pages should have high score


class TestLLMPageSelector:
    """Test the LLM page selector component"""
    
    @pytest.fixture
    def page_selector(self, mock_ai_provider):
        return LLMPageSelector(mock_ai_provider)
    
    @pytest.mark.asyncio
    async def test_select_valuable_pages_ai_success(self, page_selector):
        """Test successful AI-driven page selection"""
        
        input_urls = [
            "https://example.com/about",
            "https://example.com/contact", 
            "https://example.com/team",
            "https://example.com/blog/post1",
            "https://example.com/blog/post2"
        ]
        
        selected_urls = await page_selector.select_valuable_pages(input_urls, max_pages=3)
        
        # AI should select the high-value pages
        assert len(selected_urls) <= 3
        assert "https://example.com/about" in selected_urls
        assert "https://example.com/contact" in selected_urls
        assert "https://example.com/team" in selected_urls
    
    @pytest.mark.asyncio
    async def test_select_valuable_pages_ai_fallback(self, page_selector):
        """Test fallback to heuristics when AI fails"""
        
        # Mock AI provider to raise exception
        page_selector.ai_provider.analyze_text = AsyncMock(side_effect=Exception("AI service down"))
        
        input_urls = [
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/blog/post1"
        ]
        
        selected_urls = await page_selector.select_valuable_pages(input_urls, max_pages=2)
        
        # Should fallback to heuristic selection
        assert len(selected_urls) <= 2
        # High-value pages should still be prioritized
        assert "https://example.com/about" in selected_urls or "https://example.com/contact" in selected_urls
    
    def test_heuristic_selection(self, page_selector):
        """Test heuristic page selection algorithm"""
        
        input_urls = [
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/blog/post1",
            "https://example.com/wp-admin/login"
        ]
        
        selected_urls = page_selector._heuristic_selection(input_urls, max_pages=2)
        
        # Should prioritize valuable pages and exclude noise
        assert len(selected_urls) <= 2
        assert "https://example.com/about" in selected_urls
        assert "https://example.com/contact" in selected_urls
        assert "https://example.com/wp-admin/login" not in selected_urls


class TestParallelContentExtractor:
    """Test the parallel content extractor component"""
    
    @pytest.fixture
    def content_extractor(self):
        return ParallelContentExtractor(max_workers=3)
    
    @pytest.mark.asyncio
    async def test_extract_content_parallel_success(self, content_extractor):
        """Test successful parallel content extraction"""
        
        # Mock Crawl4AI
        with patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            
            # Mock successful extraction result
            mock_result = Mock()
            mock_result.success = True
            mock_result.markdown = "# Company About Page\nWe are a leading technology company..."
            mock_result.cleaned_html = "<h1>Company About Page</h1><p>We are a leading technology company...</p>"
            mock_result.status_code = 200
            
            mock_crawler.arun = AsyncMock(return_value=mock_result)
            mock_crawler.start = AsyncMock()
            mock_crawler.close = AsyncMock()
            
            # Test URLs
            test_urls = [
                "https://example.com/about",
                "https://example.com/contact"
            ]
            
            # Execute extraction
            results = await content_extractor.extract_content_parallel(test_urls)
            
            # Verify results
            assert len(results) == 2
            assert all(result.success for result in results)
            assert all(len(result.content) > 0 for result in results)
            assert all(result.url in test_urls for result in results)
    
    @pytest.mark.asyncio
    async def test_extract_content_with_failures(self, content_extractor):
        """Test extraction with some page failures"""
        
        with patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            
            # Mock mixed results (success and failure)
            def mock_arun(url, **kwargs):
                if "about" in url:
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.markdown = "About page content"
                    return mock_result
                else:
                    mock_result = Mock()
                    mock_result.success = False
                    mock_result.error_message = "Page not found"
                    return mock_result
            
            mock_crawler.arun = AsyncMock(side_effect=mock_arun)
            mock_crawler.start = AsyncMock()
            mock_crawler.close = AsyncMock()
            
            test_urls = [
                "https://example.com/about",
                "https://example.com/nonexistent"
            ]
            
            results = await content_extractor.extract_content_parallel(test_urls)
            
            # Verify mixed results
            assert len(results) == 2
            success_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            assert len(success_results) == 1
            assert len(failed_results) == 1
            assert success_results[0].url == "https://example.com/about"
            assert failed_results[0].url == "https://example.com/nonexistent"


class TestAIContentAggregator:
    """Test the AI content aggregator component"""
    
    @pytest.fixture
    def aggregator(self, mock_ai_provider):
        return AIContentAggregator(mock_ai_provider)
    
    @pytest.mark.asyncio
    async def test_aggregate_company_intelligence_success(self, aggregator):
        """Test successful company intelligence aggregation"""
        
        # Create mock extraction results
        extraction_results = [
            ExtractionResult(
                url="https://example.com/about",
                success=True,
                content="Example Corp is a leading technology company founded in 2015...",
                title="About Us"
            ),
            ExtractionResult(
                url="https://example.com/contact",
                success=True,
                content="Contact us at our San Francisco headquarters...",
                title="Contact"
            )
        ]
        
        # Execute aggregation
        intelligence = await aggregator.aggregate_company_intelligence(
            "Example Corp", 
            extraction_results
        )
        
        # Verify structured intelligence
        assert intelligence.company_name == "Example Corp"
        assert intelligence.industry == "Technology"
        assert intelligence.business_model == "B2B SaaS"
        assert intelligence.founding_year == 2015
        assert intelligence.headquarters == "San Francisco, CA"
        assert intelligence.confidence_score == 0.85
        assert len(intelligence.key_products) > 0
        assert len(intelligence.leadership_team) > 0
    
    @pytest.mark.asyncio
    async def test_aggregate_with_no_content(self, aggregator):
        """Test aggregation when no content is available"""
        
        # Empty extraction results
        extraction_results = []
        
        intelligence = await aggregator.aggregate_company_intelligence(
            "Example Corp",
            extraction_results
        )
        
        # Should return basic structure with low confidence
        assert intelligence.company_name == "Example Corp"
        assert intelligence.confidence_score == 0.0
        assert "no_content" in intelligence.extraction_metadata.get("error", "")
    
    @pytest.mark.asyncio
    async def test_aggregate_with_ai_failure(self, aggregator):
        """Test fallback when AI analysis fails"""
        
        # Mock AI provider to raise exception
        aggregator.ai_provider.analyze_text = AsyncMock(side_effect=Exception("AI service unavailable"))
        
        extraction_results = [
            ExtractionResult(
                url="https://example.com/about",
                success=True,
                content="Some company content...",
                title="About"
            )
        ]
        
        intelligence = await aggregator.aggregate_company_intelligence(
            "Example Corp",
            extraction_results
        )
        
        # Should return fallback intelligence
        assert intelligence.company_name == "Example Corp"
        assert intelligence.confidence_score == 0.3  # Low confidence for fallback
        assert "fallback_summary" in intelligence.extraction_metadata.get("analysis_method", "")


class TestCrawl4AIScraper:
    """Test the main Crawl4AI scraper adapter"""
    
    @pytest.mark.asyncio
    async def test_scrape_single_page(self, crawl4ai_scraper):
        """Test single page scraping"""
        
        with patch.object(crawl4ai_scraper.content_extractor, 'extract_content_parallel') as mock_extract:
            # Mock successful extraction
            mock_extract.return_value = [
                ExtractionResult(
                    url="https://example.com/about",
                    success=True,
                    content="Company about page content",
                    title="About Us",
                    metadata={"status_code": 200},
                    extraction_time=1.5
                )
            ]
            
            result = await crawl4ai_scraper.scrape_single_page("https://example.com/about")
            
            assert isinstance(result, PageResult)
            assert result.success is True
            assert result.url == "https://example.com/about"
            assert result.title == "About Us"
            assert len(result.content) > 0
            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_scrape_multiple_pages(self, crawl4ai_scraper):
        """Test multiple page scraping"""
        
        with patch.object(crawl4ai_scraper.content_extractor, 'extract_content_parallel') as mock_extract:
            # Mock extraction results
            mock_extract.return_value = [
                ExtractionResult(
                    url="https://example.com/about",
                    success=True,
                    content="About content",
                    title="About"
                ),
                ExtractionResult(
                    url="https://example.com/contact",
                    success=True,
                    content="Contact content", 
                    title="Contact"
                )
            ]
            
            test_urls = ["https://example.com/about", "https://example.com/contact"]
            result = await crawl4ai_scraper.scrape_multiple_pages(test_urls)
            
            assert isinstance(result, ScrapingResult)
            assert result.total_pages == 2
            assert result.successful_pages == 2
            assert len(result.pages) == 2
            assert all(page.success for page in result.pages)
    
    @pytest.mark.asyncio
    async def test_scrape_website_full_4_phase(self, crawl4ai_scraper):
        """Test complete 4-phase website scraping"""
        
        # Mock all 4 phases
        with patch.object(crawl4ai_scraper.link_discovery, 'discover_all_links') as mock_discovery, \
             patch.object(crawl4ai_scraper.page_selector, 'select_valuable_pages') as mock_selector, \
             patch.object(crawl4ai_scraper.content_extractor, 'extract_content_parallel') as mock_extractor, \
             patch.object(crawl4ai_scraper.aggregator, 'aggregate_company_intelligence') as mock_aggregator:
            
            # Phase 1: Link discovery
            mock_discovery.return_value = [
                "https://example.com/about",
                "https://example.com/contact", 
                "https://example.com/team",
                "https://example.com/blog/post1"
            ]
            
            # Phase 2: Page selection
            mock_selector.return_value = [
                "https://example.com/about",
                "https://example.com/contact",
                "https://example.com/team"
            ]
            
            # Phase 3: Content extraction
            mock_extractor.return_value = [
                ExtractionResult(
                    url="https://example.com/about",
                    success=True,
                    content="About page content",
                    title="About"
                ),
                ExtractionResult(
                    url="https://example.com/contact",
                    success=True,
                    content="Contact page content",
                    title="Contact"
                )
            ]
            
            # Phase 4: Intelligence aggregation
            mock_aggregator.return_value = CompanyIntelligence(
                company_name="Example Corp",
                description="A technology company",
                industry="Technology",
                confidence_score=0.85
            )
            
            # Execute full 4-phase scraping
            result = await crawl4ai_scraper.scrape_website("https://example.com")
            
            # Verify all phases were called
            mock_discovery.assert_called_once()
            mock_selector.assert_called_once()
            mock_extractor.assert_called_once()
            mock_aggregator.assert_called_once()
            
            # Verify result structure
            assert isinstance(result, ScrapingResult)
            assert result.total_links == 4  # From discovery
            assert result.total_pages == 2  # From extraction
            assert "4_phase_intelligent" in result.metadata["scraping_method"]
            assert "company_intelligence" in result.metadata
            assert result.metadata["phase_performance"]["intelligence_confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_validate_url(self, crawl4ai_scraper):
        """Test URL validation"""
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock successful head request
            mock_response = Mock()
            mock_response.status = 200
            
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance
            mock_session_instance.head.return_value.__aenter__.return_value = mock_response
            
            is_valid = await crawl4ai_scraper.validate_url("https://example.com")
            assert is_valid is True
    
    async def test_get_health_status(self, crawl4ai_scraper):
        """Test health status reporting"""
        
        health = await crawl4ai_scraper.get_health_status()
        
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "requests_processed" in health
        assert "success_rate" in health
        assert "ai_provider_available" in health
        assert "components_status" in health
        
        # All components should be operational initially
        components = health["components_status"]
        assert components["link_discovery"] == "operational"
        assert components["page_selector"] == "operational"
        assert components["content_extractor"] == "operational"
        assert components["ai_aggregator"] == "operational"
    
    def test_get_supported_features(self, crawl4ai_scraper):
        """Test supported features reporting"""
        
        features = crawl4ai_scraper.get_supported_features()
        
        # Verify key features are supported
        assert features["javascript"] is True
        assert features["parallel_processing"] is True
        assert features["ai_selection"] is True
        assert features["business_intelligence"] is True
        assert features["multi_phase_extraction"] is True
        assert features["streaming"] is True
    
    @pytest.mark.asyncio
    async def test_context_manager(self, crawl4ai_scraper):
        """Test async context manager functionality"""
        
        with patch.object(crawl4ai_scraper, 'close') as mock_close:
            async with crawl4ai_scraper as scraper:
                assert scraper is not None
            
            # Ensure cleanup was called
            mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
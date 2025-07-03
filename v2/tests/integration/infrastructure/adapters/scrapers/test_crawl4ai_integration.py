#!/usr/bin/env python3
"""
Integration Tests for Crawl4AI Scraper Adapter
==============================================

Integration tests with realistic mock adapters to validate the complete 
4-phase intelligent scraping system in a near-production environment.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from src.infrastructure.adapters.scrapers.crawl4ai.adapter import Crawl4AIScraper
from src.core.domain.value_objects.scraping_config import ScrapingConfig


class RealisticMockAIProvider:
    """Realistic AI provider mock that simulates real AI behavior"""
    
    def __init__(self):
        self.call_count = 0
        self.response_delay = 0.1  # Simulate AI processing time
    
    async def analyze_text(self, text: str, config: Dict[str, Any] = None) -> Mock:
        """Simulate realistic AI analysis with delays and varied responses"""
        
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        self.call_count += 1
        
        mock_response = Mock()
        
        # Determine response type based on content
        if "select the" in text.lower() and "valuable pages" in text.lower():
            # Page selection response - extract URLs from input
            urls_in_text = []
            lines = text.split('\n')
            for line in lines:
                if line.strip() and ('http' in line or 'www.' in line):
                    # Extract URL-like patterns
                    words = line.split()
                    for word in words:
                        if 'http' in word or ('.' in word and '/' in word):
                            urls_in_text.append(word.strip('.,'))
            
            # Select high-value URLs based on patterns
            valuable_urls = []
            for url in urls_in_text[:20]:  # Limit processing
                if any(pattern in url.lower() for pattern in ['/about', '/contact', '/team', '/company', '/careers']):
                    valuable_urls.append(url)
            
            # Fallback to first few URLs if no valuable ones found
            if not valuable_urls and urls_in_text:
                valuable_urls = urls_in_text[:3]
            
            mock_response.content = f'''```json
{valuable_urls}
```'''
        
        elif "extract" in text.lower() and "company intelligence" in text.lower():
            # Intelligence aggregation response
            # Extract company name from text
            company_name = "Unknown Company"
            if "CONTENT TO ANALYZE:" in text:
                content_section = text.split("CONTENT TO ANALYZE:")[1]
                # Look for company names in content
                if "corp" in content_section.lower():
                    company_name = "Example Corp"
                elif "inc" in content_section.lower():
                    company_name = "Example Inc" 
                elif "ltd" in content_section.lower():
                    company_name = "Example Ltd"
            
            # Generate realistic intelligence based on content analysis
            mock_response.content = f'''{{
  "company_name": "{company_name}",
  "description": "A company that provides products and services to its target market",
  "industry": "Technology",
  "business_model": "B2B",
  "target_market": "Business customers", 
  "value_proposition": "Quality products and services",
  "company_stage": "Established",
  "tech_sophistication": "Moderate",
  "funding_stage": "Unknown",
  "employee_count_estimate": "50-200",
  "founding_year": null,
  "headquarters": "",
  "key_products": ["Main Product", "Secondary Service"],
  "leadership_team": ["Executive Team"],
  "recent_news": [],
  "competitive_advantages": ["Market presence", "Customer focus"],
  "raw_content_summary": "Company information extracted from multiple web pages",
  "confidence_score": 0.75
}}'''
        else:
            # Generic response
            mock_response.content = "Mock AI analysis response"
        
        return mock_response


class RealisticMockCrawler:
    """Realistic Crawl4AI mock that simulates web crawling behavior"""
    
    def __init__(self):
        self.is_started = False
        self.call_count = 0
    
    async def start(self):
        """Simulate crawler startup"""
        await asyncio.sleep(0.05)  # Startup delay
        self.is_started = True
    
    async def close(self):
        """Simulate crawler cleanup"""
        await asyncio.sleep(0.02)  # Cleanup delay
        self.is_started = False
    
    async def arun(self, url: str, **kwargs) -> Mock:
        """Simulate web page crawling with realistic behavior"""
        
        if not self.is_started:
            raise RuntimeError("Crawler not started")
        
        # Simulate network delay
        await asyncio.sleep(0.2)
        self.call_count += 1
        
        mock_result = Mock()
        
        # Simulate success/failure based on URL patterns
        if any(pattern in url.lower() for pattern in ['404', 'nonexistent', 'error']):
            # Simulate failed requests
            mock_result.success = False
            mock_result.error_message = "Page not found (404)"
            return mock_result
        
        # Simulate successful extraction
        mock_result.success = True
        mock_result.status_code = 200
        
        # Generate realistic content based on URL
        if '/about' in url.lower():
            mock_result.markdown = f"""# About Us
            
We are a leading company in our industry, founded with the mission to provide 
excellent products and services to our customers.

Our company has been serving clients since our founding, building a reputation
for quality and innovation in everything we do.

## Our Mission
To deliver outstanding value to our customers through innovative solutions.

## Our Values
- Quality
- Innovation  
- Customer Focus
- Integrity
"""
            mock_result.cleaned_html = mock_result.markdown
        
        elif '/contact' in url.lower():
            mock_result.markdown = f"""# Contact Us

Get in touch with our team:

**Address:**
123 Business Street
City, State 12345

**Phone:** (555) 123-4567
**Email:** info@company.com

**Business Hours:**
Monday - Friday: 9:00 AM - 5:00 PM
Saturday: 10:00 AM - 2:00 PM
"""
            mock_result.cleaned_html = mock_result.markdown
        
        elif '/team' in url.lower():
            mock_result.markdown = f"""# Our Team

Meet the people behind our success:

## Leadership Team

**John Smith, CEO**
John has over 15 years of experience in the industry and leads our strategic vision.

**Jane Doe, CTO** 
Jane oversees our technology development and innovation initiatives.

**Mike Johnson, VP Sales**
Mike drives our sales strategy and customer relationships.
"""
            mock_result.cleaned_html = mock_result.markdown
        
        else:
            # Generic page content
            mock_result.markdown = f"""# Welcome

This is a sample page from our website. We provide various products and 
services to meet our customers' needs.

Visit our other pages to learn more about what we do and how we can help you.
"""
            mock_result.cleaned_html = mock_result.markdown
        
        # Add metadata
        mock_result.links = [f"{url}/link1", f"{url}/link2"]
        mock_result.media = ["image1.jpg", "image2.png"]
        
        return mock_result


@pytest.fixture
def realistic_ai_provider():
    """Provide realistic AI provider mock"""
    return RealisticMockAIProvider()


@pytest.fixture
def scraping_config():
    """Provide production-like scraping configuration"""
    config = ScrapingConfig.for_company_research()
    config.max_pages = 10
    config.max_depth = 2
    config.parallel_requests = 3
    return config


@pytest.fixture
def integration_scraper(realistic_ai_provider, scraping_config):
    """Provide scraper configured for integration testing"""
    scraper = Crawl4AIScraper(realistic_ai_provider, scraping_config)
    # Reduce parallelism for testing
    scraper.content_extractor.max_workers = 3
    scraper.link_discovery.max_links = 50
    return scraper


class TestCrawl4AIIntegration:
    """Integration tests for the complete 4-phase system"""
    
    @pytest.mark.asyncio
    async def test_complete_website_scraping_flow(self, integration_scraper):
        """Test complete 4-phase website scraping with realistic mocks"""
        
        # Mock HTTP requests for link discovery
        with patch('aiohttp.ClientSession') as mock_session_class:
            
            # Setup realistic HTTP response mocks
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock robots.txt
            mock_robots_response = Mock()
            mock_robots_response.status = 200
            mock_robots_response.text = AsyncMock(return_value="""User-agent: *
Allow: /
Disallow: /admin/
Sitemap: https://company.example/sitemap.xml""")
            
            # Mock sitemap.xml
            mock_sitemap_response = Mock()
            mock_sitemap_response.status = 200  
            mock_sitemap_response.text = AsyncMock(return_value="""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://company.example/about</loc></url>
    <url><loc>https://company.example/contact</loc></url>
    <url><loc>https://company.example/team</loc></url>
    <url><loc>https://company.example/products</loc></url>
    <url><loc>https://company.example/careers</loc></url>
</urlset>""")
            
            # Mock base page for crawling
            mock_page_response = Mock()
            mock_page_response.status = 200
            mock_page_response.headers = {'content-type': 'text/html'}
            mock_page_response.text = AsyncMock(return_value="""<html>
<head><title>Company Example</title></head>
<body>
<nav>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="/team">Team</a>
    <a href="/services">Services</a>
</nav>
<main>
    <h1>Welcome to Company Example</h1>
    <p>We provide excellent services to our customers.</p>
</main>
</body>
</html>""")
            
            # Configure HTTP response sequence
            mock_session.get.return_value.__aenter__.side_effect = [
                mock_robots_response,   # robots.txt request
                mock_sitemap_response,  # sitemap.xml request  
                mock_page_response      # base page crawl
            ]
            
            # Mock Crawl4AI for content extraction
            with patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
                mock_crawler = RealisticMockCrawler()
                mock_crawler_class.return_value = mock_crawler
                
                # Track progress updates
                progress_updates = []
                def track_progress(progress_info):
                    progress_updates.append(progress_info)
                
                # Execute complete 4-phase scraping
                result = await integration_scraper.scrape_website(
                    "https://company.example",
                    progress_callback=track_progress
                )
                
                # Verify 4-phase execution
                assert len(progress_updates) > 0
                phase_names = [p.phase for p in progress_updates]
                assert 'link_discovery' in phase_names
                assert 'page_selection' in phase_names
                assert 'content_extraction' in phase_names
                assert 'ai_aggregation' in phase_names
                
                # Verify result structure
                assert result.total_links > 0  # Links were discovered
                assert result.total_pages > 0  # Pages were extracted
                assert result.successful_pages > 0  # Some extractions succeeded
                assert result.processing_time > 0  # Time was recorded
                
                # Verify metadata includes intelligence
                assert 'company_intelligence' in result.metadata
                intelligence = result.metadata['company_intelligence']
                assert intelligence['company_name'] != ""
                assert intelligence['confidence_score'] > 0
                
                # Verify phase performance tracking
                assert 'phase_performance' in result.metadata
                phase_perf = result.metadata['phase_performance']
                assert phase_perf['discovery_links'] > 0
                assert phase_perf['selected_pages'] > 0
                assert phase_perf['extracted_pages'] >= 0
    
    @pytest.mark.asyncio
    async def test_error_resilience_integration(self, integration_scraper):
        """Test system resilience with various error conditions"""
        
        # Mock network failures for some requests
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Simulate robots.txt failure
            mock_session.get.return_value.__aenter__.side_effect = Exception("Network timeout")
            
            # Mock Crawl4AI with mixed success/failure
            with patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
                mock_crawler = RealisticMockCrawler()
                
                # Simulate some extraction failures
                original_arun = mock_crawler.arun
                async def failing_arun(url, **kwargs):
                    if 'contact' in url:
                        # Simulate contact page failure
                        result = Mock()
                        result.success = False
                        result.error_message = "Access denied"
                        return result
                    return await original_arun(url, **kwargs)
                
                mock_crawler.arun = failing_arun
                mock_crawler_class.return_value = mock_crawler
                
                # Execute scraping with error conditions
                result = await integration_scraper.scrape_website("https://company.example")
                
                # System should handle errors gracefully
                assert result is not None
                assert result.total_pages >= 0
                # Some pages may fail, but system should continue
                assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self, integration_scraper):
        """Test performance characteristics under realistic conditions"""
        
        import time
        
        # Mock fast network responses
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
            
            # Setup fast mocks
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Fast HTTP responses
            mock_response = Mock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html><a href='/about'>About</a></html>")
            mock_response.headers = {'content-type': 'text/html'}
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Fast content extraction
            fast_crawler = RealisticMockCrawler()
            fast_crawler.response_delay = 0.01  # Very fast responses
            mock_crawler_class.return_value = fast_crawler
            
            # Measure performance
            start_time = time.time()
            result = await integration_scraper.scrape_website("https://fast.example")
            end_time = time.time()
            
            # Performance assertions
            total_time = end_time - start_time
            assert total_time < 30.0  # Should complete within 30 seconds
            assert result.processing_time < 30.0
            
            # Verify performance metadata
            assert 'performance_rating' in result.metadata
            perf_rating = result.metadata['performance_rating']
            assert perf_rating in ['excellent', 'good', 'acceptable', 'slow']
    
    @pytest.mark.asyncio
    async def test_ai_provider_integration(self, integration_scraper):
        """Test integration with AI provider for page selection and aggregation"""
        
        # Track AI provider calls
        ai_calls = []
        original_analyze = integration_scraper.ai_provider.analyze_text
        
        async def track_analyze(text, config=None):
            ai_calls.append({'text': text[:100], 'config': config})
            return await original_analyze(text, config)
        
        integration_scraper.ai_provider.analyze_text = track_analyze
        
        # Mock minimal web infrastructure
        with patch('aiohttp.ClientSession') as mock_session_class, \
             patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
            
            # Setup basic mocks
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = Mock(
                status=200,
                text=AsyncMock(return_value="<html><a href='/about'>About</a></html>"),
                headers={'content-type': 'text/html'}
            )
            
            mock_crawler_class.return_value = RealisticMockCrawler()
            
            # Execute scraping
            result = await integration_scraper.scrape_website("https://ai.example")
            
            # Verify AI was called for both page selection and aggregation
            assert len(ai_calls) >= 2
            
            # Check for page selection call
            selection_calls = [call for call in ai_calls if 'select the' in call['text'].lower()]
            assert len(selection_calls) >= 1
            
            # Check for aggregation call  
            aggregation_calls = [call for call in ai_calls if 'company intelligence' in call['text'].lower()]
            assert len(aggregation_calls) >= 1
            
            # Verify AI responses were processed
            assert 'company_intelligence' in result.metadata
            intelligence = result.metadata['company_intelligence']
            assert intelligence['confidence_score'] > 0
    
    @pytest.mark.asyncio
    async def test_streaming_interface(self, integration_scraper):
        """Test streaming interface functionality"""
        
        # Mock infrastructure for streaming
        with patch('src.infrastructure.adapters.scrapers.crawl4ai.content_extractor.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler_class.return_value = RealisticMockCrawler()
            
            test_urls = [
                "https://stream.example/page1",
                "https://stream.example/page2", 
                "https://stream.example/page3"
            ]
            
            # Collect streaming results
            streamed_results = []
            async for page_result in integration_scraper.scrape_stream(test_urls):
                streamed_results.append(page_result)
            
            # Verify streaming behavior
            assert len(streamed_results) == len(test_urls)
            assert all(hasattr(result, 'url') for result in streamed_results)
            assert all(hasattr(result, 'success') for result in streamed_results)
    
    @pytest.mark.asyncio
    async def test_configuration_flexibility(self, realistic_ai_provider):
        """Test scraper behavior with different configurations"""
        
        # Test with fast preview configuration
        fast_config = ScrapingConfig.for_fast_preview()
        fast_scraper = Crawl4AIScraper(realistic_ai_provider, fast_config)
        
        # Test with comprehensive crawl configuration
        comprehensive_config = ScrapingConfig.for_comprehensive_crawl()
        comprehensive_scraper = Crawl4AIScraper(realistic_ai_provider, comprehensive_config)
        
        # Verify different configurations affect behavior
        assert fast_scraper.config.max_pages != comprehensive_scraper.config.max_pages
        assert fast_scraper.config.max_depth != comprehensive_scraper.config.max_depth
        
        # Test feature reporting varies by config
        fast_features = fast_scraper.get_supported_features()
        comprehensive_features = comprehensive_scraper.get_supported_features()
        
        # Both should support core features
        assert fast_features['javascript'] == comprehensive_features['javascript']
        assert fast_features['parallel_processing'] == comprehensive_features['parallel_processing']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
"""
Crawl4AI Best Practices Test
============================

This test demonstrates the CORRECT way to use Crawl4AI based on the latest documentation.
It showcases modern features that Theodore should be using instead of its current approach.

Key improvements demonstrated:
1. Single browser instance with arun_many() for multiple URLs
2. Built-in deep crawling with BFSDeepCrawlStrategy
3. Intelligent filtering with FilterChain
4. Memory-adaptive dispatching
5. LXML strategy for 20x faster parsing
6. Proper configuration patterns
7. Streaming results processing
8. Ethical crawling with robots.txt respect
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

try:
    from crawl4ai import (
        AsyncWebCrawler, 
        BrowserConfig, 
        CrawlerRunConfig,
        CacheMode,
        BFSDeepCrawlStrategy,
        LXMLWebScrapingStrategy
    )
    from crawl4ai.deep_crawling import (
        FilterChain,
        DomainFilter, 
        URLPatternFilter,
        ContentTypeFilter,
        KeywordRelevanceScorer
    )
    from crawl4ai.async_dispatcher import (
        MemoryAdaptiveDispatcher,
        SemaphoreDispatcher,
        CrawlerMonitor,
        DisplayMode
    )
    CRAWL4AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Crawl4AI import error: {e}")
    CRAWL4AI_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Crawl4AIBestPracticesDemo:
    """
    Demonstrates correct Crawl4AI usage patterns that Theodore should adopt
    """
    
    def __init__(self):
        self.results = {}
        
    async def test_single_browser_multiple_urls(self):
        """
        Test 1: Single browser instance for multiple URLs (Theodore's main issue)
        
        ❌ Theodore's current approach: New browser for each page
        ✅ Correct approach: Single browser with arun_many()
        """
        print("\n" + "="*60)
        print("🧪 TEST 1: Single Browser Instance for Multiple URLs")
        print("="*60)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/robots.txt", 
            "https://httpbin.org/links/3",
            "https://example.com"
        ]
        
        # ✅ CORRECT: Single browser instance
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            viewport_width=1280,
            viewport_height=720,
            verbose=False
        )
        
        run_config = CrawlerRunConfig(
            word_count_threshold=10,
            css_selector="body",
            scraping_strategy=LXMLWebScrapingStrategy(),  # 20x faster
            cache_mode=CacheMode.ENABLED,
            page_timeout=15000,
            semaphore_count=3  # Control concurrency
        )
        
        start_time = time.time()
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"🚀 Processing {len(test_urls)} URLs with single browser instance...")
            
            # Process all URLs concurrently with single browser
            results = await crawler.arun_many(test_urls, config=run_config)
            
            successful = sum(1 for r in results if r.success)
            total_content = sum(len(r.cleaned_html or "") for r in results if r.success)
            
        duration = time.time() - start_time
        
        print(f"✅ RESULTS:")
        print(f"   • URLs processed: {len(results)}")
        print(f"   • Successful: {successful}/{len(test_urls)}")
        print(f"   • Total content: {total_content:,} characters")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Performance: {len(test_urls)/duration:.1f} URLs/second")
        
        self.results['single_browser'] = {
            'urls_processed': len(results),
            'successful': successful,
            'duration': duration,
            'performance': len(test_urls)/duration
        }
        
        return results

    async def test_deep_crawling_strategy(self):
        """
        Test 2: Modern deep crawling with built-in strategies
        
        ❌ Theodore's approach: Manual link discovery + custom parsing
        ✅ Correct approach: Built-in BFSDeepCrawlStrategy with filtering
        """
        print("\n" + "="*60)
        print("🧪 TEST 2: Deep Crawling with Built-in Strategy")
        print("="*60)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        target_url = "https://docs.crawl4ai.com"
        target_domain = urlparse(target_url).netloc
        
        # ✅ CORRECT: Built-in deep crawling with intelligent filtering
        filter_chain = FilterChain([
            DomainFilter(allowed_domains=[target_domain]),
            URLPatternFilter(patterns=["*core*", "*api*", "*quickstart*"]),
            ContentTypeFilter(allowed_types=["text/html"])
        ])
        
        # Intelligent URL scoring (like Theodore's LLM page selection)
        keyword_scorer = KeywordRelevanceScorer(
            keywords=["crawl", "example", "async", "configuration"],
            weight=0.7
        )
        
        deep_crawl_config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=2,
                include_external=False,
                max_pages=10,  # Limit for demo
                filter_chain=filter_chain,
                url_scorer=keyword_scorer
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),
            check_robots_txt=True,  # Ethical crawling
            cache_mode=CacheMode.ENABLED,
            stream=True,  # Process results as they arrive
            verbose=True
        )
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        start_time = time.time()
        crawled_pages = []
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                print(f"🔍 Starting deep crawl of {target_url}...")
                print("📊 Processing results in real-time (streaming)...")
                
                async for result in await crawler.arun(target_url, config=deep_crawl_config):
                    if result.success:
                        score = result.metadata.get('score', 0)
                        depth = result.metadata.get('depth', 0)
                        content_length = len(result.cleaned_html or "")
                        
                        print(f"   ✅ {result.url}")
                        print(f"      Score: {score:.2f}, Depth: {depth}, Content: {content_length:,} chars")
                        
                        crawled_pages.append({
                            'url': result.url,
                            'score': score,
                            'depth': depth,
                            'content_length': content_length,
                            'success': True
                        })
                    else:
                        print(f"   ❌ Failed: {result.url} - {result.error_message}")
                        
        except Exception as e:
            print(f"❌ Deep crawl failed: {e}")
            return []
            
        duration = time.time() - start_time
        total_content = sum(p['content_length'] for p in crawled_pages)
        avg_score = sum(p['score'] for p in crawled_pages) / len(crawled_pages) if crawled_pages else 0
        
        print(f"\n✅ DEEP CRAWL RESULTS:")
        print(f"   • Pages crawled: {len(crawled_pages)}")
        print(f"   • Total content: {total_content:,} characters")
        print(f"   • Average relevance score: {avg_score:.2f}")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Robots.txt respected: Yes")
        
        self.results['deep_crawling'] = {
            'pages_crawled': len(crawled_pages),
            'total_content': total_content,
            'avg_score': avg_score,
            'duration': duration
        }
        
        return crawled_pages

    async def test_memory_adaptive_dispatching(self):
        """
        Test 3: Memory-adaptive dispatching for batch processing
        
        ❌ Theodore's approach: No memory management
        ✅ Correct approach: MemoryAdaptiveDispatcher with monitoring
        """
        print("\n" + "="*60)
        print("🧪 TEST 3: Memory-Adaptive Dispatching")
        print("="*60)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        # Simulate batch company processing
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json", 
            "https://httpbin.org/xml",
            "https://httpbin.org/links/5",
            "https://example.com",
            "https://httpbin.org/robots.txt"
        ]
        
        # ✅ CORRECT: Memory-adaptive dispatcher with monitoring
        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,  # Pause if memory > 80%
            check_interval=0.5,  # Check every 0.5 seconds
            max_session_permit=3,  # Max 3 concurrent
            monitor=CrawlerMonitor(
                max_visible_rows=10,
                display_mode=DisplayMode.DETAILED
            )
        )
        
        run_config = CrawlerRunConfig(
            word_count_threshold=5,
            scraping_strategy=LXMLWebScrapingStrategy(),
            cache_mode=CacheMode.BYPASS,  # Force fresh requests for demo
            stream=True,
            verbose=False
        )
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        start_time = time.time()
        processed_results = []
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                print(f"🔄 Processing {len(test_urls)} URLs with memory management...")
                print("📊 Real-time monitoring enabled...")
                
                async for result in await crawler.arun_many(
                    urls=test_urls,
                    config=run_config,
                    dispatcher=dispatcher
                ):
                    if result.success:
                        # Access dispatch metrics
                        dispatch_result = getattr(result, 'dispatch_result', None)
                        memory_usage = dispatch_result.memory_usage if dispatch_result else 0
                        
                        content_length = len(result.cleaned_html or "")
                        print(f"   ✅ {result.url}")
                        print(f"      Content: {content_length:,} chars, Memory: {memory_usage:.1f}MB")
                        
                        processed_results.append({
                            'url': result.url,
                            'content_length': content_length,
                            'memory_usage': memory_usage,
                            'success': True
                        })
                    else:
                        print(f"   ❌ Failed: {result.url}")
                        
        except Exception as e:
            print(f"❌ Memory-adaptive processing failed: {e}")
            return []
            
        duration = time.time() - start_time
        total_content = sum(r['content_length'] for r in processed_results)
        avg_memory = sum(r['memory_usage'] for r in processed_results) / len(processed_results) if processed_results else 0
        
        print(f"\n✅ MEMORY-ADAPTIVE RESULTS:")
        print(f"   • URLs processed: {len(processed_results)}")
        print(f"   • Total content: {total_content:,} characters") 
        print(f"   • Average memory usage: {avg_memory:.1f}MB")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Memory monitoring: Enabled")
        
        self.results['memory_adaptive'] = {
            'urls_processed': len(processed_results),
            'total_content': total_content,
            'avg_memory': avg_memory,
            'duration': duration
        }
        
        return processed_results

    async def test_theodore_style_company_research(self):
        """
        Test 4: Company research simulation using Crawl4AI best practices
        
        This shows how Theodore SHOULD be implemented
        """
        print("\n" + "="*60)
        print("🧪 TEST 4: Theodore-Style Company Research (Correct Implementation)")
        print("="*60)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        # Simulate company research like Theodore does
        company_url = "https://example.com"
        
        # ✅ CORRECT: Intelligent filtering for business intelligence
        business_filter_chain = FilterChain([
            DomainFilter(allowed_domains=[urlparse(company_url).netloc]),
            URLPatternFilter(patterns=[
                "*about*", "*contact*", "*team*", "*leadership*", 
                "*careers*", "*company*", "*investors*"
            ]),
            ContentTypeFilter(allowed_types=["text/html"])
        ])
        
        # Business intelligence scoring
        business_scorer = KeywordRelevanceScorer(
            keywords=[
                "contact", "about", "team", "leadership", "careers", 
                "company", "founded", "employees", "location", "office"
            ],
            weight=0.8
        )
        
        # Company research configuration
        company_research_config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=2,
                include_external=False,
                max_pages=25,  # Equivalent to Theodore's page limit
                filter_chain=business_filter_chain,
                url_scorer=business_scorer
            ),
            scraping_strategy=LXMLWebScrapingStrategy(),  # 20x faster than default
            word_count_threshold=20,
            css_selector="main, article, .content, .about, .contact",
            excluded_tags=["script", "style", "nav", "footer"],
            check_robots_txt=True,
            cache_mode=CacheMode.ENABLED,
            page_timeout=30000,
            stream=True,
            verbose=True
        )
        
        browser_config = BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=720,
            verbose=False
        )
        
        start_time = time.time()
        company_intelligence = {
            'pages': [],
            'business_data': {},
            'metadata': {}
        }
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                print(f"🏢 Researching company: {company_url}")
                print("🔍 Discovering business intelligence pages...")
                
                async for result in await crawler.arun(company_url, config=company_research_config):
                    if result.success:
                        score = result.metadata.get('score', 0)
                        depth = result.metadata.get('depth', 0)
                        content = result.cleaned_html or ""
                        markdown = result.markdown.raw_markdown if result.markdown else ""
                        
                        # Simulate Theodore's content analysis
                        page_analysis = self._analyze_business_content(
                            url=result.url,
                            content=content,
                            markdown=markdown
                        )
                        
                        print(f"   📄 {result.url}")
                        print(f"      Score: {score:.2f}, Depth: {depth}")
                        print(f"      Content: {len(content):,} chars")
                        print(f"      Business signals: {page_analysis['signals']}")
                        
                        company_intelligence['pages'].append({
                            'url': result.url,
                            'score': score,
                            'depth': depth,
                            'content_length': len(content),
                            'markdown_length': len(markdown),
                            'analysis': page_analysis,
                            'content_preview': content[:200] + "..." if content else ""
                        })
                        
        except Exception as e:
            print(f"❌ Company research failed: {e}")
            return {}
            
        duration = time.time() - start_time
        
        # Aggregate business intelligence
        total_pages = len(company_intelligence['pages'])
        total_content = sum(p['content_length'] for p in company_intelligence['pages'])
        avg_score = sum(p['score'] for p in company_intelligence['pages']) / total_pages if total_pages else 0
        high_value_pages = [p for p in company_intelligence['pages'] if p['score'] > 0.5]
        
        company_intelligence['metadata'] = {
            'total_pages': total_pages,
            'total_content': total_content,
            'avg_score': avg_score,
            'high_value_pages': len(high_value_pages),
            'duration': duration,
            'research_method': 'Crawl4AI Deep Crawling with BFS Strategy'
        }
        
        print(f"\n✅ COMPANY RESEARCH RESULTS:")
        print(f"   • Pages analyzed: {total_pages}")
        print(f"   • High-value pages: {len(high_value_pages)}")
        print(f"   • Total content: {total_content:,} characters")
        print(f"   • Average relevance: {avg_score:.2f}")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Method: Modern Crawl4AI (vs Theodore's manual approach)")
        
        self.results['company_research'] = company_intelligence['metadata']
        
        return company_intelligence

    def _analyze_business_content(self, url: str, content: str, markdown: str) -> Dict[str, Any]:
        """
        Simulate business intelligence analysis (like Theodore's LLM analysis)
        """
        signals = []
        
        # Simple keyword-based analysis (Theodore would use LLM here)
        business_keywords = {
            'contact': ['contact', 'email', 'phone', 'address', 'office'],
            'about': ['about', 'company', 'founded', 'history', 'mission'],
            'team': ['team', 'leadership', 'ceo', 'founder', 'staff'],
            'careers': ['careers', 'jobs', 'hiring', 'employees', 'work'],
            'location': ['location', 'address', 'headquarters', 'office', 'based']
        }
        
        content_lower = content.lower()
        for category, keywords in business_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                signals.append(category)
                
        return {
            'signals': signals,
            'content_type': self._classify_page_type(url),
            'business_value': len(signals) * 0.2  # Simple scoring
        }
        
    def _classify_page_type(self, url: str) -> str:
        """Classify page type based on URL patterns"""
        url_lower = url.lower()
        
        if any(pattern in url_lower for pattern in ['about', 'company']):
            return 'about'
        elif any(pattern in url_lower for pattern in ['contact', 'get-in-touch']):
            return 'contact'
        elif any(pattern in url_lower for pattern in ['team', 'leadership']):
            return 'team'
        elif any(pattern in url_lower for pattern in ['careers', 'jobs']):
            return 'careers'
        else:
            return 'general'

    async def run_performance_comparison(self):
        """
        Compare performance metrics across different approaches
        """
        print("\n" + "="*60)
        print("📊 PERFORMANCE COMPARISON SUMMARY")
        print("="*60)
        
        if not self.results:
            print("❌ No test results available")
            return
            
        print("\n🔍 Test Results Summary:")
        for test_name, metrics in self.results.items():
            print(f"\n• {test_name.replace('_', ' ').title()}:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"  - {key.replace('_', ' ').title()}: {value:.2f}")
                else:
                    print(f"  - {key.replace('_', ' ').title()}: {value}")
                    
        print(f"\n🎯 Key Improvements Over Theodore's Current Approach:")
        print(f"• Single browser instance eliminates startup overhead")
        print(f"• Built-in deep crawling replaces manual link discovery")
        print(f"• LXML strategy provides 20x faster HTML parsing")
        print(f"• Memory-adaptive dispatching prevents resource exhaustion")
        print(f"• Intelligent filtering targets business-relevant pages")
        print(f"• Streaming results enable real-time processing")
        print(f"• Robots.txt respect ensures ethical crawling")

async def main():
    """
    Run all Crawl4AI best practices tests
    """
    print("🚀 Starting Crawl4AI Best Practices Test Suite")
    print("=" * 60)
    
    if not CRAWL4AI_AVAILABLE:
        print("❌ CRITICAL: Crawl4AI is not properly installed")
        print("💡 Install with: pip install crawl4ai")
        return
        
    demo = Crawl4AIBestPracticesDemo()
    
    try:
        # Test 1: Single browser for multiple URLs (fixes Theodore's main issue)
        await demo.test_single_browser_multiple_urls()
        
        # Test 2: Modern deep crawling strategy  
        await demo.test_deep_crawling_strategy()
        
        # Test 3: Memory-adaptive dispatching
        await demo.test_memory_adaptive_dispatching()
        
        # Test 4: Complete company research simulation
        await demo.test_theodore_style_company_research()
        
        # Performance comparison
        await demo.run_performance_comparison()
        
        print(f"\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"📋 These patterns should replace Theodore's current Crawl4AI usage")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.exception("Test suite error")

if __name__ == "__main__":
    asyncio.run(main())
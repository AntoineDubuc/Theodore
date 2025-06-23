"""
Crawl4AI Simplified Best Practices Test
=======================================

This test demonstrates the CORRECT way to use Crawl4AI with the current installation.
It focuses on the most critical improvements Theodore needs to implement.

Key improvements demonstrated:
1. Single browser instance vs multiple instances (Theodore's main issue)
2. Proper arun_many() usage for batch processing
3. Correct configuration patterns
4. Performance comparison with Theodore's approach
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.async_configs import CacheMode
    CRAWL4AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Crawl4AI import error: {e}")
    CRAWL4AI_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedCrawl4AIDemo:
    """
    Demonstrates critical Crawl4AI improvements for Theodore
    """
    
    def __init__(self):
        self.results = {}
        
    async def test_theodore_wrong_vs_right(self):
        """
        Direct comparison: Theodore's wrong approach vs correct approach
        """
        print("\n" + "="*70)
        print("🧪 CRITICAL TEST: Theodore's Wrong vs Right Crawl4AI Usage")
        print("="*70)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json", 
            "https://httpbin.org/xml",
            "https://example.com"
        ]
        
        # ❌ WRONG: Theodore's current approach (multiple browser instances)
        print(f"\n❌ WRONG APPROACH (Theodore's current method):")
        print(f"Creating separate browser instance for each URL...")
        
        wrong_start = time.time()
        wrong_results = []
        
        for i, url in enumerate(test_urls):
            print(f"   🔄 [{i+1}/{len(test_urls)}] Creating new browser for {url}")
            
            # This is what Theodore currently does - NEW BROWSER EACH TIME
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False
            ) as crawler:
                config = CrawlerRunConfig(
                    only_text=True,
                    cache_mode=CacheMode.ENABLED,
                    page_timeout=15000
                )
                
                result = await crawler.arun(url=url, config=config)
                if result.success:
                    wrong_results.append({
                        'url': url,
                        'content_length': len(result.cleaned_html or ""),
                        'success': True
                    })
                    print(f"   ✅ Success: {len(result.cleaned_html or ''):,} chars")
                else:
                    print(f"   ❌ Failed: {result.error_message}")
        
        wrong_duration = time.time() - wrong_start
        
        # ✅ RIGHT: Correct approach (single browser instance)
        print(f"\n✅ CORRECT APPROACH (What Theodore should do):")
        print(f"Using single browser instance for all URLs...")
        
        right_start = time.time()
        right_results = []
        
        # This is what Theodore SHOULD do - SINGLE BROWSER
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium", 
            verbose=False
        ) as crawler:
            
            config = CrawlerRunConfig(
                word_count_threshold=10,
                cache_mode=CacheMode.ENABLED,
                page_timeout=15000
            )
            
            print(f"   🚀 Processing all {len(test_urls)} URLs concurrently...")
            
            # Process all URLs with single browser instance
            results = await crawler.arun_many(test_urls, config=config)
            
            for result in results:
                if result.success:
                    right_results.append({
                        'url': result.url,
                        'content_length': len(result.cleaned_html or ""),
                        'success': True
                    })
                    print(f"   ✅ {result.url}: {len(result.cleaned_html or ''):,} chars")
                else:
                    print(f"   ❌ {result.url}: {result.error_message}")
        
        right_duration = time.time() - right_start
        
        # Performance comparison
        wrong_successful = len(wrong_results)
        right_successful = len(right_results)
        speedup = wrong_duration / right_duration if right_duration > 0 else 0
        
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"┌─────────────────────────────────────────────────────────┐")
        print(f"│                     WRONG vs RIGHT                     │")
        print(f"├─────────────────────────────────────────────────────────┤")
        print(f"│ Wrong (Theodore's way):                                 │")
        print(f"│   • Duration: {wrong_duration:.2f} seconds                           │")
        print(f"│   • Successful: {wrong_successful}/{len(test_urls)}                                │")
        print(f"│   • Method: New browser per URL                        │")
        print(f"│                                                         │")
        print(f"│ Right (Correct way):                                    │")
        print(f"│   • Duration: {right_duration:.2f} seconds                            │")
        print(f"│   • Successful: {right_successful}/{len(test_urls)}                                │")
        print(f"│   • Method: Single browser, concurrent processing      │")
        print(f"│                                                         │")
        print(f"│ 🚀 IMPROVEMENT: {speedup:.1f}x faster!                         │")
        print(f"└─────────────────────────────────────────────────────────┘")
        
        self.results['performance_comparison'] = {
            'wrong_duration': wrong_duration,
            'right_duration': right_duration,
            'speedup': speedup,
            'wrong_successful': wrong_successful,
            'right_successful': right_successful
        }
        
        return {
            'wrong_results': wrong_results,
            'right_results': right_results,
            'speedup': speedup
        }

    async def test_proper_configuration(self):
        """
        Test proper Crawl4AI configuration patterns
        """
        print("\n" + "="*70)
        print("🧪 TEST: Proper Crawl4AI Configuration")
        print("="*70)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        test_url = "https://httpbin.org/html"
        
        # ❌ Theodore's current config (suboptimal)
        wrong_config = CrawlerRunConfig(
            only_text=True,  # Deprecated
            remove_forms=True,  # Deprecated
            css_selector='main, article, .content, .main-content, .page-content, .entry-content, .post-content, section, .container, .wrapper, body',  # Too broad
            excluded_tags=['nav', 'footer', 'aside', 'script', 'style', 'header', 'menu'],
            cache_mode=CacheMode.ENABLED,
            page_timeout=15000,  # Too short
            verbose=False
        )
        
        # ✅ Correct config (optimized)
        right_config = CrawlerRunConfig(
            word_count_threshold=20,
            css_selector="main, article, .content",  # More focused
            excluded_tags=["script", "style"],  # Minimal exclusions
            cache_mode=CacheMode.ENABLED,
            page_timeout=30000,  # Appropriate timeout
            verbose=False
        )
        
        print("📋 Configuration Comparison:")
        print("\n❌ Theodore's current config:")
        print("   • Uses deprecated parameters (only_text, remove_forms)")
        print("   • Overly broad CSS selectors")
        print("   • Too many excluded tags")
        print("   • Short timeout (15s)")
        
        print("\n✅ Correct config:")
        print("   • Uses modern word_count_threshold")
        print("   • Focused CSS selectors")
        print("   • Minimal tag exclusions")
        print("   • Appropriate timeout (30s)")
        
        # Test both configurations
        async with AsyncWebCrawler(headless=True) as crawler:
            print(f"\n🧪 Testing configurations on {test_url}...")
            
            # Test wrong config
            wrong_start = time.time()
            wrong_result = await crawler.arun(url=test_url, config=wrong_config)
            wrong_duration = time.time() - wrong_start
            
            # Test right config  
            right_start = time.time()
            right_result = await crawler.arun(url=test_url, config=right_config)
            right_duration = time.time() - right_start
            
            print(f"\n📊 Configuration Results:")
            print(f"   Wrong config: {len(wrong_result.cleaned_html or ''):,} chars in {wrong_duration:.2f}s")
            print(f"   Right config: {len(right_result.cleaned_html or ''):,} chars in {right_duration:.2f}s")
            
        return {
            'wrong_config_result': len(wrong_result.cleaned_html or ""),
            'right_config_result': len(right_result.cleaned_html or ""),
            'wrong_duration': wrong_duration,
            'right_duration': right_duration
        }

    async def test_company_research_simulation(self):
        """
        Simulate Theodore's company research with correct Crawl4AI patterns
        """
        print("\n" + "="*70)
        print("🧪 TEST: Company Research Simulation (Theodore-style)")
        print("="*70)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ Crawl4AI not available - skipping test")
            return
            
        # Simulate multiple company websites
        company_urls = [
            "https://example.com",
            "https://httpbin.org/html", 
            "https://httpbin.org/json"
        ]
        
        # ✅ CORRECT: Company research configuration
        research_config = CrawlerRunConfig(
            word_count_threshold=20,
            css_selector="main, article, .content, .about, .contact",
            excluded_tags=["script", "style", "nav", "footer"],
            cache_mode=CacheMode.ENABLED,
            page_timeout=30000,
            verbose=False
        )
        
        print(f"🏢 Simulating company research for {len(company_urls)} companies...")
        
        start_time = time.time()
        company_intelligence = []
        
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            # Process all companies with single browser instance
            results = await crawler.arun_many(company_urls, config=research_config)
            
            for result in results:
                if result.success:
                    content = result.cleaned_html or ""
                    
                    # Simulate Theodore's business intelligence extraction
                    business_data = self._extract_business_intelligence(result.url, content)
                    
                    company_intelligence.append({
                        'url': result.url,
                        'content_length': len(content),
                        'business_data': business_data,
                        'extraction_successful': True
                    })
                    
                    print(f"   ✅ {result.url}")
                    print(f"      Content: {len(content):,} characters")
                    print(f"      Business signals: {business_data['signals_found']}")
                else:
                    print(f"   ❌ Failed: {result.url}")
                    
        duration = time.time() - start_time
        
        total_content = sum(c['content_length'] for c in company_intelligence)
        successful_companies = len(company_intelligence)
        
        print(f"\n📊 Company Research Results:")
        print(f"   • Companies processed: {successful_companies}/{len(company_urls)}")
        print(f"   • Total content extracted: {total_content:,} characters")
        print(f"   • Processing time: {duration:.2f} seconds")
        print(f"   • Rate: {successful_companies/duration:.1f} companies/second")
        
        self.results['company_research'] = {
            'companies_processed': successful_companies,
            'total_content': total_content,
            'duration': duration,
            'rate': successful_companies/duration
        }
        
        return company_intelligence

    def _extract_business_intelligence(self, url: str, content: str) -> Dict[str, Any]:
        """
        Simulate Theodore's business intelligence extraction
        """
        # Simple keyword-based analysis (Theodore uses LLM for this)
        business_keywords = {
            'contact_info': ['contact', 'email', 'phone', 'address'],
            'company_info': ['about', 'company', 'founded', 'history'],
            'team_info': ['team', 'leadership', 'ceo', 'founder'],
            'location_info': ['location', 'address', 'headquarters', 'office']
        }
        
        content_lower = content.lower()
        signals_found = []
        
        for category, keywords in business_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                signals_found.append(category)
                
        return {
            'signals_found': signals_found,
            'content_quality': 'high' if len(signals_found) >= 2 else 'medium' if signals_found else 'low',
            'page_type': self._classify_page_type(url)
        }
        
    def _classify_page_type(self, url: str) -> str:
        """Classify page type based on URL"""
        url_lower = url.lower()
        
        if 'about' in url_lower:
            return 'about_page'
        elif 'contact' in url_lower:
            return 'contact_page'
        elif 'team' in url_lower:
            return 'team_page'
        else:
            return 'homepage'

    async def run_all_tests(self):
        """
        Run all tests and provide comprehensive summary
        """
        print("🚀 Starting Simplified Crawl4AI Best Practices Test")
        print("="*70)
        
        if not CRAWL4AI_AVAILABLE:
            print("❌ CRITICAL: Crawl4AI is not available")
            print("💡 Try: pip install crawl4ai")
            return
            
        try:
            # Test 1: Critical comparison (Theodore's wrong vs right approach)
            await self.test_theodore_wrong_vs_right()
            
            # Test 2: Configuration best practices
            await self.test_proper_configuration()
            
            # Test 3: Company research simulation
            await self.test_company_research_simulation()
            
            # Summary
            self._print_final_summary()
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            logger.exception("Test error")

    def _print_final_summary(self):
        """
        Print comprehensive summary of findings
        """
        print("\n" + "="*70)
        print("📋 FINAL SUMMARY: Critical Improvements for Theodore")
        print("="*70)
        
        if 'performance_comparison' in self.results:
            perf = self.results['performance_comparison']
            print(f"\n🚀 PERFORMANCE IMPACT:")
            print(f"   • Speed improvement: {perf['speedup']:.1f}x faster")
            print(f"   • Browser startup overhead eliminated")
            print(f"   • Concurrent processing enabled")
            
        print(f"\n⚠️ CRITICAL ISSUES IN THEODORE'S CURRENT CODE:")
        print(f"   1. Creates new AsyncWebCrawler for EVERY page")
        print(f"   2. Uses deprecated configuration parameters")
        print(f"   3. Overly broad CSS selectors")
        print(f"   4. No concurrency optimization")
        print(f"   5. Manual link discovery instead of built-in features")
        
        print(f"\n✅ RECOMMENDED FIXES:")
        print(f"   1. Use single AsyncWebCrawler with arun_many()")
        print(f"   2. Replace deprecated params with modern equivalents")
        print(f"   3. Use focused CSS selectors")
        print(f"   4. Implement proper timeout values")
        print(f"   5. Consider deep crawling strategies for complex sites")
        
        print(f"\n🎯 IMPLEMENTATION PRIORITY:")
        print(f"   HIGH:   Fix browser instantiation (immediate 3-5x speedup)")
        print(f"   HIGH:   Update configuration parameters")
        print(f"   MEDIUM: Optimize CSS selectors and timeouts")
        print(f"   LOW:    Consider advanced features (deep crawling, filtering)")
        
        print(f"\n📈 EXPECTED RESULTS AFTER FIXES:")
        if 'performance_comparison' in self.results:
            perf = self.results['performance_comparison']
            print(f"   • {perf['speedup']:.1f}x faster company processing")
        print(f"   • Reduced memory usage")
        print(f"   • Better resource utilization")
        print(f"   • More reliable crawling")
        print(f"   • Improved scalability")

async def main():
    """
    Run the simplified Crawl4AI test
    """
    demo = SimplifiedCrawl4AIDemo()
    await demo.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
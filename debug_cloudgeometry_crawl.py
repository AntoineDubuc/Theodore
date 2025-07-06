#!/usr/bin/env python3
"""
CloudGeometry Crawling Diagnostic Test
Identifies the root cause of Phase 3 content extraction failures
"""

import asyncio
import aiohttp
import time
import logging
from urllib.parse import urlparse
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.ssl_config import get_aiohttp_connector, get_browser_args, should_verify_ssl

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test URLs from CloudGeometry
TEST_URLS = [
    "https://cloudgeometry.com/",
    "https://cloudgeometry.com/about",
    "https://cloudgeometry.com/contact",
    "https://cloudgeometry.com/services",
    "https://cloudgeometry.com/blog",
]

BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def test_basic_connectivity():
    """Test basic HTTP connectivity to CloudGeometry"""
    print("\n" + "="*60)
    print("TEST 1: Basic HTTP Connectivity")
    print("="*60)
    
    ssl_connector = get_aiohttp_connector(verify=should_verify_ssl())
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=ssl_connector, timeout=timeout) as session:
        for url in TEST_URLS:
            try:
                print(f"\n🔍 Testing: {url}")
                start_time = time.time()
                
                async with session.head(url, headers={'User-Agent': BROWSER_USER_AGENT}) as response:
                    duration = time.time() - start_time
                    print(f"   Status: {response.status}")
                    print(f"   Duration: {duration:.2f}s")
                    print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                    print(f"   Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
                    print(f"   Server: {response.headers.get('Server', 'Unknown')}")
                    
                    if response.status == 200:
                        print("   ✅ Connection successful")
                    else:
                        print(f"   ❌ HTTP error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Connection failed: {e}")

async def test_single_page_crawl():
    """Test single page crawl with different configurations"""
    print("\n" + "="*60)
    print("TEST 2: Single Page Crawl with Different Configurations")
    print("="*60)
    
    test_url = "https://cloudgeometry.com/"
    
    # Test different browser configurations
    configurations = [
        {
            "name": "Basic Configuration",
            "browser_args": [],
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                word_count_threshold=10,
                page_timeout=30000,
                verbose=True
            )
        },
        {
            "name": "SSL-Ignoring Configuration",
            "browser_args": get_browser_args(ignore_ssl=True),
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                word_count_threshold=10,
                page_timeout=30000,
                verbose=True
            )
        },
        {
            "name": "Enhanced Configuration",
            "browser_args": get_browser_args(ignore_ssl=True),
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                page_timeout=45000,
                verbose=True
            )
        }
    ]
    
    for config_info in configurations:
        print(f"\n🧪 Testing: {config_info['name']}")
        print("-" * 40)
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=True,
                browser_args=config_info['browser_args']
            ) as crawler:
                start_time = time.time()
                result = await crawler.arun(url=test_url, config=config_info['config'])
                duration = time.time() - start_time
                
                print(f"   Duration: {duration:.2f}s")
                print(f"   Success: {result.success}")
                print(f"   Status Code: {result.status_code if hasattr(result, 'status_code') else 'N/A'}")
                print(f"   HTML Length: {len(result.html) if result.html else 0}")
                print(f"   Cleaned HTML Length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                print(f"   Markdown Length: {len(result.markdown) if hasattr(result, 'markdown') and result.markdown else 0}")
                
                if result.success and result.cleaned_html:
                    print("   ✅ Crawl successful")
                    print(f"   Content preview: {result.cleaned_html[:200]}...")
                else:
                    print("   ❌ Crawl failed")
                    if hasattr(result, 'error_message'):
                        print(f"   Error: {result.error_message}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            logger.exception(f"Single page crawl failed for {config_info['name']}")

async def test_concurrent_crawling():
    """Test concurrent crawling with different limits"""
    print("\n" + "="*60)
    print("TEST 3: Concurrent Crawling with Different Limits")
    print("="*60)
    
    concurrency_limits = [1, 2, 5, 10, 20]
    
    for limit in concurrency_limits:
        print(f"\n🧪 Testing: {limit} concurrent requests")
        print("-" * 40)
        
        browser_args = get_browser_args(ignore_ssl=True)
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False,
                browser_args=browser_args
            ) as crawler:
                config = CrawlerRunConfig(
                    user_agent=BROWSER_USER_AGENT,
                    word_count_threshold=10,
                    page_timeout=30000,
                    verbose=False
                )
                
                start_time = time.time()
                
                # Test with limited URLs based on concurrency
                test_urls = TEST_URLS[:limit] if limit <= len(TEST_URLS) else TEST_URLS * (limit // len(TEST_URLS) + 1)
                test_urls = test_urls[:limit]
                
                results = await crawler.arun_many(test_urls, config=config)
                duration = time.time() - start_time
                
                successful_results = [r for r in results if r.success]
                failed_results = [r for r in results if not r.success]
                
                print(f"   Total URLs: {len(test_urls)}")
                print(f"   Duration: {duration:.2f}s")
                print(f"   Successful: {len(successful_results)}")
                print(f"   Failed: {len(failed_results)}")
                print(f"   Success Rate: {len(successful_results)/len(test_urls)*100:.1f}%")
                
                if failed_results:
                    print("   ❌ Some failures detected")
                    for i, result in enumerate(failed_results[:3]):  # Show first 3 failures
                        print(f"      Failed URL: {result.url}")
                        if hasattr(result, 'error_message'):
                            print(f"      Error: {result.error_message}")
                else:
                    print("   ✅ All crawls successful")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            logger.exception(f"Concurrent crawling failed for limit {limit}")

async def test_timeout_scenarios():
    """Test different timeout scenarios"""
    print("\n" + "="*60)
    print("TEST 4: Timeout Scenarios")
    print("="*60)
    
    timeouts = [5000, 15000, 30000, 45000, 60000]  # 5s to 60s
    test_url = "https://cloudgeometry.com/"
    
    for timeout_ms in timeouts:
        print(f"\n🧪 Testing: {timeout_ms}ms timeout")
        print("-" * 40)
        
        browser_args = get_browser_args(ignore_ssl=True)
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False,
                browser_args=browser_args
            ) as crawler:
                config = CrawlerRunConfig(
                    user_agent=BROWSER_USER_AGENT,
                    word_count_threshold=10,
                    page_timeout=timeout_ms,
                    verbose=False
                )
                
                start_time = time.time()
                result = await crawler.arun(url=test_url, config=config)
                duration = time.time() - start_time
                
                print(f"   Duration: {duration:.2f}s")
                print(f"   Success: {result.success}")
                print(f"   Content Length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                
                if result.success:
                    print("   ✅ Crawl successful")
                else:
                    print("   ❌ Crawl failed")
                    if hasattr(result, 'error_message'):
                        print(f"   Error: {result.error_message}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_javascript_execution():
    """Test JavaScript execution scenarios"""
    print("\n" + "="*60)
    print("TEST 5: JavaScript Execution Scenarios")
    print("="*60)
    
    test_url = "https://cloudgeometry.com/"
    
    js_scenarios = [
        {
            "name": "No JavaScript",
            "js_code": None,
            "wait_for": None
        },
        {
            "name": "Basic JavaScript",
            "js_code": ["console.log('Basic JS test');"],
            "wait_for": None
        },
        {
            "name": "Scroll and Wait",
            "js_code": [
                "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});",
                "await new Promise(resolve => setTimeout(resolve, 2000));"
            ],
            "wait_for": "css:body"
        },
        {
            "name": "Advanced JavaScript",
            "js_code": [
                """
                try {
                    // Expand any collapsed menus
                    document.querySelectorAll('[data-toggle], .dropdown-toggle, .menu-toggle').forEach(btn => {
                        if (btn.click) btn.click();
                    });
                    
                    // Scroll to reveal content
                    window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                    
                    // Wait for any animations
                    await new Promise(resolve => setTimeout(resolve, 3000));
                } catch (e) { 
                    console.log('JS execution blocked:', e); 
                }
                """
            ],
            "wait_for": "css:main, css:article, css:.content"
        }
    ]
    
    for scenario in js_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print("-" * 40)
        
        browser_args = get_browser_args(ignore_ssl=True)
        
        try:
            async with AsyncWebCrawler(
                headless=True,
                browser_type="chromium",
                verbose=False,
                browser_args=browser_args
            ) as crawler:
                config_kwargs = {
                    "user_agent": BROWSER_USER_AGENT,
                    "word_count_threshold": 10,
                    "page_timeout": 45000,
                    "verbose": False
                }
                
                if scenario['js_code']:
                    config_kwargs['js_code'] = scenario['js_code']
                    
                if scenario['wait_for']:
                    config_kwargs['wait_for'] = scenario['wait_for']
                
                config = CrawlerRunConfig(**config_kwargs)
                
                start_time = time.time()
                result = await crawler.arun(url=test_url, config=config)
                duration = time.time() - start_time
                
                print(f"   Duration: {duration:.2f}s")
                print(f"   Success: {result.success}")
                print(f"   Content Length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                
                if result.success:
                    print("   ✅ Crawl successful")
                else:
                    print("   ❌ Crawl failed")
                    if hasattr(result, 'error_message'):
                        print(f"   Error: {result.error_message}")
                        
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_theodore_exact_configuration():
    """Test with Theodore's exact configuration from the scraper"""
    print("\n" + "="*60)
    print("TEST 6: Theodore's Exact Configuration")
    print("="*60)
    
    # Replicate Theodore's exact setup
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    try:
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=False,
            browser_args=browser_args
        ) as crawler:
            
            # Theodore's enhanced configuration
            config = CrawlerRunConfig(
                # Browser simulation and anti-bot bypass
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                
                # Content extraction optimization
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
                
                # JavaScript interaction
                js_code=[
                    """
                    try {
                        // Gentle scrolling with error handling
                        if (document.body && document.body.scrollHeight) {
                            window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                        }
                    } catch (e) { console.log('Scroll blocked:', e); }
                    """,
                    """
                    try {
                        // Safe button clicking with error handling
                        ['load-more', 'show-more', 'view-all', 'read-more'].forEach(className => {
                            const btn = document.querySelector('.' + className + ', button[class*="' + className + '"]');
                            if (btn) btn.click();
                        });
                    } catch (e) { console.log('Button click blocked:', e); }
                    """
                ],
                wait_for="css:.main-content, css:main, css:article",
                
                # Link and media handling
                exclude_external_links=False,
                exclude_social_media_links=True,
                exclude_domains=["ads.com", "tracking.com", "analytics.com"],
                
                # Performance and reliability
                cache_mode=CacheMode.ENABLED,
                page_timeout=45000,
                verbose=False
            )
            
            print(f"\n🧪 Testing Theodore's exact configuration on CloudGeometry URLs")
            print("-" * 40)
            
            start_time = time.time()
            results = await crawler.arun_many(TEST_URLS, config=config)
            duration = time.time() - start_time
            
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]
            
            print(f"   Total URLs: {len(TEST_URLS)}")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Successful: {len(successful_results)}")
            print(f"   Failed: {len(failed_results)}")
            print(f"   Success Rate: {len(successful_results)/len(TEST_URLS)*100:.1f}%")
            
            print(f"\n📊 DETAILED RESULTS:")
            for i, result in enumerate(results):
                status = "✅" if result.success else "❌"
                content_length = len(result.cleaned_html) if result.cleaned_html else 0
                print(f"   {status} {result.url}: {content_length} chars")
                
                if not result.success:
                    if hasattr(result, 'error_message'):
                        print(f"      Error: {result.error_message}")
                    if hasattr(result, 'status_code'):
                        print(f"      Status: {result.status_code}")
                        
            if failed_results:
                print(f"\n🔍 FAILURE ANALYSIS:")
                for result in failed_results:
                    print(f"   Failed URL: {result.url}")
                    if hasattr(result, 'error_message'):
                        print(f"   Error Message: {result.error_message}")
                    if hasattr(result, 'status_code'):
                        print(f"   Status Code: {result.status_code}")
                        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        logger.exception("Theodore's exact configuration test failed")

async def main():
    """Run all diagnostic tests"""
    print("="*60)
    print("CLOUDGEOMETRY CRAWLING DIAGNOSTIC TEST")
    print("="*60)
    print(f"Target Domain: cloudgeometry.com")
    print(f"SSL Verification: {should_verify_ssl()}")
    print(f"Test URLs: {len(TEST_URLS)}")
    
    # Run all tests
    await test_basic_connectivity()
    await test_single_page_crawl()
    await test_concurrent_crawling()
    await test_timeout_scenarios()
    await test_javascript_execution()
    await test_theodore_exact_configuration()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("Review the results above to identify the root cause of crawling failures.")

if __name__ == "__main__":
    asyncio.run(main())
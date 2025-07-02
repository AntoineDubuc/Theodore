#!/usr/bin/env python3
"""
Debug Link Discovery - Test enhanced Crawl4AI link discovery
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.ssl_config import get_browser_args, should_verify_ssl

# Browser user agent to mimic Chrome on macOS for better compatibility
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def test_link_discovery(url: str):
    """Test link discovery with enhanced Crawl4AI configuration"""
    print(f"🔍 Testing link discovery for: {url}")
    
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=True,  # Enable verbose for debugging
        browser_args=browser_args
    ) as crawler:
        
        # Test basic configuration first
        print(f"\n🧪 Test 1: Basic configuration")
        config_basic = CrawlerRunConfig(
            user_agent=BROWSER_USER_AGENT,
            word_count_threshold=1,
            css_selector="a[href]",
            excluded_tags=["script", "style"],
            cache_mode=CacheMode.ENABLED,
            page_timeout=15000,
            verbose=True
        )
        
        result_basic = await crawler.arun(url=url, config=config_basic)
        
        if result_basic and result_basic.html:
            soup = BeautifulSoup(result_basic.html, 'html.parser')
            links = soup.find_all('a', href=True)
            print(f"  📄 Basic config found {len(links)} links")
            if links:
                print(f"  📋 First 5 links:")
                for i, link in enumerate(links[:5], 1):
                    href = link['href']
                    full_url = urljoin(url, href)
                    print(f"    {i}. {full_url}")
        else:
            print(f"  ❌ Basic config: No HTML content retrieved")
        
        # Test enhanced configuration
        print(f"\n🧪 Test 2: Enhanced configuration with magic mode")
        config_enhanced = CrawlerRunConfig(
            user_agent=BROWSER_USER_AGENT,
            word_count_threshold=1,
            css_selector="a[href], nav, footer, .menu, .navigation",
            excluded_tags=["script", "style"],
            cache_mode=CacheMode.ENABLED,
            page_timeout=15000,
            verbose=True,
            simulate_user=True,
            magic=True,
            js_code=[
                """
                try {
                    // Expand any collapsed menus
                    document.querySelectorAll('[data-toggle], .dropdown-toggle, .menu-toggle').forEach(btn => {
                        if (btn.click) btn.click();
                    });
                } catch (e) { console.log('Menu expansion blocked:', e); }
                """
            ]
        )
        
        result_enhanced = await crawler.arun(url=url, config=config_enhanced)
        
        if result_enhanced and result_enhanced.html:
            soup = BeautifulSoup(result_enhanced.html, 'html.parser')
            links = soup.find_all('a', href=True)
            print(f"  📄 Enhanced config found {len(links)} links")
            if links:
                print(f"  📋 First 5 links:")
                for i, link in enumerate(links[:5], 1):
                    href = link['href']
                    full_url = urljoin(url, href)
                    print(f"    {i}. {full_url}")
                    
                # Count domain-specific links
                domain = urlparse(url).netloc
                same_domain_links = [link for link in links if urlparse(urljoin(url, link['href'])).netloc == domain]
                print(f"  🏠 Same-domain links: {len(same_domain_links)}")
        else:
            print(f"  ❌ Enhanced config: No HTML content retrieved")
        
        # Test with wait for content
        print(f"\n🧪 Test 3: Wait for content configuration")
        config_wait = CrawlerRunConfig(
            user_agent=BROWSER_USER_AGENT,
            word_count_threshold=1,
            css_selector="body",
            excluded_tags=["script", "style"],
            cache_mode=CacheMode.ENABLED,
            page_timeout=20000,
            verbose=True,
            simulate_user=True,
            magic=True,
            wait_for="css:nav, css:.navigation, css:header, css:footer",
            js_code=[
                """
                try {
                    // Wait for navigation to load
                    setTimeout(() => {
                        console.log('Navigation loaded');
                    }, 2000);
                } catch (e) { console.log('Wait script blocked:', e); }
                """
            ]
        )
        
        result_wait = await crawler.arun(url=url, config=config_wait)
        
        if result_wait and result_wait.html:
            soup = BeautifulSoup(result_wait.html, 'html.parser')
            links = soup.find_all('a', href=True)
            print(f"  📄 Wait config found {len(links)} links")
            if links:
                print(f"  📋 First 5 links:")
                for i, link in enumerate(links[:5], 1):
                    href = link['href']
                    full_url = urljoin(url, href)
                    print(f"    {i}. {full_url}")
        else:
            print(f"  ❌ Wait config: No HTML content retrieved")

async def main():
    """Test multiple websites"""
    test_sites = [
        "https://www.krkmusic.com",
        "https://example.com", 
        "https://github.com",
        "https://stripe.com"
    ]
    
    for site in test_sites:
        print(f"\n{'='*60}")
        print(f"Testing: {site}")
        print(f"{'='*60}")
        try:
            await test_link_discovery(site)
        except Exception as e:
            print(f"❌ Error testing {site}: {e}")
        print(f"\n")

if __name__ == "__main__":
    asyncio.run(main())
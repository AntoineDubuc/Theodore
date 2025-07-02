#!/usr/bin/env python3
"""
Test Scraper Link Discovery - Replicate exact scraper logic
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

async def test_scraper_link_discovery(base_url: str, domain: str):
    """Test link discovery exactly as the scraper does it"""
    print(f"🔍 Testing scraper link discovery for: {base_url}")
    print(f"🏠 Domain: {domain}")
    
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False,
        browser_args=browser_args
    ) as crawler:
        
        # Exact configuration from scraper
        config = CrawlerRunConfig(
            user_agent=BROWSER_USER_AGENT,
            word_count_threshold=1,  # Very low threshold for link discovery
            css_selector="a[href], nav, footer, .menu, .navigation",  # Focus on navigation elements
            excluded_tags=["script", "style"],
            cache_mode=CacheMode.ENABLED,
            page_timeout=15000,  # Shorter timeout for link discovery
            verbose=False,
            simulate_user=True,      # Anti-bot bypass
            magic=True,              # Enhanced compatibility
            js_code=[
                # Simple JS to reveal hidden navigation
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
        
        result = await crawler.arun(url=base_url, config=config)
        
        discovered_links = set()
        
        if result and result.html:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract all links - EXACT scraper logic
            links_found = 0
            all_links_on_page = soup.find_all('a', href=True)
            print(f"  📄 Total <a> tags found: {len(all_links_on_page)}")
            
            for link in all_links_on_page:
                href = link['href']
                full_url = urljoin(base_url, href)
                
                print(f"    🔗 Processing: {href} -> {full_url}")
                print(f"        🏠 URL domain: {urlparse(full_url).netloc}")
                print(f"        🎯 Target domain: {domain}")
                print(f"        ✅ Same domain? {urlparse(full_url).netloc == domain}")
                
                # Only follow links on same domain - EXACT scraper logic
                if urlparse(full_url).netloc == domain:
                    discovered_links.add(full_url)
                    links_found += 1
                    print(f"        ✅ ADDED to discovered_links")
                    
                    # SAFETY: Limit links per page to prevent explosion
                    if links_found >= 50:  # Max 50 links per page
                        print(f"        🛑 Hit 50 link limit, breaking")
                        break
                else:
                    print(f"        ❌ SKIPPED (different domain)")
                    
                if links_found >= 10:  # Limit debug output
                    print(f"    ... (showing first 10 for debugging)")
                    break
            
            print(f"  📊 Final results:")
            print(f"     Total <a> tags: {len(all_links_on_page)}")
            print(f"     Same-domain links: {links_found}")
            print(f"     Discovered links: {len(discovered_links)}")
            
            if discovered_links:
                print(f"  📋 First 5 discovered links:")
                for i, link in enumerate(list(discovered_links)[:5], 1):
                    print(f"    {i}. {link}")
        else:
            print(f"  ❌ No HTML content retrieved")
        
        return discovered_links

async def main():
    """Test with KRK Music to debug the exact issue"""
    base_url = "https://www.krkmusic.com"
    domain = urlparse(base_url).netloc
    
    print(f"Testing with exact scraper logic:")
    print(f"Base URL: {base_url}")
    print(f"Domain: {domain}")
    print(f"{'='*60}")
    
    try:
        discovered_links = await test_scraper_link_discovery(base_url, domain)
        print(f"\n🎯 FINAL RESULT: {len(discovered_links)} links discovered")
        if len(discovered_links) == 0:
            print(f"❌ This explains why the scraper is failing!")
        else:
            print(f"✅ Link discovery should be working!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
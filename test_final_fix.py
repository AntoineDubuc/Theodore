#!/usr/bin/env python3
"""
Test Theodore's final fixed configuration (no wait_for)
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.ssl_config import get_browser_args, should_verify_ssl

TEST_URLS = [
    "https://cloudgeometry.com/",
    "https://cloudgeometry.com/about",
    "https://cloudgeometry.com/contact",
    "https://cloudgeometry.com/services",
    "https://cloudgeometry.com/blog"
]

BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def test_final_fix():
    """Test Theodore's final fixed configuration"""
    print("="*60)
    print("TESTING THEODORE'S FINAL FIXED CONFIGURATION")
    print("="*60)
    
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False,
        browser_args=browser_args
    ) as crawler:
        
        # Theodore's FINAL FIXED enhanced configuration
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
                    if (document.body && document.body.scrollHeight) {
                        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                    }
                } catch (e) { console.log('Scroll blocked:', e); }
                """,
                """
                try {
                    ['load-more', 'show-more', 'view-all', 'read-more'].forEach(className => {
                        const btn = document.querySelector('.' + className + ', button[class*="' + className + '"]');
                        if (btn) btn.click();
                    });
                } catch (e) { console.log('Button click blocked:', e); }
                """
            ],
            # FIXED: wait_for removed - was causing timeouts
            
            # Link and media handling
            exclude_external_links=False,
            exclude_social_media_links=True,
            exclude_domains=["ads.com", "tracking.com", "analytics.com"],
            
            # Performance and reliability
            cache_mode=CacheMode.ENABLED,
            page_timeout=45000,
            verbose=False
        )
        
        print(f"🚀 Testing FINAL FIXED configuration with {len(TEST_URLS)} URLs...")
        
        start_time = time.time()
        results = await crawler.arun_many(TEST_URLS, config=config)
        duration = time.time() - start_time
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n📊 RESULTS:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Total URLs: {len(TEST_URLS)}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Success Rate: {len(successful)/len(TEST_URLS)*100:.1f}%")
        
        # Process results like Theodore does
        successful_extractions = []
        
        for i, result in enumerate(results):
            current_page = i + 1
            
            if result.success:
                # Theodore's exact content extraction logic
                content = None
                content_source = None
                
                if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                    content = result.cleaned_html[:10000]
                    content_source = "cleaned_html"
                elif hasattr(result, 'markdown') and result.markdown and len(str(result.markdown).strip()) > 50:
                    content = str(result.markdown)[:10000]
                    content_source = "markdown"
                elif hasattr(result, 'extracted_content') and result.extracted_content and len(result.extracted_content.strip()) > 50:
                    content = result.extracted_content[:10000]
                    content_source = "extracted_content"
                
                if content:
                    successful_extractions.append({
                        'url': result.url,
                        'content': content
                    })
                    print(f"✅ [{current_page}/{len(TEST_URLS)}] Success: {len(content):,} chars from {content_source} - {result.url}")
                else:
                    print(f"❌ [{current_page}/{len(TEST_URLS)}] No content - {result.url}")
            else:
                print(f"❌ [{current_page}/{len(TEST_URLS)}] Failed - {result.url}")
                if hasattr(result, 'error_message'):
                    print(f"      Error: {result.error_message}")
        
        total_content = sum(len(page['content']) for page in successful_extractions)
        print(f"\n📈 EXTRACTION SUMMARY:")
        print(f"   Pages with content: {len(successful_extractions)}")
        print(f"   Total content chars: {total_content:,}")
        
        if len(successful_extractions) == len(TEST_URLS):
            print(f"\n🎉 SUCCESS! All pages extracted successfully!")
            print(f"   Theodore's scraper is now fixed for CloudGeometry!")
        elif len(successful_extractions) > 0:
            print(f"\n✅ MOSTLY FIXED! {len(successful_extractions)}/{len(TEST_URLS)} pages successful")
            print(f"   This should be sufficient for Theodore's analysis")
        else:
            print(f"\n❌ Still failing - need deeper investigation")

if __name__ == "__main__":
    asyncio.run(test_final_fix())
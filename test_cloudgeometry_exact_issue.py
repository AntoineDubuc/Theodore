#!/usr/bin/env python3
"""
Test CloudGeometry with Theodore's exact parallel extraction method
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.ssl_config import get_browser_args, should_verify_ssl

# Theodore's exact URLs
EXACT_URLS = [
    "https://cloudgeometry.com/",
    "https://cloudgeometry.com/about",
    "https://cloudgeometry.com/contact",
    "https://cloudgeometry.com/services",
    "https://cloudgeometry.com/blog"
]

BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def test_theodore_exact_parallel():
    """Test Theodore's exact parallel extraction method"""
    print("="*60)
    print("TESTING THEODORE'S EXACT PARALLEL EXTRACTION METHOD")
    print("="*60)
    
    # Theodore's exact browser configuration
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    print(f"Browser args: {browser_args}")
    print(f"SSL verify: {should_verify_ssl()}")
    print(f"Testing {len(EXACT_URLS)} URLs")
    
    # ✅ Theodore's exact approach: Single AsyncWebCrawler for all pages
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False,
        browser_args=browser_args
    ) as crawler:
        
        # Try Theodore's enhanced configuration first
        try:
            print("\n🧪 Testing Enhanced Configuration (Theodore's exact setup)")
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
            
            print(f"🚀 Processing {len(EXACT_URLS)} URLs with crawler.arun_many()...")
            
            start_time = time.time()
            results = await crawler.arun_many(EXACT_URLS, config=config)
            duration = time.time() - start_time
            
            print(f"\n📊 RESULTS SUMMARY:")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Total URLs: {len(EXACT_URLS)}")
            print(f"   Results returned: {len(results)}")
            
            # Process results exactly like Theodore does
            successful_extractions = []
            failed_extractions = []
            
            for i, result in enumerate(results):
                current_page = i + 1
                
                if result.success:
                    # Try to get the best available content (Theodore's exact logic)
                    content = None
                    content_source = None
                    
                    # First try cleaned HTML
                    if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                        content = result.cleaned_html[:10000]  # Limit to 10k chars
                        content_source = "cleaned_html"
                    # Fallback to markdown content
                    elif hasattr(result, 'markdown') and result.markdown and len(str(result.markdown).strip()) > 50:
                        content = str(result.markdown)[:10000]
                        content_source = "markdown"
                    # Final fallback to extracted text
                    elif hasattr(result, 'extracted_content') and result.extracted_content and len(result.extracted_content.strip()) > 50:
                        content = result.extracted_content[:10000]
                        content_source = "extracted_content"
                    
                    if content:
                        successful_extractions.append({
                            'url': result.url,
                            'content': content,
                            'content_source': content_source,
                            'content_length': len(content)
                        })
                        
                        print(f"✅ [{current_page}/{len(EXACT_URLS)}] Success: {len(content):,} chars from {content_source} - {result.url}")
                    else:
                        failed_extractions.append({
                            'url': result.url,
                            'reason': 'No content extracted'
                        })
                        print(f"❌ [{current_page}/{len(EXACT_URLS)}] No content extracted - {result.url}")
                else:
                    failed_extractions.append({
                        'url': result.url,
                        'reason': 'Crawl failed'
                    })
                    print(f"❌ [{current_page}/{len(EXACT_URLS)}] Crawl failed - {result.url}")
            
            print(f"\n📈 FINAL RESULTS:")
            print(f"   Successful extractions: {len(successful_extractions)}")
            print(f"   Failed extractions: {len(failed_extractions)}")
            print(f"   Success rate: {len(successful_extractions)/len(EXACT_URLS)*100:.1f}%")
            
            total_content_chars = sum(page['content_length'] for page in successful_extractions)
            print(f"   Total content extracted: {total_content_chars:,} characters")
            
            if failed_extractions:
                print(f"\n❌ FAILURES DETECTED:")
                for failure in failed_extractions:
                    print(f"   {failure['url']}: {failure['reason']}")
            else:
                print(f"\n✅ ALL EXTRACTIONS SUCCESSFUL!")
                
        except Exception as e:
            print(f"❌ Enhanced config failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Try fallback config
            print(f"\n🔄 Trying fallback configuration...")
            
            try:
                config = CrawlerRunConfig(
                    user_agent=BROWSER_USER_AGENT,
                    word_count_threshold=20,
                    css_selector="main, article, .content",
                    excluded_tags=["script", "style"],
                    cache_mode=CacheMode.ENABLED,
                    page_timeout=30000,
                    verbose=False
                )
                
                start_time = time.time()
                results = await crawler.arun_many(EXACT_URLS, config=config)
                duration = time.time() - start_time
                
                print(f"Fallback results: {len(results)} results in {duration:.2f}s")
                
                successful_fallback = sum(1 for r in results if r.success)
                print(f"Fallback success rate: {successful_fallback}/{len(EXACT_URLS)} ({successful_fallback/len(EXACT_URLS)*100:.1f}%)")
                
            except Exception as e2:
                print(f"❌ Fallback config also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_theodore_exact_parallel())
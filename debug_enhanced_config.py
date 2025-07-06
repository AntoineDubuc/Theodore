#!/usr/bin/env python3
"""
Debug Theodore's enhanced configuration to find the problematic parameter
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.ssl_config import get_browser_args, should_verify_ssl

TEST_URL = "https://cloudgeometry.com/"
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

async def test_config_components():
    """Test individual components of Theodore's enhanced configuration"""
    print("="*60)
    print("DEBUGGING THEODORE'S ENHANCED CONFIGURATION")
    print("="*60)
    
    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
    
    # Test configurations progressively
    configs = [
        {
            "name": "1. Basic Working Config",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                word_count_threshold=10,
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "2. + Anti-bot Features",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "3. + Content Selectors",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "4. + Overlay/Iframe Processing",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "5. + JavaScript Code",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
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
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "6. + Wait For Elements",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
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
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "7. + Link/Domain Filtering",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
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
                exclude_external_links=False,
                exclude_social_media_links=True,
                exclude_domains=["ads.com", "tracking.com", "analytics.com"],
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "8. + Cache & Full Theodore Config",
            "config": CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                simulate_user=True,
                magic=True,
                override_navigator=True,
                word_count_threshold=10,
                css_selector="main, article, .content, .main-content, section",
                excluded_tags=["nav", "footer", "aside", "script", "style"],
                remove_overlay_elements=True,
                process_iframes=True,
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
                exclude_external_links=False,
                exclude_social_media_links=True,
                exclude_domains=["ads.com", "tracking.com", "analytics.com"],
                cache_mode=CacheMode.ENABLED,
                page_timeout=45000,
                verbose=False
            )
        }
    ]
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False,
        browser_args=browser_args
    ) as crawler:
        
        for config_info in configs:
            print(f"\n🧪 Testing: {config_info['name']}")
            print("-" * 50)
            
            try:
                start_time = time.time()
                result = await crawler.arun(url=TEST_URL, config=config_info['config'])
                duration = time.time() - start_time
                
                print(f"   Duration: {duration:.2f}s")
                print(f"   Success: {result.success}")
                print(f"   Content Length: {len(result.cleaned_html) if result.cleaned_html else 0}")
                
                if result.success:
                    print("   ✅ Configuration works!")
                else:
                    print("   ❌ Configuration fails!")
                    if hasattr(result, 'error_message'):
                        print(f"   Error: {result.error_message}")
                    # This is where the issue appears - break here to identify the problematic parameter
                    break
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_config_components())
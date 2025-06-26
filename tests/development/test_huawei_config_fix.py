#!/usr/bin/env python3
"""
Test Theodore's exact configuration vs optimized configuration for Huawei
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode

async def test_config_comparison():
    """Compare Theodore's config vs optimized config for Huawei"""
    
    test_urls = [
        "https://www.huawei.com/en/about-huawei",
        "https://consumer.huawei.com/en",
        "https://www.huawei.com/en/sustainability"
    ]
    
    configs = [
        {
            "name": "Theodore's Current Config (Restrictive)",
            "config": CrawlerRunConfig(
                word_count_threshold=50,  # Theodore's setting
                css_selector="main, article, .content",  # Theodore's setting
                excluded_tags=["script", "style"],
                cache_mode=CacheMode.ENABLED,
                wait_until="domcontentloaded",
                page_timeout=30000,
                verbose=False
            )
        },
        {
            "name": "Optimized Config for Dynamic Sites",
            "config": CrawlerRunConfig(
                word_count_threshold=10,  # More permissive
                css_selector="body",  # Broader selector
                excluded_tags=["script", "style", "nav", "footer"],
                cache_mode=CacheMode.ENABLED,
                wait_until="domcontentloaded", 
                page_timeout=30000,
                verbose=False
            )
        }
    ]
    
    print("🔍 Configuration Comparison for Huawei")
    print("=" * 60)
    
    for config_test in configs:
        print(f"\n📋 Testing: {config_test['name']}")
        print("-" * 50)
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=False
        ) as crawler:
            
            try:
                results = await crawler.arun_many(test_urls, config=config_test['config'])
                
                successful = 0
                total_content = 0
                
                for i, result in enumerate(results):
                    url = test_urls[i]
                    print(f"   [{i+1}] {url}")
                    
                    if result.success:
                        content = None
                        content_source = None
                        
                        if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                            content = result.cleaned_html
                            content_source = "cleaned_html"
                        elif hasattr(result, 'markdown') and result.markdown and len(str(result.markdown).strip()) > 50:
                            content = str(result.markdown)
                            content_source = "markdown"
                        
                        if content:
                            successful += 1
                            total_content += len(content)
                            
                            # Check for meaningful Huawei content
                            meaningful_keywords = ["huawei", "technology", "company", "business", "founded", "innovation"]
                            meaningful_count = sum(1 for word in meaningful_keywords 
                                                 if word.lower() in content.lower())
                            
                            print(f"       ✅ Success: {len(content):,} chars from {content_source}")
                            print(f"       🎯 Meaningful keywords: {meaningful_count}/{len(meaningful_keywords)}")
                            
                            if meaningful_count >= 3:
                                # Show a snippet of actual content
                                content_lower = content.lower()
                                for keyword in ["about huawei", "huawei technologies", "company"]:
                                    if keyword in content_lower:
                                        start_idx = content_lower.find(keyword)
                                        snippet = content[max(0, start_idx-20):start_idx+150]
                                        snippet_clean = snippet.replace('\n', ' ').replace('<', '').replace('>', '').strip()
                                        print(f"       📝 Sample: ...{snippet_clean}...")
                                        break
                        else:
                            print(f"       ⚠️ Success but no usable content")
                    else:
                        print(f"       ❌ Failed")
                
                print(f"\n   📊 Summary: {successful}/{len(test_urls)} pages, {total_content:,} total chars")
                
            except Exception as e:
                print(f"   ❌ Configuration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_config_comparison())
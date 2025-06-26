#!/usr/bin/env python3
"""
Advanced test for Huawei with JavaScript execution and delayed loading
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode

async def test_huawei_advanced():
    """Test Huawei with advanced JavaScript handling"""
    
    print("🔬 Advanced Huawei Testing - JavaScript & Dynamic Content")
    print("=" * 70)
    
    test_url = "https://www.huawei.com/en/about-huawei"
    
    # Test different JavaScript execution strategies
    configs = [
        {
            "name": "Standard JS Execution",
            "config": CrawlerRunConfig(
                word_count_threshold=10,
                wait_until="domcontentloaded",
                page_timeout=30000,
                verbose=True
            )
        },
        {
            "name": "Extended JS Wait",
            "config": CrawlerRunConfig(
                word_count_threshold=10,
                wait_until="networkidle",
                page_timeout=45000,
                delay_before_return_html=3000,  # Wait 3 seconds for JS
                verbose=True
            )
        },
        {
            "name": "Full Page Load",
            "config": CrawlerRunConfig(
                word_count_threshold=5,
                wait_until="load",
                page_timeout=60000,
                delay_before_return_html=5000,  # Wait 5 seconds for JS
                css_selector="body",  # Get everything
                verbose=True
            )
        }
    ]
    
    for test_config in configs:
        print(f"\n🧪 Testing: {test_config['name']}")
        print("-" * 50)
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=True
        ) as crawler:
            
            start_time = time.time()
            
            try:
                result = await crawler.arun(url=test_url, config=test_config['config'])
                duration = time.time() - start_time
                
                if result.success:
                    print(f"   ✅ Success in {duration:.2f}s")
                    
                    # Analyze content quality
                    if result.cleaned_html:
                        content = result.cleaned_html
                        content_length = len(content)
                        
                        # Check for meaningful content indicators
                        meaningful_indicators = [
                            "huawei", "technology", "company", "about", "founded",
                            "business", "products", "services", "vision", "mission"
                        ]
                        
                        meaningful_count = sum(1 for word in meaningful_indicators 
                                             if word.lower() in content.lower())
                        
                        print(f"   📏 Content length: {content_length:,} chars")
                        print(f"   🎯 Meaningful indicators: {meaningful_count}/{len(meaningful_indicators)}")
                        
                        # Check content quality ratio
                        cookie_content = content.lower().count("cookie")
                        navigation_content = content.lower().count("navigation") + content.lower().count("menu")
                        actual_content_ratio = (content_length - (cookie_content + navigation_content) * 50) / content_length
                        
                        print(f"   📊 Estimated content quality: {actual_content_ratio:.1%}")
                        
                        # Show sample of meaningful content (skip cookie banners)
                        lines = content.split('\n')
                        meaningful_lines = []
                        for line in lines:
                            line_clean = line.strip()
                            if (len(line_clean) > 30 and 
                                'cookie' not in line_clean.lower() and
                                'javascript' not in line_clean.lower() and
                                any(indicator in line_clean.lower() for indicator in meaningful_indicators)):
                                meaningful_lines.append(line_clean)
                                if len(meaningful_lines) >= 3:
                                    break
                        
                        if meaningful_lines:
                            print(f"   📝 Sample meaningful content:")
                            for i, line in enumerate(meaningful_lines[:2]):
                                print(f"      {i+1}. {line[:100]}...")
                        else:
                            print(f"   ⚠️ No meaningful content found beyond navigation/cookies")
                            # Show raw sample anyway
                            sample = content[:500].replace('\n', ' ').strip()
                            print(f"   📄 Raw sample: {sample}...")
                            
                else:
                    print(f"   ❌ Failed in {duration:.2f}s")
                    print(f"   💬 Error: {getattr(result, 'error_message', 'Unknown error')}")
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"   ❌ Exception in {duration:.2f}s: {e}")
    
    # Test specific Huawei pages that might have better content
    alternative_urls = [
        "https://www.huawei.com/en/about-huawei/company-overview", 
        "https://carrier.huawei.com/en/about/company-overview",
        "https://e.huawei.com/en/about-huawei"
    ]
    
    print(f"\n🌐 Testing alternative Huawei URLs")
    print("-" * 50)
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False
    ) as crawler:
        
        config = CrawlerRunConfig(
            word_count_threshold=10,
            wait_until="networkidle",
            page_timeout=30000,
            delay_before_return_html=2000,
            verbose=False
        )
        
        for url in alternative_urls:
            try:
                print(f"📄 Testing: {url}")
                start_time = time.time()
                result = await crawler.arun(url=url, config=config)
                duration = time.time() - start_time
                
                if result.success and result.cleaned_html:
                    content_length = len(result.cleaned_html)
                    
                    # Quick meaningful content check
                    meaningful_keywords = ["huawei", "company", "technology", "business", "founded"]
                    meaningful_count = sum(1 for word in meaningful_keywords 
                                         if word.lower() in result.cleaned_html.lower())
                    
                    if meaningful_count >= 3 and content_length > 1000:
                        print(f"   ✅ Good content: {content_length:,} chars, {meaningful_count} keywords")
                        
                        # Extract a meaningful snippet
                        content = result.cleaned_html.lower()
                        for keyword in ["about huawei", "company overview", "founded"]:
                            if keyword in content:
                                start_idx = content.find(keyword)
                                snippet = result.cleaned_html[max(0, start_idx-50):start_idx+200]
                                snippet_clean = snippet.replace('\n', ' ').strip()
                                print(f"   📝 Found: ...{snippet_clean}...")
                                break
                    else:
                        print(f"   ⚠️ Limited content: {content_length:,} chars, {meaningful_count} keywords")
                else:
                    print(f"   ❌ Failed or no content in {duration:.2f}s")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_huawei_advanced())
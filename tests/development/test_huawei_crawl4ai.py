#!/usr/bin/env python3
"""
Test Crawl4AI specifically on huawei.com to diagnose extraction issues
"""

import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode

async def test_huawei_crawling():
    """Test different crawling strategies on Huawei.com"""
    
    base_url = "https://www.huawei.com"
    test_urls = [
        "https://www.huawei.com",
        "https://www.huawei.com/en/about-huawei",
        "https://consumer.huawei.com/en",
        "https://www.huawei.com/en/contact-us",
        "https://www.huawei.com/en/sustainability"
    ]
    
    print("🧪 Testing Crawl4AI on Huawei.com")
    print("=" * 60)
    
    # Test 1: Basic crawling with different configurations
    configs_to_test = [
        {
            "name": "Basic Configuration",
            "config": CrawlerRunConfig(
                word_count_threshold=20,
                verbose=True
            )
        },
        {
            "name": "Aggressive Configuration", 
            "config": CrawlerRunConfig(
                word_count_threshold=10,
                css_selector="body",
                excluded_tags=["script", "style"],
                verbose=True,
                page_timeout=45000,
                wait_until="networkidle"
            )
        },
        {
            "name": "Minimal Configuration",
            "config": CrawlerRunConfig(
                word_count_threshold=5,
                verbose=True,
                page_timeout=60000
            )
        }
    ]
    
    for config_test in configs_to_test:
        print(f"\n🔧 Testing: {config_test['name']}")
        print("-" * 40)
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=True
        ) as crawler:
            
            start_time = time.time()
            
            try:
                # Test single URL first
                print(f"📄 Testing single URL: {base_url}")
                result = await crawler.arun(url=base_url, config=config_test['config'])
                
                duration = time.time() - start_time
                
                if result.success:
                    content_sources = []
                    content_lengths = []
                    
                    # Check all available content types
                    if result.cleaned_html:
                        content_sources.append("cleaned_html")
                        content_lengths.append(len(result.cleaned_html))
                    
                    if hasattr(result, 'markdown') and result.markdown:
                        content_sources.append("markdown") 
                        content_lengths.append(len(str(result.markdown)))
                    
                    if hasattr(result, 'extracted_content') and result.extracted_content:
                        content_sources.append("extracted_content")
                        content_lengths.append(len(result.extracted_content))
                    
                    if hasattr(result, 'fit_markdown') and result.fit_markdown:
                        content_sources.append("fit_markdown")
                        content_lengths.append(len(result.fit_markdown))
                        
                    print(f"   ✅ Success in {duration:.2f}s")
                    print(f"   📊 Available content: {content_sources}")
                    print(f"   📏 Content lengths: {content_lengths}")
                    
                    # Show sample content
                    if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                        sample = result.cleaned_html[:300].replace('\n', ' ').strip()
                        print(f"   📝 Sample content: {sample}...")
                    elif hasattr(result, 'markdown') and result.markdown:
                        sample = str(result.markdown)[:300].replace('\n', ' ').strip()
                        print(f"   📝 Sample markdown: {sample}...")
                    else:
                        print(f"   ⚠️ No usable content found")
                        
                else:
                    print(f"   ❌ Failed in {duration:.2f}s")
                    print(f"   💬 Error: {getattr(result, 'error_message', 'Unknown error')}")
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"   ❌ Exception in {duration:.2f}s: {e}")
    
    # Test 2: Batch processing
    print(f"\n🚀 Testing batch processing on multiple URLs")
    print("-" * 40)
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium", 
        verbose=True
    ) as crawler:
        
        config = CrawlerRunConfig(
            word_count_threshold=10,
            verbose=True,
            page_timeout=30000
        )
        
        start_time = time.time()
        
        try:
            print(f"📄 Testing {len(test_urls)} URLs with arun_many...")
            results = await crawler.arun_many(test_urls, config=config)
            
            duration = time.time() - start_time
            
            print(f"🏁 Batch processing completed in {duration:.2f}s")
            print(f"📊 Results breakdown:")
            
            for i, result in enumerate(results):
                url = test_urls[i]
                print(f"   [{i+1}] {url}")
                
                if result.success:
                    # Check content availability
                    content_found = False
                    best_content = None
                    content_source = None
                    
                    if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                        best_content = result.cleaned_html[:200]
                        content_source = "cleaned_html"
                        content_found = True
                    elif hasattr(result, 'markdown') and result.markdown and len(str(result.markdown).strip()) > 50:
                        best_content = str(result.markdown)[:200]
                        content_source = "markdown"
                        content_found = True
                    elif hasattr(result, 'extracted_content') and result.extracted_content and len(result.extracted_content.strip()) > 50:
                        best_content = result.extracted_content[:200]
                        content_source = "extracted_content"
                        content_found = True
                    
                    if content_found:
                        print(f"       ✅ Success: {len(best_content)} chars from {content_source}")
                        sample = best_content.replace('\n', ' ').strip()
                        print(f"       📝 Sample: {sample}...")
                    else:
                        print(f"       ⚠️ Success but no usable content")
                        
                else:
                    print(f"       ❌ Failed: {getattr(result, 'error_message', 'Unknown error')}")
                    
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Batch processing failed in {duration:.2f}s: {e}")

    # Test 3: SSL/Security Analysis
    print(f"\n🔒 Testing SSL and security aspects")
    print("-" * 40)
    
    import ssl
    import socket
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(base_url)
        hostname = parsed.hostname
        port = parsed.port or 443
        
        print(f"🔍 Checking SSL certificate for {hostname}:{port}")
        
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                print(f"   ✅ SSL certificate valid")
                print(f"   📋 Subject: {cert.get('subject', 'Unknown')}")
                print(f"   🏢 Issuer: {cert.get('issuer', 'Unknown')}")
                
    except Exception as e:
        print(f"   ⚠️ SSL check failed: {e}")
    
    print(f"\n✅ Huawei crawling analysis complete")

if __name__ == "__main__":
    asyncio.run(test_huawei_crawling())
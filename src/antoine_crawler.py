#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page Content Crawler with Trafilatura
=====================================

Crawls LLM-selected valuable pages and extracts clean, human-readable text content
using Trafilatura - a highly-accurate boilerplate remover & text extractor.

This tool takes the paths selected by Nova Pro LLM and extracts clean, unique
content from each page using Trafilatura's advanced content extraction, then
combines everything into a comprehensive text summary.

Usage:
    # Async usage
    content = await crawl_selected_pages(base_url, selected_paths)
    
    # Sync usage
    content = crawl_selected_pages_sync(base_url, selected_paths)
    
    # Test with DigitalRemedy
    python3 crawler.py
"""

import asyncio
import logging
import os
import sys
import time
from typing import List
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("⚠️ No .env file found, using system environment variables")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")

# Import Trafilatura for superior content extraction
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
    print("✅ Trafilatura imported successfully")
except ImportError:
    print("❌ Trafilatura not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'trafilatura'])
    import trafilatura
    TRAFILATURA_AVAILABLE = True
    print("✅ Trafilatura installed and imported successfully")

logger = logging.getLogger(__name__)


@dataclass
class PageCrawlResult:
    """Result from crawling a single page"""
    url: str
    success: bool
    content: str = ""
    title: str = ""
    content_length: int = 0
    crawl_time: float = 0.0
    extraction_method: str = ""  # "trafilatura" or "beautifulsoup_fallback"
    error: str = ""


@dataclass
class BatchCrawlResult:
    """Result from crawling multiple pages"""
    base_url: str
    total_pages: int
    successful_pages: int
    failed_pages: int
    total_content_length: int
    total_crawl_time: float
    aggregated_content: str = ""
    page_results: List[PageCrawlResult] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.page_results is None:
            self.page_results = []
        if self.errors is None:
            self.errors = []


async def crawl_single_page(
    url: str,
    base_url: str,
    timeout_seconds: int = 30,
    max_content_length: int = 10000
) -> PageCrawlResult:
    """
    Crawl a single page and extract clean text content using Trafilatura.
    
    Uses Trafilatura's superior boilerplate removal and content extraction
    to get clean, unique content from each page without navigation/header/footer.
    
    Args:
        url: Full URL to crawl
        base_url: Base website URL for context
        timeout_seconds: Timeout for page crawling
        max_content_length: Maximum content length to extract
        
    Returns:
        PageCrawlResult with extracted content or error details
    """
    if not TRAFILATURA_AVAILABLE:
        return PageCrawlResult(
            url=url,
            success=False,
            error="Trafilatura not available",
            extraction_method="unavailable"
        )
    
    print(f"🔍 [{url}] Starting Trafilatura extraction...")
    start_time = time.time()
    
    try:
        # Configure realistic browser headers to bypass anti-bot protection
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        
        # Create Trafilatura config with enhanced settings
        trafilatura_config = trafilatura.settings.use_config()
        trafilatura_config.set('DEFAULT', 'USER_AGENTS', user_agent)
        trafilatura_config.set('DEFAULT', 'TIMEOUT', '30')
        
        # Download the page content with realistic browser user agent
        downloaded = trafilatura.fetch_url(url, config=trafilatura_config)
        
        if not downloaded:
            crawl_time = time.time() - start_time
            
            # Check if this might be a 403 error (anti-bot protection)
            # and try Crawl4AI fallback for protected sites
            print(f"⚠️  [{url}] Trafilatura failed to download, trying Crawl4AI fallback...")
            
            try:
                # Import Crawl4AI for protected sites
                from crawl4ai import AsyncWebCrawler
                
                async with AsyncWebCrawler(verbose=False) as crawler:
                    crawl4ai_result = await crawler.arun(url=url)
                    
                    if crawl4ai_result.success and crawl4ai_result.cleaned_html:
                        # Extract content from Crawl4AI result
                        crawl4ai_content = crawl4ai_result.cleaned_html
                        if len(crawl4ai_content) > 200:  # Reasonable content found
                            crawl_time = time.time() - start_time
                            print(f"✅ [{url}] Crawl4AI fallback successful ({len(crawl4ai_content)} chars)")
                            
                            return PageCrawlResult(
                                url=url,
                                success=True,
                                content=crawl4ai_content[:max_content_length],
                                content_length=len(crawl4ai_content),
                                crawl_time=crawl_time,
                                extraction_method="crawl4ai_fallback"
                            )
                            
            except Exception as crawl4ai_error:
                print(f"❌ [{url}] Crawl4AI fallback also failed: {crawl4ai_error}")
            
            # Both methods failed
            return PageCrawlResult(
                url=url,
                success=False,
                crawl_time=crawl_time,
                error="Failed to download page content (both Trafilatura and Crawl4AI failed)",
                extraction_method="all_methods_failed"
            )
        
        # Extract clean content using Trafilatura (removes boilerplate by default)
        content = trafilatura.extract(downloaded)
        trafilatura_content = content.strip() if content else ""
        trafilatura_length = len(trafilatura_content)
        
        # Fallback to BeautifulSoup if Trafilatura extraction is insufficient
        final_content = trafilatura_content
        extraction_method = "trafilatura"
        
        if trafilatura_length < 500:  # Less than 500 characters triggers fallback
            print(f"⚠️  [{url}] Trafilatura extracted only {trafilatura_length} chars, trying BeautifulSoup fallback...")
            
            try:
                from bs4 import BeautifulSoup
                import re
                
                soup = BeautifulSoup(downloaded, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Try multiple extraction strategies
                beautifulsoup_content = ""
                
                # Strategy 1: Look for main content containers
                main_selectors = [
                    'main', '[role="main"]', '.main-content', '.content', 
                    '.page-content', '.services-content', '.container'
                ]
                
                for selector in main_selectors:
                    elements = soup.select(selector)
                    if elements:
                        for element in elements:
                            text = element.get_text(separator=' ', strip=True)
                            if len(text) > len(beautifulsoup_content):
                                beautifulsoup_content = text
                
                # Strategy 2: Service-specific sections (for service/product pages)
                if len(beautifulsoup_content) < 500:
                    service_selectors = [
                        '[class*="service"]', '[class*="offering"]', '[class*="solution"]',
                        '[class*="product"]', 'section', '.section'
                    ]
                    
                    service_content = []
                    for selector in service_selectors:
                        elements = soup.select(selector)
                        for element in elements:
                            text = element.get_text(separator=' ', strip=True)
                            if len(text) > 50:  # Include meaningful service descriptions
                                service_content.append(text)
                    
                    if service_content:
                        beautifulsoup_content = ' '.join(service_content)
                
                # Strategy 3: Fallback to body text with cleanup
                if len(beautifulsoup_content) < 200:
                    beautifulsoup_content = soup.get_text(separator=' ', strip=True)
                
                # Clean up extra whitespace
                beautifulsoup_content = re.sub(r'\s+', ' ', beautifulsoup_content).strip()
                beautifulsoup_length = len(beautifulsoup_content)
                
                # Compare results and keep the better one
                if beautifulsoup_length > trafilatura_length * 1.5:  # BeautifulSoup is significantly better
                    final_content = beautifulsoup_content
                    extraction_method = "beautifulsoup_fallback"
                    print(f"✅ [{url}] BeautifulSoup fallback successful: {beautifulsoup_length} chars vs {trafilatura_length} chars")
                else:
                    final_content = trafilatura_content if trafilatura_content else beautifulsoup_content
                    extraction_method = "trafilatura" if trafilatura_content else "beautifulsoup_fallback"
                    print(f"🔄 [{url}] Keeping Trafilatura result: {trafilatura_length} chars vs {beautifulsoup_length} chars")
                    
            except Exception as e:
                print(f"⚠️  [{url}] BeautifulSoup fallback failed: {e}")
                final_content = trafilatura_content
                extraction_method = "trafilatura"
        
        if not final_content:
            crawl_time = time.time() - start_time
            return PageCrawlResult(
                url=url,
                success=False,
                crawl_time=crawl_time,
                error="No content extracted from page",
                extraction_method="no_content"
            )
        
        # Clean and limit content
        if len(final_content) > max_content_length:
            final_content = final_content[:max_content_length] + "... [TRUNCATED]"
        
        # Try to extract title using Trafilatura's metadata extraction
        title = ""
        try:
            metadata = trafilatura.extract_metadata(downloaded)
            if metadata and hasattr(metadata, 'title') and metadata.title:
                title = metadata.title
        except:
            # Fallback: try basic extraction
            try:
                title = trafilatura.extract(downloaded, include_tables=False, include_links=False, 
                                          output_format='xml')
                if title and '<title>' in title:
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', title)
                    title = title_match.group(1) if title_match else ""
                else:
                    title = ""
            except:
                title = ""
        
        crawl_time = time.time() - start_time
        
        print(f"✅ [{url}] Extracted successfully ({len(final_content)} chars, {crawl_time:.2f}s) via {extraction_method}")
        
        return PageCrawlResult(
            url=url,
            success=True,
            content=final_content,
            title=title,
            content_length=len(final_content),
            crawl_time=crawl_time,
            extraction_method=extraction_method
        )
        
    except Exception as e:
        crawl_time = time.time() - start_time
        return PageCrawlResult(
            url=url,
            success=False,
            crawl_time=crawl_time,
            error=f"Trafilatura extraction failed: {str(e)}",
            extraction_method="extraction_failed"
        )


# Note: Content extraction is now handled directly by Trafilatura in crawl_single_page()
# No additional content cleaning functions needed - Trafilatura handles boilerplate removal


async def crawl_selected_pages(
    base_url: str,
    selected_paths: List[str],
    timeout_seconds: int = 30,
    max_content_per_page: int = 10000,
    max_concurrent: int = 5
) -> BatchCrawlResult:
    """
    Crawl multiple pages concurrently and aggregate content.
    
    Args:
        base_url: Base website URL
        selected_paths: List of paths to crawl (from LLM selection)
        timeout_seconds: Timeout per page
        max_content_per_page: Maximum content per page
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        BatchCrawlResult with aggregated content and individual page results
    """
    if not TRAFILATURA_AVAILABLE:
        return BatchCrawlResult(
            base_url=base_url,
            total_pages=len(selected_paths),
            successful_pages=0,
            failed_pages=len(selected_paths),
            total_content_length=0,
            total_crawl_time=0.0,
            errors=["Trafilatura not available"]
        )
    
    print(f"🌐 Crawling {len(selected_paths)} pages from {base_url}")
    print(f"⚡ Max concurrent: {max_concurrent}, timeout: {timeout_seconds}s")
    
    start_time = time.time()
    
    # Convert paths to full URLs
    full_urls = []
    for path in selected_paths:
        if path.startswith(('http://', 'https://')):
            full_urls.append(path)
        else:
            full_urls.append(urljoin(base_url, path))
    
    # Create semaphore for concurrent limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def crawl_with_semaphore(url: str) -> PageCrawlResult:
        async with semaphore:
            # Add small delay to avoid triggering anti-bot protection
            await asyncio.sleep(0.5)  # 500ms delay between requests
            return await crawl_single_page(
                url, base_url, timeout_seconds, max_content_per_page
            )
    
    # Crawl all pages concurrently
    page_results = await asyncio.gather(
        *[crawl_with_semaphore(url) for url in full_urls],
        return_exceptions=True
    )
    
    # Process results
    successful_results = []
    failed_results = []
    errors = []
    
    for i, result in enumerate(page_results):
        if isinstance(result, Exception):
            failed_result = PageCrawlResult(
                url=full_urls[i],
                success=False,
                error=f"Exception: {str(result)}",
                extraction_method="exception"
            )
            failed_results.append(failed_result)
            errors.append(f"{full_urls[i]}: {str(result)}")
        elif result.success:
            successful_results.append(result)
        else:
            failed_results.append(result)
            errors.append(f"{result.url}: {result.error}")
    
    # Aggregate content from successful pages
    aggregated_content = _aggregate_page_content(successful_results, base_url)
    
    total_crawl_time = time.time() - start_time
    total_content_length = sum(r.content_length for r in successful_results)
    
    result = BatchCrawlResult(
        base_url=base_url,
        total_pages=len(selected_paths),
        successful_pages=len(successful_results),
        failed_pages=len(failed_results),
        total_content_length=total_content_length,
        total_crawl_time=total_crawl_time,
        aggregated_content=aggregated_content,
        page_results=successful_results + failed_results,
        errors=errors
    )
    
    print(f"✅ Batch crawl completed in {total_crawl_time:.2f}s")
    print(f"   Successful: {result.successful_pages}/{result.total_pages}")
    print(f"   Total content: {result.total_content_length:,} characters")
    print(f"   Failed: {result.failed_pages} pages")
    
    return result


def _aggregate_page_content(successful_results: List[PageCrawlResult], base_url: str) -> str:
    """
    Aggregate content from multiple pages into a comprehensive text summary.
    
    Args:
        successful_results: List of successful page crawl results
        base_url: Base website URL for context
        
    Returns:
        Aggregated content text optimized for company intelligence analysis
    """
    if not successful_results:
        return ""
    
    # Parse domain for header
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc
    
    # Start with header
    content_blocks = [
        f"COMPANY WEBSITE CONTENT ANALYSIS",
        f"Website: {domain}",
        f"Content extracted from {len(successful_results)} pages",
        f"Total content length: {sum(r.content_length for r in successful_results):,} characters",
        "="*60,
        ""
    ]
    
    # Sort pages by URL for consistent ordering
    sorted_results = sorted(successful_results, key=lambda r: r.url)
    
    # Add content from each page
    for i, page_result in enumerate(sorted_results, 1):
        # Page header
        content_blocks.extend([
            f"PAGE {i}: {page_result.url}",
            f"Title: {page_result.title or 'No title'}",
            f"Content length: {page_result.content_length:,} characters",
            "-" * 40,
            ""
        ])
        
        # Page content
        if page_result.content:
            content_blocks.append(page_result.content)
        else:
            content_blocks.append("[No content extracted]")
        
        content_blocks.extend(["", ""])  # Double spacing between pages
    
    # Add footer summary
    content_blocks.extend([
        "="*60,
        "CONTENT AGGREGATION SUMMARY",
        f"Total pages processed: {len(successful_results)}",
        f"Average content per page: {sum(r.content_length for r in successful_results) // len(successful_results):,} characters",
        f"URLs processed:",
    ])
    
    for result in sorted_results:
        content_blocks.append(f"  - {result.url}")
    
    return "\n".join(content_blocks)


def crawl_selected_pages_sync(
    base_url: str,
    selected_paths: List[str],
    timeout_seconds: int = 30,
    max_content_per_page: int = 10000,
    max_concurrent: int = 5
) -> BatchCrawlResult:
    """
    Synchronous wrapper for crawl_selected_pages().
    
    Args:
        base_url: Base website URL
        selected_paths: List of paths to crawl
        timeout_seconds: Timeout per page
        max_content_per_page: Maximum content per page
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        BatchCrawlResult with aggregated content
    """
    try:
        return asyncio.run(crawl_selected_pages(
            base_url, selected_paths, timeout_seconds, 
            max_content_per_page, max_concurrent
        ))
    except Exception as e:
        logger.error(f"Error in sync wrapper for {base_url}: {e}")
        return BatchCrawlResult(
            base_url=base_url,
            total_pages=len(selected_paths),
            successful_pages=0,
            failed_pages=len(selected_paths),
            total_content_length=0,
            total_crawl_time=0.0,
            errors=[f"Sync wrapper error: {e}"]
        )


async def test_digitalremedy_crawling():
    """Test Trafilatura-based page crawling with DigitalRemedy.com example"""
    
    print("🧪 Testing Trafilatura-Based Page Crawling with DigitalRemedy.com")
    print("="*60)
    
    # Test with a few key pages that should have unique content
    test_paths = [
        "/about",
        "/contact-us", 
        "/careers",
        "/capabilities"
    ]
    
    base_url = "https://www.digitalremedy.com"
    
    print(f"🔍 Testing {len(test_paths)} pages from {base_url}")
    print(f"🎯 Using Trafilatura for superior content extraction")
    
    # Crawl pages
    result = await crawl_selected_pages(
        base_url=base_url,
        selected_paths=test_paths,
        timeout_seconds=30,
        max_content_per_page=5000,  # Reasonable limit for testing
        max_concurrent=3
    )
    
    print(f"\n📊 Crawl Results:")
    print(f"   Successful: {result.successful_pages}/{result.total_pages}")
    print(f"   Total content: {result.total_content_length:,} characters")
    print(f"   Crawl time: {result.total_crawl_time:.2f}s")
    print(f"   Avg per page: {result.total_crawl_time/result.total_pages:.2f}s")
    
    if result.errors:
        print(f"   Errors: {len(result.errors)}")
        for error in result.errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
    
    # Content uniqueness check
    successful_results = [r for r in result.page_results if r.success]
    if len(successful_results) >= 2:
        print(f"\n🔬 Content Uniqueness Check:")
        page1_words = set(successful_results[0].content.lower().split()[:50])
        page2_words = set(successful_results[1].content.lower().split()[:50])
        overlap = len(page1_words & page2_words)
        similarity = overlap / min(len(page1_words), len(page2_words)) if page1_words and page2_words else 0
        print(f"   Similarity between pages 1&2: {similarity:.1%} overlap")
        if similarity < 0.3:
            print(f"   ✅ EXCELLENT: Pages have unique content!")
        elif similarity < 0.5:
            print(f"   🟡 GOOD: Some unique content per page")
        else:
            print(f"   ❌ POOR: Pages still too similar")
    
    # Show sample content from each page
    print(f"\n📄 Content Previews:")
    for i, page_result in enumerate(successful_results, 1):
        page_name = page_result.url.split('/')[-1] or 'home'
        preview = page_result.content[:150] + "..." if len(page_result.content) > 150 else page_result.content
        print(f"   {i}. {page_name} ({page_result.content_length:,} chars): {preview}")
    
    # Save results to file
    test_dir = "test"
    os.makedirs(test_dir, exist_ok=True)
    
    output_file = os.path.join(test_dir, "trafilatura_crawler_results.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("DIGITALREMEDY.COM TRAFILATURA CRAWLER RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        # Overall metrics
        f.write("📊 CRAWL METRICS:\n")
        f.write(f"Extraction Method: Trafilatura (Superior Boilerplate Removal)\n")
        f.write(f"Base URL: {result.base_url}\n")
        f.write(f"Total Pages Processed: {result.total_pages}\n")
        f.write(f"Successful Crawls: {result.successful_pages}\n")
        f.write(f"Failed Crawls: {result.failed_pages}\n")
        f.write(f"Total Processing Time: {result.total_crawl_time:.2f} seconds\n")
        f.write(f"Average Time Per Page: {result.total_crawl_time/result.total_pages:.2f} seconds\n")
        f.write(f"Total Content Length: {result.total_content_length:,} characters\n\n")
        
        # Content uniqueness analysis
        if len(successful_results) >= 2:
            page1_words = set(successful_results[0].content.lower().split()[:50])
            page2_words = set(successful_results[1].content.lower().split()[:50])
            overlap = len(page1_words & page2_words)
            similarity = overlap / min(len(page1_words), len(page2_words)) if page1_words and page2_words else 0
            f.write("🔬 CONTENT UNIQUENESS ANALYSIS:\n")
            f.write(f"Similarity between first two pages: {similarity:.1%} overlap\n")
            f.write(f"Assessment: {'EXCELLENT - Unique content' if similarity < 0.3 else 'GOOD - Some unique content' if similarity < 0.5 else 'POOR - Too similar'}\n\n")
        
        # Individual page results
        f.write("📄 INDIVIDUAL PAGE RESULTS:\n")
        f.write("=" * 60 + "\n\n")
        
        for i, page_result in enumerate(result.page_results, 1):
            page_name = page_result.url.split('/')[-1] or 'home'
            f.write(f"PAGE {i}: {page_name.upper()}\n")
            f.write(f"URL: {page_result.url}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Success: {'✅' if page_result.success else '❌'}\n")
            f.write(f"Title: {page_result.title or 'No title'}\n")
            f.write(f"Content Length: {page_result.content_length:,} characters\n")
            f.write(f"Extraction Time: {page_result.crawl_time:.2f} seconds\n")
            
            if page_result.error:
                f.write(f"Error: {page_result.error}\n")
            
            if page_result.content:
                f.write(f"\nExtracted Content (Trafilatura):\n")
                f.write("-" * 40 + "\n")
                f.write(f"{page_result.content}\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
        
        # Full aggregated content
        f.write("📄 FULL AGGREGATED CONTENT:\n")
        f.write("=" * 60 + "\n\n")
        f.write(result.aggregated_content)
        f.write("\n\nEND OF TRAFILATURA CRAWLER REPORT\n")
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print(f"📁 File size: {os.path.getsize(output_file):,} bytes")
    
    return result




if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if not TRAFILATURA_AVAILABLE:
        print("❌ Cannot run tests - Trafilatura not available")
        exit(1)
    
    # Run Trafilatura-based text extraction test
    asyncio.run(test_digitalremedy_crawling())
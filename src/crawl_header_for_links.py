#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Header/Footer Link Extraction Tool
===================================

Extracts navigation links from website headers, footers, and menu sections using 
the proven Crawl4AI approach from Theodore's intelligent scraper.

This tool uses the exact same configuration that Theodore uses for navigation 
link discovery, including JavaScript menu expansion and anti-bot detection.

Usage:
    # Async usage
    links = await extract_header_footer_links("https://example.com")
    
    # Sync usage
    links = extract_header_footer_links_sync("https://example.com")
    
    # Test multiple sites
    python3 crawl_header_for_links.py
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("⚠️ No .env file found, using system environment variables")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")

# Theodore imports for proven Crawl4AI configuration
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.async_configs import CacheMode
    from src.ssl_config import get_browser_args, should_verify_ssl
    CRAWL4AI_AVAILABLE = True
    print("✅ Crawl4AI and Theodore SSL config imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Theodore/Crawl4AI dependencies: {e}")
    CRAWL4AI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Theodore's proven browser user agent for compatibility
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"


async def extract_header_footer_links(url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract navigation links from website headers, footers, and menus using Crawl4AI.
    
    This function uses Theodore's proven Crawl4AI configuration for reliable 
    link extraction from modern websites with JavaScript navigation.
    
    Args:
        url: The website URL to extract links from
        
    Returns:
        Dictionary categorizing links by navigation section:
        {
            "header_links": [{"url": "...", "text": "...", "section": "header"}],
            "nav_links": [{"url": "...", "text": "...", "section": "nav"}], 
            "footer_links": [{"url": "...", "text": "...", "section": "footer"}],
            "menu_links": [{"url": "...", "text": "...", "section": "menu"}],
            "all_links": [{"url": "...", "text": "...", "section": "..."}]
        }
    """
    if not CRAWL4AI_AVAILABLE:
        raise ImportError("Crawl4AI or Theodore dependencies not available")
    
    print(f"🔍 Extracting header/footer links from: {url}")
    
    # Parse domain for filtering
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # Initialize result structure
    result = {
        "header_links": [],
        "nav_links": [],
        "footer_links": [], 
        "menu_links": [],
        "all_links": []
    }
    
    try:
        # Theodore's proven Crawl4AI configuration
        browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium", 
            verbose=False,
            browser_args=browser_args
        ) as crawler:
            
            # Exact Theodore configuration for navigation link discovery
            config = CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                word_count_threshold=1,  # Very low threshold for link discovery
                css_selector="a[href], nav, footer, .menu, .navigation",  # Focus on navigation elements
                excluded_tags=["script", "style"],
                cache_mode=CacheMode.ENABLED,
                page_timeout=15000,  # 15 second timeout
                verbose=False,
                simulate_user=True,      # Anti-bot bypass
                magic=True,              # Enhanced compatibility
                js_code=[
                    # JavaScript to reveal hidden navigation (from Theodore)
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
            
            print(f"🌐 Crawling with Crawl4AI...")
            crawl_result = await crawler.arun(url=url, config=config)
            
            if crawl_result and crawl_result.html:
                print(f"✅ Successfully crawled page ({len(crawl_result.html)} chars)")
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(crawl_result.html, 'html.parser')
                
                # Extract links by navigation section
                result = _categorize_navigation_links(soup, url, domain)
                
                print(f"📊 Extraction summary:")
                print(f"   Header links: {len(result['header_links'])}")
                print(f"   Nav links: {len(result['nav_links'])}")
                print(f"   Footer links: {len(result['footer_links'])}")
                print(f"   Menu links: {len(result['menu_links'])}")
                print(f"   Total unique links: {len(result['all_links'])}")
                
            else:
                print(f"❌ Failed to crawl page: success={getattr(crawl_result, 'success', False)}")
                
    except Exception as e:
        logger.error(f"Error extracting links from {url}: {e}")
        print(f"❌ Error: {e}")
    
    return result


def _categorize_navigation_links(soup: BeautifulSoup, base_url: str, domain: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Categorize extracted links by their navigation section.
    
    Args:
        soup: BeautifulSoup parsed HTML
        base_url: Base URL for link normalization
        domain: Domain for filtering internal links
        
    Returns:
        Categorized links dictionary
    """
    result = {
        "header_links": [],
        "nav_links": [],
        "footer_links": [],
        "menu_links": [],
        "all_links": []
    }
    
    seen_urls = set()  # Deduplicate links
    
    # Define navigation sections with their CSS selectors
    navigation_sections = {
        "header": ["header", "header nav", ".header", ".site-header", ".page-header"],
        "nav": ["nav", ".navbar", ".navigation", ".main-nav", ".primary-nav"],
        "footer": ["footer", "footer nav", ".footer", ".site-footer", ".page-footer"],
        "menu": [".menu", ".menu-item", ".nav-menu", ".dropdown-menu", ".mobile-menu"]
    }
    
    # Extract links from each navigation section
    for section_name, selectors in navigation_sections.items():
        for selector in selectors:
            elements = soup.select(selector)
            
            for element in elements:
                # Find all links within this navigation element
                links = element.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '').strip()
                    if not href:
                        continue
                        
                    # Normalize URL
                    full_url = urljoin(base_url, href)
                    
                    # Skip non-HTTP URLs and external links
                    parsed_link = urlparse(full_url)
                    if (not parsed_link.scheme.startswith('http') or 
                        parsed_link.netloc != domain):
                        continue
                    
                    # Skip if already seen
                    if full_url in seen_urls:
                        continue
                    
                    seen_urls.add(full_url)
                    
                    # Extract link text
                    link_text = link.get_text(strip=True)
                    if not link_text:
                        # Use title or aria-label as fallback
                        link_text = (link.get('title', '') or 
                                   link.get('aria-label', '') or 
                                   'No text')
                    
                    # Create link object
                    link_obj = {
                        "url": full_url,
                        "text": link_text,
                        "section": section_name,
                        "selector": selector
                    }
                    
                    # Add to section-specific list
                    result[f"{section_name}_links"].append(link_obj)
                    
                    # Add to all links list
                    result["all_links"].append(link_obj)
    
    # Remove duplicates from all_links while preserving order
    seen_in_all = set()
    unique_all_links = []
    for link in result["all_links"]:
        if link["url"] not in seen_in_all:
            seen_in_all.add(link["url"])
            unique_all_links.append(link)
    
    result["all_links"] = unique_all_links
    
    return result


def strip_domains_from_links(links_result: Dict[str, List[Dict[str, str]]], base_url: str) -> Dict[str, List[str]]:
    """
    Remove domains from extracted links to get clean path-only URLs.
    
    Args:
        links_result: Result from extract_header_footer_links()
        base_url: Base URL to strip from links
        
    Returns:
        Dictionary with same structure but containing path-only URLs:
        {
            "header_paths": ["/about", "/contact"],
            "nav_paths": ["/products", "/services"], 
            "footer_paths": ["/privacy", "/terms"],
            "menu_paths": ["/support"],
            "all_paths": ["/about", "/contact", "/products", ...]
        }
    """
    from urllib.parse import urlparse
    
    # Parse the base URL to get domain info
    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc
    
    def extract_path(url: str) -> str:
        """Extract clean path from URL, removing domain if it matches base domain."""
        try:
            parsed = urlparse(url)
            
            # If it's the same domain, return just the path
            if parsed.netloc == base_domain:
                path = parsed.path
                # Ensure path starts with / and remove trailing /
                if not path.startswith('/'):
                    path = '/' + path
                if path != '/' and path.endswith('/'):
                    path = path.rstrip('/')
                return path if path != '/' else '/'
            else:
                # Different domain, return full URL
                return url
                
        except Exception:
            # If parsing fails, return original URL
            return url
    
    # Process each section
    result = {
        "header_paths": [],
        "nav_paths": [],
        "footer_paths": [],
        "menu_paths": [],
        "all_paths": []
    }
    
    # Map section names
    section_mapping = {
        "header_links": "header_paths",
        "nav_links": "nav_paths", 
        "footer_links": "footer_paths",
        "menu_links": "menu_paths"
    }
    
    # Extract paths from each section
    for section_key, path_key in section_mapping.items():
        section_links = links_result.get(section_key, [])
        paths = []
        
        for link in section_links:
            url = link.get("url", "")
            if url:
                path = extract_path(url)
                if path not in paths:  # Avoid duplicates within section
                    paths.append(path)
        
        result[path_key] = paths
    
    # Create combined all_paths list (deduplicated)
    all_paths = []
    seen_paths = set()
    
    for section_paths in [result["header_paths"], result["nav_paths"], 
                         result["footer_paths"], result["menu_paths"]]:
        for path in section_paths:
            if path not in seen_paths:
                seen_paths.add(path)
                all_paths.append(path)
    
    result["all_paths"] = all_paths
    
    return result


def extract_header_footer_links_sync(url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Synchronous wrapper for extract_header_footer_links().
    
    Args:
        url: The website URL to extract links from
        
    Returns:
        Dictionary categorizing links by navigation section
    """
    try:
        return asyncio.run(extract_header_footer_links(url))
    except Exception as e:
        logger.error(f"Error in sync wrapper for {url}: {e}")
        return {
            "header_links": [],
            "nav_links": [],
            "footer_links": [],
            "menu_links": [],
            "all_links": [],
            "error": str(e)
        }


async def analyze_navigation_structure(url: str) -> Dict[str, any]:
    """
    Analyze the navigation structure of a website in detail.
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Detailed analysis of navigation structure
    """
    print(f"\n🔍 Analyzing navigation structure: {url}")
    print("="*60)
    
    links = await extract_header_footer_links(url)
    
    analysis = {
        "url": url,
        "total_navigation_links": len(links["all_links"]),
        "sections": {
            "header": len(links["header_links"]),
            "nav": len(links["nav_links"]), 
            "footer": len(links["footer_links"]),
            "menu": len(links["menu_links"])
        },
        "unique_destinations": len(set(link["url"] for link in links["all_links"])),
        "sample_links": {}
    }
    
    # Show sample links from each section
    for section in ["header_links", "nav_links", "footer_links", "menu_links"]:
        section_name = section.replace("_links", "")
        sample_links = links[section][:3]  # First 3 links
        analysis["sample_links"][section_name] = [
            {"text": link["text"], "url": link["url"]} 
            for link in sample_links
        ]
    
    # Print analysis
    print(f"📊 Navigation Analysis:")
    print(f"   Total navigation links: {analysis['total_navigation_links']}")
    print(f"   Header links: {analysis['sections']['header']}")
    print(f"   Nav links: {analysis['sections']['nav']}")
    print(f"   Footer links: {analysis['sections']['footer']}")
    print(f"   Menu links: {analysis['sections']['menu']}")
    print(f"   Unique destinations: {analysis['unique_destinations']}")
    
    for section, sample_links in analysis["sample_links"].items():
        if sample_links:
            print(f"\n📋 Sample {section} links:")
            for i, link in enumerate(sample_links, 1):
                print(f"   {i}. {link['text']} → {link['url']}")
    
    return analysis


async def test_multiple_websites():
    """Test the link extraction on multiple websites."""
    test_sites = [
        "https://www.microsoft.com",
        "https://www.google.com", 
        "https://www.apple.com",
        "https://www.roland.com"
    ]
    
    print("🧪 Testing Header/Footer Link Extraction")
    print("="*60)
    
    for site in test_sites:
        try:
            await analyze_navigation_structure(site)
            await asyncio.sleep(2)  # Brief delay between tests
        except Exception as e:
            print(f"❌ Failed to test {site}: {e}")
    
    print("\n✅ Testing completed!")


async def demo_path_extraction():
    """Demo the new path extraction functionality."""
    print("\n🔗 Testing Path Extraction Feature")
    print("="*50)
    
    # Test with Roland.com
    url = "https://www.roland.com"
    print(f"🎵 Extracting paths from {url}...")
    
    # Get full links
    links_result = await extract_header_footer_links(url)
    
    # Strip domains to get clean paths
    paths_result = strip_domains_from_links(links_result, url)
    
    print(f"\n📊 Path Extraction Results:")
    print(f"   Total paths: {len(paths_result['all_paths'])}")
    print(f"   Nav paths: {len(paths_result['nav_paths'])}")
    print(f"   Footer paths: {len(paths_result['footer_paths'])}")
    
    # Show sample paths
    print(f"\n📋 Sample navigation paths:")
    for i, path in enumerate(paths_result['nav_paths'][:10], 1):
        print(f"   {i}. {path}")
    
    if paths_result['footer_paths']:
        print(f"\n📋 Footer paths:")
        for i, path in enumerate(paths_result['footer_paths'], 1):
            print(f"   {i}. {path}")
    
    print(f"\n🔗 All unique paths ({len(paths_result['all_paths'])}):")
    for i, path in enumerate(paths_result['all_paths'], 1):
        print(f"   {i:2d}. {path}")
    
    return paths_result


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if not CRAWL4AI_AVAILABLE:
        print("❌ Cannot run tests - Crawl4AI dependencies not available")
        sys.exit(1)
    
    async def main():
        # Run standard tests
        await test_multiple_websites()
        
        # Demo new path extraction feature
        await demo_path_extraction()
    
    # Run tests
    asyncio.run(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critter - Comprehensive Website Discovery Tool
==============================================

Combines multiple discovery methods to create a unified, deduplicated array of website paths.
This tool aggregates results from:
1. Header/Footer Link Extraction (navigation discovery)
2. Sitemap.xml Parsing (content structure discovery)  
3. Robots.txt Analysis (crawling rules and restrictions)

The result is a comprehensive understanding of website structure and accessible paths.

Usage:
    # Async usage
    result = await discover_all_paths("https://example.com")
    
    # Sync usage
    result = discover_all_paths_sync("https://example.com")
    
    # Test multiple sites
    python3 critter.py
"""

import asyncio
import logging
import os
import time
import requests
from typing import Dict, List, Set
from urllib.parse import urlparse

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print("Warning: No .env file found, using system environment variables")
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables")

# Import our custom crawlers
try:
    from crawl_header_for_links import extract_header_footer_links, strip_domains_from_links
    from crawl_sitemap_xml import extract_sitemap_paths
    from crawl_robots_txt import extract_robots_paths
    CRAWLERS_AVAILABLE = True
    print("All crawler modules imported successfully")
except ImportError as e:
    print(f"Warning: Failed to import crawler modules: {e}")
    CRAWLERS_AVAILABLE = False

logger = logging.getLogger(__name__)


def normalize_domain_url(url: str) -> str:
    """
    Normalize URL to handle www/non-www domain variants.
    
    This function determines the canonical domain by testing which variant
    (www or non-www) the website actually uses and returns the correct URL.
    
    Args:
        url: Input URL (may have www or not)
        
    Returns:
        Normalized URL with the correct domain variant
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # If domain already has www, try both variants
    # If domain doesn't have www, try both variants
    
    variants = []
    if domain.startswith('www.'):
        # Try both www and non-www
        non_www_domain = domain[4:]  # Remove 'www.'
        variants = [
            f"{parsed.scheme}://{domain}{parsed.path}",  # Original with www
            f"{parsed.scheme}://{non_www_domain}{parsed.path}"  # Without www
        ]
    else:
        # Try both non-www and www
        www_domain = f"www.{domain}"
        variants = [
            f"{parsed.scheme}://{domain}{parsed.path}",  # Original without www
            f"{parsed.scheme}://{www_domain}{parsed.path}"  # With www
        ]
    
    # Test which variant actually works by checking HTTP response
    for variant in variants:
        try:
            # Quick HEAD request to see which domain responds
            response = requests.head(variant, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                # Use the final URL after redirects
                final_url = response.url
                print(f"🔄 Domain normalized: {url} → {final_url}")
                return final_url
        except:
            continue
    
    # If neither variant works, return original
    print(f"⚠️  Could not normalize domain for {url}, using original")
    return url


class WebsiteDiscoveryResult:
    """Comprehensive website discovery results."""
    
    def __init__(self, url: str):
        self.url = url
        self.discovery_time = 0.0
        
        # Individual crawler results
        self.header_footer_results = {}
        self.sitemap_results = []
        self.robots_results = {}
        
        # Aggregated results
        self.all_paths = []
        self.unique_path_count = 0
        
        # Path categorization
        self.navigation_paths = []      # From header/footer
        self.content_paths = []         # From sitemaps
        self.restricted_paths = []      # Disallowed in robots.txt
        self.allowed_paths = []         # Explicitly allowed in robots.txt
        self.sitemap_references = []    # Sitemap URLs from robots.txt
        
        # Discovery method tracking
        self.path_sources = {}          # {path: [source1, source2]}
        
        # Errors and warnings
        self.errors = []
        self.warnings = []
    
    def __repr__(self):
        return f"WebsiteDiscoveryResult(url='{self.url}', unique_paths={self.unique_path_count}, time={self.discovery_time:.2f}s)"


async def discover_all_paths(
    base_url: str, 
    locale_filter: str = None,
    user_agent_filter: str = "*",
    timeout_seconds: int = 60
) -> WebsiteDiscoveryResult:
    """
    Discover all website paths using multiple methods and return deduplicated results.
    
    Args:
        base_url: Website URL to analyze
        locale_filter: Optional locale filter for sitemap (e.g., 'en-us')
        user_agent_filter: User agent filter for robots.txt (default: '*')
        timeout_seconds: Timeout for overall discovery process
        
    Returns:
        WebsiteDiscoveryResult with comprehensive path discovery
    """
    if not CRAWLERS_AVAILABLE:
        raise ImportError("Crawler modules not available")
    
    # Normalize domain to handle www/non-www variants
    normalized_url = normalize_domain_url(base_url)
    
    print(f"🔍 Starting comprehensive website discovery: {normalized_url}")
    if locale_filter:
        print(f"   Locale filter: {locale_filter}")
    if user_agent_filter != "*":
        print(f"   User agent filter: {user_agent_filter}")
    
    start_time = time.time()
    result = WebsiteDiscoveryResult(normalized_url)
    
    try:
        # Run all discovery methods concurrently with timeout using normalized URL
        discovery_tasks = [
            _discover_header_footer_paths(normalized_url),
            _discover_sitemap_paths(normalized_url, locale_filter),
            _discover_robots_paths(normalized_url, user_agent_filter)
        ]
        
        # Execute with timeout
        completed_results = await asyncio.wait_for(
            asyncio.gather(*discovery_tasks, return_exceptions=True),
            timeout=timeout_seconds
        )
        
        # Process results
        header_footer_result, sitemap_result, robots_result = completed_results
        
        # Store individual results
        if isinstance(header_footer_result, Exception):
            result.errors.append(f"Header/footer discovery failed: {header_footer_result}")
            result.header_footer_results = {}
        else:
            result.header_footer_results = header_footer_result
        
        if isinstance(sitemap_result, Exception):
            result.errors.append(f"Sitemap discovery failed: {sitemap_result}")
            result.sitemap_results = []
        else:
            result.sitemap_results = sitemap_result
        
        if isinstance(robots_result, Exception):
            result.errors.append(f"Robots.txt discovery failed: {robots_result}")
            result.robots_results = {}
        else:
            result.robots_results = robots_result
        
        # Aggregate and deduplicate paths
        _aggregate_and_deduplicate_paths(result)
        
        result.discovery_time = time.time() - start_time
        
        print(f"✅ Discovery completed in {result.discovery_time:.2f}s")
        print(f"   Total unique paths: {result.unique_path_count}")
        print(f"   Navigation paths: {len(result.navigation_paths)}")
        print(f"   Content paths: {len(result.content_paths)}")
        print(f"   Restricted paths: {len(result.restricted_paths)}")
        print(f"   Errors: {len(result.errors)}")
        
    except asyncio.TimeoutError:
        result.errors.append(f"Discovery timed out after {timeout_seconds} seconds")
        result.discovery_time = time.time() - start_time
        print(f"⏰ Discovery timed out after {timeout_seconds}s")
    
    except Exception as e:
        result.errors.append(f"Discovery failed: {e}")
        result.discovery_time = time.time() - start_time
        print(f"❌ Discovery failed: {e}")
    
    return result


async def _discover_header_footer_paths(base_url: str) -> Dict:
    """Discover paths from header/footer navigation."""
    print("🔗 Discovering header/footer navigation paths...")
    
    try:
        # Extract header/footer links
        links_result = await extract_header_footer_links(base_url)
        
        # Strip domains to get clean paths
        paths_result = strip_domains_from_links(links_result, base_url)
        
        return {
            "raw_links": links_result,
            "clean_paths": paths_result,
            "method": "header_footer"
        }
    
    except Exception as e:
        logger.error(f"Header/footer discovery failed for {base_url}: {e}")
        raise


async def _discover_sitemap_paths(base_url: str, locale_filter: str = None) -> List[str]:
    """Discover paths from sitemap.xml."""
    print("🗺️ Discovering sitemap content paths...")
    
    try:
        paths = await extract_sitemap_paths(base_url, locale_filter)
        return paths
    
    except Exception as e:
        logger.error(f"Sitemap discovery failed for {base_url}: {e}")
        raise


async def _discover_robots_paths(base_url: str, user_agent_filter: str = "*") -> Dict:
    """Discover paths from robots.txt."""
    print("🤖 Discovering robots.txt rules and paths...")
    
    try:
        paths = await extract_robots_paths(base_url, user_agent_filter)
        return paths
    
    except Exception as e:
        logger.error(f"Robots.txt discovery failed for {base_url}: {e}")
        raise


def _aggregate_and_deduplicate_paths(result: WebsiteDiscoveryResult) -> None:
    """Aggregate paths from all sources and deduplicate."""
    
    all_paths_set: Set[str] = set()
    path_sources = {}
    
    # Process header/footer paths
    if result.header_footer_results and "clean_paths" in result.header_footer_results:
        header_paths = result.header_footer_results["clean_paths"]
        
        for path_type, paths in header_paths.items():
            if path_type == "all_paths":
                continue  # Skip the aggregated list
            
            for path in paths:
                all_paths_set.add(path)
                if path not in path_sources:
                    path_sources[path] = []
                path_sources[path].append(f"navigation_{path_type}")
                
                # Categorize as navigation paths
                if path not in result.navigation_paths:
                    result.navigation_paths.append(path)
    
    # Process sitemap paths  
    if result.sitemap_results:
        for path in result.sitemap_results:
            all_paths_set.add(path)
            if path not in path_sources:
                path_sources[path] = []
            path_sources[path].append("sitemap")
            
            # Categorize as content paths
            if path not in result.content_paths:
                result.content_paths.append(path)
    
    # Process robots.txt paths
    if result.robots_results:
        # Allowed paths
        for path in result.robots_results.get("allowed_paths", []):
            all_paths_set.add(path)
            if path not in path_sources:
                path_sources[path] = []
            path_sources[path].append("robots_allowed")
            
            if path not in result.allowed_paths:
                result.allowed_paths.append(path)
        
        # Disallowed paths  
        for path in result.robots_results.get("disallowed_paths", []):
            all_paths_set.add(path)
            if path not in path_sources:
                path_sources[path] = []
            path_sources[path].append("robots_disallowed")
            
            if path not in result.restricted_paths:
                result.restricted_paths.append(path)
        
        # Sitemap references
        for path in result.robots_results.get("sitemap_paths", []):
            all_paths_set.add(path)
            if path not in path_sources:
                path_sources[path] = []
            path_sources[path].append("robots_sitemap")
            
            if path not in result.sitemap_references:
                result.sitemap_references.append(path)
    
    # Create final deduplicated list
    result.all_paths = sorted(list(all_paths_set))
    result.unique_path_count = len(result.all_paths)
    result.path_sources = path_sources


def discover_all_paths_sync(
    base_url: str,
    locale_filter: str = None,
    user_agent_filter: str = "*",
    timeout_seconds: int = 60
) -> WebsiteDiscoveryResult:
    """
    Synchronous wrapper for discover_all_paths().
    
    Args:
        base_url: Website URL to analyze
        locale_filter: Optional locale filter for sitemap (e.g., 'en-us')
        user_agent_filter: User agent filter for robots.txt (default: '*')
        timeout_seconds: Timeout for overall discovery process
        
    Returns:
        WebsiteDiscoveryResult with comprehensive path discovery
    """
    try:
        return asyncio.run(discover_all_paths(base_url, locale_filter, user_agent_filter, timeout_seconds))
    except Exception as e:
        # Use normalized URL for error case too
        normalized_url = normalize_domain_url(base_url) if base_url else base_url
        logger.error(f"Error in sync wrapper for {normalized_url}: {e}")
        result = WebsiteDiscoveryResult(normalized_url)
        result.errors.append(f"Sync wrapper error: {e}")
        return result


async def analyze_website_comprehensively(url: str, **kwargs) -> Dict:
    """
    Perform comprehensive website analysis and return detailed insights.
    
    Args:
        url: Website URL to analyze
        **kwargs: Additional arguments for discover_all_paths()
        
    Returns:
        Detailed analysis dictionary
    """
    print(f"\n🔍 Comprehensive Website Analysis: {url}")
    print("="*60)
    
    # Discover all paths
    result = await discover_all_paths(url, **kwargs)
    
    # Analyze the results
    analysis = {
        "url": url,
        "discovery_time": result.discovery_time,
        "total_unique_paths": result.unique_path_count,
        "discovery_success": len(result.errors) == 0,
        
        # Path counts by category
        "path_counts": {
            "navigation": len(result.navigation_paths),
            "content": len(result.content_paths), 
            "restricted": len(result.restricted_paths),
            "allowed": len(result.allowed_paths),
            "sitemap_refs": len(result.sitemap_references)
        },
        
        # Discovery method effectiveness
        "discovery_methods": {
            "header_footer_success": bool(result.header_footer_results),
            "sitemap_success": bool(result.sitemap_results),
            "robots_success": bool(result.robots_results)
        },
        
        # Path overlap analysis
        "path_sources": result.path_sources,
        "multi_source_paths": [
            path for path, sources in result.path_sources.items() 
            if len(sources) > 1
        ],
        
        # Website characteristics
        "characteristics": _analyze_website_characteristics(result),
        
        # Sample paths
        "sample_paths": {
            "navigation": result.navigation_paths[:5],
            "content": result.content_paths[:5],
            "restricted": result.restricted_paths[:5]
        },
        
        "errors": result.errors,
        "warnings": result.warnings
    }
    
    # Print analysis summary
    print(f"📊 Analysis Summary:")
    print(f"   Discovery time: {analysis['discovery_time']:.2f}s")
    print(f"   Total unique paths: {analysis['total_unique_paths']}")
    print(f"   Navigation paths: {analysis['path_counts']['navigation']}")
    print(f"   Content paths: {analysis['path_counts']['content']}")
    print(f"   Restricted paths: {analysis['path_counts']['restricted']}")
    print(f"   Multi-source paths: {len(analysis['multi_source_paths'])}")
    print(f"   Discovery success: {'✅' if analysis['discovery_success'] else '❌'}")
    
    if analysis['characteristics']:
        print(f"\n🏗️ Website characteristics:")
        for char, value in analysis['characteristics'].items():
            print(f"   {char}: {value}")
    
    return analysis


def _analyze_website_characteristics(result: WebsiteDiscoveryResult) -> Dict[str, str]:
    """Analyze website characteristics based on discovered paths."""
    
    characteristics = {}
    
    # Analyze structure complexity
    total_paths = result.unique_path_count
    if total_paths > 100:
        characteristics["structure_complexity"] = "High"
    elif total_paths > 30:
        characteristics["structure_complexity"] = "Medium"
    else:
        characteristics["structure_complexity"] = "Low"
    
    # Analyze restriction level
    restricted_ratio = len(result.restricted_paths) / max(total_paths, 1)
    if restricted_ratio > 0.5:
        characteristics["access_restriction"] = "Highly Restricted"
    elif restricted_ratio > 0.2:
        characteristics["access_restriction"] = "Moderately Restricted"
    else:
        characteristics["access_restriction"] = "Open"
    
    # Analyze content organization
    if result.sitemap_references:
        characteristics["content_organization"] = "Structured (has sitemaps)"
    elif len(result.content_paths) > 20:
        characteristics["content_organization"] = "Large Content Base"
    else:
        characteristics["content_organization"] = "Simple Structure"
    
    # Analyze navigation quality
    nav_ratio = len(result.navigation_paths) / max(total_paths, 1)
    if nav_ratio > 0.3:
        characteristics["navigation_quality"] = "Rich Navigation"
    elif nav_ratio > 0.1:
        characteristics["navigation_quality"] = "Standard Navigation"
    else:
        characteristics["navigation_quality"] = "Minimal Navigation"
    
    return characteristics


async def test_comprehensive_discovery():
    """Test comprehensive discovery on multiple websites."""
    test_sites = [
        ("https://www.apple.com", {"locale_filter": "en-us", "timeout_seconds": 30}),
        ("https://www.microsoft.com", {"locale_filter": "en-us", "timeout_seconds": 30}),
        ("https://www.roland.com", {}),
        ("https://www.google.com", {})
    ]
    
    print("🧪 Testing Comprehensive Website Discovery")
    print("="*60)
    
    for site, kwargs in test_sites:
        try:
            print(f"\n🔍 Testing: {site}")
            print("-" * 40)
            
            analysis = await analyze_website_comprehensively(site, **kwargs)
            
            print(f"✅ Success: {analysis['total_unique_paths']} unique paths discovered")
            
            # Show path source diversity
            methods = analysis['discovery_methods']
            working_methods = [k for k, v in methods.items() if v]
            print(f"   Working methods: {', '.join(working_methods)}")
            
            if analysis['multi_source_paths']:
                print(f"   Multi-source paths (first 3): {', '.join(analysis['multi_source_paths'][:3])}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        await asyncio.sleep(2)  # Brief delay between tests
    
    print("\n✅ Comprehensive discovery testing completed!")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if not CRAWLERS_AVAILABLE:
        print("❌ Cannot run tests - Crawler modules not available")
        exit(1)
    
    # Run comprehensive tests
    asyncio.run(test_comprehensive_discovery())
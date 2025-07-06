#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sitemap XML Crawler Tool
========================

Extracts all URLs from website sitemap.xml files and outputs clean path-only URLs
without domains. Handles both regular sitemaps and sitemap index files.

Usage:
    # Async usage
    paths = await extract_sitemap_paths("https://example.com")
    
    # Sync usage  
    paths = extract_sitemap_paths_sync("https://example.com")
    
    # Test multiple sites
    python3 crawl_sitemap_xml.py
"""

import asyncio
import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Dict, List
from urllib.parse import urljoin, urlparse
import aiohttp

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

logger = logging.getLogger(__name__)

# Standard user agent for compatibility
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"


def _should_include_url(url: str, locale_filter: str = None) -> bool:
    """Check if a URL should be included based on locale filtering."""
    if not locale_filter:
        return True
    
    # Normalize locale filter
    locale_filter = locale_filter.lower()
    url_lower = url.lower()
    
    # Check for locale patterns in URL
    locale_patterns = [
        f"/{locale_filter}/",
        f".{locale_filter}/",
        f"_{locale_filter}.",
        f"-{locale_filter}.",
        f"sitemap_{locale_filter}.",
        f"sitemap-{locale_filter}.",
        f"/{locale_filter}.",  # e.g., /en-us.xml
    ]
    
    # Special case: if no locale pattern found, include root domain URLs (often default to en-us)
    has_any_locale_pattern = any(
        pattern in url_lower for pattern in [
            "/en-", "/fr-", "/de-", "/es-", "/it-", "/ja-", "/ko-", "/zh-", "/pt-", "/ru-",
            "/nl-", "/sv-", "/da-", "/fi-", "/no-", "/pl-", "/cs-", "/hu-", "/tr-", "/ar-",
            ".en-", ".fr-", ".de-", ".es-", ".it-", ".ja-", ".ko-", ".zh-", ".pt-", ".ru-",
            "_en_", "_fr_", "_de_", "_es_", "_it_", "_ja_", "_ko_", "_zh_", "_pt_", "_ru_"
        ]
    )
    
    # Additional check: if filtering for en-us and URL contains other locales, exclude it first
    if locale_filter in ['en-us', 'en_us']:
        other_locale_patterns = [
            'fr-fr', 'de-de', 'es-es', 'it-it', 'ja-jp', 'ko-kr', 'zh-cn', 'zh-tw', 'pt-br', 'ru-ru',
            'nl-nl', 'sv-se', 'da-dk', 'fi-fi', 'no-no', 'pl-pl', 'cs-cz', 'hu-hu', 'tr-tr', 'ar-sa'
        ]
        for other_locale in other_locale_patterns:
            if other_locale in url_lower:
                return False
    
    # If URL contains target locale, include it
    for pattern in locale_patterns:
        if pattern in url_lower:
            return True
    
    # If URL has no locale pattern (likely default/root), include it when filtering for en-us
    if not has_any_locale_pattern and locale_filter in ['en-us', 'en_us']:
        return True
    
    return False


class SitemapEntry:
    """Represents a single URL entry from a sitemap."""
    
    def __init__(self, url: str, lastmod: str = None, changefreq: str = None, priority: str = None):
        self.url = url
        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority
    
    def __repr__(self):
        return f"SitemapEntry(url='{self.url}', lastmod='{self.lastmod}')"


async def extract_sitemap_urls(base_url: str, locale_filter: str = None) -> List[SitemapEntry]:
    """
    Extract all URLs from website sitemap.xml files.
    
    Args:
        base_url: The website URL to extract sitemap from
        locale_filter: Optional locale filter (e.g., 'en-us') to only process URLs from specific locale
        
    Returns:
        List of SitemapEntry objects containing URL and metadata
    """
    print(f"Extracting sitemap URLs from: {base_url}")
    if locale_filter:
        print(f"Filtering for locale: {locale_filter}")
    
    # Parse domain for filtering
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc
    
    discovered_entries = []
    processed_sitemaps = set()  # Avoid processing same sitemap twice
    
    try:
        # Step 1: Try to find sitemap.xml
        sitemap_urls = await _discover_sitemap_urls(base_url)
        
        if not sitemap_urls:
            print("Warning: No sitemap.xml found")
            return []
        
        print(f"Found {len(sitemap_urls)} sitemap file(s)")
        
        # Step 2: Process each sitemap file (with locale filtering)
        for sitemap_url in sitemap_urls:
            if sitemap_url not in processed_sitemaps:
                # Apply locale filtering to sitemap URLs
                if not _should_include_url(sitemap_url, locale_filter):
                    print(f"Skipping {sitemap_url} (locale filter: {locale_filter})")
                    continue
                
                processed_sitemaps.add(sitemap_url)
                entries = await _parse_sitemap_file(sitemap_url, domain, locale_filter)
                discovered_entries.extend(entries)
                print(f"Processed {sitemap_url}: {len(entries)} URLs")
        
        print(f"Total sitemap URLs extracted: {len(discovered_entries)}")
        
    except Exception as e:
        logger.error(f"Error extracting sitemap from {base_url}: {e}")
        print(f"Error: {e}")
    
    return discovered_entries


async def _discover_sitemap_urls(base_url: str) -> List[str]:
    """Discover sitemap URLs from robots.txt and common locations."""
    
    sitemap_urls = []
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": USER_AGENT}
        ) as session:
            
            # Method 1: Check robots.txt for sitemap references
            robots_url = urljoin(base_url, '/robots.txt')
            try:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        for line in robots_content.split('\n'):
                            line = line.strip()
                            if line.lower().startswith('sitemap:'):
                                sitemap_url = line.split(':', 1)[1].strip()
                                sitemap_urls.append(sitemap_url)
                        
                        if sitemap_urls:
                            print(f"Found {len(sitemap_urls)} sitemap(s) in robots.txt")
            except Exception as e:
                logger.debug(f"Failed to check robots.txt: {e}")
            
            # Method 2: Try common sitemap locations if none found in robots.txt
            if not sitemap_urls:
                common_locations = [
                    '/sitemap.xml',
                    '/sitemap_index.xml',
                    '/sitemaps/sitemap.xml',
                    '/sitemap/sitemap.xml'
                ]
                
                for location in common_locations:
                    sitemap_url = urljoin(base_url, location)
                    try:
                        async with session.get(sitemap_url) as response:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')
                                if 'xml' in content_type.lower():
                                    sitemap_urls.append(sitemap_url)
                                    print(f"Found sitemap at: {location}")
                                    break
                    except Exception:
                        continue
    
    except Exception as e:
        logger.error(f"Failed to discover sitemaps: {e}")
    
    return sitemap_urls


async def _parse_sitemap_file(sitemap_url: str, domain: str, locale_filter: str = None) -> List[SitemapEntry]:
    """Parse a single sitemap XML file and extract URLs."""
    
    entries = []
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": USER_AGENT}
        ) as session:
            
            async with session.get(sitemap_url) as response:
                if response.status != 200:
                    print(f"Warning: Failed to fetch {sitemap_url}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                
                try:
                    root = ET.fromstring(content)
                    
                    # Handle sitemap index files (contain references to other sitemaps)
                    if _is_sitemap_index(root):
                        print(f"Processing sitemap index: {sitemap_url}")
                        nested_entries = await _parse_sitemap_index(root, domain, locale_filter)
                        entries.extend(nested_entries)
                    
                    # Handle regular sitemap files (contain actual URLs)
                    else:
                        print(f"Processing sitemap: {sitemap_url}")
                        entries = _parse_sitemap_urls(root, domain, locale_filter)
                
                except ET.ParseError as e:
                    print(f"Error: Failed to parse XML from {sitemap_url}: {e}")
                    
                    # Try to parse as plain text sitemap (fallback)
                    entries = _parse_plain_text_sitemap(content, domain)
    
    except Exception as e:
        logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
    
    return entries


def _is_sitemap_index(root: ET.Element) -> bool:
    """Check if XML root is a sitemap index file."""
    return (root.tag.endswith('sitemapindex') or 
            any(child.tag.endswith('sitemap') for child in root))


async def _parse_sitemap_index(root: ET.Element, domain: str, locale_filter: str = None) -> List[SitemapEntry]:
    """Parse sitemap index file and recursively process nested sitemaps."""
    
    entries = []
    
    # Define XML namespaces
    namespaces = {
        '': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    }
    
    # Find all sitemap references
    sitemap_refs = []
    
    # Try both with and without namespace
    for ns_prefix in ['', 'ns:']:
        sitemap_elements = root.findall(f'.//{ns_prefix}sitemap', namespaces if ns_prefix else {})
        for sitemap_elem in sitemap_elements:
            loc_elem = sitemap_elem.find(f'{ns_prefix}loc', namespaces if ns_prefix else {})
            if loc_elem is not None and loc_elem.text:
                sitemap_refs.append(loc_elem.text)
    
    print(f"Found {len(sitemap_refs)} nested sitemap(s)")
    
    # Process each nested sitemap (with locale filtering)
    for sitemap_ref in sitemap_refs:
        # Apply locale filtering to nested sitemap URLs
        if not _should_include_url(sitemap_ref, locale_filter):
            print(f"Skipping nested sitemap {sitemap_ref} (locale filter: {locale_filter})")
            continue
            
        nested_entries = await _parse_sitemap_file(sitemap_ref, domain, locale_filter)
        entries.extend(nested_entries)
    
    return entries


def _parse_sitemap_urls(root: ET.Element, domain: str, locale_filter: str = None) -> List[SitemapEntry]:
    """Parse regular sitemap file and extract URL entries."""
    
    entries = []
    
    # Find all URL entries with namespace handling
    url_elements = []
    
    # Try different namespace patterns
    patterns = [
        './/url',
        './/{http://www.sitemaps.org/schemas/sitemap/0.9}url'
    ]
    
    for pattern in patterns:
        url_elements = root.findall(pattern)
        if url_elements:
            break
    
    for url_elem in url_elements:
        # Extract URL and metadata with namespace handling
        loc_elem = (url_elem.find('loc') or 
                   url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'))
        lastmod_elem = (url_elem.find('lastmod') or 
                       url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod'))
        changefreq_elem = (url_elem.find('changefreq') or 
                          url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq'))
        priority_elem = (url_elem.find('priority') or 
                        url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority'))
        
        if loc_elem is not None and loc_elem.text:
            url = loc_elem.text.strip()
            
            # Only include URLs from the same domain and matching locale filter
            parsed_url = urlparse(url)
            if parsed_url.netloc == domain and _should_include_url(url, locale_filter):
                entry = SitemapEntry(
                    url=url,
                    lastmod=lastmod_elem.text.strip() if lastmod_elem is not None and lastmod_elem.text else None,
                    changefreq=changefreq_elem.text.strip() if changefreq_elem is not None and changefreq_elem.text else None,
                    priority=priority_elem.text.strip() if priority_elem is not None and priority_elem.text else None
                )
                entries.append(entry)
    
    return entries


def _parse_plain_text_sitemap(content: str, domain: str) -> List[SitemapEntry]:
    """Parse plain text sitemap as fallback (one URL per line)."""
    
    entries = []
    
    for line in content.split('\n'):
        line = line.strip()
        if line and line.startswith('http'):
            parsed_url = urlparse(line)
            if parsed_url.netloc == domain:
                entries.append(SitemapEntry(url=line))
    
    return entries


def strip_domains_from_sitemap(sitemap_entries: List[SitemapEntry], base_url: str) -> List[str]:
    """
    Remove domains from sitemap URLs to get clean path-only URLs.
    
    Args:
        sitemap_entries: List of SitemapEntry objects
        base_url: Base URL to strip from entries
        
    Returns:
        List of path-only URLs (e.g., ["/products", "/about", "/contact"])
    """
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
    
    # Extract paths and deduplicate
    paths = []
    seen_paths = set()
    
    for entry in sitemap_entries:
        path = extract_path(entry.url)
        if path not in seen_paths:
            seen_paths.add(path)
            paths.append(path)
    
    return paths


async def extract_sitemap_paths(base_url: str, locale_filter: str = None) -> List[str]:
    """
    Extract all sitemap URLs and return as domain-free paths.
    
    Args:
        base_url: Website URL to extract sitemap from
        locale_filter: Optional locale filter (e.g., 'en-us') to only process URLs from specific locale
        
    Returns:
        List of path-only URLs without domains
    """
    # Get full sitemap entries (with locale filtering)
    sitemap_entries = await extract_sitemap_urls(base_url, locale_filter)
    
    # Strip domains to get clean paths
    paths = strip_domains_from_sitemap(sitemap_entries, base_url)
    
    return paths


def extract_sitemap_paths_sync(base_url: str, locale_filter: str = None) -> List[str]:
    """
    Synchronous wrapper for extract_sitemap_paths().
    
    Args:
        base_url: Website URL to extract sitemap from
        locale_filter: Optional locale filter (e.g., 'en-us') to only process URLs from specific locale
        
    Returns:
        List of path-only URLs without domains
    """
    try:
        return asyncio.run(extract_sitemap_paths(base_url, locale_filter))
    except Exception as e:
        logger.error(f"Error in sync wrapper for {base_url}: {e}")
        return []


async def analyze_sitemap_structure(url: str) -> Dict[str, any]:
    """
    Analyze the sitemap structure of a website in detail.
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Detailed analysis of sitemap structure
    """
    print(f"\nAnalyzing sitemap structure: {url}")
    print("="*60)
    
    start_time = time.time()
    
    # Extract sitemap entries
    sitemap_entries = await extract_sitemap_urls(url)
    
    # Get clean paths
    paths = strip_domains_from_sitemap(sitemap_entries, url)
    
    extraction_time = time.time() - start_time
    
    analysis = {
        "url": url,
        "total_sitemap_urls": len(sitemap_entries),
        "unique_paths": len(paths),
        "extraction_time": extraction_time,
        "has_sitemap": len(sitemap_entries) > 0,
        "sample_paths": paths[:10],  # First 10 paths
        "path_patterns": _analyze_path_patterns(paths)
    }
    
    # Print analysis
    print(f"Sitemap Analysis:")
    print(f"   Total URLs in sitemap: {analysis['total_sitemap_urls']}")
    print(f"   Unique paths: {analysis['unique_paths']}")
    print(f"   Extraction time: {analysis['extraction_time']:.2f}s")
    print(f"   Has sitemap: {'Yes' if analysis['has_sitemap'] else 'No'}")
    
    if analysis['sample_paths']:
        print(f"\nSample paths:")
        for i, path in enumerate(analysis['sample_paths'], 1):
            print(f"   {i}. {path}")
    
    if analysis['path_patterns']:
        print(f"\nPath patterns:")
        for pattern, count in analysis['path_patterns'].items():
            print(f"   {pattern}: {count} paths")
    
    return analysis


def _analyze_path_patterns(paths: List[str]) -> Dict[str, int]:
    """Analyze common patterns in sitemap paths."""
    
    patterns = {}
    
    for path in paths:
        # Analyze path depth
        depth = len([p for p in path.split('/') if p])
        depth_key = f"depth_{depth}"
        patterns[depth_key] = patterns.get(depth_key, 0) + 1
        
        # Analyze common prefixes
        if path.startswith('/products'):
            patterns['products'] = patterns.get('products', 0) + 1
        elif path.startswith('/blog'):
            patterns['blog'] = patterns.get('blog', 0) + 1
        elif path.startswith('/news'):
            patterns['news'] = patterns.get('news', 0) + 1
        elif path.startswith('/support'):
            patterns['support'] = patterns.get('support', 0) + 1
        elif path.startswith('/global'):
            patterns['global'] = patterns.get('global', 0) + 1
    
    # Sort by count (most common first)
    return dict(sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5])


async def demo_sitemap_extraction():
    """Demo the sitemap extraction functionality."""
    print("\nTesting Sitemap Path Extraction")
    print("="*50)
    
    # Test with Microsoft.com using en-us locale filter
    url = "https://www.microsoft.com"
    print(f"Extracting sitemap paths from {url} (en-us only)...")
    
    # Get sitemap paths with locale filtering
    paths = await extract_sitemap_paths(url, locale_filter="en-us")
    
    print(f"\nSitemap Extraction Results:")
    print(f"   Total paths found: {len(paths)}")
    
    # Show sample paths
    if paths:
        print(f"\nSample sitemap paths:")
        for i, path in enumerate(paths[:15], 1):
            print(f"   {i:2d}. {path}")
        
        if len(paths) > 15:
            print(f"   ... and {len(paths) - 15} more paths")
    else:
        print("   No sitemap paths found")
    
    return paths


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    async def main():
        # Demo sitemap extraction feature
        await demo_sitemap_extraction()
    
    # Run tests
    asyncio.run(main())
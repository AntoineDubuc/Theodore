#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robots.txt Crawler Tool
=======================

Extracts and analyzes robots.txt files, outputting clean path-only URLs for 
allowed/disallowed paths, sitemaps, and crawler directives.

This tool discovers robots.txt content and parses it to understand website crawling rules,
then strips domains to provide clean paths for further analysis.

Usage:
    # Async usage
    result = await extract_robots_info("https://example.com")
    
    # Sync usage  
    result = extract_robots_info_sync("https://example.com")
    
    # Test multiple sites
    python3 crawl_robots_txt.py
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import aiohttp
import re

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


class RobotsInfo:
    """Represents parsed robots.txt information."""
    
    def __init__(self, url: str):
        self.url = url
        self.raw_content = ""
        self.user_agents = {}  # {user_agent: {allow: [], disallow: [], crawl_delay: None}}
        self.sitemaps = []
        self.global_directives = {}
        self.comments = []
        self.parsing_errors = []
        self.found = False
    
    def __repr__(self):
        return f"RobotsInfo(url='{self.url}', found={self.found}, user_agents={len(self.user_agents)}, sitemaps={len(self.sitemaps)})"


async def extract_robots_info(base_url: str, user_agent_filter: str = "*") -> RobotsInfo:
    """
    Extract and parse robots.txt information from a website.
    
    Args:
        base_url: The website URL to extract robots.txt from
        user_agent_filter: User agent to filter rules for (default: "*" for all)
        
    Returns:
        RobotsInfo object containing parsed robots.txt data
    """
    print(f"Extracting robots.txt from: {base_url}")
    if user_agent_filter != "*":
        print(f"Filtering for user agent: {user_agent_filter}")
    
    # Parse domain for URL construction
    parsed_url = urlparse(base_url)
    domain = parsed_url.netloc
    robots_url = urljoin(base_url, '/robots.txt')
    
    robots_info = RobotsInfo(robots_url)
    
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": USER_AGENT}
        ) as session:
            
            async with session.get(robots_url) as response:
                if response.status == 200:
                    robots_info.found = True
                    robots_info.raw_content = await response.text()
                    
                    print(f"Found robots.txt ({len(robots_info.raw_content)} characters)")
                    
                    # Parse the robots.txt content
                    _parse_robots_content(robots_info, user_agent_filter)
                    
                    print(f"Parsed {len(robots_info.user_agents)} user agent sections")
                    print(f"Found {len(robots_info.sitemaps)} sitemap references")
                    
                else:
                    print(f"No robots.txt found (HTTP {response.status})")
                    robots_info.found = False
    
    except Exception as e:
        logger.error(f"Error fetching robots.txt from {base_url}: {e}")
        print(f"Error: {e}")
        robots_info.parsing_errors.append(str(e))
    
    return robots_info


def _parse_robots_content(robots_info: RobotsInfo, user_agent_filter: str = "*") -> None:
    """Parse robots.txt content into structured data."""
    
    lines = robots_info.raw_content.split('\n')
    current_user_agent = None
    current_section = None
    
    for line_num, line in enumerate(lines, 1):
        # Clean line
        original_line = line
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Handle comments
        if line.startswith('#'):
            robots_info.comments.append(line[1:].strip())
            continue
        
        # Split on colon
        if ':' not in line:
            robots_info.parsing_errors.append(f"Line {line_num}: Invalid format - '{original_line}'")
            continue
        
        directive, value = line.split(':', 1)
        directive = directive.strip().lower()
        value = value.strip()
        
        try:
            if directive == 'user-agent':
                current_user_agent = value
                current_section = {
                    'allow': [],
                    'disallow': [],
                    'crawl_delay': None,
                    'other_directives': {}
                }
                robots_info.user_agents[current_user_agent] = current_section
            
            elif directive == 'sitemap':
                robots_info.sitemaps.append(value)
            
            elif directive in ['allow', 'disallow']:
                if current_section is not None:
                    current_section[directive].append(value)
                else:
                    robots_info.parsing_errors.append(f"Line {line_num}: {directive} without user-agent")
            
            elif directive == 'crawl-delay':
                if current_section is not None:
                    try:
                        current_section['crawl_delay'] = float(value)
                    except ValueError:
                        robots_info.parsing_errors.append(f"Line {line_num}: Invalid crawl-delay value - '{value}'")
                else:
                    robots_info.parsing_errors.append(f"Line {line_num}: crawl-delay without user-agent")
            
            else:
                # Store other directives
                if current_section is not None:
                    current_section['other_directives'][directive] = value
                else:
                    robots_info.global_directives[directive] = value
        
        except Exception as e:
            robots_info.parsing_errors.append(f"Line {line_num}: Parse error - {e}")


def strip_domains_from_robots(robots_info: RobotsInfo, base_url: str, user_agent_filter: str = "*") -> Dict[str, List[str]]:
    """
    Remove domains from robots.txt paths to get clean path-only URLs.
    
    Args:
        robots_info: RobotsInfo object from extract_robots_info()
        base_url: Base URL to strip from paths
        user_agent_filter: User agent to filter rules for (default: "*" for all)
        
    Returns:
        Dictionary with clean path-only URLs:
        {
            "allowed_paths": ["/api", "/public"],
            "disallowed_paths": ["/admin", "/private"],
            "sitemap_paths": ["/sitemap.xml", "/sitemap-index.xml"],
            "all_paths": ["/api", "/public", "/admin", "/private"]
        }
    """
    # Parse the base URL to get domain info
    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc
    
    def extract_path(url_or_path: str) -> str:
        """Extract clean path from URL or path, removing domain if present."""
        try:
            # If it looks like a full URL
            if url_or_path.startswith('http'):
                parsed = urlparse(url_or_path)
                
                # If it's the same domain, return just the path
                if parsed.netloc == base_domain:
                    path = parsed.path
                else:
                    # Different domain, return full URL
                    return url_or_path
            else:
                # Already a path
                path = url_or_path
            
            # Ensure path starts with /
            if not path.startswith('/'):
                path = '/' + path
            
            # Remove trailing / except for root
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')
            
            return path if path != '/' else '/'
                
        except Exception:
            # If parsing fails, return original
            return url_or_path
    
    # Initialize result structure
    result = {
        "allowed_paths": [],
        "disallowed_paths": [],
        "sitemap_paths": [],
        "all_paths": []
    }
    
    seen_paths = set()
    
    # Process sitemap URLs
    for sitemap_url in robots_info.sitemaps:
        path = extract_path(sitemap_url)
        if path not in seen_paths:
            seen_paths.add(path)
            result["sitemap_paths"].append(path)
    
    # Find relevant user agent sections
    relevant_sections = []
    
    # Look for exact match first
    if user_agent_filter in robots_info.user_agents:
        relevant_sections.append(robots_info.user_agents[user_agent_filter])
    
    # Look for wildcard match
    if "*" in robots_info.user_agents and user_agent_filter != "*":
        relevant_sections.append(robots_info.user_agents["*"])
    
    # If filtering for "*", include all sections
    if user_agent_filter == "*":
        relevant_sections = list(robots_info.user_agents.values())
    
    # Process allow/disallow rules
    for section in relevant_sections:
        # Process allowed paths
        for allowed_path in section['allow']:
            path = extract_path(allowed_path)
            if path not in seen_paths:
                seen_paths.add(path)
                result["allowed_paths"].append(path)
        
        # Process disallowed paths
        for disallowed_path in section['disallow']:
            path = extract_path(disallowed_path)
            if path not in seen_paths:
                seen_paths.add(path)
                result["disallowed_paths"].append(path)
    
    # Create combined all_paths list
    all_paths = []
    for section_paths in [result["allowed_paths"], result["disallowed_paths"], result["sitemap_paths"]]:
        for path in section_paths:
            if path not in all_paths:
                all_paths.append(path)
    
    result["all_paths"] = all_paths
    
    return result


async def extract_robots_paths(base_url: str, user_agent_filter: str = "*") -> Dict[str, List[str]]:
    """
    Extract robots.txt information and return as domain-free paths.
    
    Args:
        base_url: Website URL to extract robots.txt from
        user_agent_filter: User agent to filter rules for (default: "*" for all)
        
    Returns:
        Dictionary with clean path-only URLs
    """
    # Get robots info
    robots_info = await extract_robots_info(base_url, user_agent_filter)
    
    # Strip domains to get clean paths
    paths = strip_domains_from_robots(robots_info, base_url, user_agent_filter)
    
    return paths


def extract_robots_paths_sync(base_url: str, user_agent_filter: str = "*") -> Dict[str, List[str]]:
    """
    Synchronous wrapper for extract_robots_paths().
    
    Args:
        base_url: Website URL to extract robots.txt from
        user_agent_filter: User agent to filter rules for (default: "*" for all)
        
    Returns:
        Dictionary with clean path-only URLs
    """
    try:
        return asyncio.run(extract_robots_paths(base_url, user_agent_filter))
    except Exception as e:
        logger.error(f"Error in sync wrapper for {base_url}: {e}")
        return {
            "allowed_paths": [],
            "disallowed_paths": [],
            "sitemap_paths": [],
            "all_paths": []
        }


async def analyze_robots_structure(url: str, user_agent_filter: str = "*") -> Dict[str, any]:
    """
    Analyze the robots.txt structure of a website in detail.
    
    Args:
        url: Website URL to analyze
        user_agent_filter: User agent to filter analysis for
        
    Returns:
        Detailed analysis of robots.txt structure
    """
    print(f"\nAnalyzing robots.txt structure: {url}")
    print("="*60)
    
    start_time = time.time()
    
    # Extract robots info
    robots_info = await extract_robots_info(url, user_agent_filter)
    
    # Get clean paths
    paths = strip_domains_from_robots(robots_info, url, user_agent_filter)
    
    extraction_time = time.time() - start_time
    
    analysis = {
        "url": url,
        "robots_found": robots_info.found,
        "total_user_agents": len(robots_info.user_agents),
        "total_sitemaps": len(robots_info.sitemaps),
        "allowed_paths": len(paths["allowed_paths"]),
        "disallowed_paths": len(paths["disallowed_paths"]),
        "sitemap_paths": len(paths["sitemap_paths"]),
        "total_paths": len(paths["all_paths"]),
        "extraction_time": extraction_time,
        "parsing_errors": len(robots_info.parsing_errors),
        "user_agents": list(robots_info.user_agents.keys()),
        "sample_paths": _get_sample_paths(paths),
        "crawl_policies": _analyze_crawl_policies(robots_info, user_agent_filter)
    }
    
    # Print analysis
    print(f"Robots.txt Analysis:")
    print(f"   Found robots.txt: {'Yes' if analysis['robots_found'] else 'No'}")
    if analysis['robots_found']:
        print(f"   User agents defined: {analysis['total_user_agents']}")
        print(f"   Sitemaps referenced: {analysis['total_sitemaps']}")
        print(f"   Allowed paths: {analysis['allowed_paths']}")
        print(f"   Disallowed paths: {analysis['disallowed_paths']}")
        print(f"   Total unique paths: {analysis['total_paths']}")
        print(f"   Parsing errors: {analysis['parsing_errors']}")
    print(f"   Extraction time: {analysis['extraction_time']:.2f}s")
    
    if analysis['user_agents']:
        print(f"\nUser agents:")
        for i, ua in enumerate(analysis['user_agents'][:5], 1):
            print(f"   {i}. {ua}")
        if len(analysis['user_agents']) > 5:
            print(f"   ... and {len(analysis['user_agents']) - 5} more")
    
    if analysis['sample_paths']:
        print(f"\nSample paths by type:")
        for path_type, sample_list in analysis['sample_paths'].items():
            if sample_list:
                print(f"   {path_type}: {', '.join(sample_list[:3])}")
    
    if analysis['crawl_policies']:
        print(f"\nCrawl policies:")
        for policy, value in analysis['crawl_policies'].items():
            print(f"   {policy}: {value}")
    
    return analysis


def _get_sample_paths(paths: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Get sample paths from each category."""
    return {
        path_type: path_list[:5]  # First 5 paths from each type
        for path_type, path_list in paths.items()
        if path_list
    }


def _analyze_crawl_policies(robots_info: RobotsInfo, user_agent_filter: str = "*") -> Dict[str, any]:
    """Analyze crawling policies from robots.txt."""
    policies = {}
    
    if not robots_info.found:
        return {"policy": "No robots.txt found - unrestricted crawling"}
    
    # Find relevant sections
    relevant_sections = []
    if user_agent_filter in robots_info.user_agents:
        relevant_sections.append((user_agent_filter, robots_info.user_agents[user_agent_filter]))
    if "*" in robots_info.user_agents and user_agent_filter != "*":
        relevant_sections.append(("*", robots_info.user_agents["*"]))
    
    if not relevant_sections and user_agent_filter == "*":
        relevant_sections = [(ua, data) for ua, data in robots_info.user_agents.items()]
    
    # Analyze restrictions
    total_disallowed = sum(len(section[1]['disallow']) for section in relevant_sections)
    total_allowed = sum(len(section[1]['allow']) for section in relevant_sections)
    
    if total_disallowed == 0:
        policies["restriction_level"] = "Open"
    elif total_disallowed > 10:
        policies["restriction_level"] = "Highly Restricted"
    elif total_disallowed > 3:
        policies["restriction_level"] = "Moderately Restricted" 
    else:
        policies["restriction_level"] = "Lightly Restricted"
    
    # Check for common patterns
    all_disallowed = []
    crawl_delays = []
    
    for ua, section in relevant_sections:
        all_disallowed.extend(section['disallow'])
        if section['crawl_delay'] is not None:
            crawl_delays.append(section['crawl_delay'])
    
    # Analyze common restrictions
    if any('/' == path for path in all_disallowed):
        policies["crawling_allowed"] = "Blocked (disallow: /)"
    elif any('/admin' in path.lower() for path in all_disallowed):
        policies["admin_access"] = "Blocked"
    elif any('/api' in path.lower() for path in all_disallowed):
        policies["api_access"] = "Blocked"
    
    if crawl_delays:
        policies["crawl_delay"] = f"{min(crawl_delays)}-{max(crawl_delays)}s"
    
    policies["total_rules"] = total_disallowed + total_allowed
    
    return policies


async def demo_robots_extraction():
    """Demo the robots.txt extraction functionality."""
    print("\nTesting Robots.txt Path Extraction")
    print("="*50)
    
    # Test with multiple sites
    test_sites = [
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.google.com",
        "https://www.roland.com"
    ]
    
    for site in test_sites:
        try:
            print(f"\nTesting: {site}")
            print("-" * 30)
            
            # Get robots paths
            paths = await extract_robots_paths(site)
            
            print(f"Results:")
            print(f"   Allowed paths: {len(paths['allowed_paths'])}")
            print(f"   Disallowed paths: {len(paths['disallowed_paths'])}")
            print(f"   Sitemap paths: {len(paths['sitemap_paths'])}")
            print(f"   Total paths: {len(paths['all_paths'])}")
            
            # Show sample paths
            if paths['disallowed_paths']:
                print(f"   Sample disallowed: {', '.join(paths['disallowed_paths'][:3])}")
            if paths['sitemap_paths']:
                print(f"   Sample sitemaps: {', '.join(paths['sitemap_paths'][:2])}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        await asyncio.sleep(1)  # Brief delay between tests
    
    return True


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    async def main():
        # Demo robots.txt extraction feature
        await demo_robots_extraction()
    
    # Run tests
    asyncio.run(main())
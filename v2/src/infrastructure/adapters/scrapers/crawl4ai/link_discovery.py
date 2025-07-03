#!/usr/bin/env python3
"""
Link Discovery Service - Phase 1 of Intelligent Scraping
========================================================

Multi-source link discovery combining robots.txt, sitemap.xml, and recursive crawling
for comprehensive site coverage while filtering noise intelligently.
"""

import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from typing import Set, List, Optional, Callable
import logging
import re


class LinkDiscoveryService:
    """Service for comprehensive link discovery using multiple sources"""
    
    def __init__(self, max_links: int = 1000):
        self.max_links = max_links
        self.discovered_urls: Set[str] = set()
        self.logger = logging.getLogger(__name__)
    
    async def discover_all_links(
        self, 
        base_url: str, 
        max_depth: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Comprehensive link discovery using multiple sources."""
        
        self.discovered_urls.clear()
        total_steps = 4  # robots.txt, sitemap, recursive crawl, filtering
        
        try:
            # Step 1: Analyze robots.txt for additional paths and sitemaps
            if progress_callback:
                from ...interfaces.web_scraper import ScrapingProgress, ScrapingPhase
                progress_callback(ScrapingProgress(
                    ScrapingPhase.LINK_DISCOVERY, 1, total_steps,
                    "Analyzing robots.txt for additional paths and sitemaps"
                ))
            
            await self._discover_from_robots(base_url)
            
            # Step 2: Parse sitemap.xml for structured site navigation
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.LINK_DISCOVERY, 2, total_steps,
                    "Parsing sitemap.xml for structured site navigation"
                ))
            
            await self._discover_from_sitemap(base_url)
            
            # Step 3: Recursive crawling for dynamic discovery
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.LINK_DISCOVERY, 3, total_steps,
                    f"Recursive crawling (depth={max_depth}) for dynamic discovery"
                ))
            
            await self._discover_from_crawling(base_url, max_depth)
            
            # Step 4: Filter and prioritize discovered links
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.LINK_DISCOVERY, 4, total_steps,
                    f"Filtering and prioritizing {len(self.discovered_urls)} discovered links",
                    {"raw_links": len(self.discovered_urls)}
                ))
            
            filtered_links = self._filter_and_prioritize_links(base_url)
            
            self.logger.info(f"Discovery completed: {len(filtered_links)} links from {len(self.discovered_urls)} discovered")
            return filtered_links[:self.max_links]
            
        except Exception as e:
            self.logger.error(f"Link discovery failed: {e}")
            # Return at least the base URL as fallback
            return [base_url]
    
    async def _discover_from_robots(self, base_url: str) -> None:
        """Extract paths and sitemap references from robots.txt."""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        
                        # Parse robots.txt for sitemap references
                        for line in robots_content.split('\n'):
                            line = line.strip()
                            if line.lower().startswith('sitemap:'):
                                sitemap_url = line.split(':', 1)[1].strip()
                                await self._discover_from_sitemap(sitemap_url)
                            
                            # Extract allowed paths as potential URLs
                            elif line.lower().startswith('allow:'):
                                path = line.split(':', 1)[1].strip()
                                if path and path != '/':
                                    url = urljoin(base_url, path)
                                    self.discovered_urls.add(url)
                        
                        self.logger.debug(f"Discovered {len(self.discovered_urls)} URLs from robots.txt")
        
        except Exception as e:
            self.logger.debug(f"Failed to process robots.txt: {e}")
    
    async def _discover_from_sitemap(self, sitemap_url: str) -> None:
        """Recursively parse sitemap.xml and sitemap index files."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        sitemap_content = await response.text()
                        
                        try:
                            root = ET.fromstring(sitemap_content)
                            
                            # Handle sitemap index files
                            for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                if loc is not None and loc.text:
                                    await self._discover_from_sitemap(loc.text)
                            
                            # Handle regular sitemap entries
                            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                if loc is not None and loc.text:
                                    self.discovered_urls.add(loc.text)
                        
                        except ET.ParseError:
                            # Try parsing as plain text sitemap
                            for line in sitemap_content.split('\n'):
                                line = line.strip()
                                if line and line.startswith('http'):
                                    self.discovered_urls.add(line)
                        
                        self.logger.debug(f"Sitemap processed: {len(self.discovered_urls)} total URLs")
        
        except Exception as e:
            self.logger.debug(f"Failed to process sitemap {sitemap_url}: {e}")
    
    async def _discover_from_crawling(self, base_url: str, max_depth: int) -> None:
        """Intelligent recursive crawling with noise filtering."""
        crawled_urls = set()
        urls_to_crawl = [(base_url, 0)]  # (url, depth)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            while urls_to_crawl and len(self.discovered_urls) < self.max_links:
                url, depth = urls_to_crawl.pop(0)
                
                if url in crawled_urls or depth > max_depth:
                    continue
                
                crawled_urls.add(url)
                
                try:
                    async with session.get(url) as response:
                        if response.status == 200 and 'text/html' in response.headers.get('content-type', ''):
                            html_content = await response.text()
                            
                            # Extract links using regex (faster than BeautifulSoup for discovery)
                            link_pattern = r'href=["\']([^"\']+)["\']'
                            found_links = re.findall(link_pattern, html_content, re.IGNORECASE)
                            
                            for link in found_links:
                                absolute_url = urljoin(url, link)
                                
                                # Smart filtering during discovery
                                if self._is_valuable_url(absolute_url, base_url):
                                    self.discovered_urls.add(absolute_url)
                                    
                                    # Add to crawl queue if we haven't reached max depth
                                    if depth < max_depth and len(urls_to_crawl) < 100:
                                        urls_to_crawl.append((absolute_url, depth + 1))
                
                except Exception as e:
                    self.logger.debug(f"Failed to crawl {url}: {e}")
                
                # Respect rate limits during discovery
                await asyncio.sleep(0.5)
    
    def _is_valuable_url(self, url: str, base_url: str) -> bool:
        """Filter out noise during link discovery."""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_url)
            
            # Only same domain
            if parsed.netloc != base_parsed.netloc:
                return False
            
            path = parsed.path.lower()
            
            # Skip common noise patterns
            noise_patterns = [
                '/wp-content/', '/wp-admin/', '/wp-includes/',  # WordPress
                '.pdf', '.doc', '.zip', '.jpg', '.png', '.gif',  # Files
                '/admin/', '/login/', '/logout/', '/auth/',  # Admin
                '?page=', '&page=', '/page/', '/p/',  # Pagination
                '/tag/', '/tags/', '/category/', '/cat/',  # Blog categories
                '/wp-json/', '/api/', '/ajax/',  # API endpoints
                '/search?', '?s=', '?search=',  # Search results
                '#', 'javascript:', 'mailto:',  # Non-HTTP
            ]
            
            for pattern in noise_patterns:
                if pattern in url.lower():
                    return False
            
            # Prefer valuable patterns
            valuable_patterns = [
                '/about', '/contact', '/team', '/careers', '/jobs',
                '/company', '/leadership', '/management', '/executive',
                '/investors', '/news', '/press', '/media',
                '/products', '/services', '/solutions',
                '/security', '/compliance', '/partners'
            ]
            
            # Higher priority for valuable patterns
            for pattern in valuable_patterns:
                if pattern in path:
                    return True
            
            # Accept reasonable looking pages
            return len(path) < 100 and path.count('/') < 6
            
        except Exception:
            return False
    
    def _filter_and_prioritize_links(self, base_url: str) -> List[str]:
        """Filter and prioritize discovered links by value."""
        
        # Score all URLs
        scored_urls = []
        for url in self.discovered_urls:
            score = self._calculate_url_score(url)
            scored_urls.append((score, url))
        
        # Sort by score (highest first)
        scored_urls.sort(reverse=True, key=lambda x: x[0])
        
        # Return prioritized URLs
        return [url for score, url in scored_urls]
    
    def _calculate_url_score(self, url: str) -> float:
        """Calculate value score for URL prioritization."""
        score = 0.0
        path = url.lower()
        
        # High-value page patterns
        high_value = {
            '/contact': 10.0, '/about': 9.0, '/team': 8.0, '/careers': 7.0,
            '/company': 8.0, '/leadership': 7.0, '/management': 6.0, '/executive': 6.0,
            '/investors': 5.0, '/news': 4.0, '/press': 4.0, '/media': 4.0
        }
        
        for pattern, points in high_value.items():
            if pattern in path:
                score += points
        
        # Bonus for root-level pages
        if path.count('/') <= 2:
            score += 2.0
        
        # Penalty for deep nesting
        depth_penalty = max(0, path.count('/') - 3) * 0.5
        score -= depth_penalty
        
        return score
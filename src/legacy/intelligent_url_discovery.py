"""
Intelligent URL Discovery for Theodore
Uses robots.txt analysis, sitemap parsing, and AI to discover the best pages to crawl
"""

import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import aiohttp
import re
from dataclasses import dataclass
from datetime import datetime

from crawl4ai.utils import RobotsParser
from src.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredURL:
    """Represents a discovered URL with metadata"""
    url: str
    source: str  # 'robots', 'sitemap', 'ai_suggested', 'common_pattern'
    priority: float  # 0.0 to 1.0
    page_type: str  # 'homepage', 'about', 'services', etc.
    confidence: float  # AI confidence in this URL being useful

@dataclass 
class URLDiscoveryResult:
    """Results from intelligent URL discovery"""
    discovered_urls: List[DiscoveredURL]
    robots_analysis: Dict[str, any]
    sitemap_found: bool
    total_processing_time: float

class IntelligentURLDiscovery:
    """
    Intelligent URL discovery using robots.txt, sitemaps, and AI analysis
    """
    
    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock_client = bedrock_client
        self.robots_parser = RobotsParser()
        
        # Common page patterns as fallback
        self.fallback_patterns = [
            ("", "homepage", 1.0),
            ("/about", "about", 0.9),
            ("/about-us", "about", 0.9), 
            ("/company", "company", 0.8),
            ("/services", "services", 0.7),
            ("/products", "products", 0.7),
            ("/solutions", "solutions", 0.6),
            ("/team", "team", 0.5),
            ("/leadership", "leadership", 0.5),
            ("/pricing", "pricing", 0.9),
            ("/customers", "customers", 0.8),
            ("/case-studies", "case_studies", 0.8),
            ("/careers", "careers", 0.3),
            ("/contact", "contact", 0.2)
        ]

    async def discover_urls(self, base_url: str, company_name: str) -> URLDiscoveryResult:
        """
        Intelligently discover the best URLs to crawl for a company
        
        Args:
            base_url: Company website base URL
            company_name: Company name for context
            
        Returns:
            URLDiscoveryResult with discovered URLs and metadata
        """
        start_time = datetime.now()
        discovered_urls = []
        robots_analysis = {}
        sitemap_found = False
        
        logger.info(f"Starting intelligent URL discovery for {company_name} at {base_url}")
        
        try:
            # Step 1: Parse robots.txt
            robots_analysis = await self._analyze_robots_txt(base_url)
            logger.info(f"Robots.txt analysis: {len(robots_analysis.get('sitemap_urls', []))} sitemaps found")
            
            # Step 2: Process sitemaps if found
            sitemap_urls = robots_analysis.get('sitemap_urls', [])
            if sitemap_urls:
                sitemap_found = True
                sitemap_discovered = await self._process_sitemaps(sitemap_urls, base_url)
                discovered_urls.extend(sitemap_discovered)
                logger.info(f"Discovered {len(sitemap_discovered)} URLs from sitemaps")
            
            # Step 3: Crawl homepage to extract actual links
            homepage_links = await self._extract_homepage_links(base_url)
            discovered_urls.extend(homepage_links)
            logger.info(f"Extracted {len(homepage_links)} URLs from homepage links")
            
            # Step 4: AI-powered URL suggestion based on robots.txt content
            if robots_analysis.get('robots_content'):
                ai_suggested = await self._ai_suggest_urls(
                    base_url, 
                    company_name,
                    robots_analysis['robots_content']
                )
                discovered_urls.extend(ai_suggested)
                logger.info(f"AI suggested {len(ai_suggested)} additional URLs")
            
            # Step 5: Fallback to intelligent common patterns
            pattern_urls = await self._generate_pattern_urls(base_url, discovered_urls)
            discovered_urls.extend(pattern_urls)
            logger.info(f"Added {len(pattern_urls)} pattern-based URLs")
            
            # Step 6: Filter and prioritize
            discovered_urls = self._filter_and_prioritize(discovered_urls, robots_analysis)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"URL discovery completed: {len(discovered_urls)} URLs in {processing_time:.2f}s")
            
            return URLDiscoveryResult(
                discovered_urls=discovered_urls,
                robots_analysis=robots_analysis,
                sitemap_found=sitemap_found,
                total_processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"URL discovery failed for {base_url}: {e}")
            
            # Fallback to basic pattern URLs
            fallback_urls = await self._generate_pattern_urls(base_url, [])
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return URLDiscoveryResult(
                discovered_urls=fallback_urls,
                robots_analysis={"error": str(e)},
                sitemap_found=False,
                total_processing_time=processing_time
            )

    async def _analyze_robots_txt(self, base_url: str) -> Dict[str, any]:
        """Analyze robots.txt to extract sitemap URLs and understand crawling rules"""
        
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=10) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        
                        # Extract sitemap URLs
                        sitemap_urls = []
                        for line in robots_content.split('\n'):
                            line = line.strip()
                            if line.lower().startswith('sitemap:'):
                                sitemap_url = line.split(':', 1)[1].strip()
                                sitemap_urls.append(sitemap_url)
                        
                        # Extract disallowed paths
                        disallowed_paths = []
                        for line in robots_content.split('\n'):
                            line = line.strip()
                            if line.lower().startswith('disallow:'):
                                path = line.split(':', 1)[1].strip()
                                if path and path != '/':
                                    disallowed_paths.append(path)
                        
                        return {
                            'robots_content': robots_content,
                            'sitemap_urls': sitemap_urls,
                            'disallowed_paths': disallowed_paths,
                            'found': True
                        }
                    else:
                        logger.warning(f"robots.txt not found at {robots_url} (status: {response.status})")
                        return {'found': False, 'sitemap_urls': [], 'disallowed_paths': []}
                        
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {base_url}: {e}")
            return {'found': False, 'sitemap_urls': [], 'disallowed_paths': [], 'error': str(e)}

    async def _process_sitemaps(self, sitemap_urls: List[str], base_url: str) -> List[DiscoveredURL]:
        """Process sitemap XML files to extract URLs"""
        
        discovered_urls = []
        
        for sitemap_url in sitemap_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(sitemap_url, timeout=15) as response:
                        if response.status == 200:
                            sitemap_content = await response.text()
                            urls = self._parse_sitemap_xml(sitemap_content, base_url)
                            
                            for url, lastmod in urls:
                                # Determine page type from URL pattern
                                page_type = self._classify_url_type(url)
                                priority = self._calculate_sitemap_priority(url, page_type, lastmod)
                                
                                discovered_urls.append(DiscoveredURL(
                                    url=url,
                                    source='sitemap',
                                    priority=priority,
                                    page_type=page_type,
                                    confidence=0.9  # High confidence for sitemap URLs
                                ))
                            
                            logger.info(f"Extracted {len(urls)} URLs from sitemap: {sitemap_url}")
                        
            except Exception as e:
                logger.warning(f"Failed to process sitemap {sitemap_url}: {e}")
        
        return discovered_urls

    def _parse_sitemap_xml(self, sitemap_content: str, base_url: str) -> List[Tuple[str, Optional[str]]]:
        """Parse sitemap XML and extract URLs with lastmod dates"""
        
        urls = []
        
        try:
            # Handle sitemap index files
            if '<sitemapindex' in sitemap_content:
                root = ET.fromstring(sitemap_content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                for sitemap in root.findall('.//ns:sitemap', namespace):
                    loc = sitemap.find('ns:loc', namespace)
                    if loc is not None:
                        # This is a sitemap index, would need recursive processing
                        # For now, just note it
                        logger.info(f"Found sitemap index with nested sitemap: {loc.text}")
            
            # Handle regular sitemap files
            else:
                root = ET.fromstring(sitemap_content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                for url_elem in root.findall('.//ns:url', namespace):
                    loc = url_elem.find('ns:loc', namespace)
                    lastmod = url_elem.find('ns:lastmod', namespace)
                    
                    if loc is not None:
                        url = loc.text
                        lastmod_date = lastmod.text if lastmod is not None else None
                        
                        # Only include URLs from the same domain
                        if url.startswith(base_url):
                            urls.append((url, lastmod_date))
        
        except ET.ParseError as e:
            logger.warning(f"Failed to parse sitemap XML: {e}")
        
        return urls

    async def _extract_homepage_links(self, base_url: str) -> List[DiscoveredURL]:
        """Extract internal links from homepage using crawl4ai"""
        
        discovered_urls = []
        
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            
            async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
                config = CrawlerRunConfig(
                    cache_mode='disabled',  # Don't cache for discovery
                    page_timeout=10000,     # 10 second timeout
                    word_count_threshold=10  # Minimal filtering
                )
                
                result = await crawler.arun(url=base_url, config=config)
                
                if result.success and result.links:
                    # Process internal links from the homepage
                    internal_links = result.links.get('internal', [])
                    
                    for link in internal_links:
                        href = link.get('href', '')
                        text = link.get('text', '').strip()
                        
                        if href and self._is_valuable_link(href, text):
                            # Determine page type from URL and text
                            page_type = self._classify_url_type(href)
                            
                            # Use text context to improve classification
                            if text:
                                page_type = self._improve_classification_with_text(page_type, text, href)
                            
                            # Calculate priority based on page type and link context
                            priority = self._calculate_link_priority(href, page_type, text)
                            
                            discovered_urls.append(DiscoveredURL(
                                url=href,
                                source='homepage_links',
                                priority=priority,
                                page_type=page_type,
                                confidence=0.8  # High confidence for actual links
                            ))
                    
                    logger.info(f"Extracted {len(discovered_urls)} valuable internal links from homepage")
                else:
                    logger.warning(f"Failed to extract links from homepage: success={result.success}")
                    
        except Exception as e:
            logger.warning(f"Homepage link extraction failed: {e}")
        
        return discovered_urls

    def _is_valuable_link(self, href: str, text: str) -> bool:
        """Determine if a link is valuable for company intelligence"""
        
        # Skip non-valuable links
        skip_patterns = [
            '/blog/', '/news/', '/press/', '/events/', '/webinar',
            '/download/', '/pdf/', '/doc/', '/zip/', 
            '/login', '/signup', '/register', '/account',
            '/privacy', '/terms', '/cookie', '/legal',
            '/support', '/help', '/faq', '/documentation',
            '#', 'javascript:', 'mailto:', 'tel:',
            '/search', '/sitemap', '/feed', '/rss'
        ]
        
        href_lower = href.lower()
        text_lower = text.lower()
        
        for pattern in skip_patterns:
            if pattern in href_lower or pattern in text_lower:
                return False
        
        # Focus on valuable pages
        valuable_patterns = [
            'about', 'company', 'team', 'leadership', 'management',
            'service', 'product', 'solution', 'offering',
            'pricing', 'price', 'plan', 'customer', 'client',
            'case', 'portfolio', 'work', 'career', 'job'
        ]
        
        for pattern in valuable_patterns:
            if pattern in href_lower or pattern in text_lower:
                return True
        
        # Include short paths that might be top-level pages
        path = urlparse(href).path.strip('/')
        if path and len(path.split('/')) <= 2 and len(path) <= 20:
            return True
            
        return False

    def _improve_classification_with_text(self, initial_type: str, link_text: str, href: str) -> str:
        """Improve page type classification using link text context"""
        
        text_lower = link_text.lower()
        
        # Text-based classification rules
        text_patterns = {
            'about': ['about', 'company', 'who we are', 'our story', 'overview'],
            'team': ['team', 'people', 'staff', 'leadership', 'management', 'founders'],
            'services': ['service', 'what we do', 'offering', 'capabilities'],
            'products': ['product', 'solution', 'platform', 'tool'],
            'pricing': ['pricing', 'price', 'cost', 'plan', 'package'],
            'customers': ['customer', 'client', 'testimonial', 'reference'],
            'case_studies': ['case', 'portfolio', 'work', 'project', 'success'],
            'careers': ['career', 'job', 'hiring', 'opportunity', 'join'],
            'contact': ['contact', 'reach', 'get in touch', 'location']
        }
        
        for page_type, patterns in text_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return page_type
        
        return initial_type

    def _calculate_link_priority(self, href: str, page_type: str, text: str) -> float:
        """Calculate priority for discovered links"""
        
        # Base priority by page type
        type_priorities = {
            'homepage': 1.0,
            'about': 0.9,
            'company': 0.8,
            'services': 0.7,
            'products': 0.7,
            'pricing': 0.9,
            'customers': 0.8,
            'case_studies': 0.8,
            'team': 0.5,
            'solutions': 0.6,
            'careers': 0.3,
            'contact': 0.2,
            'unknown': 0.4
        }
        
        priority = type_priorities.get(page_type, 0.4)
        
        # Boost priority for prominent link text
        prominent_indicators = [
            'main', 'primary', 'key', 'core', 'top', 'featured',
            'overview', 'introduction', 'learn more'
        ]
        
        text_lower = text.lower()
        for indicator in prominent_indicators:
            if indicator in text_lower:
                priority += 0.1
                break
        
        # Boost priority for shorter URLs (often more important)
        path_depth = len(urlparse(href).path.strip('/').split('/'))
        if path_depth <= 1:
            priority += 0.1
        elif path_depth == 2:
            priority += 0.05
        
        return min(1.0, priority)

    async def _ai_suggest_urls(self, base_url: str, company_name: str, robots_content: str) -> List[DiscoveredURL]:
        """Use AI to suggest URLs based on robots.txt content and company context"""
        
        try:
            prompt = f"""
            Analyze this robots.txt content for {company_name} (website: {base_url}) and suggest the most valuable page URLs to crawl for company intelligence gathering.

            robots.txt content:
            {robots_content}

            Based on this robots.txt and common website patterns, suggest 5-10 specific URLs that would be most valuable for extracting:
            - Company information and business model
            - Services and products 
            - Team and leadership
            - Company stage and target market
            - Technology and industry focus

            Consider:
            1. What paths are NOT disallowed in robots.txt
            2. Common corporate website structures
            3. Pages that typically contain company intelligence

            Respond with ONLY a JSON list of objects like:
            [
                {{"url": "https://example.com/about", "page_type": "about", "confidence": 0.9, "reasoning": "About pages contain company background"}},
                {{"url": "https://example.com/team", "page_type": "team", "confidence": 0.7, "reasoning": "Team pages show company structure"}}
            ]
            """
            
            response = self.bedrock_client.analyze_content(prompt)
            
            # Parse AI response
            import json
            try:
                ai_suggestions = json.loads(response)
                discovered_urls = []
                
                for suggestion in ai_suggestions:
                    discovered_urls.append(DiscoveredURL(
                        url=suggestion.get('url', ''),
                        source='ai_suggested',
                        priority=suggestion.get('confidence', 0.5),
                        page_type=suggestion.get('page_type', 'unknown'),
                        confidence=suggestion.get('confidence', 0.5)
                    ))
                
                return discovered_urls
                
            except json.JSONDecodeError:
                logger.warning("AI response was not valid JSON, falling back to pattern matching")
                return []
                
        except Exception as e:
            logger.warning(f"AI URL suggestion failed: {e}")
            return []

    async def _generate_pattern_urls(self, base_url: str, existing_urls: List[DiscoveredURL]) -> List[DiscoveredURL]:
        """Generate URLs using common patterns, avoiding duplicates"""
        
        existing_paths = {urlparse(url.url).path for url in existing_urls}
        pattern_urls = []
        
        for path, page_type, priority in self.fallback_patterns:
            full_url = urljoin(base_url, path)
            url_path = urlparse(full_url).path
            
            # Skip if we already have this path
            if url_path not in existing_paths:
                pattern_urls.append(DiscoveredURL(
                    url=full_url,
                    source='common_pattern',
                    priority=priority * 0.7,  # Lower priority than discovered URLs
                    page_type=page_type,
                    confidence=0.6  # Medium confidence for patterns
                ))
        
        return pattern_urls

    def _classify_url_type(self, url: str) -> str:
        """Classify URL type based on path patterns"""
        
        path = urlparse(url).path.lower()
        
        if path == '/' or path == '':
            return 'homepage'
        elif 'about' in path:
            return 'about'
        elif 'team' in path or 'leadership' in path:
            return 'team'
        elif 'service' in path:
            return 'services'
        elif 'product' in path:
            return 'products'
        elif 'solution' in path:
            return 'solutions'
        elif 'pricing' in path or 'price' in path:
            return 'pricing'
        elif 'customer' in path or 'client' in path:
            return 'customers'
        elif 'case' in path or 'study' in path:
            return 'case_studies'
        elif 'career' in path or 'job' in path:
            return 'careers'
        elif 'contact' in path:
            return 'contact'
        elif 'company' in path:
            return 'company'
        else:
            return 'unknown'

    def _calculate_sitemap_priority(self, url: str, page_type: str, lastmod: Optional[str]) -> float:
        """Calculate priority for sitemap URLs"""
        
        # Base priority by page type
        type_priorities = {
            'homepage': 1.0,
            'about': 0.9,
            'company': 0.8,
            'services': 0.7,
            'products': 0.7,
            'pricing': 0.9,
            'customers': 0.8,
            'case_studies': 0.8,
            'team': 0.5,
            'solutions': 0.6,
            'careers': 0.3,
            'contact': 0.2,
            'unknown': 0.4
        }
        
        base_priority = type_priorities.get(page_type, 0.4)
        
        # Boost priority for recently modified pages
        if lastmod:
            try:
                from datetime import datetime, timezone
                lastmod_date = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
                days_since_update = (datetime.now(timezone.utc) - lastmod_date).days
                
                if days_since_update < 30:
                    base_priority += 0.1  # Recent updates boost priority
                elif days_since_update > 365:
                    base_priority -= 0.1  # Old content lower priority
                    
            except:
                pass  # Ignore date parsing errors
        
        return min(1.0, max(0.1, base_priority))

    def _filter_and_prioritize(self, discovered_urls: List[DiscoveredURL], robots_analysis: Dict) -> List[DiscoveredURL]:
        """Filter out disallowed URLs and prioritize the final list"""
        
        disallowed_paths = robots_analysis.get('disallowed_paths', [])
        filtered_urls = []
        
        for discovered_url in discovered_urls:
            # Check if URL is disallowed by robots.txt
            url_path = urlparse(discovered_url.url).path
            
            is_allowed = True
            for disallowed in disallowed_paths:
                if url_path.startswith(disallowed):
                    is_allowed = False
                    break
            
            if is_allowed:
                filtered_urls.append(discovered_url)
        
        # Sort by priority (highest first) and remove duplicates
        seen_urls = set()
        unique_urls = []
        
        for url in sorted(filtered_urls, key=lambda x: x.priority, reverse=True):
            if url.url not in seen_urls:
                seen_urls.add(url.url)
                unique_urls.append(url)
        
        # Limit to top 20 URLs for performance
        return unique_urls[:20]

    async def get_crawl_priority_list(self, base_url: str, company_name: str) -> List[Tuple[str, str, float]]:
        """
        Get a prioritized list of URLs to crawl
        Returns: List of (url, page_type, priority) tuples
        """
        
        discovery_result = await self.discover_urls(base_url, company_name)
        
        return [
            (url.url, url.page_type, url.priority) 
            for url in discovery_result.discovered_urls
        ]
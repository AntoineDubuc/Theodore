"""
Intelligent Company Scraper using LLM-driven discovery and parallel extraction
Replaces hardcoded schemas with dynamic, sales-focused intelligence gathering
"""

import logging
import asyncio
import aiohttp
import time
import re
import json
import os
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlencode
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.models import CompanyData, CompanyIntelligenceConfig
from src.progress_logger import log_processing_phase, start_company_processing, complete_company_processing

logger = logging.getLogger(__name__)


class IntelligentCompanyScraper:
    """
    Advanced company scraper using LLM-driven link discovery and parallel extraction
    """
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.bedrock_client = bedrock_client
        self.max_depth = 3  # Recursive crawl depth
        self.max_pages = 100  # Maximum pages to process
        self.concurrent_limit = 10  # Concurrent requests limit
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        
        # Initialize Gemini client if available
        self.gemini_client = None
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key and gemini_api_key.startswith("AIza"):
                try:
                    genai.configure(api_key=gemini_api_key)
                    self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
                    logger.info("Gemini 2.0 Flash client initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini client: {e}")
            else:
                logger.warning("GEMINI_API_KEY not found or invalid in environment variables")
        
    async def scrape_company_intelligent(self, company_data: CompanyData, job_id: str = None) -> CompanyData:
        """
        Main method: Intelligent company scraping with LLM-driven discovery and progress tracking
        """
        start_time = time.time()
        base_url = self._normalize_url(company_data.website)
        
        # Start progress tracking if no job_id provided
        if not job_id:
            job_id = start_company_processing(company_data.name)
        
        logger.info(f"Starting intelligent scraping for {company_data.name} (job: {job_id})")
        
        try:
            # Phase 1: Comprehensive Link Discovery
            log_processing_phase(job_id, "Link Discovery", "running", 
                               target_url=base_url, max_depth=self.max_depth)
            
            all_links = await self._discover_all_links(base_url)
            
            log_processing_phase(job_id, "Link Discovery", "completed", 
                               links_discovered=len(all_links), 
                               sources=["robots.txt", "sitemap.xml", "recursive_crawl"])
            
            # Phase 2: LLM-Driven Page Selection
            log_processing_phase(job_id, "LLM Page Selection", "running",
                               total_links=len(all_links), max_pages=self.max_pages)
            
            selected_urls = await self._llm_select_promising_pages(
                all_links, company_data.name, base_url
            )
            
            log_processing_phase(job_id, "LLM Page Selection", "completed",
                               pages_selected=len(selected_urls),
                               selection_ratio=f"{len(selected_urls)}/{len(all_links)}")
            
            # Phase 3: Parallel Content Extraction
            log_processing_phase(job_id, "Content Extraction", "running",
                               pages_to_extract=len(selected_urls),
                               concurrent_limit=self.concurrent_limit)
            
            page_contents = await self._parallel_extract_content(selected_urls)
            
            total_content_chars = sum(len(page['content']) for page in page_contents)
            log_processing_phase(job_id, "Content Extraction", "completed",
                               successful_extractions=len(page_contents),
                               failed_extractions=len(selected_urls) - len(page_contents),
                               total_content_chars=total_content_chars)
            
            # Phase 4: LLM Content Aggregation
            log_processing_phase(job_id, "Sales Intelligence Generation", "running",
                               content_pages=len(page_contents),
                               total_content_chars=total_content_chars)
            
            sales_intelligence = await self._llm_aggregate_sales_intelligence(
                page_contents, company_data.name
            )
            
            log_processing_phase(job_id, "Sales Intelligence Generation", "completed",
                               intelligence_length=len(sales_intelligence),
                               word_count=len(sales_intelligence.split()) if sales_intelligence else 0)
            
            # Apply results to company data
            company_data.company_description = sales_intelligence
            company_data.pages_crawled = selected_urls
            company_data.crawl_depth = len(selected_urls)
            company_data.crawl_duration = time.time() - start_time
            company_data.scrape_status = "success"
            
            # Complete job tracking
            summary = f"Generated {len(sales_intelligence)} character sales intelligence from {len(page_contents)} pages"
            complete_company_processing(job_id, True, summary=summary)
            
            logger.info(f"Intelligent scraping completed for {company_data.name}")
            
        except Exception as e:
            error_msg = f"Intelligent scraping failed: {str(e)}"
            logger.error(f"{error_msg} for {company_data.name}")
            
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            
            # Complete job tracking with error
            complete_company_processing(job_id, False, error=error_msg)
        
        return company_data
    
    async def _discover_all_links(self, base_url: str) -> List[str]:
        """
        Phase 1: Comprehensive link discovery with multiple sources
        """
        all_links = set()
        domain = urlparse(base_url).netloc
        
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            
            # 1. Robots.txt discovery
            try:
                robots_links = await self._parse_robots_txt(session, base_url)
                all_links.update(robots_links)
                logger.info(f"Found {len(robots_links)} links from robots.txt")
            except Exception as e:
                logger.warning(f"Failed to parse robots.txt: {e}")
            
            # 2. Sitemap.xml discovery
            try:
                sitemap_links = await self._parse_sitemap(session, base_url)
                all_links.update(sitemap_links)
                logger.info(f"Found {len(sitemap_links)} links from sitemap")
            except Exception as e:
                logger.warning(f"Failed to parse sitemap: {e}")
            
            # 3. Recursive page crawling for navigation links
            try:
                crawled_links = await self._recursive_link_discovery(
                    session, base_url, domain, max_depth=self.max_depth
                )
                all_links.update(crawled_links)
                logger.info(f"Found {len(crawled_links)} links from recursive crawling")
            except Exception as e:
                logger.warning(f"Failed recursive discovery: {e}")
        
        # Filter and normalize links
        filtered_links = self._filter_and_normalize_links(list(all_links), domain)
        
        return filtered_links[:1000]  # Limit to prevent overwhelming LLM
    
    async def _parse_robots_txt(self, session: aiohttp.ClientSession, base_url: str) -> Set[str]:
        """Parse robots.txt for additional paths and sitemaps"""
        robots_url = urljoin(base_url, '/robots.txt')
        links = set()
        
        try:
            async with session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract sitemap URLs
                    sitemap_pattern = r'Sitemap:\s*(.+)'
                    sitemaps = re.findall(sitemap_pattern, content, re.IGNORECASE)
                    links.update(sitemaps)
                    
                    # Extract disallowed paths (might indicate important sections)
                    disallow_pattern = r'Disallow:\s*(.+)'
                    disallowed = re.findall(disallow_pattern, content)
                    for path in disallowed:
                        if path.strip() and path != '/':
                            full_url = urljoin(base_url, path.strip())
                            links.add(full_url)
                            
        except Exception as e:
            logger.warning(f"Error parsing robots.txt: {e}")
        
        return links
    
    async def _parse_sitemap(self, session: aiohttp.ClientSession, base_url: str) -> Set[str]:
        """Parse sitemap.xml for comprehensive URL list"""
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/sitemaps/sitemap.xml')
        ]
        
        links = set()
        
        for sitemap_url in sitemap_urls:
            try:
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse XML sitemap
                        try:
                            root = ET.fromstring(content)
                            
                            # Handle regular sitemap
                            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                                loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                if loc_elem is not None:
                                    links.add(loc_elem.text)
                            
                            # Handle sitemap index
                            for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                                loc_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                if loc_elem is not None:
                                    # Recursively parse sub-sitemaps
                                    sub_links = await self._parse_single_sitemap(session, loc_elem.text)
                                    links.update(sub_links)
                                    
                        except ET.ParseError:
                            logger.warning(f"Failed to parse XML sitemap: {sitemap_url}")
                            
            except Exception as e:
                logger.warning(f"Error accessing sitemap {sitemap_url}: {e}")
        
        return links
    
    async def _parse_single_sitemap(self, session: aiohttp.ClientSession, sitemap_url: str) -> Set[str]:
        """Parse a single sitemap file"""
        links = set()
        
        try:
            async with session.get(sitemap_url) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None:
                            links.add(loc_elem.text)
                            
        except Exception as e:
            logger.warning(f"Error parsing single sitemap {sitemap_url}: {e}")
        
        return links
    
    async def _recursive_link_discovery(
        self, 
        session: aiohttp.ClientSession, 
        base_url: str, 
        domain: str, 
        max_depth: int,
        visited: Optional[Set[str]] = None,
        current_depth: int = 0
    ) -> Set[str]:
        """
        Recursively discover links by crawling pages
        """
        if visited is None:
            visited = set()
        
        if current_depth >= max_depth:
            return set()
        
        discovered_links = set()
        
        try:
            # Get page content
            async with session.get(base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)
                        
                        # Only follow links on same domain
                        if urlparse(full_url).netloc == domain:
                            discovered_links.add(full_url)
                            
                            # Recursively crawl if not visited and within depth limit
                            if full_url not in visited and current_depth < max_depth - 1:
                                visited.add(full_url)
                                recursive_links = await self._recursive_link_discovery(
                                    session, full_url, domain, max_depth, visited, current_depth + 1
                                )
                                discovered_links.update(recursive_links)
                                
                                # Add small delay to avoid overwhelming server
                                await asyncio.sleep(0.1)
                                
        except Exception as e:
            logger.warning(f"Error in recursive discovery for {base_url}: {e}")
        
        return discovered_links
    
    def _filter_and_normalize_links(self, links: List[str], domain: str) -> List[str]:
        """
        Filter and normalize discovered links
        """
        filtered = set()
        
        # Exclude patterns
        exclude_patterns = [
            r'\.pdf$', r'\.jpg$', r'\.png$', r'\.gif$', r'\.css$', r'\.js$',
            r'\.ico$', r'\.svg$', r'\.woff$', r'\.ttf$', r'\.mp4$', r'\.zip$',
            r'/wp-admin/', r'/admin/', r'/login', r'/logout', r'/cart', r'/checkout',
            r'#', r'javascript:', r'mailto:', r'tel:', r'ftp:'
        ]
        
        exclude_regex = '|'.join(exclude_patterns)
        
        for link in links:
            try:
                # Normalize URL
                parsed = urlparse(link)
                
                # Must be same domain
                if parsed.netloc != domain:
                    continue
                
                # Remove fragment and query parameters for deduplication
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                
                # Skip if matches exclude patterns
                if re.search(exclude_regex, clean_url, re.IGNORECASE):
                    continue
                
                # Skip very long URLs (likely not useful)
                if len(clean_url) > 200:
                    continue
                
                filtered.add(clean_url)
                
            except Exception:
                continue
        
        return sorted(list(filtered))
    
    async def _llm_select_promising_pages(
        self, 
        all_links: List[str], 
        company_name: str, 
        base_url: str
    ) -> List[str]:
        """
        Phase 2: Use LLM to select most promising pages for sales intelligence
        """
        if not self.bedrock_client:
            # Fallback: Use heuristic selection
            return self._heuristic_page_selection(all_links)
        
        # Prepare links for LLM analysis
        links_text = "\n".join([f"- {link}" for link in all_links[:500]])  # Limit for token management
        
        prompt = f"""You are a sales intelligence analyst. Your goal is to help a salesperson understand everything they need to know about {company_name} to have an effective sales conversation.

Given these discovered links for {company_name} (base URL: {base_url}):

{links_text}

Select up to 100 URLs that would provide the most valuable sales intelligence, focusing on:

1. **Business Model & Value Proposition**: How they make money, what problems they solve
2. **Target Customers**: Who they serve, customer segments, use cases
3. **Product/Service Offerings**: What they sell, pricing models, features
4. **Company Maturity**: Size indicators, funding, growth stage, team
5. **Competitive Position**: Differentiators, market position, partnerships
6. **Sales Process**: How they sell, pricing transparency, contact methods

Prioritize pages that typically contain this information:
- Homepage, About, Products/Services, Pricing, Customers, Case Studies
- Team/Leadership, Careers, Press/News, Partnerships, Solutions
- Industry-specific pages, Use Cases, Documentation

Return ONLY a JSON array of the selected URLs (no explanations):
["url1", "url2", "url3", ...]

Focus on quality over quantity. Better to select 50 highly relevant pages than 100 mediocre ones."""

        try:
            response = await self._call_llm_async(prompt)
            
            # Parse JSON response
            try:
                selected_urls = json.loads(response.strip())
                if isinstance(selected_urls, list):
                    # Validate URLs and limit to max_pages
                    valid_urls = [url for url in selected_urls if url in all_links]
                    return valid_urls[:self.max_pages]
                else:
                    logger.warning("LLM response was not a JSON array, falling back to heuristic")
                    return self._heuristic_page_selection(all_links)
                    
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON, falling back to heuristic")
                return self._heuristic_page_selection(all_links)
                
        except Exception as e:
            logger.error(f"LLM page selection failed: {e}, falling back to heuristic")
            return self._heuristic_page_selection(all_links)
    
    def _heuristic_page_selection(self, all_links: List[str]) -> List[str]:
        """
        Fallback: Heuristic-based page selection when LLM is unavailable
        """
        # Priority keywords for sales intelligence
        high_priority = ['about', 'pricing', 'customers', 'products', 'services', 'solutions']
        medium_priority = ['team', 'leadership', 'careers', 'news', 'press', 'case-studies', 'use-cases']
        low_priority = ['contact', 'blog', 'resources', 'support', 'documentation', 'partners']
        
        scored_links = []
        
        for link in all_links:
            score = 0
            link_lower = link.lower()
            
            # Homepage gets highest priority
            if link.endswith('/') or link.count('/') <= 3:
                score += 100
            
            # Score based on keywords
            for keyword in high_priority:
                if keyword in link_lower:
                    score += 50
                    
            for keyword in medium_priority:
                if keyword in link_lower:
                    score += 25
                    
            for keyword in low_priority:
                if keyword in link_lower:
                    score += 10
            
            scored_links.append((link, score))
        
        # Sort by score and return top pages
        scored_links.sort(key=lambda x: x[1], reverse=True)
        return [link for link, score in scored_links[:self.max_pages]]
    
    async def _parallel_extract_content(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        Phase 3: Extract content from selected pages in parallel
        """
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def extract_single_page(url: str) -> Optional[Dict[str, str]]:
            async with semaphore:
                try:
                    async with AsyncWebCrawler(
                        headless=True,
                        browser_type="chromium",
                        verbose=False
                    ) as crawler:
                        
                        config = CrawlerRunConfig(
                            # Clean content extraction
                            only_text=True,
                            remove_forms=True,
                            word_count_threshold=50,
                            excluded_tags=['nav', 'footer', 'aside', 'script', 'style'],
                            css_selector='main, article, .content, .main-content',
                            
                            # Performance optimization
                            cache_mode=CacheMode.ENABLED,
                            wait_until="domcontentloaded",
                            page_timeout=20000,
                            verbose=False
                        )
                        
                        result = await crawler.arun(url=url, config=config)
                        
                        if result.success and result.cleaned_html:
                            return {
                                'url': url,
                                'content': result.cleaned_html[:10000]  # Limit content length
                            }
                        else:
                            logger.warning(f"Failed to extract content from {url}")
                            return None
                            
                except Exception as e:
                    logger.warning(f"Error extracting from {url}: {e}")
                    return None
        
        # Execute parallel extraction
        logger.info(f"Starting parallel extraction of {len(urls)} pages...")
        tasks = [extract_single_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_extractions = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                successful_extractions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Extraction task failed: {result}")
        
        logger.info(f"Successfully extracted content from {len(successful_extractions)} pages")
        return successful_extractions
    
    async def _llm_aggregate_sales_intelligence(
        self, 
        page_contents: List[Dict[str, str]], 
        company_name: str
    ) -> str:
        """
        Phase 4: Use LLM to aggregate all content into sales intelligence paragraphs
        """
        if not page_contents:
            return f"No content could be extracted for {company_name}."
        
        # Prepare content for LLM analysis
        content_summary = []
        for page in page_contents:
            url_path = urlparse(page['url']).path
            content_summary.append(f"=== Page: {url_path} ===\n{page['content'][:5000]}")  # Limit per page
        
        combined_content = "\n\n".join(content_summary)
        
        # Use Gemini 2.5 Pro with 1M token context if available, otherwise fallback
        prompt = f"""You are a sales intelligence analyst. Analyze all the extracted content from {company_name}'s website and write 2-3 focused paragraphs that provide everything a salesperson needs to know for an effective sales conversation.

Website Content Analysis:
{combined_content}

Write a comprehensive sales intelligence summary covering:

**Paragraph 1 - Company Overview & Value Proposition:**
- What the company does and the problems they solve
- Their primary value proposition and competitive advantages
- Target market and customer segments they serve

**Paragraph 2 - Business Model & Products:**
- How they make money (business model, pricing approach)
- Key products/services and their main features
- Notable customers, partnerships, or market position

**Paragraph 3 - Company Maturity & Sales Context:**
- Company size indicators, growth stage, and maturity
- Sales process indicators (self-serve vs enterprise sales)
- Any relevant context for sales approach (technical complexity, decision makers, etc.)

Focus on factual information that helps with sales qualification and conversation. Avoid marketing fluff. Be specific about business model, customer segments, and company characteristics that matter for sales strategy.

Write in a professional, concise style suitable for sales team consumption."""

        try:
            response = await self._call_llm_async(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM aggregation failed: {e}")
            # Fallback: Simple content summary
            return f"Content extracted from {len(page_contents)} pages for {company_name}. Manual analysis required."
    
    async def _call_llm_async(self, prompt: str) -> str:
        """
        Call LLM asynchronously - supports Gemini, Bedrock, and fallback options
        """
        # Try Gemini first (1M token context, faster)
        if self.gemini_client:
            try:
                logger.info("Using Gemini 2.0 Flash for LLM analysis")
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.gemini_client.generate_content(prompt)
                )
                return response.text
            except Exception as e:
                logger.warning(f"Gemini LLM call failed: {e}, falling back to Bedrock")
        
        # Fallback to Bedrock
        if self.bedrock_client:
            try:
                logger.info("Using Bedrock for LLM analysis")
                response = self.bedrock_client.analyze_content(prompt)
                return response
            except Exception as e:
                logger.error(f"Bedrock LLM call failed: {e}")
                raise
        
        raise ValueError("No LLM client available for content analysis (Gemini or Bedrock required)")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize website URL"""
        if not url:
            raise ValueError("No website URL provided")
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url.rstrip('/')


# Synchronous wrapper for pipeline compatibility
class IntelligentCompanyScraperSync:
    """Synchronous wrapper for the intelligent scraper"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    def scrape_company(self, company_data: CompanyData, job_id: str = None) -> CompanyData:
        """Synchronous wrapper for intelligent company scraping"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.scraper.scrape_company_intelligent(company_data, job_id)
            )
            
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Intelligent scraping error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            
            # Complete job tracking if error
            if job_id:
                complete_company_processing(job_id, False, error=str(e))
            
            return company_data
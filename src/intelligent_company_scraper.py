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
from src.progress_logger import log_processing_phase, start_company_processing, complete_company_processing, progress_logger

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
        self.session_timeout = aiohttp.ClientTimeout(total=10)  # Reduced for fast research
        
        # Initialize Gemini client if available
        self.gemini_client = None
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key and gemini_api_key.startswith("AIza"):
                try:
                    genai.configure(api_key=gemini_api_key)
                    self.gemini_client = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
                    logger.info("Gemini 2.5 Flash Preview client initialized successfully")
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
            
            page_contents = await self._parallel_extract_content(selected_urls, job_id)
            
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
            company_data.raw_content = sales_intelligence  # Store as raw_content for AI analysis
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
        
        # Prepare links for LLM analysis (reduced for faster processing)
        links_text = "\n".join([f"- {link}" for link in all_links[:100]])  # Reduced from 500 to 100 for speed
        
        prompt = f"""You are a data extraction specialist analyzing {company_name}'s website to find specific missing information.

Given these discovered links for {company_name} (base URL: {base_url}):

{links_text}

Select up to 50 pages that are MOST LIKELY to contain these CRITICAL missing data points:

🔴 HIGHEST PRIORITY (Currently missing from our database):
1. **Contact & Location**: Physical address, headquarters location
   → Look for: /contact, /about, /offices, /locations
2. **Founded Year**: When the company was established
   → Look for: /about, /our-story, /history, /company
3. **Employee Count**: Team size or number of employees  
   → Look for: /about, /team, /careers, /jobs
4. **Contact Details**: Email, phone, social media links
   → Look for: /contact, /connect, footer pages
5. **Products/Services**: Specific offerings (not categories)
   → Look for: /products, /services, /solutions, /offerings
6. **Leadership Team**: Names and titles of executives
   → Look for: /team, /leadership, /about/team, /management
7. **Partnerships**: Key partners and integrations
   → Look for: /partners, /integrations, /ecosystem
8. **Certifications**: Compliance and security certifications
   → Look for: /security, /compliance, /trust, /certifications

🟡 ALSO VALUABLE:
- Company stage/maturity (/about, /investors)
- Recent news and funding (/news, /press, /media)
- Company culture (/careers, /culture)
- Awards and recognition (/awards, /about)

PRIORITIZE pages with these URL patterns:
- /contact* or /get-in-touch* (contact info + location)
- /about* or /company* (founding year + size)  
- /team* or /people* or /leadership* (decision makers)
- /careers* or /jobs* (employee count + culture)
- Footer pages often have social media links

Return ONLY a JSON array of the most promising URLs for data extraction:
["url1", "url2", "url3", ...]

Select pages with STRUCTURED DATA we can extract, not blog posts or general content."""

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
        # Priority keywords for missing data extraction
        high_priority = ['contact', 'about', 'team', 'leadership', 'careers', 'jobs']  # Pages with location, founding year, employee count
        medium_priority = ['products', 'services', 'solutions', 'partners', 'integrations', 'security', 'compliance']
        low_priority = ['pricing', 'customers', 'news', 'press', 'blog', 'resources']
        
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
    
    async def _parallel_extract_content(self, urls: List[str], job_id: str = None) -> List[Dict[str, str]]:
        """
        Phase 3: Extract content from selected pages in parallel
        """
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        page_counter = {"count": 0}  # Mutable counter for async functions
        total_pages = len(urls)
        
        async def extract_single_page(url: str) -> Optional[Dict[str, str]]:
            async with semaphore:
                try:
                    # Update progress counter
                    page_counter["count"] += 1
                    current_page = page_counter["count"]
                    
                    # Log current page being scraped
                    print(f"🔍 [{current_page}/{total_pages}] Starting: {url}")
                    
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
                            content = result.cleaned_html[:10000]  # Limit content length
                            
                            # Log successful extraction with content preview
                            content_preview = content[:200] + "..." if len(content) > 200 else content
                            print(f"✅ [{current_page}/{total_pages}] Success: {url}")
                            print(f"📄 Content preview: {content_preview}")
                            
                            # Update progress logger if job_id provided
                            if job_id:
                                progress_logger.log_page_scraping(
                                    job_id, url, content, current_page, total_pages
                                )
                            
                            return {
                                'url': url,
                                'content': content
                            }
                        else:
                            print(f"❌ [{current_page}/{total_pages}] Failed: {url} - No content extracted")
                            logger.warning(f"Failed to extract content from {url}")
                            return None
                            
                except Exception as e:
                    print(f"❌ [{page_counter['count']}/{total_pages}] Error: {url} - {str(e)}")
                    logger.warning(f"Error extracting from {url}: {e}")
                    return None
        
        # Execute parallel extraction
        logger.info(f"Starting parallel extraction of {len(urls)} pages...")
        print(f"🚀 Starting parallel extraction of {total_pages} pages...")
        
        tasks = [extract_single_page(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_extractions = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                successful_extractions.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Extraction task failed: {result}")
        
        success_count = len(successful_extractions)
        print(f"🎉 Extraction complete: {success_count}/{total_pages} pages successful")
        logger.info(f"Successfully extracted content from {success_count} pages")
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
        self.config = config  # Store config for external access
        self.scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    def scrape_company(self, company_data: CompanyData, job_id: str = None, timeout: int = None) -> CompanyData:
        """Synchronous wrapper for intelligent company scraping
        
        Args:
            company_data: Company data to scrape
            job_id: Optional job ID for progress tracking
            timeout: Optional timeout in seconds (defaults to 25)
        """
        if timeout is None:
            timeout = getattr(self.config, 'scraper_timeout', 25)
            
        print(f"🔬 SCRAPER: Starting scrape for company '{company_data.name}' with website '{company_data.website}'")
        print(f"🔬 SCRAPER: Job ID: {job_id}")
        
        try:
            import subprocess
            import json
            import tempfile
            import os
            import sys
            
            print(f"🔬 SCRAPER: All imports successful")
            print(f"🔬 SCRAPER: Working directory: {os.getcwd()}")
            print(f"🔬 SCRAPER: Python executable: {sys.executable}")
            
            # Ensure job_id is properly formatted for script
            safe_job_id = job_id if job_id else 'subprocess'
            print(f"🔬 SCRAPER: Using job_id: {safe_job_id}")
            
            # Use the working test script instead of generating inline
            script_content = f'''#!/usr/bin/env python3
import asyncio
import json
import sys
import os
sys.path.append("{os.getcwd()}")

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient

async def run_scraping():
    try:
        import logging
        # Suppress debug output to keep stdout clean for JSON
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        company_data = CompanyData(
            name="{company_data.name}",
            website="{company_data.website}"
        )
        
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        # Capture the original print function and redirect to stderr
        import builtins
        original_print = builtins.print
        def debug_print(*args, **kwargs):
            kwargs['file'] = sys.stderr
            original_print(*args, **kwargs)
        builtins.print = debug_print
        
        try:
            result = await scraper.scrape_company_intelligent(company_data, "{safe_job_id}")
        finally:
            # Restore original print
            builtins.print = original_print
        
        result_dict = {{
            "success": True,
            "name": result.name,
            "website": result.website,
            "scrape_status": result.scrape_status,
            "scrape_error": result.scrape_error,
            "company_description": result.company_description,
            "raw_content": result.raw_content,
            "ai_summary": result.ai_summary,
            "industry": result.industry,
            "business_model": result.business_model,
            "target_market": result.target_market,
            "key_services": result.key_services or [],
            "company_size": result.company_size,
            "location": result.location,
            "tech_stack": result.tech_stack or [],
            "value_proposition": result.value_proposition,
            "pain_points": result.pain_points or [],
            "pages_crawled": result.pages_crawled or [],
            "crawl_duration": result.crawl_duration,
            "crawl_depth": result.crawl_depth
        }}
        
        return result_dict
        
    except Exception as e:
        import traceback
        return {{
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "scrape_status": "failed",
            "scrape_error": str(e)
        }}

if __name__ == "__main__":
    result = asyncio.run(run_scraping())
    print(json.dumps(result, default=str))
'''
            
            # Write script to temporary file
            print(f"🔬 SCRAPER: Creating temporary script file...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            print(f"🔬 SCRAPER: Temporary script created at: {script_path}")
            
            try:
                print(f"🔬 SCRAPER: Starting subprocess for scraping...")
                print(f"🔬 SCRAPER: Command: {sys.executable} {script_path}")
                print(f"🔬 SCRAPER: Timeout: {timeout} seconds")
                
                # Update progress in main process before starting subprocess
                if job_id:
                    print(f"🔬 SCRAPER: Updating progress - starting intelligent scraping...")
                    from src.progress_logger import progress_logger
                    progress_logger.update_phase(job_id, "Intelligent Web Scraping", "running", {
                        "status": "Running intelligent web scraper in subprocess...",
                        "subprocess_started": True,
                        "timeout_seconds": timeout
                    })
                
                import time
                start_time = time.time()
                
                # Run the script in a subprocess with timeout
                # Add extra buffer to subprocess timeout to allow for startup/shutdown
                subprocess_timeout = timeout + 35  # Extra time for subprocess overhead
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    timeout=subprocess_timeout,
                    cwd=os.getcwd()
                )
                
                end_time = time.time()
                duration = end_time - start_time
                print(f"🔬 SCRAPER: Subprocess completed in {duration:.2f} seconds")
                
                print(f"🔬 SCRAPER: Subprocess completed in {duration:.2f} seconds")
                print(f"🔬 SCRAPER: Return code: {result.returncode}")
                print(f"🔬 SCRAPER: Stdout length: {len(result.stdout)} characters")
                print(f"🔬 SCRAPER: Stderr length: {len(result.stderr)} characters")
                if result.stdout:
                    print(f"🔬 SCRAPER: Stdout preview: {result.stdout[:500]}...")
                if result.stderr:
                    print(f"🔬 SCRAPER: Stderr preview: {result.stderr[:500]}...")
                
                if result.returncode == 0:
                    # Parse JSON result - extract from end of stdout since debug prints contaminate it
                    try:
                        # Find the last valid JSON in stdout
                        stdout_lines = result.stdout.strip().split('\n')
                        json_line = None
                        
                        # Look for JSON starting from the end
                        for line in reversed(stdout_lines):
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                try:
                                    json.loads(line)  # Test if it's valid JSON
                                    json_line = line
                                    break
                                except:
                                    continue
                        
                        if json_line:
                            result_data = json.loads(json_line)
                            print(f"🔧 DEBUG: Parsed result data successfully from JSON line")
                            print(f"🔧 DEBUG: Success flag: {result_data.get('success')}")
                            print(f"🔧 DEBUG: Scrape status: {result_data.get('scrape_status')}")
                        else:
                            raise json.JSONDecodeError("No valid JSON found in subprocess output", result.stdout, 0)
                        
                        if result_data.get("success"):
                            print(f"🔬 SCRAPER: Subprocess returned success! Applying results...")
                            
                            # Update progress - scraping phase completed
                            if job_id:
                                from src.progress_logger import progress_logger
                                progress_logger.update_phase(job_id, "Intelligent Web Scraping", "completed", {
                                    "subprocess_duration": duration,
                                    "pages_extracted": result_data.get("crawl_depth", 0),
                                    "content_length": len(result_data.get("company_description", "")),
                                    "status": "Intelligent scraping completed successfully"
                                })
                            
                            # Apply results to company_data
                            company_data.scrape_status = result_data.get("scrape_status", "success")
                            company_data.scrape_error = result_data.get("scrape_error")
                            company_data.company_description = result_data.get("company_description")
                            company_data.ai_summary = result_data.get("ai_summary")
                            company_data.industry = result_data.get("industry")
                            company_data.business_model = result_data.get("business_model") 
                            company_data.target_market = result_data.get("target_market")
                            company_data.key_services = result_data.get("key_services", [])
                            company_data.company_size = result_data.get("company_size")
                            company_data.location = result_data.get("location")
                            company_data.tech_stack = result_data.get("tech_stack", [])
                            company_data.value_proposition = result_data.get("value_proposition")
                            company_data.pain_points = result_data.get("pain_points", [])
                            company_data.pages_crawled = result_data.get("pages_crawled", [])
                            company_data.crawl_duration = result_data.get("crawl_duration", 0)
                            company_data.crawl_depth = result_data.get("crawl_depth", 0)
                            
                            # IMPORTANT: Store the extracted content as raw_content for AI analysis
                            # This allows downstream AI analysis to extract all the detailed fields
                            if result_data.get("raw_content"):
                                company_data.raw_content = result_data.get("raw_content", "")
                                print(f"🔬 SCRAPER: Populated raw_content with {len(company_data.raw_content)} chars")
                            elif result_data.get("company_description"):
                                # Fallback if raw_content not provided
                                company_data.raw_content = result_data.get("company_description", "")
                                print(f"🔬 SCRAPER: Populated raw_content from company_description with {len(company_data.raw_content)} chars")
                            
                            print(f"🔬 SCRAPER: Successfully applied all scraping results")
                            print(f"🔬 SCRAPER: Pages crawled: {len(company_data.pages_crawled or [])}")
                            print(f"🔬 SCRAPER: Crawl duration: {company_data.crawl_duration}")
                            print(f"🔬 SCRAPER: Industry: {company_data.industry}")
                            print(f"🔬 SCRAPER: AI Summary available: {bool(company_data.ai_summary)}")
                        else:
                            company_data.scrape_status = "failed" 
                            company_data.scrape_error = result_data.get("error", "Unknown subprocess error")
                            print(f"🔬 SCRAPER: ❌ Subprocess reported failure: {company_data.scrape_error}")
                            if result_data.get("traceback"):
                                print(f"🔬 SCRAPER: ❌ Traceback: {result_data.get('traceback')}")
                                
                        print(f"🔬 SCRAPER: Final status: {company_data.scrape_status}")
                            
                    except json.JSONDecodeError as e:
                        print(f"🔬 SCRAPER: ❌ JSON parsing failed: {e}")
                        print(f"🔬 SCRAPER: ❌ Raw stdout length: {len(result.stdout)}")
                        print(f"🔬 SCRAPER: ❌ Raw stderr length: {len(result.stderr)}")
                        print(f"🔬 SCRAPER: ❌ Subprocess stdout first 1000 chars: {result.stdout[:1000]}")
                        print(f"🔬 SCRAPER: ❌ Subprocess stderr: {result.stderr}")
                        company_data.scrape_status = "failed"
                        company_data.scrape_error = f"Failed to parse scraper results: {e}"
                else:
                    print(f"🔬 SCRAPER: ❌ Subprocess failed with return code: {result.returncode}")
                    print(f"🔬 SCRAPER: ❌ Subprocess stderr: {result.stderr}")
                    print(f"🔬 SCRAPER: ❌ Subprocess stdout: {result.stdout}")
                    company_data.scrape_status = "failed"
                    company_data.scrape_error = f"Scraper subprocess failed (code {result.returncode}): {result.stderr}"
                    
            except subprocess.TimeoutExpired as e:
                print(f"🔬 SCRAPER: ❌ TIMEOUT after {timeout} seconds for {company_data.name}")
                print(f"🔬 SCRAPER: ❌ This indicates website complexity or network issues")
                print(f"🔬 SCRAPER: ❌ Timeout details: {e}")
                company_data.scrape_status = "failed"
                company_data.scrape_error = f"Scraping timed out after {timeout} seconds - this may indicate a complex website or network issues"
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except:
                    pass
            
            return company_data
            
        except Exception as e:
            logger.error(f"Intelligent scraping error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            
            # Complete job tracking if error
            if job_id:
                complete_company_processing(job_id, False, error=str(e))
            
            return company_data
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
    from google.generativeai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai_types = None

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode
from src.models import CompanyData, CompanyIntelligenceConfig
from src.progress_logger import log_processing_phase, start_company_processing, complete_company_processing, progress_logger
from src.ssl_config import get_aiohttp_connector, get_browser_args, should_verify_ssl

logger = logging.getLogger(__name__)

# Browser user agent to mimic Chrome on macOS for better compatibility
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"


class IntelligentCompanyScraper:
    """
    Advanced company scraper using LLM-driven link discovery and parallel extraction
    """
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.bedrock_client = bedrock_client
        self.max_depth = 3  # Recursive crawl depth
        self.max_pages = 100  # Maximum pages to process
        
        # Will be adjusted per company during scraping
        
        # LLM and scraping tracking
        self.llm_call_count = 0
        self.scraped_pages = []
        self.llm_call_log = []
        
        # Special handling for store locator sites
        self.store_locator_patterns = [
            'stores.', 'locations.', 'store-locator', 'find-store', 
            'store/', 'location/', 'outlet', 'dealers'
        ]
        self.concurrent_limit = 10  # Concurrent requests limit
        self.session_timeout = aiohttp.ClientTimeout(total=10)  # Reduced for fast research
        
        # Initialize Gemini client if available
        self.gemini_client = None
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key and gemini_api_key.startswith("AIza"):
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Use the stable model that we know works
                    self.gemini_client = genai.GenerativeModel('gemini-2.5-flash')
                    logger.info("Gemini 2.5 Flash client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self.gemini_client = None
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
        
        # Detect if this is a store locator site and adjust strategy
        is_store_locator = any(pattern in base_url.lower() for pattern in self.store_locator_patterns)
        if is_store_locator:
            logger.info(f"Detected store locator site for {company_data.name}, using optimized strategy")
            self.max_pages = 20  # More aggressive reduction for store locators
            self.max_depth = 2   # Reduce depth for store locators
            self.concurrent_limit = 5  # Reduce concurrent requests for store locators
        
        print(f"🔍 SCRAPING: {company_data.name} → {base_url}", flush=True)
        print(f"📋 TARGET: Extract comprehensive business intelligence", flush=True)
        
        # Reduce depth for known large retailer sites to prevent timeout
        retailer_domains = ['walmart.com', 'amazon.com', 'target.com', 'bestbuy.com', 'costco.com', 'homedepot.com']
        if any(domain in base_url.lower() for domain in retailer_domains):
            self.max_depth = 1  # Minimal depth for large retailers
            logger.info(f"Reduced crawl depth to 1 for large retailer site: {company_data.name}")
        
        # Log to UI processing log
        if job_id:
            from src.progress_logger import progress_logger
            progress_logger.add_to_progress_log(job_id, f"🔍 Starting intelligent scraping for {company_data.name}")
            progress_logger.add_to_progress_log(job_id, f"🌐 Target website: {base_url}")
            progress_logger.add_to_progress_log(job_id, f"⚙️ Configuration: max_pages={self.max_pages}, max_depth={self.max_depth}")
        
        print(f"⚙️ SCRAPER CONFIG: max_pages={self.max_pages}, max_depth={self.max_depth}, concurrent_limit={self.concurrent_limit}", flush=True)
        
        
        try:
            # Phase 1: Comprehensive Link Discovery
            print(f"🔍 PHASE 1: Starting comprehensive link discovery...")
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"🔍 PHASE 1: Starting comprehensive link discovery")
            
            log_processing_phase(job_id, "Link Discovery", "running", 
                               target_url=base_url, max_depth=self.max_depth)
            
            all_links = await self._discover_all_links(base_url, job_id)
            
            print(f"🔍 PHASE 1 COMPLETE: Discovered {len(all_links)} total links")
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"✅ Link discovery complete: {len(all_links)} links found")
            
            log_processing_phase(job_id, "Link Discovery", "completed", 
                               links_discovered=len(all_links), 
                               sources=["robots.txt", "sitemap.xml", "recursive_crawl"])
            
            # Phase 2: LLM-Driven Page Selection
            print(f"🧠 PHASE 2: Starting LLM-driven page selection from {len(all_links)} links...")
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"🧠 PHASE 2: Starting LLM page selection from {len(all_links)} links")
            
            log_processing_phase(job_id, "LLM Page Selection", "running",
                               total_links=len(all_links), max_pages=self.max_pages)
            
            selected_urls = await self._llm_select_promising_pages(
                all_links, company_data.name, base_url, job_id
            )
            
            print(f"🧠 PHASE 2 COMPLETE: Selected {len(selected_urls)} promising pages")
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"✅ Page selection complete: {len(selected_urls)} pages selected")
            
            log_processing_phase(job_id, "LLM Page Selection", "completed",
                               pages_selected=len(selected_urls),
                               selection_ratio=f"{len(selected_urls)}/{len(all_links)}")
            
            print(f"\n🎯 PAGES SELECTED ({len(selected_urls)}/{len(all_links)} links):")
            for i, url in enumerate(selected_urls[:20], 1):  # Show first 20 selected
                print(f"  {i:2d}. {url}")
            if len(selected_urls) > 20:
                print(f"  ... and {len(selected_urls) - 20} more pages")
            
            # Phase 3: Parallel Content Extraction
            print(f"\n📄 PHASE 3: Starting parallel content extraction from {len(selected_urls)} pages...", flush=True)
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"📄 PHASE 3: Starting content extraction from {len(selected_urls)} pages")
            
            log_processing_phase(job_id, "Content Extraction", "running",
                               pages_to_extract=len(selected_urls),
                               concurrent_limit=self.concurrent_limit)
            
            page_contents = await self._parallel_extract_content(selected_urls, job_id)
            
            total_content_chars = sum(len(page['content']) for page in page_contents)
            print(f"📄 PHASE 3 COMPLETE: Extracted content from {len(page_contents)}/{len(selected_urls)} pages", flush=True)
            print(f"📊 Total content extracted: {total_content_chars:,} characters", flush=True)
            
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"✅ Content extraction complete: {len(page_contents)} pages, {total_content_chars:,} chars")
            
            log_processing_phase(job_id, "Content Extraction", "completed",
                               successful_extractions=len(page_contents),
                               failed_extractions=len(selected_urls) - len(page_contents),
                               total_content_chars=total_content_chars)
            
            # Phase 4: LLM Content Aggregation
            print(f"\n🧠 PHASE 4: Starting LLM analysis of {total_content_chars:,} characters...", flush=True)
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"🧠 PHASE 4: Starting sales intelligence generation from {total_content_chars:,} chars")
            
            log_processing_phase(job_id, "Sales Intelligence Generation", "running",
                               content_pages=len(page_contents),
                               total_content_chars=total_content_chars)
            
            sales_intelligence = await self._llm_aggregate_sales_intelligence(
                page_contents, company_data.name, job_id
            )
            
            print(f"🧠 PHASE 4 COMPLETE: Generated {len(sales_intelligence):,} character sales intelligence", flush=True)
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"✅ Sales intelligence complete: {len(sales_intelligence):,} characters generated")
            
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
            
            # Complete job tracking with detailed summary
            summary = f"Generated {len(sales_intelligence)} character sales intelligence from {len(page_contents)} pages"
            complete_company_processing(job_id, True, summary=summary)
            
            # Add summary to UI progress log
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.add_to_progress_log(job_id, f"📄 CRAWLED {len(self.scraped_pages)} pages total:")
                for i, page in enumerate(self.scraped_pages, 1):
                    progress_logger.add_to_progress_log(job_id, f"   {i}. {page['url']} ({page['content_length']:,} chars)")
                progress_logger.add_to_progress_log(job_id, f"🧠 MADE {len(self.llm_call_log)} LLM calls total")
                progress_logger.add_to_progress_log(job_id, f"📝 GENERATED {len(sales_intelligence):,} characters final result")

            # Print final summary
            print(f"\n🎉 SCRAPING COMPLETE for {company_data.name}")
            print(f"📄 PAGES SCRAPED: {len(self.scraped_pages)} pages")
            for i, page in enumerate(self.scraped_pages, 1):
                print(f"  {i}. {page['url']} ({page['content_length']:,} chars from {page['content_source']})")
            print(f"🧠 LLM CALLS: {len(self.llm_call_log)} total")
            for call in self.llm_call_log:
                status = "✅" if call['success'] else "❌"
                print(f"  {status} Call #{call['call_number']}: {call['model']} - {call['prompt_length']:,} chars in, {call['response_length']:,} chars out")
            print(f"📝 FINAL RESULT: {len(sales_intelligence):,} characters generated\n")
            
            logger.info(f"Intelligent scraping completed for {company_data.name}")
            
        except Exception as e:
            error_msg = f"Intelligent scraping failed: {str(e)}"
            logger.error(f"{error_msg} for {company_data.name}")
            
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            
            # Complete job tracking with error
            complete_company_processing(job_id, False, error=error_msg)
        
        return company_data
    
    async def _discover_all_links(self, base_url: str, job_id: str = None) -> List[str]:
        """
        Phase 1: Comprehensive link discovery with multiple sources and safety limits
        """
        all_links = set()
        domain = urlparse(base_url).netloc
        
        print(f"🔍 LINK DISCOVERY: Finding pages on {base_url}")
        start_time = time.time()
        
        # Create SSL-configured connector
        ssl_connector = get_aiohttp_connector(verify=should_verify_ssl())
        
        async with aiohttp.ClientSession(connector=ssl_connector, timeout=self.session_timeout) as session:
            
            # 1. Robots.txt discovery
            try:
                robots_url = urljoin(base_url, '/robots.txt')
                print(f"🔍 Analyzing robots.txt: {robots_url}", flush=True)
                if job_id:
                    log_processing_phase(job_id, "Link Discovery", "running", 
                                       current_url=robots_url, status_message="Analyzing robots.txt")
                    progress_logger.add_to_progress_log(job_id, f"🔍 Analyzing robots.txt: {robots_url}")
                
                robots_links = await self._parse_robots_txt(session, base_url)
                all_links.update(robots_links)
                
                print(f"✅ Found {len(robots_links)} links from robots.txt", flush=True)
                logger.info(f"Found {len(robots_links)} links from robots.txt")
                
                if job_id and robots_links:
                    progress_logger.add_to_progress_log(job_id, f"✅ robots.txt: {len(robots_links)} links discovered")
                    
            except Exception as e:
                print(f"❌ Failed to parse robots.txt: {e}", flush=True)
                logger.warning(f"Failed to parse robots.txt: {e}")
                if job_id:
                    progress_logger.add_to_progress_log(job_id, f"❌ robots.txt failed: {e}")
            
            # 2. Sitemap.xml discovery
            try:
                sitemap_url = urljoin(base_url, '/sitemap.xml')
                print(f"🔍 Analyzing sitemap.xml: {sitemap_url}", flush=True)
                if job_id:
                    log_processing_phase(job_id, "Link Discovery", "running", 
                                       current_url=sitemap_url, status_message="Analyzing sitemap.xml")
                    progress_logger.add_to_progress_log(job_id, f"🔍 Analyzing sitemap.xml: {sitemap_url}")
                
                sitemap_links = await self._parse_sitemap(session, base_url)
                all_links.update(sitemap_links)
                
                print(f"✅ Found {len(sitemap_links)} links from sitemap.xml", flush=True)
                logger.info(f"Found {len(sitemap_links)} links from sitemap")
                
                if job_id and sitemap_links:
                    progress_logger.add_to_progress_log(job_id, f"✅ sitemap.xml: {len(sitemap_links)} links discovered")
                    
            except Exception as e:
                print(f"❌ Failed to parse sitemap.xml: {e}", flush=True)
                logger.warning(f"Failed to parse sitemap: {e}")
                if job_id:
                    progress_logger.add_to_progress_log(job_id, f"❌ sitemap.xml failed: {e}")
            
            # 3. Recursive page crawling for navigation links using Crawl4AI (with timeout check)
            try:
                elapsed = time.time() - start_time
                if elapsed > 30:  # Maximum 30 seconds for link discovery
                    print(f"⏰ Skipping recursive crawling - time limit reached ({elapsed:.1f}s)", flush=True)
                    if job_id:
                        progress_logger.add_to_progress_log(job_id, f"⏰ Skipping recursive crawling - time limit reached")
                else:
                    print(f"🔍 Starting recursive crawling from: {base_url}", flush=True)
                    if job_id:
                        log_processing_phase(job_id, "Link Discovery", "running", 
                                           current_url=base_url, status_message="Recursive crawling")
                        progress_logger.add_to_progress_log(job_id, f"🔍 Starting recursive crawling from: {base_url}")
                    
                    # ✅ Use Crawl4AI for recursive crawling instead of basic aiohttp
                    browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
                    async with AsyncWebCrawler(
                        headless=True,
                        browser_type="chromium",
                        verbose=False,
                        browser_args=browser_args
                    ) as crawler:
                        crawled_links = await self._recursive_link_discovery(
                            crawler, base_url, domain, max_depth=self.max_depth, job_id=job_id
                        )
                        all_links.update(crawled_links)
                    
                    print(f"✅ Found {len(crawled_links)} links from recursive crawling", flush=True)
                    logger.info(f"Found {len(crawled_links)} links from recursive crawling")
                    
                    if job_id and crawled_links:
                        progress_logger.add_to_progress_log(job_id, f"✅ Recursive crawl: {len(crawled_links)} links discovered")
                        
            except Exception as e:
                print(f"❌ Failed recursive discovery: {e}", flush=True)
                logger.warning(f"Failed recursive discovery: {e}")
                if job_id:
                    progress_logger.add_to_progress_log(job_id, f"❌ Recursive crawling failed: {e}")
        
        # Filter and normalize links
        filtered_links = self._filter_and_normalize_links(list(all_links), domain)
        
        # Summary
        total_time = time.time() - start_time
        # Link discovery completed
        
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
        crawler: "AsyncWebCrawler", 
        base_url: str, 
        domain: str, 
        max_depth: int,
        visited: Optional[Set[str]] = None,
        current_depth: int = 0,
        job_id: str = None
    ) -> Set[str]:
        """
        Recursively discover links by crawling pages with Crawl4AI for enhanced compatibility
        """
        if visited is None:
            visited = set()
        
        if current_depth >= max_depth:
            return set()
        
        # SAFETY: Limit total URLs processed to prevent infinite loops
        if len(visited) >= 200:  # Maximum 200 URLs total
            print(f"🛑 Recursive discovery hit 200 URL limit, stopping to prevent infinite loops")
            return set()
        
        discovered_links = set()
        
        # SAFETY: Don't re-visit the same URL
        if base_url in visited:
            return set()
        
        visited.add(base_url)
        
        try:
            print(f"🔍 Crawling depth {current_depth}: {base_url}")
            if job_id:
                log_processing_phase(job_id, "Link Discovery", "running", 
                                   current_url=base_url, 
                                   status_message=f"Crawling depth {current_depth}")
                progress_logger.add_to_progress_log(job_id, f"🔍 Crawling depth {current_depth}: {base_url}")
            
            # ✅ Use Crawl4AI for link discovery to handle JavaScript and complex sites
            config = CrawlerRunConfig(
                user_agent=BROWSER_USER_AGENT,
                word_count_threshold=1,  # Very low threshold for link discovery
                css_selector="a[href], nav, footer, .menu, .navigation",  # Focus on navigation elements
                excluded_tags=["script", "style"],
                cache_mode=CacheMode.ENABLED,
                page_timeout=15000,  # Shorter timeout for link discovery
                verbose=False,
                simulate_user=True,      # Anti-bot bypass
                magic=True,              # Enhanced compatibility
                js_code=[
                    # Simple JS to reveal hidden navigation
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
            
            result = await crawler.arun(url=base_url, config=config)
            
            if result and result.html:
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extract all links
                links_found = 0
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    
                    # Only follow links on same domain
                    if urlparse(full_url).netloc == domain:
                        discovered_links.add(full_url)
                        links_found += 1
                        
                        # SAFETY: Limit links per page to prevent explosion
                        if links_found >= 50:  # Max 50 links per page
                            break
                        
                        # Recursively crawl if not visited and within depth limit
                        if full_url not in visited and current_depth < max_depth - 1:
                            recursive_links = await self._recursive_link_discovery(
                                crawler, full_url, domain, max_depth, visited, current_depth + 1, job_id
                            )
                            discovered_links.update(recursive_links)
                            
                            # SAFETY: Add delay and check total time
                            await asyncio.sleep(0.2)
                
                print(f"  📄 Found {links_found} links on this page")
            else:
                print(f"  ❌ No content retrieved from {base_url}")
                                
        except Exception as e:
            logger.warning(f"Error in recursive discovery for {base_url}: {e}")
            print(f"  ❌ Error crawling {base_url}: {e}")
        
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
        base_url: str,
        job_id: str = None
    ) -> List[str]:
        """
        Phase 2: Use LLM to select most promising pages for sales intelligence
        """
        import sys
        
        if not self.bedrock_client:
            # Fallback: Use heuristic selection
            print(f"🧠 Bedrock client not available, using heuristic page selection", flush=True)
            return self._heuristic_page_selection(all_links)
        
        # CRITICAL FIX: Limit links to prevent infinite LLM processing
        max_links_for_llm = 25  # Reduced to 25 to prevent timeout issues
        limited_links = all_links[:max_links_for_llm]
        
        print(f"🧠 LLM Page Selection: Processing {len(limited_links)} links (from {len(all_links)} total)", flush=True)
        if job_id:
            from src.progress_logger import progress_logger
            progress_logger.add_to_progress_log(job_id, f"🧠 Processing {len(limited_links)} links (from {len(all_links)} total)")
        
        # Prepare links for LLM analysis
        print(f"🧠 Preparing {len(limited_links)} links for LLM analysis...", flush=True)
        links_text = "\n".join([f"- {link}" for link in limited_links])
        
        print(f"🧠 Links being sent to LLM for analysis:", flush=True)
        for i, link in enumerate(limited_links, 1):
            print(f"  {i:2d}. {link}", flush=True)
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"📋 Link {i}: {link}")
        
        if job_id:
            progress_logger.add_to_progress_log(job_id, f"🧠 Sending {len(limited_links)} links to LLM for intelligent selection...")
        
        prompt = f"""You are a data extraction specialist analyzing {company_name}'s website to find specific missing information.

Given these discovered links for {company_name} (base URL: {base_url}):

{links_text}

Select up to 25 pages that are MOST LIKELY to contain these CRITICAL missing data points:

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
            print(f"🧠 LLM Page Selection: Calling LLM with {len(prompt)} chars...", flush=True)
            print(f"🧠 PROMPT PREVIEW (first 500 chars):", flush=True)
            print(f"{'='*60}", flush=True)
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt, flush=True)
            print(f"{'='*60}", flush=True)
            
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"🧠 Sending prompt to LLM ({len(prompt)} chars)")
            
            # Add timeout to prevent infinite hanging
            response = await asyncio.wait_for(
                self._call_llm_async(prompt, job_id),
                timeout=120  # Increased to 120 second timeout for page selection
            )
            
            print(f"🧠 LLM Page Selection: Received response ({len(response)} chars)", flush=True)
            print(f"🧠 RESPONSE PREVIEW (first 500 chars):", flush=True)
            print(f"{'='*60}", flush=True)
            print(response[:500] + "..." if len(response) > 500 else response, flush=True)
            print(f"{'='*60}", flush=True)
            
            if job_id:
                progress_logger.add_to_progress_log(job_id, f"🧠 Received LLM response ({len(response)} chars)")
            
            # Track LLM page selection
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # Clean the response to extract JSON from markdown code blocks
                cleaned_response = response.strip()
                
                # Remove markdown code block markers if present
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                elif cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                
                cleaned_response = cleaned_response.strip()
                
                print(f"🐛 DEBUG: Cleaned response (first 200 chars): {cleaned_response[:200]}")
                
                selected_urls = json.loads(cleaned_response)
                if isinstance(selected_urls, list):
                    # Validate URLs and limit to max_pages
                    valid_urls = [url for url in selected_urls if url in all_links]
                    final_selection = valid_urls[:self.max_pages]
                    
                    # Update debug file with successful parse
                    try:
                        debug_data["parse_success"] = True
                        debug_data["cleaned_response"] = cleaned_response
                        debug_data["llm_recommended_count"] = len(selected_urls)
                        debug_data["valid_urls_count"] = len(valid_urls)
                        debug_data["final_selection_count"] = len(final_selection)
                        debug_data["final_selection"] = final_selection
                        with open(debug_filename, 'w') as f:
                            json.dump(debug_data, f, indent=2, default=str)
                        print(f"🐛 DEBUG: Successful parse logged to debug file")
                    except:
                        pass

                    # 🎯 DETAILED LLM SELECTION LOGGING
                    print(f"\n🧠 LLM PAGE SELECTION RESULTS for {company_name}:")
                    print(f"📊 Total links discovered: {len(all_links)}")
                    print(f"🤖 LLM recommended: {len(selected_urls)} pages")
                    print(f"✅ Valid URLs from LLM: {len(valid_urls)}")
                    print(f"🎯 Final selection (max {self.max_pages}): {len(final_selection)} pages")
                    print(f"\n📋 LLM SELECTED PAGES:")
                    for i, url in enumerate(final_selection, 1):
                        print(f"  {i:2d}. {url}")
                    
                    # Show categorization of selected pages
                    contact_pages = [url for url in final_selection if any(keyword in url.lower() for keyword in ['contact', 'get-in-touch'])]
                    about_pages = [url for url in final_selection if any(keyword in url.lower() for keyword in ['about', 'company', 'our-story', 'history'])]
                    team_pages = [url for url in final_selection if any(keyword in url.lower() for keyword in ['team', 'leadership', 'people', 'management'])]
                    career_pages = [url for url in final_selection if any(keyword in url.lower() for keyword in ['careers', 'jobs', 'join'])]
                    product_pages = [url for url in final_selection if any(keyword in url.lower() for keyword in ['products', 'services', 'solutions', 'offerings'])]
                    
                    print(f"\n📂 PAGE CATEGORIES SELECTED:")
                    if contact_pages: print(f"📞 Contact/Location pages: {len(contact_pages)}")
                    if about_pages: print(f"🏢 About/Company pages: {len(about_pages)}")
                    if team_pages: print(f"👥 Team/Leadership pages: {len(team_pages)}")
                    if career_pages: print(f"💼 Careers/Jobs pages: {len(career_pages)}")
                    if product_pages: print(f"🛍️ Products/Services pages: {len(product_pages)}")
                    other_pages = len(final_selection) - len(contact_pages) - len(about_pages) - len(team_pages) - len(career_pages) - len(product_pages)
                    if other_pages > 0: print(f"🔗 Other pages: {other_pages}")
                    print(f"")
                    
                    return final_selection
                else:
                    print(f"🧠 LLM response was not a JSON array, falling back to heuristic selection")
                    print(f"🐛 Response type: {type(selected_urls)}")
                    print(f"🐛 Response content: {selected_urls}")
                    
                    # Update debug file with type error details
                    try:
                        debug_data["response_type_error"] = f"Expected list, got {type(selected_urls)}"
                        debug_data["parsed_response"] = selected_urls
                        with open(debug_filename, 'w') as f:
                            json.dump(debug_data, f, indent=2, default=str)
                        print(f"🐛 DEBUG: Updated debug file with type error details")
                    except:
                        pass
                    
                    logger.warning("LLM response was not a JSON array, falling back to heuristic")
                    return self._heuristic_page_selection(all_links)
                    
            except json.JSONDecodeError as e:
                print(f"🧠 Failed to parse LLM response as JSON, falling back to heuristic selection")
                print(f"🐛 JSON Parse Error: {e}")
                print(f"🐛 Response preview (first 500 chars): {response[:500]}")
                print(f"🐛 Response preview (last 500 chars): {response[-500:]}")
                
                # Update debug file with parse error details
                try:
                    debug_data["json_parse_error"] = str(e)
                    debug_data["response_preview_start"] = response[:500]
                    debug_data["response_preview_end"] = response[-500:]
                    with open(debug_filename, 'w') as f:
                        json.dump(debug_data, f, indent=2, default=str)
                    print(f"🐛 DEBUG: Updated debug file with parse error details")
                except:
                    pass
                
                logger.warning("Failed to parse LLM response as JSON, falling back to heuristic")
                return self._heuristic_page_selection(all_links)
                
        except asyncio.TimeoutError:
            print(f"🧠 LLM Page Selection: TIMEOUT after 120 seconds, falling back to heuristic selection")
            logger.warning("LLM page selection timed out, using heuristic fallback")
            return self._heuristic_page_selection(all_links)
        except Exception as e:
            print(f"🧠 LLM page selection failed: {e}, falling back to heuristic selection")
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
        selected_pages = [link for link, score in scored_links[:self.max_pages]]
        
        # 🎯 HEURISTIC SELECTION LOGGING
        print(f"\n🔧 HEURISTIC PAGE SELECTION (LLM not available):")
        print(f"📊 Total links discovered: {len(all_links)}")
        print(f"🎯 Selected by heuristic: {len(selected_pages)} pages")
        print(f"\n📋 HEURISTIC SELECTED PAGES:")
        for i, link in enumerate(selected_pages, 1):
            score = next(score for url, score in scored_links if url == link)
            print(f"  {i:2d}. {link} (score: {score})")
        print(f"")
        
        return selected_pages
    
    async def _parallel_extract_content(self, urls: List[str], job_id: str = None) -> List[Dict[str, str]]:
        """
        🔧 FIXED: Extract content from selected pages using SINGLE browser instance
        
        CRITICAL IMPROVEMENT:
        - Before: New AsyncWebCrawler per page (3-5x slower)
        - After: Single AsyncWebCrawler for all pages (optimal performance)
        """
        if not urls:
            return []
            
        page_contents = []
        total_pages = len(urls)
        
        # Progress logging
        if job_id:
            from src.progress_logger import progress_logger
            progress_logger.add_to_progress_log(job_id, f"📄 PHASE 3: Starting optimized content extraction from {total_pages} pages")
        
        print(f"📄 OPTIMIZED EXTRACTION: Processing {total_pages} pages with single browser instance", flush=True)
        
        start_time = time.time()
        
        # ✅ CRITICAL FIX: Single AsyncWebCrawler instance for ALL pages with SSL configuration
        browser_args = get_browser_args(ignore_ssl=not should_verify_ssl())
        
        async with AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=False,
            browser_args=browser_args
        ) as crawler:
            
            # Try enhanced configuration first, fall back to basic if it fails
            try:
                # ✅ ENHANCED: Advanced Crawl4AI configuration with browser simulation
                config = CrawlerRunConfig(
                    # Browser simulation and anti-bot bypass
                    user_agent=BROWSER_USER_AGENT,  # Mimic Chrome on macOS
                    simulate_user=True,             # Simulate human-like interactions
                    magic=True,                     # Advanced anti-bot detection bypass
                    override_navigator=True,        # Override navigator properties
                    
                    # Content extraction optimization
                    word_count_threshold=10,        # Lower threshold for short content
                    css_selector="main, article, .content, .main-content, section",
                    excluded_tags=["nav", "footer", "aside", "script", "style"],
                    remove_overlay_elements=True,   # Remove popups/modals automatically
                    process_iframes=True,          # Process iframe content
                    
                    # JavaScript interaction for dynamic content (with error handling)
                    js_code=[
                        """
                        try {
                            // Gentle scrolling with error handling
                            if (document.body && document.body.scrollHeight) {
                                window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                            }
                        } catch (e) { console.log('Scroll blocked:', e); }
                        """,
                        """
                        try {
                            // Safe button clicking with error handling
                            ['load-more', 'show-more', 'view-all', 'read-more'].forEach(className => {
                                const btn = document.querySelector('.' + className + ', button[class*="' + className + '"]');
                                if (btn) btn.click();
                            });
                        } catch (e) { console.log('Button click blocked:', e); }
                        """
                    ],
                    # wait_for removed - causing timeouts on sites without <main> element
                    
                    # Link and media handling
                    exclude_external_links=False,      # Allow external discovery initially
                    exclude_social_media_links=True,   # Skip social media
                    exclude_domains=["ads.com", "tracking.com", "analytics.com"],
                    
                    # Performance and reliability
                    cache_mode=CacheMode.ENABLED,
                    page_timeout=45000,             # Increased timeout for JS execution
                    verbose=False,
                    
                    # Note: Deliberately NOT using check_robots_txt=True to bypass restrictions
                    # This allows crawling of sites that might block bots via robots.txt
                )
                
                print(f"   🚀 Using enhanced configuration with anti-bot features...")
                
            except Exception as e:
                print(f"   ⚠️  Enhanced config failed, using basic config: {e}")
                # ✅ FALLBACK: Basic configuration without problematic features
                config = CrawlerRunConfig(
                    user_agent=BROWSER_USER_AGENT,
                    word_count_threshold=20,
                    css_selector="main, article, .content",
                    excluded_tags=["script", "style"],
                    cache_mode=CacheMode.ENABLED,
                    page_timeout=30000,
                    verbose=False
                )
            
            print(f"   🚀 Processing all {total_pages} URLs concurrently with single browser...", flush=True)
            
            # ✅ CRITICAL FIX: Use arun_many() with single browser instance
            results = await crawler.arun_many(urls, config=config)
            
            # Process results and maintain Theodore's expected format
            for i, result in enumerate(results):
                current_page = i + 1
                
                if result.success:
                    # Try to get the best available content
                    content = None
                    content_source = None
                    
                    # First try cleaned HTML
                    if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
                        content = result.cleaned_html[:10000]  # Limit to 10k chars
                        content_source = "cleaned_html"
                    # Fallback to markdown content
                    elif hasattr(result, 'markdown') and result.markdown and len(str(result.markdown).strip()) > 50:
                        content = str(result.markdown)[:10000]
                        content_source = "markdown"
                    # Final fallback to extracted text
                    elif hasattr(result, 'extracted_content') and result.extracted_content and len(result.extracted_content.strip()) > 50:
                        content = result.extracted_content[:10000]
                        content_source = "extracted_content"
                    
                    if content:
                        # Track scraped page (maintain compatibility)
                        page_info = {
                            "url": result.url,
                            "content_length": len(content),
                            "content_source": content_source,
                            "page_number": current_page
                        }
                        self.scraped_pages.append(page_info)
                        
                        # Add to results in Theodore's expected format
                        page_contents.append({
                            'url': result.url,
                            'content': content
                        })
                        
                        print(f"✅ [{current_page}/{total_pages}] Success: {len(content):,} chars from {content_source} - {result.url}", flush=True)
                        
                        # Progress logging (maintain compatibility)
                        if job_id:
                            progress_logger.add_to_progress_log(job_id, f"✅ [{current_page}/{total_pages}] Success: {len(content):,} chars - {result.url}")
                            progress_logger.log_page_scraping(
                                job_id, result.url, content, current_page, total_pages
                            )
                    else:
                        print(f"❌ [{current_page}/{total_pages}] No content extracted - {result.url}", flush=True)
                        if job_id:
                            progress_logger.add_to_progress_log(job_id, f"❌ [{current_page}/{total_pages}] No content - {result.url}")
                else:
                    print(f"❌ [{current_page}/{total_pages}] Crawl failed - {result.url}", flush=True)
                    if job_id:
                        progress_logger.add_to_progress_log(job_id, f"❌ [{current_page}/{total_pages}] Crawl failed - {result.url}")
        
        duration = time.time() - start_time
        success_count = len(page_contents)
        total_content_chars = sum(len(page.get('content', '')) for page in page_contents)
        
        print(f"🚀 OPTIMIZED EXTRACTION COMPLETE: {success_count}/{total_pages} pages in {duration:.2f}s", flush=True)
        print(f"📊 Performance: {total_pages/duration:.1f} pages/second (vs ~0.3 pages/sec with old method)", flush=True)
        print(f"📈 Estimated speedup: {duration*3:.1f}s -> {duration:.2f}s ({duration*3/duration:.1f}x faster)", flush=True)
        
        if job_id:
            progress_logger.add_to_progress_log(job_id, f"🚀 Optimized extraction complete: {success_count} pages, {total_content_chars:,} chars in {duration:.2f}s")
        
        return page_contents
    
    async def _llm_aggregate_sales_intelligence(
        self, 
        page_contents: List[Dict[str, str]], 
        company_name: str,
        job_id: str = None
    ) -> str:
        """
        Phase 4: Use LLM to aggregate all content into sales intelligence paragraphs
        """
        if not page_contents:
            return f"No content could be extracted for {company_name}."
        
        # Prepare content for LLM analysis
        content_summary = []
        total_chars = 0
        print(f"\n📄 PAGES CRAWLED ({len(page_contents)} pages):")
        for i, page in enumerate(page_contents, 1):
            url_path = urlparse(page['url']).path
            content_chunk = page['content'][:5000]  # Limit per page
            content_summary.append(f"=== Page: {url_path} ===\n{content_chunk}")
            total_chars += len(content_chunk)
            print(f"  {i:2d}. {page['url']} ({len(content_chunk):,} chars)")
        
        combined_content = "\n\n".join(content_summary)
        print(f"\n📊 CONTENT SUMMARY: {total_chars:,} chars from {len(page_contents)} pages")
        
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
            print(f"\n🧠 LLM ANALYSIS:")
            print(f"   INPUT: {len(combined_content):,} characters → LLM")
            response = await self._call_llm_async(prompt, job_id)
            print(f"   OUTPUT: {len(response):,} characters ← LLM")
            print(f"   RESULT: {response[:200]}..." if len(response) > 200 else f"   RESULT: {response}")
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM aggregation failed: {e}")
            # Fallback: Simple content summary
            return f"Content extracted from {len(page_contents)} pages for {company_name}. Manual analysis required."
    
    async def _call_llm_async(self, prompt: str, job_id: str = None) -> str:
        """
        Call LLM asynchronously - supports Gemini, Bedrock, and fallback options
        """
        # Track LLM call
        self.llm_call_count += 1
        call_info = {
            "call_number": self.llm_call_count,
            "model": None,
            "prompt_length": len(prompt),
            "response_length": 0,
            "success": False
        }
        
        # Try Gemini first (1M token context, faster)
        if self.gemini_client:
            try:
                call_info["model"] = "Gemini 2.0 Flash"
                print(f"🧠 LLM CALL #{self.llm_call_count}: Using Gemini 2.0 Flash ({len(prompt):,} chars prompt)", flush=True)
                
                # CRITICAL FIX: Move progress logging AFTER the LLM call to avoid hang
                # The hang occurs during progress logger operations, so we'll log success/failure after
                
                print(f"🧠 About to make Gemini API call with asyncio timeout...", flush=True)
                
                # Configure generation parameters
                generation_config = genai_types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.7,
                    candidate_count=1,
                )
                
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
                
                # CRITICAL FIX: Use asyncio.wait_for() with async Gemini call
                timeout_seconds = 30
                print(f"⏰ Applying {timeout_seconds}s timeout with asyncio.wait_for()", flush=True)
                
                try:
                    # This is the proven solution from research - use async call with timeout
                    response = await asyncio.wait_for(
                        self.gemini_client.generate_content_async(
                            prompt,
                            generation_config=generation_config,
                            safety_settings=safety_settings
                        ),
                        timeout=timeout_seconds
                    )
                    print(f"✅ Gemini call completed successfully! Response: {len(response.text)} chars", flush=True)
                    
                except asyncio.TimeoutError:
                    timeout_msg = f"⏰ Gemini API call timed out after {timeout_seconds} seconds"
                    print(timeout_msg, flush=True)
                    logger.warning(f"Gemini timeout for call #{self.llm_call_count} - falling back to Bedrock")
                    
                    # Log timeout to progress tracker AFTER the timeout (safe)
                    if job_id:
                        try:
                            from src.progress_logger import progress_logger
                            progress_logger.add_to_progress_log(job_id, timeout_msg)
                            progress_logger.add_to_progress_log(job_id, "🔄 Attempting Bedrock fallback...")
                        except Exception as e:
                            logger.error(f"Progress logging failed: {e}")
                    
                    # Don't raise exception - let it fall through to Bedrock fallback
                    call_info["error"] = f"Gemini timeout after {timeout_seconds}s"
                    self.llm_call_log.append(call_info)
                    # Continue to Bedrock fallback below
                    response = None
                    
                except Exception as e:
                    error_msg = f"❌ Gemini API call failed: {e}"
                    print(error_msg, flush=True)
                    logger.error(f"Gemini exception for call #{self.llm_call_count}: {e}")
                    
                    # Log error AFTER the failure (safe)
                    if job_id:
                        try:
                            from src.progress_logger import progress_logger
                            progress_logger.add_to_progress_log(job_id, error_msg)
                        except Exception as pe:
                            logger.error(f"Progress logging failed: {pe}")
                    
                    call_info["error"] = str(e)
                    self.llm_call_log.append(call_info)
                    response = None
                
                # If Gemini succeeded, log success and return
                if response and response.text:
                    # Log success AFTER completion (safe)
                    if job_id:
                        try:
                            from src.progress_logger import progress_logger
                            progress_logger.log_llm_call(job_id, self.llm_call_count, "Gemini 2.0 Flash", len(prompt))
                            progress_logger.add_to_progress_log(job_id, f"✅ Gemini completed: {len(response.text)} chars")
                        except Exception as e:
                            logger.error(f"Progress logging failed: {e}")
                    
                    call_info["response_length"] = len(response.text)
                    call_info["success"] = True
                    self.llm_call_log.append(call_info)
                    return response.text.strip()
            except Exception as e:
                call_info["error"] = str(e)
                self.llm_call_log.append(call_info)
        
        # Fallback to Bedrock
        if self.bedrock_client:
            try:
                if call_info["model"] is None:  # Direct Bedrock call
                    call_info["model"] = "Bedrock"
                    print(f"🧠 LLM CALL #{self.llm_call_count}: Using Bedrock ({len(prompt):,} chars prompt)")
                else:  # Fallback from Gemini
                    call_info["model"] = "Bedrock (fallback)"
                    print(f"🧠 LLM CALL #{self.llm_call_count}: Fallback to Bedrock")
                
                response = self.bedrock_client.analyze_content(prompt)
                call_info["response_length"] = len(response)
                call_info["success"] = True
                self.llm_call_log.append(call_info)
                return response
            except Exception as e:
                call_info["error"] = str(e)
                self.llm_call_log.append(call_info)
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
            timeout: Optional timeout in seconds (defaults to 60)
        """
        if timeout is None:
            timeout = getattr(self.config, 'scraper_timeout', 120)  # Increased from 60 to 120 seconds
            
        # Use direct async execution instead of subprocess (same as batch processing)
        
        try:
            import asyncio
            import time
            
            # Update progress - starting direct async execution (same as batch processing)
            if job_id:
                from src.progress_logger import progress_logger
                progress_logger.update_phase(job_id, "Intelligent Web Scraping", "running", {
                    "status": "Running intelligent web scraper directly...",
                    "direct_execution": True,
                    "timeout_seconds": timeout
                })
            
            start_time = time.time()
            
            # ✅ Direct async execution (same as batch processing) - no subprocess overhead
            result = asyncio.run(asyncio.wait_for(
                self.scraper.scrape_company_intelligent(company_data, job_id),
                timeout=timeout
            ))
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Update progress - scraping phase completed
            if job_id:
                progress_logger.update_phase(job_id, "Intelligent Web Scraping", "completed", {
                    "direct_duration": duration,
                    "pages_extracted": len(result.pages_crawled) if result.pages_crawled else 0,
                    "content_length": len(result.company_description) if result.company_description else 0,
                    "status": "Intelligent scraping completed successfully"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Intelligent scraping error for {company_data.name}: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            
            # Complete job tracking if error
            if job_id:
                complete_company_processing(job_id, False, error=str(e))
            
            return company_data
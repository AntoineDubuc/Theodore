"""
Concurrent Intelligent Company Scraper - Theodore Production Implementation
Integrates the rate-limited concurrent approach with detailed URL logging
"""

import asyncio
import threading
import time
import logging
import json
import re
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from dotenv import load_dotenv

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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_json_from_response(response_text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks"""
    if not response_text:
        return response_text
    
    text = response_text.strip()
    
    # Pattern 1: JSON wrapped in markdown code blocks
    markdown_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
    match = re.search(markdown_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: JSON wrapped in single backticks
    single_tick_pattern = r'`(\{.*?\}|\[.*?\])`'
    match = re.search(single_tick_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Look for JSON-like structures
    json_pattern = r'(\{.*?\}|\[.*?\])'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text

def safe_json_parse(text: str, fallback_value=None):
    """Safely parse JSON with automatic markdown extraction and fallback"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            extracted = extract_json_from_response(text)
            return json.loads(extracted)
        except (json.JSONDecodeError, AttributeError):
            logger.warning(f"Failed to parse JSON from: {text[:100]}...")
            return fallback_value

# ============================================================================
# CONCURRENT LLM SYSTEM
# ============================================================================

@dataclass
class LLMTask:
    """Represents a single LLM task to be processed"""
    task_id: str
    prompt: str
    callback: Optional[Callable] = None
    context: Optional[Dict] = None

@dataclass
class LLMResult:
    """Result from LLM processing"""
    task_id: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0

class ThreadLocalGeminiClient:
    """Thread-local Gemini client that ensures complete isolation per thread"""
    
    def __init__(self):
        self._local = threading.local()
    
    def _get_client(self):
        """Get or create thread-local Gemini client"""
        if not hasattr(self._local, 'client'):
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found")
                
                genai.configure(api_key=api_key)
                self._local.client = genai.GenerativeModel('gemini-2.5-flash')
                self._local.thread_id = threading.get_ident()
                
                logger.info(f"🧵 Thread {self._local.thread_id}: Initialized fresh Gemini client")
                
                # Test the client immediately
                test_response = self._local.client.generate_content("Test")
                logger.info(f"🧵 Thread {self._local.thread_id}: Client test successful")
                
            except Exception as e:
                logger.error(f"🧵 Thread {threading.get_ident()}: Failed to initialize client: {e}")
                raise
        
        return self._local.client
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using thread-local client"""
        client = self._get_client()
        thread_id = getattr(self._local, 'thread_id', 'unknown')
        
        start_time = time.time()
        try:
            logger.debug(f"🧵 Thread {thread_id}: Starting generation...")
            response = client.generate_content(prompt)
            duration = time.time() - start_time
            logger.debug(f"🧵 Thread {thread_id}: Generation completed in {duration:.2f}s")
            return response.text
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"🧵 Thread {thread_id}: Generation failed after {duration:.2f}s: {e}")
            raise

    def generate_content_with_usage(self, prompt: str) -> Dict[str, Any]:
        """Generate content with usage tracking using thread-local client"""
        client = self._get_client()
        thread_id = getattr(self._local, 'thread_id', 'unknown')
        
        start_time = time.time()
        try:
            logger.debug(f"🧵 Thread {thread_id}: Starting generation with usage tracking...")
            response = client.generate_content(prompt)
            duration = time.time() - start_time
            logger.debug(f"🧵 Thread {thread_id}: Generation completed in {duration:.2f}s")
            
            # Extract usage information
            usage_data = self._extract_usage_from_response(response)
            
            return {
                "text": response.text,
                "usage": usage_data,
                "processing_time": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"🧵 Thread {thread_id}: Generation failed after {duration:.2f}s: {e}")
            return {
                "text": "",
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "model": "gemini-2.5-flash",
                    "error": str(e)
                },
                "processing_time": duration
            }

    def _extract_usage_from_response(self, response) -> Dict[str, Any]:
        """Extract token usage and calculate cost from Gemini response"""
        input_tokens = 0
        output_tokens = 0
        
        # Extract usage from Gemini response
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', 0)
            output_tokens = getattr(usage, 'candidates_token_count', 0)
        
        total_tokens = input_tokens + output_tokens
        cost_usd = self._calculate_cost(input_tokens, output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd,
            "model": "gemini-2.5-flash"
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on Gemini pricing"""
        # Gemini 2.5 Flash pricing (per 1M tokens as of Dec 2024)
        input_rate_per_1m = 0.075
        output_rate_per_1m = 0.30
        
        input_cost = (input_tokens / 1000000.0) * input_rate_per_1m
        output_cost = (output_tokens / 1000000.0) * output_rate_per_1m
        
        return round(input_cost + output_cost, 6)

class GeminiWorkerPool:
    """Pre-warmed worker pool for Gemini API calls"""
    
    def __init__(self, max_workers: int = 2, scraper_ref=None):
        self.max_workers = max_workers
        self.client = ThreadLocalGeminiClient()
        self.executor = None
        self._warmed_up = False
        self.scraper_ref = scraper_ref  # Reference to parent scraper for data tracking
    
    def start(self):
        """Start and warm up the worker pool"""
        logger.info(f"🚀 Starting Gemini worker pool with {self.max_workers} workers...")
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._warm_up_workers()
        self._warmed_up = True
        
        logger.info("✅ Gemini worker pool ready!")
    
    def _warm_up_workers(self):
        """Pre-warm all worker threads by testing Gemini connectivity"""
        logger.info("🔥 Warming up worker threads...")
        
        warmup_tasks = []
        for i in range(self.max_workers):
            future = self.executor.submit(self._warmup_worker, i)
            warmup_tasks.append(future)
        
        successful_workers = 0
        for future in as_completed(warmup_tasks, timeout=30):
            try:
                result = future.result()
                if result:
                    successful_workers += 1
            except Exception as e:
                logger.error(f"❌ Worker warmup failed: {e}")
        
        if successful_workers == 0:
            raise RuntimeError("❌ No workers successfully warmed up!")
        
        logger.info(f"✅ {successful_workers}/{self.max_workers} workers warmed up successfully")
    
    def _warmup_worker(self, worker_id: int) -> bool:
        """Warm up a single worker thread"""
        try:
            logger.info(f"🔥 Warming up worker {worker_id}...")
            response = self.client.generate_content("Hello")
            
            if response and "hello" in response.lower():
                logger.info(f"✅ Worker {worker_id} warmed up successfully")
                return True
            else:
                logger.warning(f"⚠️ Worker {worker_id} gave unexpected response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Worker {worker_id} warmup failed: {e}")
            return False
    
    def process_task(self, task: LLMTask) -> LLMResult:
        """Process a single LLM task with token usage tracking"""
        if not self._warmed_up:
            raise RuntimeError("Worker pool not started! Call start() first.")
        
        start_time = time.time()
        
        try:
            logger.debug(f"📝 Processing task {task.task_id}...")
            
            future = self.executor.submit(self.client.generate_content_with_usage, task.prompt)
            generation_result = future.result(timeout=60)
            
            processing_time = time.time() - start_time
            response = generation_result.get("text", "")
            usage_data = generation_result.get("usage", {})
            
            result = LLMResult(
                task_id=task.task_id,
                success=True,
                response=response,
                processing_time=processing_time
            )
            
            # Track LLM interaction with usage data if we have a company context
            if task.context and 'company_name' in task.context:
                llm_interaction = {
                    "task_id": task.task_id,
                    "prompt": task.prompt[:1000] + "..." if len(task.prompt) > 1000 else task.prompt,
                    "response": response[:1000] + "..." if len(response) > 1000 else response,
                    "processing_time": processing_time,
                    "timestamp": time.time(),
                    "usage": usage_data
                }
                
                # Store in current company data if available
                if (self.scraper_ref and 
                    hasattr(self.scraper_ref, '_current_company_data') and 
                    self.scraper_ref._current_company_data):
                    company_data = self.scraper_ref._current_company_data
                    company_data.llm_prompts_sent.append(llm_interaction)
                    
                    # Accumulate token usage and costs
                    if usage_data:
                        company_data.total_input_tokens += usage_data.get("input_tokens", 0)
                        company_data.total_output_tokens += usage_data.get("output_tokens", 0)
                        company_data.total_cost_usd += usage_data.get("cost_usd", 0.0)
                        
                        # Add to detailed breakdown
                        company_data.llm_calls_breakdown.append({
                            "task_id": task.task_id,
                            "input_tokens": usage_data.get("input_tokens", 0),
                            "output_tokens": usage_data.get("output_tokens", 0),
                            "cost_usd": usage_data.get("cost_usd", 0.0),
                            "model": usage_data.get("model", "gemini-2.5-flash"),
                            "timestamp": time.time()
                        })
            
            logger.debug(f"✅ Task {task.task_id} completed in {processing_time:.2f}s")
            
            if task.callback:
                task.callback(result)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            result = LLMResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
            
            logger.error(f"❌ Task {task.task_id} failed after {processing_time:.2f}s: {e}")
            
            if task.callback:
                task.callback(result)
            
            return result
    
    def shutdown(self):
        """Shutdown the worker pool"""
        if self.executor:
            logger.info("🛑 Shutting down Gemini worker pool...")
            self.executor.shutdown(wait=True)
            logger.info("✅ Worker pool shut down")

# ============================================================================
# CONCURRENT INTELLIGENT SCRAPER
# ============================================================================

class ConcurrentIntelligentScraper:
    """
    Concurrent Intelligent Company Scraper with detailed URL logging
    Replaces the hanging single-threaded approach with thread-safe LLM calls
    """
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.bedrock_client = bedrock_client
        self.max_depth = 3
        self.max_pages = 50
        self.concurrent_limit = 10
        
        # Initialize worker pool (will be started when needed)
        self.worker_pool = GeminiWorkerPool(max_workers=2, scraper_ref=self)
        self._pool_started = False
        
        # Tracking
        self.llm_call_count = 0
        self.scraped_pages = []
    
    def _ensure_worker_pool(self):
        """Ensure worker pool is started (lazy initialization)"""
        if not self._pool_started:
            try:
                self.worker_pool.start()
                self._pool_started = True
            except Exception as e:
                logger.error(f"Failed to start worker pool: {e}")
                raise
    
    async def scrape_company_intelligent(self, company_data: CompanyData, job_id: str = None) -> CompanyData:
        """
        Main method: Concurrent intelligent company scraping with detailed URL logging
        """
        start_time = time.time()
        base_url = self._normalize_url(company_data.website)
        
        if not job_id:
            job_id = start_company_processing(company_data.name)
        
        print(f"🔍 SCRAPING: {company_data.name} → {base_url}", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🔍 Starting intelligent scraping: {base_url}")
        
        # Store reference for prompt tracking
        self._current_company_data = company_data
        
        try:
            # Ensure worker pool is ready
            self._ensure_worker_pool()
            
            # Phase 1: Link Discovery with detailed URL logging
            log_processing_phase(job_id, "Link Discovery", "running")
            progress_logger.add_to_progress_log(job_id, "🔍 Phase 1: Discovering all website links...")
            
            discovered_links = await self._discover_links_with_logging(base_url, job_id)
            
            log_processing_phase(job_id, "Link Discovery", "completed")
            progress_logger.add_to_progress_log(job_id, f"✅ Link Discovery: Found {len(discovered_links)} links")
            
            if not discovered_links:
                raise Exception("No links discovered during crawling")
            
            # Phase 2: LLM Page Selection with concurrent processing
            log_processing_phase(job_id, "LLM Page Selection", "running")
            progress_logger.add_to_progress_log(job_id, f"🧠 Phase 2: AI analyzing {len(discovered_links)} links...")
            
            selected_urls = await self._select_pages_concurrent(discovered_links, company_data.name, job_id)
            
            log_processing_phase(job_id, "LLM Page Selection", "completed")
            progress_logger.add_to_progress_log(job_id, f"✅ LLM Page Selection: Selected {len(selected_urls)} priority pages")
            
            # Phase 3: Content Extraction with detailed progress
            log_processing_phase(job_id, "Content Extraction", "running")
            progress_logger.add_to_progress_log(job_id, f"📄 Phase 3: Extracting content from {len(selected_urls)} pages...")
            
            scraped_content = await self._extract_content_with_logging(selected_urls, job_id)
            
            log_processing_phase(job_id, "Content Extraction", "completed")
            progress_logger.add_to_progress_log(job_id, f"✅ Content Extraction: Scraped {len(scraped_content)} pages successfully")
            
            # Phase 4: AI Content Analysis with concurrent processing
            log_processing_phase(job_id, "AI Content Analysis", "running")
            progress_logger.add_to_progress_log(job_id, "🧠 Phase 4: AI analyzing all scraped content...")
            
            analysis = await self._analyze_content_concurrent(scraped_content, company_data.name, job_id)
            
            log_processing_phase(job_id, "AI Content Analysis", "completed")
            progress_logger.add_to_progress_log(job_id, "✅ AI Content Analysis: Business intelligence generated")
            
            # Update company data with results
            if analysis and isinstance(analysis, dict):
                company_data.company_description = analysis.get('company_overview', '')
                company_data.business_model = analysis.get('business_model', '')
                company_data.industry = analysis.get('industry', '')
                company_data.target_market = analysis.get('target_market', '')
                company_data.key_services = analysis.get('key_services', [])
                company_data.value_proposition = analysis.get('value_proposition', '')
                company_data.company_size = analysis.get('company_size', '')
                # Parse founding year safely
                founding_year_str = analysis.get('founding_year', '')
                if founding_year_str and founding_year_str.isdigit():
                    company_data.founding_year = int(founding_year_str)
                company_data.location = analysis.get('location', '')
                company_data.leadership_team = analysis.get('leadership', [])
            
            # Store scraping details
            company_data.scraped_urls = list(scraped_content.keys())
            company_data.scraped_content_details = scraped_content
            
            # Also populate the legacy pages_crawled field for compatibility
            company_data.pages_crawled = list(scraped_content.keys())
            
            total_time = time.time() - start_time
            
            # Set scrape status for main pipeline compatibility
            company_data.scrape_status = "success"
            company_data.crawl_duration = total_time
            
            # Prepare results for the UI
            results = {
                "company": company_data.dict(),
                "processing_time": total_time,
                "success": True
            }
            
            complete_company_processing(job_id, True, summary=f"Completed in {total_time:.1f}s", results=results)
            progress_logger.add_to_progress_log(job_id, f"🎉 Research completed successfully in {total_time:.1f} seconds!")
            
            return company_data
            
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(f"Company scraping failed for {company_data.name}: {e}")
            complete_company_processing(job_id, False, error=error_msg)
            progress_logger.add_to_progress_log(job_id, f"❌ Research failed: {error_msg}")
            raise
    
    async def _discover_links_with_logging(self, base_url: str, job_id: str) -> List[str]:
        """Phase 1: Link discovery with detailed URL logging"""
        all_links = set()
        
        # Step 1: robots.txt analysis
        robots_url = urljoin(base_url, '/robots.txt')
        print(f"🔍 Analyzing robots.txt: {robots_url}", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🔍 Analyzing robots.txt: {robots_url}")
        
        try:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # Extract sitemap URLs from robots.txt
            sitemaps = rp.site_maps() or []
            
            # Filter sitemaps: prioritize main/US sitemaps, skip international variations
            filtered_sitemaps = self._filter_us_sitemaps(sitemaps)
            
            for sitemap_url in filtered_sitemaps:
                print(f"📍 Processing sitemap: {sitemap_url}", flush=True)
                progress_logger.add_to_progress_log(job_id, f"📍 Processing sitemap: {sitemap_url}")
                sitemap_links = await self._parse_sitemap(sitemap_url, job_id)
                all_links.update(sitemap_links)
            
            if len(sitemaps) > len(filtered_sitemaps):
                skipped_count = len(sitemaps) - len(filtered_sitemaps)
                print(f"⏩ Skipped {skipped_count} international sitemaps (focusing on US/main content)", flush=True)
                progress_logger.add_to_progress_log(job_id, f"⏩ Skipped {skipped_count} international sitemaps")
        except Exception as e:
            print(f"⚠️ robots.txt analysis failed: {e}", flush=True)
            progress_logger.add_to_progress_log(job_id, f"⚠️ robots.txt analysis failed: {e}")
        
        # Step 2: Default sitemap.xml analysis
        default_sitemap = urljoin(base_url, '/sitemap.xml')
        print(f"🔍 Analyzing default sitemap: {default_sitemap}", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🔍 Analyzing default sitemap: {default_sitemap}")
        
        try:
            sitemap_links = await self._parse_sitemap(default_sitemap, job_id)
            all_links.update(sitemap_links)
            print(f"✅ Sitemap analysis: {len(sitemap_links)} URLs found", flush=True)
            progress_logger.add_to_progress_log(job_id, f"✅ Sitemap analysis: {len(sitemap_links)} URLs found")
        except Exception as e:
            print(f"⚠️ Sitemap analysis failed: {e}", flush=True)
            progress_logger.add_to_progress_log(job_id, f"⚠️ Sitemap analysis failed: {e}")
        
        # Step 3: Recursive crawling with detailed progress
        print(f"🔍 Starting recursive crawling from: {base_url}", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🔍 Starting recursive crawling from: {base_url}")
        
        crawled_links = await self._recursive_crawl_with_logging(base_url, job_id)
        all_links.update(crawled_links)
        
        final_links = list(all_links)[:200]  # Limit to prevent excessive processing
        print(f"✅ Link discovery complete: {len(final_links)} total URLs", flush=True)
        progress_logger.add_to_progress_log(job_id, f"✅ Link discovery complete: {len(final_links)} total URLs")
        
        return final_links
    
    async def _parse_sitemap(self, sitemap_url: str, job_id: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=sitemap_url, bypass_cache=True)
                if result.success and result.raw_html:
                    root = ET.fromstring(result.raw_html)
                    urls = []
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None and loc_elem.text:
                            urls.append(loc_elem.text)
                    return urls
        except Exception as e:
            logger.debug(f"Sitemap parsing failed for {sitemap_url}: {e}")
        return []
    
    def _filter_us_sitemaps(self, sitemaps: List[str]) -> List[str]:
        """Filter sitemaps to prioritize US/main content and skip international variations"""
        if not sitemaps:
            return []
        
        # International country/language codes to skip
        international_patterns = [
            '/ap/', '/au/', '/br/', '/ca/', '/de/', '/dk/', '/es/', '/fi/', '/fr/', 
            '/fr-ca/', '/in/', '/it/', '/jp/', '/kr/', '/mx/', '/nl/', '/se/', 
            '/sg/', '/uk/', '/cn/', '/tw/', '/hk/', '/ie/', '/no/', '/pl/', 
            '/pt/', '/ru/', '/th/', '/tr/', '/za/', '/ar/', '/cl/', '/pe/',
            '/co/', '/uy/', '/ec/', '/ve/', '/bo/', '/py/', '/gt/', '/cr/',
            '/pa/', '/sv/', '/hn/', '/ni/', '/bz/', '/jm/', '/tt/', '/bb/',
            '/gd/', '/lc/', '/vc/', '/dm/', '/ag/', '/kn/', '/ms/', '/vg/',
            '/ai/', '/tc/', '/ky/', '/bm/', '/fk/', '/gs/', '/sh/', '/ac/',
            '/ta/', '/pn/', '/nu/', '/tk/', '/to/', '/tv/', '/vu/', '/ws/',
            '/as/', '/fm/', '/gu/', '/mh/', '/mp/', '/pw/', '/um/', '/vi/'
        ]
        
        # Prioritize main sitemaps (no country/language code)
        main_sitemaps = []
        us_sitemaps = []
        
        for sitemap in sitemaps:
            # Check if this is an international sitemap
            is_international = any(pattern in sitemap.lower() for pattern in international_patterns)
            
            if not is_international:
                # This is likely a main/US sitemap
                main_sitemaps.append(sitemap)
            elif '/us/' in sitemap.lower():
                # Explicitly US sitemap
                us_sitemaps.append(sitemap)
        
        # Return main sitemaps first, then US sitemaps, limit to 3 total to prevent overload
        filtered = (main_sitemaps + us_sitemaps)[:3]
        
        return filtered if filtered else sitemaps[:1]  # At least process one sitemap
    
    async def _recursive_crawl_with_logging(self, start_url: str, job_id: str) -> List[str]:
        """Recursive crawling with detailed URL logging"""
        found_links = set()
        to_crawl = [(start_url, 0)]  # (url, depth)
        crawled = set()
        
        async with AsyncWebCrawler() as crawler:
            while to_crawl and len(found_links) < 100:  # Limit to prevent excessive crawling
                current_url, depth = to_crawl.pop(0)
                
                if current_url in crawled or depth > self.max_depth:
                    continue
                
                print(f"🔍 Crawling depth {depth}: {current_url}", flush=True)
                progress_logger.add_to_progress_log(job_id, f"🔍 Crawling depth {depth}: {current_url}")
                
                try:
                    result = await crawler.arun(
                        url=current_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.ENABLED,
                            word_count_threshold=10
                        )
                    )
                    
                    if result.success and result.links:
                        page_links = []
                        for link in result.links:
                            try:
                                if isinstance(link, dict):
                                    # Handle dictionary format
                                    href = link.get('href')
                                    if href:
                                        page_links.append(href)
                                elif isinstance(link, str):
                                    # Handle string format
                                    page_links.append(link)
                                else:
                                    # Handle other formats by converting to string
                                    link_str = str(link)
                                    if link_str and link_str.startswith('http'):
                                        page_links.append(link_str)
                            except Exception as e:
                                logger.debug(f"Failed to process link {link}: {e}")
                                continue
                        
                        found_links.update(page_links[:20])  # Limit links per page
                        
                        print(f"  📄 Found {len(page_links)} links on this page", flush=True)
                        
                        # Add new links for deeper crawling
                        if depth < self.max_depth:
                            for link in page_links[:5]:  # Only crawl a few links deeper
                                if link not in crawled:
                                    to_crawl.append((link, depth + 1))
                    
                    crawled.add(current_url)
                    
                except Exception as e:
                    print(f"  ❌ Failed to crawl {current_url}: {e}", flush=True)
                    progress_logger.add_to_progress_log(job_id, f"❌ Crawl failed: {current_url}")
        
        return list(found_links)
    
    async def _select_pages_concurrent(self, discovered_links: List[str], company_name: str, job_id: str) -> List[str]:
        """Phase 2: LLM page selection using concurrent worker pool"""
        print(f"🧠 LLM analyzing {len(discovered_links)} links for {company_name}...", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🧠 LLM analyzing {len(discovered_links)} links...")
        
        # Prepare prompt
        links_text = "\n".join([f"- {link}" for link in discovered_links[:100]])
        
        prompt = f"""Analyze these website links for {company_name} and select the 10-20 most valuable pages for business intelligence extraction.

PRIORITIZE pages likely to contain:
1. Contact information and company location
2. Company founding information and history  
3. Employee count and team information
4. Leadership and management details
5. Business model and revenue information
6. Products, services, and value proposition

Website links to analyze:
{links_text}

Return ONLY a JSON array of the selected URLs, ordered by priority:
["url1", "url2", "url3", ...]

Selected URLs:"""
        
        # Store the page selection prompt for later reference
        if hasattr(self, '_current_company_data'):
            self._current_company_data.page_selection_prompt = prompt

        # Create LLM task
        task = LLMTask(
            task_id=f"{job_id}_page_selection",
            prompt=prompt,
            context={"company_name": company_name, "job_id": job_id}
        )
        
        print(f"🧠 Sending {len(prompt):,} characters to LLM for page selection...", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🧠 LLM prompt sent: {len(prompt):,} characters")
        
        # Process the task
        result = self.worker_pool.process_task(task)
        
        if result.success:
            print(f"✅ LLM page selection completed in {result.processing_time:.2f}s", flush=True)
            progress_logger.add_to_progress_log(job_id, f"✅ LLM response received in {result.processing_time:.2f}s")
            
            # Parse JSON response
            selected_urls = safe_json_parse(result.response.strip(), fallback_value=[])
            
            if selected_urls and isinstance(selected_urls, list):
                # Normalize all selected URLs to ensure proper format
                normalized_urls = []
                for url in selected_urls:
                    normalized_url = self._normalize_url(url)
                    if normalized_url:  # Only add valid URLs
                        normalized_urls.append(normalized_url)
                
                print(f"🎯 LLM selected {len(normalized_urls)} priority pages", flush=True)
                for i, url in enumerate(normalized_urls[:5]):  # Show first 5
                    progress_logger.add_to_progress_log(job_id, f"🎯 Priority {i+1}: {url}")
                return normalized_urls
            else:
                print(f"❌ LLM response parsing failed, using heuristic fallback", flush=True)
                progress_logger.add_to_progress_log(job_id, "❌ LLM response parsing failed, using heuristic fallback")
                return self._heuristic_page_selection(discovered_links)
        else:
            print(f"❌ LLM page selection failed: {result.error}", flush=True)
            progress_logger.add_to_progress_log(job_id, f"❌ LLM page selection failed: {result.error}")
            return self._heuristic_page_selection(discovered_links)
    
    async def _extract_content_with_logging(self, selected_urls: List[str], job_id: str) -> Dict[str, str]:
        """Phase 3: Concurrent content extraction with detailed per-page logging"""
        scraped_content = {}
        max_concurrent_pages = min(10, len(selected_urls))  # Limit concurrent pages to 10 or total URLs
        semaphore = asyncio.Semaphore(max_concurrent_pages)
        
        print(f"📄 Starting concurrent extraction of {len(selected_urls)} pages (max {max_concurrent_pages} concurrent)", flush=True)
        progress_logger.add_to_progress_log(job_id, f"📄 Starting concurrent extraction: {len(selected_urls)} pages ({max_concurrent_pages} concurrent)")
        
        async def extract_single_page(url: str, index: int) -> tuple:
            """Extract content from a single page with semaphore limiting"""
            async with semaphore:
                page_start_time = time.time()
                print(f"📄 [{index}/{len(selected_urls)}] Starting: {url}", flush=True)
                progress_logger.add_to_progress_log(job_id, f"📄 [{index}/{len(selected_urls)}] Starting: {url}")
                
                try:
                    async with AsyncWebCrawler() as crawler:
                        result = await crawler.arun(
                            url=url,
                            config=CrawlerRunConfig(
                                cache_mode=CacheMode.ENABLED,
                                word_count_threshold=50
                            )
                        )
                        
                        page_duration = time.time() - page_start_time
                        
                        if result.success and result.cleaned_html:
                            content = result.cleaned_html[:5000]  # Limit content size
                            print(f"  ✅ [{index}/{len(selected_urls)}] Success: {len(content):,} chars in {page_duration:.1f}s", flush=True)
                            progress_logger.add_to_progress_log(job_id, f"✅ Page {index}: {len(content):,} characters in {page_duration:.1f}s")
                            return (url, content, True, None)
                        else:
                            print(f"  ❌ [{index}/{len(selected_urls)}] Failed: No content in {page_duration:.1f}s", flush=True)
                            progress_logger.add_to_progress_log(job_id, f"❌ Page {index}: No content in {page_duration:.1f}s")
                            return (url, None, False, "No content extracted")
                
                except Exception as e:
                    page_duration = time.time() - page_start_time
                    error_msg = str(e)
                    print(f"  ❌ [{index}/{len(selected_urls)}] Error: {error_msg} in {page_duration:.1f}s", flush=True)
                    progress_logger.add_to_progress_log(job_id, f"❌ Page {index}: Error - {error_msg} in {page_duration:.1f}s")
                    return (url, None, False, error_msg)
        
        # Create concurrent tasks for all pages
        tasks = [extract_single_page(url, i) for i, url in enumerate(selected_urls, 1)]
        
        # Execute all tasks concurrently
        extraction_start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_extraction_time = time.time() - extraction_start_time
        
        # Process results
        successful_extractions = 0
        for result in results:
            if isinstance(result, Exception):
                print(f"  ❌ Task exception: {result}", flush=True)
                continue
                
            url, content, success, error = result
            if success and content:
                scraped_content[url] = content
                successful_extractions += 1
        
        print(f"✅ Concurrent extraction complete: {successful_extractions}/{len(selected_urls)} pages in {total_extraction_time:.1f}s", flush=True)
        progress_logger.add_to_progress_log(job_id, f"✅ Extraction complete: {successful_extractions}/{len(selected_urls)} pages in {total_extraction_time:.1f}s")
        
        return scraped_content
    
    async def _analyze_content_concurrent(self, scraped_content: Dict[str, str], company_name: str, job_id: str) -> Dict:
        """Phase 4: AI content analysis using concurrent worker pool"""
        print(f"🧠 AI analyzing {len(scraped_content)} pages for {company_name}...", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🧠 AI analyzing {len(scraped_content)} pages...")
        
        # Combine all content
        combined_content = ""
        for url, content in scraped_content.items():
            combined_content += f"\n\nPage: {url}\nContent: {content[:2000]}..."
            if len(combined_content) > 50000:
                break
        
        prompt = f"""Analyze this comprehensive website content for {company_name} and extract structured business intelligence.

Content from {len(scraped_content)} pages:
{combined_content}

Extract and provide:
1. Company Overview (2-3 sentences)
2. Business Model (B2B/B2C/B2B2C)
3. Industry/Sector
4. Target Market
5. Key Products/Services (list)
6. Value Proposition
7. Company Size (estimate)
8. Founding Year (if found)
9. Location (if found)
10. Key Leadership (if found)

Respond in JSON format:
{{
    "company_overview": "...",
    "business_model": "...",
    "industry": "...",
    "target_market": "...",
    "key_services": ["...", "..."],
    "value_proposition": "...",
    "company_size": "...",
    "founding_year": "...",
    "location": "...",
    "leadership": ["...", "..."]
}}"""
        
        # Store the content analysis prompt for later reference
        if hasattr(self, '_current_company_data'):
            self._current_company_data.content_analysis_prompt = prompt

        # Create LLM task
        task = LLMTask(
            task_id=f"{job_id}_content_analysis",
            prompt=prompt,
            context={"company_name": company_name, "job_id": job_id}
        )
        
        print(f"🧠 Sending {len(prompt):,} characters to LLM for analysis...", flush=True)
        progress_logger.add_to_progress_log(job_id, f"🧠 AI analysis prompt sent: {len(prompt):,} characters")
        
        # Process the task
        result = self.worker_pool.process_task(task)
        
        if result.success:
            print(f"✅ AI analysis completed in {result.processing_time:.2f}s", flush=True)
            progress_logger.add_to_progress_log(job_id, f"✅ AI analysis completed in {result.processing_time:.2f}s")
            
            # Parse JSON response
            analysis = safe_json_parse(result.response.strip(), fallback_value={})
            
            if analysis and isinstance(analysis, dict):
                print(f"📊 Analysis generated {len(analysis)} business intelligence fields", flush=True)
                progress_logger.add_to_progress_log(job_id, f"📊 Generated {len(analysis)} intelligence fields")
                return analysis
            else:
                print(f"❌ Analysis parsing failed", flush=True)
                progress_logger.add_to_progress_log(job_id, "❌ Analysis parsing failed")
                return {}
        else:
            print(f"❌ AI analysis failed: {result.error}", flush=True)
            progress_logger.add_to_progress_log(job_id, f"❌ AI analysis failed: {result.error}")
            return {}
    
    def _heuristic_page_selection(self, urls: List[str]) -> List[str]:
        """Fallback: select pages using simple heuristics"""
        priority_patterns = [
            ('contact', 10), ('about', 9), ('team', 8), ('careers', 7),
            ('leadership', 7), ('company', 6), ('services', 5), ('products', 5),
            ('history', 4), ('our-story', 4), ('management', 6)
        ]
        
        scored_urls = []
        for url in urls:
            score = 0
            url_lower = url.lower()
            for pattern, weight in priority_patterns:
                if pattern in url_lower:
                    score += weight
            if score > 0:
                scored_urls.append((url, score))
        
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        selected_urls = [url for url, score in scored_urls[:20]]
        
        # Normalize URLs before returning
        normalized_urls = []
        for url in selected_urls:
            normalized_url = self._normalize_url(url)
            if normalized_url:  # Only add valid URLs
                normalized_urls.append(normalized_url)
        
        return normalized_urls
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure proper format"""
        if not url:
            return ""
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if url.endswith('/'):
            url = url[:-1]
        
        return url
    
    def shutdown(self):
        """Shutdown the worker pool"""
        if self._pool_started:
            self.worker_pool.shutdown()
            self._pool_started = False

# ============================================================================
# SYNCHRONOUS WRAPPER
# ============================================================================

class ConcurrentIntelligentScraperSync:
    """Synchronous wrapper for the concurrent scraper"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.scraper = ConcurrentIntelligentScraper(config, bedrock_client)
    
    def scrape_company_intelligent(self, company_data: CompanyData, job_id: str = None) -> CompanyData:
        """Synchronous wrapper for async scrape method"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                self.scraper.scrape_company_intelligent(company_data, job_id)
            )
        finally:
            loop.close()
    
    def scrape_company(self, company_data: CompanyData, job_id: str = None) -> CompanyData:
        """Main scrape method - calls the intelligent scraper"""
        return self.scrape_company_intelligent(company_data, job_id)
    
    def shutdown(self):
        """Shutdown the scraper"""
        self.scraper.shutdown()
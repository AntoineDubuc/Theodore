#!/usr/bin/env python3
"""
Theodore Gemini Solution - Complete multithreaded LLM solution for Theodore
Eliminates hanging issues through thread-local isolation and provides integration layer
"""

import threading
import queue
import time
import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON from LLM response, handling markdown code blocks and other formatting
    """
    if not response_text:
        return response_text
    
    # Remove leading/trailing whitespace
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
    
    # Pattern 4: Return as-is if no patterns match
    return text

def safe_json_parse(text: str, fallback_value=None):
    """
    Safely parse JSON with automatic markdown extraction and fallback
    """
    try:
        # First try direct parsing
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # Try extracting JSON from markdown/formatting
            extracted = extract_json_from_response(text)
            return json.loads(extracted)
        except (json.JSONDecodeError, AttributeError):
            logger.warning(f"Failed to parse JSON from: {text[:100]}...")
            return fallback_value

# ============================================================================
# CORE MULTITHREADING SOLUTION
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
                # Each thread gets its own completely fresh client
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found")
                
                # Configure fresh for this thread
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

class GeminiWorkerPool:
    """Pre-warmed worker pool for Gemini API calls"""
    
    def __init__(self, max_workers: int = 3, warmup_timeout: int = 30):
        self.max_workers = max_workers
        self.warmup_timeout = warmup_timeout
        self.client = ThreadLocalGeminiClient()
        self.executor = None
        self._warmed_up = False
    
    def start(self):
        """Start and warm up the worker pool"""
        logger.info(f"🚀 Starting Gemini worker pool with {self.max_workers} workers...")
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Pre-warm all workers
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
        
        # Wait for all workers to warm up
        successful_workers = 0
        for future in as_completed(warmup_tasks, timeout=self.warmup_timeout):
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
            
            # This will create the thread-local client and test it
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
        """Process a single LLM task"""
        if not self._warmed_up:
            raise RuntimeError("Worker pool not started! Call start() first.")
        
        start_time = time.time()
        
        try:
            logger.debug(f"📝 Processing task {task.task_id}...")
            
            # Submit to pre-warmed worker
            future = self.executor.submit(self.client.generate_content, task.prompt)
            response = future.result(timeout=60)  # 1 minute timeout per task
            
            processing_time = time.time() - start_time
            
            result = LLMResult(
                task_id=task.task_id,
                success=True,
                response=response,
                processing_time=processing_time
            )
            
            logger.debug(f"✅ Task {task.task_id} completed in {processing_time:.2f}s")
            
            # Call callback if provided
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
# THEODORE INTEGRATION LAYER
# ============================================================================

class TheodoreLLMManager:
    """
    Integration layer between Theodore scraping system and multithreaded Gemini
    """
    
    def __init__(self, max_workers: int = 3):
        self.worker_pool = GeminiWorkerPool(max_workers=max_workers)
        self._started = False
    
    def start(self):
        """Start the LLM worker pool (call once at app startup)"""
        if not self._started:
            print("🚀 Starting Theodore LLM Manager...")
            self.worker_pool.start()
            self._started = True
            print("✅ Theodore LLM Manager ready!")
    
    def shutdown(self):
        """Shutdown the worker pool (call at app shutdown)"""
        if self._started:
            self.worker_pool.shutdown()
            self._started = False
    
    def analyze_page_selection(self, job_id: str, discovered_links: List[str], 
                              company_name: str, progress_callback=None) -> Dict:
        """
        Analyze discovered links and select the best pages for scraping
        This replaces the hanging LLM call in intelligent_company_scraper.py
        """
        print(f"🧠 Analyzing page selection for {company_name} ({len(discovered_links)} links)")
        
        # Prepare prompt
        links_text = "\n".join([f"- {link}" for link in discovered_links[:100]])  # Limit for token size
        
        prompt = f"""
Analyze these website links for {company_name} and select the 10-20 most valuable pages for business intelligence extraction.

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

        # Create LLM task
        task = LLMTask(
            task_id=f"{job_id}_page_selection",
            prompt=prompt,
            context={"company_name": company_name, "job_id": job_id}
        )
        
        # Add progress callback
        if progress_callback:
            def llm_callback(result: LLMResult):
                if result.success:
                    progress_callback(job_id, "LLM Page Selection", "completed", {
                        "selected_pages": len(result.response.split('\n')),
                        "processing_time": result.processing_time
                    })
                else:
                    progress_callback(job_id, "LLM Page Selection", "failed", {
                        "error": result.error
                    })
            task.callback = llm_callback
        
        # Process the task
        result = self.worker_pool.process_task(task)
        
        if result.success:
            # Parse JSON response with smart extraction
            selected_urls = safe_json_parse(result.response.strip(), fallback_value=[])
            
            if selected_urls and isinstance(selected_urls, list):
                return {
                    "success": True,
                    "selected_urls": selected_urls,
                    "processing_time": result.processing_time,
                    "total_analyzed": len(discovered_links)
                }
            else:
                print(f"❌ Failed to parse LLM response as JSON array")
                print(f"Raw response: {result.response}")
                
                # Fallback: extract URLs from text
                fallback_urls = self._extract_urls_from_text(result.response, discovered_links)
                return {
                    "success": True,
                    "selected_urls": fallback_urls,
                    "processing_time": result.processing_time,
                    "fallback_used": True
                }
        else:
            print(f"❌ LLM page selection failed: {result.error}")
            # Fallback to heuristic selection
            fallback_urls = self._heuristic_page_selection(discovered_links)
            return {
                "success": False,
                "error": result.error,
                "selected_urls": fallback_urls,
                "fallback_used": True
            }
    
    def analyze_scraped_content(self, job_id: str, company_name: str, 
                               scraped_pages: Dict[str, str], progress_callback=None) -> Dict:
        """
        Analyze all scraped content and generate business intelligence
        This replaces the final LLM analysis in the scraping pipeline
        """
        print(f"🧠 Analyzing scraped content for {company_name} ({len(scraped_pages)} pages)")
        
        # Combine all content (with size limits)
        combined_content = ""
        for url, content in scraped_pages.items():
            combined_content += f"\n\nPage: {url}\nContent: {content[:2000]}..."  # Limit per page
            if len(combined_content) > 50000:  # Overall limit
                break
        
        prompt = f"""
Analyze this comprehensive website content for {company_name} and extract structured business intelligence.

Content from {len(scraped_pages)} pages:
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

        # Create LLM task
        task = LLMTask(
            task_id=f"{job_id}_content_analysis",
            prompt=prompt,
            context={"company_name": company_name, "job_id": job_id}
        )
        
        # Add progress callback
        if progress_callback:
            def llm_callback(result: LLMResult):
                if result.success:
                    progress_callback(job_id, "AI Content Analysis", "completed", {
                        "processing_time": result.processing_time,
                        "content_length": len(combined_content)
                    })
                else:
                    progress_callback(job_id, "AI Content Analysis", "failed", {
                        "error": result.error
                    })
            task.callback = llm_callback
        
        # Process the task
        result = self.worker_pool.process_task(task)
        
        if result.success:
            # Parse JSON response with smart extraction
            analysis = safe_json_parse(result.response.strip(), fallback_value={})
            
            if analysis and isinstance(analysis, dict):
                return {
                    "success": True,
                    "analysis": analysis,
                    "processing_time": result.processing_time,
                    "pages_analyzed": len(scraped_pages)
                }
            else:
                print(f"❌ Failed to parse analysis as JSON object")
                print(f"Raw response: {result.response}")
                return {
                    "success": False,
                    "error": "JSON parsing failed - expected object format",
                    "raw_response": result.response
                }
        else:
            return {
                "success": False,
                "error": result.error
            }
    
    def _extract_urls_from_text(self, text: str, available_urls: List[str]) -> List[str]:
        """Fallback: extract URLs mentioned in LLM response text"""
        selected = []
        for url in available_urls:
            if url in text:
                selected.append(url)
        return selected[:20]  # Limit to reasonable number
    
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
        
        # Sort by score and return top 20
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        return [url for url, score in scored_urls[:20]]

# ============================================================================
# FLASK INTEGRATION EXAMPLE
# ============================================================================

def create_flask_integration():
    """
    Example of how to integrate this into Theodore's Flask app
    """
    # Global LLM manager (initialize once at app startup)
    llm_manager = TheodoreLLMManager(max_workers=3)
    
    def init_app():
        """Call this when Flask app starts"""
        llm_manager.start()
    
    def shutdown_app():
        """Call this when Flask app shuts down"""
        llm_manager.shutdown()
    
    def research_company_fixed(company_name: str, website: str, job_id: str):
        """
        Fixed version of the research flow that doesn't hang
        """
        print(f"🔍 Starting research for {company_name}")
        
        # Phase 1: Link Discovery (existing code, no LLM)
        discovered_links = discover_links(website)  # Your existing function
        print(f"📋 Discovered {len(discovered_links)} links")
        
        # Phase 2: LLM Page Selection (NEW - no hanging!)
        def progress_update(job_id, phase, status, details):
            print(f"📊 {phase}: {status}")
            # Update your progress logger here
        
        selection_result = llm_manager.analyze_page_selection(
            job_id, discovered_links, company_name, progress_update
        )
        
        if not selection_result["success"]:
            print(f"⚠️ Page selection failed, using fallback")
        
        selected_urls = selection_result["selected_urls"]
        print(f"🎯 Selected {len(selected_urls)} pages for scraping")
        
        # Phase 3: Content Extraction (existing code, no LLM)
        scraped_content = scrape_pages(selected_urls)  # Your existing function
        print(f"📄 Scraped {len(scraped_content)} pages")
        
        # Phase 4: LLM Content Analysis (NEW - no hanging!)
        analysis_result = llm_manager.analyze_scraped_content(
            job_id, company_name, scraped_content, progress_update
        )
        
        if analysis_result["success"]:
            print(f"✅ Analysis completed in {analysis_result['processing_time']:.2f}s")
            return analysis_result["analysis"]
        else:
            print(f"❌ Analysis failed: {analysis_result['error']}")
            return None
    
    return {
        "init_app": init_app,
        "shutdown_app": shutdown_app,
        "research_company": research_company_fixed,
        "llm_manager": llm_manager
    }

# Dummy functions for example
def discover_links(website: str) -> List[str]:
    """Placeholder for your existing link discovery"""
    return [f"{website}/about", f"{website}/contact", f"{website}/team"]

def scrape_pages(urls: List[str]) -> Dict[str, str]:
    """Placeholder for your existing page scraping"""
    return {url: f"Content from {url}" for url in urls}

# ============================================================================
# SIMPLE TEST FUNCTION
# ============================================================================

def test_solution():
    """Simple test to verify the solution works without hanging"""
    print("🧪 Testing Theodore Gemini Solution...")
    
    manager = TheodoreLLMManager(max_workers=1)  # Single worker to avoid rate limits
    
    try:
        manager.start()
        
        # Test page selection
        test_links = [
            "https://company.com/about",
            "https://company.com/contact", 
            "https://company.com/team",
            "https://company.com/products"
        ]
        
        result = manager.analyze_page_selection(
            "test_job_123", test_links, "Test Company"
        )
        
        print(f"✅ Page selection result: {result['success']}")
        
        if result['success']:
            print("🎉 Threading solution works - no hanging!")
            return True
        else:
            print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        manager.shutdown()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run simple test
    success = test_solution()
    
    if success:
        print("\n🎉 CONCLUSION: Threading solution works without hanging!")
        print("💡 Ready to integrate into Theodore!")
    else:
        print("\n❌ Threading solution has issues")
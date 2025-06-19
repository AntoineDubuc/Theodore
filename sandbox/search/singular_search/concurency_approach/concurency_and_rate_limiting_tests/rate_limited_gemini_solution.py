#!/usr/bin/env python3
"""
Rate-Limited Theodore Gemini Solution
Implements proper rate limiting to respect Gemini API quotas
"""

import threading
import time
import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING IMPLEMENTATIONS
# ============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter - allows bursts up to capacity
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second (e.g., 10/60 = 10 per minute)
        """
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def acquire_token(self, tokens_needed: int = 1) -> bool:
        """Try to acquire tokens from bucket"""
        with self.lock:
            self._refill_tokens()
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False
    
    def wait_for_token(self, tokens_needed: int = 1, timeout: float = None) -> bool:
        """Wait until tokens are available"""
        start_time = time.time()
        
        while True:
            if self.acquire_token(tokens_needed):
                return True
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Calculate wait time until next token
            with self.lock:
                self._refill_tokens()
                tokens_deficit = tokens_needed - self.tokens
                wait_time = min(1.0, tokens_deficit / self.refill_rate)
            
            time.sleep(wait_time)
    
    def get_status(self) -> Dict:
        """Get current rate limiter status"""
        with self.lock:
            self._refill_tokens()
            return {
                "tokens_available": self.tokens,
                "capacity": self.capacity,
                "refill_rate_per_second": self.refill_rate,
                "utilization": (self.capacity - self.tokens) / self.capacity
            }

class SimpleRateLimiter:
    """
    Simple rate limiter - enforces minimum interval between requests
    """
    
    def __init__(self, requests_per_minute: int):
        """
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait_for_slot(self):
        """Wait until it's safe to make another request"""
        with self.lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)
            self.last_request_time = time.time()

# ============================================================================
# RATE-LIMITED GEMINI CLIENT
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
    rate_limited: bool = False
    tokens_used: int = 1

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

class RateLimitedGeminiClient:
    """Gemini client with built-in rate limiting"""
    
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        self._local = threading.local()
        self.rate_limiter = rate_limiter
    
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
                
                logger.info(f"🧵 Thread {self._local.thread_id}: Initialized Gemini client")
                
            except Exception as e:
                logger.error(f"🧵 Thread {threading.get_ident()}: Failed to initialize client: {e}")
                raise
        
        return self._local.client
    
    def generate_content(self, prompt: str, timeout: float = 120) -> str:
        """Generate content with rate limiting"""
        thread_id = getattr(self._local, 'thread_id', 'unknown')
        
        # Wait for rate limit approval
        logger.debug(f"🧵 Thread {thread_id}: Waiting for rate limit approval...")
        rate_limit_start = time.time()
        
        if not self.rate_limiter.wait_for_token(timeout=timeout):
            raise Exception("Rate limit timeout - no tokens available")
        
        rate_limit_wait = time.time() - rate_limit_start
        logger.debug(f"🧵 Thread {thread_id}: Rate limit approved after {rate_limit_wait:.2f}s")
        
        # Make the API call
        client = self._get_client()
        api_start = time.time()
        
        try:
            logger.debug(f"🧵 Thread {thread_id}: Making API call...")
            response = client.generate_content(prompt)
            api_duration = time.time() - api_start
            
            logger.debug(f"🧵 Thread {thread_id}: API call completed in {api_duration:.2f}s")
            return response.text
            
        except Exception as e:
            api_duration = time.time() - api_start
            logger.error(f"🧵 Thread {thread_id}: API call failed after {api_duration:.2f}s: {e}")
            raise

# ============================================================================
# RATE-LIMITED WORKER POOL
# ============================================================================

class RateLimitedWorkerPool:
    """Worker pool with built-in rate limiting"""
    
    def __init__(self, max_workers: int = 1, requests_per_minute: int = 8):
        """
        Args:
            max_workers: Number of worker threads
            requests_per_minute: Rate limit (conservative default for free tier)
        """
        self.max_workers = max_workers
        self.requests_per_minute = requests_per_minute
        
        # Create rate limiter - token bucket with burst capacity
        refill_rate = requests_per_minute / 60.0  # tokens per second
        self.rate_limiter = TokenBucketRateLimiter(
            capacity=min(3, requests_per_minute),  # Small burst capacity
            refill_rate=refill_rate
        )
        
        self.client = RateLimitedGeminiClient(self.rate_limiter)
        self.executor = None
        self._started = False
    
    def start(self):
        """Start the worker pool"""
        if self._started:
            return
        
        logger.info(f"🚀 Starting rate-limited worker pool...")
        logger.info(f"   • Workers: {self.max_workers}")
        logger.info(f"   • Rate limit: {self.requests_per_minute} requests/minute")
        logger.info(f"   • Min interval: {60/self.requests_per_minute:.1f}s between requests")
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._started = True
        
        logger.info("✅ Rate-limited worker pool ready!")
    
    def process_task(self, task: LLMTask) -> LLMResult:
        """Process a single LLM task with rate limiting"""
        if not self._started:
            raise RuntimeError("Worker pool not started! Call start() first.")
        
        total_start = time.time()
        
        try:
            logger.debug(f"📝 Processing task {task.task_id} with rate limiting...")
            
            # Get rate limiter status before request
            rate_status = self.rate_limiter.get_status()
            logger.debug(f"📊 Rate limiter status: {rate_status['tokens_available']:.1f}/{rate_status['capacity']} tokens")
            
            # Submit to worker with rate limiting
            future = self.executor.submit(self.client.generate_content, task.prompt)
            response = future.result(timeout=180)  # 3 minute timeout
            
            processing_time = time.time() - total_start
            
            result = LLMResult(
                task_id=task.task_id,
                success=True,
                response=response,
                processing_time=processing_time,
                rate_limited=True,
                tokens_used=1
            )
            
            logger.debug(f"✅ Task {task.task_id} completed in {processing_time:.2f}s")
            
            if task.callback:
                task.callback(result)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - total_start
            
            result = LLMResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                processing_time=processing_time,
                rate_limited=True
            )
            
            logger.error(f"❌ Task {task.task_id} failed after {processing_time:.2f}s: {e}")
            
            if task.callback:
                task.callback(result)
            
            return result
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limiting status"""
        return self.rate_limiter.get_status()
    
    def shutdown(self):
        """Shutdown the worker pool"""
        if self.executor:
            logger.info("🛑 Shutting down rate-limited worker pool...")
            self.executor.shutdown(wait=True)
            self._started = False
            logger.info("✅ Worker pool shut down")

# ============================================================================
# THEODORE INTEGRATION WITH RATE LIMITING
# ============================================================================

class RateLimitedTheodoreLLMManager:
    """
    Theodore LLM Manager with proper rate limiting
    """
    
    def __init__(self, max_workers: int = 1, requests_per_minute: int = 8):
        """
        Args:
            max_workers: Number of concurrent workers (recommend 1 for free tier)
            requests_per_minute: Rate limit (8 is conservative for 10/min free tier)
        """
        self.worker_pool = RateLimitedWorkerPool(max_workers, requests_per_minute)
        self._started = False
    
    def start(self):
        """Start the LLM manager"""
        if not self._started:
            print("🚀 Starting Rate-Limited Theodore LLM Manager...")
            self.worker_pool.start()
            self._started = True
            print("✅ Rate-Limited Theodore LLM Manager ready!")
    
    def shutdown(self):
        """Shutdown the LLM manager"""
        if self._started:
            self.worker_pool.shutdown()
            self._started = False
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limiting status"""
        return self.worker_pool.get_rate_limit_status()
    
    def analyze_page_selection(self, job_id: str, discovered_links: List[str], 
                              company_name: str, progress_callback=None) -> Dict:
        """Analyze discovered links with rate limiting"""
        
        status = self.get_rate_limit_status()
        print(f"🧠 Analyzing page selection for {company_name} (Rate: {status['tokens_available']:.1f}/{status['capacity']} tokens)")
        
        # Prepare prompt
        links_text = "\n".join([f"- {link}" for link in discovered_links[:100]])
        
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
        
        # Process with rate limiting
        result = self.worker_pool.process_task(task)
        
        if result.success:
            selected_urls = safe_json_parse(result.response.strip(), fallback_value=[])
            
            if selected_urls and isinstance(selected_urls, list):
                return {
                    "success": True,
                    "selected_urls": selected_urls,
                    "processing_time": result.processing_time,
                    "total_analyzed": len(discovered_links),
                    "rate_limited": result.rate_limited
                }
            else:
                print(f"❌ Failed to parse LLM response as JSON array")
                # Fallback to heuristic selection
                fallback_urls = self._heuristic_page_selection(discovered_links)
                return {
                    "success": True,
                    "selected_urls": fallback_urls,
                    "processing_time": result.processing_time,
                    "fallback_used": True,
                    "rate_limited": result.rate_limited
                }
        else:
            print(f"❌ LLM page selection failed: {result.error}")
            fallback_urls = self._heuristic_page_selection(discovered_links)
            return {
                "success": False,
                "error": result.error,
                "selected_urls": fallback_urls,
                "fallback_used": True,
                "rate_limited": result.rate_limited
            }
    
    def analyze_scraped_content(self, job_id: str, company_name: str, 
                               scraped_pages: Dict[str, str], progress_callback=None) -> Dict:
        """Analyze scraped content with rate limiting"""
        
        status = self.get_rate_limit_status()
        print(f"🧠 Analyzing scraped content for {company_name} (Rate: {status['tokens_available']:.1f}/{status['capacity']} tokens)")
        
        # Combine all content (with size limits)
        combined_content = ""
        for url, content in scraped_pages.items():
            combined_content += f"\n\nPage: {url}\nContent: {content[:2000]}..."
            if len(combined_content) > 50000:
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
        
        # Process with rate limiting
        result = self.worker_pool.process_task(task)
        
        if result.success:
            analysis = safe_json_parse(result.response.strip(), fallback_value={})
            
            if analysis and isinstance(analysis, dict):
                return {
                    "success": True,
                    "analysis": analysis,
                    "processing_time": result.processing_time,
                    "pages_analyzed": len(scraped_pages),
                    "rate_limited": result.rate_limited
                }
            else:
                print(f"❌ Failed to parse analysis as JSON object")
                return {
                    "success": False,
                    "error": "JSON parsing failed - expected object format",
                    "raw_response": result.response,
                    "rate_limited": result.rate_limited
                }
        else:
            return {
                "success": False,
                "error": result.error,
                "rate_limited": result.rate_limited
            }
    
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
        return [url for url, score in scored_urls[:20]]

# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_rate_limited_solution():
    """Test the rate-limited solution"""
    print("🧪 Testing Rate-Limited Theodore Gemini Solution...")
    print("=" * 60)
    
    # Test with conservative settings for free tier
    manager = RateLimitedTheodoreLLMManager(
        max_workers=1,
        requests_per_minute=8  # Conservative for 10/min free tier
    )
    
    try:
        manager.start()
        
        # Show initial rate limit status
        status = manager.get_rate_limit_status()
        print(f"📊 Initial rate limit status: {status}")
        print()
        
        # Test 1: Page Selection
        print("📋 TEST 1: Page Selection Analysis")
        test_links = [
            "https://company.com/about",
            "https://company.com/contact", 
            "https://company.com/team",
            "https://company.com/products"
        ]
        
        start_time = time.time()
        result = manager.analyze_page_selection(
            "test_job_123", test_links, "Test Company"
        )
        duration = time.time() - start_time
        
        print(f"✅ Page selection completed in {duration:.2f}s")
        print(f"🎯 Success: {result['success']}, Rate limited: {result.get('rate_limited', 'N/A')}")
        print()
        
        # Show rate limit status after first request
        status = manager.get_rate_limit_status()
        print(f"📊 Rate limit status after request 1: {status}")
        print()
        
        # Test 2: Content Analysis (this will test rate limiting)
        print("📋 TEST 2: Content Analysis")
        test_content = {
            "https://company.com/about": "Founded in 2020, Test Company is a software firm...",
            "https://company.com/contact": "Email: info@testcompany.com, Phone: (555) 123-4567..."
        }
        
        start_time = time.time()
        result2 = manager.analyze_scraped_content(
            "test_job_123", "Test Company", test_content
        )
        duration2 = time.time() - start_time
        
        print(f"✅ Content analysis completed in {duration2:.2f}s")
        print(f"🎯 Success: {result2['success']}, Rate limited: {result2.get('rate_limited', 'N/A')}")
        
        # Final status
        status = manager.get_rate_limit_status()
        print(f"📊 Final rate limit status: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        manager.shutdown()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_rate_limited_solution()
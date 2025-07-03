#!/usr/bin/env python3
"""
Parallel Content Extractor - Phase 3 of Intelligent Scraping
============================================================

High-performance parallel content extraction using Crawl4AI with sophisticated
rate limiting, progress tracking, and error handling for production environments.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Callable
import logging
from dataclasses import dataclass
from crawl4ai import AsyncWebCrawler
import time


@dataclass
class ExtractionResult:
    """Result from a single page extraction"""
    url: str
    success: bool
    content: str = ""
    title: str = ""
    metadata: Dict[str, Any] = None
    extraction_time: float = 0.0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ParallelContentExtractor:
    """High-performance parallel content extraction service"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self._semaphore = asyncio.Semaphore(max_workers)
        self._crawlers = []
    
    async def extract_content_parallel(
        self, 
        urls: List[str], 
        progress_callback: Optional[Callable] = None
    ) -> List[ExtractionResult]:
        """Extract content from multiple pages in parallel."""
        
        if not urls:
            return []
        
        self.logger.info(f"Starting parallel extraction for {len(urls)} pages")
        start_time = time.time()
        
        # Initialize crawler pool
        await self._initialize_crawler_pool()
        
        try:
            # Create extraction tasks
            tasks = []
            for i, url in enumerate(urls):
                task = asyncio.create_task(
                    self._extract_single_page_with_progress(url, i, len(urls), progress_callback)
                )
                tasks.append(task)
            
            # Execute all tasks and collect results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            extraction_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Extraction failed for {urls[i]}: {result}")
                    extraction_results.append(ExtractionResult(
                        url=urls[i],
                        success=False,
                        error=str(result)
                    ))
                else:
                    extraction_results.append(result)
            
            # Log performance metrics
            total_time = time.time() - start_time
            successful = sum(1 for r in extraction_results if r.success)
            self.logger.info(
                f"Parallel extraction completed: {successful}/{len(urls)} pages "
                f"extracted in {total_time:.2f}s ({len(urls)/total_time:.1f} pages/sec)"
            )
            
            return extraction_results
            
        finally:
            await self._cleanup_crawler_pool()
    
    async def _extract_single_page_with_progress(
        self, 
        url: str, 
        index: int, 
        total: int, 
        progress_callback: Optional[Callable]
    ) -> ExtractionResult:
        """Extract a single page with progress reporting."""
        
        async with self._semaphore:  # Rate limiting
            if progress_callback:
                from ...interfaces.web_scraper import ScrapingProgress, ScrapingPhase
                progress_callback(ScrapingProgress(
                    ScrapingPhase.CONTENT_EXTRACTION, index + 1, total,
                    f"Extracting content from {url}",
                    {"current_url": url}
                ))
            
            return await self._extract_single_page(url)
    
    async def _extract_single_page(self, url: str) -> ExtractionResult:
        """Extract content from a single page using Crawl4AI."""
        
        start_time = time.time()
        
        try:
            # Get crawler from pool
            crawler = await self._get_crawler()
            
            # Configure extraction settings
            crawl_config = {
                "word_count_threshold": 50,  # Minimum meaningful content
                "only_text": True,  # Extract clean text
                "remove_overlay_elements": True,  # Remove popups/modals
                "bypass_cache": False,  # Use cache for efficiency
                "simulate_user": True,  # Better JS handling
                "magic": True,  # Enable smart content extraction
                "exclude_tags": ["nav", "footer", "aside", "header", ".sidebar", "#comments"],
                "css_selector": "main, article, .content, .main-content, [role='main']",
                "wait_for": "networkidle",  # Wait for page to stabilize
                "timeout": 25000,  # 25 second timeout
            }
            
            # Execute extraction
            result = await crawler.arun(url=url, **crawl_config)
            
            if result.success:
                # Extract title and clean content
                title = self._extract_title(result.markdown or result.cleaned_html or "")
                content = self._clean_content(result.markdown or result.cleaned_html or "")
                
                # Build metadata
                metadata = {
                    "status_code": getattr(result, "status_code", 200),
                    "content_length": len(content),
                    "links_found": len(getattr(result, "links", [])),
                    "images_found": len(getattr(result, "media", [])),
                    "extraction_method": "crawl4ai_magic"
                }
                
                self.logger.debug(f"✅ [{index+1}/{total}] Success: {url} - {len(content)} chars")
                
                return ExtractionResult(
                    url=url,
                    success=True,
                    content=content,
                    title=title,
                    metadata=metadata,
                    extraction_time=time.time() - start_time
                )
            else:
                error_msg = getattr(result, "error_message", "Unknown extraction error")
                self.logger.warning(f"❌ [{index+1}/{total}] Failed: {url} - {error_msg}")
                
                return ExtractionResult(
                    url=url,
                    success=False,
                    error=error_msg,
                    extraction_time=time.time() - start_time
                )
        
        except Exception as e:
            self.logger.error(f"❌ Extraction exception for {url}: {e}")
            return ExtractionResult(
                url=url,
                success=False,
                error=str(e),
                extraction_time=time.time() - start_time
            )
    
    def _extract_title(self, content: str) -> str:
        """Extract page title from content."""
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) < 200:  # Reasonable title length
                # Remove markdown formatting
                title = line.replace('#', '').strip()
                if title:
                    return title
        return "Untitled Page"
    
    def _clean_content(self, content: str) -> str:
        """Clean and optimize extracted content."""
        if not content:
            return ""
        
        # Basic cleaning
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and very short lines (likely navigation)
            if len(line) > 20:
                cleaned_lines.append(line)
        
        # Join and limit content length
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Limit to reasonable size (10K chars max per page)
        if len(cleaned_content) > 10000:
            cleaned_content = cleaned_content[:10000] + "... [content truncated]"
        
        return cleaned_content
    
    async def _initialize_crawler_pool(self):
        """Initialize pool of Crawl4AI crawlers for parallel use."""
        self.logger.debug(f"Initializing crawler pool with {self.max_workers} workers")
        
        # Create crawler instances (thread-local for safety)
        self._crawlers = []
        for _ in range(min(self.max_workers, 5)):  # Limit actual crawlers
            crawler = AsyncWebCrawler(
                verbose=False,
                browser_type="chromium",
                headless=True,
                user_agent="Mozilla/5.0 (compatible; TheodoreBot/2.0; +https://theodore.ai/bot)",
            )
            await crawler.start()
            self._crawlers.append(crawler)
    
    async def _get_crawler(self) -> AsyncWebCrawler:
        """Get an available crawler from the pool."""
        # Simple round-robin assignment
        if not self._crawlers:
            await self._initialize_crawler_pool()
        
        # For now, just use the first crawler (Crawl4AI handles concurrency internally)
        return self._crawlers[0] if self._crawlers else None
    
    async def _cleanup_crawler_pool(self):
        """Clean up crawler resources."""
        self.logger.debug("Cleaning up crawler pool")
        
        for crawler in self._crawlers:
            try:
                await crawler.close()
            except Exception as e:
                self.logger.warning(f"Error closing crawler: {e}")
        
        self._crawlers.clear()
    
    async def get_extraction_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the extractor."""
        return {
            "max_workers": self.max_workers,
            "active_crawlers": len(self._crawlers),
            "semaphore_capacity": self._semaphore._value,
            "status": "ready" if self._crawlers else "uninitialized"
        }
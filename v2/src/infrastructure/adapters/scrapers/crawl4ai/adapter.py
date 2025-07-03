#!/usr/bin/env python3
"""
Crawl4AI Scraper Adapter - Main Orchestrator
============================================

Production-ready implementation of the WebScraper interface using Crawl4AI with
a sophisticated 4-phase intelligent scraping system optimized for business intelligence.

Phases:
1. Link Discovery: Multi-source discovery (robots.txt, sitemap, recursive crawling)
2. Page Selection: AI-driven prioritization for maximum value extraction
3. Content Extraction: High-performance parallel content extraction
4. AI Aggregation: Business intelligence generation from combined content
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
import logging
import time
from dataclasses import dataclass

from ...core.ports.web_scraper import (
    WebScraper, ScrapingConfig, ScrapingResult, PageResult, 
    ProgressCallback, ValidationCallback, WebScraperException,
    ScrapingTimeoutException, ConfigurationException,
    StreamingWebScraper, CacheableWebScraper
)
from ...core.ports.progress import ProgressTracker
from ...core.interfaces.ai_provider import AIProviderPort

from .link_discovery import LinkDiscoveryService
from .page_selector import LLMPageSelector
from .content_extractor import ParallelContentExtractor, ExtractionResult
from .aggregator import AIContentAggregator, CompanyIntelligence


@dataclass 
class ScrapingPhase:
    """Enumeration of scraping phases for progress tracking"""
    LINK_DISCOVERY = "link_discovery"
    PAGE_SELECTION = "page_selection" 
    CONTENT_EXTRACTION = "content_extraction"
    AI_AGGREGATION = "ai_aggregation"


@dataclass
class ScrapingProgress:
    """Progress information for a scraping operation"""
    phase: str
    current: int
    total: int
    message: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Crawl4AIScraper(WebScraper, StreamingWebScraper):
    """
    Production-ready Crawl4AI adapter implementing sophisticated 4-phase intelligent scraping.
    
    Optimized for business intelligence extraction with comprehensive error handling,
    progress tracking, and production-ready performance characteristics.
    """
    
    def __init__(self, ai_provider: AIProviderPort, config: Optional[ScrapingConfig] = None):
        self.ai_provider = ai_provider
        self.config = config or ScrapingConfig.for_company_research()
        self.logger = logging.getLogger(__name__)
        
        # Initialize 4-phase system components
        self.link_discovery = LinkDiscoveryService(max_links=1000)
        self.page_selector = LLMPageSelector(ai_provider)
        self.content_extractor = ParallelContentExtractor(max_workers=10)
        self.aggregator = AIContentAggregator(ai_provider)
        
        # Performance tracking
        self._stats = {
            "requests_processed": 0,
            "total_response_time": 0.0,
            "success_count": 0,
            "error_count": 0,
            "last_health_check": time.time()
        }
        
        self.logger.info("Crawl4AI scraper initialized with 4-phase intelligent system")
    
    async def scrape_single_page(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PageResult:
        """Scrape a single page with optimized content extraction."""
        
        start_time = time.time()
        effective_config = config or self.config
        
        try:
            self.logger.info(f"Single page scraping: {url}")
            
            # Extract content using Phase 3 component
            results = await self.content_extractor.extract_content_parallel([url])
            
            if results and results[0].success:
                result = results[0]
                page_result = PageResult(
                    url=url,
                    content=result.content,
                    title=result.title,
                    metadata=result.metadata,
                    links=[],  # Single page doesn't extract links
                    images=[],
                    success=True,
                    status_code=result.metadata.get("status_code", 200),
                    response_time=result.extraction_time
                )
                
                self._update_stats(True, time.time() - start_time)
                return page_result
            else:
                error_msg = results[0].error if results else "Unknown extraction error"
                raise WebScraperException(f"Failed to extract content from {url}: {error_msg}")
        
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            self.logger.error(f"Single page scraping failed for {url}: {e}")
            raise
    
    async def scrape_multiple_pages(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """Scrape multiple pages with parallel extraction."""
        
        start_time = time.time()
        effective_config = config or self.config
        
        try:
            self.logger.info(f"Multi-page scraping: {len(urls)} URLs")
            
            # Use Phase 3 for parallel extraction
            extraction_results = await self.content_extractor.extract_content_parallel(
                urls, progress_callback
            )
            
            # Convert to PageResult objects
            pages = []
            for result in extraction_results:
                page_result = PageResult(
                    url=result.url,
                    content=result.content,
                    title=result.title,
                    metadata=result.metadata,
                    links=[],
                    images=[],
                    success=result.success,
                    status_code=result.metadata.get("status_code", 200) if result.metadata else 500,
                    response_time=result.extraction_time,
                    error=result.error
                )
                pages.append(page_result)
            
            # Build final result
            successful_pages = [p for p in pages if p.success]
            scraping_result = ScrapingResult(
                pages=pages,
                total_pages=len(pages),
                successful_pages=len(successful_pages),
                total_links=0,  # Multi-page mode doesn't aggregate links
                processing_time=time.time() - start_time,
                metadata={
                    "extraction_method": "parallel_crawl4ai",
                    "success_rate": len(successful_pages) / len(pages) if pages else 0.0,
                    "average_page_time": sum(p.response_time for p in pages) / len(pages) if pages else 0.0
                }
            )
            
            self._update_stats(True, time.time() - start_time)
            return scraping_result
        
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            self.logger.error(f"Multi-page scraping failed: {e}")
            raise
    
    async def scrape_website(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None,
        url_filter: Optional[ValidationCallback] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> ScrapingResult:
        """
        Execute complete 4-phase intelligent scraping for comprehensive business intelligence.
        
        This is the main entry point for Theodore's intelligent company research.
        """
        
        start_time = time.time()
        effective_config = config or self.config
        total_phases = 4
        
        try:
            self.logger.info(f"🚀 Starting 4-phase intelligent scraping for: {base_url}")
            
            # PHASE 1: Link Discovery
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.LINK_DISCOVERY, 1, total_phases,
                    "🔍 Phase 1: Multi-source link discovery starting",
                    {"base_url": base_url}
                ))
            
            discovered_urls = await self.link_discovery.discover_all_links(
                base_url, 
                max_depth=effective_config.max_depth,
                progress_callback=self._wrap_progress_callback(progress_callback, ScrapingPhase.LINK_DISCOVERY)
            )
            
            self.logger.info(f"🔍 Phase 1 Complete: {len(discovered_urls)} URLs discovered")
            
            # Apply URL filter if provided
            if url_filter:
                discovered_urls = [url for url in discovered_urls if url_filter(url)]
                self.logger.info(f"URL filter applied: {len(discovered_urls)} URLs remaining")
            
            # PHASE 2: AI-Powered Page Selection
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.PAGE_SELECTION, 2, total_phases,
                    "🎯 Phase 2: AI-powered page selection",
                    {"discovered_urls": len(discovered_urls)}
                ))
            
            selected_urls = await self.page_selector.select_valuable_pages(
                discovered_urls, 
                max_pages=effective_config.max_pages,
                base_url=base_url
            )
            
            self.logger.info(f"🎯 Phase 2 Complete: {len(selected_urls)} high-value pages selected")
            
            # PHASE 3: Parallel Content Extraction
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.CONTENT_EXTRACTION, 3, total_phases,
                    "📄 Phase 3: Parallel content extraction",
                    {"selected_pages": len(selected_urls)}
                ))
            
            extraction_results = await self.content_extractor.extract_content_parallel(
                selected_urls,
                progress_callback=self._wrap_progress_callback(progress_callback, ScrapingPhase.CONTENT_EXTRACTION)
            )
            
            successful_extractions = [r for r in extraction_results if r.success]
            self.logger.info(f"📄 Phase 3 Complete: {len(successful_extractions)}/{len(selected_urls)} pages extracted")
            
            # PHASE 4: AI Business Intelligence Aggregation
            if progress_callback:
                progress_callback(ScrapingProgress(
                    ScrapingPhase.AI_AGGREGATION, 4, total_phases,
                    "🧠 Phase 4: AI business intelligence generation",
                    {"content_pages": len(successful_extractions)}
                ))
            
            # Extract company name from base URL for intelligence generation
            company_name = self._extract_company_name(base_url)
            company_intelligence = await self.aggregator.aggregate_company_intelligence(
                company_name,
                extraction_results,
                progress_callback=self._wrap_progress_callback(progress_callback, ScrapingPhase.AI_AGGREGATION)
            )
            
            self.logger.info(f"🧠 Phase 4 Complete: Business intelligence generated (confidence: {company_intelligence.confidence_score:.2f})")
            
            # Convert extraction results to PageResult objects
            pages = []
            for result in extraction_results:
                page_result = PageResult(
                    url=result.url,
                    content=result.content,
                    title=result.title,
                    metadata=result.metadata,
                    links=[],
                    images=[],
                    success=result.success,
                    status_code=result.metadata.get("status_code", 200) if result.metadata else 500,
                    response_time=result.extraction_time,
                    error=result.error
                )
                pages.append(page_result)
            
            # Build comprehensive scraping result
            total_time = time.time() - start_time
            scraping_result = ScrapingResult(
                pages=pages,
                total_pages=len(pages),
                successful_pages=len(successful_extractions),
                total_links=len(discovered_urls),
                processing_time=total_time,
                metadata={
                    "scraping_method": "4_phase_intelligent",
                    "base_url": base_url,
                    "company_name": company_name,
                    "company_intelligence": company_intelligence.__dict__,
                    "phase_performance": {
                        "discovery_links": len(discovered_urls),
                        "selected_pages": len(selected_urls),
                        "extracted_pages": len(successful_extractions),
                        "intelligence_confidence": company_intelligence.confidence_score
                    },
                    "success_rate": len(successful_extractions) / len(selected_urls) if selected_urls else 0.0,
                    "performance_rating": self._calculate_performance_rating(total_time, len(successful_extractions))
                }
            )
            
            self._update_stats(True, total_time)
            self.logger.info(f"✅ 4-Phase intelligent scraping completed in {total_time:.2f}s")
            
            return scraping_result
        
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            self.logger.error(f"4-phase scraping failed for {base_url}: {e}")
            raise WebScraperException(f"Intelligent scraping failed: {e}")
    
    async def scrape_with_progress(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> ScrapingResult:
        """Scrape with integrated progress tracking."""
        
        # Convert ProgressTracker to ProgressCallback if needed
        progress_callback = None
        if progress_tracker:
            def callback(message: str, progress: float, details: Optional[str] = None):
                progress_tracker.update_progress(progress, message, details)
            progress_callback = callback
        
        # Use multi-page scraping for simplicity with progress tracking
        return await self.scrape_multiple_pages(urls, config, progress_callback)
    
    async def validate_url(self, url: str, timeout: float = 5.0) -> bool:
        """Quick URL accessibility check without full scraping."""
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.head(url) as response:
                    return 200 <= response.status < 400
        except Exception:
            return False
    
    async def discover_links(
        self,
        url: str,
        config: Optional[ScrapingConfig] = None,
        depth: int = 1
    ) -> List[str]:
        """Discover links using Phase 1 component."""
        try:
            return await self.link_discovery.discover_all_links(url, max_depth=depth)
        except Exception as e:
            self.logger.error(f"Link discovery failed for {url}: {e}")
            return [url]  # Return at least the original URL
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get scraper capabilities."""
        return {
            "javascript": True,
            "cookies": True,
            "custom_headers": True,
            "proxy_support": False,  # Not implemented yet
            "streaming": True,
            "caching": True,  # Crawl4AI has built-in caching
            "rate_limiting": True,
            "parallel_processing": True,
            "ai_selection": True,  # Unique to this implementation
            "business_intelligence": True,  # Unique to this implementation
            "multi_phase_extraction": True  # Unique to this implementation
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health and performance status."""
        current_time = time.time()
        
        # Calculate success rate
        total_requests = self._stats["requests_processed"]
        success_rate = (self._stats["success_count"] / total_requests) if total_requests > 0 else 1.0
        error_rate = (self._stats["error_count"] / total_requests) if total_requests > 0 else 0.0
        
        # Calculate average response time
        avg_response_time = (
            self._stats["total_response_time"] / total_requests
        ) if total_requests > 0 else 0.0
        
        # Determine health status
        if error_rate > 0.5:
            status = "unhealthy"
        elif error_rate > 0.2 or avg_response_time > 60:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "requests_processed": total_requests,
            "average_response_time": avg_response_time,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "last_check": current_time,
            "uptime": current_time - self._stats["last_health_check"],
            "ai_provider_available": self.ai_provider is not None,
            "components_status": {
                "link_discovery": "operational",
                "page_selector": "operational",
                "content_extractor": "operational", 
                "ai_aggregator": "operational"
            }
        }
    
    async def close(self) -> None:
        """Clean up resources."""
        try:
            await self.content_extractor._cleanup_crawler_pool()
            self.logger.info("Crawl4AI scraper resources cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
    
    # StreamingWebScraper implementation
    async def scrape_stream(
        self,
        urls: List[str],
        config: Optional[ScrapingConfig] = None
    ):
        """Stream page results as they complete."""
        
        # Create tasks for parallel extraction
        extraction_tasks = []
        for url in urls:
            task = asyncio.create_task(self.scrape_single_page(url, config))
            extraction_tasks.append(task)
        
        # Yield results as they complete
        for completed_task in asyncio.as_completed(extraction_tasks):
            try:
                page_result = await completed_task
                yield page_result
            except Exception as e:
                # Yield error result
                yield PageResult(
                    url="unknown",
                    content="",
                    success=False,
                    error=str(e)
                )
    
    async def scrape_with_discovery_stream(
        self,
        base_url: str,
        config: Optional[ScrapingConfig] = None
    ):
        """Stream results during discovery and extraction."""
        
        effective_config = config or self.config
        
        # Phase 1: Discover links
        discovered_urls = await self.link_discovery.discover_all_links(
            base_url, max_depth=effective_config.max_depth
        )
        
        # Phase 2: Select valuable pages
        selected_urls = await self.page_selector.select_valuable_pages(
            discovered_urls, max_pages=effective_config.max_pages, base_url=base_url
        )
        
        # Phase 3: Stream extraction results
        async for page_result in self.scrape_stream(selected_urls, config):
            yield page_result
    
    # Helper methods
    def _wrap_progress_callback(self, original_callback: Optional, phase: str) -> Optional:
        """Wrap progress callback to include phase information."""
        if not original_callback:
            return None
        
        def wrapped_callback(progress_info):
            # Add phase context to progress information
            if hasattr(progress_info, 'metadata'):
                progress_info.metadata = progress_info.metadata or {}
                progress_info.metadata['current_phase'] = phase
            
            original_callback(progress_info)
        
        return wrapped_callback
    
    def _extract_company_name(self, base_url: str) -> str:
        """Extract company name from URL for intelligence generation."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(base_url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes and suffixes
            domain = domain.replace('www.', '').replace('app.', '').replace('api.', '')
            
            # Extract main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                # Use the second-to-last part as company name
                company_name = parts[-2]
                # Capitalize first letter
                return company_name.capitalize()
            else:
                return domain.capitalize()
        
        except Exception:
            return "Unknown Company"
    
    def _update_stats(self, success: bool, response_time: float) -> None:
        """Update internal performance statistics."""
        self._stats["requests_processed"] += 1
        self._stats["total_response_time"] += response_time
        
        if success:
            self._stats["success_count"] += 1
        else:
            self._stats["error_count"] += 1
    
    def _calculate_performance_rating(self, total_time: float, pages_extracted: int) -> str:
        """Calculate performance rating based on time and pages extracted."""
        if total_time < 30 and pages_extracted >= 10:
            return "excellent"
        elif total_time < 60 and pages_extracted >= 5:
            return "good"
        elif total_time < 120:
            return "acceptable"
        else:
            return "slow"
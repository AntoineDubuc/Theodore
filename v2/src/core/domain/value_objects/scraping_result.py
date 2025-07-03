#!/usr/bin/env python3
"""
Theodore v2 Scraping Result Value Objects

Comprehensive result structures for web scraping operations including
individual page results, aggregated metrics, and operation summaries.
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict
import statistics


class ScrapingStatus(str, Enum):
    """Status of scraping operation"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"


class PageStatus(str, Enum):
    """Status of individual page scraping"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class PageResult:
    """Result for a single page"""
    url: str
    status: PageStatus
    content: Optional[str] = None
    html: Optional[str] = None
    links: List[str] = None
    images: List[str] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    status_code: Optional[int] = None
    content_length: int = 0
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.images is None:
            self.images = []
        if self.metadata is None:
            self.metadata = {}
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc)
    
    @property
    def is_successful(self) -> bool:
        return self.status == PageStatus.SUCCESS
    
    @property
    def has_content(self) -> bool:
        return self.content is not None and len(self.content.strip()) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class ScrapingMetrics:
    """Performance metrics for scraping operation"""
    total_pages_attempted: int = 0
    pages_successful: int = 0
    pages_failed: int = 0
    pages_skipped: int = 0
    total_content_size: int = 0
    average_response_time: float = 0.0
    total_duration: float = 0.0
    requests_per_second: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_pages_attempted == 0:
            return 0.0
        return self.pages_successful / self.total_pages_attempted
    
    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class ScrapingResult(BaseModel):
    """Complete result of a scraping operation"""
    
    # Operation metadata
    operation_id: str = Field(..., description="Unique identifier for this operation")
    status: ScrapingStatus = Field(..., description="Overall operation status")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Configuration used
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration used for scraping")
    
    # Results
    pages: List[PageResult] = Field(default_factory=list)
    primary_content: Optional[str] = Field(None, description="Main extracted content")
    
    # Aggregated data
    all_links: List[str] = Field(default_factory=list)
    all_images: List[str] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance and diagnostics
    metrics: ScrapingMetrics = Field(default_factory=ScrapingMetrics)
    error_details: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Raw response data (optional)
    raw_responses: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_page_result(self, page_result: PageResult) -> None:
        """Add a page result and update metrics"""
        self.pages.append(page_result)
        self._update_metrics(page_result)
        self._update_aggregated_data(page_result)
    
    def _update_metrics(self, page_result: PageResult) -> None:
        """Update performance metrics"""
        self.metrics.total_pages_attempted += 1
        
        if page_result.status == PageStatus.SUCCESS:
            self.metrics.pages_successful += 1
        elif page_result.status == PageStatus.FAILED:
            self.metrics.pages_failed += 1
        elif page_result.status == PageStatus.SKIPPED:
            self.metrics.pages_skipped += 1
        
        # Update content size
        if page_result.content:
            self.metrics.total_content_size += len(page_result.content)
        
        # Update response time
        if self.metrics.total_pages_attempted > 0:
            total_time = (self.metrics.average_response_time * 
                         (self.metrics.total_pages_attempted - 1) + 
                         page_result.response_time)
            self.metrics.average_response_time = total_time / self.metrics.total_pages_attempted
    
    def _update_aggregated_data(self, page_result: PageResult) -> None:
        """Update aggregated links and images"""
        if page_result.links:
            self.all_links.extend(page_result.links)
        if page_result.images:
            self.all_images.extend(page_result.images)
        
        # Deduplicate
        self.all_links = list(set(self.all_links))
        self.all_images = list(set(self.all_images))
    
    def finalize(self) -> None:
        """Finalize the result after all pages are processed"""
        self.completed_at = datetime.now(timezone.utc)
        
        # Calculate total duration
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.metrics.total_duration = duration
            
            # Calculate requests per second
            if duration > 0:
                self.metrics.requests_per_second = self.metrics.total_pages_attempted / duration
        
        # Set primary content (combine successful pages)
        successful_content = []
        for page in self.pages:
            if page.is_successful and page.has_content:
                successful_content.append(page.content)
        
        self.primary_content = "\n\n".join(successful_content)
        
        # Determine overall status
        if self.metrics.pages_successful == 0:
            self.status = ScrapingStatus.FAILED
        elif self.metrics.success_rate >= 0.8:
            self.status = ScrapingStatus.SUCCESS
        else:
            self.status = ScrapingStatus.PARTIAL_SUCCESS
    
    @property
    def is_successful(self) -> bool:
        return self.status in [ScrapingStatus.SUCCESS, ScrapingStatus.PARTIAL_SUCCESS]
    
    @property
    def has_content(self) -> bool:
        return self.primary_content is not None and len(self.primary_content.strip()) > 0
    
    @property
    def successful_pages(self) -> List[PageResult]:
        return [page for page in self.pages if page.is_successful]
    
    @property
    def failed_pages(self) -> List[PageResult]:
        return [page for page in self.pages if page.status == PageStatus.FAILED]
    
    def get_content_by_url(self, url: str) -> Optional[str]:
        """Get content for a specific URL"""
        for page in self.pages:
            if page.url == url and page.has_content:
                return page.content
        return None
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Get a summary dictionary for logging/reporting"""
        return {
            "operation_id": self.operation_id,
            "status": self.status,
            "pages_attempted": self.metrics.total_pages_attempted,
            "pages_successful": self.metrics.pages_successful,
            "success_rate": self.metrics.success_rate,
            "total_content_size": self.metrics.total_content_size,
            "duration": self.metrics.total_duration,
            "has_content": self.has_content
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        response_times = [page.response_time for page in self.pages if page.response_time > 0]
        
        performance_data = {
            "total_duration": self.metrics.total_duration,
            "pages_processed": len(self.pages),
            "success_rate": self.metrics.success_rate,
            "requests_per_second": self.metrics.requests_per_second,
            "average_response_time": self.metrics.average_response_time,
            "total_content_size": self.metrics.total_content_size,
        }
        
        if response_times:
            performance_data.update({
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            })
        
        return performance_data
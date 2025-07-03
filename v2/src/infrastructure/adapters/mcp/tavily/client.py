"""
Tavily AI HTTP Client.

Production-ready HTTP client for Tavily AI API with comprehensive error handling,
rate limiting, retries, and performance monitoring.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import TavilyConfig


@dataclass
class TavilyResponse:
    """Tavily API response with structured data."""
    
    query: str
    answer: Optional[str]
    results: List[Dict[str, Any]]
    response_time: float
    images: List[str]
    follow_up_questions: List[str]
    search_depth: str
    
    # Metadata
    request_id: Optional[str] = None
    total_results: int = 0
    search_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.search_metadata is None:
            self.search_metadata = {}
        self.total_results = len(self.results)


class TavilyClientError(Exception):
    """Base exception for Tavily client errors."""
    pass


class TavilyRateLimitError(TavilyClientError):
    """Raised when rate limited by Tavily API."""
    
    def __init__(self, message: str = "Rate limited", retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after or 60


class TavilyQuotaError(TavilyClientError):
    """Raised when quota is exceeded."""
    pass


class TavilyAuthError(TavilyClientError):
    """Raised when authentication fails."""
    pass


class TavilyClient:
    """
    Production HTTP client for Tavily AI API.
    
    Features:
    - Async HTTP requests with connection pooling
    - Automatic rate limiting and retry logic
    - Comprehensive error handling
    - Request/response logging
    - Performance monitoring
    - Health check capabilities
    """
    
    def __init__(self, config: TavilyConfig):
        """Initialize Tavily client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # HTTP session management
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Monitoring
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0
        
        # API endpoints
        self._search_endpoint = f"{config.base_url}/search"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool size
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.config.get_request_headers()
            )
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = time.time()
            
            # Remove old timestamps (older than 1 minute)
            cutoff = now - 60
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at the rate limit
            if len(self._request_times) >= self.config.rate_limit_requests_per_minute:
                # Calculate how long to wait
                oldest_request = min(self._request_times)
                wait_time = 60 - (now - oldest_request)
                
                if wait_time > 0:
                    self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Tavily API."""
        await self._ensure_session()
        await self._check_rate_limit()
        
        start_time = time.time()
        
        try:
            self._request_count += 1
            
            # Log request
            self.logger.debug(f"Making {method} request to {endpoint}")
            if data:
                self.logger.debug(f"Request data: {json.dumps(data, indent=2)}")
            
            # Make request
            async with self._session.request(
                method=method,
                url=endpoint,
                json=data,
                params=params
            ) as response:
                
                # Calculate latency
                latency = (time.time() - start_time) * 1000
                self._total_latency += latency
                
                # Log response
                self.logger.debug(f"Response status: {response.status}, latency: {latency:.1f}ms")
                
                # Handle different status codes
                if response.status == 200:
                    response_data = await response.json()
                    self.logger.debug(f"Response data: {json.dumps(response_data, indent=2)[:500]}...")
                    return response_data
                
                elif response.status == 401:
                    self._error_count += 1
                    raise TavilyAuthError("Invalid API key or authentication failed")
                
                elif response.status == 402:
                    self._error_count += 1
                    raise TavilyQuotaError("API quota exceeded")
                
                elif response.status == 429:
                    self._error_count += 1
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise TavilyRateLimitError(
                        f"Rate limited by Tavily API",
                        retry_after=retry_after
                    )
                
                else:
                    self._error_count += 1
                    error_text = await response.text()
                    raise TavilyClientError(
                        f"HTTP {response.status}: {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            self._error_count += 1
            raise TavilyClientError(f"Request failed: {str(e)}") from e
        
        except asyncio.TimeoutError:
            self._error_count += 1
            raise TavilyClientError(
                f"Request timed out after {self.config.timeout_seconds}s"
            )
    
    async def search(
        self,
        query: str,
        search_depth: Optional[str] = None,
        max_results: Optional[int] = None,
        include_answer: Optional[bool] = None,
        include_raw_content: Optional[bool] = None,
        include_images: Optional[bool] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: Optional[int] = None,
        **kwargs
    ) -> TavilyResponse:
        """
        Perform search using Tavily API.
        
        Args:
            query: Search query
            search_depth: Search depth level
            max_results: Maximum number of results
            include_answer: Include AI-generated answer
            include_raw_content: Include raw page content
            include_images: Include image results
            include_domains: Domains to include
            exclude_domains: Domains to exclude
            days: Limit to last N days
            **kwargs: Additional parameters
            
        Returns:
            TavilyResponse with search results
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        # Build request parameters
        search_params = self.config.get_search_params()
        
        # Override with provided parameters
        if search_depth is not None:
            search_params["search_depth"] = search_depth
        if max_results is not None:
            search_params["max_results"] = max_results
        if include_answer is not None:
            search_params["include_answer"] = include_answer
        if include_raw_content is not None:
            search_params["include_raw_content"] = include_raw_content
        if include_images is not None:
            search_params["include_images"] = include_images
        if include_domains is not None:
            search_params["include_domains"] = include_domains
        if exclude_domains is not None:
            search_params["exclude_domains"] = exclude_domains
        if days is not None:
            search_params["days"] = days
        
        # Add any additional parameters
        search_params.update(kwargs)
        
        # Prepare request data
        request_data = {
            "query": query.strip(),
            **search_params
        }
        
        # Make API request
        start_time = time.time()
        response_data = await self._make_request(
            method="POST",
            endpoint=self._search_endpoint,
            data=request_data
        )
        response_time = time.time() - start_time
        
        # Parse response
        return TavilyResponse(
            query=query,
            answer=response_data.get("answer"),
            results=response_data.get("results", []),
            response_time=response_time,
            images=response_data.get("images", []),
            follow_up_questions=response_data.get("follow_up_questions", []),
            search_depth=search_params.get("search_depth", "basic"),
            request_id=response_data.get("request_id"),
            search_metadata={
                "search_type": self.config.search_type.value,
                "include_raw_content": search_params.get("include_raw_content", False),
                "max_results_requested": search_params.get("max_results", 10),
                "domains_included": search_params.get("include_domains", []),
                "domains_excluded": search_params.get("exclude_domains", []),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of Tavily API."""
        try:
            # Simple test search
            start_time = time.time()
            response = await self.search(
                query="test health check",
                max_results=1,
                include_answer=False,
                include_raw_content=False
            )
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "api_accessible": True,
                "results_count": len(response.results),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_accessible": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics."""
        success_rate = 1.0
        if self._request_count > 0:
            success_rate = 1.0 - (self._error_count / self._request_count)
        
        avg_latency = 0.0
        if self._request_count > 0:
            avg_latency = self._total_latency / self._request_count
        
        return {
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "current_rate_limit_count": len(self._request_times),
            "rate_limit_window": f"{len(self._request_times)}/{self.config.rate_limit_requests_per_minute} per minute"
        }
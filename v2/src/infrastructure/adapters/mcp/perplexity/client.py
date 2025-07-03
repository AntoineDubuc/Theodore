"""
Perplexity AI HTTP client.

Provides enterprise-grade HTTP client for Perplexity AI API with comprehensive
error handling, rate limiting, retries, and monitoring capabilities.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import aiohttp
import json
from dataclasses import dataclass
import logging
from contextlib import asynccontextmanager

from .config import PerplexityConfig


@dataclass
class PerplexityResponse:
    """Response from Perplexity AI API."""
    
    content: str
    citations: List[str]
    search_time_ms: float
    model: str
    usage: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    
    requests_remaining: int
    reset_time: float
    retry_after: Optional[int] = None


class PerplexityClientError(Exception):
    """Base exception for Perplexity client errors."""
    pass


class PerplexityRateLimitError(PerplexityClientError):
    """Raised when rate limited by Perplexity API."""
    
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = "Rate limited by Perplexity API"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message)


class PerplexityQuotaError(PerplexityClientError):
    """Raised when API quota is exceeded."""
    pass


class PerplexityAuthError(PerplexityClientError):
    """Raised when authentication fails."""
    pass


class PerplexityClient:
    """
    Production-grade HTTP client for Perplexity AI API.
    
    Features:
    - Connection pooling and keep-alive
    - Automatic retries with exponential backoff
    - Rate limiting and quota management
    - Request/response monitoring
    - Health check capabilities
    """
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(self, config: PerplexityConfig):
        """
        Initialize Perplexity client.
        
        Args:
            config: Perplexity configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # Monitoring
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0
        self._last_health_check = 0.0
        
        # Cache for health status
        self._health_status = "unknown"
        self._last_error: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is initialized."""
        if self._session is None or self._session.closed:
            # Configure connector with connection pooling
            self._connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            # Configure session
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout_seconds,
                connect=10.0,
                sock_read=self.config.timeout_seconds
            )
            
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers=self.config.get_request_headers(),
                raise_for_status=False  # Handle status codes manually
            )
    
    async def close(self) -> None:
        """Close HTTP session and clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        
        if self._connector:
            await self._connector.close()
        
        self._session = None
        self._connector = None
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            cutoff = now - 60.0
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at the limit
            if len(self._request_times) >= self.config.rate_limit_requests_per_minute:
                # Calculate delay needed
                oldest_request = min(self._request_times)
                delay = 60.0 - (now - oldest_request)
                
                if delay > 0:
                    self.logger.warning(f"Rate limit reached, waiting {delay:.1f}s")
                    await asyncio.sleep(delay)
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and retries.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            params: URL parameters
            
        Returns:
            Response data
            
        Raises:
            PerplexityClientError: On API errors
        """
        await self._ensure_session()
        await self._check_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries + 1):
            start_time = time.time()
            
            try:
                # Make the request
                async with self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    
                    # Record metrics
                    request_time = (time.time() - start_time) * 1000
                    self._request_count += 1
                    self._total_latency += request_time
                    
                    # Handle response
                    response_data = await response.json()
                    
                    if response.status == 200:
                        self._health_status = "healthy"
                        self._last_error = None
                        return response_data
                    
                    elif response.status == 429:
                        # Rate limited
                        retry_after = response.headers.get('Retry-After')
                        retry_after = int(retry_after) if retry_after else None
                        
                        if attempt < self.config.max_retries:
                            delay = retry_after or (2 ** attempt)
                            self.logger.warning(f"Rate limited, retrying in {delay}s")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise PerplexityRateLimitError(retry_after)
                    
                    elif response.status == 401:
                        raise PerplexityAuthError("Invalid API key")
                    
                    elif response.status == 402:
                        raise PerplexityQuotaError("API quota exceeded")
                    
                    else:
                        error_msg = response_data.get('error', f"HTTP {response.status}")
                        
                        if attempt < self.config.max_retries and response.status >= 500:
                            # Retry on server errors
                            delay = self.config.retry_delay_seconds
                            if self.config.retry_exponential_backoff:
                                delay *= (2 ** attempt)
                            
                            self.logger.warning(f"Server error {response.status}, retrying in {delay}s")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise PerplexityClientError(f"API error: {error_msg}")
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self._error_count += 1
                self._health_status = "unhealthy"
                self._last_error = str(e)
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay_seconds
                    if self.config.retry_exponential_backoff:
                        delay *= (2 ** attempt)
                    
                    self.logger.warning(f"Request failed: {e}, retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise PerplexityClientError(f"Request failed after {self.config.max_retries + 1} attempts: {e}")
        
        # Should never reach here
        raise PerplexityClientError("Unexpected error in request handling")
    
    async def search(
        self,
        query: str,
        model: Optional[str] = None,
        search_focus: Optional[str] = None,
        search_recency_filter: Optional[str] = None,
        return_citations: bool = True,
        return_images: bool = False
    ) -> PerplexityResponse:
        """
        Perform search using Perplexity AI.
        
        Args:
            query: Search query
            model: Model to use (defaults to config model)
            search_focus: Search focus (web, news, etc.)
            search_recency_filter: Recency filter
            return_citations: Include citations in response
            return_images: Include images in response
            
        Returns:
            Perplexity search response
            
        Raises:
            PerplexityClientError: On API errors
        """
        start_time = time.time()
        
        # Prepare request data
        data = {
            "model": model or self.config.model.value,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful search assistant providing comprehensive information about companies."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.2,
            "return_citations": return_citations,
            "return_images": return_images
        }
        
        # Add optional parameters
        if search_focus:
            data["search_domain_filter"] = [search_focus]
        
        if search_recency_filter:
            data["search_recency_filter"] = search_recency_filter
        
        # Make the request
        response_data = await self._make_request("POST", "/chat/completions", data=data)
        
        # Extract response data
        search_time_ms = (time.time() - start_time) * 1000
        
        choices = response_data.get("choices", [])
        if not choices:
            raise PerplexityClientError("No response choices returned")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        # Extract citations
        citations = []
        if return_citations and "citations" in response_data:
            citations = response_data["citations"]
        
        # Extract usage info
        usage = response_data.get("usage", {})
        
        return PerplexityResponse(
            content=content,
            citations=citations,
            search_time_ms=search_time_ms,
            model=data["model"],
            usage=usage,
            metadata={
                "search_focus": search_focus,
                "recency_filter": search_recency_filter,
                "request_id": response_data.get("id"),
                "choices_count": len(choices)
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Perplexity API.
        
        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            
            # Simple test query
            await self.search(
                query="test query for health check",
                model=self.config.model.value
            )
            
            latency = (time.time() - start_time) * 1000
            
            # Calculate success rate
            total_requests = self._request_count
            success_rate = 1.0 if total_requests == 0 else (total_requests - self._error_count) / total_requests
            
            # Calculate average latency
            avg_latency = 0.0 if total_requests == 0 else self._total_latency / total_requests
            
            self._health_status = "healthy"
            self._last_health_check = time.time()
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "average_latency_ms": avg_latency,
                "success_rate": success_rate,
                "total_requests": total_requests,
                "error_count": self._error_count,
                "last_check": self._last_health_check,
                "rate_limit_remaining": max(0, self.config.rate_limit_requests_per_minute - len(self._request_times))
            }
        
        except Exception as e:
            self._health_status = "unhealthy"
            self._last_error = str(e)
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_error": self._last_error,
                "total_requests": self._request_count,
                "error_count": self._error_count
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client performance metrics.
        
        Returns:
            Performance metrics
        """
        total_requests = self._request_count
        success_rate = 1.0 if total_requests == 0 else (total_requests - self._error_count) / total_requests
        avg_latency = 0.0 if total_requests == 0 else self._total_latency / total_requests
        
        return {
            "total_requests": total_requests,
            "error_count": self._error_count,
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "health_status": self._health_status,
            "last_error": self._last_error,
            "active_connections": len(self._request_times),
            "rate_limit_remaining": max(0, self.config.rate_limit_requests_per_minute - len(self._request_times))
        }
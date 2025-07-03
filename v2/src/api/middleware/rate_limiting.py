#!/usr/bin/env python3
"""
Theodore v2 API Rate Limiting Middleware

Advanced rate limiting with user quotas and fair usage policies.
"""

import time
import asyncio
from typing import Callable, Dict, Optional
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from ...infrastructure.observability.logging import get_logger
from ..models.responses import ErrorResponse

logger = get_logger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with sliding window and user quotas
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Rate limit configurations
        self.limits = {
            # Global limits (per IP)
            "global": {"requests": 1000, "window": 3600},  # 1000 req/hour
            
            # Endpoint-specific limits
            "/api/v2/research": {"requests": 100, "window": 3600},  # 100 research/hour
            "/api/v2/discover": {"requests": 200, "window": 3600},  # 200 discovery/hour
            "/api/v2/batch": {"requests": 10, "window": 3600},      # 10 batch jobs/hour
            
            # Auth endpoints
            "/api/v2/auth/login": {"requests": 10, "window": 900},  # 10 login attempts/15min
            
            # System endpoints (higher limits)
            "/api/v2/health": {"requests": 1000, "window": 60},     # 1000 health checks/min
            "/api/v2/metrics": {"requests": 100, "window": 60},     # 100 metrics calls/min
        }
        
        # User-specific rate limits (higher than IP-based)
        self.user_limits = {
            "research": {"requests": 500, "window": 3600},    # 500 research/hour per user
            "discovery": {"requests": 1000, "window": 3600},  # 1000 discovery/hour per user
            "batch": {"requests": 50, "window": 3600},        # 50 batch jobs/hour per user
        }
        
        # Storage for tracking requests
        self.ip_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.user_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting before processing request"""
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        
        # Get endpoint for rate limiting
        endpoint = self._get_rate_limit_endpoint(request.url.path)
        
        # Check rate limits
        rate_limit_result = await self._check_rate_limits(client_ip, user_id, endpoint, request.method)
        
        if not rate_limit_result["allowed"]:
            # Rate limit exceeded
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "limit_type": rate_limit_result["limit_type"],
                    "retry_after": rate_limit_result["retry_after"]
                }
            )
            
            return self._create_rate_limit_response(rate_limit_result)
        
        # Record the request
        await self._record_request(client_ip, user_id, endpoint)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip, user_id, endpoint)
        
        return response
    
    async def _check_rate_limits(self, client_ip: str, user_id: Optional[str], endpoint: str, method: str) -> dict:
        """Check if request is within rate limits"""
        
        current_time = time.time()
        
        # Skip rate limiting for certain methods/endpoints
        if method in ["OPTIONS"] or endpoint in ["/", "/ping"]:
            return {"allowed": True}
        
        # Check IP-based global limit
        global_limit = self.limits["global"]
        ip_global_requests = self.ip_requests[client_ip]["global"]
        
        # Clean old requests
        self._clean_old_requests(ip_global_requests, current_time, global_limit["window"])
        
        if len(ip_global_requests) >= global_limit["requests"]:
            return {
                "allowed": False,
                "limit_type": "global_ip",
                "retry_after": self._calculate_retry_after(ip_global_requests, global_limit["window"])
            }
        
        # Check endpoint-specific IP limit
        if endpoint in self.limits:
            endpoint_limit = self.limits[endpoint]
            ip_endpoint_requests = self.ip_requests[client_ip][endpoint]
            
            self._clean_old_requests(ip_endpoint_requests, current_time, endpoint_limit["window"])
            
            if len(ip_endpoint_requests) >= endpoint_limit["requests"]:
                return {
                    "allowed": False,
                    "limit_type": "endpoint_ip",
                    "retry_after": self._calculate_retry_after(ip_endpoint_requests, endpoint_limit["window"])
                }
        
        # Check user-specific limits (if authenticated)
        if user_id:
            user_limit_key = self._get_user_limit_key(endpoint)
            if user_limit_key and user_limit_key in self.user_limits:
                user_limit = self.user_limits[user_limit_key]
                user_requests = self.user_requests[user_id][user_limit_key]
                
                self._clean_old_requests(user_requests, current_time, user_limit["window"])
                
                if len(user_requests) >= user_limit["requests"]:
                    return {
                        "allowed": False,
                        "limit_type": "user",
                        "retry_after": self._calculate_retry_after(user_requests, user_limit["window"])
                    }
        
        return {"allowed": True}
    
    async def _record_request(self, client_ip: str, user_id: Optional[str], endpoint: str):
        """Record a request for rate limiting tracking"""
        
        current_time = time.time()
        
        # Record IP-based requests
        self.ip_requests[client_ip]["global"].append(current_time)
        
        if endpoint in self.limits:
            self.ip_requests[client_ip][endpoint].append(current_time)
        
        # Record user-based requests
        if user_id:
            user_limit_key = self._get_user_limit_key(endpoint)
            if user_limit_key and user_limit_key in self.user_limits:
                self.user_requests[user_id][user_limit_key].append(current_time)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated)"""
        
        # This would integrate with the authentication system
        # For now, return None (unauthenticated)
        return getattr(request.state, "user_id", None)
    
    def _get_rate_limit_endpoint(self, path: str) -> str:
        """Get the endpoint key for rate limiting"""
        
        # Normalize path for rate limiting
        path = path.rstrip('/')
        
        # Check for exact matches first
        if path in self.limits:
            return path
        
        # Check for prefix matches
        for endpoint_path in self.limits:
            if path.startswith(endpoint_path + "/"):
                return endpoint_path
        
        # Return the base path for grouping
        if path.startswith('/api/v2/research'):
            return '/api/v2/research'
        elif path.startswith('/api/v2/discover'):
            return '/api/v2/discover'
        elif path.startswith('/api/v2/batch'):
            return '/api/v2/batch'
        elif path.startswith('/api/v2/auth'):
            return '/api/v2/auth/login'  # Group auth endpoints
        
        return path
    
    def _get_user_limit_key(self, endpoint: str) -> Optional[str]:
        """Get user limit key from endpoint"""
        
        if endpoint.startswith('/api/v2/research'):
            return 'research'
        elif endpoint.startswith('/api/v2/discover'):
            return 'discovery'
        elif endpoint.startswith('/api/v2/batch'):
            return 'batch'
        
        return None
    
    def _clean_old_requests(self, requests: deque, current_time: float, window: int):
        """Remove requests outside the time window"""
        
        cutoff_time = current_time - window
        while requests and requests[0] < cutoff_time:
            requests.popleft()
    
    def _calculate_retry_after(self, requests: deque, window: int) -> int:
        """Calculate retry-after time in seconds"""
        
        if not requests:
            return 1
        
        # Time until the oldest request expires
        oldest_request = requests[0]
        current_time = time.time()
        retry_after = int(oldest_request + window - current_time) + 1
        
        return max(1, retry_after)
    
    def _create_rate_limit_response(self, rate_limit_result: dict) -> JSONResponse:
        """Create rate limit exceeded response"""
        
        retry_after = rate_limit_result["retry_after"]
        
        error_response = ErrorResponse(
            error="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            status_code=429,
            timestamp=time.time(),
            details={
                "limit_type": rate_limit_result["limit_type"],
                "retry_after_seconds": retry_after
            }
        )
        
        return JSONResponse(
            status_code=429,
            content=error_response.dict(),
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": "See API documentation",
                "X-RateLimit-Remaining": "0"
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str, user_id: Optional[str], endpoint: str):
        """Add rate limit information to response headers"""
        
        current_time = time.time()
        
        # Add basic rate limit headers
        if endpoint in self.limits:
            limit_config = self.limits[endpoint]
            requests = self.ip_requests[client_ip][endpoint]
            self._clean_old_requests(requests, current_time, limit_config["window"])
            
            remaining = max(0, limit_config["requests"] - len(requests))
            
            response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(limit_config["window"])
        
        # Add global rate limit info
        global_limit = self.limits["global"]
        global_requests = self.ip_requests[client_ip]["global"]
        self._clean_old_requests(global_requests, current_time, global_limit["window"])
        
        global_remaining = max(0, global_limit["requests"] - len(global_requests))
        response.headers["X-RateLimit-Global-Remaining"] = str(global_remaining)
    
    def _start_cleanup_task(self):
        """Start background task for cleaning up old request records"""
        
        async def cleanup_old_records():
            """Periodically clean up old request records"""
            while True:
                try:
                    await asyncio.sleep(300)  # Clean up every 5 minutes
                    current_time = time.time()
                    
                    # Clean IP requests
                    for ip, endpoints in list(self.ip_requests.items()):
                        for endpoint, requests in list(endpoints.items()):
                            window = self.limits.get(endpoint, self.limits["global"])["window"]
                            self._clean_old_requests(requests, current_time, window)
                            
                            # Remove empty queues
                            if not requests:
                                del endpoints[endpoint]
                        
                        # Remove empty IP records
                        if not endpoints:
                            del self.ip_requests[ip]
                    
                    # Clean user requests
                    for user_id, limit_types in list(self.user_requests.items()):
                        for limit_type, requests in list(limit_types.items()):
                            if limit_type in self.user_limits:
                                window = self.user_limits[limit_type]["window"]
                                self._clean_old_requests(requests, current_time, window)
                                
                                # Remove empty queues
                                if not requests:
                                    del limit_types[limit_type]
                        
                        # Remove empty user records
                        if not limit_types:
                            del self.user_requests[user_id]
                
                except Exception as e:
                    logger.error(f"Error in rate limit cleanup: {e}")
        
        # Only start if not already running
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(cleanup_old_records())
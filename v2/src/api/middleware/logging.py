#!/usr/bin/env python3
"""
Theodore v2 API Request Logging Middleware

Comprehensive request/response logging with performance metrics.
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ...infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_headers = {
            "authorization", "x-api-key", "cookie", "set-cookie"
        }
        self.log_body_paths = {"/api/v2/research", "/api/v2/discover", "/api/v2/batch"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with performance metrics"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to state for use in handlers
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            await self._log_response(request, response, request_id, duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # Re-raise exception
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Get filtered headers
        headers = self._filter_headers(dict(request.headers))
        
        # Prepare log data
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": headers,
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length")
        }
        
        # Add body for specific endpoints (if small enough)
        if (request.url.path in self.log_body_paths and 
            request.headers.get("content-type", "").startswith("application/json")):
            
            try:
                content_length = int(request.headers.get("content-length", "0"))
                if content_length < 10000:  # Only log bodies < 10KB
                    body = await request.body()
                    if body:
                        log_data["body_preview"] = body.decode("utf-8")[:1000]
            except Exception:
                # Skip body logging if there's an issue
                pass
        
        logger.info("API request received", extra=log_data)
    
    async def _log_response(self, request: Request, response: Response, request_id: str, duration: float):
        """Log response details and performance metrics"""
        
        # Prepare log data
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_headers": self._filter_headers(dict(response.headers))
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error("API request completed with server error", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("API request completed with client error", extra=log_data)
        else:
            logger.info("API request completed successfully", extra=log_data)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        # Check for forwarded headers (from load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _filter_headers(self, headers: dict) -> dict:
        """Filter sensitive headers from logs"""
        
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in self.sensitive_headers:
                # Mask sensitive headers
                if key_lower == "authorization":
                    if value.startswith("Bearer "):
                        filtered[key] = "Bearer ***"
                    else:
                        filtered[key] = "***"
                else:
                    filtered[key] = "***"
            else:
                filtered[key] = value
        
        return filtered
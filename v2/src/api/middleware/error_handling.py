#!/usr/bin/env python3
"""
Theodore v2 API Error Handling Middleware

Comprehensive error handling and response standardization.
"""

import traceback
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ..models.responses import ErrorResponse

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error handling middleware with structured error responses
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Map exception types to error codes and status codes
        self.exception_mapping = {
            "ValueError": {"code": "INVALID_INPUT", "status": 400},
            "TypeError": {"code": "TYPE_ERROR", "status": 400},
            "KeyError": {"code": "MISSING_FIELD", "status": 400},
            "AttributeError": {"code": "ATTRIBUTE_ERROR", "status": 400},
            "NotImplementedError": {"code": "NOT_IMPLEMENTED", "status": 501},
            "PermissionError": {"code": "PERMISSION_DENIED", "status": 403},
            "FileNotFoundError": {"code": "RESOURCE_NOT_FOUND", "status": 404},
            "TimeoutError": {"code": "REQUEST_TIMEOUT", "status": 408},
            "ConnectionError": {"code": "CONNECTION_ERROR", "status": 503},
            "MemoryError": {"code": "INSUFFICIENT_MEMORY", "status": 507},
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and standardize error responses"""
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            return await self._handle_exception(request, e)
    
    async def _handle_exception(self, request: Request, exception: Exception) -> JSONResponse:
        """Handle and format exceptions into standardized responses"""
        
        # Get request ID if available
        request_id = getattr(request.state, "request_id", None)
        
        # Determine error details
        exception_type = type(exception).__name__
        error_mapping = self.exception_mapping.get(exception_type, {
            "code": "INTERNAL_SERVER_ERROR",
            "status": 500
        })
        
        error_code = error_mapping["code"]
        status_code = error_mapping["status"]
        
        # Create error response
        error_response = ErrorResponse(
            error=error_code,
            message=str(exception),
            status_code=status_code,
            timestamp=None,  # Will be set by the model
            path=request.url.path,
            request_id=request_id
        )
        
        # Add exception details for server errors (in development)
        if status_code >= 500:
            import os
            if os.getenv("ENVIRONMENT", "development").lower() == "development":
                error_response.details = {
                    "exception_type": exception_type,
                    "traceback": traceback.format_exc()
                }
        
        # Log the error
        await self._log_error(request, exception, error_response, request_id)
        
        # Record metrics
        self._record_error_metrics(request, exception_type, status_code)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    async def _log_error(self, request: Request, exception: Exception, error_response: ErrorResponse, request_id: str):
        """Log error details with appropriate level"""
        
        # Prepare log data
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "error_code": error_response.error,
            "error_message": error_response.message,
            "status_code": error_response.status_code,
            "exception_type": type(exception).__name__,
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": self._get_client_ip(request)
        }
        
        # Add user context if available
        if hasattr(request.state, "user_id"):
            log_data["user_id"] = request.state.user_id
        
        # Determine log level based on status code
        if error_response.status_code >= 500:
            # Server errors - log with full traceback
            logger.error(
                f"Server error: {error_response.message}",
                extra=log_data,
                exc_info=True
            )
        elif error_response.status_code >= 400:
            # Client errors - log as warning
            logger.warning(
                f"Client error: {error_response.message}",
                extra=log_data
            )
        else:
            # Other errors - log as info
            logger.info(
                f"Request error: {error_response.message}",
                extra=log_data
            )
    
    def _record_error_metrics(self, request: Request, exception_type: str, status_code: int):
        """Record error metrics"""
        
        tags = {
            "method": request.method,
            "endpoint": self._normalize_endpoint(request.url.path),
            "exception_type": exception_type,
            "status_code": str(status_code)
        }
        
        # Record exception
        metrics.increment_counter("api_exceptions_total", tags=tags)
        
        # Record error by type
        if status_code >= 500:
            metrics.increment_counter("api_server_errors_total", tags=tags)
        elif status_code >= 400:
            metrics.increment_counter("api_client_errors_total", tags=tags)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics"""
        
        path = path.rstrip('/')
        
        # Group dynamic paths
        if path.startswith('/api/v2/research/'):
            return '/api/v2/research/{id}'
        elif path.startswith('/api/v2/discover/'):
            return '/api/v2/discover/{id}'
        elif path.startswith('/api/v2/batch/jobs/'):
            return '/api/v2/batch/jobs/{id}'
        elif path.startswith('/api/v2/plugins/'):
            return '/api/v2/plugins/{name}'
        
        return path or '/'
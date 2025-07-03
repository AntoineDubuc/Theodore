#!/usr/bin/env python3
"""
Theodore v2 API Metrics Middleware

Request metrics collection and performance monitoring.
"""

import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ...infrastructure.observability.metrics import get_metrics_collector

metrics = get_metrics_collector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting API metrics and performance data
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for request/response cycle"""
        
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        endpoint = self._normalize_endpoint(path)
        
        # Increment request counter
        metrics.increment_counter(
            "api_requests_total",
            tags={
                "method": method,
                "endpoint": endpoint
            }
        )
        
        # Track concurrent requests
        metrics.increment_gauge("api_requests_active")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record response metrics
            self._record_response_metrics(method, endpoint, response.status_code, duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record error metrics
            self._record_error_metrics(method, endpoint, type(e).__name__, duration)
            
            # Re-raise exception
            raise
            
        finally:
            # Decrement active requests
            metrics.decrement_gauge("api_requests_active")
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics grouping"""
        
        # Remove trailing slash
        path = path.rstrip('/')
        
        # Group similar endpoints
        if path.startswith('/api/v2/research/'):
            if path.endswith('/progress'):
                return '/api/v2/research/{id}/progress'
            else:
                return '/api/v2/research/{id}'
        elif path.startswith('/api/v2/discover/'):
            if path.endswith('/progress'):
                return '/api/v2/discover/{id}/progress'
            else:
                return '/api/v2/discover/{id}'
        elif path.startswith('/api/v2/batch/jobs/'):
            parts = path.split('/')
            if len(parts) >= 6:
                action = parts[5] if len(parts) > 5 else ''
                if action in ['pause', 'resume']:
                    return f'/api/v2/batch/jobs/{{id}}/{action}'
                else:
                    return '/api/v2/batch/jobs/{id}'
            return '/api/v2/batch/jobs'
        elif path.startswith('/api/v2/plugins/'):
            parts = path.split('/')
            if len(parts) >= 5:
                action = parts[4] if len(parts) > 4 else ''
                if action in ['install', 'enable', 'disable', 'status']:
                    return f'/api/v2/plugins/{{name}}/{action}'
                else:
                    return '/api/v2/plugins/{name}'
            return '/api/v2/plugins'
        elif path.startswith('/api/v2/ws/'):
            return '/api/v2/ws/*'
        
        # Return path as-is for other endpoints
        return path or '/'
    
    def _record_response_metrics(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record response metrics"""
        
        tags = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
            "status_class": f"{status_code // 100}xx"
        }
        
        # Response counter
        metrics.increment_counter("api_responses_total", tags=tags)
        
        # Response duration
        metrics.record_histogram(
            "api_request_duration_seconds",
            duration,
            tags=tags
        )
        
        # Track error rates
        if status_code >= 400:
            metrics.increment_counter(
                "api_errors_total",
                tags={
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": str(status_code)
                }
            )
    
    def _record_error_metrics(self, method: str, endpoint: str, error_type: str, duration: float):
        """Record error metrics"""
        
        tags = {
            "method": method,
            "endpoint": endpoint,
            "error_type": error_type
        }
        
        # Exception counter
        metrics.increment_counter("api_exceptions_total", tags=tags)
        
        # Duration even for failed requests
        metrics.record_histogram(
            "api_request_duration_seconds",
            duration,
            tags={
                "method": method,
                "endpoint": endpoint,
                "status_code": "500",
                "status_class": "5xx"
            }
        )
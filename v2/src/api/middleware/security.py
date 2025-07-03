#!/usr/bin/env python3
"""
Theodore v2 API Security Middleware

Security headers and protection middleware.
"""

import os
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.enable_hsts = os.getenv("ENABLE_HSTS", "false").lower() == "true"
        self.csp_policy = self._build_csp_policy()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        if self.csp_policy:
            response.headers["Content-Security-Policy"] = self.csp_policy
        
        # HSTS for HTTPS
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # API-specific headers
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-Powered-By"] = "Theodore v2"
        
        return response
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy"""
        
        # Base CSP for API server
        policies = [
            "default-src 'none'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests"
        ]
        
        # Allow docs/redoc in development
        if os.getenv("ENVIRONMENT", "development").lower() == "development":
            policies[1] = "script-src 'self' 'unsafe-inline'"  # For docs
        
        return "; ".join(policies)
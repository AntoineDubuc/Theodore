#!/usr/bin/env python3
"""
Theodore v2 FastAPI Application

Main FastAPI application factory with comprehensive middleware,
routing, WebSocket support, and production-grade configurations.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from ..infrastructure.container.application import ApplicationContainer
from ..infrastructure.observability.logging import get_logger
from ..infrastructure.observability.metrics import MetricsCollector
from ..infrastructure.observability.health import HealthChecker
from .routers import (
    auth,
    research,
    discovery,
    batch,
    plugins,
    system,
    websocket,
)
from .middleware import (
    RequestLoggingMiddleware,
    RateLimitingMiddleware,
    SecurityHeadersMiddleware,
    MetricsMiddleware,
    ErrorHandlingMiddleware,
)
from .models.responses import ErrorResponse
from .security import get_current_user
from .websocket.manager import WebSocketManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Theodore v2 API Server...")
    
    try:
        # Initialize container
        container = ApplicationContainer()
        await container.wire_all()
        app.state.container = container
        
        # Initialize WebSocket manager
        app.state.websocket_manager = WebSocketManager()
        
        # Initialize metrics collector
        app.state.metrics = MetricsCollector()
        
        # Initialize health checker
        app.state.health_checker = HealthChecker(container)
        
        # Start background tasks
        asyncio.create_task(app.state.websocket_manager.start_heartbeat())
        asyncio.create_task(app.state.metrics.start_collection())
        
        logger.info("✅ Theodore v2 API Server started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Shutting down Theodore v2 API Server...")
    
    try:
        # Stop background tasks
        if hasattr(app.state, 'websocket_manager'):
            await app.state.websocket_manager.shutdown()
        
        if hasattr(app.state, 'metrics'):
            await app.state.metrics.stop_collection()
        
        # Cleanup container
        if hasattr(app.state, 'container'):
            await app.state.container.cleanup()
        
        logger.info("✅ Theodore v2 API Server shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_app(
    title: str = "Theodore v2 API",
    description: str = "AI-powered company intelligence and discovery system",
    version: str = "2.0.0",
    debug: bool = False,
    **kwargs
) -> FastAPI:
    """
    Create and configure FastAPI application with comprehensive middleware and routing
    
    Args:
        title: API application title
        description: API description for documentation
        version: API version
        debug: Enable debug mode
        **kwargs: Additional FastAPI configuration
    
    Returns:
        Configured FastAPI application
    """
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        lifespan=lifespan,
        docs_url="/docs" if debug else None,
        redoc_url="/redoc" if debug else None,
        openapi_url="/openapi.json" if debug else None,
        **kwargs
    )
    
    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=_get_allowed_hosts()
    )
    
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add custom middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add exception handlers
    _add_exception_handlers(app)
    
    # Include routers
    _include_routers(app)
    
    # Add root endpoint
    _add_root_endpoints(app)
    
    return app


def _get_allowed_origins() -> list:
    """Get allowed CORS origins from environment"""
    origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
    return [origin.strip() for origin in origins_env.split(",") if origin.strip()]


def _get_allowed_hosts() -> list:
    """Get allowed hosts for TrustedHostMiddleware"""
    hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
    hosts = [host.strip() for host in hosts_env.split(",") if host.strip()]
    
    # Add wildcard for development
    if os.getenv("ENVIRONMENT", "development").lower() == "development":
        hosts.extend(["*"])
    
    return hosts


def _add_exception_handlers(app: FastAPI):
    """Add custom exception handlers"""
    
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with consistent error format"""
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTP_ERROR",
                message=str(exc.detail),
                status_code=exc.status_code,
                timestamp=datetime.now(timezone.utc).isoformat(),
                path=str(request.url.path)
            ).dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message="Request validation failed",
                details=exc.errors(),
                status_code=422,
                timestamp=datetime.now(timezone.utc).isoformat(),
                path=str(request.url.path)
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                status_code=500,
                timestamp=datetime.now(timezone.utc).isoformat(),
                path=str(request.url.path)
            ).dict()
        )


def _include_routers(app: FastAPI):
    """Include API routers with proper prefixes and tags"""
    
    # Authentication router
    app.include_router(
        auth.router,
        prefix="/api/v2/auth",
        tags=["Authentication"]
    )
    
    # Research router
    app.include_router(
        research.router,
        prefix="/api/v2/research",
        tags=["Research"],
        dependencies=[]  # Add auth dependency when ready
    )
    
    # Discovery router
    app.include_router(
        discovery.router,
        prefix="/api/v2/discover",
        tags=["Discovery"],
        dependencies=[]  # Add auth dependency when ready
    )
    
    # Batch processing router
    app.include_router(
        batch.router,
        prefix="/api/v2/batch",
        tags=["Batch Processing"],
        dependencies=[]  # Add auth dependency when ready
    )
    
    # Plugin management router
    app.include_router(
        plugins.router,
        prefix="/api/v2/plugins",
        tags=["Plugin Management"],
        dependencies=[]  # Add auth dependency when ready
    )
    
    # System router
    app.include_router(
        system.router,
        prefix="/api/v2",
        tags=["System"]
    )
    
    # WebSocket router
    app.include_router(
        websocket.router,
        prefix="/api/v2/ws",
        tags=["WebSocket"]
    )


def _add_root_endpoints(app: FastAPI):
    """Add root and basic endpoints"""
    
    @app.get("/", summary="API Root", tags=["Root"])
    async def root():
        """API root endpoint with basic information"""
        return {
            "name": "Theodore v2 API",
            "version": "2.0.0",
            "description": "AI-powered company intelligence and discovery system",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoints": {
                "health": "/api/v2/health",
                "metrics": "/api/v2/metrics",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    @app.get("/ping", summary="Health Ping", tags=["Root"])
    async def ping():
        """Simple health check endpoint"""
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Export app creation function
__all__ = ["create_app"]
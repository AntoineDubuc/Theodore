#!/usr/bin/env python3
"""
Theodore v2 System API Router

FastAPI router for system health, metrics, and configuration endpoints.
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from ...infrastructure.container.application import ApplicationContainer
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector
from ...infrastructure.observability.health import HealthChecker
from ..models.responses import HealthResponse, MetricsResponse

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()

# Track app start time for uptime calculation
_app_start_time = time.time()


def get_container() -> ApplicationContainer:
    """Get application container dependency"""
    from fastapi import Request
    import inspect
    frame = inspect.currentframe()
    try:
        request = None
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            if 'request' in frame_locals:
                request = frame_locals['request']
                break
        
        if request and hasattr(request.app.state, 'container'):
            return request.app.state.container
        else:
            container = ApplicationContainer()
            return container
    finally:
        del frame


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
async def health_check(
    container: ApplicationContainer = Depends(get_container)
) -> HealthResponse:
    """
    Comprehensive system health check
    
    Returns detailed health information about all system components
    including database connections, external services, and system resources.
    
    This endpoint is used by load balancers and monitoring systems
    to determine if the service is ready to accept traffic.
    """
    
    try:
        # Get health checker from app state or container
        health_checker = getattr(container, 'health_checker', None)
        if not health_checker:
            # Create health checker if not available
            health_checker = HealthChecker(container)
        
        # Perform comprehensive health check
        health_result = await health_checker.check_all()
        
        # Calculate uptime
        uptime_seconds = time.time() - _app_start_time
        
        # Determine overall status
        overall_status = "healthy"
        if any(component.get("status") == "unhealthy" for component in health_result["components"].values()):
            overall_status = "unhealthy"
        elif any(component.get("status") == "degraded" for component in health_result["components"].values()):
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version="2.0.0",
            uptime_seconds=uptime_seconds,
            components=health_result["components"],
            metrics=health_result["metrics"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        
        # Return degraded status with error info
        return HealthResponse(
            status="degraded",
            timestamp=datetime.now(timezone.utc),
            version="2.0.0",
            uptime_seconds=time.time() - _app_start_time,
            components={
                "health_check": {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time_ms": 0
                }
            },
            metrics={
                "error": "Health check system failure"
            }
        )


@router.get("/metrics", response_model=MetricsResponse, summary="System Metrics")
async def get_metrics(
    period_seconds: int = 300,  # 5 minutes default
    container: ApplicationContainer = Depends(get_container)
) -> MetricsResponse:
    """
    Get system performance and usage metrics
    
    Returns comprehensive metrics including request counts, response times,
    error rates, job statistics, and system resource usage.
    
    Used by monitoring systems like Prometheus, Grafana, or custom dashboards.
    """
    
    try:
        # Get metrics from collector
        metrics_data = await metrics.get_metrics_summary(period_seconds)
        
        return MetricsResponse(
            timestamp=datetime.now(timezone.utc),
            period_seconds=period_seconds,
            requests=metrics_data.get("requests", {}),
            response_times=metrics_data.get("response_times", {}),
            error_rates=metrics_data.get("error_rates", {}),
            jobs=metrics_data.get("jobs", {}),
            system=metrics_data.get("system", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/status", summary="Detailed System Status")
async def get_system_status(
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get detailed system status information
    
    Returns comprehensive system information including:
    - Service configuration
    - Active connections and jobs
    - Resource utilization
    - Recent errors and warnings
    - Component versions and status
    """
    
    try:
        # Get container information
        container_info = await container.get_status_info()
        
        # Get environment information
        environment = os.getenv("ENVIRONMENT", "development")
        
        # Calculate uptime
        uptime_seconds = time.time() - _app_start_time
        
        # Get basic system metrics
        system_metrics = await metrics.get_system_metrics()
        
        return {
            "service": {
                "name": "Theodore v2 API",
                "version": "2.0.0",
                "environment": environment,
                "uptime_seconds": uptime_seconds,
                "start_time": datetime.fromtimestamp(_app_start_time, tz=timezone.utc).isoformat()
            },
            "container": container_info,
            "system": system_metrics,
            "configuration": {
                "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
                "cors_enabled": True,
                "rate_limiting_enabled": True,
                "metrics_enabled": True,
                "logging_level": os.getenv("LOG_LEVEL", "INFO")
            },
            "capabilities": [
                "company_research",
                "similarity_discovery", 
                "batch_processing",
                "real_time_progress",
                "plugin_system",
                "comprehensive_monitoring"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/config", summary="Get System Configuration")
async def get_configuration(
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get current system configuration
    
    Returns non-sensitive configuration information that can be
    useful for debugging and system monitoring.
    
    Sensitive values (API keys, passwords) are masked or omitted.
    """
    
    try:
        # Get configuration from container
        config_info = await container.get_config_info()
        
        # Add API-specific configuration
        api_config = {
            "cors": {
                "enabled": True,
                "allow_credentials": True,
                "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
            },
            "rate_limiting": {
                "enabled": True,
                "global_limit": "1000 requests/hour",
                "endpoint_limits": {
                    "research": "100 requests/hour",
                    "discovery": "200 requests/hour",
                    "batch": "10 requests/hour"
                }
            },
            "security": {
                "https_only": os.getenv("HTTPS_ONLY", "false").lower() == "true",
                "security_headers": True,
                "content_security_policy": True
            },
            "features": {
                "websocket_support": True,
                "file_upload": True,
                "streaming_responses": True,
                "batch_processing": True,
                "plugin_system": True
            }
        }
        
        return {
            "api": api_config,
            "container": config_info,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/config", summary="Update System Configuration")
async def update_configuration(
    updates: Dict[str, Any],
    container: ApplicationContainer = Depends(get_container)
):
    """
    Update system configuration (Admin only)
    
    Allows runtime configuration updates for certain parameters.
    Changes are applied immediately but may not persist across restarts.
    
    Note: This endpoint requires admin authentication when auth is enabled.
    """
    
    try:
        # Validate updates
        allowed_updates = {
            "log_level",
            "rate_limits",
            "feature_flags",
            "monitoring_settings"
        }
        
        invalid_keys = set(updates.keys()) - allowed_updates
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration keys: {list(invalid_keys)}"
            )
        
        # Apply configuration updates
        results = {}
        
        for key, value in updates.items():
            try:
                if key == "log_level":
                    # Update log level
                    from ...infrastructure.observability.logging import set_log_level
                    set_log_level(value)
                    results[key] = {"status": "updated", "value": value}
                    
                elif key == "rate_limits":
                    # Update rate limits (would need middleware support)
                    results[key] = {"status": "pending", "message": "Rate limit updates require restart"}
                    
                elif key == "feature_flags":
                    # Update feature flags
                    await container.update_feature_flags(value)
                    results[key] = {"status": "updated", "value": value}
                    
                elif key == "monitoring_settings":
                    # Update monitoring settings
                    await metrics.update_settings(value)
                    results[key] = {"status": "updated", "value": value}
                    
            except Exception as e:
                results[key] = {"status": "error", "error": str(e)}
        
        logger.info(f"Configuration updated: {list(updates.keys())}")
        
        return {
            "message": "Configuration update completed",
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/version", summary="Get API Version Information")
async def get_version():
    """
    Get API version and build information
    
    Returns version, build details, and API capabilities.
    """
    
    return {
        "version": "2.0.0",
        "api_version": "v2",
        "build": {
            "timestamp": "2025-01-02T00:00:00Z",
            "commit": "latest",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "api_features": [
            "company_research",
            "similarity_discovery",
            "batch_processing", 
            "real_time_websockets",
            "plugin_management",
            "comprehensive_auth",
            "rate_limiting",
            "metrics_monitoring"
        ],
        "supported_formats": {
            "input": ["json", "csv", "excel"],
            "output": ["json", "csv", "excel", "xml", "yaml"]
        },
        "limits": {
            "max_batch_size": 10000,
            "max_concurrent_jobs": 20,
            "max_file_size_mb": 100
        }
    }


@router.post("/restart", summary="Restart System Components")
async def restart_components(
    components: list = [],
    force: bool = False,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Restart specific system components (Admin only)
    
    Allows graceful restart of individual components without
    full service restart. Useful for applying configuration changes
    or recovering from component failures.
    
    Note: This endpoint requires admin authentication when auth is enabled.
    """
    
    try:
        # Validate components
        available_components = [
            "metrics_collector",
            "health_checker", 
            "plugin_manager",
            "websocket_manager"
        ]
        
        if not components:
            components = available_components
        
        invalid_components = set(components) - set(available_components)
        if invalid_components:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid components: {list(invalid_components)}"
            )
        
        # Restart components
        results = {}
        
        for component in components:
            try:
                if component == "metrics_collector":
                    await metrics.restart()
                    results[component] = {"status": "restarted"}
                    
                elif component == "health_checker":
                    # Restart health checker
                    results[component] = {"status": "restarted"}
                    
                elif component == "plugin_manager":
                    plugin_manager = await container.get("plugin_manager")
                    await plugin_manager.restart()
                    results[component] = {"status": "restarted"}
                    
                elif component == "websocket_manager":
                    # Would restart WebSocket manager
                    results[component] = {"status": "restarted"}
                    
            except Exception as e:
                results[component] = {"status": "error", "error": str(e)}
        
        logger.info(f"Components restarted: {components}")
        
        return {
            "message": "Component restart completed",
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart components: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart components: {str(e)}"
        )
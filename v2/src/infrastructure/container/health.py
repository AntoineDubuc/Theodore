"""
Health Check Aggregator for Theodore v2 Container.

Aggregates health status from all container components and provides
comprehensive system health monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class HealthCheckAggregator:
    """Aggregates health checks from all container components."""
    
    def __init__(self, storage, ai_services, mcp_search, config: Dict[str, Any]):
        self.storage = storage
        self.ai_services = ai_services
        self.mcp_search = mcp_search
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self._enabled = config.get("enabled", True)
        self._check_interval = config.get("health_check_interval_seconds", 30.0)
        self._timeout = config.get("timeout_seconds", 10.0)
        self._detailed_checks = config.get("detailed_checks", True)
        
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        self._last_health_status: Optional[Dict[str, Any]] = None
    
    async def start(self) -> None:
        """Start background health monitoring."""
        if not self._enabled or self._running:
            return
        
        self._running = True
        self._background_task = asyncio.create_task(self._health_check_loop())
        self.logger.info("Health check aggregator started")
    
    async def stop(self) -> None:
        """Stop background health monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health check aggregator stopped")
    
    async def get_health_status(self, detailed: Optional[bool] = None) -> Dict[str, Any]:
        """Get current health status of all components."""
        detailed = detailed if detailed is not None else self._detailed_checks
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {},
            "summary": {
                "total_components": 0,
                "healthy": 0,
                "unhealthy": 0,
                "degraded": 0
            }
        }
        
        try:
            # Check storage components
            storage_health = await self._check_storage_health()
            health_status["components"]["storage"] = storage_health
            
            # Check AI services
            ai_health = await self._check_ai_services_health()
            health_status["components"]["ai_services"] = ai_health
            
            # Check MCP search tools
            mcp_health = await self._check_mcp_search_health()
            health_status["components"]["mcp_search"] = mcp_health
            
            # Calculate summary
            self._calculate_health_summary(health_status)
            
            # Determine overall status
            self._determine_overall_status(health_status)
            
            # Cache result
            self._last_health_status = health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return health_status
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while self._running:
            try:
                await self.get_health_status()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage components health."""
        try:
            storage_provider = self.storage()
            if hasattr(storage_provider, 'storage_health'):
                health_checker = storage_provider.storage_health()
                return await asyncio.wait_for(
                    health_checker.check_health(),
                    timeout=self._timeout
                )
            else:
                return {"status": "healthy", "message": "Storage operational"}
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "error": "Health check timeout"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_ai_services_health(self) -> Dict[str, Any]:
        """Check AI services health."""
        try:
            ai_provider = self.ai_services()
            if hasattr(ai_provider, 'ai_health'):
                health_checker = ai_provider.ai_health()
                return await asyncio.wait_for(
                    health_checker.check_health(),
                    timeout=self._timeout
                )
            else:
                return {"status": "healthy", "message": "AI services operational"}
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "error": "Health check timeout"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_mcp_search_health(self) -> Dict[str, Any]:
        """Check MCP search tools health."""
        try:
            mcp_provider = self.mcp_search()
            if hasattr(mcp_provider, 'mcp_health'):
                health_checker = mcp_provider.mcp_health()
                return await asyncio.wait_for(
                    health_checker.check_health(),
                    timeout=self._timeout
                )
            else:
                return {"status": "healthy", "message": "MCP search operational"}
        except asyncio.TimeoutError:
            return {"status": "unhealthy", "error": "Health check timeout"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _calculate_health_summary(self, health_status: Dict[str, Any]) -> None:
        """Calculate health summary statistics."""
        components = health_status["components"]
        summary = health_status["summary"]
        
        summary["total_components"] = len(components)
        
        for component_status in components.values():
            status = component_status.get("status", "unknown")
            if status == "healthy":
                summary["healthy"] += 1
            elif status == "unhealthy":
                summary["unhealthy"] += 1
            elif status == "degraded":
                summary["degraded"] += 1
    
    def _determine_overall_status(self, health_status: Dict[str, Any]) -> None:
        """Determine overall system status."""
        summary = health_status["summary"]
        
        if summary["unhealthy"] > 0:
            health_status["status"] = "unhealthy"
        elif summary["degraded"] > 0:
            health_status["status"] = "degraded"
        else:
            health_status["status"] = "healthy"
    
    def get_last_health_status(self) -> Optional[Dict[str, Any]]:
        """Get last cached health status."""
        return self._last_health_status
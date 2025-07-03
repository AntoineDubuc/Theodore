#!/usr/bin/env python3
"""
Theodore v2 Health Monitoring System
===================================

Comprehensive health checking and system status monitoring for Theodore v2
components including AI services, databases, external APIs, and system resources.

This module provides:
- Health check framework for all system components
- System resource monitoring (CPU, memory, disk)
- External service dependency health checks
- Automated health reporting and alerting
- Health status aggregation and scoring
"""

import asyncio
import time

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
import json
import logging

from .logging import get_system_logger


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Types of system components"""
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    EXTERNAL_API = "external_api"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    WEB_SERVER = "web_server"
    WORKER = "worker"
    SYSTEM_RESOURCE = "system_resource"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health summary"""
    overall_status: HealthStatus
    healthy_components: int
    degraded_components: int
    unhealthy_components: int
    total_components: int
    last_check: datetime
    components: List[HealthCheckResult]
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if self.total_components == 0:
            return 100.0
        
        # Weight different statuses
        score = (
            (self.healthy_components * 100) +
            (self.degraded_components * 50) +
            (self.unhealthy_components * 0)
        ) / self.total_components
        
        return min(100.0, max(0.0, score))


class BaseHealthCheck(ABC):
    """Base class for health checks"""
    
    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        self.name = name
        self.component_type = component_type
        self.timeout_seconds = timeout_seconds
        self.critical = critical
        self.logger = get_system_logger(f"health_check.{name}")
    
    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Perform the health check"""
        pass
    
    async def run_check(self) -> HealthCheckResult:
        """Run health check with timeout and error handling"""
        start_time = time.perf_counter()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_health(),
                timeout=self.timeout_seconds
            )
            
            # Calculate response time
            response_time = (time.perf_counter() - start_time) * 1000
            result.response_time_ms = response_time
            
            return result
            
        except asyncio.TimeoutError:
            response_time = (time.perf_counter() - start_time) * 1000
            self.logger.warn(f"Health check timeout for {self.name}")
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout_seconds}s",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
                error="timeout"
            )
            
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Health check failed for {self.name}", error=e)
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
                error=str(e)
            )


class HTTPHealthCheck(BaseHealthCheck):
    """Health check for HTTP endpoints"""
    
    def __init__(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        expected_response: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        super().__init__(name, ComponentType.EXTERNAL_API, timeout_seconds, critical)
        self.url = url
        self.expected_status = expected_status
        self.expected_response = expected_response
        self.headers = headers or {}
    
    async def check_health(self) -> HealthCheckResult:
        """Check HTTP endpoint health"""
        if not AIOHTTP_AVAILABLE:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNKNOWN,
                message="aiohttp not available for HTTP health checks",
                timestamp=datetime.now(timezone.utc)
            )
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    
                    # Check status code
                    if response.status != self.expected_status:
                        return HealthCheckResult(
                            component_name=self.name,
                            component_type=self.component_type,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Unexpected status code: {response.status}",
                            timestamp=datetime.now(timezone.utc),
                            details={"status_code": response.status, "url": self.url}
                        )
                    
                    # Check response content if specified
                    if self.expected_response:
                        text = await response.text()
                        if self.expected_response not in text:
                            return HealthCheckResult(
                                component_name=self.name,
                                component_type=self.component_type,
                                status=HealthStatus.DEGRADED,
                                message="Response content doesn't match expected",
                                timestamp=datetime.now(timezone.utc),
                                details={"response_preview": text[:200]}
                            )
                    
                    return HealthCheckResult(
                        component_name=self.name,
                        component_type=self.component_type,
                        status=HealthStatus.HEALTHY,
                        message="HTTP endpoint responding normally",
                        timestamp=datetime.now(timezone.utc),
                        details={"status_code": response.status, "url": self.url}
                    )
                    
            except aiohttp.ClientError as e:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP request failed: {str(e)}",
                    timestamp=datetime.now(timezone.utc),
                    error=str(e)
                )


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connections"""
    
    def __init__(
        self,
        name: str,
        connection_test: Callable,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        super().__init__(name, ComponentType.DATABASE, timeout_seconds, critical)
        self.connection_test = connection_test
    
    async def check_health(self) -> HealthCheckResult:
        """Check database connectivity"""
        try:
            # Run connection test
            result = await self.connection_test()
            
            if result:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed",
                    timestamp=datetime.now(timezone.utc)
                )
                
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )


class SystemResourceHealthCheck(BaseHealthCheck):
    """Health check for system resources"""
    
    def __init__(
        self,
        name: str = "system_resources",
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 90.0,
        timeout_seconds: float = 2.0,
        critical: bool = True
    ):
        super().__init__(name, ComponentType.SYSTEM_RESOURCE, timeout_seconds, critical)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def check_health(self) -> HealthCheckResult:
        """Check system resource utilization"""
        try:
            if not PSUTIL_AVAILABLE:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNKNOWN,
                    message="psutil not available for system monitoring",
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine overall status
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > self.cpu_threshold:
                status = HealthStatus.DEGRADED if cpu_percent < 95 else HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > self.memory_threshold:
                status = HealthStatus.DEGRADED if memory_percent < 95 else HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            
            if disk_percent > self.disk_threshold:
                status = HealthStatus.DEGRADED if disk_percent < 98 else HealthStatus.UNHEALTHY
                messages.append(f"High disk usage: {disk_percent:.1f}%")
            
            message = "System resources normal" if not messages else "; ".join(messages)
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"System resource check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )


class AIServiceHealthCheck(BaseHealthCheck):
    """Health check for AI services"""
    
    def __init__(
        self,
        name: str,
        service_test: Callable,
        timeout_seconds: float = 10.0,
        critical: bool = True
    ):
        super().__init__(name, ComponentType.AI_SERVICE, timeout_seconds, critical)
        self.service_test = service_test
    
    async def check_health(self) -> HealthCheckResult:
        """Check AI service availability"""
        try:
            # Run service test (should be a simple ping or health endpoint)
            result = await self.service_test()
            
            if result.get("status") == "ok":
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    message="AI service responding normally",
                    timestamp=datetime.now(timezone.utc),
                    details=result
                )
            else:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.DEGRADED,
                    message="AI service responding with issues",
                    timestamp=datetime.now(timezone.utc),
                    details=result
                )
                
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"AI service health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                error=str(e)
            )


class HealthChecker:
    """Central health checking system"""
    
    def __init__(self):
        self.health_checks: List[BaseHealthCheck] = []
        self.logger = get_system_logger("health_checker")
        self._last_check_results: Optional[SystemHealth] = None
        self._check_interval = 60  # seconds
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def register_health_check(self, health_check: BaseHealthCheck):
        """Register a health check"""
        self.health_checks.append(health_check)
        self.logger.info(f"Registered health check: {health_check.name}")
    
    def register_http_check(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        """Register HTTP endpoint health check"""
        check = HTTPHealthCheck(name, url, expected_status, timeout_seconds=timeout_seconds, critical=critical)
        self.register_health_check(check)
    
    def register_database_check(
        self,
        name: str,
        connection_test: Callable,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        """Register database health check"""
        check = DatabaseHealthCheck(name, connection_test, timeout_seconds, critical)
        self.register_health_check(check)
    
    def register_ai_service_check(
        self,
        name: str,
        service_test: Callable,
        timeout_seconds: float = 10.0,
        critical: bool = True
    ):
        """Register AI service health check"""
        check = AIServiceHealthCheck(name, service_test, timeout_seconds, critical)
        self.register_health_check(check)
    
    def register_system_resources_check(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 90.0
    ):
        """Register system resources health check"""
        check = SystemResourceHealthCheck(
            cpu_threshold=cpu_threshold,
            memory_threshold=memory_threshold,
            disk_threshold=disk_threshold
        )
        self.register_health_check(check)
    
    async def check_all_health(self) -> SystemHealth:
        """Run all health checks and return system health"""
        if not self.health_checks:
            return SystemHealth(
                overall_status=HealthStatus.UNKNOWN,
                healthy_components=0,
                degraded_components=0,
                unhealthy_components=0,
                total_components=0,
                last_check=datetime.now(timezone.utc),
                components=[]
            )
        
        self.logger.debug(f"Running {len(self.health_checks)} health checks")
        
        # Run all health checks concurrently
        tasks = [check.run_check() for check in self.health_checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        component_results = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle unexpected errors
                check = self.health_checks[i]
                result = HealthCheckResult(
                    component_name=check.name,
                    component_type=check.component_type,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(result)}",
                    timestamp=datetime.now(timezone.utc),
                    error=str(result)
                )
            
            component_results.append(result)
            
            # Count statuses
            if result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif result.status == HealthStatus.DEGRADED:
                degraded_count += 1
            else:
                unhealthy_count += 1
        
        # Determine overall status
        overall_status = self._calculate_overall_status(
            healthy_count, degraded_count, unhealthy_count
        )
        
        system_health = SystemHealth(
            overall_status=overall_status,
            healthy_components=healthy_count,
            degraded_components=degraded_count,
            unhealthy_components=unhealthy_count,
            total_components=len(component_results),
            last_check=datetime.now(timezone.utc),
            components=component_results
        )
        
        self._last_check_results = system_health
        
        # Log health status
        self.logger.info(
            f"Health check completed: {overall_status.value} "
            f"({healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy)"
        )
        
        # Log unhealthy components
        for result in component_results:
            if result.status == HealthStatus.UNHEALTHY:
                self.logger.error(
                    f"Unhealthy component: {result.component_name} - {result.message}",
                    component=result.component_name,
                    error=result.error
                )
        
        return system_health
    
    def _calculate_overall_status(
        self, 
        healthy_count: int, 
        degraded_count: int, 
        unhealthy_count: int
    ) -> HealthStatus:
        """Calculate overall system health status"""
        total = healthy_count + degraded_count + unhealthy_count
        
        if total == 0:
            return HealthStatus.UNKNOWN
        
        # Check for critical components being unhealthy
        critical_unhealthy = any(
            result.status == HealthStatus.UNHEALTHY and check.critical
            for check, result in zip(self.health_checks, self._last_check_results.components if self._last_check_results else [])
            if hasattr(check, 'critical')
        )
        
        if critical_unhealthy or unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_last_health_check(self) -> Optional[SystemHealth]:
        """Get results of last health check"""
        return self._last_check_results
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous health monitoring"""
        self._check_interval = interval_seconds
        
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Started health monitoring with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self.logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while True:
            try:
                await self.check_all_health()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in health monitoring loop", error=e)
                await asyncio.sleep(self._check_interval)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export health status as dictionary"""
        if not self._last_check_results:
            return {"status": "no_checks_performed"}
        
        health = self._last_check_results
        
        return {
            "status": health.overall_status.value,
            "health_score": health.health_score,
            "summary": {
                "healthy": health.healthy_components,
                "degraded": health.degraded_components,
                "unhealthy": health.unhealthy_components,
                "total": health.total_components
            },
            "last_check": health.last_check.isoformat(),
            "components": [
                {
                    "name": comp.component_name,
                    "type": comp.component_type.value,
                    "status": comp.status.value,
                    "message": comp.message,
                    "response_time_ms": comp.response_time_ms,
                    "timestamp": comp.timestamp.isoformat(),
                    "details": comp.details,
                    "error": comp.error
                }
                for comp in health.components
            ]
        }


# Global health checker instance
_global_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = HealthChecker()
    return _global_health_checker


def setup_default_health_checks():
    """Setup default health checks for Theodore v2"""
    checker = get_health_checker()
    
    # System resources
    checker.register_system_resources_check()
    
    # Add other default checks as needed
    # These would be configured based on actual deployment
    
    return checker
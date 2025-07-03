"""
Container Lifecycle Manager for Theodore v2.

Manages async initialization, startup, and shutdown sequences
for all container components.
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timezone


class ContainerLifecycleManager:
    """Manages container lifecycle with proper async initialization and shutdown."""
    
    def __init__(self, container, config: Dict[str, Any]):
        self.container = container
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self._startup_tasks: List[Callable] = []
        self._shutdown_tasks: List[Callable] = []
        self._startup_timeout = config.get("startup_timeout_seconds", 60.0)
        self._shutdown_timeout = config.get("shutdown_timeout_seconds", 30.0)
        
        self._started = False
        self._startup_time: Optional[datetime] = None
    
    async def startup(self) -> None:
        """Perform startup sequence."""
        if self._started:
            return
        
        self.logger.info("Starting container lifecycle")
        start_time = datetime.now(timezone.utc)
        
        try:
            # Execute startup tasks with timeout
            await asyncio.wait_for(
                self._execute_startup_tasks(),
                timeout=self._startup_timeout
            )
            
            self._started = True
            self._startup_time = start_time
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(f"Container startup completed in {duration:.2f}s")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Container startup timed out after {self._startup_timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"Container startup failed: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Perform shutdown sequence."""
        if not self._started:
            return
        
        self.logger.info("Starting container shutdown")
        
        try:
            await asyncio.wait_for(
                self._execute_shutdown_tasks(),
                timeout=self._shutdown_timeout
            )
            
            self._started = False
            self.logger.info("Container shutdown completed")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Container shutdown timed out after {self._shutdown_timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"Container shutdown failed: {e}")
            raise
    
    async def _execute_startup_tasks(self) -> None:
        """Execute all startup tasks."""
        # Initialize async components
        await self._initialize_async_components()
        
        # Execute custom startup tasks
        for task in self._startup_tasks:
            try:
                await task()
            except Exception as e:
                self.logger.error(f"Startup task failed: {e}")
                raise
    
    async def _execute_shutdown_tasks(self) -> None:
        """Execute all shutdown tasks."""
        # Execute custom shutdown tasks
        for task in reversed(self._shutdown_tasks):
            try:
                await task()
            except Exception as e:
                self.logger.warning(f"Shutdown task failed: {e}")
        
        # Cleanup async components
        await self._cleanup_async_components()
    
    async def _initialize_async_components(self) -> None:
        """Initialize async components."""
        # Initialize external services
        if hasattr(self.container, 'external_services'):
            self.logger.debug("Initializing external services")
        
        # Initialize storage components
        if hasattr(self.container, 'storage'):
            self.logger.debug("Initializing storage components")
        
        # Initialize AI services
        if hasattr(self.container, 'ai_services'):
            self.logger.debug("Initializing AI services")
        
        # Initialize MCP search tools
        if hasattr(self.container, 'mcp_search'):
            self.logger.debug("Initializing MCP search tools")
    
    async def _cleanup_async_components(self) -> None:
        """Cleanup async components."""
        # Cleanup in reverse order
        components = ['mcp_search', 'ai_services', 'storage', 'external_services']
        
        for component_name in components:
            if hasattr(self.container, component_name):
                try:
                    component = getattr(self.container, component_name)()
                    if hasattr(component, 'close'):
                        await component.close()
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup {component_name}: {e}")
    
    def add_startup_task(self, task: Callable) -> None:
        """Add custom startup task."""
        self._startup_tasks.append(task)
    
    def add_shutdown_task(self, task: Callable) -> None:
        """Add custom shutdown task."""
        self._shutdown_tasks.append(task)
    
    def get_status(self) -> Dict[str, Any]:
        """Get lifecycle status."""
        return {
            "started": self._started,
            "startup_time": self._startup_time.isoformat() if self._startup_time else None,
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self._startup_time).total_seconds()
                if self._startup_time else 0
            )
        }
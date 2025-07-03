"""
MCP Tool Registry for Theodore.

This module provides registry management for MCP (Model Context Protocol) search tools,
including registration, validation, and capability-based tool selection.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Union
from datetime import datetime, timedelta
from enum import Enum

from src.core.ports.mcp_search_tool import (
    MCPSearchTool, MCPToolInfo, MCPSearchCapability,
    MCPConfigurationException, MCPSearchException,
    StreamingMCPSearchTool, CacheableMCPSearchTool, BatchMCPSearchTool
)


logger = logging.getLogger(__name__)


class ToolStatus(str, Enum):
    """Status of an MCP tool in the registry."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    MAINTENANCE = "maintenance"


class ToolRegistration:
    """Registration information for an MCP tool."""
    
    def __init__(
        self,
        tool: MCPSearchTool,
        priority: int = 50,
        enabled: bool = True,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tool = tool
        self.tool_info = tool.get_tool_info()
        self.priority = priority  # Higher number = higher priority
        self.enabled = enabled
        self.tags = tags or []
        self.metadata = metadata or {}
        
        # Status tracking
        self.status = ToolStatus.ACTIVE if enabled else ToolStatus.INACTIVE
        self.last_health_check = datetime.utcnow()
        self.health_check_count = 0
        self.error_count = 0
        self.success_count = 0
        self.last_error: Optional[Exception] = None
        
        # Performance tracking
        self.total_search_time_ms = 0.0
        self.total_searches = 0
        self.total_cost_incurred = 0.0
        
        # Rate limiting
        self.requests_this_minute = 0
        self.minute_window_start = datetime.utcnow()
    
    def get_average_search_time(self) -> float:
        """Get average search time in milliseconds."""
        if self.total_searches == 0:
            return 0.0
        return self.total_search_time_ms / self.total_searches
    
    def get_success_rate(self) -> float:
        """Get success rate as a float between 0.0 and 1.0."""
        total_requests = self.success_count + self.error_count
        if total_requests == 0:
            return 1.0
        return self.success_count / total_requests
    
    def can_handle_request(self) -> bool:
        """Check if tool can handle another request."""
        if not self.enabled or self.status != ToolStatus.ACTIVE:
            return False
        
        # Check rate limits
        now = datetime.utcnow()
        if (now - self.minute_window_start).total_seconds() >= 60:
            # Reset minute window
            self.requests_this_minute = 0
            self.minute_window_start = now
        
        rate_limit = self.tool_info.rate_limit_per_minute
        if rate_limit and self.requests_this_minute >= rate_limit:
            return False
        
        return True
    
    def record_request(self):
        """Record a request against rate limits."""
        now = datetime.utcnow()
        if (now - self.minute_window_start).total_seconds() >= 60:
            self.requests_this_minute = 1
            self.minute_window_start = now
        else:
            self.requests_this_minute += 1
    
    def record_success(self, search_time_ms: float, cost: Optional[float] = None):
        """Record a successful search."""
        self.success_count += 1
        self.total_searches += 1
        self.total_search_time_ms += search_time_ms
        if cost:
            self.total_cost_incurred += cost
        
        if self.status == ToolStatus.ERROR:
            self.status = ToolStatus.ACTIVE
    
    def record_error(self, error: Exception):
        """Record an error."""
        self.error_count += 1
        self.last_error = error
        
        # Update status based on error type
        if "rate" in str(error).lower():
            self.status = ToolStatus.RATE_LIMITED
        elif "quota" in str(error).lower():
            self.status = ToolStatus.QUOTA_EXCEEDED
        else:
            self.status = ToolStatus.ERROR


class MCPToolRegistry:
    """
    Registry for managing MCP search tools.
    
    Provides registration, validation, health monitoring, and intelligent
    tool selection based on capabilities and performance.
    """
    
    def __init__(
        self,
        health_check_interval: int = 300,  # 5 minutes
        max_error_rate: float = 0.1,  # 10% error rate threshold
        enable_auto_disable: bool = True
    ):
        self._registrations: Dict[str, ToolRegistration] = {}
        self._default_tool: Optional[str] = None
        self._health_check_interval = health_check_interval
        self._max_error_rate = max_error_rate
        self._enable_auto_disable = enable_auto_disable
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the registry background tasks."""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("MCP Tool Registry started")
    
    async def stop(self):
        """Stop the registry and cleanup resources."""
        self._running = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all tools
        for registration in self._registrations.values():
            try:
                await registration.tool.close()
            except Exception as e:
                logger.warning(f"Error closing tool {registration.tool_info.tool_name}: {e}")
        
        logger.info("MCP Tool Registry stopped")
    
    async def register_tool(
        self,
        tool: MCPSearchTool,
        priority: int = 50,
        enabled: bool = True,
        tags: Optional[List[str]] = None,
        validate_immediately: bool = True
    ) -> None:
        """
        Register a new MCP tool.
        
        Args:
            tool: MCP search tool to register
            priority: Tool priority (higher = preferred)
            enabled: Whether tool is enabled
            tags: Optional tags for categorization
            validate_immediately: Whether to validate configuration immediately
            
        Raises:
            MCPConfigurationException: If tool validation fails
            ValueError: If tool name already exists
        """
        tool_info = tool.get_tool_info()
        tool_name = tool_info.tool_name
        
        if tool_name in self._registrations:
            raise ValueError(f"Tool '{tool_name}' is already registered")
        
        # Validate configuration if requested
        if validate_immediately:
            try:
                async with tool:
                    is_valid = await tool.validate_configuration()
                    if not is_valid:
                        raise MCPConfigurationException(
                            tool_name,
                            "Tool validation returned False"
                        )
            except Exception as e:
                if isinstance(e, MCPConfigurationException):
                    raise
                raise MCPConfigurationException(
                    tool_name,
                    f"Validation failed: {str(e)}"
                )
        
        # Create registration
        registration = ToolRegistration(
            tool=tool,
            priority=priority,
            enabled=enabled,
            tags=tags or []
        )
        
        self._registrations[tool_name] = registration
        
        logger.info(
            f"Registered MCP tool: {tool_name} "
            f"(capabilities: {[c.value for c in tool_info.capabilities]})"
        )
    
    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister an MCP tool.
        
        Args:
            tool_name: Name of tool to unregister
            
        Raises:
            KeyError: If tool not found
        """
        if tool_name not in self._registrations:
            raise KeyError(f"Tool '{tool_name}' not found")
        
        del self._registrations[tool_name]
        
        if self._default_tool == tool_name:
            self._default_tool = None
        
        logger.info(f"Unregistered MCP tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> MCPSearchTool:
        """
        Get a specific tool by name.
        
        Args:
            tool_name: Name of tool to retrieve
            
        Returns:
            MCPSearchTool instance
            
        Raises:
            KeyError: If tool not found
            MCPSearchException: If tool is not available
        """
        if tool_name not in self._registrations:
            available = list(self._registrations.keys())
            raise KeyError(
                f"Tool '{tool_name}' not found. Available: {available}"
            )
        
        registration = self._registrations[tool_name]
        
        if not registration.can_handle_request():
            raise MCPSearchException(
                f"Tool '{tool_name}' is not available (status: {registration.status.value})"
            )
        
        return registration.tool
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names that can handle requests
        """
        available = []
        for name, registration in self._registrations.items():
            if registration.can_handle_request():
                available.append(name)
        return available
    
    def get_all_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._registrations.keys())
    
    def get_tools_with_capability(
        self,
        capability: Union[str, MCPSearchCapability]
    ) -> List[MCPSearchTool]:
        """
        Find all available tools with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of tools that have the capability and are available
        """
        if isinstance(capability, str):
            capability = MCPSearchCapability(capability)
        
        matching_tools = []
        for registration in self._registrations.values():
            if (registration.can_handle_request() and 
                registration.tool_info.has_capability(capability)):
                matching_tools.append(registration.tool)
        
        # Sort by priority (descending)
        matching_tools.sort(
            key=lambda t: self._registrations[t.get_tool_info().tool_name].priority,
            reverse=True
        )
        
        return matching_tools
    
    def get_tools_with_tag(self, tag: str) -> List[MCPSearchTool]:
        """
        Find all available tools with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of tools that have the tag and are available
        """
        matching_tools = []
        for registration in self._registrations.values():
            if registration.can_handle_request() and tag in registration.tags:
                matching_tools.append(registration.tool)
        
        return matching_tools
    
    def get_best_tool_for_capability(
        self,
        capability: Union[str, MCPSearchCapability]
    ) -> Optional[MCPSearchTool]:
        """
        Get the best available tool for a specific capability.
        
        Selection is based on priority, success rate, and performance.
        
        Args:
            capability: Capability required
            
        Returns:
            Best tool for the capability, or None if none available
        """
        tools_with_capability = self.get_tools_with_capability(capability)
        
        if not tools_with_capability:
            return None
        
        # Score tools based on multiple factors
        def score_tool(tool: MCPSearchTool) -> float:
            registration = self._registrations[tool.get_tool_info().tool_name]
            
            # Base score from priority (0-100)
            score = registration.priority
            
            # Success rate bonus (0-20)
            score += registration.get_success_rate() * 20
            
            # Performance bonus (faster = better, max 10)
            avg_time = registration.get_average_search_time()
            if avg_time > 0:
                # Bonus for sub-second response (max 10 points)
                performance_bonus = max(0, 10 - (avg_time / 1000) * 2)
                score += performance_bonus
            
            return score
        
        best_tool = max(tools_with_capability, key=score_tool)
        return best_tool
    
    def set_default_tool(self, tool_name: str) -> None:
        """
        Set the default tool for searches.
        
        Args:
            tool_name: Name of tool to set as default
            
        Raises:
            KeyError: If tool not registered
        """
        if tool_name not in self._registrations:
            raise KeyError(f"Cannot set default: tool '{tool_name}' not registered")
        
        self._default_tool = tool_name
        logger.info(f"Set default MCP tool: {tool_name}")
    
    def get_default_tool(self) -> Optional[MCPSearchTool]:
        """
        Get the default tool.
        
        Returns:
            Default tool if set and available, None otherwise
        """
        if not self._default_tool:
            return None
        
        try:
            return self.get_tool(self._default_tool)
        except (KeyError, MCPSearchException):
            return None
    
    def get_tool_statistics(self, tool_name: str) -> Dict[str, Any]:
        """
        Get performance statistics for a tool.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Dictionary with tool statistics
            
        Raises:
            KeyError: If tool not found
        """
        if tool_name not in self._registrations:
            raise KeyError(f"Tool '{tool_name}' not found")
        
        registration = self._registrations[tool_name]
        
        return {
            "tool_name": tool_name,
            "status": registration.status.value,
            "enabled": registration.enabled,
            "priority": registration.priority,
            "capabilities": [c.value for c in registration.tool_info.capabilities],
            "total_searches": registration.total_searches,
            "success_count": registration.success_count,
            "error_count": registration.error_count,
            "success_rate": registration.get_success_rate(),
            "average_search_time_ms": registration.get_average_search_time(),
            "total_cost_incurred": registration.total_cost_incurred,
            "last_health_check": registration.last_health_check.isoformat(),
            "last_error": str(registration.last_error) if registration.last_error else None,
            "requests_this_minute": registration.requests_this_minute,
            "rate_limit_per_minute": registration.tool_info.rate_limit_per_minute
        }
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """
        Get overall registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        total_tools = len(self._registrations)
        active_tools = len([r for r in self._registrations.values() 
                           if r.status == ToolStatus.ACTIVE])
        available_tools = len(self.get_available_tools())
        
        total_searches = sum(r.total_searches for r in self._registrations.values())
        total_errors = sum(r.error_count for r in self._registrations.values())
        total_cost = sum(r.total_cost_incurred for r in self._registrations.values())
        
        # Capability distribution
        capability_counts = {}
        for registration in self._registrations.values():
            for capability in registration.tool_info.capabilities:
                capability_counts[capability.value] = capability_counts.get(capability.value, 0) + 1
        
        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "available_tools": available_tools,
            "total_searches": total_searches,
            "total_errors": total_errors,
            "overall_success_rate": (total_searches - total_errors) / max(total_searches, 1),
            "total_cost_incurred": total_cost,
            "default_tool": self._default_tool,
            "capability_distribution": capability_counts,
            "health_check_interval": self._health_check_interval,
            "auto_disable_enabled": self._enable_auto_disable
        }
    
    async def record_search_result(
        self,
        tool_name: str,
        success: bool,
        search_time_ms: float,
        error: Optional[Exception] = None,
        cost: Optional[float] = None
    ) -> None:
        """
        Record the result of a search operation.
        
        Args:
            tool_name: Name of tool that performed search
            success: Whether search was successful
            search_time_ms: Time taken for search
            error: Error if search failed
            cost: Cost incurred for search
        """
        if tool_name not in self._registrations:
            return
        
        registration = self._registrations[tool_name]
        registration.record_request()
        
        if success:
            registration.record_success(search_time_ms, cost)
        else:
            registration.record_error(error or Exception("Unknown error"))
        
        # Auto-disable tool if error rate is too high
        if (self._enable_auto_disable and 
            registration.get_success_rate() < (1 - self._max_error_rate) and
            registration.total_searches > 10):  # Need minimum samples
            
            registration.enabled = False
            registration.status = ToolStatus.ERROR
            logger.warning(
                f"Auto-disabled tool {tool_name} due to high error rate: "
                f"{registration.get_success_rate():.2%}"
            )
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all registered tools."""
        for registration in self._registrations.values():
            if not registration.enabled:
                continue
            
            try:
                async with registration.tool:
                    health_info = await registration.tool.health_check()
                
                registration.last_health_check = datetime.utcnow()
                registration.health_check_count += 1
                
                # Update status based on health
                status = health_info.get("status", "unknown").lower()
                if status == "healthy":
                    if registration.status in [ToolStatus.ERROR, ToolStatus.RATE_LIMITED]:
                        registration.status = ToolStatus.ACTIVE
                        logger.info(f"Tool {registration.tool_info.tool_name} recovered")
                elif status == "degraded":
                    # Keep current status but log warning
                    logger.warning(f"Tool {registration.tool_info.tool_name} is degraded")
                elif status == "unhealthy":
                    registration.status = ToolStatus.ERROR
                    logger.warning(f"Tool {registration.tool_info.tool_name} is unhealthy")
                
            except Exception as e:
                registration.record_error(e)
                logger.warning(
                    f"Health check failed for {registration.tool_info.tool_name}: {e}"
                )
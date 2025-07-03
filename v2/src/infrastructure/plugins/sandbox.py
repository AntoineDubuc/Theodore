#!/usr/bin/env python3
"""
Theodore v2 Plugin Sandbox

Secure execution environment for plugins with resource limits,
permission controls, and isolation mechanisms.
"""

import os
import sys
import time
import threading
import resource
import tracemalloc
from typing import Dict, Any, Optional, Set, List, Type
from dataclasses import dataclass
from contextlib import contextmanager
import asyncio
import signal
from pathlib import Path

from .base import BasePlugin, PluginMetadata


class SandboxViolationError(Exception):
    """Raised when plugin violates sandbox restrictions"""
    pass


class ResourceLimitError(SandboxViolationError):
    """Raised when plugin exceeds resource limits"""
    pass


class PermissionDeniedError(SandboxViolationError):
    """Raised when plugin attempts forbidden operation"""
    pass


@dataclass
class ResourceLimits:
    """Resource limits for plugin execution"""
    max_memory_mb: int = 128
    max_cpu_time_seconds: int = 30
    max_open_files: int = 50
    max_network_connections: int = 10
    max_disk_io_mb: int = 100
    max_execution_time_seconds: int = 60


@dataclass 
class PluginPermissions:
    """Permissions for plugin operations"""
    network_access: bool = False
    file_system_read: Set[str] = None
    file_system_write: Set[str] = None
    subprocess_execution: bool = False
    system_calls: Set[str] = None
    environment_variables: Set[str] = None
    
    def __post_init__(self):
        if self.file_system_read is None:
            self.file_system_read = set()
        if self.file_system_write is None:
            self.file_system_write = set()
        if self.system_calls is None:
            self.system_calls = set()
        if self.environment_variables is None:
            self.environment_variables = set()


class ResourceMonitor:
    """Monitor and enforce resource usage limits"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.start_time = None
        self.memory_tracker = None
        self.cpu_start = None
        
        # Track resource usage
        self.peak_memory_mb = 0
        self.cpu_time_used = 0
        self.files_opened = 0
        self.network_connections = 0
        
        # Original resource limits
        self.original_limits = {}
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        
        # Start memory tracking
        tracemalloc.start()
        
        # Get CPU time baseline
        self.cpu_start = time.process_time()
        
        # Set resource limits
        self._set_resource_limits()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        # Stop memory tracking
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        # Restore original resource limits
        self._restore_resource_limits()
    
    def check_limits(self):
        """Check if resource limits are exceeded"""
        current_time = time.time()
        
        # Check execution time
        if self.start_time and current_time - self.start_time > self.limits.max_execution_time_seconds:
            raise ResourceLimitError(
                f"Execution time limit exceeded: {current_time - self.start_time:.2f}s > {self.limits.max_execution_time_seconds}s"
            )
        
        # Check memory usage
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            peak_mb = peak / 1024 / 1024
            self.peak_memory_mb = max(self.peak_memory_mb, peak_mb)
            
            if peak_mb > self.limits.max_memory_mb:
                raise ResourceLimitError(
                    f"Memory limit exceeded: {peak_mb:.2f}MB > {self.limits.max_memory_mb}MB"
                )
        
        # Check CPU time
        if self.cpu_start:
            cpu_time = time.process_time() - self.cpu_start
            self.cpu_time_used = cpu_time
            
            if cpu_time > self.limits.max_cpu_time_seconds:
                raise ResourceLimitError(
                    f"CPU time limit exceeded: {cpu_time:.2f}s > {self.limits.max_cpu_time_seconds}s"
                )
    
    def _set_resource_limits(self):
        """Set system resource limits"""
        try:
            # Memory limit (virtual memory)
            if hasattr(resource, 'RLIMIT_AS'):
                current_limit = resource.getrlimit(resource.RLIMIT_AS)
                self.original_limits['RLIMIT_AS'] = current_limit
                new_limit = self.limits.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (new_limit, current_limit[1]))
            
            # CPU time limit
            if hasattr(resource, 'RLIMIT_CPU'):
                current_limit = resource.getrlimit(resource.RLIMIT_CPU)
                self.original_limits['RLIMIT_CPU'] = current_limit
                resource.setrlimit(resource.RLIMIT_CPU, (self.limits.max_cpu_time_seconds, current_limit[1]))
            
            # File descriptor limit
            if hasattr(resource, 'RLIMIT_NOFILE'):
                current_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
                self.original_limits['RLIMIT_NOFILE'] = current_limit
                resource.setrlimit(resource.RLIMIT_NOFILE, (self.limits.max_open_files, current_limit[1]))
                
        except (OSError, ValueError) as e:
            print(f"Warning: Could not set resource limits: {e}")
    
    def _restore_resource_limits(self):
        """Restore original resource limits"""
        try:
            for limit_name, original_limit in self.original_limits.items():
                limit_constant = getattr(resource, limit_name)
                resource.setrlimit(limit_constant, original_limit)
        except (OSError, ValueError) as e:
            print(f"Warning: Could not restore resource limits: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        stats = {
            'peak_memory_mb': self.peak_memory_mb,
            'cpu_time_used': self.cpu_time_used,
            'execution_time': time.time() - self.start_time if self.start_time else 0,
            'files_opened': self.files_opened,
            'network_connections': self.network_connections
        }
        
        # Add current memory usage if tracking
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            stats['current_memory_mb'] = current / 1024 / 1024
        
        return stats


class SecureImportHook:
    """Import hook to control plugin imports"""
    
    def __init__(self, permissions: PluginPermissions):
        self.permissions = permissions
        self.blocked_modules = {
            'subprocess', 'os.system', 'shutil', 'socket', 'urllib',
            'requests', 'http', 'ftplib', 'smtplib', 'telnetlib'
        }
        
        if not permissions.network_access:
            self.blocked_modules.update({
                'socket', 'urllib', 'requests', 'http', 'aiohttp',
                'httpx', 'websockets', 'ftplib', 'smtplib'
            })
    
    def find_spec(self, fullname, path, target=None):
        """Check if module import should be allowed"""
        if fullname in self.blocked_modules:
            raise PermissionDeniedError(f"Import of module '{fullname}' is not allowed")
        return None  # Use default import mechanism


class FileSystemGuard:
    """Guard for file system operations"""
    
    def __init__(self, permissions: PluginPermissions):
        self.permissions = permissions
        self.original_open = None
    
    def install(self):
        """Install file system guards"""
        import builtins
        self.original_open = builtins.open
        builtins.open = self._guarded_open
    
    def uninstall(self):
        """Uninstall file system guards"""
        import builtins
        if self.original_open:
            builtins.open = self.original_open
    
    def _guarded_open(self, file, mode='r', **kwargs):
        """Guarded file open operation"""
        file_path = Path(file).resolve()
        
        # Check read permissions
        if 'r' in mode:
            if not self._check_read_permission(file_path):
                raise PermissionDeniedError(f"Read access denied: {file_path}")
        
        # Check write permissions
        if any(m in mode for m in ['w', 'a', 'x']):
            if not self._check_write_permission(file_path):
                raise PermissionDeniedError(f"Write access denied: {file_path}")
        
        return self.original_open(file, mode, **kwargs)
    
    def _check_read_permission(self, file_path: Path) -> bool:
        """Check if file read is permitted"""
        if not self.permissions.file_system_read:
            return False
        
        file_str = str(file_path)
        for allowed_path in self.permissions.file_system_read:
            if file_str.startswith(allowed_path):
                return True
        
        return False
    
    def _check_write_permission(self, file_path: Path) -> bool:
        """Check if file write is permitted"""
        if not self.permissions.file_system_write:
            return False
        
        file_str = str(file_path)
        for allowed_path in self.permissions.file_system_write:
            if file_str.startswith(allowed_path):
                return True
        
        return False


class PluginSandbox:
    """Secure sandbox for plugin execution"""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.resource_limits = ResourceLimits()
        self.permissions = PluginPermissions()
        self.resource_monitor = None
        self.import_hook = None
        self.filesystem_guard = None
        self._active = False
        
        # Execution context
        self._execution_thread = None
        self._execution_result = None
        self._execution_error = None
    
    def configure_limits(self, limits: ResourceLimits):
        """Configure resource limits"""
        self.resource_limits = limits
    
    def configure_permissions(self, permissions: PluginPermissions):
        """Configure permissions"""
        self.permissions = permissions
    
    @contextmanager
    def execution_context(self):
        """Context manager for sandboxed execution"""
        try:
            self._activate_sandbox()
            yield
        finally:
            self._deactivate_sandbox()
    
    def _activate_sandbox(self):
        """Activate sandbox protections"""
        if self._active:
            return
        
        # Start resource monitoring
        self.resource_monitor = ResourceMonitor(self.resource_limits)
        self.resource_monitor.start_monitoring()
        
        # Install import hook
        self.import_hook = SecureImportHook(self.permissions)
        sys.meta_path.insert(0, self.import_hook)
        
        # Install filesystem guard
        self.filesystem_guard = FileSystemGuard(self.permissions)
        self.filesystem_guard.install()
        
        self._active = True
    
    def _deactivate_sandbox(self):
        """Deactivate sandbox protections"""
        if not self._active:
            return
        
        # Remove import hook
        if self.import_hook and self.import_hook in sys.meta_path:
            sys.meta_path.remove(self.import_hook)
        
        # Uninstall filesystem guard
        if self.filesystem_guard:
            self.filesystem_guard.uninstall()
        
        # Stop resource monitoring
        if self.resource_monitor:
            self.resource_monitor.stop_monitoring()
        
        self._active = False
    
    async def create_plugin_instance(
        self, 
        plugin_class: Type[BasePlugin], 
        metadata: PluginMetadata,
        config: Optional[Dict[str, Any]] = None
    ) -> BasePlugin:
        """Create plugin instance in sandbox"""
        
        def create_instance():
            with self.execution_context():
                try:
                    instance = plugin_class(metadata, config)
                    self._execution_result = instance
                except Exception as e:
                    self._execution_error = e
        
        # Run in separate thread with timeout
        self._execution_thread = threading.Thread(target=create_instance)
        self._execution_thread.start()
        
        # Wait for completion with timeout
        timeout = self.resource_limits.max_execution_time_seconds
        self._execution_thread.join(timeout=timeout)
        
        if self._execution_thread.is_alive():
            # Force terminate if still running
            raise ResourceLimitError(f"Plugin instantiation timed out after {timeout}s")
        
        if self._execution_error:
            raise self._execution_error
        
        if not self._execution_result:
            raise SandboxViolationError("Plugin instantiation failed")
        
        return self._execution_result
    
    async def execute_plugin_method(
        self, 
        instance: BasePlugin, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Any:
        """Execute plugin method in sandbox"""
        
        if not hasattr(instance, method_name):
            raise AttributeError(f"Plugin does not have method: {method_name}")
        
        method = getattr(instance, method_name)
        
        def execute_method():
            with self.execution_context():
                try:
                    # Check resource limits periodically during execution
                    if self.resource_monitor:
                        self.resource_monitor.check_limits()
                    
                    result = method(*args, **kwargs)
                    
                    # Handle async methods
                    if asyncio.iscoroutine(result):
                        self._execution_result = asyncio.run(result)
                    else:
                        self._execution_result = result
                        
                except Exception as e:
                    self._execution_error = e
        
        # Reset execution state
        self._execution_result = None
        self._execution_error = None
        
        # Run in separate thread
        self._execution_thread = threading.Thread(target=execute_method)
        self._execution_thread.start()
        
        # Wait for completion with timeout
        timeout = self.resource_limits.max_execution_time_seconds
        self._execution_thread.join(timeout=timeout)
        
        if self._execution_thread.is_alive():
            raise ResourceLimitError(f"Method execution timed out after {timeout}s")
        
        if self._execution_error:
            raise self._execution_error
        
        return self._execution_result
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage statistics"""
        if self.resource_monitor:
            return self.resource_monitor.get_usage_stats()
        return {}
    
    def is_active(self) -> bool:
        """Check if sandbox is currently active"""
        return self._active


class SandboxManager:
    """Manager for multiple plugin sandboxes"""
    
    def __init__(self):
        self.sandboxes: Dict[str, PluginSandbox] = {}
        self._lock = threading.RLock()
    
    def create_sandbox(
        self, 
        plugin_id: str, 
        limits: Optional[ResourceLimits] = None,
        permissions: Optional[PluginPermissions] = None
    ) -> PluginSandbox:
        """Create a new sandbox for a plugin"""
        
        with self._lock:
            if plugin_id in self.sandboxes:
                return self.sandboxes[plugin_id]
            
            sandbox = PluginSandbox(plugin_id)
            
            if limits:
                sandbox.configure_limits(limits)
            
            if permissions:
                sandbox.configure_permissions(permissions)
            
            self.sandboxes[plugin_id] = sandbox
            return sandbox
    
    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """Get existing sandbox for plugin"""
        with self._lock:
            return self.sandboxes.get(plugin_id)
    
    def remove_sandbox(self, plugin_id: str):
        """Remove sandbox for plugin"""
        with self._lock:
            if plugin_id in self.sandboxes:
                sandbox = self.sandboxes[plugin_id]
                if sandbox.is_active():
                    sandbox._deactivate_sandbox()
                del self.sandboxes[plugin_id]
    
    def get_all_resource_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get resource usage for all sandboxes"""
        with self._lock:
            usage = {}
            for plugin_id, sandbox in self.sandboxes.items():
                usage[plugin_id] = sandbox.get_resource_usage()
            return usage
    
    def cleanup_inactive_sandboxes(self):
        """Clean up inactive sandboxes"""
        with self._lock:
            inactive = [
                plugin_id for plugin_id, sandbox in self.sandboxes.items()
                if not sandbox.is_active()
            ]
            
            for plugin_id in inactive:
                del self.sandboxes[plugin_id]


# Global sandbox manager
_global_sandbox_manager: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get global sandbox manager"""
    global _global_sandbox_manager
    if _global_sandbox_manager is None:
        _global_sandbox_manager = SandboxManager()
    return _global_sandbox_manager
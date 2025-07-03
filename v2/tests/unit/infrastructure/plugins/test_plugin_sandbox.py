#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Sandbox
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.infrastructure.plugins.sandbox import (
    PluginSandbox,
    SandboxManager,
    ResourceMonitor,
    SecureImportHook,
    FileSystemGuard,
    ResourceLimits,
    PluginPermissions,
    SandboxViolationError,
    ResourceLimitError,
    PermissionDeniedError,
    get_sandbox_manager
)
from src.infrastructure.plugins.base import BasePlugin, PluginMetadata


class TestResourceLimits:
    """Test resource limits configuration"""
    
    def test_default_limits(self):
        """Test default resource limits"""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 128
        assert limits.max_cpu_time_seconds == 30
        assert limits.max_open_files == 50
        assert limits.max_network_connections == 10
        assert limits.max_disk_io_mb == 100
        assert limits.max_execution_time_seconds == 60
    
    def test_custom_limits(self):
        """Test custom resource limits"""
        limits = ResourceLimits(
            max_memory_mb=256,
            max_cpu_time_seconds=60,
            max_execution_time_seconds=120
        )
        
        assert limits.max_memory_mb == 256
        assert limits.max_cpu_time_seconds == 60
        assert limits.max_execution_time_seconds == 120


class TestPluginPermissions:
    """Test plugin permissions configuration"""
    
    def test_default_permissions(self):
        """Test default permissions"""
        perms = PluginPermissions()
        
        assert not perms.network_access
        assert not perms.subprocess_execution
        assert len(perms.file_system_read) == 0
        assert len(perms.file_system_write) == 0
        assert len(perms.system_calls) == 0
        assert len(perms.environment_variables) == 0
    
    def test_custom_permissions(self):
        """Test custom permissions"""
        perms = PluginPermissions(
            network_access=True,
            file_system_read={"/tmp", "/var/tmp"},
            file_system_write={"/tmp/plugins"},
            subprocess_execution=True
        )
        
        assert perms.network_access
        assert perms.subprocess_execution
        assert "/tmp" in perms.file_system_read
        assert "/tmp/plugins" in perms.file_system_write


class TestResourceMonitor:
    """Test resource monitoring functionality"""
    
    def test_monitor_creation(self):
        """Test creating resource monitor"""
        limits = ResourceLimits(max_memory_mb=64, max_cpu_time_seconds=10)
        monitor = ResourceMonitor(limits)
        
        assert monitor.limits == limits
        assert monitor.start_time is None
        assert monitor.peak_memory_mb == 0
    
    def test_monitor_lifecycle(self):
        """Test monitor start/stop lifecycle"""
        limits = ResourceLimits()
        monitor = ResourceMonitor(limits)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor.start_time is not None
        assert monitor.cpu_start is not None
        
        # Stop monitoring
        monitor.stop_monitoring()
        # Should not raise errors
    
    def test_execution_time_limit(self):
        """Test execution time limit checking"""
        limits = ResourceLimits(max_execution_time_seconds=0.1)  # Very short limit
        monitor = ResourceMonitor(limits)
        
        monitor.start_monitoring()
        time.sleep(0.2)  # Exceed limit
        
        with pytest.raises(ResourceLimitError, match="Execution time limit exceeded"):
            monitor.check_limits()
        
        monitor.stop_monitoring()
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        limits = ResourceLimits()
        monitor = ResourceMonitor(limits)
        
        monitor.start_monitoring()
        stats = monitor.get_usage_stats()
        
        assert isinstance(stats, dict)
        assert "peak_memory_mb" in stats
        assert "cpu_time_used" in stats
        assert "execution_time" in stats
        assert "files_opened" in stats
        assert "network_connections" in stats
        
        monitor.stop_monitoring()


class TestSecureImportHook:
    """Test secure import hook functionality"""
    
    def test_hook_creation(self):
        """Test creating import hook"""
        perms = PluginPermissions(network_access=False)
        hook = SecureImportHook(perms)
        
        assert hook.permissions == perms
        assert "subprocess" in hook.blocked_modules
        assert "socket" in hook.blocked_modules
    
    def test_network_access_blocking(self):
        """Test network access blocking"""
        perms = PluginPermissions(network_access=False)
        hook = SecureImportHook(perms)
        
        # Should block network modules
        assert "socket" in hook.blocked_modules
        assert "urllib" in hook.blocked_modules
        assert "requests" in hook.blocked_modules
    
    def test_network_access_allowed(self):
        """Test network access when allowed"""
        perms = PluginPermissions(network_access=True)
        hook = SecureImportHook(perms)
        
        # Should still block dangerous modules, but allow network modules
        assert "subprocess" in hook.blocked_modules
        # Network modules should not be in blocked list when network_access=True
    
    def test_find_spec_blocking(self):
        """Test import blocking through find_spec"""
        perms = PluginPermissions()
        hook = SecureImportHook(perms)
        
        # Should raise PermissionDeniedError for blocked modules
        with pytest.raises(PermissionDeniedError, match="Import of module 'subprocess' is not allowed"):
            hook.find_spec("subprocess", None, None)
        
        # Should return None for allowed modules (use default import)
        result = hook.find_spec("json", None, None)
        assert result is None


class TestFileSystemGuard:
    """Test file system guard functionality"""
    
    def test_guard_creation(self):
        """Test creating file system guard"""
        perms = PluginPermissions(
            file_system_read={"/tmp"},
            file_system_write={"/tmp/plugins"}
        )
        guard = FileSystemGuard(perms)
        
        assert guard.permissions == perms
        assert guard.original_open is None
    
    def test_read_permission_check(self):
        """Test read permission checking"""
        perms = PluginPermissions(file_system_read={"/tmp", "/var/tmp"})
        guard = FileSystemGuard(perms)
        
        # Should allow reads from permitted paths
        assert guard._check_read_permission(Path("/tmp/file.txt"))
        assert guard._check_read_permission(Path("/var/tmp/data.json"))
        
        # Should deny reads from non-permitted paths
        assert not guard._check_read_permission(Path("/etc/passwd"))
        assert not guard._check_read_permission(Path("/home/user/secret.txt"))
    
    def test_write_permission_check(self):
        """Test write permission checking"""
        perms = PluginPermissions(file_system_write={"/tmp/plugins"})
        guard = FileSystemGuard(perms)
        
        # Should allow writes to permitted paths
        assert guard._check_write_permission(Path("/tmp/plugins/output.txt"))
        
        # Should deny writes to non-permitted paths
        assert not guard._check_write_permission(Path("/tmp/system.conf"))
        assert not guard._check_write_permission(Path("/etc/important.cfg"))


class TestPluginSandbox:
    """Test plugin sandbox functionality"""
    
    class TestPlugin(BasePlugin):
        """Test plugin for sandbox testing"""
        
        def __init__(self, metadata, config=None):
            super().__init__(metadata, config)
            self.test_value = "initialized"
        
        async def initialize(self) -> bool:
            self._initialized = True
            return True
        
        async def cleanup(self) -> bool:
            return True
        
        async def enable(self) -> bool:
            self._enabled = True
            return True
        
        async def disable(self) -> bool:
            self._enabled = False
            return True
        
        def get_test_value(self):
            return self.test_value
        
        def cpu_intensive_task(self):
            """CPU intensive task for testing limits"""
            total = 0
            for i in range(1000000):
                total += i * i
            return total
    
    @pytest.fixture
    def sandbox(self):
        """Create test sandbox"""
        return PluginSandbox("test-plugin-id")
    
    @pytest.fixture
    def test_metadata(self):
        """Create test metadata"""
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin for sandbox",
            author="Test Author"
        )
    
    def test_sandbox_creation(self, sandbox):
        """Test sandbox creation"""
        assert sandbox.plugin_id == "test-plugin-id"
        assert not sandbox.is_active()
        assert isinstance(sandbox.resource_limits, ResourceLimits)
        assert isinstance(sandbox.permissions, PluginPermissions)
    
    def test_configure_limits(self, sandbox):
        """Test configuring resource limits"""
        limits = ResourceLimits(max_memory_mb=64, max_cpu_time_seconds=10)
        sandbox.configure_limits(limits)
        
        assert sandbox.resource_limits == limits
    
    def test_configure_permissions(self, sandbox):
        """Test configuring permissions"""
        perms = PluginPermissions(network_access=True, file_system_read={"/tmp"})
        sandbox.configure_permissions(perms)
        
        assert sandbox.permissions == perms
    
    def test_execution_context(self, sandbox):
        """Test execution context manager"""
        assert not sandbox.is_active()
        
        with sandbox.execution_context():
            assert sandbox.is_active()
        
        assert not sandbox.is_active()
    
    @pytest.mark.asyncio
    async def test_create_plugin_instance(self, sandbox, test_metadata):
        """Test creating plugin instance in sandbox"""
        # Configure lenient limits for testing
        limits = ResourceLimits(
            max_memory_mb=512,
            max_cpu_time_seconds=30,
            max_execution_time_seconds=60
        )
        sandbox.configure_limits(limits)
        
        instance = await sandbox.create_plugin_instance(
            self.TestPlugin, 
            test_metadata,
            {"test_config": "value"}
        )
        
        assert isinstance(instance, self.TestPlugin)
        assert instance.metadata == test_metadata
        assert instance.get_config("test_config") == "value"
        assert instance.test_value == "initialized"
    
    @pytest.mark.asyncio
    async def test_execute_plugin_method(self, sandbox, test_metadata):
        """Test executing plugin method in sandbox"""
        # Configure lenient limits
        limits = ResourceLimits(
            max_memory_mb=512,
            max_cpu_time_seconds=30,
            max_execution_time_seconds=60
        )
        sandbox.configure_limits(limits)
        
        instance = await sandbox.create_plugin_instance(self.TestPlugin, test_metadata)
        
        # Execute method
        result = await sandbox.execute_plugin_method(instance, "get_test_value")
        assert result == "initialized"
        
        # Execute async method
        result = await sandbox.execute_plugin_method(instance, "initialize")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_method_execution_timeout(self, sandbox, test_metadata):
        """Test method execution timeout"""
        # Configure very short timeout
        limits = ResourceLimits(max_execution_time_seconds=0.1)
        sandbox.configure_limits(limits)
        
        instance = await sandbox.create_plugin_instance(self.TestPlugin, test_metadata)
        
        # This should timeout
        with pytest.raises(ResourceLimitError, match="Method execution timed out"):
            await sandbox.execute_plugin_method(instance, "cpu_intensive_task")
    
    @pytest.mark.asyncio
    async def test_nonexistent_method(self, sandbox, test_metadata):
        """Test executing non-existent method"""
        limits = ResourceLimits(max_execution_time_seconds=60)
        sandbox.configure_limits(limits)
        
        instance = await sandbox.create_plugin_instance(self.TestPlugin, test_metadata)
        
        with pytest.raises(AttributeError, match="Plugin does not have method"):
            await sandbox.execute_plugin_method(instance, "nonexistent_method")
    
    def test_get_resource_usage(self, sandbox):
        """Test getting resource usage"""
        usage = sandbox.get_resource_usage()
        assert isinstance(usage, dict)
        # Should return empty dict when not active
        assert len(usage) == 0


class TestSandboxManager:
    """Test sandbox manager functionality"""
    
    def test_manager_creation(self):
        """Test creating sandbox manager"""
        manager = SandboxManager()
        
        assert isinstance(manager.sandboxes, dict)
        assert len(manager.sandboxes) == 0
    
    def test_create_sandbox(self):
        """Test creating sandbox"""
        manager = SandboxManager()
        
        sandbox = manager.create_sandbox("test-plugin")
        
        assert isinstance(sandbox, PluginSandbox)
        assert sandbox.plugin_id == "test-plugin"
        assert "test-plugin" in manager.sandboxes
    
    def test_create_sandbox_with_config(self):
        """Test creating sandbox with configuration"""
        manager = SandboxManager()
        
        limits = ResourceLimits(max_memory_mb=64)
        perms = PluginPermissions(network_access=True)
        
        sandbox = manager.create_sandbox("test-plugin", limits=limits, permissions=perms)
        
        assert sandbox.resource_limits == limits
        assert sandbox.permissions == perms
    
    def test_get_existing_sandbox(self):
        """Test getting existing sandbox"""
        manager = SandboxManager()
        
        # Create sandbox
        original = manager.create_sandbox("test-plugin")
        
        # Get existing should return same instance
        retrieved = manager.create_sandbox("test-plugin")
        assert retrieved is original
        
        # Get by get_sandbox method
        retrieved2 = manager.get_sandbox("test-plugin")
        assert retrieved2 is original
    
    def test_get_nonexistent_sandbox(self):
        """Test getting non-existent sandbox"""
        manager = SandboxManager()
        
        result = manager.get_sandbox("nonexistent")
        assert result is None
    
    def test_remove_sandbox(self):
        """Test removing sandbox"""
        manager = SandboxManager()
        
        # Create sandbox
        sandbox = manager.create_sandbox("test-plugin")
        assert "test-plugin" in manager.sandboxes
        
        # Remove sandbox
        manager.remove_sandbox("test-plugin")
        assert "test-plugin" not in manager.sandboxes
    
    def test_remove_active_sandbox(self):
        """Test removing active sandbox"""
        manager = SandboxManager()
        
        # Create and activate sandbox
        sandbox = manager.create_sandbox("test-plugin")
        
        # Mock active state
        with patch.object(sandbox, 'is_active', return_value=True):
            with patch.object(sandbox, '_deactivate_sandbox') as mock_deactivate:
                manager.remove_sandbox("test-plugin")
                mock_deactivate.assert_called_once()
    
    def test_get_all_resource_usage(self):
        """Test getting resource usage for all sandboxes"""
        manager = SandboxManager()
        
        # Create sandboxes
        sandbox1 = manager.create_sandbox("plugin1")
        sandbox2 = manager.create_sandbox("plugin2")
        
        # Mock resource usage
        with patch.object(sandbox1, 'get_resource_usage', return_value={"memory": 50}):
            with patch.object(sandbox2, 'get_resource_usage', return_value={"memory": 75}):
                usage = manager.get_all_resource_usage()
                
                assert "plugin1" in usage
                assert "plugin2" in usage
                assert usage["plugin1"]["memory"] == 50
                assert usage["plugin2"]["memory"] == 75
    
    def test_cleanup_inactive_sandboxes(self):
        """Test cleaning up inactive sandboxes"""
        manager = SandboxManager()
        
        # Create sandboxes
        active_sandbox = manager.create_sandbox("active-plugin")
        inactive_sandbox = manager.create_sandbox("inactive-plugin")
        
        # Mock activity status
        with patch.object(active_sandbox, 'is_active', return_value=True):
            with patch.object(inactive_sandbox, 'is_active', return_value=False):
                manager.cleanup_inactive_sandboxes()
                
                # Active should remain, inactive should be removed
                assert "active-plugin" in manager.sandboxes
                assert "inactive-plugin" not in manager.sandboxes


class TestGlobalSandboxManager:
    """Test global sandbox manager functions"""
    
    def test_get_global_sandbox_manager(self):
        """Test getting global sandbox manager"""
        manager1 = get_sandbox_manager()
        manager2 = get_sandbox_manager()
        
        # Should return same instance
        assert manager1 is manager2
        assert isinstance(manager1, SandboxManager)
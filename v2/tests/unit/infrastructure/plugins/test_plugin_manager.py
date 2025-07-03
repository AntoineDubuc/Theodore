#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Manager
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from src.infrastructure.plugins.manager import (
    PluginManager,
    PluginLifecycleError,
    PluginInstallError,
    PluginConfigurationError,
    PluginDependencyError,
    InstallationOptions,
    PluginConfig,
    get_plugin_manager,
    initialize_plugin_system
)
from src.infrastructure.plugins.base import (
    PluginMetadata,
    PluginStatus,
    PluginCategory,
    PluginDependency,
    PluginCompatibility,
    BasePlugin
)
from src.infrastructure.plugins.discovery import PluginSource


class TestInstallationOptions:
    """Test installation options configuration"""
    
    def test_default_options(self):
        """Test default installation options"""
        options = InstallationOptions()
        
        assert not options.force_reinstall
        assert not options.skip_dependencies
        assert options.install_dependencies
        assert options.verify_signatures
        assert options.sandbox_enabled
        assert options.custom_install_path is None
        assert options.memory_limit_mb == 128
        assert options.cpu_limit_seconds == 30
        assert options.execution_timeout_seconds == 60
        assert not options.network_access
        assert len(options.file_read_paths) == 0
        assert len(options.file_write_paths) == 0
    
    def test_custom_options(self):
        """Test custom installation options"""
        options = InstallationOptions(
            force_reinstall=True,
            memory_limit_mb=256,
            network_access=True,
            file_read_paths=["/tmp"],
            file_write_paths=["/tmp/plugins"]
        )
        
        assert options.force_reinstall
        assert options.memory_limit_mb == 256
        assert options.network_access
        assert "/tmp" in options.file_read_paths
        assert "/tmp/plugins" in options.file_write_paths


class TestPluginConfig:
    """Test plugin configuration functionality"""
    
    def test_config_creation(self):
        """Test creating plugin config"""
        config = PluginConfig(
            plugin_id="test-plugin-id",
            config={"setting1": "value1", "setting2": 42},
            last_updated=datetime.now(timezone.utc)
        )
        
        assert config.plugin_id == "test-plugin-id"
        assert config.config["setting1"] == "value1"
        assert config.config["setting2"] == 42
        assert config.schema_version == "1.0.0"
    
    def test_config_serialization(self):
        """Test config serialization"""
        now = datetime.now(timezone.utc)
        config = PluginConfig(
            plugin_id="test-plugin-id",
            config={"test": "value"},
            last_updated=now
        )
        
        # To dict
        data = config.to_dict()
        assert data["plugin_id"] == "test-plugin-id"
        assert data["config"]["test"] == "value"
        assert data["last_updated"] == now.isoformat()
        
        # From dict
        restored = PluginConfig.from_dict(data)
        assert restored.plugin_id == config.plugin_id
        assert restored.config == config.config
        assert restored.last_updated == config.last_updated


class TestPluginManager:
    """Test plugin manager functionality"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugins_dir = temp_path / "plugins"
            config_dir = temp_path / "config"
            plugins_dir.mkdir()
            config_dir.mkdir()
            yield plugins_dir, config_dir
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock registry"""
        registry = Mock()
        registry.initialize = AsyncMock(return_value=True)
        registry.register_plugin = AsyncMock(return_value=True)
        registry.unregister_plugin = AsyncMock(return_value=True)
        registry.get_plugin = Mock(return_value=None)
        registry.get_plugin_by_name = Mock(return_value=None)
        registry.get_plugin_instance = Mock(return_value=None)
        registry.get_dependents = Mock(return_value=[])
        registry.update_plugin_status = Mock(return_value=True)
        registry.list_plugins = Mock(return_value=[])
        registry.search_plugins = Mock(return_value=[])
        registry.get_registry_stats = Mock(return_value={"total_plugins": 0})
        return registry
    
    @pytest.fixture
    def mock_loader(self):
        """Create mock loader"""
        loader = Mock()
        loader.load_plugin = AsyncMock()
        loader.load_plugin_by_id = AsyncMock()
        loader.unload_plugin = AsyncMock(return_value=True)
        loader.reload_plugin = AsyncMock()
        loader.list_loaded_plugins = Mock(return_value=[])
        loader._discover_plugin_metadata = AsyncMock()
        return loader
    
    @pytest.fixture
    def mock_sandbox_manager(self):
        """Create mock sandbox manager"""
        manager = Mock()
        manager.create_sandbox = Mock()
        manager.get_sandbox = Mock(return_value=None)
        manager.remove_sandbox = Mock()
        return manager
    
    @pytest.fixture
    def mock_discovery(self):
        """Create mock discovery"""
        discovery = Mock()
        discovery.search_plugins = AsyncMock(return_value=[])
        return discovery
    
    @pytest.fixture
    def manager(self, temp_dirs, mock_registry, mock_loader, mock_sandbox_manager, mock_discovery):
        """Create test plugin manager"""
        plugins_dir, config_dir = temp_dirs
        
        with patch('src.infrastructure.plugins.manager.get_plugin_registry', return_value=mock_registry):
            with patch('src.infrastructure.plugins.manager.get_plugin_loader', return_value=mock_loader):
                with patch('src.infrastructure.plugins.manager.get_sandbox_manager', return_value=mock_sandbox_manager):
                    with patch('src.infrastructure.plugins.manager.PluginDiscovery', return_value=mock_discovery):
                        return PluginManager(plugins_dir=plugins_dir, config_dir=config_dir)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample plugin metadata"""
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
    
    @pytest.fixture
    def sample_plugin_source(self):
        """Create sample plugin source"""
        return PluginSource(
            type="local",
            location="/path/to/plugin.py",
            name="test-plugin",
            description="Test plugin source"
        )
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initialization"""
        assert await manager.initialize()
        assert manager._initialized
        manager.registry.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_install_plugin_from_source(self, manager, sample_plugin_source, sample_metadata):
        """Test installing plugin from source"""
        await manager.initialize()
        
        # Mock the preparation and installation steps
        with patch.object(manager, '_prepare_plugin_for_installation', 
                         return_value=(Path("/path/to/plugin.py"), sample_metadata)):
            with patch.object(manager, '_install_dependencies', return_value=True):
                with patch.object(manager, '_install_plugin_files', return_value=Path("/installed/plugin.py")):
                    with patch.object(manager, '_configure_plugin_sandbox'):
                        # Mock loader to return plugin instance
                        mock_instance = Mock(spec=BasePlugin)
                        manager.loader.load_plugin.return_value = mock_instance
                        
                        result = await manager.install_plugin(sample_plugin_source)
                        
                        assert result
                        manager.registry.register_plugin.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_install_plugin_from_path(self, manager, sample_metadata):
        """Test installing plugin from file path"""
        await manager.initialize()
        
        plugin_path = Path("/path/to/plugin.py")
        
        with patch.object(manager, '_prepare_plugin_for_installation',
                         return_value=(plugin_path, sample_metadata)):
            with patch.object(manager, '_install_dependencies', return_value=True):
                with patch.object(manager, '_install_plugin_files', return_value=plugin_path):
                    with patch.object(manager, '_configure_plugin_sandbox'):
                        mock_instance = Mock(spec=BasePlugin)
                        manager.loader.load_plugin.return_value = mock_instance
                        
                        result = await manager.install_plugin(plugin_path)
                        
                        assert result
    
    @pytest.mark.asyncio
    async def test_install_plugin_already_installed(self, manager, sample_plugin_source, sample_metadata):
        """Test installing already installed plugin"""
        await manager.initialize()
        
        # Mock existing plugin
        existing_metadata = sample_metadata.copy()
        existing_metadata.status = PluginStatus.INSTALLED
        manager.registry.get_plugin_by_name.return_value = existing_metadata
        
        with patch.object(manager, '_prepare_plugin_for_installation',
                         return_value=(Path("/path"), sample_metadata)):
            result = await manager.install_plugin(sample_plugin_source)
            
            # Should succeed without reinstalling
            assert result
    
    @pytest.mark.asyncio
    async def test_install_plugin_force_reinstall(self, manager, sample_plugin_source, sample_metadata):
        """Test force reinstall of existing plugin"""
        await manager.initialize()
        
        options = InstallationOptions(force_reinstall=True)
        
        # Mock existing plugin
        existing_metadata = sample_metadata.copy()
        existing_metadata.status = PluginStatus.INSTALLED
        manager.registry.get_plugin_by_name.return_value = existing_metadata
        
        with patch.object(manager, '_prepare_plugin_for_installation',
                         return_value=(Path("/path"), sample_metadata)):
            with patch.object(manager, '_install_dependencies', return_value=True):
                with patch.object(manager, '_install_plugin_files', return_value=Path("/installed")):
                    with patch.object(manager, '_configure_plugin_sandbox'):
                        mock_instance = Mock(spec=BasePlugin)
                        manager.loader.load_plugin.return_value = mock_instance
                        
                        result = await manager.install_plugin(sample_plugin_source, options)
                        
                        assert result
                        # Should register with force=True
                        manager.registry.register_plugin.assert_called_once()
                        call_args = manager.registry.register_plugin.call_args
                        assert call_args[1]['force'] == True
    
    @pytest.mark.asyncio
    async def test_install_plugin_dependency_failure(self, manager, sample_plugin_source, sample_metadata):
        """Test plugin installation with dependency failure"""
        await manager.initialize()
        
        with patch.object(manager, '_prepare_plugin_for_installation',
                         return_value=(Path("/path"), sample_metadata)):
            with patch.object(manager, '_install_dependencies', return_value=False):
                result = await manager.install_plugin(sample_plugin_source)
                
                assert not result
    
    @pytest.mark.asyncio
    async def test_uninstall_plugin(self, manager, sample_metadata):
        """Test uninstalling plugin"""
        await manager.initialize()
        
        # Mock existing plugin
        sample_metadata.status = PluginStatus.INSTALLED
        sample_metadata.module_path = "/path/to/plugin.py"
        manager.registry.get_plugin.return_value = sample_metadata
        
        # Mock file system
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('pathlib.Path.unlink') as mock_unlink:
                    result = await manager.uninstall_plugin(sample_metadata.plugin_id)
                    
                    assert result
                    manager.loader.unload_plugin.assert_called_once()
                    manager.sandbox_manager.remove_sandbox.assert_called_once()
                    manager.registry.unregister_plugin.assert_called_once()
                    mock_unlink.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_uninstall_plugin_with_dependents(self, manager, sample_metadata):
        """Test uninstalling plugin with dependents"""
        await manager.initialize()
        
        # Mock plugin with dependents
        dependent_metadata = PluginMetadata(
            name="dependent", version="1.0.0", description="Dependent", author="Author"
        )
        manager.registry.get_plugin.return_value = sample_metadata
        manager.registry.get_dependents.return_value = [dependent_metadata]
        
        result = await manager.uninstall_plugin(sample_metadata.plugin_id)
        
        # Should fail due to dependents
        assert not result
    
    @pytest.mark.asyncio
    async def test_uninstall_plugin_force_with_dependents(self, manager, sample_metadata):
        """Test force uninstalling plugin with dependents"""
        await manager.initialize()
        
        # Mock plugin with dependents
        dependent_metadata = PluginMetadata(
            name="dependent", version="1.0.0", description="Dependent", author="Author"
        )
        sample_metadata.module_path = "/path/to/plugin.py"
        manager.registry.get_plugin.return_value = sample_metadata
        manager.registry.get_dependents.return_value = [dependent_metadata]
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('pathlib.Path.unlink'):
                    result = await manager.uninstall_plugin(sample_metadata.plugin_id, force=True)
                    
                    assert result
                    # Should unregister with force=True
                    call_args = manager.registry.unregister_plugin.call_args
                    assert call_args[1]['force'] == True
    
    @pytest.mark.asyncio
    async def test_enable_plugin(self, manager, sample_metadata):
        """Test enabling plugin"""
        await manager.initialize()
        
        # Mock plugin instance
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.enable = AsyncMock(return_value=True)
        mock_instance.metadata = sample_metadata
        manager.registry.get_plugin_instance.return_value = mock_instance
        
        result = await manager.enable_plugin(sample_metadata.plugin_id)
        
        assert result
        mock_instance.enable.assert_called_once()
        manager.registry.update_plugin_status.assert_called_with(
            sample_metadata.plugin_id, PluginStatus.ENABLED
        )
    
    @pytest.mark.asyncio
    async def test_enable_plugin_not_loaded(self, manager, sample_metadata):
        """Test enabling plugin that's not loaded"""
        await manager.initialize()
        
        # Mock plugin instance that will be loaded
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.enable = AsyncMock(return_value=True)
        mock_instance.metadata = sample_metadata
        
        # First call returns None (not loaded), second call loads it
        manager.registry.get_plugin_instance.return_value = None
        manager.loader.load_plugin_by_id.return_value = mock_instance
        
        result = await manager.enable_plugin(sample_metadata.plugin_id)
        
        assert result
        manager.loader.load_plugin_by_id.assert_called_once_with(sample_metadata.plugin_id)
    
    @pytest.mark.asyncio
    async def test_disable_plugin(self, manager, sample_metadata):
        """Test disabling plugin"""
        await manager.initialize()
        
        # Mock plugin instance
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.disable = AsyncMock(return_value=True)
        mock_instance.metadata = sample_metadata
        manager.registry.get_plugin_instance.return_value = mock_instance
        
        result = await manager.disable_plugin(sample_metadata.plugin_id)
        
        assert result
        mock_instance.disable.assert_called_once()
        manager.registry.update_plugin_status.assert_called_with(
            sample_metadata.plugin_id, PluginStatus.DISABLED
        )
    
    @pytest.mark.asyncio
    async def test_disable_plugin_not_loaded(self, manager, sample_metadata):
        """Test disabling plugin that's not loaded"""
        await manager.initialize()
        
        manager.registry.get_plugin_instance.return_value = None
        
        result = await manager.disable_plugin(sample_metadata.plugin_id)
        
        # Should succeed (already disabled)
        assert result
    
    @pytest.mark.asyncio
    async def test_configure_plugin(self, manager, sample_metadata):
        """Test configuring plugin"""
        await manager.initialize()
        
        config = {"setting1": "value1", "setting2": 42}
        
        # Mock plugin instance
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.update_config = Mock(return_value=True)
        
        manager.registry.get_plugin.return_value = sample_metadata
        manager.registry.get_plugin_instance.return_value = mock_instance
        
        result = await manager.configure_plugin(sample_metadata.plugin_id, config)
        
        assert result
        mock_instance.update_config.assert_called_once_with(config)
        
        # Check that config was stored
        stored_config = manager.get_plugin_config(sample_metadata.plugin_id)
        assert stored_config == config
    
    @pytest.mark.asyncio
    async def test_configure_plugin_not_found(self, manager):
        """Test configuring non-existent plugin"""
        await manager.initialize()
        
        manager.registry.get_plugin.return_value = None
        
        result = await manager.configure_plugin("non-existent", {})
        
        assert not result
    
    @pytest.mark.asyncio
    async def test_configure_plugin_validation(self, manager, sample_metadata):
        """Test plugin configuration validation"""
        await manager.initialize()
        
        # Add config schema to metadata
        sample_metadata.config_schema = {
            "required": ["required_field"],
            "properties": {
                "required_field": {"type": "string"}
            }
        }
        
        manager.registry.get_plugin.return_value = sample_metadata
        manager.registry.get_plugin_instance.return_value = None
        
        # Try with missing required field
        result = await manager.configure_plugin(sample_metadata.plugin_id, {"other_field": "value"})
        
        assert not result
    
    def test_list_plugins(self, manager):
        """Test listing plugins"""
        sample_plugins = [
            PluginMetadata(name="plugin1", version="1.0.0", description="Plugin 1", author="Author"),
            PluginMetadata(name="plugin2", version="1.0.0", description="Plugin 2", author="Author")
        ]
        
        manager.registry.list_plugins.return_value = sample_plugins
        
        result = manager.list_plugins()
        
        assert result == sample_plugins
        manager.registry.list_plugins.assert_called_once_with(category=None, status=None)
    
    def test_search_plugins(self, manager):
        """Test searching plugins"""
        sample_plugins = [
            PluginMetadata(name="search-plugin", version="1.0.0", description="Plugin", author="Author")
        ]
        
        manager.registry.search_plugins.return_value = sample_plugins
        
        result = manager.search_plugins("search")
        
        assert result == sample_plugins
        manager.registry.search_plugins.assert_called_once_with("search")
    
    @pytest.mark.asyncio
    async def test_get_plugin_health(self, manager, sample_metadata):
        """Test getting plugin health"""
        await manager.initialize()
        
        # Mock plugin instance
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.get_health = Mock(return_value={"status": "healthy"})
        manager.registry.get_plugin_instance.return_value = mock_instance
        
        # Mock sandbox
        mock_sandbox = Mock()
        mock_sandbox.get_resource_usage = Mock(return_value={"memory": 50})
        manager.sandbox_manager.get_sandbox.return_value = mock_sandbox
        
        health = await manager.get_plugin_health(sample_metadata.plugin_id)
        
        assert health["status"] == "healthy"
        assert health["resource_usage"]["memory"] == 50
    
    @pytest.mark.asyncio
    async def test_get_plugin_health_not_loaded(self, manager):
        """Test getting health for non-loaded plugin"""
        manager.registry.get_plugin_instance.return_value = None
        
        health = await manager.get_plugin_health("non-existent")
        
        assert health is None
    
    @pytest.mark.asyncio
    async def test_reload_plugin(self, manager, sample_metadata):
        """Test reloading plugin"""
        mock_instance = Mock(spec=BasePlugin)
        mock_instance.metadata = sample_metadata
        manager.loader.reload_plugin.return_value = mock_instance
        
        result = await manager.reload_plugin(sample_metadata.plugin_id)
        
        assert result
        manager.loader.reload_plugin.assert_called_once_with(sample_metadata.plugin_id)
    
    def test_get_manager_stats(self, manager):
        """Test getting manager statistics"""
        manager.registry.get_registry_stats.return_value = {"total_plugins": 5}
        manager.loader.list_loaded_plugins.return_value = [Mock(), Mock()]
        manager.configs = {"plugin1": Mock(), "plugin2": Mock()}
        manager.sandbox_manager.sandboxes = {"plugin1": Mock()}
        
        stats = manager.get_manager_stats()
        
        assert stats["registry"]["total_plugins"] == 5
        assert stats["loaded_plugins"] == 2
        assert stats["configurations"] == 2
        assert stats["sandboxes"] == 1
        assert "plugins_directory" in stats
        assert "config_directory" in stats


class TestGlobalPluginManager:
    """Test global plugin manager functions"""
    
    def test_get_global_manager(self):
        """Test getting global plugin manager"""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        
        # Should return same instance
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
    
    @pytest.mark.asyncio
    async def test_initialize_plugin_system(self):
        """Test initializing plugin system"""
        with patch.object(PluginManager, 'initialize', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True
            
            result = await initialize_plugin_system()
            
            assert result
            mock_init.assert_called_once()
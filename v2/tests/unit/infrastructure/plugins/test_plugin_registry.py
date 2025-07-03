#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Registry
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.plugins.registry import (
    PluginRegistry,
    PluginRegistryError,
    PluginConflictError,
    PluginNotFoundError,
    PluginCompatibilityError,
    get_plugin_registry,
    initialize_plugin_registry
)
from src.infrastructure.plugins.base import (
    PluginMetadata,
    PluginStatus,
    PluginCategory,
    PluginDependency,
    PluginCompatibility,
    BasePlugin
)


class TestPluginRegistry:
    """Test plugin registry functionality"""
    
    @pytest.fixture
    def temp_registry_file(self):
        """Create temporary registry file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def registry(self, temp_registry_file):
        """Create test registry"""
        return PluginRegistry(temp_registry_file)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample plugin metadata"""
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
            tags=["test", "utility"]
        )
    
    @pytest.fixture
    def sample_metadata_with_deps(self):
        """Create sample plugin metadata with dependencies"""
        dep = PluginDependency(name="dependency-plugin", version="1.0.0")
        compatibility = PluginCompatibility(
            dependencies=[dep],
            conflicts=["conflicting-plugin"]
        )
        
        return PluginMetadata(
            name="dependent-plugin",
            version="1.0.0",
            description="Plugin with dependencies",
            author="Test Author",
            compatibility=compatibility
        )
    
    @pytest.mark.asyncio
    async def test_registry_initialization(self, registry):
        """Test registry initialization"""
        assert await registry.initialize()
        assert registry._loaded
    
    @pytest.mark.asyncio
    async def test_register_plugin(self, registry, sample_metadata):
        """Test plugin registration"""
        await registry.initialize()
        
        # Register plugin
        assert await registry.register_plugin(sample_metadata)
        
        # Verify registration
        retrieved = registry.get_plugin(sample_metadata.plugin_id)
        assert retrieved is not None
        assert retrieved.name == sample_metadata.name
        assert retrieved.version == sample_metadata.version
    
    @pytest.mark.asyncio
    async def test_register_duplicate_plugin(self, registry, sample_metadata):
        """Test registering duplicate plugin"""
        await registry.initialize()
        
        # Register first time
        assert await registry.register_plugin(sample_metadata)
        
        # Register again with same name/version should fail
        duplicate = PluginMetadata(
            name=sample_metadata.name,
            version=sample_metadata.version,
            description="Duplicate plugin",
            author="Different Author"
        )
        
        # Should fail due to conflict
        assert not await registry.register_plugin(duplicate)
    
    @pytest.mark.asyncio
    async def test_register_plugin_force(self, registry, sample_metadata):
        """Test force registration"""
        await registry.initialize()
        
        # Register first time
        assert await registry.register_plugin(sample_metadata)
        
        # Force register duplicate
        duplicate = PluginMetadata(
            name=sample_metadata.name,
            version=sample_metadata.version,
            description="Duplicate plugin",
            author="Different Author"
        )
        
        assert await registry.register_plugin(duplicate, force=True)
    
    @pytest.mark.asyncio
    async def test_unregister_plugin(self, registry, sample_metadata):
        """Test plugin unregistration"""
        await registry.initialize()
        
        # Register plugin
        await registry.register_plugin(sample_metadata)
        
        # Unregister plugin
        assert await registry.unregister_plugin(sample_metadata.plugin_id)
        
        # Verify removal
        assert registry.get_plugin(sample_metadata.plugin_id) is None
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_plugin(self, registry):
        """Test unregistering non-existent plugin"""
        await registry.initialize()
        
        with pytest.raises(PluginNotFoundError):
            await registry.unregister_plugin("non-existent-id")
    
    def test_get_plugin_by_name(self, registry, sample_metadata):
        """Test getting plugin by name"""
        registry._plugins[sample_metadata.plugin_id] = sample_metadata
        registry._version_index[sample_metadata.name] = {
            sample_metadata.version: sample_metadata.plugin_id
        }
        
        # Get by name only (latest version)
        result = registry.get_plugin_by_name(sample_metadata.name)
        assert result == sample_metadata
        
        # Get by name and version
        result = registry.get_plugin_by_name(sample_metadata.name, sample_metadata.version)
        assert result == sample_metadata
        
        # Get non-existent
        result = registry.get_plugin_by_name("non-existent")
        assert result is None
    
    def test_plugin_instances(self, registry, sample_metadata):
        """Test plugin instance management"""
        mock_instance = Mock(spec=BasePlugin)
        
        # Set instance
        registry.set_plugin_instance(sample_metadata.plugin_id, mock_instance)
        
        # Get instance
        retrieved = registry.get_plugin_instance(sample_metadata.plugin_id)
        assert retrieved == mock_instance
        
        # Remove instance
        registry.remove_plugin_instance(sample_metadata.plugin_id)
        retrieved = registry.get_plugin_instance(sample_metadata.plugin_id)
        assert retrieved is None
    
    def test_list_plugins(self, registry):
        """Test listing plugins with filters"""
        # Create test plugins
        plugin1 = PluginMetadata(
            name="plugin1", version="1.0.0", description="Plugin 1",
            author="Author", category=PluginCategory.AI_PROVIDER,
            status=PluginStatus.ENABLED, tags=["ai"]
        )
        plugin2 = PluginMetadata(
            name="plugin2", version="1.0.0", description="Plugin 2", 
            author="Author", category=PluginCategory.UTILITY,
            status=PluginStatus.DISABLED, tags=["utility"]
        )
        plugin3 = PluginMetadata(
            name="plugin3", version="1.0.0", description="Plugin 3",
            author="Author", category=PluginCategory.AI_PROVIDER,
            status=PluginStatus.ENABLED, tags=["ai", "test"]
        )
        
        registry._plugins = {
            plugin1.plugin_id: plugin1,
            plugin2.plugin_id: plugin2,
            plugin3.plugin_id: plugin3
        }
        
        # List all
        all_plugins = registry.list_plugins()
        assert len(all_plugins) == 3
        
        # Filter by category
        ai_plugins = registry.list_plugins(category=PluginCategory.AI_PROVIDER)
        assert len(ai_plugins) == 2
        
        # Filter by status
        enabled_plugins = registry.list_plugins(status=PluginStatus.ENABLED)
        assert len(enabled_plugins) == 2
        
        # Filter by tags
        ai_tagged = registry.list_plugins(tags=["ai"])
        assert len(ai_tagged) == 2
    
    def test_search_plugins(self, registry):
        """Test plugin search"""
        # Create test plugins
        plugin1 = PluginMetadata(
            name="search-plugin", version="1.0.0", 
            description="A plugin for searching", author="Author",
            tags=["search", "utility"]
        )
        plugin2 = PluginMetadata(
            name="ai-plugin", version="1.0.0",
            description="AI-powered functionality", author="Author",
            tags=["ai", "machine-learning"]
        )
        plugin3 = PluginMetadata(
            name="data-processor", version="1.0.0",
            description="Process and search data efficiently", author="Author",
            tags=["data", "processing"]
        )
        
        registry._plugins = {
            plugin1.plugin_id: plugin1,
            plugin2.plugin_id: plugin2,
            plugin3.plugin_id: plugin3
        }
        
        # Search by name
        results = registry.search_plugins("search")
        assert len(results) == 2  # search-plugin and data-processor
        
        # Search by description
        results = registry.search_plugins("AI")
        assert len(results) == 1
        assert results[0].name == "ai-plugin"
        
        # Search by tag
        results = registry.search_plugins("utility")
        assert len(results) == 1
        assert results[0].name == "search-plugin"
    
    @pytest.mark.asyncio
    async def test_dependency_tracking(self, registry, sample_metadata, sample_metadata_with_deps):
        """Test dependency tracking"""
        await registry.initialize()
        
        # Register dependency first
        await registry.register_plugin(sample_metadata)
        
        # Update dependent metadata to reference the actual plugin
        sample_metadata_with_deps.compatibility.dependencies[0].name = sample_metadata.name
        
        # Register dependent plugin
        await registry.register_plugin(sample_metadata_with_deps)
        
        # Check dependencies
        deps = registry.get_dependencies(sample_metadata_with_deps.plugin_id)
        assert len(deps) == 1
        assert deps[0].plugin_id == sample_metadata.plugin_id
        
        # Check dependents
        dependents = registry.get_dependents(sample_metadata.plugin_id)
        assert len(dependents) == 1
        assert dependents[0].plugin_id == sample_metadata_with_deps.plugin_id
    
    @pytest.mark.asyncio
    async def test_resolve_dependencies(self, registry):
        """Test dependency resolution"""
        await registry.initialize()
        
        # Create dependency chain: A -> B -> C
        plugin_c = PluginMetadata(
            name="plugin-c", version="1.0.0", description="Plugin C", author="Author"
        )
        
        dep_c = PluginDependency(name="plugin-c", version="1.0.0")
        plugin_b = PluginMetadata(
            name="plugin-b", version="1.0.0", description="Plugin B", author="Author",
            compatibility=PluginCompatibility(dependencies=[dep_c])
        )
        
        dep_b = PluginDependency(name="plugin-b", version="1.0.0") 
        plugin_a = PluginMetadata(
            name="plugin-a", version="1.0.0", description="Plugin A", author="Author",
            compatibility=PluginCompatibility(dependencies=[dep_b])
        )
        
        # Register plugins
        await registry.register_plugin(plugin_c)
        await registry.register_plugin(plugin_b)
        await registry.register_plugin(plugin_a)
        
        # Resolve dependencies for A
        resolved = await registry.resolve_dependencies(plugin_a.plugin_id)
        
        # Should return in dependency order: C, B, A
        assert len(resolved) == 3
        resolved_names = [registry.get_plugin(pid).name for pid in resolved]
        assert resolved_names == ["plugin-c", "plugin-b", "plugin-a"]
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, registry):
        """Test circular dependency detection"""
        await registry.initialize()
        
        # Create circular dependency: A -> B -> A
        dep_b = PluginDependency(name="plugin-b", version="1.0.0")
        plugin_a = PluginMetadata(
            name="plugin-a", version="1.0.0", description="Plugin A", author="Author",
            compatibility=PluginCompatibility(dependencies=[dep_b])
        )
        
        dep_a = PluginDependency(name="plugin-a", version="1.0.0")
        plugin_b = PluginMetadata(
            name="plugin-b", version="1.0.0", description="Plugin B", author="Author",
            compatibility=PluginCompatibility(dependencies=[dep_a])
        )
        
        # Register plugins
        await registry.register_plugin(plugin_a)
        await registry.register_plugin(plugin_b)
        
        # Should detect circular dependency
        with pytest.raises(PluginConflictError, match="Circular dependency"):
            await registry.resolve_dependencies(plugin_a.plugin_id)
    
    def test_update_plugin_status(self, registry, sample_metadata):
        """Test updating plugin status"""
        registry._plugins[sample_metadata.plugin_id] = sample_metadata
        
        # Update status
        assert registry.update_plugin_status(sample_metadata.plugin_id, PluginStatus.ENABLED)
        
        # Verify update
        updated = registry.get_plugin(sample_metadata.plugin_id)
        assert updated.status == PluginStatus.ENABLED
        
        # Test non-existent plugin
        assert not registry.update_plugin_status("non-existent", PluginStatus.ENABLED)
    
    def test_registry_stats(self, registry):
        """Test registry statistics"""
        # Create test plugins
        plugin1 = PluginMetadata(
            name="plugin1", version="1.0.0", description="Plugin 1",
            author="Author", category=PluginCategory.AI_PROVIDER,
            status=PluginStatus.ENABLED
        )
        plugin2 = PluginMetadata(
            name="plugin2", version="1.0.0", description="Plugin 2",
            author="Author", category=PluginCategory.UTILITY,
            status=PluginStatus.DISABLED
        )
        
        registry._plugins = {
            plugin1.plugin_id: plugin1,
            plugin2.plugin_id: plugin2
        }
        registry._instances = {plugin1.plugin_id: Mock()}
        
        stats = registry.get_registry_stats()
        
        assert stats["total_plugins"] == 2
        assert stats["total_instances"] == 1
        assert stats["by_category"]["ai_provider"] == 1
        assert stats["by_category"]["utility"] == 1
        assert stats["by_status"]["enabled"] == 1
        assert stats["by_status"]["disabled"] == 1
    
    @pytest.mark.asyncio
    async def test_registry_persistence(self, registry, sample_metadata):
        """Test registry persistence"""
        await registry.initialize()
        
        # Register plugin
        await registry.register_plugin(sample_metadata)
        
        # Create new registry with same file
        new_registry = PluginRegistry(registry.registry_path)
        await new_registry.initialize()
        
        # Should load the plugin
        loaded_plugin = new_registry.get_plugin(sample_metadata.plugin_id)
        assert loaded_plugin is not None
        assert loaded_plugin.name == sample_metadata.name
    
    @pytest.mark.asyncio
    async def test_conflict_detection(self, registry, sample_metadata):
        """Test conflict detection"""
        await registry.initialize()
        
        # Register plugin
        await registry.register_plugin(sample_metadata)
        
        # Create conflicting plugin
        conflicting = PluginMetadata(
            name="conflicting-plugin", version="1.0.0",
            description="Conflicting plugin", author="Author",
            compatibility=PluginCompatibility(conflicts=[sample_metadata.name])
        )
        
        # Should detect conflict
        assert not await registry.register_plugin(conflicting)


class TestGlobalRegistry:
    """Test global registry functions"""
    
    def test_get_global_registry(self):
        """Test getting global registry"""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()
        
        # Should return same instance
        assert registry1 is registry2
    
    @pytest.mark.asyncio
    async def test_initialize_global_registry(self):
        """Test initializing global registry"""
        result = await initialize_plugin_registry()
        assert isinstance(result, bool)
#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Base Classes
"""

import pytest
from datetime import datetime, timezone
from dataclasses import asdict
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from src.infrastructure.plugins.base import (
    PluginMetadata,
    PluginStatus,
    PluginCategory,
    PluginDependency,
    PluginCompatibility,
    BasePlugin,
    AIProviderPlugin,
    ScraperPlugin,
    StoragePlugin,
    SearchToolPlugin
)


class TestPluginMetadata:
    """Test plugin metadata functionality"""
    
    def test_metadata_creation(self):
        """Test basic metadata creation"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
        assert metadata.category == PluginCategory.UTILITY
        assert metadata.status == PluginStatus.UNKNOWN
        assert isinstance(metadata.plugin_id, str)
        assert len(metadata.plugin_id) > 0
    
    def test_metadata_with_dependencies(self):
        """Test metadata with dependencies"""
        dep1 = PluginDependency(name="dep1")
        dep2 = PluginDependency(name="dep2", optional=True)
        
        compatibility = PluginCompatibility(
            dependencies=[dep1, dep2],
            conflicts=["conflicting-plugin"],
            python_version=">=3.8",
            theodore_version=">=2.0.0"
        )
        
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
            compatibility=compatibility
        )
        
        assert len(metadata.compatibility.dependencies) == 2
        assert metadata.compatibility.dependencies[0].name == "dep1"
        assert not metadata.compatibility.dependencies[0].optional
        assert metadata.compatibility.dependencies[1].optional
        assert "conflicting-plugin" in metadata.compatibility.conflicts
    
    def test_metadata_serialization(self):
        """Test metadata to/from dict conversion"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.AI_PROVIDER,
            tags=["ai", "test"]
        )
        
        # Convert to dict
        data = metadata.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "test_plugin"
        assert data["version"] == "1.0.0"
        assert data["category"] == "ai_provider"
        
        # Convert back from dict
        restored = PluginMetadata.from_dict(data)
        assert restored.name == metadata.name
        assert restored.version == metadata.version
        assert restored.category == metadata.category
        assert restored.plugin_id == metadata.plugin_id
    
    def test_metadata_validation(self):
        """Test metadata validation"""
        # Valid metadata should not raise
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        # Test required fields
        with pytest.raises(TypeError):
            PluginMetadata()  # Missing required fields


class TestPluginDependency:
    """Test plugin dependency functionality"""
    
    def test_dependency_creation(self):
        """Test dependency creation"""
        dep = PluginDependency(
            name="test_dep",
            optional=True
        )
        
        assert dep.name == "test_dep"
        assert dep.optional
    
    def test_dependency_serialization(self):
        """Test dependency serialization"""
        dep = PluginDependency(
            name="test_dep"
        )
        
        data = asdict(dep)
        assert data["name"] == "test_dep"
        assert not data["optional"]


class TestBasePlugin:
    """Test base plugin functionality"""
    
    class TestPlugin(BasePlugin):
        """Test plugin implementation"""
        
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
        
        def get_capabilities(self) -> List[str]:
            return ["test_capability"]
    
    def test_plugin_creation(self):
        """Test plugin creation"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        plugin = self.TestPlugin(metadata)
        
        assert plugin.metadata == metadata
        assert not plugin.is_initialized()
        assert not plugin.is_enabled()
    
    def test_plugin_config(self):
        """Test plugin configuration"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        config = {"setting1": "value1", "setting2": 42}
        plugin = self.TestPlugin(metadata, config)
        
        assert plugin.get_config("setting1") == "value1"
        assert plugin.get_config("setting2") == 42
        assert plugin.get_config("missing") is None
        assert plugin.get_config("missing", "default") == "default"
    
    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        plugin = self.TestPlugin(metadata)
        
        # Initialize
        assert await plugin.initialize()
        assert plugin.is_initialized()
        
        # Enable
        assert await plugin.enable()
        assert plugin.is_enabled()
        
        # Disable
        assert await plugin.disable()
        assert not plugin.is_enabled()
        
        # Cleanup
        assert await plugin.cleanup()
    
    def test_plugin_config_update(self):
        """Test plugin configuration update"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        plugin = self.TestPlugin(metadata)
        
        new_config = {"new_setting": "new_value"}
        assert plugin.update_config(new_config)
        assert plugin.get_config("new_setting") == "new_value"
    
    def test_plugin_health(self):
        """Test plugin health check"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        plugin = self.TestPlugin(metadata)
        health = plugin.get_health()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "initialized" in health
        assert "enabled" in health
        assert "last_error" in health


class TestSpecializedPlugins:
    """Test specialized plugin interfaces"""
    
    class TestAIProvider(AIProviderPlugin):
        """Test AI provider implementation"""
        
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
        
        def get_capabilities(self) -> List[str]:
            return ["text_generation", "embeddings"]
        
        async def analyze_text(self, text: str, **kwargs) -> Dict[str, Any]:
            return {"sentiment": "positive", "summary": "Test analysis"}
        
        async def generate_text(self, prompt: str, **kwargs) -> str:
            return f"Generated response for: {prompt}"
        
        async def generate_embeddings(self, texts: list, **kwargs) -> list:
            return [[0.1, 0.2, 0.3]] * len(texts)
        
        def get_model_info(self) -> dict:
            return {"model": "test-model", "provider": "test"}
    
    @pytest.mark.asyncio
    async def test_ai_provider_plugin(self):
        """Test AI provider plugin"""
        metadata = PluginMetadata(
            name="test_ai_provider",
            version="1.0.0",
            description="Test AI provider",
            author="Test Author",
            category=PluginCategory.AI_PROVIDER
        )
        
        plugin = self.TestAIProvider(metadata)
        
        # Test AI provider methods
        response = await plugin.generate_text("test prompt")
        assert "Generated response for: test prompt" == response
        
        embeddings = await plugin.generate_embeddings(["text1", "text2"])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3
        
        model_info = plugin.get_model_info()
        assert model_info["model"] == "test-model"


class TestPluginCategories:
    """Test plugin categories"""
    
    def test_all_categories_exist(self):
        """Test that all expected categories exist"""
        expected_categories = {
            "ai_provider", "scraper", "storage", "search_tool", 
            "export", "authentication", "integration", "utility", "extension"
        }
        
        actual_categories = {cat.value for cat in PluginCategory}
        assert expected_categories.issubset(actual_categories)
    
    def test_category_serialization(self):
        """Test category serialization"""
        category = PluginCategory.AI_PROVIDER
        assert category.value == "ai_provider"
        
        # Test that we can recreate from value
        restored = PluginCategory(category.value)
        assert restored == category


class TestPluginStatus:
    """Test plugin status"""
    
    def test_all_statuses_exist(self):
        """Test that all expected statuses exist"""
        expected_statuses = {
            "unknown", "discovered", "installed", "enabled", "disabled", 
            "error", "uninstalled"
        }
        
        actual_statuses = {status.value for status in PluginStatus}
        assert expected_statuses.issubset(actual_statuses)
    
    def test_status_progression(self):
        """Test typical status progression"""
        # This would be the typical flow
        statuses = [
            PluginStatus.UNKNOWN,
            PluginStatus.DISCOVERED,
            PluginStatus.INSTALLED,
            PluginStatus.ENABLED,
            PluginStatus.DISABLED,
            PluginStatus.UNINSTALLED
        ]
        
        # Just verify they all exist
        for status in statuses:
            assert isinstance(status, PluginStatus)
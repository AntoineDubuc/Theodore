#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Loader
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.infrastructure.plugins.loader import (
    PluginLoader,
    PluginLoadError,
    PluginValidationError,
    PluginSecurityError,
    PluginImportError,
    SecurityValidator,
    LoadedPlugin,
    get_plugin_loader
)
from src.infrastructure.plugins.base import (
    PluginMetadata,
    PluginStatus,
    PluginCategory,
    BasePlugin
)
from src.infrastructure.plugins.registry import PluginRegistry


class TestSecurityValidator:
    """Test security validation functionality"""
    
    def test_validate_safe_code(self):
        """Test validation of safe code"""
        safe_code = '''
"""A safe plugin"""
from typing import Optional
from src.infrastructure.plugins.base import BasePlugin, PluginMetadata

class SafePlugin(BasePlugin):
    async def initialize(self) -> bool:
        return True
        
    async def cleanup(self) -> bool:
        return True
'''
        
        validator = SecurityValidator()
        assert validator.validate_source_code(safe_code, "test.py")
        assert len(validator.get_violations()) == 0
    
    def test_validate_dangerous_imports(self):
        """Test detection of dangerous imports"""
        dangerous_code = '''
import subprocess
import os.system
from eval import something

class DangerousPlugin(BasePlugin):
    def run(self):
        subprocess.call(["rm", "-rf", "/"])
'''
        
        validator = SecurityValidator()
        assert not validator.validate_source_code(dangerous_code, "test.py")
        violations = validator.get_violations()
        assert len(violations) > 0
        assert any("subprocess" in v for v in violations)
    
    def test_validate_dangerous_function_calls(self):
        """Test detection of dangerous function calls"""
        dangerous_code = '''
class DangerousPlugin(BasePlugin):
    def run(self):
        eval("malicious_code()")
        exec("rm -rf /")
        compile("bad_code", "string", "exec")
'''
        
        validator = SecurityValidator()
        assert not validator.validate_source_code(dangerous_code, "test.py")
        violations = validator.get_violations()
        assert any("eval" in v for v in violations)
        assert any("exec" in v for v in violations)
        assert any("compile" in v for v in violations)
    
    def test_validate_syntax_error(self):
        """Test handling of syntax errors"""
        invalid_code = '''
class BadPlugin(BasePlugin:  # Missing closing parenthesis
    def run(self):
        return "syntax error"
'''
        
        validator = SecurityValidator()
        assert not validator.validate_source_code(invalid_code, "test.py")
        violations = validator.get_violations()
        assert any("Syntax error" in v for v in violations)


class TestPluginLoader:
    """Test plugin loader functionality"""
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock registry"""
        registry = Mock(spec=PluginRegistry)
        registry.get_plugin = Mock(return_value=None)
        registry.set_plugin_instance = Mock()
        registry.remove_plugin_instance = Mock()
        return registry
    
    @pytest.fixture
    def loader(self, mock_registry):
        """Create test loader"""
        return PluginLoader(registry=mock_registry)
    
    @pytest.fixture
    def sample_plugin_code(self):
        """Sample valid plugin code"""
        return '''
"""Test plugin module"""
from src.infrastructure.plugins.base import BasePlugin, PluginMetadata

PLUGIN_METADATA = {
    "name": "test-plugin",
    "version": "1.0.0", 
    "description": "Test plugin",
    "author": "Test Author"
}

class TestPlugin(BasePlugin):
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
'''
    
    @pytest.fixture
    def temp_plugin_file(self, sample_plugin_code):
        """Create temporary plugin file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_plugin_code)
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_plugin_success(self, loader, temp_plugin_file):
        """Test successful plugin loading"""
        # Mock security validation
        with patch.object(loader, '_validate_plugin_security', new_callable=AsyncMock):
            instance = await loader.load_plugin(temp_plugin_file)
            
            assert instance is not None
            assert hasattr(instance, 'metadata')
            assert instance.metadata.name == "test-plugin"
            
            # Check that plugin is tracked
            loaded = loader.get_loaded_plugin(instance.metadata.plugin_id)
            assert loaded is not None
            assert loaded.instance == instance
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_plugin(self, loader):
        """Test loading non-existent plugin"""
        nonexistent_path = Path("nonexistent_plugin.py")
        
        with pytest.raises(PluginLoadError, match="Plugin file not found"):
            await loader.load_plugin(nonexistent_path)
    
    @pytest.mark.asyncio
    async def test_load_plugin_security_violation(self, loader, temp_plugin_file):
        """Test loading plugin with security violations"""
        # Mock security validation to fail
        with patch.object(loader, '_validate_plugin_security', side_effect=PluginSecurityError("Security violation")):
            with pytest.raises(PluginLoadError, match="Security violation"):
                await loader.load_plugin(temp_plugin_file)
    
    @pytest.mark.asyncio
    async def test_load_plugin_with_metadata(self, loader, temp_plugin_file):
        """Test loading plugin with provided metadata"""
        metadata = PluginMetadata(
            name="custom-plugin",
            version="2.0.0",
            description="Custom plugin",
            author="Custom Author"
        )
        
        with patch.object(loader, '_validate_plugin_security', new_callable=AsyncMock):
            instance = await loader.load_plugin(temp_plugin_file, metadata)
            
            assert instance.metadata.name == "custom-plugin"
            assert instance.metadata.version == "2.0.0"
    
    @pytest.mark.asyncio
    async def test_load_plugin_force_reload(self, loader, temp_plugin_file):
        """Test force reloading plugin"""
        with patch.object(loader, '_validate_plugin_security', new_callable=AsyncMock):
            # Load first time
            instance1 = await loader.load_plugin(temp_plugin_file)
            
            # Load again with force reload
            instance2 = await loader.load_plugin(temp_plugin_file, force_reload=True)
            
            # Should get new instance
            assert instance1 is not instance2
            assert instance2.metadata.name == "test-plugin"
    
    @pytest.mark.asyncio
    async def test_load_plugin_by_id(self, loader, mock_registry):
        """Test loading plugin by ID"""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            module_path="/path/to/plugin.py"
        )
        
        mock_registry.get_plugin.return_value = metadata
        
        with patch.object(loader, 'load_plugin', new_callable=AsyncMock) as mock_load:
            mock_instance = Mock(spec=BasePlugin)
            mock_load.return_value = mock_instance
            
            result = await loader.load_plugin_by_id(metadata.plugin_id)
            
            assert result == mock_instance
            mock_load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_plugin_by_id_not_found(self, loader, mock_registry):
        """Test loading non-existent plugin by ID"""
        mock_registry.get_plugin.return_value = None
        
        with pytest.raises(PluginLoadError, match="Plugin not found in registry"):
            await loader.load_plugin_by_id("non-existent-id")
    
    @pytest.mark.asyncio
    async def test_unload_plugin(self, loader, temp_plugin_file):
        """Test unloading plugin"""
        with patch.object(loader, '_validate_plugin_security', new_callable=AsyncMock):
            # Load plugin first
            instance = await loader.load_plugin(temp_plugin_file)
            plugin_id = instance.metadata.plugin_id
            
            # Mock cleanup method
            instance.unload = AsyncMock(return_value=True)
            
            # Unload plugin
            assert await loader.unload_plugin(plugin_id)
            
            # Verify removal
            assert loader.get_loaded_plugin(plugin_id) is None
            instance.unload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unload_nonexistent_plugin(self, loader):
        """Test unloading non-existent plugin"""
        # Should succeed (already unloaded)
        assert await loader.unload_plugin("non-existent-id")
    
    @pytest.mark.asyncio
    async def test_reload_plugin(self, loader, temp_plugin_file):
        """Test reloading plugin"""
        with patch.object(loader, '_validate_plugin_security', new_callable=AsyncMock):
            # Load plugin first
            instance1 = await loader.load_plugin(temp_plugin_file)
            plugin_id = instance1.metadata.plugin_id
            
            # Mock cleanup method
            instance1.unload = AsyncMock(return_value=True)
            
            # Reload plugin
            instance2 = await loader.reload_plugin(plugin_id)
            
            # Should get new instance
            assert instance2 is not instance1
            assert instance2.metadata.name == instance1.metadata.name
    
    @pytest.mark.asyncio
    async def test_reload_nonexistent_plugin(self, loader):
        """Test reloading non-existent plugin"""
        with pytest.raises(PluginLoadError, match="Plugin not loaded"):
            await loader.reload_plugin("non-existent-id")
    
    def test_list_loaded_plugins(self, loader):
        """Test listing loaded plugins"""
        # Create mock loaded plugins
        metadata1 = PluginMetadata(name="plugin1", version="1.0.0", description="Plugin 1", author="Author")
        metadata2 = PluginMetadata(name="plugin2", version="1.0.0", description="Plugin 2", author="Author")
        
        loaded1 = LoadedPlugin(
            metadata=metadata1,
            instance=Mock(spec=BasePlugin),
            module=Mock(),
            load_time=0.1,
            file_hash="hash1",
            last_modified=123456789
        )
        loaded2 = LoadedPlugin(
            metadata=metadata2,
            instance=Mock(spec=BasePlugin),
            module=Mock(),
            load_time=0.2,
            file_hash="hash2", 
            last_modified=123456790
        )
        
        loader.loaded_plugins = {
            metadata1.plugin_id: loaded1,
            metadata2.plugin_id: loaded2
        }
        
        loaded_list = loader.list_loaded_plugins()
        assert len(loaded_list) == 2
        assert loaded1 in loaded_list
        assert loaded2 in loaded_list
    
    def test_hot_reload_watching(self, loader):
        """Test hot reload file watching"""
        # Start watching
        loader.start_hot_reload_watching()
        assert loader._watch_enabled
        assert loader._watch_thread is not None
        
        # Stop watching  
        loader.stop_hot_reload_watching()
        assert not loader._watch_enabled
    
    @pytest.mark.asyncio
    async def test_discover_plugin_metadata(self, loader, temp_plugin_file):
        """Test discovering plugin metadata from file"""
        metadata = await loader._discover_plugin_metadata(temp_plugin_file)
        
        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
    
    @pytest.mark.asyncio
    async def test_discover_plugin_metadata_no_metadata(self, loader):
        """Test discovering metadata from file without PLUGIN_METADATA"""
        code_without_metadata = '''
"""Plugin without metadata"""
from src.infrastructure.plugins.base import BasePlugin

class SimplePlugin(BasePlugin):
    pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_without_metadata)
            temp_path = Path(f.name)
        
        try:
            metadata = await loader._discover_plugin_metadata(temp_path)
            
            # Should create basic metadata from filename
            assert metadata.name == temp_path.stem
            assert metadata.version == "1.0.0"
            assert "Plugin loaded from" in metadata.description
        finally:
            temp_path.unlink()
    
    def test_calculate_file_hash(self, loader, temp_plugin_file):
        """Test file hash calculation"""
        hash1 = loader._calculate_file_hash(temp_plugin_file)
        hash2 = loader._calculate_file_hash(temp_plugin_file)
        
        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_find_loaded_plugin_by_path(self, loader, temp_plugin_file):
        """Test finding loaded plugin by file path"""
        # Create mock loaded plugin
        metadata = PluginMetadata(
            name="test-plugin", version="1.0.0", description="Test", author="Author",
            module_path=str(temp_plugin_file)
        )
        loaded = LoadedPlugin(
            metadata=metadata,
            instance=Mock(spec=BasePlugin),
            module=Mock(),
            load_time=0.1,
            file_hash="hash",
            last_modified=123456789
        )
        
        loader.loaded_plugins[metadata.plugin_id] = loaded
        
        # Find by path
        found = loader._find_loaded_plugin_by_path(temp_plugin_file)
        assert found == loaded
        
        # Non-existent path
        not_found = loader._find_loaded_plugin_by_path(Path("nonexistent.py"))
        assert not_found is None


class TestGlobalLoader:
    """Test global loader functions"""
    
    def test_get_global_loader(self):
        """Test getting global loader"""
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()
        
        # Should return same instance
        assert loader1 is loader2
    
    def test_loader_configuration(self):
        """Test loader configuration"""
        loader = get_plugin_loader()
        
        # Test default configuration
        assert loader.security_enabled
        assert loader.strict_mode
        assert loader.sandbox_enabled
#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Discovery
"""

import pytest
import tempfile
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from src.infrastructure.plugins.discovery import (
    PluginDiscovery,
    PluginSource,
    DiscoverySource,
    LocalDirectoryDiscovery,
    RegistryDiscovery,
    GitHubDiscovery,
    DiscoveryError,
    SourceNotAvailableError,
    search_plugins,
    discover_local_plugins
)
from src.infrastructure.plugins.base import PluginCategory


class TestPluginSource:
    """Test plugin source functionality"""
    
    def test_source_creation(self):
        """Test creating plugin source"""
        source = PluginSource(
            type="local",
            location="/path/to/plugin.py",
            name="test-plugin",
            description="Test plugin",
            version="1.0.0"
        )
        
        assert source.type == "local"
        assert source.location == "/path/to/plugin.py"
        assert source.name == "test-plugin"
        assert source.description == "Test plugin"
        assert source.version == "1.0.0"
    
    def test_source_serialization(self):
        """Test source serialization"""
        now = datetime.now(timezone.utc)
        source = PluginSource(
            type="registry",
            location="https://registry.com/plugin",
            name="registry-plugin",
            description="Registry plugin",
            version="2.0.0",
            checksum="abc123",
            size_bytes=1024,
            last_updated=now
        )
        
        # To dict
        data = source.to_dict()
        assert data["type"] == "registry"
        assert data["name"] == "registry-plugin"
        assert data["last_updated"] == now.isoformat()
        
        # From dict
        restored = PluginSource.from_dict(data)
        assert restored.type == source.type
        assert restored.name == source.name
        assert restored.last_updated == source.last_updated


class TestDiscoverySource:
    """Test discovery source configuration"""
    
    def test_source_creation(self):
        """Test creating discovery source"""
        source = DiscoverySource(
            name="local-plugins",
            type="local",
            location="/path/to/plugins",
            enabled=True,
            priority=10
        )
        
        assert source.name == "local-plugins"
        assert source.type == "local"
        assert source.location == "/path/to/plugins"
        assert source.enabled
        assert source.priority == 10
        assert source.refresh_interval_hours == 24
        assert not source.auth_required
        assert isinstance(source.auth_config, dict)
        assert isinstance(source.filters, dict)
    
    def test_source_with_auth(self):
        """Test discovery source with authentication"""
        source = DiscoverySource(
            name="private-registry",
            type="registry",
            location="https://private.registry.com",
            auth_required=True,
            auth_config={"token": "secret-token"}
        )
        
        assert source.auth_required
        assert source.auth_config["token"] == "secret-token"


class TestLocalDirectoryDiscovery:
    """Test local directory discovery"""
    
    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary directory with test plugins"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a valid plugin file
            plugin_file = temp_path / "test_plugin.py"
            plugin_content = '''
"""Test plugin"""
from src.infrastructure.plugins.base import BasePlugin

__version__ = "1.0.0"

class TestPlugin(BasePlugin):
    pass
'''
            plugin_file.write_text(plugin_content)
            
            # Create a non-plugin file
            other_file = temp_path / "other.py"
            other_file.write_text("# Not a plugin")
            
            yield temp_path
    
    @pytest.mark.asyncio
    async def test_discover_plugins(self, temp_plugin_dir):
        """Test discovering plugins in directory"""
        discovery = LocalDirectoryDiscovery([temp_plugin_dir])
        
        plugins = await discovery.discover_plugins()
        
        assert len(plugins) >= 1
        plugin_names = [p.name for p in plugins]
        assert "test_plugin" in plugin_names
        
        # Check plugin details
        test_plugin = next(p for p in plugins if p.name == "test_plugin")
        assert test_plugin.type == "local"
        assert test_plugin.version == "1.0.0"
        assert test_plugin.location == str(temp_plugin_dir / "test_plugin.py")
    
    @pytest.mark.asyncio
    async def test_discover_plugins_with_search(self, temp_plugin_dir):
        """Test discovering plugins with search query"""
        discovery = LocalDirectoryDiscovery([temp_plugin_dir])
        
        # Search for "test"
        plugins = await discovery.discover_plugins("test")
        plugin_names = [p.name for p in plugins]
        assert "test_plugin" in plugin_names
        
        # Search for something that doesn't match
        plugins = await discovery.discover_plugins("nonexistent")
        assert len(plugins) == 0
    
    @pytest.mark.asyncio
    async def test_discover_nonexistent_directory(self):
        """Test discovering in non-existent directory"""
        discovery = LocalDirectoryDiscovery([Path("/nonexistent/path")])
        
        plugins = await discovery.discover_plugins()
        
        # Should return empty list without error
        assert len(plugins) == 0
    
    def test_extract_description(self):
        """Test extracting description from code"""
        discovery = LocalDirectoryDiscovery([])
        
        # Test docstring extraction
        code_with_docstring = '''
"""This is a test plugin"""
class TestPlugin:
    pass
'''
        desc = discovery._extract_description(code_with_docstring)
        assert desc == "This is a test plugin"
        
        # Test comment extraction
        code_with_comment = '''
# Description: A simple plugin
class TestPlugin:
    pass
'''
        desc = discovery._extract_description(code_with_comment)
        assert desc == "A simple plugin"
        
        # Test no description
        code_without_desc = '''
class TestPlugin:
    pass
'''
        desc = discovery._extract_description(code_without_desc)
        assert desc is None
    
    def test_extract_version(self):
        """Test extracting version from code"""
        discovery = LocalDirectoryDiscovery([])
        
        # Test __version__
        code_with_version = '''
__version__ = "1.2.3"
class TestPlugin:
    pass
'''
        version = discovery._extract_version(code_with_version)
        assert version == "1.2.3"
        
        # Test VERSION
        code_with_VERSION = '''
VERSION = "2.0.0"
class TestPlugin:
    pass
'''
        version = discovery._extract_version(code_with_VERSION)
        assert version == "2.0.0"
        
        # Test no version
        code_without_version = '''
class TestPlugin:
    pass
'''
        version = discovery._extract_version(code_without_version)
        assert version is None


class TestRegistryDiscovery:
    """Test registry discovery"""
    
    @pytest.fixture
    def registry_discovery(self):
        """Create registry discovery"""
        return RegistryDiscovery(["https://registry.example.com"])
    
    @pytest.mark.asyncio
    async def test_discover_plugins_success(self, registry_discovery):
        """Test successful registry discovery"""
        mock_response_data = {
            "plugins": [
                {
                    "name": "registry-plugin-1",
                    "version": "1.0.0",
                    "description": "First registry plugin",
                    "checksum": "abc123",
                    "size_bytes": 1024,
                    "last_updated": "2023-01-01T00:00:00Z"
                },
                {
                    "name": "registry-plugin-2", 
                    "version": "2.0.0",
                    "description": "Second registry plugin",
                    "checksum": "def456",
                    "size_bytes": 2048,
                    "last_updated": "2023-01-02T00:00:00Z"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            plugins = await registry_discovery.discover_plugins()
            
            assert len(plugins) == 2
            assert plugins[0].name == "registry-plugin-1"
            assert plugins[0].type == "registry"
            assert plugins[1].name == "registry-plugin-2"
    
    @pytest.mark.asyncio
    async def test_discover_plugins_with_search(self, registry_discovery):
        """Test registry discovery with search query"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"plugins": []})
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await registry_discovery.discover_plugins("search-term")
            
            # Verify search parameter was sent
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            assert call_args[1]['params']['q'] == "search-term"
    
    @pytest.mark.asyncio
    async def test_discover_plugins_registry_error(self, registry_discovery):
        """Test registry discovery with server error"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 500
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            plugins = await registry_discovery.discover_plugins()
            
            # Should return empty list on error
            assert len(plugins) == 0
    
    @pytest.mark.asyncio
    async def test_discover_plugins_caching(self, registry_discovery):
        """Test registry discovery caching"""
        mock_response_data = {"plugins": []}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # First call
            await registry_discovery.discover_plugins("test")
            
            # Second call with same query should use cache
            await registry_discovery.discover_plugins("test")
            
            # Should only make one HTTP request due to caching
            assert mock_session.return_value.__aenter__.return_value.get.call_count == 1


class TestGitHubDiscovery:
    """Test GitHub discovery"""
    
    @pytest.fixture
    def github_discovery(self):
        """Create GitHub discovery"""
        return GitHubDiscovery()
    
    @pytest.fixture
    def github_discovery_with_token(self):
        """Create GitHub discovery with token"""
        return GitHubDiscovery(github_token="test-token")
    
    @pytest.mark.asyncio
    async def test_discover_plugins_success(self, github_discovery):
        """Test successful GitHub discovery"""
        mock_response_data = {
            "items": [
                {
                    "name": "theodore-awesome-plugin",
                    "full_name": "user/theodore-awesome-plugin",
                    "description": "An awesome Theodore plugin",
                    "clone_url": "https://github.com/user/theodore-awesome-plugin.git",
                    "stargazers_count": 42,
                    "language": "Python",
                    "license": {"name": "MIT"},
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            plugins = await github_discovery.discover_plugins()
            
            assert len(plugins) >= 1
            
            # Find our plugin
            plugin = next((p for p in plugins if p.name == "theodore-awesome-plugin"), None)
            assert plugin is not None
            assert plugin.type == "git"
            assert plugin.location == "https://github.com/user/theodore-awesome-plugin.git"
            assert plugin.metadata["stars"] == 42
            assert plugin.metadata["language"] == "Python"
    
    @pytest.mark.asyncio
    async def test_discover_plugins_with_token(self, github_discovery_with_token):
        """Test GitHub discovery with authentication token"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"items": []})
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await github_discovery_with_token.discover_plugins()
            
            # Verify authorization header was set
            call_args = mock_session.return_value.__aenter__.return_value.get.call_args
            headers = call_args[1]['headers']
            assert headers['Authorization'] == "token test-token"
    
    @pytest.mark.asyncio
    async def test_discover_plugins_with_search_query(self, github_discovery):
        """Test GitHub discovery with search query"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"items": []})
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await github_discovery.discover_plugins("custom-search")
            
            # Should search for custom term in addition to default terms
            assert mock_session.return_value.__aenter__.return_value.get.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_discover_plugins_api_error(self, github_discovery):
        """Test GitHub discovery with API error"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 403  # Rate limit or auth error
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            plugins = await github_discovery.discover_plugins()
            
            # Should handle error gracefully
            assert len(plugins) == 0


class TestPluginDiscovery:
    """Test main plugin discovery coordinator"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "sources": [
                    {
                        "name": "custom-local",
                        "type": "local",
                        "location": "/custom/plugins",
                        "priority": 5
                    }
                ]
            }
            json.dump(config_data, f)
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()
    
    def test_discovery_creation(self):
        """Test creating plugin discovery"""
        discovery = PluginDiscovery()
        
        assert len(discovery.sources) > 0
        assert any(s.name == "local_default" for s in discovery.sources)
        assert any(s.name == "github" for s in discovery.sources)
    
    def test_discovery_with_custom_config(self, temp_config_file):
        """Test discovery with custom configuration"""
        discovery = PluginDiscovery(config_file=temp_config_file)
        
        # Should have default sources plus custom ones
        source_names = [s.name for s in discovery.sources]
        assert "custom-local" in source_names
        assert "local_default" in source_names
    
    @pytest.mark.asyncio
    async def test_search_plugins(self):
        """Test searching plugins across sources"""
        with patch('src.infrastructure.plugins.discovery.LocalDirectoryDiscovery') as mock_local:
            with patch('src.infrastructure.plugins.discovery.GitHubDiscovery') as mock_github:
                # Mock discoverers
                mock_local_instance = Mock()
                mock_local_instance.discover_plugins = AsyncMock(return_value=[
                    PluginSource(type="local", location="/local/plugin.py", name="local-plugin")
                ])
                mock_local.return_value = mock_local_instance
                
                mock_github_instance = Mock()
                mock_github_instance.discover_plugins = AsyncMock(return_value=[
                    PluginSource(type="git", location="https://github.com/user/plugin.git", name="github-plugin")
                ])
                mock_github.return_value = mock_github_instance
                
                discovery = PluginDiscovery()
                plugins = await discovery.search_plugins("test")
                
                # Should find plugins from all sources
                assert len(plugins) >= 2
                plugin_names = [p.name for p in plugins]
                assert "local-plugin" in plugin_names
                assert "github-plugin" in plugin_names
    
    @pytest.mark.asyncio
    async def test_search_plugins_with_category_filter(self):
        """Test searching plugins with category filter"""
        with patch('src.infrastructure.plugins.discovery.LocalDirectoryDiscovery') as mock_local:
            # Mock plugin with metadata
            plugin_with_ai_category = PluginSource(
                type="local", 
                location="/plugin.py", 
                name="ai-plugin",
                metadata={"category": "ai_provider"}
            )
            plugin_with_util_category = PluginSource(
                type="local",
                location="/plugin2.py", 
                name="util-plugin",
                metadata={"category": "utility"}
            )
            
            mock_local_instance = Mock()
            mock_local_instance.discover_plugins = AsyncMock(return_value=[
                plugin_with_ai_category,
                plugin_with_util_category
            ])
            mock_local.return_value = mock_local_instance
            
            discovery = PluginDiscovery()
            plugins = await discovery.search_plugins(category=PluginCategory.AI_PROVIDER)
            
            # Should only return AI provider plugins
            assert len(plugins) == 1
            assert plugins[0].name == "ai-plugin"
    
    @pytest.mark.asyncio
    async def test_search_plugins_with_source_filter(self):
        """Test searching plugins with source type filter"""
        with patch('src.infrastructure.plugins.discovery.LocalDirectoryDiscovery') as mock_local:
            with patch('src.infrastructure.plugins.discovery.GitHubDiscovery') as mock_github:
                mock_local_instance = Mock()
                mock_local_instance.discover_plugins = AsyncMock(return_value=[
                    PluginSource(type="local", location="/plugin.py", name="local-plugin")
                ])
                mock_local.return_value = mock_local_instance
                
                mock_github_instance = Mock()
                mock_github_instance.discover_plugins = AsyncMock(return_value=[
                    PluginSource(type="git", location="https://github.com/user/plugin.git", name="github-plugin")
                ])
                mock_github.return_value = mock_github_instance
                
                discovery = PluginDiscovery()
                plugins = await discovery.search_plugins(source_types=["local"])
                
                # Should only search local sources
                assert len(plugins) == 1
                assert plugins[0].name == "local-plugin"
    
    def test_sort_plugins(self):
        """Test plugin sorting by relevance"""
        discovery = PluginDiscovery()
        
        plugins = [
            PluginSource(type="git", location="git://plugin", name="exact-match", description="Plugin"),
            PluginSource(type="local", location="/local", name="local-exact-match", description="Plugin"),
            PluginSource(type="registry", location="registry://plugin", name="partial-exact", description="Plugin"),
            PluginSource(type="local", location="/other", name="other", description="Has exact-match in description")
        ]
        
        sorted_plugins = discovery._sort_plugins(plugins, "exact-match")
        
        # Local exact match should be first (highest priority + exact name match)
        assert sorted_plugins[0].name == "local-exact-match"
        
        # Git exact match should be before registry partial match
        git_plugin = next(p for p in sorted_plugins if p.name == "exact-match")
        registry_plugin = next(p for p in sorted_plugins if p.name == "partial-exact")
        assert sorted_plugins.index(git_plugin) < sorted_plugins.index(registry_plugin)
    
    def test_add_remove_source(self):
        """Test adding and removing discovery sources"""
        discovery = PluginDiscovery()
        initial_count = len(discovery.sources)
        
        # Add source
        new_source = DiscoverySource(
            name="test-source",
            type="local",
            location="/test/path"
        )
        
        with patch.object(discovery, '_save_config'):
            with patch.object(discovery, '_initialize_discoverers'):
                discovery.add_source(new_source)
        
        assert len(discovery.sources) == initial_count + 1
        assert any(s.name == "test-source" for s in discovery.sources)
        
        # Remove source
        with patch.object(discovery, '_save_config'):
            with patch.object(discovery, '_initialize_discoverers'):
                discovery.remove_source("test-source")
        
        assert len(discovery.sources) == initial_count
        assert not any(s.name == "test-source" for s in discovery.sources)


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_search_plugins_function(self):
        """Test search_plugins convenience function"""
        with patch('src.infrastructure.plugins.discovery.PluginDiscovery') as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery.search_plugins = AsyncMock(return_value=[])
            mock_discovery_class.return_value = mock_discovery
            
            result = await search_plugins("test-query")
            
            assert result == []
            mock_discovery.search_plugins.assert_called_once_with("test-query", None, None)
    
    @pytest.mark.asyncio
    async def test_discover_local_plugins_function(self):
        """Test discover_local_plugins convenience function"""
        with patch('src.infrastructure.plugins.discovery.LocalDirectoryDiscovery') as mock_local_class:
            mock_discoverer = Mock()
            mock_discoverer.discover_plugins = AsyncMock(return_value=[])
            mock_local_class.return_value = mock_discoverer
            
            result = await discover_local_plugins(["/path1", "/path2"])
            
            assert result == []
            mock_discoverer.discover_plugins.assert_called_once()
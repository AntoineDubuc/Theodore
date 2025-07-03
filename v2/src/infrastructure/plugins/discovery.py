#!/usr/bin/env python3
"""
Theodore v2 Plugin Discovery

Plugin discovery system for finding plugins from local directories,
remote repositories, plugin marketplaces, and other sources.
"""

import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import hashlib
from urllib.parse import urlparse

from .base import PluginMetadata, PluginCategory


class DiscoveryError(Exception):
    """Base exception for plugin discovery errors"""
    pass


class SourceNotAvailableError(DiscoveryError):
    """Raised when a discovery source is not available"""
    pass


@dataclass
class PluginSource:
    """Represents a plugin source location"""
    type: str  # "local", "remote", "registry", "git"
    location: str  # Path, URL, or identifier
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'type': self.type,
            'location': self.location,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'metadata': self.metadata,
            'checksum': self.checksum,
            'size_bytes': self.size_bytes
        }
        
        if self.last_updated:
            result['last_updated'] = self.last_updated.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginSource':
        """Create from dictionary"""
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)


@dataclass
class DiscoverySource:
    """Configuration for a plugin discovery source"""
    name: str
    type: str  # "local", "registry", "github", "git"
    location: str
    enabled: bool = True
    priority: int = 100
    refresh_interval_hours: int = 24
    auth_required: bool = False
    auth_config: Optional[Dict[str, str]] = None
    filters: Optional[Dict[str, Any]] = None
    last_refresh: Optional[datetime] = None
    
    def __post_init__(self):
        if self.auth_config is None:
            self.auth_config = {}
        if self.filters is None:
            self.filters = {}


class LocalDirectoryDiscovery:
    """Discover plugins in local directories"""
    
    def __init__(self, base_paths: List[Path]):
        self.base_paths = [Path(p) for p in base_paths]
    
    async def discover_plugins(self, search_query: Optional[str] = None) -> List[PluginSource]:
        """Discover plugins in local directories"""
        plugins = []
        
        for base_path in self.base_paths:
            if not base_path.exists():
                continue
            
            # Search for Python files that might be plugins
            python_files = base_path.glob("**/*.py")
            
            for py_file in python_files:
                try:
                    plugin_source = await self._analyze_plugin_file(py_file)
                    if plugin_source:
                        # Apply search filter
                        if not search_query or self._matches_query(plugin_source, search_query):
                            plugins.append(plugin_source)
                            
                except Exception:
                    continue  # Skip invalid files
        
        return plugins
    
    async def _analyze_plugin_file(self, file_path: Path) -> Optional[PluginSource]:
        """Analyze a Python file to see if it's a plugin"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for plugin indicators
            if 'BasePlugin' not in content:
                return None
            
            # Try to extract basic metadata
            name = file_path.stem
            description = self._extract_description(content)
            version = self._extract_version(content)
            
            return PluginSource(
                type="local",
                location=str(file_path),
                name=name,
                description=description,
                version=version,
                size_bytes=file_path.stat().st_size,
                last_updated=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            )
            
        except Exception:
            return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from file content"""
        # Look for docstring
        docstring_match = re.search(r'"""([^"]+)"""', content)
        if docstring_match:
            return docstring_match.group(1).strip()
        
        # Look for description comment
        desc_match = re.search(r'#\s*Description:\s*(.+)', content)
        if desc_match:
            return desc_match.group(1).strip()
        
        return None
    
    def _extract_version(self, content: str) -> Optional[str]:
        """Extract version from file content"""
        # Look for __version__ or VERSION
        version_match = re.search(r'(?:__version__|VERSION)\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)
        
        return None
    
    def _matches_query(self, plugin_source: PluginSource, query: str) -> bool:
        """Check if plugin matches search query"""
        query_lower = query.lower()
        
        return (query_lower in plugin_source.name.lower() or
                (plugin_source.description and query_lower in plugin_source.description.lower()))


class RegistryDiscovery:
    """Discover plugins from online registries"""
    
    def __init__(self, registry_urls: List[str]):
        self.registry_urls = registry_urls
        self._cache: Dict[str, List[PluginSource]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
    
    async def discover_plugins(self, search_query: Optional[str] = None) -> List[PluginSource]:
        """Discover plugins from registries"""
        all_plugins = []
        
        for registry_url in self.registry_urls:
            try:
                plugins = await self._fetch_from_registry(registry_url, search_query)
                all_plugins.extend(plugins)
            except Exception as e:
                print(f"Failed to fetch from registry {registry_url}: {e}")
                continue
        
        return all_plugins
    
    async def _fetch_from_registry(self, registry_url: str, search_query: Optional[str]) -> List[PluginSource]:
        """Fetch plugins from a specific registry"""
        
        # Check cache
        cache_key = f"{registry_url}:{search_query or ''}"
        if cache_key in self._cache:
            expiry = self._cache_expiry.get(cache_key)
            if expiry and datetime.now(timezone.utc) < expiry:
                return self._cache[cache_key]
        
        plugins = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Build API URL
                api_url = f"{registry_url}/api/plugins"
                params = {}
                if search_query:
                    params['q'] = search_query
                
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for plugin_data in data.get('plugins', []):
                            plugin_source = self._parse_registry_plugin(plugin_data, registry_url)
                            if plugin_source:
                                plugins.append(plugin_source)
                    
                    # Cache results for 1 hour
                    self._cache[cache_key] = plugins
                    self._cache_expiry[cache_key] = datetime.now(timezone.utc).replace(hour=datetime.now().hour + 1)
        
        except Exception as e:
            raise SourceNotAvailableError(f"Registry {registry_url} not available: {e}")
        
        return plugins
    
    def _parse_registry_plugin(self, plugin_data: Dict[str, Any], registry_url: str) -> Optional[PluginSource]:
        """Parse plugin data from registry"""
        try:
            return PluginSource(
                type="registry",
                location=f"{registry_url}/plugins/{plugin_data['name']}/{plugin_data['version']}",
                name=plugin_data['name'],
                description=plugin_data.get('description'),
                version=plugin_data.get('version'),
                metadata=plugin_data,
                checksum=plugin_data.get('checksum'),
                size_bytes=plugin_data.get('size_bytes'),
                last_updated=datetime.fromisoformat(plugin_data['last_updated']) if plugin_data.get('last_updated') else None
            )
        except KeyError:
            return None


class GitHubDiscovery:
    """Discover plugins from GitHub repositories"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.api_base = "https://api.github.com"
    
    async def discover_plugins(self, search_query: Optional[str] = None) -> List[PluginSource]:
        """Discover plugins from GitHub"""
        plugins = []
        
        # Search for repositories with theodore plugin topics
        search_terms = ["theodore-plugin", "theodore-v2-plugin"]
        if search_query:
            search_terms.append(search_query)
        
        for term in search_terms:
            try:
                repos = await self._search_github_repos(term)
                for repo in repos:
                    plugin_source = await self._analyze_github_repo(repo)
                    if plugin_source:
                        plugins.append(plugin_source)
            except Exception as e:
                print(f"GitHub search failed for term {term}: {e}")
        
        return plugins
    
    async def _search_github_repos(self, query: str) -> List[Dict[str, Any]]:
        """Search GitHub repositories"""
        headers = {}
        if self.github_token:
            headers['Authorization'] = f"token {self.github_token}"
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base}/search/repositories"
            params = {
                'q': f"{query} language:python",
                'sort': 'updated',
                'per_page': 50
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                else:
                    raise SourceNotAvailableError(f"GitHub API error: {response.status}")
    
    async def _analyze_github_repo(self, repo_data: Dict[str, Any]) -> Optional[PluginSource]:
        """Analyze GitHub repository for plugin"""
        try:
            return PluginSource(
                type="git",
                location=repo_data['clone_url'],
                name=repo_data['name'],
                description=repo_data.get('description'),
                version=None,  # Would need to check releases
                metadata={
                    'github_repo': repo_data['full_name'],
                    'stars': repo_data['stargazers_count'],
                    'language': repo_data['language'],
                    'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None
                },
                last_updated=datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
            )
        except KeyError:
            return None


class PluginDiscovery:
    """Main plugin discovery coordinator"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path.home() / ".theodore" / "config" / "plugin_discovery.json"
        self.sources: List[DiscoverySource] = []
        self.discoverers: Dict[str, Any] = {}
        
        # Load default configuration
        self._load_default_sources()
        
        # Load custom configuration
        self._load_config()
        
        # Initialize discoverers
        self._initialize_discoverers()
    
    def _load_default_sources(self):
        """Load default discovery sources"""
        # Default local directories
        default_paths = [
            Path.home() / ".theodore" / "plugins",
            Path.cwd() / "plugins",
            Path("/usr/local/share/theodore/plugins"),
        ]
        
        self.sources.append(DiscoverySource(
            name="local_default",
            type="local",
            location=str(default_paths[0]),
            priority=10
        ))
        
        # Default plugin registry (hypothetical)
        self.sources.append(DiscoverySource(
            name="theodore_registry",
            type="registry",
            location="https://plugins.theodore.ai",
            priority=50,
            enabled=False  # Disabled by default until registry exists
        ))
        
        # GitHub discovery
        self.sources.append(DiscoverySource(
            name="github",
            type="github",
            location="github.com",
            priority=80,
            refresh_interval_hours=6
        ))
    
    def _load_config(self):
        """Load discovery configuration from file"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load custom sources
            for source_data in config_data.get('sources', []):
                source = DiscoverySource(**source_data)
                self.sources.append(source)
                
        except Exception as e:
            print(f"Failed to load discovery config: {e}")
    
    def _initialize_discoverers(self):
        """Initialize discovery implementations"""
        # Local directory discoverers
        local_sources = [s for s in self.sources if s.type == "local" and s.enabled]
        if local_sources:
            paths = [Path(s.location) for s in local_sources]
            self.discoverers['local'] = LocalDirectoryDiscovery(paths)
        
        # Registry discoverers
        registry_sources = [s for s in self.sources if s.type == "registry" and s.enabled]
        if registry_sources:
            urls = [s.location for s in registry_sources]
            self.discoverers['registry'] = RegistryDiscovery(urls)
        
        # GitHub discoverer
        github_sources = [s for s in self.sources if s.type == "github" and s.enabled]
        if github_sources:
            # Use token from first source that has it
            token = None
            for source in github_sources:
                if source.auth_config and 'token' in source.auth_config:
                    token = source.auth_config['token']
                    break
            
            self.discoverers['github'] = GitHubDiscovery(token)
    
    async def search_plugins(
        self, 
        query: Optional[str] = None,
        category: Optional[PluginCategory] = None,
        source_types: Optional[List[str]] = None
    ) -> List[PluginSource]:
        """Search for plugins across all discovery sources"""
        
        all_plugins = []
        
        # Determine which discoverers to use
        discoverers_to_use = self.discoverers.items()
        if source_types:
            discoverers_to_use = [(k, v) for k, v in self.discoverers.items() if k in source_types]
        
        # Search in parallel
        tasks = []
        for source_type, discoverer in discoverers_to_use:
            task = self._safe_discover(discoverer, query)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_plugins.extend(result)
                elif isinstance(result, Exception):
                    print(f"Discovery error: {result}")
        
        # Apply category filter
        if category:
            filtered_plugins = []
            for plugin in all_plugins:
                if plugin.metadata and plugin.metadata.get('category') == category.value:
                    filtered_plugins.append(plugin)
            all_plugins = filtered_plugins
        
        # Sort by priority and relevance
        return self._sort_plugins(all_plugins, query)
    
    async def _safe_discover(self, discoverer: Any, query: Optional[str]) -> List[PluginSource]:
        """Safely run discovery with error handling"""
        try:
            return await discoverer.discover_plugins(query)
        except Exception as e:
            print(f"Discovery failed: {e}")
            return []
    
    def _sort_plugins(self, plugins: List[PluginSource], query: Optional[str]) -> List[PluginSource]:
        """Sort plugins by relevance and source priority"""
        
        def score_plugin(plugin: PluginSource) -> int:
            score = 0
            
            # Base score by source type priority
            source_priority = {
                'local': 100,
                'registry': 80,
                'github': 60,
                'git': 40
            }
            score += source_priority.get(plugin.type, 0)
            
            # Boost score for query matches
            if query:
                query_lower = query.lower()
                if plugin.name.lower() == query_lower:
                    score += 50
                elif query_lower in plugin.name.lower():
                    score += 30
                elif plugin.description and query_lower in plugin.description.lower():
                    score += 20
            
            # Boost for metadata quality
            if plugin.metadata:
                score += 10
            if plugin.version:
                score += 5
            if plugin.checksum:
                score += 5
            
            return score
        
        return sorted(plugins, key=score_plugin, reverse=True)
    
    def add_source(self, source: DiscoverySource):
        """Add a new discovery source"""
        self.sources.append(source)
        self._save_config()
        self._initialize_discoverers()
    
    def remove_source(self, source_name: str):
        """Remove a discovery source"""
        self.sources = [s for s in self.sources if s.name != source_name]
        self._save_config()
        self._initialize_discoverers()
    
    def get_sources(self) -> List[DiscoverySource]:
        """Get all configured discovery sources"""
        return self.sources.copy()
    
    def _save_config(self):
        """Save discovery configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'version': '1.0.0',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'sources': [source.__dict__ for source in self.sources if source.name not in ['local_default', 'theodore_registry', 'github']]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save discovery config: {e}")


# Convenience functions

async def search_plugins(
    query: Optional[str] = None,
    category: Optional[PluginCategory] = None,
    source_types: Optional[List[str]] = None
) -> List[PluginSource]:
    """Search for plugins using default discovery"""
    discovery = PluginDiscovery()
    return await discovery.search_plugins(query, category, source_types)


async def discover_local_plugins(directories: List[Union[str, Path]]) -> List[PluginSource]:
    """Discover plugins in local directories"""
    paths = [Path(d) for d in directories]
    discoverer = LocalDirectoryDiscovery(paths)
    return await discoverer.discover_plugins()
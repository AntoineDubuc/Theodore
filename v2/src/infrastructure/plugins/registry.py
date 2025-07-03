#!/usr/bin/env python3
"""
Theodore v2 Plugin Registry

Manages plugin metadata, dependencies, versioning, and relationships.
Provides search, conflict detection, and compatibility checking.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime, timezone
from dataclasses import asdict
import threading
import hashlib

from .base import (
    BasePlugin, 
    PluginMetadata, 
    PluginStatus, 
    PluginCategory,
    PluginDependency,
    PluginCompatibility
)


class PluginRegistryError(Exception):
    """Base exception for plugin registry errors"""
    pass


class PluginConflictError(PluginRegistryError):
    """Raised when plugin conflicts are detected"""
    pass


class PluginNotFoundError(PluginRegistryError):
    """Raised when a requested plugin is not found"""
    pass


class PluginCompatibilityError(PluginRegistryError):
    """Raised when plugin compatibility issues are detected"""
    pass


class PluginRegistry:
    """Comprehensive plugin registry with advanced management capabilities"""
    
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path.home() / ".theodore" / "plugins" / "registry.json"
        self._plugins: Dict[str, PluginMetadata] = {}
        self._instances: Dict[str, BasePlugin] = {}
        self._dependencies: Dict[str, Set[str]] = {}  # plugin_id -> set of dependency plugin_ids
        self._dependents: Dict[str, Set[str]] = {}    # plugin_id -> set of dependent plugin_ids
        self._lock = threading.RLock()
        self._loaded = False
        
        # Plugin categories index for fast lookups
        self._category_index: Dict[PluginCategory, Set[str]] = {
            category: set() for category in PluginCategory
        }
        
        # Tag index for search
        self._tag_index: Dict[str, Set[str]] = {}
        
        # Version index for compatibility checking
        self._version_index: Dict[str, Dict[str, str]] = {}  # name -> version -> plugin_id
    
    async def initialize(self) -> bool:
        """Initialize the registry"""
        try:
            await self._load_registry()
            await self._rebuild_indexes()
            self._loaded = True
            return True
        except Exception as e:
            print(f"Failed to initialize plugin registry: {e}")
            return False
    
    async def register_plugin(self, metadata: PluginMetadata, force: bool = False) -> bool:
        """Register a plugin in the registry"""
        async with asyncio.Lock():
            try:
                # Validate plugin metadata
                self._validate_plugin_metadata(metadata)
                
                # Check for conflicts
                if not force:
                    conflicts = await self._check_conflicts(metadata)
                    if conflicts:
                        raise PluginConflictError(f"Plugin conflicts detected: {conflicts}")
                
                # Check compatibility
                compatibility_issues = await self._check_compatibility(metadata)
                if compatibility_issues:
                    raise PluginCompatibilityError(f"Compatibility issues: {compatibility_issues}")
                
                with self._lock:
                    # Update metadata timestamps
                    metadata.last_updated = datetime.now(timezone.utc)
                    if metadata.plugin_id not in self._plugins:
                        metadata.install_date = datetime.now(timezone.utc)
                    
                    # Register the plugin
                    self._plugins[metadata.plugin_id] = metadata
                    
                    # Update indexes
                    self._update_indexes(metadata)
                    
                    # Update dependency tracking
                    await self._update_dependencies(metadata)
                
                # Persist to disk
                await self._save_registry()
                
                return True
                
            except Exception as e:
                print(f"Failed to register plugin {metadata.name}: {e}")
                return False
    
    async def unregister_plugin(self, plugin_id: str, force: bool = False) -> bool:
        """Unregister a plugin from the registry"""
        async with asyncio.Lock():
            try:
                with self._lock:
                    if plugin_id not in self._plugins:
                        raise PluginNotFoundError(f"Plugin not found: {plugin_id}")
                    
                    metadata = self._plugins[plugin_id]
                    
                    # Check for dependents
                    if not force:
                        dependents = self._dependents.get(plugin_id, set())
                        if dependents:
                            dependent_names = [
                                self._plugins[dep_id].name 
                                for dep_id in dependents 
                                if dep_id in self._plugins
                            ]
                            raise PluginConflictError(
                                f"Cannot unregister plugin {metadata.name}: "
                                f"Required by {dependent_names}"
                            )
                    
                    # Remove from registry
                    del self._plugins[plugin_id]
                    
                    # Remove from instances if loaded
                    if plugin_id in self._instances:
                        del self._instances[plugin_id]
                    
                    # Update indexes
                    self._remove_from_indexes(metadata)
                    
                    # Update dependency tracking
                    self._remove_dependencies(plugin_id)
                
                # Persist to disk
                await self._save_registry()
                
                return True
                
            except Exception as e:
                print(f"Failed to unregister plugin {plugin_id}: {e}")
                return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by ID"""
        with self._lock:
            return self._plugins.get(plugin_id)
    
    def get_plugin_by_name(self, name: str, version: Optional[str] = None) -> Optional[PluginMetadata]:
        """Get plugin metadata by name and optional version"""
        with self._lock:
            if version:
                plugin_id = self._version_index.get(name, {}).get(version)
                if plugin_id:
                    return self._plugins.get(plugin_id)
            else:
                # Return latest version
                for metadata in self._plugins.values():
                    if metadata.name == name:
                        return metadata
        return None
    
    def get_plugin_instance(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get loaded plugin instance"""
        with self._lock:
            return self._instances.get(plugin_id)
    
    def set_plugin_instance(self, plugin_id: str, instance: BasePlugin):
        """Set loaded plugin instance"""
        with self._lock:
            self._instances[plugin_id] = instance
    
    def remove_plugin_instance(self, plugin_id: str):
        """Remove loaded plugin instance"""
        with self._lock:
            if plugin_id in self._instances:
                del self._instances[plugin_id]
    
    def list_plugins(
        self, 
        category: Optional[PluginCategory] = None,
        status: Optional[PluginStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[PluginMetadata]:
        """List plugins with optional filtering"""
        with self._lock:
            plugins = list(self._plugins.values())
            
            if category:
                plugins = [p for p in plugins if p.category == category]
            
            if status:
                plugins = [p for p in plugins if p.status == status]
            
            if tags:
                plugins = [
                    p for p in plugins 
                    if any(tag in p.tags for tag in tags)
                ]
            
            return sorted(plugins, key=lambda p: p.name)
    
    def search_plugins(self, query: str) -> List[PluginMetadata]:
        """Search plugins by name, description, or tags"""
        query_lower = query.lower()
        
        with self._lock:
            results = []
            for metadata in self._plugins.values():
                # Search in name, description, and tags
                if (query_lower in metadata.name.lower() or
                    query_lower in metadata.description.lower() or
                    any(query_lower in tag.lower() for tag in metadata.tags)):
                    results.append(metadata)
            
            return sorted(results, key=lambda p: p.name)
    
    def get_dependencies(self, plugin_id: str) -> List[PluginMetadata]:
        """Get plugin dependencies"""
        with self._lock:
            dep_ids = self._dependencies.get(plugin_id, set())
            return [
                self._plugins[dep_id] 
                for dep_id in dep_ids 
                if dep_id in self._plugins
            ]
    
    def get_dependents(self, plugin_id: str) -> List[PluginMetadata]:
        """Get plugins that depend on this plugin"""
        with self._lock:
            dependent_ids = self._dependents.get(plugin_id, set())
            return [
                self._plugins[dep_id] 
                for dep_id in dependent_ids 
                if dep_id in self._plugins
            ]
    
    async def resolve_dependencies(self, plugin_id: str) -> List[str]:
        """Resolve plugin dependencies in installation order"""
        with self._lock:
            resolved = []
            visited = set()
            temp_visited = set()
            
            def visit(pid: str):
                if pid in temp_visited:
                    raise PluginConflictError(f"Circular dependency detected involving {pid}")
                if pid in visited:
                    return
                
                temp_visited.add(pid)
                
                # Visit dependencies first
                for dep_id in self._dependencies.get(pid, set()):
                    visit(dep_id)
                
                temp_visited.remove(pid)
                visited.add(pid)
                resolved.append(pid)
            
            visit(plugin_id)
            return resolved
    
    async def get_installation_order(self, plugin_ids: List[str]) -> List[str]:
        """Get installation order for multiple plugins"""
        all_resolved = []
        for plugin_id in plugin_ids:
            resolved = await self.resolve_dependencies(plugin_id)
            for pid in resolved:
                if pid not in all_resolved:
                    all_resolved.append(pid)
        return all_resolved
    
    def update_plugin_status(self, plugin_id: str, status: PluginStatus) -> bool:
        """Update plugin status"""
        with self._lock:
            if plugin_id in self._plugins:
                self._plugins[plugin_id].status = status
                self._plugins[plugin_id].last_updated = datetime.now(timezone.utc)
                return True
        return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._lock:
            stats = {
                'total_plugins': len(self._plugins),
                'by_category': {},
                'by_status': {},
                'total_instances': len(self._instances),
                'registry_path': str(self.registry_path)
            }
            
            for metadata in self._plugins.values():
                # Count by category
                category = metadata.category.value
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                # Count by status
                status = metadata.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            return stats
    
    # Private methods
    
    def _validate_plugin_metadata(self, metadata: PluginMetadata):
        """Validate plugin metadata"""
        if not metadata.name:
            raise ValueError("Plugin name is required")
        if not metadata.version:
            raise ValueError("Plugin version is required")
        if not metadata.author:
            raise ValueError("Plugin author is required")
        if not metadata.description:
            raise ValueError("Plugin description is required")
    
    async def _check_conflicts(self, metadata: PluginMetadata) -> List[str]:
        """Check for plugin conflicts"""
        conflicts = []
        
        with self._lock:
            # Check for same name and version
            existing = self.get_plugin_by_name(metadata.name, metadata.version)
            if existing and existing.plugin_id != metadata.plugin_id:
                conflicts.append(f"Plugin {metadata.name} v{metadata.version} already exists")
            
            # Check explicit conflicts
            for conflict_name in metadata.compatibility.conflicts:
                conflicting = self.get_plugin_by_name(conflict_name)
                if conflicting and conflicting.status in [PluginStatus.INSTALLED, PluginStatus.ENABLED]:
                    conflicts.append(f"Conflicts with installed plugin: {conflict_name}")
        
        return conflicts
    
    async def _check_compatibility(self, metadata: PluginMetadata) -> List[str]:
        """Check plugin compatibility"""
        issues = []
        
        # Check Python version compatibility
        # (This would integrate with actual version checking)
        
        # Check Theodore version compatibility
        # (This would check against current Theodore version)
        
        # Check dependency availability
        for dep in metadata.compatibility.dependencies:
            if not dep.optional:
                dep_plugin = self.get_plugin_by_name(dep.name)
                if not dep_plugin:
                    issues.append(f"Required dependency not available: {dep.name}")
                elif dep_plugin.status not in [PluginStatus.INSTALLED, PluginStatus.ENABLED]:
                    issues.append(f"Required dependency not installed: {dep.name}")
        
        return issues
    
    def _update_indexes(self, metadata: PluginMetadata):
        """Update search and category indexes"""
        plugin_id = metadata.plugin_id
        
        # Update category index
        self._category_index[metadata.category].add(plugin_id)
        
        # Update tag index
        for tag in metadata.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(plugin_id)
        
        # Update version index
        if metadata.name not in self._version_index:
            self._version_index[metadata.name] = {}
        self._version_index[metadata.name][metadata.version] = plugin_id
    
    def _remove_from_indexes(self, metadata: PluginMetadata):
        """Remove plugin from indexes"""
        plugin_id = metadata.plugin_id
        
        # Remove from category index
        self._category_index[metadata.category].discard(plugin_id)
        
        # Remove from tag index
        for tag in metadata.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(plugin_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
        
        # Remove from version index
        if metadata.name in self._version_index:
            if metadata.version in self._version_index[metadata.name]:
                del self._version_index[metadata.name][metadata.version]
            if not self._version_index[metadata.name]:
                del self._version_index[metadata.name]
    
    async def _update_dependencies(self, metadata: PluginMetadata):
        """Update dependency tracking"""
        plugin_id = metadata.plugin_id
        
        # Clear existing dependencies
        if plugin_id in self._dependencies:
            for old_dep_id in self._dependencies[plugin_id]:
                if old_dep_id in self._dependents:
                    self._dependents[old_dep_id].discard(plugin_id)
        
        # Add new dependencies
        dep_ids = set()
        for dep in metadata.compatibility.dependencies:
            dep_plugin = self.get_plugin_by_name(dep.name)
            if dep_plugin:
                dep_id = dep_plugin.plugin_id
                dep_ids.add(dep_id)
                
                # Update reverse dependency tracking
                if dep_id not in self._dependents:
                    self._dependents[dep_id] = set()
                self._dependents[dep_id].add(plugin_id)
        
        self._dependencies[plugin_id] = dep_ids
    
    def _remove_dependencies(self, plugin_id: str):
        """Remove dependency tracking for a plugin"""
        # Remove from dependencies
        if plugin_id in self._dependencies:
            for dep_id in self._dependencies[plugin_id]:
                if dep_id in self._dependents:
                    self._dependents[dep_id].discard(plugin_id)
            del self._dependencies[plugin_id]
        
        # Remove from dependents
        if plugin_id in self._dependents:
            del self._dependents[plugin_id]
    
    async def _rebuild_indexes(self):
        """Rebuild all indexes from plugin data"""
        with self._lock:
            # Clear indexes
            self._category_index = {category: set() for category in PluginCategory}
            self._tag_index = {}
            self._version_index = {}
            self._dependencies = {}
            self._dependents = {}
            
            # Rebuild indexes
            for metadata in self._plugins.values():
                self._update_indexes(metadata)
                await self._update_dependencies(metadata)
    
    async def _load_registry(self):
        """Load registry from disk"""
        if not self.registry_path.exists():
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            with self._lock:
                self._plugins = {}
                for plugin_data in data.get('plugins', []):
                    metadata = PluginMetadata.from_dict(plugin_data)
                    self._plugins[metadata.plugin_id] = metadata
                    
        except Exception as e:
            print(f"Failed to load plugin registry: {e}")
    
    async def _save_registry(self):
        """Save registry to disk"""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                data = {
                    'version': '1.0.0',
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'plugins': [metadata.to_dict() for metadata in self._plugins.values()]
                }
            
            # Write to temporary file first, then rename for atomicity
            temp_path = self.registry_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_path.rename(self.registry_path)
            
        except Exception as e:
            print(f"Failed to save plugin registry: {e}")


# Global registry instance
_global_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get global plugin registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


async def initialize_plugin_registry() -> bool:
    """Initialize global plugin registry"""
    registry = get_plugin_registry()
    return await registry.initialize()
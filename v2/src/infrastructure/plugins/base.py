#!/usr/bin/env python3
"""
Theodore v2 Plugin Base Classes and Metadata

Defines the foundation for all Theodore plugins with comprehensive metadata,
lifecycle management, and security features.
"""

import uuid
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Set, Type
from dataclasses import dataclass, field
from pathlib import Path
import inspect


class PluginStatus(str, Enum):
    """Plugin lifecycle status"""
    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class PluginCategory(str, Enum):
    """Plugin categories for organization and discovery"""
    AI_PROVIDER = "ai_provider"
    SCRAPER = "scraper"
    STORAGE = "storage"
    SEARCH_TOOL = "search_tool"
    EXPORT = "export"
    AUTHENTICATION = "authentication"
    INTEGRATION = "integration"
    UTILITY = "utility"
    EXTENSION = "extension"


@dataclass
class PluginDependency:
    """Plugin dependency specification"""
    name: str
    version_requirement: str = "*"
    optional: bool = False
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate dependency specification"""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Dependency name must be a non-empty string")
        
        # Validate version requirement format (semver-like)
        if not re.match(r'^[\d\.\*\>\<\=\!\~\^]*$', self.version_requirement):
            raise ValueError(f"Invalid version requirement: {self.version_requirement}")


@dataclass
class PluginCompatibility:
    """Plugin compatibility requirements"""
    theodore_version: str = "*"
    python_version: str = ">=3.8"
    platform: Optional[str] = None
    dependencies: List[PluginDependency] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate compatibility specification"""
        if not self.theodore_version:
            raise ValueError("Theodore version requirement is required")
        
        if not self.python_version:
            raise ValueError("Python version requirement is required")


@dataclass 
class PluginMetadata:
    """Comprehensive plugin metadata"""
    # Core identification
    name: str
    version: str
    description: str
    author: str
    
    # Plugin classification
    category: PluginCategory
    tags: List[str] = field(default_factory=list)
    
    # Technical details
    entry_point: str = ""
    module_path: Optional[str] = None
    
    # Compatibility and dependencies
    compatibility: PluginCompatibility = field(default_factory=PluginCompatibility)
    
    # Documentation and support
    homepage: Optional[str] = None
    documentation: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    
    # Runtime information
    plugin_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PluginStatus = PluginStatus.UNKNOWN
    install_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Configuration and features
    config_schema: Optional[Dict[str, Any]] = None
    features: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    
    # Runtime metrics
    load_time: Optional[float] = None
    memory_usage: Optional[int] = None
    error_count: int = 0
    
    def __post_init__(self):
        """Validate metadata"""
        self._validate_required_fields()
        self._validate_name()
        self._validate_version()
        self._validate_entry_point()
        
        # Set timestamps
        if not self.install_date:
            self.install_date = datetime.now(timezone.utc)
        if not self.last_updated:
            self.last_updated = datetime.now(timezone.utc)
    
    def _validate_required_fields(self):
        """Validate required metadata fields"""
        required_fields = ['name', 'version', 'description', 'author']
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not isinstance(value, str) or not value.strip():
                raise ValueError(f"Plugin {field_name} is required and must be a non-empty string")
    
    def _validate_name(self):
        """Validate plugin name format"""
        # Plugin names must be valid Python identifiers with optional namespacing
        name_pattern = r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$'
        if not re.match(name_pattern, self.name):
            raise ValueError(f"Invalid plugin name format: {self.name}")
    
    def _validate_version(self):
        """Validate version format (semantic versioning)"""
        version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9\-\.]+)?(\+[a-zA-Z0-9\-\.]+)?$'
        if not re.match(version_pattern, self.version):
            raise ValueError(f"Invalid version format: {self.version} (must be semantic version)")
    
    def _validate_entry_point(self):
        """Validate entry point format"""
        if self.entry_point and ':' in self.entry_point:
            module, attr = self.entry_point.split(':', 1)
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\.]*$', module):
                raise ValueError(f"Invalid module name in entry point: {module}")
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', attr):
                raise ValueError(f"Invalid attribute name in entry point: {attr}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Enum):
                result[field_name] = field_value.value
            elif isinstance(field_value, datetime):
                result[field_name] = field_value.isoformat()
            elif isinstance(field_value, PluginCompatibility):
                result[field_name] = {
                    'theodore_version': field_value.theodore_version,
                    'python_version': field_value.python_version,
                    'platform': field_value.platform,
                    'dependencies': [
                        {
                            'name': dep.name,
                            'version_requirement': dep.version_requirement,
                            'optional': dep.optional,
                            'description': dep.description
                        }
                        for dep in field_value.dependencies
                    ],
                    'conflicts': field_value.conflicts
                }
            else:
                result[field_name] = field_value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata from dictionary"""
        # Handle enum conversion
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = PluginCategory(data['category'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = PluginStatus(data['status'])
        
        # Handle datetime conversion
        for date_field in ['install_date', 'last_updated']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # Handle compatibility conversion
        if 'compatibility' in data and isinstance(data['compatibility'], dict):
            compat_data = data['compatibility']
            dependencies = []
            if 'dependencies' in compat_data:
                dependencies = [
                    PluginDependency(**dep_data)
                    for dep_data in compat_data['dependencies']
                ]
            
            data['compatibility'] = PluginCompatibility(
                theodore_version=compat_data.get('theodore_version', '*'),
                python_version=compat_data.get('python_version', '>=3.8'),
                platform=compat_data.get('platform'),
                dependencies=dependencies,
                conflicts=compat_data.get('conflicts', [])
            )
        
        return cls(**data)


class BasePlugin(ABC):
    """Base class for all Theodore plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        self.metadata = metadata
        self.config = config or {}
        self._initialized = False
        self._enabled = False
        self._dependencies_satisfied = False
        
        # Plugin lifecycle hooks
        self._hooks = {
            'on_load': [],
            'on_unload': [],
            'on_enable': [],
            'on_disable': [],
            'on_config_change': []
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities. Must be implemented by subclasses."""
        pass
    
    async def enable(self) -> bool:
        """Enable the plugin"""
        if not self._initialized:
            if not await self.initialize():
                return False
            self._initialized = True
        
        if not self._dependencies_satisfied:
            if not await self._check_dependencies():
                return False
            self._dependencies_satisfied = True
        
        # Run enable hooks
        for hook in self._hooks['on_enable']:
            try:
                await hook()
            except Exception as e:
                print(f"Error in enable hook: {e}")
                return False
        
        self._enabled = True
        self.metadata.status = PluginStatus.ENABLED
        return True
    
    async def disable(self) -> bool:
        """Disable the plugin"""
        if not self._enabled:
            return True
        
        # Run disable hooks
        for hook in self._hooks['on_disable']:
            try:
                await hook()
            except Exception as e:
                print(f"Error in disable hook: {e}")
                return False
        
        self._enabled = False
        self.metadata.status = PluginStatus.DISABLED
        return True
    
    async def unload(self) -> bool:
        """Unload the plugin"""
        if self._enabled:
            await self.disable()
        
        # Run unload hooks
        for hook in self._hooks['on_unload']:
            try:
                await hook()
            except Exception as e:
                print(f"Error in unload hook: {e}")
                return False
        
        if self._initialized:
            await self.cleanup()
            self._initialized = False
        
        return True
    
    async def reload(self) -> bool:
        """Reload the plugin"""
        was_enabled = self._enabled
        
        if not await self.unload():
            return False
        
        if was_enabled:
            return await self.enable()
        
        return True
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update plugin configuration"""
        old_config = self.config.copy()
        try:
            # Validate configuration if schema is available
            if self.metadata.config_schema:
                self._validate_config(new_config)
            
            self.config.update(new_config)
            
            # Run config change hooks
            for hook in self._hooks['on_config_change']:
                try:
                    hook(old_config, new_config)
                except Exception as e:
                    # Rollback on error
                    self.config = old_config
                    print(f"Error in config change hook: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.config = old_config
            print(f"Error updating config: {e}")
            return False
    
    def add_hook(self, event: str, callback: callable):
        """Add lifecycle hook"""
        if event in self._hooks:
            self._hooks[event].append(callback)
        else:
            raise ValueError(f"Unknown hook event: {event}")
    
    def remove_hook(self, event: str, callback: callable):
        """Remove lifecycle hook"""
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
    
    async def _check_dependencies(self) -> bool:
        """Check if plugin dependencies are satisfied"""
        # This would integrate with the plugin registry to check dependencies
        # For now, return True (implementation would be in the manager)
        return True
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration against schema"""
        # Basic validation - could integrate with jsonschema for full validation
        if not self.metadata.config_schema:
            return
        
        required = self.metadata.config_schema.get('required', [])
        for field in required:
            if field not in config:
                raise ValueError(f"Required configuration field missing: {field}")
    
    def get_health(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            'plugin_id': self.metadata.plugin_id,
            'name': self.metadata.name,
            'version': self.metadata.version,
            'status': self.metadata.status.value,
            'initialized': self._initialized,
            'enabled': self._enabled,
            'dependencies_satisfied': self._dependencies_satisfied,
            'error_count': self.metadata.error_count,
            'memory_usage': self.metadata.memory_usage,
            'load_time': self.metadata.load_time
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.metadata.name}', version='{self.metadata.version}', status='{self.metadata.status.value}')>"


class PluginInterface(ABC):
    """Interface for specific plugin types"""
    
    @abstractmethod
    def get_interface_version(self) -> str:
        """Get the interface version this plugin implements"""
        pass
    
    @abstractmethod
    def is_compatible_with(self, interface_version: str) -> bool:
        """Check if plugin is compatible with interface version"""
        pass


# Specific plugin base classes for different types
class AIProviderPlugin(BasePlugin, PluginInterface):
    """Base class for AI provider plugins"""
    
    def get_interface_version(self) -> str:
        return "1.0.0"
    
    def is_compatible_with(self, interface_version: str) -> bool:
        # Simple version check - could be more sophisticated
        return interface_version.startswith("1.")
    
    @abstractmethod
    async def analyze_text(self, text: str, prompt: str) -> str:
        """Analyze text with AI provider"""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass


class ScraperPlugin(BasePlugin, PluginInterface):
    """Base class for scraper plugins"""
    
    def get_interface_version(self) -> str:
        return "1.0.0"
    
    def is_compatible_with(self, interface_version: str) -> bool:
        return interface_version.startswith("1.")
    
    @abstractmethod
    async def scrape_website(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape website content"""
        pass


class StoragePlugin(BasePlugin, PluginInterface):
    """Base class for storage plugins"""
    
    def get_interface_version(self) -> str:
        return "1.0.0"
    
    def is_compatible_with(self, interface_version: str) -> bool:
        return interface_version.startswith("1.")
    
    @abstractmethod
    async def store_vector(self, vector: List[float], metadata: Dict[str, Any]) -> str:
        """Store vector with metadata"""
        pass
    
    @abstractmethod
    async def search_vectors(self, query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass


class SearchToolPlugin(BasePlugin, PluginInterface):
    """Base class for search tool plugins"""
    
    def get_interface_version(self) -> str:
        return "1.0.0"
    
    def is_compatible_with(self, interface_version: str) -> bool:
        return interface_version.startswith("1.")
    
    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform search with filters"""
        pass
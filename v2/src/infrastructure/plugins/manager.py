#!/usr/bin/env python3
"""
Theodore v2 Plugin Manager

Orchestrates the complete plugin lifecycle including installation, 
configuration, dependency resolution, and lifecycle management.
"""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import threading
import zipfile
import tarfile

from .base import (
    BasePlugin, 
    PluginMetadata, 
    PluginStatus, 
    PluginCategory,
    PluginDependency,
    PluginCompatibility
)
from .registry import PluginRegistry, get_plugin_registry
from .loader import PluginLoader, get_plugin_loader
from .sandbox import (
    PluginSandbox, 
    SandboxManager, 
    get_sandbox_manager,
    ResourceLimits,
    PluginPermissions
)
from .discovery import PluginDiscovery, PluginSource


class PluginLifecycleError(Exception):
    """Base exception for plugin lifecycle errors"""
    pass


class PluginInstallError(PluginLifecycleError):
    """Raised when plugin installation fails"""
    pass


class PluginConfigurationError(PluginLifecycleError):
    """Raised when plugin configuration is invalid"""
    pass


class PluginDependencyError(PluginLifecycleError):
    """Raised when plugin dependencies cannot be resolved"""
    pass


@dataclass
class InstallationOptions:
    """Options for plugin installation"""
    force_reinstall: bool = False
    skip_dependencies: bool = False
    install_dependencies: bool = True
    verify_signatures: bool = True
    sandbox_enabled: bool = True
    custom_install_path: Optional[Path] = None
    
    # Resource limits for installed plugins
    memory_limit_mb: int = 128
    cpu_limit_seconds: int = 30
    execution_timeout_seconds: int = 60
    
    # Permissions for installed plugins
    network_access: bool = False
    file_read_paths: List[str] = None
    file_write_paths: List[str] = None
    
    def __post_init__(self):
        if self.file_read_paths is None:
            self.file_read_paths = []
        if self.file_write_paths is None:
            self.file_write_paths = []


@dataclass
class PluginConfig:
    """Plugin configuration container"""
    plugin_id: str
    config: Dict[str, Any]
    last_updated: datetime
    schema_version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plugin_id': self.plugin_id,
            'config': self.config,
            'last_updated': self.last_updated.isoformat(),
            'schema_version': self.schema_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfig':
        return cls(
            plugin_id=data['plugin_id'],
            config=data['config'],
            last_updated=datetime.fromisoformat(data['last_updated']),
            schema_version=data.get('schema_version', '1.0.0')
        )


class PluginManager:
    """Comprehensive plugin lifecycle manager"""
    
    def __init__(
        self, 
        plugins_dir: Optional[Path] = None,
        config_dir: Optional[Path] = None
    ):
        # Core directories
        self.plugins_dir = plugins_dir or Path.home() / ".theodore" / "plugins"
        self.config_dir = config_dir or Path.home() / ".theodore" / "config" / "plugins"
        
        # Component managers
        self.registry = get_plugin_registry()
        self.loader = get_plugin_loader()
        self.sandbox_manager = get_sandbox_manager()
        self.discovery = PluginDiscovery()
        
        # Plugin configurations
        self.configs: Dict[str, PluginConfig] = {}
        self.config_file = self.config_dir / "plugin_configs.json"
        
        # State tracking
        self._initialized = False
        self._lock = threading.RLock()
        
        # Default installation options
        self.default_install_options = InstallationOptions()
        
        # Create directories
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the plugin manager"""
        if self._initialized:
            return True
        
        try:
            # Initialize registry
            if not await self.registry.initialize():
                return False
            
            # Load plugin configurations
            await self._load_plugin_configs()
            
            # Auto-discover installed plugins
            await self._discover_installed_plugins()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize plugin manager: {e}")
            return False
    
    async def install_plugin(
        self, 
        source: Union[str, Path, PluginSource],
        options: Optional[InstallationOptions] = None
    ) -> bool:
        """Install a plugin from various sources"""
        
        if not self._initialized:
            await self.initialize()
        
        options = options or self.default_install_options
        
        try:
            # Resolve plugin source
            if isinstance(source, str):
                source = await self._resolve_plugin_source(source)
            elif isinstance(source, Path):
                source = PluginSource(
                    type="local",
                    location=str(source),
                    name=source.name
                )
            
            # Download/extract plugin
            plugin_path, metadata = await self._prepare_plugin_for_installation(source, options)
            
            # Check if already installed
            existing = self.registry.get_plugin_by_name(metadata.name, metadata.version)
            if existing and not options.force_reinstall:
                if existing.status in [PluginStatus.INSTALLED, PluginStatus.ENABLED]:
                    print(f"Plugin {metadata.name} v{metadata.version} already installed")
                    return True
            
            # Resolve and install dependencies
            if options.install_dependencies and not options.skip_dependencies:
                if not await self._install_dependencies(metadata, options):
                    raise PluginInstallError("Failed to install plugin dependencies")
            
            # Install plugin files
            final_plugin_path = await self._install_plugin_files(plugin_path, metadata, options)
            
            # Update metadata with installation path
            metadata.module_path = str(final_plugin_path)
            metadata.status = PluginStatus.INSTALLED
            metadata.install_date = datetime.now(timezone.utc)
            
            # Register plugin
            if not await self.registry.register_plugin(metadata, force=options.force_reinstall):
                raise PluginInstallError("Failed to register plugin in registry")
            
            # Create sandbox configuration
            await self._configure_plugin_sandbox(metadata, options)
            
            # Load plugin to verify installation
            instance = await self.loader.load_plugin(final_plugin_path, metadata)
            if not instance:
                raise PluginInstallError("Failed to load installed plugin")
            
            print(f"Successfully installed plugin: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            print(f"Failed to install plugin: {e}")
            return False
    
    async def uninstall_plugin(self, plugin_id: str, force: bool = False) -> bool:
        """Uninstall a plugin"""
        
        try:
            # Get plugin metadata
            metadata = self.registry.get_plugin(plugin_id)
            if not metadata:
                print(f"Plugin not found: {plugin_id}")
                return True  # Already uninstalled
            
            # Check for dependents
            dependents = self.registry.get_dependents(plugin_id)
            if dependents and not force:
                dependent_names = [dep.name for dep in dependents]
                raise PluginInstallError(
                    f"Cannot uninstall {metadata.name}: required by {dependent_names}. "
                    f"Use force=True to override."
                )
            
            # Disable and unload plugin first
            if metadata.status == PluginStatus.ENABLED:
                await self.disable_plugin(plugin_id)
            
            # Unload from loader
            await self.loader.unload_plugin(plugin_id)
            
            # Remove sandbox
            self.sandbox_manager.remove_sandbox(plugin_id)
            
            # Remove plugin files
            if metadata.module_path:
                plugin_path = Path(metadata.module_path)
                if plugin_path.exists():
                    if plugin_path.is_file():
                        plugin_path.unlink()
                    else:
                        shutil.rmtree(plugin_path)
            
            # Remove from registry
            await self.registry.unregister_plugin(plugin_id, force=force)
            
            # Remove configuration
            if plugin_id in self.configs:
                del self.configs[plugin_id]
                await self._save_plugin_configs()
            
            print(f"Successfully uninstalled plugin: {metadata.name}")
            return True
            
        except Exception as e:
            print(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        
        try:
            # Get plugin instance
            instance = self.registry.get_plugin_instance(plugin_id)
            if not instance:
                # Try to load plugin
                instance = await self.loader.load_plugin_by_id(plugin_id)
                if not instance:
                    raise PluginLifecycleError(f"Failed to load plugin: {plugin_id}")
            
            # Enable the plugin
            if await instance.enable():
                self.registry.update_plugin_status(plugin_id, PluginStatus.ENABLED)
                print(f"Plugin enabled: {instance.metadata.name}")
                return True
            else:
                raise PluginLifecycleError("Plugin enable method returned False")
                
        except Exception as e:
            print(f"Failed to enable plugin {plugin_id}: {e}")
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        
        try:
            # Get plugin instance
            instance = self.registry.get_plugin_instance(plugin_id)
            if not instance:
                print(f"Plugin not loaded: {plugin_id}")
                return True  # Already disabled
            
            # Disable the plugin
            if await instance.disable():
                self.registry.update_plugin_status(plugin_id, PluginStatus.DISABLED)
                print(f"Plugin disabled: {instance.metadata.name}")
                return True
            else:
                raise PluginLifecycleError("Plugin disable method returned False")
                
        except Exception as e:
            print(f"Failed to disable plugin {plugin_id}: {e}")
            return False
    
    async def configure_plugin(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Configure a plugin"""
        
        try:
            # Get plugin metadata
            metadata = self.registry.get_plugin(plugin_id)
            if not metadata:
                raise PluginConfigurationError(f"Plugin not found: {plugin_id}")
            
            # Validate configuration against schema
            if metadata.config_schema:
                self._validate_plugin_config(config, metadata.config_schema)
            
            # Update plugin instance if loaded
            instance = self.registry.get_plugin_instance(plugin_id)
            if instance:
                if not instance.update_config(config):
                    raise PluginConfigurationError("Plugin rejected configuration update")
            
            # Store configuration
            plugin_config = PluginConfig(
                plugin_id=plugin_id,
                config=config,
                last_updated=datetime.now(timezone.utc)
            )
            
            self.configs[plugin_id] = plugin_config
            await self._save_plugin_configs()
            
            print(f"Configuration updated for plugin: {metadata.name}")
            return True
            
        except Exception as e:
            print(f"Failed to configure plugin {plugin_id}: {e}")
            return False
    
    def get_plugin_config(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin configuration"""
        config = self.configs.get(plugin_id)
        return config.config if config else None
    
    def list_plugins(
        self, 
        category: Optional[PluginCategory] = None,
        status: Optional[PluginStatus] = None
    ) -> List[PluginMetadata]:
        """List installed plugins"""
        return self.registry.list_plugins(category=category, status=status)
    
    def search_plugins(self, query: str) -> List[PluginMetadata]:
        """Search plugins"""
        return self.registry.search_plugins(query)
    
    async def get_plugin_health(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin health status"""
        instance = self.registry.get_plugin_instance(plugin_id)
        if not instance:
            return None
        
        health = instance.get_health()
        
        # Add sandbox resource usage
        sandbox = self.sandbox_manager.get_sandbox(plugin_id)
        if sandbox:
            health['resource_usage'] = sandbox.get_resource_usage()
        
        return health
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin"""
        try:
            instance = await self.loader.reload_plugin(plugin_id)
            if instance:
                print(f"Plugin reloaded: {instance.metadata.name}")
                return True
            return False
        except Exception as e:
            print(f"Failed to reload plugin {plugin_id}: {e}")
            return False
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        registry_stats = self.registry.get_registry_stats()
        
        return {
            'registry': registry_stats,
            'loaded_plugins': len(self.loader.list_loaded_plugins()),
            'configurations': len(self.configs),
            'sandboxes': len(self.sandbox_manager.sandboxes),
            'plugins_directory': str(self.plugins_dir),
            'config_directory': str(self.config_dir)
        }
    
    # Private methods
    
    async def _resolve_plugin_source(self, source_str: str) -> PluginSource:
        """Resolve plugin source from string"""
        # Try to find in discovery sources
        sources = await self.discovery.search_plugins(source_str)
        if sources:
            return sources[0]
        
        # Check if it's a URL or path
        if source_str.startswith(('http://', 'https://')):
            return PluginSource(
                type="remote",
                location=source_str,
                name=Path(source_str).name
            )
        elif Path(source_str).exists():
            return PluginSource(
                type="local",
                location=source_str,
                name=Path(source_str).name
            )
        else:
            raise PluginInstallError(f"Unable to resolve plugin source: {source_str}")
    
    async def _prepare_plugin_for_installation(
        self, 
        source: PluginSource, 
        options: InstallationOptions
    ) -> tuple[Path, PluginMetadata]:
        """Prepare plugin for installation"""
        
        if source.type == "local":
            plugin_path = Path(source.location)
            
            # If it's an archive, extract it
            if plugin_path.suffix in ['.zip', '.tar.gz', '.tgz']:
                extract_dir = self.plugins_dir / "temp" / plugin_path.stem
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                if plugin_path.suffix == '.zip':
                    with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                else:
                    with tarfile.open(plugin_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                # Find the main plugin file
                plugin_files = list(extract_dir.glob("**/*.py"))
                if not plugin_files:
                    raise PluginInstallError("No Python files found in plugin archive")
                
                plugin_path = plugin_files[0]  # Use first Python file
            
            # Discover metadata
            metadata = await self.loader._discover_plugin_metadata(plugin_path)
            return plugin_path, metadata
        
        elif source.type == "remote":
            # Download plugin (would implement HTTP download)
            raise PluginInstallError("Remote plugin installation not yet implemented")
        
        else:
            raise PluginInstallError(f"Unsupported plugin source type: {source.type}")
    
    async def _install_dependencies(
        self, 
        metadata: PluginMetadata, 
        options: InstallationOptions
    ) -> bool:
        """Install plugin dependencies"""
        
        for dependency in metadata.compatibility.dependencies:
            if dependency.optional:
                continue
            
            # Check if dependency is already installed
            dep_plugin = self.registry.get_plugin_by_name(dependency.name)
            if dep_plugin and dep_plugin.status in [PluginStatus.INSTALLED, PluginStatus.ENABLED]:
                continue
            
            # Try to find and install dependency
            dep_sources = await self.discovery.search_plugins(dependency.name)
            if not dep_sources:
                print(f"Warning: Dependency not found: {dependency.name}")
                if not dependency.optional:
                    return False
                continue
            
            # Install dependency
            if not await self.install_plugin(dep_sources[0], options):
                print(f"Failed to install dependency: {dependency.name}")
                return False
        
        return True
    
    async def _install_plugin_files(
        self, 
        source_path: Path, 
        metadata: PluginMetadata, 
        options: InstallationOptions
    ) -> Path:
        """Install plugin files to final location"""
        
        # Determine installation path
        if options.custom_install_path:
            install_dir = options.custom_install_path
        else:
            install_dir = self.plugins_dir / metadata.name / metadata.version
        
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy plugin files
        if source_path.is_file():
            final_path = install_dir / source_path.name
            shutil.copy2(source_path, final_path)
        else:
            final_path = install_dir
            shutil.copytree(source_path, final_path, dirs_exist_ok=True)
        
        return final_path
    
    async def _configure_plugin_sandbox(
        self, 
        metadata: PluginMetadata, 
        options: InstallationOptions
    ):
        """Configure sandbox for plugin"""
        
        if not options.sandbox_enabled:
            return
        
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=options.memory_limit_mb,
            max_cpu_time_seconds=options.cpu_limit_seconds,
            max_execution_time_seconds=options.execution_timeout_seconds
        )
        
        # Create permissions
        permissions = PluginPermissions(
            network_access=options.network_access,
            file_system_read=set(options.file_read_paths),
            file_system_write=set(options.file_write_paths)
        )
        
        # Create sandbox
        self.sandbox_manager.create_sandbox(
            metadata.plugin_id,
            limits=limits,
            permissions=permissions
        )
    
    def _validate_plugin_config(self, config: Dict[str, Any], schema: Dict[str, Any]):
        """Validate plugin configuration against schema"""
        # Basic validation - could integrate with jsonschema
        required = schema.get('required', [])
        for field in required:
            if field not in config:
                raise PluginConfigurationError(f"Required field missing: {field}")
    
    async def _discover_installed_plugins(self):
        """Discover and register installed plugins"""
        if not self.plugins_dir.exists():
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            # Look for Python files
            plugin_files = list(plugin_dir.glob("**/*.py"))
            for plugin_file in plugin_files:
                try:
                    metadata = await self.loader._discover_plugin_metadata(plugin_file)
                    if metadata:
                        await self.registry.register_plugin(metadata)
                except Exception:
                    continue  # Skip invalid plugins
    
    async def _load_plugin_configs(self):
        """Load plugin configurations from disk"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            for config_data in data.get('configs', []):
                config = PluginConfig.from_dict(config_data)
                self.configs[config.plugin_id] = config
                
        except Exception as e:
            print(f"Failed to load plugin configurations: {e}")
    
    async def _save_plugin_configs(self):
        """Save plugin configurations to disk"""
        try:
            data = {
                'version': '1.0.0',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'configs': [config.to_dict() for config in self.configs.values()]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save plugin configurations: {e}")


# Global plugin manager instance
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


async def initialize_plugin_system() -> bool:
    """Initialize the complete plugin system"""
    manager = get_plugin_manager()
    return await manager.initialize()
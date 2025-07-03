#!/usr/bin/env python3
"""
Theodore v2 Plugin System Dependency Injection Integration

Integrates the plugin system with Theodore's dependency injection container,
allowing plugins to register services and access container services.
"""

from typing import Dict, Any, Optional, Type, List
import asyncio
from pathlib import Path

from src.infrastructure.di.container import Container, Scope
from src.infrastructure.plugins.manager import get_plugin_manager, PluginManager
from src.infrastructure.plugins.registry import get_plugin_registry, PluginRegistry
from src.infrastructure.plugins.base import BasePlugin, PluginMetadata, PluginStatus
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PluginDIRegistry:
    """Registry for plugin-provided services in the DI container"""
    
    def __init__(self, container: Container):
        self.container = container
        self.plugin_services: Dict[str, List[str]] = {}  # plugin_id -> service_names
        self._lock = asyncio.Lock()
    
    async def register_plugin_services(self, plugin_id: str, instance: BasePlugin) -> bool:
        """Register services provided by a plugin"""
        async with self._lock:
            try:
                services = []
                
                # Check if plugin provides services via interface methods
                if hasattr(instance, 'get_provided_services'):
                    provided_services = instance.get_provided_services()
                    
                    for service_name, service_config in provided_services.items():
                        service_type = service_config.get('type')
                        scope = service_config.get('scope', Scope.SINGLETON)
                        factory = service_config.get('factory')
                        
                        if service_type and factory:
                            # Register service in container
                            if callable(factory):
                                self.container.register(
                                    service_type,
                                    factory=lambda: factory(instance),
                                    scope=scope
                                )
                            else:
                                # Direct instance registration
                                self.container.register_instance(service_type, factory)
                            
                            services.append(service_name)
                            logger.info(f"Registered plugin service: {service_name} from {plugin_id}")
                
                # Check for auto-registration based on plugin category
                services.extend(await self._auto_register_plugin_services(plugin_id, instance))
                
                self.plugin_services[plugin_id] = services
                return True
                
            except Exception as e:
                logger.error(f"Failed to register services for plugin {plugin_id}: {e}")
                return False
    
    async def unregister_plugin_services(self, plugin_id: str) -> bool:
        """Unregister services provided by a plugin"""
        async with self._lock:
            try:
                services = self.plugin_services.get(plugin_id, [])
                
                for service_name in services:
                    try:
                        # Remove from container if possible
                        # Note: Container doesn't have unregister method yet, 
                        # this is a placeholder for future implementation
                        logger.info(f"Unregistered plugin service: {service_name} from {plugin_id}")
                    except Exception as e:
                        logger.warning(f"Failed to unregister service {service_name}: {e}")
                
                if plugin_id in self.plugin_services:
                    del self.plugin_services[plugin_id]
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister services for plugin {plugin_id}: {e}")
                return False
    
    async def _auto_register_plugin_services(self, plugin_id: str, instance: BasePlugin) -> List[str]:
        """Auto-register plugin services based on category and interfaces"""
        services = []
        
        try:
            category = instance.metadata.category
            
            # Auto-register based on plugin category
            if category.value == "ai_provider":
                from src.infrastructure.plugins.base import AIProviderPlugin
                if isinstance(instance, AIProviderPlugin):
                    # Register as AI provider service
                    self.container.register_instance(AIProviderPlugin, instance)
                    services.append(f"ai_provider_{plugin_id}")
            
            elif category.value == "scraper":
                from src.infrastructure.plugins.base import ScraperPlugin
                if isinstance(instance, ScraperPlugin):
                    # Register as scraper service
                    self.container.register_instance(ScraperPlugin, instance)
                    services.append(f"scraper_{plugin_id}")
            
            elif category.value == "storage":
                from src.infrastructure.plugins.base import StoragePlugin
                if isinstance(instance, StoragePlugin):
                    # Register as storage service
                    self.container.register_instance(StoragePlugin, instance)
                    services.append(f"storage_{plugin_id}")
            
            elif category.value == "search_tool":
                from src.infrastructure.plugins.base import SearchToolPlugin
                if isinstance(instance, SearchToolPlugin):
                    # Register as search tool service
                    self.container.register_instance(SearchToolPlugin, instance)
                    services.append(f"search_tool_{plugin_id}")
            
            # Register the plugin instance itself
            self.container.register_instance(BasePlugin, instance, name=plugin_id)
            services.append(f"plugin_{plugin_id}")
            
        except Exception as e:
            logger.warning(f"Auto-registration failed for plugin {plugin_id}: {e}")
        
        return services
    
    def get_plugin_services(self, plugin_id: str) -> List[str]:
        """Get list of services provided by a plugin"""
        return self.plugin_services.get(plugin_id, [])
    
    def get_all_plugin_services(self) -> Dict[str, List[str]]:
        """Get all plugin services"""
        return self.plugin_services.copy()


class DIAwarePlugin(BasePlugin):
    """Base class for plugins that need dependency injection access"""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None, container: Optional[Container] = None):
        super().__init__(metadata, config)
        self.container = container
    
    def get_service(self, service_type: Type, name: Optional[str] = None):
        """Get service from DI container"""
        if not self.container:
            raise RuntimeError("DI container not available")
        
        try:
            if name:
                return self.container.get(service_type, name=name)
            else:
                return self.container.get(service_type)
        except Exception as e:
            logger.error(f"Failed to get service {service_type} from container: {e}")
            return None
    
    def register_service(self, service_type: Type, instance: Any, name: Optional[str] = None):
        """Register a service in the DI container"""
        if not self.container:
            raise RuntimeError("DI container not available")
        
        try:
            if name:
                self.container.register_instance(service_type, instance, name=name)
            else:
                self.container.register_instance(service_type, instance)
        except Exception as e:
            logger.error(f"Failed to register service {service_type} in container: {e}")


class PluginEnabledPluginManager(PluginManager):
    """Plugin manager with DI container integration"""
    
    def __init__(self, container: Container, plugins_dir: Optional[Path] = None, config_dir: Optional[Path] = None):
        super().__init__(plugins_dir, config_dir)
        self.container = container
        self.di_registry = PluginDIRegistry(container)
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable plugin and register its services in DI container"""
        try:
            # Enable plugin normally
            if not await super().enable_plugin(plugin_id):
                return False
            
            # Get plugin instance
            instance = self.registry.get_plugin_instance(plugin_id)
            if not instance:
                logger.error(f"Plugin instance not found after enabling: {plugin_id}")
                return False
            
            # Inject container if plugin supports it
            if isinstance(instance, DIAwarePlugin):
                instance.container = self.container
            
            # Register plugin services in DI container
            await self.di_registry.register_plugin_services(plugin_id, instance)
            
            logger.info(f"Plugin {plugin_id} enabled and services registered")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable plugin with DI integration: {e}")
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable plugin and unregister its services from DI container"""
        try:
            # Unregister services first
            await self.di_registry.unregister_plugin_services(plugin_id)
            
            # Disable plugin normally
            result = await super().disable_plugin(plugin_id)
            
            if result:
                logger.info(f"Plugin {plugin_id} disabled and services unregistered")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to disable plugin with DI integration: {e}")
            return False
    
    async def install_plugin(self, source, options=None) -> bool:
        """Install plugin with DI container available during installation"""
        try:
            # Install plugin normally
            result = await super().install_plugin(source, options)
            
            if result:
                # Find the installed plugin (this is a bit hacky, could be improved)
                registry = get_plugin_registry()
                plugins = registry.list_plugins(status=PluginStatus.INSTALLED)
                
                # Get the most recently installed plugin
                if plugins:
                    latest_plugin = max(plugins, key=lambda p: p.install_date or p.last_updated)
                    instance = registry.get_plugin_instance(latest_plugin.plugin_id)
                    
                    if instance and isinstance(instance, DIAwarePlugin):
                        instance.container = self.container
                        logger.info(f"DI container injected into plugin: {latest_plugin.plugin_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to install plugin with DI integration: {e}")
            return False
    
    def get_plugin_services(self, plugin_id: str) -> List[str]:
        """Get services provided by a plugin"""
        return self.di_registry.get_plugin_services(plugin_id)
    
    def get_all_plugin_services(self) -> Dict[str, List[str]]:
        """Get all plugin services"""
        return self.di_registry.get_all_plugin_services()


async def initialize_plugin_di_integration(container: Container) -> bool:
    """Initialize plugin system with DI container integration"""
    try:
        # Create DI-enabled plugin manager
        manager = PluginEnabledPluginManager(container)
        
        # Initialize the manager
        if not await manager.initialize():
            logger.error("Failed to initialize DI-enabled plugin manager")
            return False
        
        # Replace global plugin manager with DI-enabled version
        import src.infrastructure.plugins.manager as manager_module
        manager_module._global_plugin_manager = manager
        
        # Register plugin manager in container
        container.register_instance(PluginManager, manager)
        container.register_instance(PluginEnabledPluginManager, manager)
        
        # Register plugin registry
        registry = get_plugin_registry()
        container.register_instance(PluginRegistry, registry)
        
        logger.info("Plugin system initialized with DI container integration")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize plugin DI integration: {e}")
        return False


def get_di_enabled_plugin_manager() -> Optional[PluginEnabledPluginManager]:
    """Get the DI-enabled plugin manager if available"""
    manager = get_plugin_manager()
    if isinstance(manager, PluginEnabledPluginManager):
        return manager
    return None


# Helper functions for plugin developers

def create_ai_provider_plugin(metadata: PluginMetadata, container: Container) -> Type[DIAwarePlugin]:
    """Create a base AI provider plugin class with DI support"""
    from src.infrastructure.plugins.base import AIProviderPlugin
    
    class DIAIProviderPlugin(AIProviderPlugin, DIAwarePlugin):
        def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
            super().__init__(metadata, config, container)
        
        def get_provided_services(self) -> Dict[str, Dict[str, Any]]:
            """Define services this plugin provides"""
            return {
                'ai_provider': {
                    'type': AIProviderPlugin,
                    'factory': lambda: self,
                    'scope': Scope.SINGLETON
                }
            }
    
    return DIAIProviderPlugin


def create_scraper_plugin(metadata: PluginMetadata, container: Container) -> Type[DIAwarePlugin]:
    """Create a base scraper plugin class with DI support"""
    from src.infrastructure.plugins.base import ScraperPlugin
    
    class DIScraperPlugin(ScraperPlugin, DIAwarePlugin):
        def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
            super().__init__(metadata, config, container)
        
        def get_provided_services(self) -> Dict[str, Dict[str, Any]]:
            """Define services this plugin provides"""
            return {
                'scraper': {
                    'type': ScraperPlugin,
                    'factory': lambda: self,
                    'scope': Scope.SINGLETON
                }
            }
    
    return DIScraperPlugin


def create_storage_plugin(metadata: PluginMetadata, container: Container) -> Type[DIAwarePlugin]:
    """Create a base storage plugin class with DI support"""
    from src.infrastructure.plugins.base import StoragePlugin
    
    class DIStoragePlugin(StoragePlugin, DIAwarePlugin):
        def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
            super().__init__(metadata, config, container)
        
        def get_provided_services(self) -> Dict[str, Dict[str, Any]]:
            """Define services this plugin provides"""
            return {
                'storage': {
                    'type': StoragePlugin,
                    'factory': lambda: self,
                    'scope': Scope.SINGLETON
                }
            }
    
    return DIStoragePlugin


def create_search_tool_plugin(metadata: PluginMetadata, container: Container) -> Type[DIAwarePlugin]:
    """Create a base search tool plugin class with DI support"""
    from src.infrastructure.plugins.base import SearchToolPlugin
    
    class DISearchToolPlugin(SearchToolPlugin, DIAwarePlugin):
        def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
            super().__init__(metadata, config, container)
        
        def get_provided_services(self) -> Dict[str, Dict[str, Any]]:
            """Define services this plugin provides"""
            return {
                'search_tool': {
                    'type': SearchToolPlugin,
                    'factory': lambda: self,
                    'scope': Scope.SINGLETON
                }
            }
    
    return DISearchToolPlugin
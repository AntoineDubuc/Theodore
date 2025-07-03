#!/usr/bin/env python3
"""
Theodore v2 Plugin System Foundation

Comprehensive plugin architecture for extending Theodore with custom adapters,
AI providers, storage backends, and search tools.
"""

from .base import (
    BasePlugin,
    PluginMetadata,
    PluginStatus,
    PluginCategory,
    PluginCompatibility,
    PluginDependency
)

from .registry import (
    PluginRegistry,
    PluginRegistryError,
    PluginConflictError,
    PluginNotFoundError
)

from .loader import (
    PluginLoader,
    PluginLoadError,
    PluginValidationError,
    PluginSecurityError
)

from .manager import (
    PluginManager,
    PluginLifecycleError,
    PluginInstallError,
    PluginConfigurationError
)

from .sandbox import (
    PluginSandbox,
    SandboxViolationError,
    ResourceLimitError
)

from .discovery import (
    PluginDiscovery,
    PluginSource,
    DiscoveryError
)

__all__ = [
    # Base classes
    "BasePlugin",
    "PluginMetadata", 
    "PluginStatus",
    "PluginCategory",
    "PluginCompatibility",
    "PluginDependency",
    
    # Registry
    "PluginRegistry",
    "PluginRegistryError",
    "PluginConflictError", 
    "PluginNotFoundError",
    
    # Loader
    "PluginLoader",
    "PluginLoadError",
    "PluginValidationError",
    "PluginSecurityError",
    
    # Manager
    "PluginManager",
    "PluginLifecycleError",
    "PluginInstallError",
    "PluginConfigurationError",
    
    # Sandbox
    "PluginSandbox",
    "SandboxViolationError",
    "ResourceLimitError",
    
    # Discovery
    "PluginDiscovery",
    "PluginSource",
    "DiscoveryError"
]
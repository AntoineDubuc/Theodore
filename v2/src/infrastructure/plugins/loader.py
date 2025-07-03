#!/usr/bin/env python3
"""
Theodore v2 Plugin Loader

Secure plugin loading with validation, sandboxing, and dependency management.
Supports dynamic loading and hot reloading with security controls.
"""

import os
import sys
import ast
import importlib
import importlib.util
import inspect
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set
import threading
import asyncio
from dataclasses import dataclass

from .base import BasePlugin, PluginMetadata, PluginStatus, PluginCategory
from .registry import PluginRegistry, get_plugin_registry
from .sandbox import PluginSandbox


class PluginLoadError(Exception):
    """Base exception for plugin loading errors"""
    pass


class PluginValidationError(PluginLoadError):
    """Raised when plugin validation fails"""
    pass


class PluginSecurityError(PluginLoadError):
    """Raised when plugin security validation fails"""
    pass


class PluginImportError(PluginLoadError):
    """Raised when plugin import fails"""
    pass


@dataclass
class LoadedPlugin:
    """Container for loaded plugin information"""
    metadata: PluginMetadata
    instance: BasePlugin
    module: Any
    load_time: float
    file_hash: str
    last_modified: float


class SecurityValidator:
    """Security validation for plugin code"""
    
    # Dangerous modules and functions to check for
    DANGEROUS_IMPORTS = {
        'os.system', 'subprocess', 'eval', 'exec', 'compile',
        'open', '__import__', 'getattr', 'setattr', 'delattr',
        'globals', 'locals', 'vars', 'dir'
    }
    
    RESTRICTED_MODULES = {
        'subprocess', 'os.system', 'shutil', 'socket', 'urllib',
        'requests', 'http', 'ftplib', 'smtplib', 'telnetlib'
    }
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violations: List[str] = []
    
    def validate_source_code(self, source_code: str, file_path: str) -> bool:
        """Validate plugin source code for security issues"""
        self.violations = []
        
        try:
            # Parse AST
            tree = ast.parse(source_code, filename=file_path)
            
            # Check for dangerous patterns
            self._check_ast_tree(tree)
            
            return len(self.violations) == 0
            
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {e}")
            return False
        except Exception as e:
            self.violations.append(f"Validation error: {e}")
            return False
    
    def _check_ast_tree(self, tree: ast.AST):
        """Check AST tree for security violations"""
        for node in ast.walk(tree):
            self._check_node(node)
    
    def _check_node(self, node: ast.AST):
        """Check individual AST node for security issues"""
        # Check imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            self._check_import(node)
        
        # Check function calls
        elif isinstance(node, ast.Call):
            self._check_call(node)
        
        # Check attribute access
        elif isinstance(node, ast.Attribute):
            self._check_attribute(node)
        
        # Check exec/eval usage
        elif isinstance(node, ast.Name):
            if node.id in {'eval', 'exec', 'compile'}:
                self.violations.append(f"Dangerous function usage: {node.id}")
    
    def _check_import(self, node):
        """Check import statements"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.RESTRICTED_MODULES:
                    self.violations.append(f"Restricted module import: {alias.name}")
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            if module in self.RESTRICTED_MODULES:
                self.violations.append(f"Restricted module import: {module}")
            
            # Check specific imports
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                if full_name in self.DANGEROUS_IMPORTS:
                    self.violations.append(f"Dangerous import: {full_name}")
    
    def _check_call(self, node):
        """Check function calls"""
        if isinstance(node.func, ast.Name):
            if node.func.id in {'eval', 'exec', 'compile', '__import__'}:
                self.violations.append(f"Dangerous function call: {node.func.id}")
    
    def _check_attribute(self, node):
        """Check attribute access"""
        # Reconstruct attribute chain
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        attribute_chain = '.'.join(reversed(parts))
        
        if attribute_chain in self.DANGEROUS_IMPORTS:
            self.violations.append(f"Dangerous attribute access: {attribute_chain}")
    
    def get_violations(self) -> List[str]:
        """Get list of security violations"""
        return self.violations.copy()


class PluginLoader:
    """Secure plugin loader with validation and sandboxing"""
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or get_plugin_registry()
        self.loaded_plugins: Dict[str, LoadedPlugin] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Security configuration
        self.security_enabled = True
        self.strict_mode = True
        self.sandbox_enabled = True
        
        # File monitoring for hot reloading
        self._file_watchers: Dict[str, float] = {}  # file_path -> last_modified
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_enabled = False
    
    async def load_plugin(
        self, 
        plugin_path: Path, 
        metadata: Optional[PluginMetadata] = None,
        force_reload: bool = False
    ) -> Optional[BasePlugin]:
        """Load a plugin from file path"""
        
        try:
            plugin_path = Path(plugin_path).resolve()
            
            if not plugin_path.exists():
                raise PluginLoadError(f"Plugin file not found: {plugin_path}")
            
            # Calculate file hash for integrity checking
            file_hash = self._calculate_file_hash(plugin_path)
            file_modified = plugin_path.stat().st_mtime
            
            # Check if already loaded and not modified
            if not force_reload:
                existing = self._find_loaded_plugin_by_path(plugin_path)
                if existing and existing.file_hash == file_hash:
                    return existing.instance
            
            # Security validation
            if self.security_enabled:
                await self._validate_plugin_security(plugin_path)
            
            # Load or discover metadata
            if not metadata:
                metadata = await self._discover_plugin_metadata(plugin_path)
            
            # Load the plugin module
            start_time = time.perf_counter()
            module = await self._load_plugin_module(plugin_path, metadata)
            
            # Create plugin instance
            plugin_class = self._find_plugin_class(module, metadata)
            
            # Initialize with sandbox if enabled
            if self.sandbox_enabled:
                sandbox = PluginSandbox(metadata.plugin_id)
                instance = await sandbox.create_plugin_instance(plugin_class, metadata)
            else:
                instance = plugin_class(metadata)
            
            load_time = time.perf_counter() - start_time
            
            # Store loaded plugin info
            loaded_plugin = LoadedPlugin(
                metadata=metadata,
                instance=instance,
                module=module,
                load_time=load_time,
                file_hash=file_hash,
                last_modified=file_modified
            )
            
            with self._lock:
                self.loaded_plugins[metadata.plugin_id] = loaded_plugin
                self.plugin_modules[metadata.plugin_id] = module
                
                # Update registry
                self.registry.set_plugin_instance(metadata.plugin_id, instance)
                
                # Start file watching for hot reload
                if self._watch_enabled:
                    self._file_watchers[str(plugin_path)] = file_modified
            
            # Update metadata with load information
            metadata.load_time = load_time
            metadata.status = PluginStatus.INSTALLED
            
            return instance
            
        except Exception as e:
            error_msg = f"Failed to load plugin from {plugin_path}: {e}"
            raise PluginLoadError(error_msg) from e
    
    async def load_plugin_by_id(self, plugin_id: str, force_reload: bool = False) -> Optional[BasePlugin]:
        """Load a plugin by its ID from the registry"""
        
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise PluginLoadError(f"Plugin not found in registry: {plugin_id}")
        
        if not metadata.module_path:
            raise PluginLoadError(f"Plugin module path not specified: {plugin_id}")
        
        return await self.load_plugin(Path(metadata.module_path), metadata, force_reload)
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        try:
            with self._lock:
                if plugin_id not in self.loaded_plugins:
                    return True  # Already unloaded
                
                loaded_plugin = self.loaded_plugins[plugin_id]
                
                # Cleanup plugin instance
                try:
                    await loaded_plugin.instance.unload()
                except Exception as e:
                    print(f"Error during plugin cleanup: {e}")
                
                # Remove from tracking
                del self.loaded_plugins[plugin_id]
                if plugin_id in self.plugin_modules:
                    del self.plugin_modules[plugin_id]
                
                # Remove from registry
                self.registry.remove_plugin_instance(plugin_id)
                
                # Update status
                loaded_plugin.metadata.status = PluginStatus.DISABLED
            
            return True
            
        except Exception as e:
            print(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    async def reload_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Reload a plugin"""
        
        # Get current plugin info
        with self._lock:
            if plugin_id not in self.loaded_plugins:
                raise PluginLoadError(f"Plugin not loaded: {plugin_id}")
            
            loaded_plugin = self.loaded_plugins[plugin_id]
            plugin_path = loaded_plugin.metadata.module_path
        
        if not plugin_path:
            raise PluginLoadError(f"Plugin module path not available: {plugin_id}")
        
        # Unload current instance
        await self.unload_plugin(plugin_id)
        
        # Reload from file
        return await self.load_plugin(Path(plugin_path), force_reload=True)
    
    def get_loaded_plugin(self, plugin_id: str) -> Optional[LoadedPlugin]:
        """Get loaded plugin information"""
        with self._lock:
            return self.loaded_plugins.get(plugin_id)
    
    def list_loaded_plugins(self) -> List[LoadedPlugin]:
        """List all loaded plugins"""
        with self._lock:
            return list(self.loaded_plugins.values())
    
    def start_hot_reload_watching(self):
        """Start watching plugin files for changes"""
        if self._watch_enabled:
            return
        
        self._watch_enabled = True
        self._watch_thread = threading.Thread(target=self._file_watch_loop, daemon=True)
        self._watch_thread.start()
    
    def stop_hot_reload_watching(self):
        """Stop watching plugin files"""
        self._watch_enabled = False
        if self._watch_thread:
            self._watch_thread.join(timeout=1)
    
    # Private methods
    
    async def _validate_plugin_security(self, plugin_path: Path):
        """Validate plugin security"""
        try:
            with open(plugin_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            validator = SecurityValidator(strict_mode=self.strict_mode)
            
            if not validator.validate_source_code(source_code, str(plugin_path)):
                violations = validator.get_violations()
                raise PluginSecurityError(
                    f"Security violations detected in {plugin_path}:\n" + 
                    "\n".join(f"- {v}" for v in violations)
                )
                
        except PluginSecurityError:
            raise
        except Exception as e:
            raise PluginValidationError(f"Failed to validate plugin security: {e}")
    
    async def _discover_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Discover plugin metadata from source code"""
        try:
            # Try to find metadata in the module
            spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path)
            if not spec or not spec.loader:
                raise PluginLoadError(f"Cannot create module spec for {plugin_path}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Load module temporarily to extract metadata
            spec.loader.exec_module(module)
            
            # Look for plugin metadata
            if hasattr(module, 'PLUGIN_METADATA'):
                metadata_dict = module.PLUGIN_METADATA
                if isinstance(metadata_dict, dict):
                    metadata = PluginMetadata.from_dict(metadata_dict)
                    metadata.module_path = str(plugin_path)
                    return metadata
            
            # If no metadata found, create basic metadata
            plugin_name = plugin_path.stem
            return PluginMetadata(
                name=plugin_name,
                version="1.0.0",
                description=f"Plugin loaded from {plugin_path}",
                author="Unknown",
                category=PluginCategory.UTILITY,
                module_path=str(plugin_path)
            )
            
        except Exception as e:
            raise PluginValidationError(f"Failed to discover plugin metadata: {e}")
    
    async def _load_plugin_module(self, plugin_path: Path, metadata: PluginMetadata) -> Any:
        """Load plugin module"""
        try:
            # Create module spec
            module_name = f"theodore_plugin_{metadata.name}_{metadata.plugin_id[:8]}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            
            if not spec or not spec.loader:
                raise PluginImportError(f"Cannot create module spec for {plugin_path}")
            
            # Create and load module
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules temporarily for imports
            sys.modules[module_name] = module
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                # Remove from sys.modules on failure
                sys.modules.pop(module_name, None)
                raise
            
            return module
            
        except Exception as e:
            raise PluginImportError(f"Failed to load plugin module: {e}")
    
    def _find_plugin_class(self, module: Any, metadata: PluginMetadata) -> Type[BasePlugin]:
        """Find plugin class in module"""
        
        # Look for explicitly named entry point
        if metadata.entry_point and ':' in metadata.entry_point:
            _, class_name = metadata.entry_point.split(':', 1)
            if hasattr(module, class_name):
                plugin_class = getattr(module, class_name)
                if inspect.isclass(plugin_class) and issubclass(plugin_class, BasePlugin):
                    return plugin_class
        
        # Search for BasePlugin subclasses
        plugin_classes = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj != BasePlugin:
                plugin_classes.append(obj)
        
        if len(plugin_classes) == 1:
            return plugin_classes[0]
        elif len(plugin_classes) > 1:
            raise PluginLoadError(
                f"Multiple plugin classes found in module. "
                f"Specify entry_point in metadata or ensure only one BasePlugin subclass exists."
            )
        else:
            raise PluginLoadError("No plugin class found in module")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _find_loaded_plugin_by_path(self, plugin_path: Path) -> Optional[LoadedPlugin]:
        """Find loaded plugin by file path"""
        plugin_path_str = str(plugin_path)
        with self._lock:
            for loaded_plugin in self.loaded_plugins.values():
                if loaded_plugin.metadata.module_path == plugin_path_str:
                    return loaded_plugin
        return None
    
    def _file_watch_loop(self):
        """File watching loop for hot reload"""
        while self._watch_enabled:
            try:
                modified_files = []
                
                with self._lock:
                    for file_path, last_modified in self._file_watchers.items():
                        try:
                            current_modified = Path(file_path).stat().st_mtime
                            if current_modified > last_modified:
                                modified_files.append(file_path)
                                self._file_watchers[file_path] = current_modified
                        except (OSError, FileNotFoundError):
                            # File might have been deleted
                            pass
                
                # Reload modified plugins
                for file_path in modified_files:
                    try:
                        # Find plugin by file path
                        loaded_plugin = self._find_loaded_plugin_by_path(Path(file_path))
                        if loaded_plugin:
                            print(f"Hot reloading plugin: {loaded_plugin.metadata.name}")
                            asyncio.create_task(self.reload_plugin(loaded_plugin.metadata.plugin_id))
                    except Exception as e:
                        print(f"Failed to hot reload plugin from {file_path}: {e}")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in file watch loop: {e}")
                time.sleep(5)  # Wait longer on error


# Global loader instance
_global_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get global plugin loader"""
    global _global_loader
    if _global_loader is None:
        _global_loader = PluginLoader()
    return _global_loader
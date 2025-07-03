#!/usr/bin/env python3
"""
Theodore v2 Plugin Management API Router

FastAPI router for plugin discovery, installation, and management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from ...infrastructure.container.application import ApplicationContainer
from ...infrastructure.plugins.manager import PluginManager
from ...infrastructure.plugins.discovery import PluginDiscovery
from ...infrastructure.observability.logging import get_logger
from ...infrastructure.observability.metrics import get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()

router = APIRouter()


def get_container() -> ApplicationContainer:
    """Get application container dependency"""
    from fastapi import Request
    import inspect
    frame = inspect.currentframe()
    try:
        request = None
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            if 'request' in frame_locals:
                request = frame_locals['request']
                break
        
        if request and hasattr(request.app.state, 'container'):
            return request.app.state.container
        else:
            container = ApplicationContainer()
            return container
    finally:
        del frame


@router.get("", summary="List Available Plugins")
async def list_plugins(
    category: Optional[str] = Query(None, description="Filter by plugin category"),
    status: Optional[str] = Query(None, description="Filter by plugin status"),
    search: Optional[str] = Query(None, description="Search plugins by name or description"),
    limit: int = Query(50, ge=1, le=200, description="Maximum plugins to return"),
    offset: int = Query(0, ge=0, description="Number of plugins to skip"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    List available plugins with filtering and search
    
    Returns a paginated list of available plugins from all configured
    discovery sources including local directories, registries, and GitHub.
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # List plugins with filters
        plugins = await plugin_manager.list_plugins(
            category=category,
            status=status,
            search_query=search,
            limit=limit,
            offset=offset
        )
        
        # Record metrics
        metrics.increment_counter(
            "plugin_list_requests",
            tags={
                "has_category_filter": str(bool(category)),
                "has_status_filter": str(bool(status)),
                "has_search": str(bool(search))
            }
        )
        
        return {
            "plugins": [plugin.to_dict() for plugin in plugins.plugins],
            "total": plugins.total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(plugins.plugins) < plugins.total,
            "categories": plugins.categories,
            "available_statuses": ["unknown", "discovered", "installed", "enabled", "disabled", "error"]
        }
        
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list plugins: {str(e)}"
        )


@router.get("/search", summary="Search for Plugins")
async def search_plugins(
    query: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    source_types: Optional[List[str]] = Query(None, description="Source types to search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Search for plugins across all discovery sources
    
    Performs a comprehensive search across local directories,
    plugin registries, and GitHub repositories for plugins
    matching the search query.
    """
    
    try:
        # Get plugin discovery
        plugin_discovery = PluginDiscovery()
        
        # Search plugins
        results = await plugin_discovery.search_plugins(
            query=query,
            category=category,
            source_types=source_types
        )
        
        # Limit results
        limited_results = results[:limit]
        
        # Record metrics
        metrics.increment_counter(
            "plugin_search_requests",
            tags={"has_category": str(bool(category))}
        )
        
        logger.info(
            f"Plugin search completed: '{query}'",
            extra={
                "query": query,
                "results_count": len(limited_results),
                "category": category,
                "source_types": source_types
            }
        )
        
        return {
            "query": query,
            "results": [result.to_dict() for result in limited_results],
            "total_found": len(results),
            "showing": len(limited_results),
            "sources_searched": source_types or ["local", "registry", "github"]
        }
        
    except Exception as e:
        logger.error(f"Plugin search failed for query '{query}': {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Plugin search failed: {str(e)}"
        )


@router.post("/{plugin_name}/install", summary="Install Plugin")
async def install_plugin(
    plugin_name: str,
    version: Optional[str] = Query(None, description="Specific version to install"),
    force: bool = Query(False, description="Force installation even if conflicts exist"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Install a plugin
    
    Downloads and installs the specified plugin, resolving dependencies
    and checking for conflicts. The plugin will be installed but not
    enabled automatically.
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # Install plugin
        result = await plugin_manager.install_plugin(
            plugin_name=plugin_name,
            version=version,
            force=force
        )
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"Plugin installation failed: {result.error}"
            )
        
        # Record metrics
        metrics.increment_counter(
            "plugin_installations",
            tags={
                "plugin_name": plugin_name,
                "force": str(force)
            }
        )
        
        logger.info(
            f"Plugin installed: {plugin_name}",
            extra={
                "plugin_name": plugin_name,
                "version": version or "latest",
                "force": force
            }
        )
        
        return {
            "message": f"Plugin '{plugin_name}' installed successfully",
            "plugin_name": plugin_name,
            "version": result.version,
            "plugin_id": result.plugin_id,
            "dependencies_installed": result.dependencies_installed,
            "installation_time_seconds": result.installation_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to install plugin {plugin_name}: {e}", exc_info=True)
        metrics.increment_counter("plugin_installation_errors")
        
        raise HTTPException(
            status_code=500,
            detail=f"Plugin installation failed: {str(e)}"
        )


@router.post("/{plugin_name}/enable", summary="Enable Plugin")
async def enable_plugin(
    plugin_name: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Enable an installed plugin
    
    Enables a previously installed plugin, making its functionality
    available in the system. The plugin must be installed first.
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # Enable plugin
        success = await plugin_manager.enable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin not found or cannot be enabled: {plugin_name}"
            )
        
        # Record metrics
        metrics.increment_counter("plugin_enabled", tags={"plugin_name": plugin_name})
        
        logger.info(f"Plugin enabled: {plugin_name}")
        
        return {
            "message": f"Plugin '{plugin_name}' enabled successfully",
            "plugin_name": plugin_name,
            "status": "enabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable plugin {plugin_name}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enable plugin: {str(e)}"
        )


@router.post("/{plugin_name}/disable", summary="Disable Plugin")
async def disable_plugin(
    plugin_name: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Disable an enabled plugin
    
    Disables a currently enabled plugin, making its functionality
    unavailable. The plugin remains installed and can be re-enabled.
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # Disable plugin
        success = await plugin_manager.disable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin not found or cannot be disabled: {plugin_name}"
            )
        
        # Record metrics
        metrics.increment_counter("plugin_disabled", tags={"plugin_name": plugin_name})
        
        logger.info(f"Plugin disabled: {plugin_name}")
        
        return {
            "message": f"Plugin '{plugin_name}' disabled successfully",
            "plugin_name": plugin_name,
            "status": "disabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable plugin {plugin_name}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disable plugin: {str(e)}"
        )


@router.delete("/{plugin_name}", summary="Uninstall Plugin")
async def uninstall_plugin(
    plugin_name: str,
    force: bool = Query(False, description="Force uninstall even if other plugins depend on it"),
    container: ApplicationContainer = Depends(get_container)
):
    """
    Uninstall a plugin
    
    Completely removes a plugin from the system, including all
    its files and dependencies (if not used by other plugins).
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # Uninstall plugin
        result = await plugin_manager.uninstall_plugin(
            plugin_name=plugin_name,
            force=force
        )
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"Plugin uninstallation failed: {result.error}"
            )
        
        # Record metrics
        metrics.increment_counter(
            "plugin_uninstalled",
            tags={
                "plugin_name": plugin_name,
                "force": str(force)
            }
        )
        
        logger.info(f"Plugin uninstalled: {plugin_name}")
        
        return {
            "message": f"Plugin '{plugin_name}' uninstalled successfully",
            "plugin_name": plugin_name,
            "dependencies_removed": result.dependencies_removed,
            "files_removed": result.files_removed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to uninstall plugin {plugin_name}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Plugin uninstallation failed: {str(e)}"
        )


@router.get("/{plugin_name}/status", summary="Get Plugin Status")
async def get_plugin_status(
    plugin_name: str,
    container: ApplicationContainer = Depends(get_container)
):
    """
    Get detailed status information for a plugin
    
    Returns comprehensive information about a plugin including
    its current status, configuration, dependencies, and health.
    """
    
    try:
        # Get plugin manager
        plugin_manager = await container.get(PluginManager)
        
        # Get plugin status
        status_info = await plugin_manager.get_plugin_status(plugin_name)
        
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin not found: {plugin_name}"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for plugin {plugin_name}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get plugin status: {str(e)}"
        )


@router.get("/categories", summary="Get Plugin Categories")
async def get_plugin_categories():
    """
    Get available plugin categories
    
    Returns a list of all available plugin categories with
    descriptions and example plugin types.
    """
    
    return {
        "categories": [
            {
                "name": "ai_provider",
                "display_name": "AI Providers",
                "description": "AI and LLM service integrations",
                "examples": ["OpenAI", "Anthropic", "Cohere"]
            },
            {
                "name": "scraper",
                "display_name": "Web Scrapers",
                "description": "Web scraping implementations",
                "examples": ["Crawl4AI", "Playwright", "Selenium"]
            },
            {
                "name": "storage",
                "display_name": "Storage Backends",
                "description": "Vector and data storage systems",
                "examples": ["Pinecone", "Weaviate", "ChromaDB"]
            },
            {
                "name": "search_tool",
                "display_name": "Search Tools",
                "description": "MCP search tool implementations",
                "examples": ["Perplexity", "Tavily", "Google Search"]
            },
            {
                "name": "export",
                "display_name": "Export Tools",
                "description": "Data export and formatting tools",
                "examples": ["CSV", "Excel", "PDF"]
            },
            {
                "name": "integration",
                "display_name": "Integrations",
                "description": "Third-party service integrations",
                "examples": ["Slack", "Discord", "Teams"]
            },
            {
                "name": "utility",
                "display_name": "Utilities",
                "description": "General utility plugins",
                "examples": ["Data validators", "Text processors"]
            }
        ]
    }
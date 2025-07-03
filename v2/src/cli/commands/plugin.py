#!/usr/bin/env python3
"""
Theodore v2 Plugin CLI Commands

Provides comprehensive plugin management through CLI commands including
installation, configuration, lifecycle management, and discovery.
"""

import asyncio
import click
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.infrastructure.plugins.manager import (
    get_plugin_manager,
    InstallationOptions,
    initialize_plugin_system
)
from src.infrastructure.plugins.discovery import search_plugins, discover_local_plugins
from src.infrastructure.plugins.base import PluginCategory, PluginStatus
from src.infrastructure.plugins.registry import get_plugin_registry
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)
console = Console()


def format_plugin_table(plugins: List[Any], show_details: bool = False) -> Table:
    """Format plugins as a Rich table"""
    if show_details:
        table = Table(title="📦 Plugin Details")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Category", style="blue")
        table.add_column("Author", style="green")
        table.add_column("Description", style="white")
        
        for plugin in plugins:
            status = getattr(plugin, 'status', PluginStatus.UNKNOWN)
            category = getattr(plugin, 'category', PluginCategory.UTILITY)
            
            # Status with color
            status_text = status.value if hasattr(status, 'value') else str(status)
            if status_text == "enabled":
                status_display = "[green]✅ enabled[/green]"
            elif status_text == "disabled":
                status_display = "[yellow]⏸️ disabled[/yellow]"
            elif status_text == "installed":
                status_display = "[blue]📦 installed[/blue]"
            elif status_text == "failed":
                status_display = "[red]❌ failed[/red]"
            else:
                status_display = f"[dim]{status_text}[/dim]"
            
            description = plugin.description
            if len(description) > 60:
                description = description[:57] + "..."
            
            table.add_row(
                plugin.name,
                plugin.version,
                status_display,
                category.value if hasattr(category, 'value') else str(category),
                plugin.author,
                description
            )
    else:
        table = Table(title="📦 Installed Plugins")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Category", style="blue")
        
        for plugin in plugins:
            status = getattr(plugin, 'status', PluginStatus.UNKNOWN)
            category = getattr(plugin, 'category', PluginCategory.UTILITY)
            
            # Status with color
            status_text = status.value if hasattr(status, 'value') else str(status)
            if status_text == "enabled":
                status_display = "[green]✅ enabled[/green]"
            elif status_text == "disabled":
                status_display = "[yellow]⏸️ disabled[/yellow]"
            elif status_text == "installed":
                status_display = "[blue]📦 installed[/blue]"
            elif status_text == "failed":
                status_display = "[red]❌ failed[/red]"
            else:
                status_display = f"[dim]{status_text}[/dim]"
            
            table.add_row(
                plugin.name,
                plugin.version,
                status_display,
                category.value if hasattr(category, 'value') else str(category)
            )
    
    return table


def format_plugin_sources_table(sources: List[Any]) -> Table:
    """Format plugin sources as a Rich table"""
    table = Table(title="🔍 Available Plugin Sources")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Location", style="blue")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    
    for source in sources:
        location = source.location
        if len(location) > 50:
            location = location[:47] + "..."
        
        description = source.description or "No description"
        if len(description) > 40:
            description = description[:37] + "..."
        
        # Type with emoji
        type_display = source.type
        if source.type == "local":
            type_display = "📁 local"
        elif source.type == "registry":
            type_display = "🌐 registry"
        elif source.type == "git":
            type_display = "🔗 git"
        elif source.type == "github":
            type_display = "🐙 github"
        
        table.add_row(
            source.name,
            type_display,
            location,
            source.version or "[dim]Unknown[/dim]",
            description
        )
    
    return table


@click.group(name='plugin')
def plugin_group():
    """🔌 Manage Theodore plugins and extensions"""
    pass


@plugin_group.command()
@click.option('--category', type=click.Choice([cat.value for cat in PluginCategory]), 
              help='Filter by plugin category')
@click.option('--status', type=click.Choice([status.value for status in PluginStatus]),
              help='Filter by plugin status')
@click.option('--details', is_flag=True, help='Show detailed information')
async def list(category: Optional[str], status: Optional[str], details: bool):
    """
    List all installed plugins
    
    Examples:
        theodore plugin list
        theodore plugin list --category ai_provider
        theodore plugin list --status enabled --details
    """
    try:
        # Initialize plugin system
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        # Convert string values back to enums
        category_enum = PluginCategory(category) if category else None
        status_enum = PluginStatus(status) if status else None
        
        plugins = manager.list_plugins(category=category_enum, status=status_enum)
        
        if not plugins:
            console.print("📭 No plugins found matching the criteria.", style="yellow")
            return
        
        table = format_plugin_table(plugins, show_details=details)
        console.print(table)
        
        # Summary
        console.print(f"\n📊 Total: {len(plugins)} plugin(s)", style="dim")
        
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('query')
async def search(query: str):
    """
    Search for plugins in local registry
    
    QUERY: Search term for plugin name, description, or tags
    
    Examples:
        theodore plugin search ai
        theodore plugin search perplexity
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        registry = get_plugin_registry()
        plugins = registry.search_plugins(query)
        
        if not plugins:
            console.print(f"🔍 No plugins found matching '{query}'.", style="yellow")
            return
        
        table = format_plugin_table(plugins, show_details=True)
        console.print(table)
        
        console.print(f"\n📊 Found {len(plugins)} plugin(s) matching '{query}'", style="dim")
        
    except Exception as e:
        logger.error(f"Failed to search plugins: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('query', required=False)
@click.option('--category', type=click.Choice([cat.value for cat in PluginCategory]),
              help='Filter by plugin category')
@click.option('--source', multiple=True, help='Discovery sources to search (local, registry, github)')
@click.option('--limit', type=int, default=20, help='Maximum number of results')
async def discover(query: Optional[str], category: Optional[str], source: List[str], limit: int):
    """
    Discover available plugins from various sources
    
    QUERY: Optional search term to filter results
    
    Examples:
        theodore plugin discover
        theodore plugin discover ai --category ai_provider
        theodore plugin discover search --source github --limit 10
    """
    try:
        console.print("🔍 Discovering plugins from available sources...", style="blue")
        
        # Convert category string to enum
        category_enum = PluginCategory(category) if category else None
        
        # Search plugins
        sources = list(source) if source else None
        plugin_sources = await search_plugins(
            query=query,
            category=category_enum, 
            source_types=sources
        )
        
        if not plugin_sources:
            search_desc = f" matching '{query}'" if query else ""
            category_desc = f" in category '{category}'" if category else ""
            console.print(f"📭 No plugins found{search_desc}{category_desc}.", style="yellow")
            return
        
        # Limit results
        total_found = len(plugin_sources)
        if len(plugin_sources) > limit:
            plugin_sources = plugin_sources[:limit]
        
        table = format_plugin_sources_table(plugin_sources)
        console.print(table)
        
        if total_found > limit:
            console.print(f"\n📋 Showing first {limit} of {total_found} results", style="dim")
            console.print(f"💡 Use --limit {total_found} to see all results", style="blue")
        else:
            console.print(f"\n📊 Found {total_found} plugin source(s)", style="dim")
        
    except Exception as e:
        logger.error(f"Failed to discover plugins: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('source')
@click.option('--force', is_flag=True, help='Force reinstall if already installed')
@click.option('--no-deps', is_flag=True, help='Skip dependency installation')
@click.option('--no-sandbox', is_flag=True, help='Disable sandbox for plugin')
@click.option('--memory-limit', type=int, default=128, help='Memory limit in MB')
@click.option('--cpu-limit', type=int, default=30, help='CPU time limit in seconds')
@click.option('--network', is_flag=True, help='Allow network access')
@click.option('--read-path', multiple=True, help='Allowed read paths')
@click.option('--write-path', multiple=True, help='Allowed write paths')
async def install(source: str, force: bool, no_deps: bool, no_sandbox: bool,
                 memory_limit: int, cpu_limit: int, network: bool,
                 read_path: List[str], write_path: List[str]):
    """
    Install a plugin from various sources
    
    SOURCE: Plugin source (path, URL, or plugin name)
    
    Examples:
        theodore plugin install ./my-plugin.py
        theodore plugin install https://github.com/user/plugin.git
        theodore plugin install plugin-name --memory-limit 256 --network
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        # Create installation options
        options = InstallationOptions(
            force_reinstall=force,
            skip_dependencies=no_deps,
            install_dependencies=not no_deps,
            sandbox_enabled=not no_sandbox,
            memory_limit_mb=memory_limit,
            cpu_limit_seconds=cpu_limit,
            network_access=network,
            file_read_paths=list(read_path),
            file_write_paths=list(write_path)
        )
        
        console.print(f"📦 Installing plugin from: [cyan]{source}[/cyan]")
        
        # Show security settings
        if options.sandbox_enabled:
            console.print(f"🔒 Sandbox enabled (Memory: {memory_limit}MB, CPU: {cpu_limit}s)", style="blue")
            if network:
                console.print("🌐 Network access: [green]Allowed[/green]")
            else:
                console.print("🌐 Network access: [red]Blocked[/red]")
        else:
            console.print("⚠️  [yellow]Sandbox disabled - plugin will run without restrictions[/yellow]")
        
        with console.status("[bold green]Installing plugin..."):
            success = await manager.install_plugin(source, options)
        
        if success:
            console.print("✅ Plugin installed successfully!", style="green")
        else:
            console.print("❌ Plugin installation failed!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to install plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
@click.option('--force', is_flag=True, help='Force uninstall even if other plugins depend on it')
async def uninstall(plugin_id: str, force: bool):
    """
    Uninstall a plugin
    
    PLUGIN_ID: ID or name of the plugin to uninstall
    
    Examples:
        theodore plugin uninstall my-plugin
        theodore plugin uninstall plugin-id --force
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        registry = get_plugin_registry()
        
        # Try to find plugin by ID or name
        metadata = registry.get_plugin(plugin_id)
        if not metadata:
            # Try by name
            metadata = registry.get_plugin_by_name(plugin_id)
        
        if not metadata:
            console.print(f"❌ Plugin not found: {plugin_id}", style="red")
            return
        
        # Check dependencies
        if not force:
            dependents = registry.get_dependents(metadata.plugin_id)
            if dependents:
                dependent_names = [dep.name for dep in dependents]
                console.print(Panel(
                    f"Plugin '[cyan]{metadata.name}[/cyan]' is required by:\n" + 
                    "\n".join(f"• {name}" for name in dependent_names) +
                    "\n\nUse --force to uninstall anyway.",
                    title="⚠️  Dependency Warning",
                    border_style="yellow"
                ))
                if not click.confirm("Continue with uninstallation?"):
                    console.print("Uninstallation cancelled.", style="yellow")
                    return
                force = True
        
        console.print(f"🗑️  Uninstalling plugin: [cyan]{metadata.name}[/cyan] v{metadata.version}")
        
        with console.status("[bold red]Uninstalling plugin..."):
            success = await manager.uninstall_plugin(metadata.plugin_id, force=force)
        
        if success:
            console.print("✅ Plugin uninstalled successfully!", style="green")
        else:
            console.print("❌ Plugin uninstallation failed!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to uninstall plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
async def enable(plugin_id: str):
    """
    Enable a disabled plugin
    
    PLUGIN_ID: ID or name of the plugin to enable
    
    Examples:
        theodore plugin enable my-plugin
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        console.print(f"✅ Enabling plugin: [cyan]{plugin_id}[/cyan]")
        
        success = await manager.enable_plugin(plugin_id)
        
        if success:
            console.print("✅ Plugin enabled successfully!", style="green")
        else:
            console.print("❌ Failed to enable plugin!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to enable plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
async def disable(plugin_id: str):
    """
    Disable an active plugin
    
    PLUGIN_ID: ID or name of the plugin to disable
    
    Examples:
        theodore plugin disable my-plugin
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        console.print(f"⏸️  Disabling plugin: [cyan]{plugin_id}[/cyan]")
        
        success = await manager.disable_plugin(plugin_id)
        
        if success:
            console.print("✅ Plugin disabled successfully!", style="green")
        else:
            console.print("❌ Failed to disable plugin!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to disable plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
async def reload(plugin_id: str):
    """
    Reload a plugin (hot reload)
    
    PLUGIN_ID: ID or name of the plugin to reload
    
    Examples:
        theodore plugin reload my-plugin
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        console.print(f"🔄 Reloading plugin: [cyan]{plugin_id}[/cyan]")
        
        with console.status("[bold blue]Reloading plugin..."):
            success = await manager.reload_plugin(plugin_id)
        
        if success:
            console.print("✅ Plugin reloaded successfully!", style="green")
        else:
            console.print("❌ Failed to reload plugin!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to reload plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
@click.argument('config_file', type=click.Path(exists=True))
async def configure(plugin_id: str, config_file: str):
    """
    Configure a plugin from JSON file
    
    PLUGIN_ID: ID or name of the plugin to configure
    CONFIG_FILE: Path to JSON configuration file
    
    Examples:
        theodore plugin configure my-plugin ./config.json
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        # Load configuration from file
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"❌ Invalid JSON in config file: {e}", style="red")
            return
        
        console.print(f"⚙️  Configuring plugin: [cyan]{plugin_id}[/cyan]")
        console.print(f"📄 Config file: [blue]{config_file}[/blue]")
        
        success = await manager.configure_plugin(plugin_id, config)
        
        if success:
            console.print("✅ Plugin configured successfully!", style="green")
        else:
            console.print("❌ Failed to configure plugin!", style="red")
        
    except Exception as e:
        logger.error(f"Failed to configure plugin: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
async def health(plugin_id: str):
    """
    Check plugin health status
    
    PLUGIN_ID: ID or name of the plugin to check
    
    Examples:
        theodore plugin health my-plugin
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        
        health_info = await manager.get_plugin_health(plugin_id)
        
        if not health_info:
            console.print(f"❌ Plugin not found or not loaded: {plugin_id}", style="red")
            return
        
        console.print(Panel(
            json.dumps(health_info, indent=2),
            title=f"🏥 Health Status: {plugin_id}",
            border_style="green"
        ))
        
    except Exception as e:
        logger.error(f"Failed to get plugin health: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
@click.argument('plugin_id')
async def info(plugin_id: str):
    """
    Show detailed information about a plugin
    
    PLUGIN_ID: ID or name of the plugin to inspect
    
    Examples:
        theodore plugin info my-plugin
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        registry = get_plugin_registry()
        manager = get_plugin_manager()
        
        # Try to find plugin by ID or name
        metadata = registry.get_plugin(plugin_id)
        if not metadata:
            metadata = registry.get_plugin_by_name(plugin_id)
        
        if not metadata:
            console.print(f"❌ Plugin not found: {plugin_id}", style="red")
            return
        
        # Create info display
        info_text = Text()
        info_text.append(f"ID: ", style="cyan")
        info_text.append(f"{metadata.plugin_id}\n")
        info_text.append(f"Name: ", style="cyan")
        info_text.append(f"{metadata.name}\n", style="bold")
        info_text.append(f"Version: ", style="cyan")
        info_text.append(f"{metadata.version}\n")
        info_text.append(f"Author: ", style="cyan")
        info_text.append(f"{metadata.author}\n")
        info_text.append(f"Category: ", style="cyan")
        info_text.append(f"{metadata.category.value}\n", style="blue")
        info_text.append(f"Status: ", style="cyan")
        
        status = metadata.status.value
        if status == "enabled":
            info_text.append("✅ enabled\n", style="green")
        elif status == "disabled":
            info_text.append("⏸️ disabled\n", style="yellow")
        elif status == "installed":
            info_text.append("📦 installed\n", style="blue")
        else:
            info_text.append(f"{status}\n")
        
        info_text.append(f"Description: ", style="cyan")
        info_text.append(f"{metadata.description}\n")
        
        if metadata.tags:
            info_text.append(f"Tags: ", style="cyan")
            info_text.append(f"{', '.join(metadata.tags)}\n", style="magenta")
        
        if metadata.module_path:
            info_text.append(f"Module Path: ", style="cyan")
            info_text.append(f"{metadata.module_path}\n", style="dim")
        
        console.print(Panel(
            info_text,
            title=f"📋 Plugin Information: {metadata.name}",
            border_style="blue"
        ))
        
        # Dependencies
        if metadata.compatibility.dependencies:
            dep_table = Table(title="📦 Dependencies")
            dep_table.add_column("Name", style="cyan")
            dep_table.add_column("Version", style="magenta")
            dep_table.add_column("Status", justify="center")
            
            for dep in metadata.compatibility.dependencies:
                status = "[green]required[/green]" if not dep.optional else "[yellow]optional[/yellow]"
                dep_table.add_row(dep.name, dep.version, status)
            
            console.print(dep_table)
        
        # Runtime info
        instance = registry.get_plugin_instance(metadata.plugin_id)
        if instance:
            console.print("🚀 [green]Runtime Status: Loaded and available[/green]")
            
            # Configuration
            config = manager.get_plugin_config(metadata.plugin_id)
            if config:
                console.print(Panel(
                    json.dumps(config, indent=2),
                    title="⚙️ Configuration",
                    border_style="yellow"
                ))
        else:
            console.print("💤 [dim]Runtime Status: Not loaded[/dim]")
        
        # Dependencies and dependents
        dependencies = registry.get_dependencies(metadata.plugin_id)
        dependents = registry.get_dependents(metadata.plugin_id)
        
        if dependencies or dependents:
            if dependencies:
                console.print("\n⬇️  [cyan]Depends on:[/cyan]")
                for dep in dependencies:
                    console.print(f"  • {dep.name} v{dep.version}")
            
            if dependents:
                console.print("\n⬆️  [cyan]Required by:[/cyan]")
                for dep in dependents:
                    console.print(f"  • {dep.name} v{dep.version}")
        
    except Exception as e:
        logger.error(f"Failed to get plugin info: {e}")
        console.print(f"❌ Error: {e}", style="red")


@plugin_group.command()
async def stats():
    """
    Show plugin system statistics
    
    Examples:
        theodore plugin stats
    """
    try:
        if not await initialize_plugin_system():
            console.print("❌ Failed to initialize plugin system", style="red")
            return
        
        manager = get_plugin_manager()
        stats = manager.get_manager_stats()
        
        # Main stats
        registry_stats = stats.get('registry', {})
        
        stats_text = Text()
        stats_text.append("Total Plugins: ", style="cyan")
        stats_text.append(f"{registry_stats.get('total_plugins', 0)}\n", style="bold green")
        stats_text.append("Loaded Plugins: ", style="cyan")
        stats_text.append(f"{stats.get('loaded_plugins', 0)}\n", style="bold blue")
        stats_text.append("Configurations: ", style="cyan")
        stats_text.append(f"{stats.get('configurations', 0)}\n", style="bold yellow")
        stats_text.append("Sandboxes: ", style="cyan")
        stats_text.append(f"{stats.get('sandboxes', 0)}\n", style="bold magenta")
        
        console.print(Panel(
            stats_text,
            title="📊 Plugin System Statistics",
            border_style="green"
        ))
        
        # Category breakdown
        by_category = registry_stats.get('by_category', {})
        if by_category:
            cat_table = Table(title="📂 Plugins by Category")
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Count", justify="right", style="green")
            
            for category, count in by_category.items():
                cat_table.add_row(category, str(count))
            
            console.print(cat_table)
        
        # Status breakdown
        by_status = registry_stats.get('by_status', {})
        if by_status:
            status_table = Table(title="📈 Plugins by Status")
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Count", justify="right", style="green")
            
            for status, count in by_status.items():
                if status == "enabled":
                    status_display = "[green]✅ enabled[/green]"
                elif status == "disabled":
                    status_display = "[yellow]⏸️ disabled[/yellow]"
                elif status == "installed":
                    status_display = "[blue]📦 installed[/blue]"
                else:
                    status_display = status
                
                status_table.add_row(status_display, str(count))
            
            console.print(status_table)
        
        # Directory info
        dir_text = Text()
        dir_text.append("Plugins Directory: ", style="cyan")
        dir_text.append(f"{stats.get('plugins_directory')}\n", style="dim")
        dir_text.append("Config Directory: ", style="cyan")
        dir_text.append(f"{stats.get('config_directory')}", style="dim")
        
        console.print(Panel(
            dir_text,
            title="📁 Directories",
            border_style="blue"
        ))
        
    except Exception as e:
        logger.error(f"Failed to get plugin stats: {e}")
        console.print(f"❌ Error: {e}", style="red")


# Convert async commands to sync for Click compatibility
def async_command(f):
    """Decorator to make async commands work with Click"""
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


# Apply decorator to all async commands
list = async_command(list)
search = async_command(search)
discover = async_command(discover)
install = async_command(install)
uninstall = async_command(uninstall)
enable = async_command(enable)
disable = async_command(disable)
reload = async_command(reload)
configure = async_command(configure)
health = async_command(health)
info = async_command(info)
stats = async_command(stats)
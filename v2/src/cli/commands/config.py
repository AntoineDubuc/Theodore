"""
Configuration command group for Theodore CLI.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

from src.infrastructure.config.settings import TheodoreSettings, settings
from src.infrastructure.config.secure_storage import SecureStorage, ensure_keyring_setup
from src.infrastructure.config.validators import ConfigValidator

console = Console()

@click.group(name='config')
def config_group():
    """Manage Theodore configuration settings"""
    pass

@config_group.command()
@click.option('--include-sensitive', is_flag=True, help='Show API keys (masked)')
@click.pass_context
def show(ctx, include_sensitive: bool):
    """
    Show current configuration settings
    
    Examples:
        theodore config show
        theodore config show --include-sensitive
    """
    
    console.print("[bold blue]⚙️  Theodore Configuration[/bold blue]")
    
    # Get current configuration
    config_dict = settings.to_safe_dict()
    
    # Organize settings by category
    config_sections = {
        "Environment": {
            "Environment": str(config_dict.get('environment', 'N/A')),
            "Debug Mode": str(config_dict.get('debug', False)),
            "Log Level": str(config_dict.get('log_level', 'INFO')),
            "Verbose": str(config_dict.get('verbose', False))
        },
        "AI Providers": {
            "Gemini Model": config_dict.get('gemini_model', 'N/A'),
            "Bedrock Model": config_dict.get('bedrock_analysis_model', 'N/A'),
            "OpenAI Model": config_dict.get('openai_model', 'N/A'),
            "AWS Region": config_dict.get('aws_region', 'N/A')
        },
        "Vector Storage": {
            "Pinecone Index": config_dict.get('pinecone_index_name', 'N/A'),
            "Environment": config_dict.get('pinecone_environment', 'N/A')
        },
        "Research Settings": {
            "Max Pages": str(config_dict.get('research', {}).get('max_pages_per_company', 'N/A')),
            "Timeout": f"{config_dict.get('research', {}).get('timeout_seconds', 'N/A')}s",
            "Parallel Requests": str(config_dict.get('research', {}).get('parallel_requests', 'N/A')),
            "JavaScript": str(config_dict.get('research', {}).get('enable_javascript', 'N/A'))
        },
        "Output": {
            "Default Format": config_dict.get('default_output_format', 'N/A'),
            "Colors": str(config_dict.get('colored_output', True)),
            "Progress Bars": str(config_dict.get('progress_bars', True))
        }
    }
    
    # Add credentials section if requested
    if include_sensitive:
        stored_creds = SecureStorage.export_credentials_to_dict(mask_values=True)
        config_sections["API Keys (Masked)"] = stored_creds
    
    for section, section_settings in config_sections.items():
        table = Table(title=section)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in section_settings.items():
            table.add_row(key, str(value))
        
        console.print(table)
        console.print()

@config_group.command()
@click.argument('key')
@click.argument('value')
@click.option('--secure', is_flag=True, help='Store in secure keyring storage')
@click.pass_context
def set(ctx, key: str, value: str, secure: bool):
    """
    Set a configuration value
    
    KEY: Configuration key (e.g., 'gemini_api_key', 'research.timeout_seconds')
    VALUE: Configuration value
    
    Examples:
        theodore config set gemini_api_key "AIza..." --secure
        theodore config set research.timeout_seconds 60
        theodore config set default_output_format json
    """
    
    # Handle secure storage for API keys
    if secure or key.endswith('_api_key') or key.endswith('_access_key'):
        if ensure_keyring_setup():
            success = SecureStorage.store_credential(key, value)
            if success:
                console.print(f"[green]✅ Stored securely:[/green] {key}")
            else:
                console.print(f"[red]❌ Failed to store securely:[/red] {key}")
                return
        else:
            console.print("[red]❌ Keyring not available for secure storage[/red]")
            return
    else:
        # Handle regular configuration file updates
        config_file = settings.get_config_file_path()
        settings.ensure_config_dir()
        
        # Load existing config or create new
        config_data = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Handle nested keys (e.g., research.timeout_seconds)
        keys = key.split('.')
        current = config_data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value with type conversion
        final_key = keys[-1]
        try:
            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                current[final_key] = value.lower() == 'true'
            elif value.isdigit():
                current[final_key] = int(value)
            elif value.replace('.', '').isdigit():
                current[final_key] = float(value)
            else:
                current[final_key] = value
        except:
            current[final_key] = value
        
        # Save configuration
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        console.print(f"[green]✅ Set configuration:[/green] {key} = {value}")
        console.print(f"[dim]Saved to {config_file}[/dim]")

@config_group.command()
@click.argument('key')
@click.option('--show-source', is_flag=True, help='Show configuration source')
@click.pass_context
def get(ctx, key: str, show_source: bool):
    """
    Get a configuration value
    
    KEY: Configuration key to retrieve
    
    Examples:
        theodore config get gemini_model
        theodore config get research.timeout_seconds --show-source
    """
    
    # Check secure storage first for API keys
    if key.endswith('_api_key') or key.endswith('_access_key'):
        value = SecureStorage.get_credential(key)
        source = "keyring" if value else "not found"
        if value:
            # Mask the value for display
            display_value = f"{value[:8]}***" if len(value) > 8 else "***"
            console.print(f"[cyan]{key}[/cyan]: [green]{display_value}[/green]")
        else:
            console.print(f"[cyan]{key}[/cyan]: [red]Not set[/red]")
    else:
        # Get from regular settings
        config_dict = settings.model_dump()
        
        # Handle nested keys
        keys = key.split('.')
        current = config_dict
        source = "settings"
        
        try:
            for k in keys:
                current = current[k]
            
            console.print(f"[cyan]{key}[/cyan]: [green]{current}[/green]")
        except (KeyError, TypeError):
            console.print(f"[cyan]{key}[/cyan]: [red]Not found[/red]")
            source = "not found"
    
    if show_source:
        console.print(f"[dim]Source: {source}[/dim]")

@config_group.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.option('--keep-credentials', is_flag=True, help='Keep API keys in secure storage')
@click.pass_context
def reset(ctx, confirm: bool, keep_credentials: bool):
    """
    Reset configuration to defaults
    
    Examples:
        theodore config reset --confirm
        theodore config reset --keep-credentials
    """
    
    if not confirm:
        if not Confirm.ask("This will reset all configuration to defaults. Continue?"):
            console.print("[yellow]Reset cancelled[/yellow]")
            return
    
    # Remove configuration file
    config_file = settings.get_config_file_path()
    if config_file.exists():
        config_file.unlink()
        console.print(f"[green]✅ Removed configuration file:[/green] {config_file}")
    
    # Clear secure storage unless keeping credentials
    if not keep_credentials:
        if SecureStorage.clear_all_credentials():
            console.print("[green]✅ Cleared all stored credentials[/green]")
        else:
            console.print("[yellow]⚠️  Some credentials may not have been cleared[/yellow]")
    else:
        console.print("[blue]ℹ️  Kept stored credentials[/blue]")
    
    console.print("[green]✅ Configuration reset to defaults[/green]")

@config_group.command()
@click.pass_context
def validate(ctx):
    """
    Validate current configuration and API connections
    
    Examples:
        theodore config validate
    """
    
    console.print("[bold blue]🔍 Validating Theodore configuration...[/bold blue]")
    
    # Get current configuration
    config_dict = settings.model_dump()
    
    # Perform comprehensive validation
    is_valid, issues = ConfigValidator.validate_complete_config(config_dict)
    
    # Check keyring access
    keyring_ok = SecureStorage.validate_keyring_access()
    keyring_info = SecureStorage.get_keyring_backend_info()
    
    # Create validation table
    table = Table(title="Configuration Validation")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    
    # Overall status
    overall_status = "✅ Valid" if is_valid else "❌ Invalid"
    table.add_row("Overall Configuration", overall_status)
    
    # Keyring status
    keyring_status = "✅ Working" if keyring_ok else "❌ Failed"
    table.add_row("Secure Storage", f"{keyring_status} ({keyring_info.get('backend_name', 'unknown')})")
    
    # Required credentials
    missing_creds = settings.get_missing_credentials()
    creds_status = "✅ Complete" if not missing_creds else f"❌ Missing: {', '.join(missing_creds)}"
    table.add_row("Required Credentials", creds_status)
    
    # Production readiness
    prod_ready = settings.is_production_ready()
    prod_status = "✅ Ready" if prod_ready else "⚠️  Development mode"
    table.add_row("Production Ready", prod_status)
    
    console.print(table)
    
    # Show detailed issues if any
    if issues:
        console.print("\n[bold red]Validation Issues:[/bold red]")
        for issue in issues:
            if issue.startswith("ERROR:"):
                console.print(f"[red]• {issue}[/red]")
            elif issue.startswith("WARNING:"):
                console.print(f"[yellow]• {issue}[/yellow]")
            else:
                console.print(f"[blue]• {issue}[/blue]")
    else:
        console.print("\n[green]✅ No validation issues found[/green]")

@config_group.command()
@click.option('--output', '-o', help='Output file path (default: ~/.theodore/config.yml)')
@click.option('--force', is_flag=True, help='Overwrite existing file')
@click.pass_context
def init(ctx, output: Optional[str], force: bool):
    """
    Initialize Theodore configuration with template
    
    Examples:
        theodore config init
        theodore config init --output ./my-config.yml --force
    """
    
    # Determine output path
    if output:
        config_path = Path(output)
    else:
        config_path = settings.get_config_file_path()
        settings.ensure_config_dir()
    
    # Check if file exists
    if config_path.exists() and not force:
        if not Confirm.ask(f"Configuration file exists at {config_path}. Overwrite?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    # Generate and write template
    template = ConfigValidator.generate_config_template()
    
    try:
        with open(config_path, 'w') as f:
            f.write(template)
        
        console.print(f"[green]✅ Configuration template created:[/green] {config_path}")
        console.print("\n[blue]Next steps:[/blue]")
        console.print("1. Edit the configuration file with your API keys")
        console.print("2. Run 'theodore config set <key> <value> --secure' for API keys")
        console.print("3. Run 'theodore config validate' to check your setup")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create configuration:[/red] {e}")
"""
Theodore v2 CLI application main entry point.
"""

import click
from rich.console import Console
from rich.text import Text
import sys
from typing import Optional

# Import implemented command groups - temporarily commented out to fix circular imports
# from .commands.research import research_group
# from .commands.discover import discover_command
# from .commands.batch import batch
# from .commands.config import config_group
# from .commands.export import export_group
# from .commands.plugin import plugin_group

console = Console()

@click.group()
@click.version_option(
    version="2.0.0",
    prog_name="Theodore AI Company Intelligence",
    message="%(prog)s version %(version)s"
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--config-file',
    type=click.Path(exists=True),
    help='Path to configuration file'
)
@click.pass_context
def cli(ctx, verbose: bool, config_file: Optional[str]):
    """
    Theodore AI Company Intelligence System
    
    Research companies, discover similar businesses, and export insights
    using AI-powered analysis and MCP search tools.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config_file
    
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")

# Add implemented command groups to the main CLI - temporarily commented out
# cli.add_command(research_group)
# cli.add_command(discover_command, name="discover")
# cli.add_command(batch)
# cli.add_command(config_group)
# cli.add_command(export_group)
# cli.add_command(plugin_group)

# Add a simple test command to verify CLI is working
@cli.command()
def test():
    """Test command to verify CLI functionality."""
    console.print("✅ [green]Theodore v2 CLI is working![/green]")
    console.print("🏗️ [yellow]Full commands temporarily disabled to fix import issues[/yellow]")

# Error handling
@cli.result_callback()
def process_result(result, **kwargs):
    """Process the final result of CLI execution"""
    if result is None:
        return
    
    # Handle any final processing
    pass

# Custom error handler
def handle_cli_error(exception):
    """Handle CLI errors gracefully"""
    if isinstance(exception, click.ClickException):
        exception.show()
        sys.exit(exception.exit_code)
    
    # For unexpected errors, show a friendly message
    console.print(f"[red]Error:[/red] {str(exception)}")
    console.print("[dim]Use --verbose for more details[/dim]")
    sys.exit(1)

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        handle_cli_error(e)
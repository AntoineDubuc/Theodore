"""
CLI Research Command Implementation for Theodore v2.

This module provides the comprehensive `theodore research` command with
real-time progress tracking, multiple output formats, and graceful error handling.
"""

import asyncio
import json
import yaml
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich import box

from src.infrastructure.container.application import ApplicationContainer
from src.core.domain.entities.company import Company
from src.core.ports.progress import ProgressCallback
from src.cli.utils.formatters import FormatterFactory
from src.cli.utils.error_handler import CLIErrorHandler, ErrorContext, cli_error_context


console = Console()


class ResearchSession:
    """Manages a research session with progress tracking and cleanup"""
    
    def __init__(self, container: ApplicationContainer):
        self.container = container
        self.research_use_case = None
        self.progress_tracker = None
        self.cancelled = False
        self.current_task_id = None
        
    async def __aenter__(self):
        """Initialize research session"""
        self.research_use_case = await self.container.use_cases.research_company()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up research session"""
        if self.research_use_case:
            await self.research_use_case.cleanup()
        if self.progress_tracker:
            await self.progress_tracker.close()
    
    def handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.cancelled = True
        console.print("\n[yellow]⚠️  Research cancelled by user. Cleaning up...[/yellow]")
        if self.current_task_id and self.progress_tracker:
            asyncio.create_task(
                self.progress_tracker.fail(
                    self.current_task_id, 
                    KeyboardInterrupt("User cancelled operation"),
                    "Operation cancelled by user"
                )
            )


class ResearchProgressDisplay:
    """Manages rich progress display for research operations"""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            expand=True
        )
        self.tasks = {}
        self.live = None
        
    async def __aenter__(self):
        self.live = Live(self.progress, console=console, refresh_per_second=10)
        self.live.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.live:
            self.live.stop()
    
    def create_progress_callback(self) -> ProgressCallback:
        """Create progress callback for use cases"""
        def callback(phase: str, progress_pct: float, message: str):
            if phase not in self.tasks:
                self.tasks[phase] = self.progress.add_task(
                    description=f"[cyan]{phase}[/cyan]",
                    total=100
                )
            
            self.progress.update(
                self.tasks[phase],
                completed=progress_pct,
                description=f"[cyan]{phase}[/cyan]: {message}"
            )
        
        return callback


@click.command()
@click.argument('company_name')
@click.argument('website', required=False)
@click.option(
    '--output', '-o',
    type=click.Choice(['table', 'json', 'yaml', 'markdown'], case_sensitive=False),
    default='table',
    help='Output format [default: table]'
)
@click.option(
    '--no-domain-discovery',
    is_flag=True,
    help='Skip automatic domain discovery'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--timeout',
    type=int,
    default=60,
    help='Timeout in seconds [default: 60]'
)
@click.option(
    '--save',
    type=click.Path(),
    help='Save results to file'
)
@click.option(
    '--config-override',
    multiple=True,
    help='Override configuration (key=value)'
)
@click.pass_context
async def research(
    ctx,
    company_name: str,
    website: Optional[str],
    output: str,
    no_domain_discovery: bool,
    verbose: bool,
    timeout: int,
    save: Optional[str],
    config_override: tuple
):
    """
    Research a company using AI-powered analysis.
    
    COMPANY_NAME: Name of the company to research
    WEBSITE: Optional company website URL
    
    Examples:
        theodore research "Apple Inc" "apple.com"
        theodore research "Salesforce" --output json --save results.json
        theodore research "Unknown Startup" --no-domain-discovery --verbose
    """
    
    # Parse configuration overrides
    config_overrides = {}
    for override in config_override:
        try:
            key, value = override.split('=', 1)
            config_overrides[key.strip()] = value.strip()
        except ValueError:
            console.print(f"[red]❌ Invalid config override format: {override}[/red]")
            console.print("[dim]Use format: key=value[/dim]")
            raise click.Abort()
    
    if verbose:
        console.print(f"[dim]📊 Starting research for: {company_name}[/dim]")
        if website:
            console.print(f"[dim]🌐 Website: {website}[/dim]")
        if config_overrides:
            console.print(f"[dim]⚙️  Config overrides: {config_overrides}[/dim]")
    
    try:
        # Create DI container
        from src.infrastructure.container import ContainerFactory
        container = ContainerFactory.create_cli_container()
        
        async with ResearchSession(container) as session:
            # Set up signal handling for graceful shutdown
            signal.signal(signal.SIGINT, session.handle_interrupt)
            
            async with ResearchProgressDisplay() as progress_display:
                # Create progress callback
                progress_callback = progress_display.create_progress_callback()
                
                # Configure research parameters
                research_config = {
                    'enable_domain_discovery': not no_domain_discovery,
                    'timeout': timeout,
                    'verbose': verbose,
                    **config_overrides
                }
                
                try:
                    # Execute research
                    session.current_task_id = f"research_{company_name}_{datetime.now().isoformat()}"
                    
                    company_data = await session.research_use_case.research_company(
                        company_name=company_name,
                        website_url=website,
                        config=research_config,
                        progress_callback=progress_callback
                    )
                    
                    if session.cancelled:
                        console.print("[yellow]⚠️  Research was cancelled[/yellow]")
                        raise click.Abort()
                    
                    # Display results using formatter
                    results = _convert_company_to_dict(company_data)
                    FormatterFactory.format_and_display(
                        data=results,
                        format_type=output,
                        save_path=save,
                        verbose=verbose
                    )
                    
                    console.print(f"\n[green]✅ Research completed for {company_name}[/green]")
                    
                except asyncio.TimeoutError:
                    console.print(f"[red]⏰ Research timed out after {timeout} seconds[/red]")
                    console.print("[dim]Try increasing timeout with --timeout option[/dim]")
                    raise click.Abort()
                    
                except Exception as e:
                    await _handle_research_error(e, company_name, verbose)
                    raise click.Abort()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Research interrupted by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def _convert_company_to_dict(company_data: Company) -> Dict[str, Any]:
    """Convert Company object to dictionary for display"""
    
    results = {
        'company_name': company_data.name,
        'website': company_data.website_url,
        'industry': company_data.industry,
        'description': company_data.description,
        'founding_year': company_data.founding_year,
        'location': company_data.location,
        'employee_count': company_data.employee_count,
        'revenue_range': company_data.revenue_range,
        'business_model': company_data.business_model,
        'research_timestamp': datetime.now().isoformat(),
        'research_confidence': getattr(company_data, 'confidence_score', None)
    }
    
    # Remove None values for cleaner output
    return {k: v for k, v in results.items() if v is not None}


async def _handle_research_error(error: Exception, company_name: str, verbose: bool) -> None:
    """Handle and display research errors with helpful suggestions"""
    
    error_handler = CLIErrorHandler(verbose=verbose)
    context = ErrorContext(operation="research", entity=company_name)
    error_handler.handle_error(error, context, show_suggestions=True)


# Command group for research operations
@click.group(name='research')
def research_group():
    """Research companies using AI-powered analysis"""
    pass


# Add the main research command to the group
research_group.add_command(research)


# Additional research commands for future implementation
@research_group.command()
@click.argument('companies_file', type=click.Path(exists=True))
@click.option('--output-dir', type=click.Path(), default='./results')
@click.option('--parallel', type=int, default=3)
def batch(companies_file: str, output_dir: str, parallel: int):
    """Research multiple companies from a file (Future: TICKET-022)"""
    console.print("[yellow]⚠️  Batch research will be implemented in TICKET-022[/yellow]")
    console.print(f"[dim]Would process: {companies_file} with {parallel} parallel jobs[/dim]")


@research_group.command()
@click.option('--format', type=click.Choice(['table', 'json']))
def history(format: str):
    """Show research history (Future: TICKET-023)"""
    console.print("[yellow]⚠️  Research history will be implemented in TICKET-023[/yellow]")


if __name__ == "__main__":
    # Support running as standalone module
    asyncio.run(research())
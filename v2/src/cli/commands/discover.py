"""
Theodore CLI Discover Command - Advanced Company Discovery Interface.

Provides sophisticated company discovery with multi-dimensional filtering,
similarity scoring explanations, and interactive research workflows.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json
import yaml

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.core.domain.entities.company import Company, BusinessModel, CompanySize, CompanyStage
from src.core.use_cases.discover_similar import DiscoverSimilarCompaniesUseCase
from src.core.domain.value_objects.similarity_result import (
    DiscoveryRequest,
    DiscoveryResult,
    DiscoverySource,
    CompanyMatch
)
from src.infrastructure.container.application import ApplicationContainer as Container
from src.cli.utils.output import OutputFormat, format_company_data
from src.cli.utils.validation import validate_company_name


console = Console()


class DiscoveryCommand:
    """
    Advanced company discovery command with intelligent filtering,
    similarity scoring, and interactive research capabilities.
    """
    
    def __init__(self, container: Container):
        self.container = container
        self.discover_use_case = container.get_discovery_use_case()
        
    async def execute(
        self,
        company_name: str,
        limit: int = 10,
        output: OutputFormat = OutputFormat.TABLE,
        business_model: Optional[str] = None,
        company_size: Optional[str] = None,
        industry: Optional[str] = None,
        growth_stage: Optional[str] = None,
        location: Optional[str] = None,
        similarity_threshold: float = 0.6,
        source: str = "hybrid",
        interactive: bool = False,
        research_discovered: bool = False,
        save: Optional[str] = None,
        cache_results: bool = True,
        explain_similarity: bool = False,
        verbose: bool = False,
        timeout: int = 45,
        **kwargs
    ) -> None:
        """
        Execute the discovery command with advanced filtering and options.
        """
        start_time = time.time()
        
        try:
            # Validate and normalize inputs
            company_name = validate_company_name(company_name)
            if not company_name:
                console.print("❌ [red]Invalid company name provided[/red]")
                return
            
            if verbose:
                console.print(f"🔍 [blue]Starting discovery for:[/blue] {company_name}")
                console.print(f"🎯 [blue]Source:[/blue] {source}")
                console.print(f"📊 [blue]Limit:[/blue] {limit}")
            
            # Create discovery request
            discovery_request = DiscoveryRequest(
                company_name=company_name,
                max_results=limit,
                min_similarity_score=similarity_threshold,
                industry_filter=industry,
                business_model_filter=business_model,
                location_filter=location,
                size_filter=company_size,
                include_database_search=(source in ["hybrid", "vector"]),
                include_web_discovery=(source in ["hybrid", "web"]),
                enable_parallel_search=True
            )
            
            # Execute discovery with progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
                
                task = progress.add_task("Discovering similar companies...", total=100)
                
                # Execute discovery
                discovery_result = await asyncio.wait_for(
                    self.discover_use_case.execute(discovery_request),
                    timeout=timeout
                )
                
                progress.update(task, description="Discovery completed!", completed=100)
            
            # Handle the discovery result
            await self._handle_discovery_result(
                discovery_result, output, explain_similarity, save, interactive, research_discovered
            )
            
            # Print performance summary
            elapsed_time = time.time() - start_time
            if verbose:
                console.print(f"\n✅ [green]Discovery completed in {elapsed_time:.2f}s[/green]")
                console.print(f"📊 [blue]Found {len(discovery_result.matches)} similar companies[/blue]")
                
        except asyncio.TimeoutError:
            console.print(f"⏰ [red]Discovery timed out after {timeout} seconds[/red]")
        except Exception as e:
            console.print(f"❌ [red]Discovery failed: {str(e)}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    async def _handle_discovery_result(
        self,
        discovery_result: DiscoveryResult,
        output: OutputFormat,
        explain_similarity: bool,
        save: Optional[str],
        interactive: bool,
        research_discovered: bool
    ) -> None:
        """Handle and display discovery results based on output format and options."""
        
        if not discovery_result.matches:
            console.print("📭 [yellow]No similar companies found with current filters[/yellow]")
            console.print("💡 [blue]Try adjusting your similarity threshold or filters[/blue]")
            return
        
        # Handle interactive mode
        if interactive:
            await self._handle_interactive_mode(discovery_result, research_discovered)
            return
        
        # Format and display results
        await self._display_results(discovery_result, output, explain_similarity)
        
        # Auto-research if requested
        if research_discovered:
            await self._auto_research_companies(discovery_result.matches)
        
        # Save results if requested
        if save:
            await self._save_results(discovery_result, save, output)
    
    async def _display_results(
        self,
        discovery_result: DiscoveryResult,
        output: OutputFormat,
        explain_similarity: bool
    ) -> None:
        """Display discovery results in the specified format."""
        
        if output == OutputFormat.TABLE:
            await self._display_table_results(discovery_result, explain_similarity)
        elif output == OutputFormat.JSON:
            await self._display_json_results(discovery_result)
        elif output == OutputFormat.YAML:
            await self._display_yaml_results(discovery_result)
        elif output == OutputFormat.MARKDOWN:
            await self._display_markdown_results(discovery_result, explain_similarity)
        else:
            console.print(f"❌ [red]Unsupported output format: {output}[/red]")
    
    async def _display_table_results(
        self,
        discovery_result: DiscoveryResult,
        explain_similarity: bool
    ) -> None:
        """Display results in rich table format."""
        
        # Create summary panel
        summary_text = Text()
        summary_text.append(f"🎯 Target: ", style="bold blue")
        summary_text.append(f"{discovery_result.query_company}\n")
        summary_text.append(f"📊 Found: ", style="bold blue")
        summary_text.append(f"{len(discovery_result.matches)} similar companies\n")
        summary_text.append(f"⚡ Strategy: ", style="bold blue")
        summary_text.append(f"{discovery_result.search_strategy}\n")
        summary_text.append(f"⏱️ Time: ", style="bold blue")
        summary_text.append(f"{discovery_result.execution_time_seconds:.2f}s")
        
        console.print(Panel(summary_text, title="Discovery Summary", border_style="blue"))
        
        # Create results table
        table = Table(
            title="🔍 Similar Companies",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("Rank", style="bold white", width=4, justify="center")
        table.add_column("Company", style="bold green", min_width=20)
        table.add_column("Similarity", style="bold yellow", width=12, justify="center")
        table.add_column("Source", style="cyan", width=15)
        table.add_column("Website", style="dim blue", min_width=15)
        
        if explain_similarity:
            table.add_column("Description", style="white", min_width=20)
        
        # Sort matches by similarity score
        sorted_matches = sorted(
            discovery_result.matches,
            key=lambda m: m.similarity_score * m.confidence_score,
            reverse=True
        )
        
        for rank, match in enumerate(sorted_matches, 1):
            # Format similarity score with visual indicator
            score = match.similarity_score
            if score >= 0.8:
                score_display = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                score_display = f"[yellow]{score:.2f}[/yellow]"
            else:
                score_display = f"[red]{score:.2f}[/red]"
            
            # Format source
            source_display = match.source.value.replace('_', ' ').title()
            
            # Prepare row data
            row_data = [
                str(rank),
                match.company_name,
                score_display,
                source_display,
                match.domain or "N/A"
            ]
            
            if explain_similarity:
                description = match.description or "No description available"
                if len(description) > 50:
                    description = description[:47] + "..."
                row_data.append(description)
            
            table.add_row(*row_data)
        
        console.print(table)
        
        # Display discovery metrics
        if discovery_result.matches:
            metrics_text = Text()
            metrics_text.append(f"📈 Avg Confidence: ", style="bold")
            metrics_text.append(f"{discovery_result.average_confidence:.2f}\n", style="green")
            metrics_text.append(f"📊 Coverage Score: ", style="bold")
            metrics_text.append(f"{discovery_result.coverage_score:.2f}\n", style="cyan")
            metrics_text.append(f"🔄 Sources Used: ", style="bold")
            metrics_text.append(f"{discovery_result.total_sources_used}", style="white")
            
            console.print(Panel(metrics_text, title="Discovery Metrics", border_style="green"))
    
    async def _display_json_results(self, discovery_result: DiscoveryResult) -> None:
        """Display results in JSON format."""
        # Convert CompanyMatch objects to dictionaries
        matches_data = []
        for match in discovery_result.matches:
            match_data = {
                'company_name': match.company_name,
                'domain': match.domain,
                'description': match.description,
                'industry': match.industry,
                'business_model': match.business_model,
                'employee_count': match.employee_count,
                'location': match.location,
                'similarity_score': match.similarity_score,
                'confidence_score': match.confidence_score,
                'source': match.source.value
            }
            matches_data.append(match_data)
        
        data = {
            'query_company': discovery_result.query_company,
            'search_strategy': discovery_result.search_strategy,
            'total_matches': discovery_result.total_matches,
            'execution_time_seconds': discovery_result.execution_time_seconds,
            'average_confidence': discovery_result.average_confidence,
            'coverage_score': discovery_result.coverage_score,
            'matches': matches_data
        }
        
        console.print(json.dumps(data, indent=2, default=str))
    
    async def _display_yaml_results(self, discovery_result: DiscoveryResult) -> None:
        """Display results in YAML format."""
        # Convert to dictionary (same as JSON)
        matches_data = []
        for match in discovery_result.matches:
            match_data = {
                'company_name': match.company_name,
                'domain': match.domain,
                'description': match.description,
                'industry': match.industry,
                'business_model': match.business_model,
                'employee_count': match.employee_count,
                'location': match.location,
                'similarity_score': match.similarity_score,
                'confidence_score': match.confidence_score,
                'source': match.source.value
            }
            matches_data.append(match_data)
        
        data = {
            'query_company': discovery_result.query_company,
            'search_strategy': discovery_result.search_strategy,
            'total_matches': discovery_result.total_matches,
            'execution_time_seconds': discovery_result.execution_time_seconds,
            'average_confidence': discovery_result.average_confidence,
            'coverage_score': discovery_result.coverage_score,
            'matches': matches_data
        }
        
        console.print(yaml.dump(data, default_flow_style=False))
    
    async def _display_markdown_results(
        self,
        discovery_result: DiscoveryResult,
        explain_similarity: bool
    ) -> None:
        """Display results in Markdown format."""
        
        output = []
        output.append(f"# Company Discovery Results")
        output.append(f"")
        output.append(f"**Target Company:** {discovery_result.query_company}")
        output.append(f"**Companies Found:** {len(discovery_result.matches)}")
        output.append(f"**Search Strategy:** {discovery_result.search_strategy}")
        output.append(f"**Execution Time:** {discovery_result.execution_time_seconds:.2f}s")
        output.append(f"")
        output.append(f"## Similar Companies")
        output.append(f"")
        
        sorted_matches = sorted(
            discovery_result.matches,
            key=lambda m: m.similarity_score * m.confidence_score,
            reverse=True
        )
        
        for i, match in enumerate(sorted_matches, 1):
            output.append(f"### {i}. {match.company_name}")
            output.append(f"")
            output.append(f"- **Website:** {match.domain or 'N/A'}")
            output.append(f"- **Similarity Score:** {match.similarity_score:.2f}")
            output.append(f"- **Source:** {match.source.value}")
            if match.industry:
                output.append(f"- **Industry:** {match.industry}")
            if match.location:
                output.append(f"- **Location:** {match.location}")
            if match.description:
                output.append(f"- **Description:** {match.description}")
            output.append(f"")
        
        console.print("\n".join(output))
    
    async def _handle_interactive_mode(
        self,
        discovery_result: DiscoveryResult,
        research_discovered: bool
    ) -> None:
        """Handle interactive discovery and selection workflow."""
        
        console.print("\n🎮 [bold cyan]Interactive Discovery Mode[/bold cyan]")
        console.print("(Simplified interactive mode - full implementation pending)")
        
        # Display results summary
        console.print(f"\n📊 Found {len(discovery_result.matches)} companies:")
        
        for i, match in enumerate(discovery_result.matches[:5], 1):
            console.print(f"{i}. {match.company_name} ({match.similarity_score:.2f})")
        
        if research_discovered:
            console.print("\n🔬 Auto-research requested...")
            await self._auto_research_companies(discovery_result.matches[:3])
    
    async def _auto_research_companies(self, matches: List[CompanyMatch]) -> None:
        """Automatically research discovered companies."""
        
        if not matches:
            return
        
        console.print(f"\n🔬 [blue]Starting auto-research for {len(matches)} companies...[/blue]")
        
        # Convert CompanyMatch to Company objects for research
        companies = []
        for match in matches:
            company = Company(
                name=match.company_name,
                website=match.domain or f"https://{match.company_name.lower().replace(' ', '')}.com"
            )
            companies.append(company)
        
        try:
            # Import research command
            from src.cli.commands.research import ResearchCommand
            research_command = ResearchCommand(self.container)
            
            # Research each company
            for i, company in enumerate(companies, 1):
                console.print(f"\n📊 [blue]Researching {i}/{len(companies)}: {company.name}[/blue]")
                
                try:
                    await research_command.execute(
                        company_name=company.name,
                        company_website=company.website,
                        output=OutputFormat.TABLE,
                        verbose=False
                    )
                except Exception as e:
                    console.print(f"❌ [red]Research failed for {company.name}: {str(e)}[/red]")
        except ImportError:
            console.print("⚠️ [yellow]Research command not available[/yellow]")
    
    async def _save_results(
        self,
        discovery_result: DiscoveryResult,
        file_path: str,
        output_format: OutputFormat
    ) -> None:
        """Save discovery results to file."""
        
        try:
            path = Path(file_path)
            
            # Convert to serializable data
            matches_data = []
            for match in discovery_result.matches:
                match_data = {
                    'company_name': match.company_name,
                    'domain': match.domain,
                    'description': match.description,
                    'industry': match.industry,
                    'business_model': match.business_model,
                    'employee_count': match.employee_count,
                    'location': match.location,
                    'similarity_score': match.similarity_score,
                    'confidence_score': match.confidence_score,
                    'source': match.source.value
                }
                matches_data.append(match_data)
            
            data = {
                'query_company': discovery_result.query_company,
                'search_strategy': discovery_result.search_strategy,
                'total_matches': discovery_result.total_matches,
                'execution_time_seconds': discovery_result.execution_time_seconds,
                'average_confidence': discovery_result.average_confidence,
                'coverage_score': discovery_result.coverage_score,
                'matches': matches_data,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Determine format from extension or output format
            if path.suffix.lower() == '.json' or output_format == OutputFormat.JSON:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            elif path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml' or output_format == OutputFormat.YAML:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                # Default to JSON
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            console.print(f"💾 [green]Results saved to: {file_path}[/green]")
            
        except Exception as e:
            console.print(f"❌ [red]Failed to save results: {str(e)}[/red]")


# Click command definition with simplified options
@click.command()
@click.argument('company_name', type=str)
@click.option('--limit', type=int, default=10, help='Maximum results to return')
@click.option('--output', '-o', 
              type=click.Choice(['table', 'json', 'yaml', 'markdown'], case_sensitive=False),
              default='table', help='Output format')
@click.option('--business-model', 
              type=click.Choice(['b2b', 'b2c', 'marketplace', 'saas', 'ecommerce'], case_sensitive=False),
              help='Filter by business model')
@click.option('--company-size',
              type=click.Choice(['startup', 'small', 'medium', 'large', 'enterprise'], case_sensitive=False),
              help='Filter by company size')
@click.option('--industry', type=str, help='Filter by industry sector')
@click.option('--location', type=str, help='Filter by geographic location')
@click.option('--similarity-threshold', type=float, default=0.6, help='Minimum similarity score')
@click.option('--source',
              type=click.Choice(['vector', 'web', 'hybrid'], case_sensitive=False),
              default='hybrid', help='Discovery source preference')
@click.option('--interactive', '-i', is_flag=True, help='Enable interactive research mode')
@click.option('--research-discovered', is_flag=True, help='Automatically research all discovered companies')
@click.option('--save', type=str, help='Save discovery results to file')
@click.option('--explain-similarity', is_flag=True, help='Show detailed similarity explanations')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose discovery logging')
@click.option('--timeout', type=int, default=45, help='Discovery timeout in seconds')
@click.pass_context
def discover_command(
    ctx,
    company_name: str,
    limit: int,
    output: str,
    business_model: Optional[str],
    company_size: Optional[str],
    industry: Optional[str],
    location: Optional[str],
    similarity_threshold: float,
    source: str,
    interactive: bool,
    research_discovered: bool,
    save: Optional[str],
    explain_similarity: bool,
    verbose: bool,
    timeout: int
) -> None:
    """
    Discover companies similar to the specified company with advanced filtering.
    
    Provides intelligent similarity matching with transparent scoring,
    multi-source discovery, and seamless research integration.
    
    Examples:
    
    \b
    # Basic discovery
    theodore discover "Salesforce"
    
    \b
    # Advanced filtering
    theodore discover "Stripe" --business-model saas --limit 20 --explain-similarity
    
    \b
    # Interactive mode with auto-research
    theodore discover "Microsoft" --interactive --research-discovered
    
    \b
    # Export results
    theodore discover "Apple" --save apple-competitors.json --output json
    """
    
    # Get container from context
    container = ctx.obj['container']
    
    # Create and execute command
    command = DiscoveryCommand(container)
    
    # Convert output string to enum
    output_format = OutputFormat(output.lower())
    
    # Run the async command
    asyncio.run(command.execute(
        company_name=company_name,
        limit=limit,
        output=output_format,
        business_model=business_model,
        company_size=company_size,
        industry=industry,
        location=location,
        similarity_threshold=similarity_threshold,
        source=source,
        interactive=interactive,
        research_discovered=research_discovered,
        save=save,
        explain_similarity=explain_similarity,
        verbose=verbose,
        timeout=timeout
    ))
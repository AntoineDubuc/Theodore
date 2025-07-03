#!/usr/bin/env python3
"""
Theodore v2 Export CLI Commands

Command-line interface for data export, analytics, and report generation.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ....core.use_cases.export_data import ExportData, ExportDataRequest
from ....core.domain.models.export import (
    ExportFormat, ExportFilters, OutputConfig, AnalysisType
)
from ....infrastructure.adapters.io.export_engine import ExportEngine
from ....infrastructure.adapters.io.analytics_engine import AnalyticsEngine
from ....infrastructure.adapters.io.visualization_engine import VisualizationEngine
from ....infrastructure.adapters.io.report_engine import ReportEngine
from ....infrastructure.observability.logging import get_logger
from ..utils.formatters import format_file_size, format_duration
from ..utils.validators import validate_file_path, validate_export_format

console = Console()
logger = get_logger(__name__)


@click.group(name='export')
def export_group():
    """Data export, analytics, and reporting commands"""
    pass


@export_group.command()
@click.option('--format', '-f', 
              type=click.Choice(['csv', 'json', 'excel', 'pdf', 'parquet', 'powerbi', 'tableau']),
              default='csv',
              help='Export format')
@click.option('--output', '-o', 
              type=click.Path(),
              help='Output file path (auto-generated if not provided)')
@click.option('--filter-industry', 
              multiple=True,
              help='Filter by industry (can be used multiple times)')
@click.option('--filter-location',
              multiple=True, 
              help='Filter by location (can be used multiple times)')
@click.option('--filter-business-model',
              multiple=True,
              help='Filter by business model (can be used multiple times)')
@click.option('--created-after',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Include only companies created after this date (YYYY-MM-DD)')
@click.option('--created-before',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Include only companies created before this date (YYYY-MM-DD)')
@click.option('--min-employees',
              type=int,
              help='Minimum number of employees')
@click.option('--max-employees',
              type=int,
              help='Maximum number of employees')
@click.option('--include-analytics',
              is_flag=True,
              help='Include analytics data in export')
@click.option('--include-visualizations',
              is_flag=True,
              help='Include visualizations in export')
@click.option('--compress',
              is_flag=True,
              help='Compress output file')
@click.option('--stream',
              is_flag=True,
              help='Use streaming for large datasets')
@click.option('--chunk-size',
              type=int,
              default=1000,
              help='Chunk size for streaming (default: 1000)')
@click.option('--fields',
              help='Comma-separated list of fields to include')
@click.option('--exclude-fields',
              help='Comma-separated list of fields to exclude')
@click.option('--custom-columns',
              help='Custom column mappings in JSON format')
def data(format: str, output: Optional[str], filter_industry: List[str], 
         filter_location: List[str], filter_business_model: List[str],
         created_after: Optional[datetime], created_before: Optional[datetime],
         min_employees: Optional[int], max_employees: Optional[int],
         include_analytics: bool, include_visualizations: bool,
         compress: bool, stream: bool, chunk_size: int,
         fields: Optional[str], exclude_fields: Optional[str],
         custom_columns: Optional[str]):
    """Export company data with filtering and analytics"""
    
    asyncio.run(_export_data(
        format=format,
        output=output,
        filter_industry=list(filter_industry),
        filter_location=list(filter_location),
        filter_business_model=list(filter_business_model),
        created_after=created_after,
        created_before=created_before,
        min_employees=min_employees,
        max_employees=max_employees,
        include_analytics=include_analytics,
        include_visualizations=include_visualizations,
        compress=compress,
        stream=stream,
        chunk_size=chunk_size,
        fields=fields,
        exclude_fields=exclude_fields,
        custom_columns=custom_columns
    ))


async def _export_data(
    format: str,
    output: Optional[str],
    filter_industry: List[str],
    filter_location: List[str], 
    filter_business_model: List[str],
    created_after: Optional[datetime],
    created_before: Optional[datetime],
    min_employees: Optional[int],
    max_employees: Optional[int],
    include_analytics: bool,
    include_visualizations: bool,
    compress: bool,
    stream: bool,
    chunk_size: int,
    fields: Optional[str],
    exclude_fields: Optional[str],
    custom_columns: Optional[str]
):
    """Execute data export"""
    
    try:
        # Create export filters
        filters = ExportFilters(
            industries=filter_industry,
            locations=filter_location,
            business_models=filter_business_model,
            created_after=created_after,
            created_before=created_before,
            min_employee_count=min_employees,
            max_employee_count=max_employees
        )
        
        # Parse field selections
        include_fields = fields.split(',') if fields else []
        exclude_fields_list = exclude_fields.split(',') if exclude_fields else []
        
        # Parse custom columns
        custom_columns_dict = {}
        if custom_columns:
            try:
                custom_columns_dict = json.loads(custom_columns)
            except json.JSONDecodeError:
                console.print("[red]Error: Invalid JSON format for custom columns[/red]")
                return
        
        # Generate output path if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"theodore_export_{timestamp}.{format}"
        
        # Validate export format
        try:
            export_format = ExportFormat(format.upper())
        except ValueError:
            console.print(f"[red]Error: Unsupported export format '{format}'[/red]")
            return
        
        # Create output configuration
        output_config = OutputConfig(
            format=export_format,
            file_path=Path(output),
            compress=compress,
            stream_large_datasets=stream,
            streaming_threshold=chunk_size * 2,  # Stream if more than 2x chunk size
            chunk_size=chunk_size,
            include_fields=include_fields,
            exclude_fields=exclude_fields_list,
            custom_columns=custom_columns_dict
        )
        
        # Create export request
        export_request = ExportDataRequest(
            filters=filters,
            output_config=output_config,
            include_analytics=include_analytics,
            include_visualizations=include_visualizations
        )
        
        # Initialize export use case
        export_engine = ExportEngine()
        analytics_engine = AnalyticsEngine() if include_analytics else None
        visualization_engine = VisualizationEngine() if include_visualizations else None
        
        export_use_case = ExportData(
            export_engine=export_engine,
            analytics_engine=analytics_engine,
            visualization_engine=visualization_engine
        )
        
        # Execute export with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Start export task
            task = progress.add_task("Exporting data...", total=None)
            
            try:
                response = await export_use_case.execute(export_request)
                
                if response.success:
                    progress.update(task, description="Export completed successfully!")
                    
                    # Display results
                    _display_export_results(response)
                    
                else:
                    progress.update(task, description="Export failed")
                    console.print(f"[red]Export failed: {response.error_message}[/red]")
            
            except Exception as e:
                progress.update(task, description="Export failed")
                console.print(f"[red]Export failed: {str(e)}[/red]")
                logger.error(f"Data export failed: {e}", exc_info=True)
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Export command failed: {e}", exc_info=True)


def _display_export_results(response):
    """Display export results in a formatted table"""
    
    # Create results panel
    results_text = Text()
    results_text.append("Export completed successfully!\n\n", style="bold green")
    
    # File information
    results_text.append(f"📄 Output File: {response.file_path}\n", style="cyan")
    results_text.append(f"📊 Format: {response.format.value.upper()}\n", style="cyan")
    results_text.append(f"📈 Records: {response.record_count:,}\n", style="cyan")
    results_text.append(f"💾 File Size: {format_file_size(response.file_size_bytes)}\n", style="cyan")
    
    if response.processing_time_seconds:
        results_text.append(f"⏱️  Processing Time: {format_duration(response.processing_time_seconds)}\n", style="cyan")
    
    if response.streaming_used:
        results_text.append(f"🔄 Streaming: Used ({response.chunks_processed} chunks)\n", style="yellow")
    
    # Analytics information
    if response.analytics:
        results_text.append(f"\n📊 Analytics:\n", style="bold blue")
        results_text.append(f"   • Industries: {response.analytics.industries_count}\n", style="blue")
        results_text.append(f"   • Avg Company Size: {response.analytics.average_company_size or 'N/A'}\n", style="blue")
        if response.analytics.market_concentration:
            results_text.append(f"   • Market Concentration: {response.analytics.market_concentration:.3f}\n", style="blue")
    
    # Visualizations information
    if response.visualizations:
        results_text.append(f"\n🎨 Visualizations: {len(response.visualizations)} generated\n", style="bold magenta")
        for viz in response.visualizations[:3]:  # Show first 3
            results_text.append(f"   • {viz.title}\n", style="magenta")
        if len(response.visualizations) > 3:
            results_text.append(f"   • ... and {len(response.visualizations) - 3} more\n", style="magenta")
    
    # Filters applied
    if response.filters_applied:
        results_text.append(f"\n🔍 Filters Applied: {len(response.filters_applied)}\n", style="yellow")
        for filter_name in response.filters_applied[:3]:
            results_text.append(f"   • {filter_name}\n", style="yellow")
    
    console.print(Panel(results_text, title="Export Results", border_style="green"))


@export_group.command()
@click.option('--type', '-t',
              type=click.Choice(['competitive_landscape', 'market_trends', 'growth_patterns', 'similarity_clusters', 'summary']),
              default='summary',
              help='Type of analytics to generate')
@click.option('--output', '-o',
              type=click.Path(),
              help='Output file path')
@click.option('--format', '-f',
              type=click.Choice(['json', 'html', 'markdown']),
              default='json',
              help='Output format')
@click.option('--filter-industry',
              multiple=True,
              help='Filter by industry')
@click.option('--include-visualizations',
              is_flag=True,
              help='Include visualizations in analytics')
def analytics(type: str, output: Optional[str], format: str,
              filter_industry: List[str], include_visualizations: bool):
    """Generate analytics reports"""
    
    asyncio.run(_generate_analytics(
        analysis_type=type,
        output=output,
        format=format,
        filter_industry=list(filter_industry),
        include_visualizations=include_visualizations
    ))


async def _generate_analytics(
    analysis_type: str,
    output: Optional[str],
    format: str,
    filter_industry: List[str],
    include_visualizations: bool
):
    """Execute analytics generation"""
    
    try:
        # Map analysis type
        analysis_type_enum = AnalysisType(analysis_type.upper())
        
        # Generate output path if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"theodore_analytics_{analysis_type}_{timestamp}.{format}"
        
        # Initialize engines
        analytics_engine = AnalyticsEngine()
        visualization_engine = VisualizationEngine() if include_visualizations else None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Generating analytics...", total=None)
            
            try:
                # For now, create mock data since we don't have database integration in CLI
                # In production, this would fetch from the database
                mock_companies = []  # Would fetch from database
                
                if not mock_companies:
                    progress.update(task, description="No companies found")
                    console.print("[yellow]No companies found. Please run research first.[/yellow]")
                    return
                
                # Generate analytics
                analytics_report = await analytics_engine.generate_market_analysis(
                    mock_companies, analysis_type_enum
                )
                
                # Generate visualizations if requested
                visualizations = []
                if include_visualizations and visualization_engine:
                    visualizations = await visualization_engine.create_visualizations(mock_companies)
                
                # Save results
                await _save_analytics_results(analytics_report, visualizations, output, format)
                
                progress.update(task, description="Analytics generated successfully!")
                
                # Display summary
                _display_analytics_summary(analytics_report, output)
                
            except Exception as e:
                progress.update(task, description="Analytics generation failed")
                console.print(f"[red]Analytics generation failed: {str(e)}[/red]")
                logger.error(f"Analytics generation failed: {e}", exc_info=True)
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Analytics command failed: {e}", exc_info=True)


async def _save_analytics_results(analytics_report, visualizations, output: str, format: str):
    """Save analytics results to file"""
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'json':
        # Save as JSON
        results = {
            'analytics_report': analytics_report.dict(),
            'visualizations': [v.dict() for v in visualizations],
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    
    elif format == 'html':
        # Generate HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{analytics_report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .insight {{ margin: 10px 0; padding: 10px; background: #e8f4f8; border-left: 4px solid #007acc; }}
    </style>
</head>
<body>
    <h1>{analytics_report.title}</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>{analytics_report.summary}</p>
    </div>
    
    <h2>Key Insights</h2>
    {''.join(f'<div class="insight">{insight}</div>' for insight in analytics_report.key_insights)}
    
    {'<h2>Visualizations</h2>' if visualizations else ''}
    {'<ul>' + ''.join(f'<li>{v.title}: {v.description}</li>' for v in visualizations) + '</ul>' if visualizations else ''}
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    elif format == 'markdown':
        # Generate Markdown report
        md_content = f"# {analytics_report.title}\n\n"
        md_content += f"## Summary\n\n{analytics_report.summary}\n\n"
        md_content += "## Key Insights\n\n"
        
        for insight in analytics_report.key_insights:
            md_content += f"- {insight}\n"
        
        if visualizations:
            md_content += "\n## Visualizations\n\n"
            for viz in visualizations:
                md_content += f"### {viz.title}\n\n{viz.description}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)


def _display_analytics_summary(analytics_report, output: str):
    """Display analytics summary"""
    
    # Create summary table
    table = Table(title="Analytics Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Report Type", analytics_report.report_type.value)
    table.add_row("Title", analytics_report.title)
    table.add_row("Key Insights", str(len(analytics_report.key_insights)))
    
    if analytics_report.analytics:
        table.add_row("Companies Analyzed", str(analytics_report.analytics.total_companies))
        table.add_row("Industries", str(analytics_report.analytics.industries_count))
    
    table.add_row("Output File", output)
    
    console.print(table)
    
    # Display key insights
    if analytics_report.key_insights:
        console.print("\n[bold blue]Key Insights:[/bold blue]")
        for i, insight in enumerate(analytics_report.key_insights[:5], 1):
            console.print(f"  {i}. {insight}")
        
        if len(analytics_report.key_insights) > 5:
            console.print(f"  ... and {len(analytics_report.key_insights) - 5} more insights")


@export_group.command()
@click.option('--template', '-t',
              help='Report template name')
@click.option('--output', '-o',
              type=click.Path(),
              help='Output file path')
@click.option('--format', '-f',
              type=click.Choice(['html', 'pdf', 'markdown', 'json']),
              default='html',
              help='Report format')
@click.option('--title',
              help='Report title')
@click.option('--parameters',
              help='Report parameters in JSON format')
@click.option('--include-analytics',
              is_flag=True,
              help='Include analytics in report')
@click.option('--include-visualizations',
              is_flag=True,
              help='Include visualizations in report')
def report(template: Optional[str], output: Optional[str], format: str,
           title: Optional[str], parameters: Optional[str],
           include_analytics: bool, include_visualizations: bool):
    """Generate formatted reports from templates"""
    
    asyncio.run(_generate_report(
        template=template,
        output=output,
        format=format,
        title=title,
        parameters=parameters,
        include_analytics=include_analytics,
        include_visualizations=include_visualizations
    ))


async def _generate_report(
    template: Optional[str],
    output: Optional[str],
    format: str,
    title: Optional[str],
    parameters: Optional[str],
    include_analytics: bool,
    include_visualizations: bool
):
    """Execute report generation"""
    
    try:
        # Initialize report engine
        report_engine = ReportEngine()
        
        # List available templates if none specified
        if not template:
            templates = await report_engine.list_templates()
            
            if not templates:
                console.print("[yellow]No templates available. Creating default templates...[/yellow]")
                return
            
            console.print("[bold blue]Available Templates:[/bold blue]")
            for tmpl in templates:
                console.print(f"  • {tmpl.name}: {tmpl.description}")
            
            console.print("\nUse --template to specify a template name")
            return
        
        # Parse parameters
        report_parameters = {"title": title or f"Theodore Report - {datetime.now().strftime('%Y-%m-%d')}"}
        if parameters:
            try:
                custom_params = json.loads(parameters)
                report_parameters.update(custom_params)
            except json.JSONDecodeError:
                console.print("[red]Error: Invalid JSON format for parameters[/red]")
                return
        
        # Generate output path if not provided
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"theodore_report_{template}_{timestamp}.{format}"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Generating report...", total=None)
            
            try:
                # For now, use mock data since we don't have database integration
                mock_companies = []  # Would fetch from database
                
                if not mock_companies:
                    progress.update(task, description="No companies found")
                    console.print("[yellow]No companies found. Please run research first.[/yellow]")
                    return
                
                # Generate analytics if requested
                analytics = None
                if include_analytics:
                    analytics_engine = AnalyticsEngine()
                    analytics = await analytics_engine.generate_analytics(mock_companies)
                
                # Generate visualizations if requested
                visualizations = None
                if include_visualizations:
                    viz_engine = VisualizationEngine()
                    visualizations = await viz_engine.create_visualizations(mock_companies)
                
                # Generate report
                generated_report = await report_engine.generate_report(
                    template_name=template,
                    companies=mock_companies,
                    parameters=report_parameters,
                    analytics=analytics,
                    visualizations=visualizations
                )
                
                # Export report
                exported_path = await report_engine.export_report(
                    generated_report,
                    output,
                    format
                )
                
                progress.update(task, description="Report generated successfully!")
                
                # Display summary
                _display_report_summary(generated_report, exported_path)
                
            except Exception as e:
                progress.update(task, description="Report generation failed")
                console.print(f"[red]Report generation failed: {str(e)}[/red]")
                logger.error(f"Report generation failed: {e}", exc_info=True)
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Report command failed: {e}", exc_info=True)


def _display_report_summary(generated_report, exported_path: str):
    """Display report generation summary"""
    
    # Create summary panel
    summary_text = Text()
    summary_text.append("Report generated successfully!\n\n", style="bold green")
    
    summary_text.append(f"📄 Template: {generated_report.template_name}\n", style="cyan")
    summary_text.append(f"📊 Title: {generated_report.title}\n", style="cyan")
    summary_text.append(f"📈 Companies: {generated_report.companies_count}\n", style="cyan")
    summary_text.append(f"📁 Output: {exported_path}\n", style="cyan")
    summary_text.append(f"🔖 Format: {generated_report.format.value.upper()}\n", style="cyan")
    summary_text.append(f"⏰ Generated: {generated_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n", style="cyan")
    
    if generated_report.visualizations:
        summary_text.append(f"🎨 Visualizations: {len(generated_report.visualizations)}\n", style="magenta")
    
    if generated_report.analytics:
        summary_text.append(f"📊 Analytics: Included\n", style="blue")
    
    console.print(Panel(summary_text, title="Report Summary", border_style="green"))


@export_group.command()
@click.option('--format', '-f',
              type=click.Choice(['csv', 'json', 'excel', 'pdf', 'parquet', 'powerbi', 'tableau']),
              help='Show formats (all if not specified)')
def formats(format: Optional[str]):
    """Show available export formats and their capabilities"""
    
    # Format information
    format_info = {
        'csv': {
            'name': 'CSV (Comma-Separated Values)',
            'streaming': True,
            'compression': False,
            'visualizations': False,
            'analytics': False,
            'use_cases': ['Data analysis', 'Spreadsheet import', 'Database loading']
        },
        'json': {
            'name': 'JSON (JavaScript Object Notation)',
            'streaming': False,
            'compression': True,
            'visualizations': True,
            'analytics': True,
            'use_cases': ['API integration', 'Web applications', 'Data interchange']
        },
        'excel': {
            'name': 'Excel Workbook (.xlsx)',
            'streaming': False,
            'compression': False,
            'visualizations': True,
            'analytics': True,
            'use_cases': ['Business reports', 'Executive dashboards', 'Data presentation']
        },
        'pdf': {
            'name': 'PDF Report',
            'streaming': False,
            'compression': False,
            'visualizations': True,
            'analytics': True,
            'use_cases': ['Formal reports', 'Presentations', 'Documentation']
        },
        'parquet': {
            'name': 'Apache Parquet',
            'streaming': True,
            'compression': True,
            'visualizations': False,
            'analytics': False,
            'use_cases': ['Big data analytics', 'Data warehousing', 'High performance']
        },
        'powerbi': {
            'name': 'PowerBI Optimized',
            'streaming': False,
            'compression': False,
            'visualizations': True,
            'analytics': True,
            'use_cases': ['PowerBI dashboards', 'Business intelligence', 'Interactive reports']
        },
        'tableau': {
            'name': 'Tableau Optimized',
            'streaming': False,
            'compression': False,
            'visualizations': True,
            'analytics': True,
            'use_cases': ['Tableau dashboards', 'Data visualization', 'Interactive analysis']
        }
    }
    
    if format:
        # Show specific format details
        if format in format_info:
            info = format_info[format]
            
            console.print(f"\n[bold blue]{info['name']}[/bold blue]\n")
            
            # Capabilities table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Capability", style="cyan")
            table.add_column("Supported", style="white")
            
            table.add_row("Streaming Support", "✅ Yes" if info['streaming'] else "❌ No")
            table.add_row("Compression", "✅ Yes" if info['compression'] else "❌ No")
            table.add_row("Visualizations", "✅ Yes" if info['visualizations'] else "❌ No")
            table.add_row("Analytics Integration", "✅ Yes" if info['analytics'] else "❌ No")
            
            console.print(table)
            
            # Use cases
            console.print(f"\n[bold green]Common Use Cases:[/bold green]")
            for use_case in info['use_cases']:
                console.print(f"  • {use_case}")
        else:
            console.print(f"[red]Unknown format: {format}[/red]")
    else:
        # Show all formats
        console.print("[bold blue]Available Export Formats[/bold blue]\n")
        
        for fmt, info in format_info.items():
            capabilities = []
            if info['streaming']:
                capabilities.append("Streaming")
            if info['compression']:
                capabilities.append("Compression")
            if info['visualizations']:
                capabilities.append("Visualizations")
            if info['analytics']:
                capabilities.append("Analytics")
            
            capability_str = ", ".join(capabilities) if capabilities else "Basic export"
            
            console.print(f"[cyan]{fmt:10}[/cyan] {info['name']}")
            console.print(f"           {capability_str}")
            console.print()


# Add the export group to the main CLI
def register_commands(cli_group):
    """Register export commands with the main CLI"""
    cli_group.add_command(export_group)
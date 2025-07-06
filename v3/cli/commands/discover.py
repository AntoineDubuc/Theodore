#!/usr/bin/env python3
"""
Theodore v3 Discover Command
===========================

Find similar companies using vector search in the Pinecone database.
Uses the proven antoine discovery modules.
"""

import click
import sys
import os
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.command()
@click.argument('query', required=True)
@click.option(
    '--limit', 
    default=10, 
    type=int,
    help='Maximum number of similar companies to find'
)
@click.option(
    '--industry',
    help='Filter by industry'
)
@click.option(
    '--format', 
    type=click.Choice(['console', 'json', 'csv']), 
    default='console',
    help='Output format'
)
@click.option(
    '--output', 
    type=click.Path(), 
    help='Save results to file'
)
@click.pass_context
def discover(ctx, query: str, limit: int, industry: Optional[str], format: str, output: Optional[str]):
    """
    Find similar companies using vector search.
    
    QUERY can be a company name, description, or industry term:
    - "cloud consulting"
    - "CloudGeometry"
    - "SaaS platform development"
    
    Examples:
        theodore discover "cloud consulting" --limit 5
        theodore discover "CloudGeometry" --format json
        theodore discover "SaaS" --industry "Software" --output results.csv
    """
    
    verbose = ctx.obj.get('verbose', False)
    
    console.print(f"🔍 Discovering companies similar to: [bold blue]{query}[/bold blue]")
    
    if verbose:
        console.print(f"📊 Limit: {limit}")
        console.print(f"🏭 Industry filter: {industry or 'None'}")
        console.print(f"📋 Format: {format}")
        console.print()
    
    # Execute discovery using antoine modules
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("🔍 Searching vector database...", total=None)
            
            results = execute_discovery_search(
                query=query,
                limit=limit,
                industry_filter=industry,
                verbose=verbose
            )
            
            progress.update(task, description="✅ Search completed")
        
        if results['success']:
            companies = results['companies']
            
            if not companies:
                console.print("📭 No similar companies found.", style="yellow")
                return
            
            console.print(f"\n✅ Found {len(companies)} similar companies:")
            
            if format == 'console':
                display_discovery_results(companies, query)
            elif format == 'json':
                output_discovery_json(companies, output)
            elif format == 'csv':
                output_discovery_csv(companies, output)
                
        else:
            console.print(f"❌ Discovery failed: {results['error']}", style="red")
            return 1
            
    except Exception as e:
        console.print(f"❌ Discovery error: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        return 1

def execute_discovery_search(query: str, limit: int, industry_filter: Optional[str], verbose: bool) -> dict:
    """Execute similarity search using enhanced OrganizationFinder"""
    
    # Add core modules to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
    
    try:
        from find_org_in_vectordb import OrganizationFinder
        
        # Initialize enhanced finder
        finder = OrganizationFinder()
        
        # Execute similarity search using enhanced methods
        search_results = finder.search_similar_companies(
            query=query,
            limit=limit,
            industry_filter=industry_filter
        )
        
        if verbose:
            print(f"Found {len(search_results)} similar companies using enhanced 51-field retrieval")
        
        return {
            'success': True,
            'companies': search_results,
            'query': query,
            'limit': limit
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def display_discovery_results(companies: List[dict], query: str):
    """Display discovery results in rich console format"""
    
    # Results overview panel
    overview_panel = Panel(
        f"[bold blue]Search Query:[/bold blue] {query}\n"
        f"[bold green]Results Found:[/bold green] {len(companies)} companies\n"
        f"[bold yellow]Sorted by:[/bold yellow] Similarity score (highest first)",
        title="🔍 Discovery Results",
        border_style="blue"
    )
    console.print(overview_panel)
    
    # Results table
    table = Table(title="📊 Similar Companies")
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Company", style="bold white", width=20)
    table.add_column("Industry", style="green", width=25)
    table.add_column("Description", style="white", width=40)
    table.add_column("Score", style="yellow", width=8)
    
    for idx, company in enumerate(companies, 1):
        table.add_row(
            str(idx),
            company.get('name', 'Unknown'),
            company.get('industry', 'Unknown'),
            (company.get('description', 'No description')[:37] + '...') if len(company.get('description', '')) > 40 else company.get('description', 'No description'),
            f"{company.get('similarity_score', 0):.3f}"
        )
    
    console.print(table)

def output_discovery_json(companies: List[dict], output_file: Optional[str]):
    """Output discovery results as JSON"""
    import json
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(companies, f, indent=2, default=str)
        console.print(f"📁 Discovery results saved to: {output_file}")
    else:
        console.print(json.dumps(companies, indent=2, default=str))

def output_discovery_csv(companies: List[dict], output_file: Optional[str]):
    """Output discovery results as CSV"""
    import pandas as pd
    
    df = pd.DataFrame(companies)
    
    if output_file:
        df.to_csv(output_file, index=False)
        console.print(f"📁 Discovery CSV saved to: {output_file}")
    else:
        console.print(df.to_csv(index=False))
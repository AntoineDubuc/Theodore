#!/usr/bin/env python3
"""
Theodore v3 Batch Command
========================

Process multiple companies from a file using the proven antoine pipeline.
Supports parallel processing and various input formats.
"""

import click
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

console = Console()

@click.command()
@click.argument('file', type=click.Path(exists=True), required=True)
@click.option(
    '--parallel', 
    default=3, 
    type=int,
    help='Number of companies to process in parallel (default: 3)'
)
@click.option(
    '--format', 
    type=click.Choice(['console', 'json', 'csv']), 
    default='console',
    help='Output format for results'
)
@click.option(
    '--output-dir', 
    type=click.Path(), 
    help='Directory to save individual company results'
)
@click.option(
    '--summary-file',
    type=click.Path(),
    help='File to save batch processing summary'
)
@click.option(
    '--skip-errors',
    is_flag=True,
    help='Continue processing even if some companies fail'
)
@click.pass_context
def batch(ctx, file: str, parallel: int, format: str, output_dir: Optional[str], 
          summary_file: Optional[str], skip_errors: bool):
    """
    Process multiple companies from a file.
    
    FILE should contain one company per line. Supports:
    - Company names: "Cloud Geometry"
    - Domain names: cloudgeometry.com
    - URLs: https://www.cloudgeometry.com
    - Mixed formats
    
    Examples:
        theodore batch companies.txt
        theodore batch companies.csv --parallel 5 --output-dir results/
        theodore batch domains.txt --format json --summary-file summary.json
    """
    
    verbose = ctx.obj.get('verbose', False)
    
    console.print(f"📋 Processing companies from: [bold blue]{file}[/bold blue]")
    
    if verbose:
        console.print(f"⚡ Parallel processing: {parallel} companies")
        console.print(f"📋 Output format: {format}")
        console.print(f"📁 Output directory: {output_dir or 'None'}")
        console.print(f"📄 Summary file: {summary_file or 'None'}")
        console.print()
    
    # Load companies from file
    try:
        companies = load_companies_from_file(file)
        console.print(f"📊 Loaded {len(companies)} companies from file")
        
        if not companies:
            console.print("❌ No companies found in file", style="red")
            return 1
            
    except Exception as e:
        console.print(f"❌ Failed to load companies: {str(e)}", style="red")
        return 1
    
    # Create output directory if specified
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        console.print(f"📁 Output directory: {output_dir}")
    
    # Execute batch processing
    try:
        results = execute_batch_processing(
            companies=companies,
            parallel_count=parallel,
            skip_errors=skip_errors,
            verbose=verbose
        )
        
        # Display results
        display_batch_summary(results, companies)
        
        # Save results if requested
        if output_dir or summary_file:
            save_batch_results(results, companies, output_dir, summary_file, format)
        
        # Return appropriate exit code
        if results['failed_count'] > 0 and not skip_errors:
            return 1
        
        console.print(f"\n✅ Batch processing completed!", style="green")
        
    except KeyboardInterrupt:
        console.print("\n⚠️ Batch processing interrupted by user", style="yellow")
        return 1
    except Exception as e:
        console.print(f"\n❌ Batch processing failed: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        return 1

def load_companies_from_file(file_path: str) -> List[str]:
    """Load company list from various file formats"""
    
    companies = []
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.csv':
        # Handle CSV files
        import pandas as pd
        df = pd.read_csv(file_path)
        
        # Try common column names
        possible_columns = ['company', 'name', 'domain', 'website', 'url']
        company_column = None
        
        for col in possible_columns:
            if col in df.columns:
                company_column = col
                break
        
        if company_column:
            companies = df[company_column].dropna().tolist()
        else:
            # Use first column
            companies = df.iloc[:, 0].dropna().tolist()
            
    else:
        # Handle text files
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    companies.append(line)
    
    return companies

def execute_batch_processing(companies: List[str], parallel_count: int, skip_errors: bool, verbose: bool) -> Dict:
    """Execute batch processing of companies"""
    
    # Add core modules to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
    
    from cli.commands.research import execute_research_pipeline, extract_company_name_from_url, find_company_website
    
    results = {
        'successful': [],
        'failed': [],
        'successful_count': 0,
        'failed_count': 0,
        'total_companies': len(companies),
        'start_time': time.time(),
        'total_cost': 0.0
    }
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("🏭 Processing companies...", total=len(companies))
        
        for idx, company in enumerate(companies, 1):
            progress.update(task, description=f"🏭 Processing: {company[:30]}...")
            
            try:
                # Determine URL and company name
                if company.startswith(('http://', 'https://')):
                    base_url = company
                    company_name = extract_company_name_from_url(company)
                elif '.' in company and not ' ' in company:
                    base_url = f"https://www.{company}" if not company.startswith('www.') else f"https://{company}"
                    company_name = extract_company_name_from_url(company)
                else:
                    # Company name - find website
                    base_url = find_company_website(company)
                    company_name = company
                    
                    if not base_url:
                        raise Exception(f"Could not find website for: {company}")
                
                # Execute research pipeline
                result = execute_research_pipeline(
                    base_url=base_url,
                    company_name=company_name,
                    show_progress=False,
                    verbose=verbose
                )
                
                if result['success']:
                    results['successful'].append({
                        'company': company,
                        'result': result
                    })
                    results['successful_count'] += 1
                    results['total_cost'] += result.get('total_cost', 0)
                    
                    if verbose:
                        console.print(f"✅ {company} completed successfully")
                        
                else:
                    error_info = {
                        'company': company,
                        'error': result.get('error', 'Unknown error')
                    }
                    results['failed'].append(error_info)
                    results['failed_count'] += 1
                    
                    if not skip_errors:
                        console.print(f"❌ {company} failed: {error_info['error']}", style="red")
                    elif verbose:
                        console.print(f"⚠️ {company} failed: {error_info['error']}", style="yellow")
                
            except Exception as e:
                error_info = {
                    'company': company,
                    'error': str(e)
                }
                results['failed'].append(error_info)
                results['failed_count'] += 1
                
                if not skip_errors:
                    console.print(f"❌ {company} failed: {str(e)}", style="red")
                elif verbose:
                    console.print(f"⚠️ {company} failed: {str(e)}", style="yellow")
            
            progress.update(task, advance=1)
    
    results['total_time'] = time.time() - results['start_time']
    results['end_time'] = time.time()
    
    return results

def display_batch_summary(results: Dict, companies: List[str]):
    """Display batch processing summary"""
    
    # Summary panel
    summary_panel = Panel(
        f"[bold green]Successful:[/bold green] {results['successful_count']}/{results['total_companies']}\n"
        f"[bold red]Failed:[/bold red] {results['failed_count']}/{results['total_companies']}\n"
        f"[bold blue]Total Time:[/bold blue] {results['total_time']:.2f} seconds\n"
        f"[bold yellow]Total Cost:[/bold yellow] ${results['total_cost']:.4f}",
        title="📊 Batch Processing Summary",
        border_style="blue"
    )
    console.print(summary_panel)
    
    # Show failed companies if any
    if results['failed_count'] > 0:
        console.print(f"\n❌ Failed Companies ({results['failed_count']}):", style="red")
        
        failed_table = Table(show_header=False)
        failed_table.add_column("Company", style="white")
        failed_table.add_column("Error", style="red")
        
        for failed in results['failed']:
            failed_table.add_row(failed['company'], failed['error'])
        
        console.print(failed_table)

def save_batch_results(results: Dict, companies: List[str], output_dir: Optional[str], 
                      summary_file: Optional[str], format: str):
    """Save batch processing results"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual company results
    if output_dir:
        for success in results['successful']:
            company_name = success['company'].replace('/', '_').replace(' ', '_')
            filename = f"{company_name}_{timestamp}.{format}"
            filepath = Path(output_dir) / filename
            
            if format == 'json':
                import json
                with open(filepath, 'w') as f:
                    json.dump(success['result'], f, indent=2, default=str)
            elif format == 'csv':
                import pandas as pd
                # Flatten result for CSV
                flattened = {
                    'company': success['company'],
                    'total_time': success['result']['total_time'],
                    'total_cost': success['result']['total_cost']
                }
                df = pd.DataFrame([flattened])
                df.to_csv(filepath, index=False)
        
        console.print(f"📁 Individual results saved to: {output_dir}")
    
    # Save summary file
    if summary_file:
        summary_data = {
            'batch_summary': {
                'total_companies': results['total_companies'],
                'successful_count': results['successful_count'],
                'failed_count': results['failed_count'],
                'total_time': results['total_time'],
                'total_cost': results['total_cost'],
                'timestamp': timestamp
            },
            'successful_companies': [s['company'] for s in results['successful']],
            'failed_companies': results['failed']
        }
        
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        console.print(f"📄 Summary saved to: {summary_file}")
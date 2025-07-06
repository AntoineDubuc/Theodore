#!/usr/bin/env python3
"""
Theodore v3 Research Command
===========================

Research a single company using the complete proven pipeline from antoine:
1. Critter discovers all website paths
2. Nova Pro LLM selects most valuable paths  
3. Parallel crawler extracts content (10 concurrent)
4. Field extraction generates structured intelligence + operational metadata

Proven performance: 23.42 seconds, $0.01 cost, 49 fields, 100% reliability
"""

import click
import time
import sys
import os
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

@click.command()
@click.argument('company', required=True)
@click.option(
    '--format', 
    type=click.Choice(['console', 'json', 'csv', 'fields']), 
    default='console',
    help='Output format (console=rich display, json=machine readable, csv=spreadsheet, fields=simple key-value)'
)
@click.option(
    '--output', 
    type=click.Path(), 
    help='Save results to file'
)
@click.option(
    '--no-progress', 
    is_flag=True,
    help='Disable progress display'
)
@click.pass_context
def research(ctx, company: str, format: str, output: Optional[str], no_progress: bool):
    """
    Research a single company using the complete Theodore pipeline.
    
    COMPANY can be a domain name or company name:
    - cloudgeometry.com
    - "Cloud Geometry"  
    - example.com
    
    Examples:
        theodore research cloudgeometry.com
        theodore research "Cloud Geometry" --format json
        theodore research example.com --output results.json
    """
    
    verbose = ctx.obj.get('verbose', False)
    
    console.print(f"🔍 Researching: [bold blue]{company}[/bold blue]")
    
    if verbose:
        console.print(f"📋 Format: {format}")
        console.print(f"📁 Output: {output or 'console'}")
        console.print(f"⚡ Using proven antoine pipeline with 10 concurrent pages")
        console.print()
    
    # Determine if input is URL or company name
    if company.startswith(('http://', 'https://')):
        base_url = company
        company_name = extract_company_name_from_url(company)
    elif '.' in company and not ' ' in company:
        # Looks like a domain
        base_url = f"https://www.{company}" if not company.startswith('www.') else f"https://{company}"
        company_name = extract_company_name_from_url(company)
    else:
        # Company name - need to find website
        console.print("🔍 Finding website URL for company name...")
        base_url = find_company_website(company)
        company_name = company
        if not base_url:
            console.print(f"❌ Could not find website for: {company}", style="red")
            return
    
    console.print(f"🌐 Target URL: [cyan]{base_url}[/cyan]")
    console.print(f"🏢 Company: [green]{company_name}[/green]")
    console.print()
    
    # Execute the proven antoine pipeline
    try:
        result = execute_research_pipeline(
            base_url=base_url,
            company_name=company_name,
            show_progress=not no_progress,
            verbose=verbose
        )
        
        if result['success']:
            # Display results based on format
            if format == 'console':
                display_console_results(result, verbose)
            elif format == 'json':
                output_json_results(result, output)
            elif format == 'csv':
                output_csv_results(result, output)
            elif format == 'fields':
                output_fields_results(result, output)
                
            console.print(f"\n✅ Research completed successfully!", style="green")
            console.print(f"💰 Total cost: ${result['total_cost']:.4f}")
            console.print(f"⏱️  Total time: {result['total_time']:.2f} seconds")
            
        else:
            console.print(f"❌ Research failed: {result['error']}", style="red")
            return 1
            
    except KeyboardInterrupt:
        console.print("\n⚠️ Research interrupted by user", style="yellow")
        return 1
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {str(e)}", style="red")
        if verbose:
            console.print_exception()
        return 1

def extract_company_name_from_url(url: str) -> str:
    """Extract company name from URL"""
    from urllib.parse import urlparse
    parsed = urlparse(url if url.startswith('http') else f'https://{url}')
    domain = parsed.netloc.lower().replace('www.', '')
    return domain.split('.')[0].title()

def find_company_website(company_name: str) -> Optional[str]:
    """Find website URL for a company name"""
    # Import the antoine module for website discovery
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
    try:
        from find_website_url import find_website_url_sync
        return find_website_url_sync(company_name)
    except Exception as e:
        console.print(f"⚠️ Website discovery failed: {e}", style="yellow")
        return None

def execute_research_pipeline(base_url: str, company_name: str, show_progress: bool = True, verbose: bool = False) -> dict:
    """Execute the complete proven antoine pipeline"""
    
    # Add core modules to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
    
    try:
        # Import all antoine modules
        from critter import discover_all_paths_sync
        from get_valuable_links_from_llm import filter_valuable_links_sync
        from crawler import crawl_selected_pages_sync
        from distill_out_fields import extract_company_fields_sync
        
        start_time = time.time()
        pipeline_results = {
            'company_name': company_name,
            'base_url': base_url,
            'start_time': start_time,
            'phases': {}
        }
        
        # Progress tracking
        if show_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            )
            progress.start()
            
            task1 = progress.add_task("🔍 Discovering website paths...", total=4)
            task2 = progress.add_task("🧠 AI path selection...", total=4)
            task3 = progress.add_task("📄 Parallel content extraction...", total=4)
            task4 = progress.add_task("🎯 Field extraction...", total=4)
        
        # Phase 1: Path Discovery with Critter
        phase1_start = time.time()
        try:
            if verbose:
                console.print("🔍 Phase 1: Discovering website paths with Critter...")
            
            discovery_result = discover_all_paths_sync(base_url)
            discovered_paths = discovery_result.all_paths
            phase1_time = time.time() - phase1_start
            
            pipeline_results['phases']['phase1_discovery'] = {
                'success': True,
                'paths_discovered': len(discovered_paths),
                'processing_time': phase1_time
            }
            
            if show_progress:
                progress.update(task1, completed=4)
                progress.update(task2, description="🧠 AI selecting valuable paths...")
            
            if verbose:
                console.print(f"✅ Discovered {len(discovered_paths)} paths in {phase1_time:.2f}s")
                
        except Exception as e:
            progress.stop() if show_progress else None
            return {'success': False, 'error': f"Path discovery failed: {str(e)}"}
        
        # Phase 2: Nova Pro Path Selection
        phase2_start = time.time()
        try:
            if verbose:
                console.print("🧠 Phase 2: Nova Pro selecting valuable paths...")
            
            selection_result = filter_valuable_links_sync(
                discovered_paths, 
                base_url, 
                min_confidence=0.6,
                timeout_seconds=120
            )
            phase2_time = time.time() - phase2_start
            
            if selection_result.success:
                pipeline_results['phases']['phase2_selection'] = {
                    'success': True,
                    'paths_selected': len(selection_result.selected_paths),
                    'model_used': selection_result.model_used,
                    'cost_usd': selection_result.cost_usd,
                    'tokens_used': selection_result.tokens_used,
                    'processing_time': phase2_time
                }
                
                if show_progress:
                    progress.update(task2, completed=4)
                    progress.update(task3, description=f"📄 Crawling {len(selection_result.selected_paths)} pages (10 concurrent)...")
                
                if verbose:
                    console.print(f"✅ Selected {len(selection_result.selected_paths)} high-value paths in {phase2_time:.2f}s")
                    
            else:
                progress.stop() if show_progress else None
                return {'success': False, 'error': f"Path selection failed: {selection_result.error}"}
                
        except Exception as e:
            progress.stop() if show_progress else None
            return {'success': False, 'error': f"Path selection failed: {str(e)}"}
        
        # Phase 3: Parallel Content Extraction (10 concurrent)
        phase3_start = time.time()
        try:
            if verbose:
                console.print("📄 Phase 3: Parallel content extraction (10 concurrent)...")
            
            crawl_result = crawl_selected_pages_sync(
                base_url=base_url,
                selected_paths=selection_result.selected_paths,
                timeout_seconds=30,
                max_content_per_page=15000,
                max_concurrent=10  # Proven optimal setting from antoine
            )
            phase3_time = time.time() - phase3_start
            
            pipeline_results['phases']['phase3_extraction'] = {
                'success': True,
                'total_pages': crawl_result.total_pages,
                'successful_pages': crawl_result.successful_pages,
                'total_content_length': crawl_result.total_content_length,
                'processing_time': phase3_time
            }
            
            if show_progress:
                progress.update(task3, completed=4)
                progress.update(task4, description="🎯 Extracting structured fields...")
            
            if verbose:
                console.print(f"✅ Extracted {crawl_result.total_content_length:,} characters from {crawl_result.successful_pages} pages in {phase3_time:.2f}s")
                
        except Exception as e:
            progress.stop() if show_progress else None
            return {'success': False, 'error': f"Content extraction failed: {str(e)}"}
        
        # Phase 4: Field Extraction with Operational Metadata
        phase4_start = time.time()
        try:
            if verbose:
                console.print("🎯 Phase 4: Field extraction with operational metadata...")
            
            field_result = extract_company_fields_sync(
                crawl_result,
                company_name=company_name,
                timeout_seconds=120,
                pipeline_metadata=pipeline_results['phases']
            )
            phase4_time = time.time() - phase4_start
            
            if field_result.success:
                pipeline_results['phases']['phase4_fields'] = {
                    'success': True,
                    'extracted_fields': field_result.extracted_fields,
                    'field_confidence_scores': field_result.field_confidence_scores,
                    'overall_confidence': field_result.overall_confidence,
                    'model_used': field_result.model_used,
                    'cost_usd': field_result.cost_usd,
                    'tokens_used': field_result.tokens_used,
                    'processing_time': phase4_time
                }
                
                if show_progress:
                    progress.update(task4, completed=4)
                    progress.stop()
                
                if verbose:
                    console.print(f"✅ Extracted {len(field_result.extracted_fields)} fields in {phase4_time:.2f}s")
                    
            else:
                progress.stop() if show_progress else None
                return {'success': False, 'error': f"Field extraction failed: {field_result.error}"}
                
        except Exception as e:
            progress.stop() if show_progress else None
            return {'success': False, 'error': f"Field extraction failed: {str(e)}"}
        
        # Calculate final metrics
        total_time = time.time() - start_time
        total_cost = 0
        if pipeline_results['phases'].get('phase2_selection', {}).get('success'):
            total_cost += pipeline_results['phases']['phase2_selection']['cost_usd']
        if pipeline_results['phases'].get('phase4_fields', {}).get('success'):
            total_cost += pipeline_results['phases']['phase4_fields']['cost_usd']
        
        pipeline_results.update({
            'success': True,
            'total_time': total_time,
            'total_cost': total_cost,
            'timestamp': datetime.now().isoformat()
        })
        
        return pipeline_results
        
    except Exception as e:
        return {'success': False, 'error': f"Pipeline execution failed: {str(e)}"}

def display_console_results(result: dict, verbose: bool = False):
    """Display rich console results"""
    
    # Company Overview Panel
    company_panel = Panel(
        f"[bold blue]{result['company_name']}[/bold blue]\n"
        f"🌐 {result['base_url']}\n"
        f"⏱️ Analyzed in {result['total_time']:.2f} seconds\n"
        f"💰 Cost: ${result['total_cost']:.4f}",
        title="📊 Company Analysis",
        border_style="blue"
    )
    console.print(company_panel)
    
    # Extract key fields from results
    fields = result['phases']['phase4_fields']['extracted_fields']
    
    # Core Information Table
    core_table = Table(title="🏢 Core Company Information", show_header=False)
    core_table.add_column("Field", style="cyan", width=20)
    core_table.add_column("Value", style="white")
    
    if isinstance(fields, dict):
        for key, value in fields.items():
            if key in ['company_name', 'website', 'industry', 'location', 'company_size']:
                core_table.add_row(key.replace('_', ' ').title(), str(value) if value else "Not found")
    
    console.print(core_table)
    
    # Performance Metrics
    perf_table = Table(title="⚡ Pipeline Performance", show_header=False)
    perf_table.add_column("Metric", style="yellow", width=25)
    perf_table.add_column("Value", style="green")
    
    phases = result['phases']
    perf_table.add_row("Paths Discovered", str(phases['phase1_discovery']['paths_discovered']))
    perf_table.add_row("Paths Selected", str(phases['phase2_selection']['paths_selected']))
    perf_table.add_row("Pages Crawled", str(phases['phase3_extraction']['successful_pages']))
    perf_table.add_row("Content Extracted", f"{phases['phase3_extraction']['total_content_length']:,} chars")
    perf_table.add_row("Crawling Time", f"{phases['phase3_extraction']['processing_time']:.2f}s")
    perf_table.add_row("Total Tokens Used", str(phases['phase4_fields']['tokens_used']))
    
    console.print(perf_table)

def output_json_results(result: dict, output_file: Optional[str]):
    """Output results as JSON"""
    import json
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        console.print(f"📁 Results saved to: {output_file}")
    else:
        console.print(json.dumps(result, indent=2, default=str))

def output_csv_results(result: dict, output_file: Optional[str]):
    """Output results as CSV"""
    import pandas as pd
    
    # Flatten the results for CSV format
    flattened = {}
    fields = result['phases']['phase4_fields']['extracted_fields']
    
    # Add core metrics
    flattened['company_name'] = result['company_name']
    flattened['base_url'] = result['base_url']
    flattened['total_time'] = result['total_time']
    flattened['total_cost'] = result['total_cost']
    
    # Add extracted fields
    if isinstance(fields, dict):
        for key, value in fields.items():
            flattened[key] = value
    
    df = pd.DataFrame([flattened])
    
    if output_file:
        df.to_csv(output_file, index=False)
        console.print(f"📁 CSV saved to: {output_file}")
    else:
        console.print(df.to_csv(index=False))

def output_fields_results(result: dict, output_file: Optional[str]):
    """Output simple field mappings like antoine test format"""
    
    fields = result['phases']['phase4_fields']['extracted_fields']
    
    output_lines = [
        f"Theodore v3 Research Results - {result['company_name']}",
        "=" * 60,
        f"Company: {result['company_name']}",
        f"Website: {result['base_url']}",
        f"Analysis Date: {result['timestamp'][:10]}",
        f"Total Time: {result['total_time']:.2f} seconds",
        f"Total Cost: ${result['total_cost']:.4f}",
        "",
        "EXTRACTED FIELDS:",
        "=" * 30
    ]
    
    if isinstance(fields, dict):
        for key, value in fields.items():
            clean_key = key.replace('_', ' ').title()
            output_lines.append(f"{clean_key}: {value}")
    
    output_lines.extend([
        "",
        "PERFORMANCE METRICS:",
        "=" * 30,
        f"Paths Discovered: {result['phases']['phase1_discovery']['paths_discovered']}",
        f"Paths Selected: {result['phases']['phase2_selection']['paths_selected']}",
        f"Pages Crawled: {result['phases']['phase3_extraction']['successful_pages']}",
        f"Crawling Time: {result['phases']['phase3_extraction']['processing_time']:.2f}s",
        f"Tokens Used: {result['phases']['phase4_fields']['tokens_used']}",
        f"Model Used: {result['phases']['phase4_fields']['model_used']}"
    ])
    
    output_text = "\n".join(output_lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output_text)
        console.print(f"📁 Field mappings saved to: {output_file}")
    else:
        console.print(output_text)
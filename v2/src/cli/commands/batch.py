"""
Theodore CLI Batch Processing Commands.

Provides comprehensive batch processing capabilities for company research
with job management, progress tracking, and multiple output formats.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.text import Text

from src.core.domain.entities.batch_job import (
    BatchJob, BatchInputSource, BatchOutputDestination,
    InputSourceType, OutputDestinationType, BatchJobPriority,
    BatchConfiguration
)
from src.core.use_cases.batch_processing import BatchProcessingUseCase
from src.infrastructure.container.application import ApplicationContainer as Container
from src.cli.utils.output import OutputFormat
from src.cli.utils.validation import validate_file_path

console = Console()


class BatchCommand:
    """
    Advanced batch processing command with comprehensive job management,
    progress tracking, and multi-format support.
    """
    
    def __init__(self, container: Container):
        self.container = container
        self.batch_use_case = self._get_batch_use_case()
    
    def _get_batch_use_case(self) -> BatchProcessingUseCase:
        """Get batch processing use case from container"""
        try:
            research_use_case = self.container.get_research_use_case()
            discovery_use_case = self.container.get_discovery_use_case()
            
            return BatchProcessingUseCase(
                research_use_case=research_use_case,
                discovery_use_case=discovery_use_case
            )
        except Exception as e:
            console.print(f"❌ [red]Failed to initialize batch processing: {e}[/red]")
            raise
    
    async def execute_research_batch(
        self,
        input_file: str,
        output: str = "results.csv",
        format: str = "csv",
        concurrency: int = 5,
        timeout: int = 120,
        job_name: Optional[str] = None,
        checkpoint_interval: int = 10,
        cost_estimate: bool = False,
        dry_run: bool = False,
        verbose: bool = False,
        max_retries: int = 2,
        priority: str = "medium",
        **kwargs
    ) -> None:
        """Execute batch research processing with comprehensive options"""
        
        start_time = time.time()
        
        try:
            # Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                console.print(f"❌ [red]Input file not found: {input_file}[/red]")
                return
            
            if verbose:
                console.print(f"🔍 [blue]Starting batch research for:[/blue] {input_file}")
                console.print(f"📊 [blue]Concurrency:[/blue] {concurrency}")
                console.print(f"📁 [blue]Output:[/blue] {output}")
            
            # Create batch configuration
            input_source = BatchInputSource(
                type=InputSourceType.CSV_FILE,
                path=str(input_path.absolute())
            )
            
            output_destination = BatchOutputDestination(
                type=self._get_output_type(format),
                path=output
            )
            
            config = BatchConfiguration(
                max_concurrent=concurrency,
                timeout_per_company=timeout,
                checkpoint_interval=checkpoint_interval,
                max_retries=max_retries,
                enable_progress_tracking=True,
                include_metadata=True
            )
            
            # Dry run - validate input without processing
            if dry_run:
                await self._perform_dry_run(input_source, verbose)
                return
            
            # Cost estimation
            if cost_estimate:
                await self._show_cost_estimate(input_source, config)
                return
            
            # Start batch job
            batch_job = await self.batch_use_case.start_batch_research(
                input_source=input_source,
                output_destination=output_destination,
                job_name=job_name or f"Research batch {input_path.stem}",
                max_concurrent=concurrency,
                timeout_per_company=timeout,
                checkpoint_interval=checkpoint_interval,
                max_retries=max_retries
            )
            
            # Monitor progress
            await self._monitor_batch_progress(batch_job, verbose)
            
            # Display results
            elapsed_time = time.time() - start_time
            await self._display_batch_results(batch_job, elapsed_time)
            
        except Exception as e:
            console.print(f"❌ [red]Batch research failed: {str(e)}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
    
    def _get_output_type(self, format_str: str) -> OutputDestinationType:
        """Convert format string to output destination type"""
        format_mapping = {
            'csv': OutputDestinationType.CSV_FILE,
            'json': OutputDestinationType.JSON_FILE,
            'excel': OutputDestinationType.EXCEL_FILE,
            'sheets': OutputDestinationType.GOOGLE_SHEETS
        }
        return format_mapping.get(format_str.lower(), OutputDestinationType.CSV_FILE)
    
    async def _perform_dry_run(self, input_source: BatchInputSource, verbose: bool) -> None:
        """Perform dry run validation of input data"""
        console.print("🔍 [blue]Performing dry run validation...[/blue]")
        
        company_count = 0
        validation_errors = []
        
        try:
            from src.core.use_cases.batch_processing import BatchInputProcessor
            processor = BatchInputProcessor()
            
            async for company_data in processor.read_companies_from_csv(input_source.path):
                company_count += 1
                
                # Validate company data
                if not company_data.get('company_name'):
                    validation_errors.append(f"Row {company_count}: Missing company name")
                
                if verbose and company_count <= 5:
                    console.print(f"  📋 Company {company_count}: {company_data['company_name']}")
            
            # Display results
            console.print(f"✅ [green]Dry run completed[/green]")
            console.print(f"📊 [blue]Total companies found:[/blue] {company_count}")
            
            if validation_errors:
                console.print(f"⚠️ [yellow]Validation warnings:[/yellow] {len(validation_errors)}")
                for error in validation_errors[:10]:  # Show first 10 errors
                    console.print(f"  • {error}")
            else:
                console.print("✅ [green]All companies passed validation[/green]")
                
        except Exception as e:
            console.print(f"❌ [red]Dry run failed: {e}[/red]")
    
    async def _show_cost_estimate(
        self, 
        input_source: BatchInputSource, 
        config: BatchConfiguration
    ) -> None:
        """Show cost estimate for batch processing"""
        console.print("💰 [blue]Calculating cost estimate...[/blue]")
        
        try:
            from src.core.use_cases.batch_processing import BatchInputProcessor
            processor = BatchInputProcessor()
            
            company_count = 0
            async for _ in processor.read_companies_from_csv(input_source.path):
                company_count += 1
            
            # Rough cost estimation (this would use actual cost models)
            estimated_cost_per_company = 0.15  # Example cost
            total_estimated_cost = company_count * estimated_cost_per_company
            
            # Estimated time calculation
            estimated_time_per_company = 45  # seconds
            total_estimated_time = (company_count * estimated_time_per_company) / config.max_concurrent
            estimated_hours = total_estimated_time / 3600
            
            # Display cost estimate
            cost_panel = Panel(
                f"📊 Companies to process: [bold]{company_count}[/bold]\n"
                f"💰 Estimated cost: [bold]${total_estimated_cost:.2f}[/bold]\n"
                f"⏱️ Estimated time: [bold]{estimated_hours:.1f} hours[/bold]\n"
                f"🔄 Concurrency: [bold]{config.max_concurrent}[/bold]\n"
                f"⚡ Rate: [bold]{60/estimated_time_per_company:.1f} companies/min[/bold]",
                title="💰 Batch Processing Cost Estimate",
                border_style="blue"
            )
            console.print(cost_panel)
            
            # Ask for confirmation
            if not click.confirm("Do you want to proceed with batch processing?"):
                console.print("❌ [yellow]Batch processing cancelled[/yellow]")
                return
                
        except Exception as e:
            console.print(f"❌ [red]Cost estimation failed: {e}[/red]")
    
    async def _monitor_batch_progress(self, batch_job: BatchJob, verbose: bool) -> None:
        """Monitor batch job progress with live updates"""
        
        def create_progress_panel(job: BatchJob) -> Panel:
            """Create progress display panel"""
            progress_info = job.progress
            
            # Progress bar representation
            progress_bar = "█" * int(progress_info.completion_percentage / 2)
            progress_bar += "░" * (50 - len(progress_bar))
            
            content = (
                f"📊 Progress: [{progress_bar}] {progress_info.completion_percentage:.1f}%\n"
                f"✅ Completed: {progress_info.completed_companies}/{progress_info.total_companies}\n"
                f"❌ Failed: {progress_info.failed_companies}\n"
                f"⚡ Rate: {progress_info.processing_rate:.1f} companies/min\n"
                f"💰 Cost: ${progress_info.cost_accumulated:.2f}\n"
                f"🔄 Current: {progress_info.current_company or 'Waiting...'}"
            )
            
            if progress_info.estimated_completion:
                content += f"\n⏰ ETA: {progress_info.estimated_completion.strftime('%H:%M:%S')}"
            
            return Panel(
                content,
                title=f"🚀 Batch Job: {batch_job.job_name}",
                border_style="blue"
            )
        
        # Monitor with live updates
        with Live(create_progress_panel(batch_job), refresh_per_second=2) as live:
            while not batch_job.is_terminal:
                await asyncio.sleep(2)
                
                # Refresh job status
                current_job = await self.batch_use_case.get_job_status(batch_job.job_id)
                if current_job:
                    batch_job = current_job
                
                # Update display
                live.update(create_progress_panel(batch_job))
                
                if verbose and batch_job.progress.current_company:
                    console.print(f"🔍 Processing: {batch_job.progress.current_company}")
    
    async def _display_batch_results(self, batch_job: BatchJob, elapsed_time: float) -> None:
        """Display comprehensive batch processing results"""
        
        result_summary = batch_job.result_summary
        if not result_summary:
            console.print("⚠️ [yellow]No result summary available[/yellow]")
            return
        
        # Create results table
        results_table = Table(title="📊 Batch Processing Results", border_style="green")
        results_table.add_column("Metric", style="bold blue")
        results_table.add_column("Value", style="green")
        
        results_table.add_row("Total Companies", str(result_summary.total_processed))
        results_table.add_row("Successful", str(result_summary.successful_results))
        results_table.add_row("Failed", str(result_summary.failed_results))
        results_table.add_row("Success Rate", f"{result_summary.success_rate:.1f}%")
        results_table.add_row("Total Time", f"{elapsed_time:.1f}s")
        results_table.add_row("Avg Time/Company", f"{result_summary.average_processing_time:.1f}s")
        results_table.add_row("Total Cost", f"${result_summary.total_cost:.2f}")
        results_table.add_row("Cost/Company", f"${result_summary.cost_per_company:.2f}")
        results_table.add_row("Data Quality", f"{result_summary.data_quality_score:.2f}")
        
        console.print(results_table)
        
        # Show error summary if there were failures
        if result_summary.failed_results > 0 and result_summary.most_common_errors:
            error_panel = Panel(
                "\n".join([f"• {error}" for error in result_summary.most_common_errors[:5]]),
                title="❌ Most Common Errors",
                border_style="red"
            )
            console.print(error_panel)
        
        # Show output file information
        if batch_job.output_destination.path:
            console.print(f"💾 [green]Results saved to:[/green] {batch_job.output_destination.path}")
    
    async def list_batch_jobs(self, all_jobs: bool = False, verbose: bool = False) -> None:
        """List batch jobs with status information"""
        
        active_jobs = self.batch_use_case.list_active_jobs()
        
        if not active_jobs:
            console.print("📭 [yellow]No active batch jobs found[/yellow]")
            return
        
        # Create jobs table
        jobs_table = Table(title="📋 Batch Jobs", border_style="blue")
        jobs_table.add_column("Job ID", style="bold")
        jobs_table.add_column("Name", style="cyan")
        jobs_table.add_column("Type", style="green")
        jobs_table.add_column("Status", style="yellow")
        jobs_table.add_column("Progress", style="blue")
        jobs_table.add_column("Created", style="dim")
        
        for job in active_jobs:
            progress_str = f"{job.progress.completion_percentage:.1f}%"
            if job.progress.total_companies > 0:
                progress_str += f" ({job.progress.completed_companies}/{job.progress.total_companies})"
            
            # Status color coding
            status_display = job.status.value
            if job.status.value == "completed":
                status_display = f"[green]{status_display}[/green]"
            elif job.status.value == "failed":
                status_display = f"[red]{status_display}[/red]"
            elif job.status.value == "running":
                status_display = f"[blue]{status_display}[/blue]"
            
            jobs_table.add_row(
                job.job_id[:8] + "...",
                job.job_name or "Unnamed",
                job.job_type.value,
                status_display,
                progress_str,
                job.created_at.strftime("%H:%M:%S")
            )
        
        console.print(jobs_table)
    
    async def get_job_status(self, job_id: str, verbose: bool = False) -> None:
        """Get detailed status of a specific batch job"""
        
        job = await self.batch_use_case.get_job_status(job_id)
        if not job:
            console.print(f"❌ [red]Job not found: {job_id}[/red]")
            return
        
        # Display detailed job information
        job_info = job.to_summary_dict()
        
        status_panel = Panel(
            f"🆔 Job ID: {job_info['job_id']}\n"
            f"📝 Name: {job_info['job_name']}\n"
            f"🔧 Type: {job_info['job_type']}\n"
            f"📊 Status: {job_info['status']}\n"
            f"📈 Progress: {job_info['progress']['completion_percentage']:.1f}%\n"
            f"✅ Completed: {job_info['progress']['completed']}\n"
            f"❌ Failed: {job_info['progress']['failed']}\n"
            f"📊 Total: {job_info['progress']['total']}\n"
            f"💰 Cost: ${job_info['cost_accumulated']:.2f}\n"
            f"📅 Created: {job_info['created_at']}\n"
            f"📁 Input: {job_info['input_source']}\n"
            f"📄 Output: {job_info['output_destination']}",
            title=f"📋 Job Status: {job_id[:8]}...",
            border_style="blue"
        )
        
        console.print(status_panel)
        
        if verbose and job.progress.errors_by_type:
            error_table = Table(title="❌ Error Summary", border_style="red")
            error_table.add_column("Error Type", style="bold red")
            error_table.add_column("Count", style="yellow")
            
            for error_type, count in job.progress.errors_by_type.items():
                error_table.add_row(error_type, str(count))
            
            console.print(error_table)
    
    async def cancel_job(self, job_id: str) -> None:
        """Cancel a running batch job"""
        
        success = await self.batch_use_case.cancel_job(job_id)
        if success:
            console.print(f"✅ [green]Job cancelled successfully: {job_id}[/green]")
        else:
            console.print(f"❌ [red]Failed to cancel job (not found or not active): {job_id}[/red]")
    
    async def pause_job(self, job_id: str) -> None:
        """Pause a running batch job"""
        
        success = await self.batch_use_case.pause_job(job_id)
        if success:
            console.print(f"⏸️ [yellow]Job paused successfully: {job_id}[/yellow]")
        else:
            console.print(f"❌ [red]Failed to pause job (not found or not running): {job_id}[/red]")
    
    async def resume_job(self, job_id: str) -> None:
        """Resume a paused batch job"""
        
        success = await self.batch_use_case.resume_job(job_id)
        if success:
            console.print(f"▶️ [green]Job resumed successfully: {job_id}[/green]")
        else:
            console.print(f"❌ [red]Failed to resume job (not found or not resumable): {job_id}[/red]")


# Click command group for batch operations
@click.group()
@click.pass_context
def batch(ctx):
    """
    Batch processing commands for Theodore v2.
    
    Process multiple companies efficiently with job management,
    progress tracking, and comprehensive error handling.
    """
    pass


@batch.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='results.csv', help='Output file path')
@click.option('--format', type=click.Choice(['csv', 'json', 'excel'], case_sensitive=False), 
              default='csv', help='Output format')
@click.option('--concurrency', type=int, default=5, help='Maximum concurrent operations')
@click.option('--timeout', type=int, default=120, help='Timeout per company (seconds)')
@click.option('--job-name', type=str, help='Custom name for the batch job')
@click.option('--checkpoint-interval', type=int, default=10, help='Save progress every N companies')
@click.option('--cost-estimate', is_flag=True, help='Show cost estimate before processing')
@click.option('--dry-run', is_flag=True, help='Validate input without processing')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--max-retries', type=int, default=2, help='Maximum retry attempts per company')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high'], case_sensitive=False),
              default='medium', help='Job priority level')
@click.pass_context
def research(ctx, input_file: str, output: str, format: str, concurrency: int, 
             timeout: int, job_name: Optional[str], checkpoint_interval: int,
             cost_estimate: bool, dry_run: bool, verbose: bool, max_retries: int,
             priority: str) -> None:
    """
    Process companies for research intelligence from CSV file.
    
    Examples:
    
    \\b
    # Basic batch research
    theodore batch research companies.csv
    
    \\b
    # Custom output and concurrency
    theodore batch research companies.csv --output results.json --format json --concurrency 10
    
    \\b
    # Cost estimation before processing
    theodore batch research companies.csv --cost-estimate
    
    \\b
    # Dry run to validate input
    theodore batch research companies.csv --dry-run
    """
    
    # Get container from context
    container = ctx.obj['container']
    
    # Create and execute command
    command = BatchCommand(container)
    
    # Run the async command
    asyncio.run(command.execute_research_batch(
        input_file=input_file,
        output=output,
        format=format,
        concurrency=concurrency,
        timeout=timeout,
        job_name=job_name,
        checkpoint_interval=checkpoint_interval,
        cost_estimate=cost_estimate,
        dry_run=dry_run,
        verbose=verbose,
        max_retries=max_retries,
        priority=priority
    ))


@batch.command()
@click.option('--all', is_flag=True, help='Show all jobs (including completed)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.pass_context
def list_jobs(ctx, all: bool, verbose: bool) -> None:
    """List batch jobs with status information."""
    
    container = ctx.obj['container']
    command = BatchCommand(container)
    
    asyncio.run(command.list_batch_jobs(all_jobs=all, verbose=verbose))


@batch.command()
@click.argument('job_id', type=str)
@click.option('--verbose', '-v', is_flag=True, help='Show detailed status including errors')
@click.pass_context
def status(ctx, job_id: str, verbose: bool) -> None:
    """Get detailed status of a specific batch job."""
    
    container = ctx.obj['container']
    command = BatchCommand(container)
    
    asyncio.run(command.get_job_status(job_id, verbose=verbose))


@batch.command()
@click.argument('job_id', type=str)
@click.pass_context
def cancel(ctx, job_id: str) -> None:
    """Cancel a running batch job."""
    
    container = ctx.obj['container']
    command = BatchCommand(container)
    
    asyncio.run(command.cancel_job(job_id))


@batch.command()
@click.argument('job_id', type=str)
@click.pass_context
def pause(ctx, job_id: str) -> None:
    """Pause a running batch job."""
    
    container = ctx.obj['container']
    command = BatchCommand(container)
    
    asyncio.run(command.pause_job(job_id))


@batch.command()
@click.argument('job_id', type=str)
@click.pass_context
def resume(ctx, job_id: str) -> None:
    """Resume a paused batch job."""
    
    container = ctx.obj['container']
    command = BatchCommand(container)
    
    asyncio.run(command.resume_job(job_id))
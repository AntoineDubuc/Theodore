"""
CLI error handling utilities for Theodore v2.

This module provides comprehensive error handling with user-friendly messages,
actionable suggestions, and graceful degradation strategies.
"""

import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box


console = Console()


class ErrorContext:
    """Context information for better error handling"""
    
    def __init__(
        self,
        operation: str,
        entity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.entity = entity
        self.details = details or {}


class CLIErrorHandler:
    """Comprehensive CLI error handler with user-friendly messaging"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.error_mappings = self._initialize_error_mappings()
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        show_suggestions: bool = True
    ) -> None:
        """Handle an error with appropriate user messaging"""
        
        error_name = type(error).__name__
        error_info = self.error_mappings.get(error_name, self._get_generic_error_info())
        
        # Create error panel
        self._display_error_panel(error, error_info, context)
        
        # Show technical details if verbose
        if self.verbose:
            self._display_technical_details(error)
        
        # Show suggestions if requested
        if show_suggestions:
            self._display_suggestions(error_info, context)
    
    def handle_validation_error(
        self,
        field: str,
        value: Any,
        expected: str,
        context: Optional[ErrorContext] = None
    ) -> None:
        """Handle validation errors with specific field information"""
        
        panel = Panel(
            f"[red]=� Validation Error[/red]\n\n"
            f"Field: [cyan]{field}[/cyan]\n"
            f"Value: [yellow]{value}[/yellow]\n"
            f"Expected: [green]{expected}[/green]\n\n"
            "Please check your input and try again.",
            title="Input Validation Failed",
            border_style="red"
        )
        
        console.print()
        console.print(panel)
        
        if context:
            self._display_context_suggestions(context)
    
    def handle_network_error(
        self,
        error: Exception,
        url: Optional[str] = None,
        operation: Optional[str] = None
    ) -> None:
        """Handle network-related errors with specific guidance"""
        
        content = "[red]< Network Error[/red]\n\n"
        
        if url:
            content += f"URL: [cyan]{url}[/cyan]\n"
        if operation:
            content += f"Operation: [yellow]{operation}[/yellow]\n"
        
        content += f"Error: {str(error)}\n\n"
        content += "" Check your internet connection\n"
        content += "" Verify the URL is accessible\n"
        content += "" Try again in a few moments\n"
        content += "" Check firewall/proxy settings"
        
        panel = Panel(
            content,
            title="Network Connection Problem",
            border_style="red"
        )
        
        console.print()
        console.print(panel)
    
    def handle_authentication_error(
        self,
        provider: Optional[str] = None,
        api_key_hint: Optional[str] = None
    ) -> None:
        """Handle authentication errors with provider-specific guidance"""
        
        content = "[red]= Authentication Error[/red]\n\n"
        
        if provider:
            content += f"Provider: [cyan]{provider}[/cyan]\n"
        if api_key_hint:
            content += f"API Key: [yellow]{api_key_hint}...{api_key_hint[-4:]}[/yellow]\n"
        
        content += "\n"
        content += "" Check your API credentials in configuration\n"
        content += "" Verify API key permissions and quotas\n"
        content += "" Ensure all required environment variables are set\n"
        content += "" Run 'theodore config validate' to check configuration"
        
        panel = Panel(
            content,
            title="Authentication Failed",
            border_style="red"
        )
        
        console.print()
        console.print(panel)
    
    def handle_timeout_error(
        self,
        operation: str,
        timeout: int,
        suggestions: Optional[List[str]] = None
    ) -> None:
        """Handle timeout errors with operation-specific guidance"""
        
        content = f"[yellow]� Operation Timeout[/yellow]\n\n"
        content += f"Operation: [cyan]{operation}[/cyan]\n"
        content += f"Timeout: [yellow]{timeout} seconds[/yellow]\n\n"
        
        if suggestions:
            for suggestion in suggestions:
                content += f"" {suggestion}\n"
        else:
            content += "" Try increasing timeout with --timeout option\n"
            content += "" Check if the target service is responsive\n"
            content += "" Consider breaking the operation into smaller parts\n"
            content += "" Try again during off-peak hours"
        
        panel = Panel(
            content,
            title="Timeout Error",
            border_style="yellow"
        )
        
        console.print()
        console.print(panel)
    
    def handle_quota_error(
        self,
        provider: str,
        quota_type: str,
        current: Optional[int] = None,
        limit: Optional[int] = None
    ) -> None:
        """Handle quota exceeded errors"""
        
        content = f"[red]=� Quota Exceeded[/red]\n\n"
        content += f"Provider: [cyan]{provider}[/cyan]\n"
        content += f"Quota Type: [yellow]{quota_type}[/yellow]\n"
        
        if current is not None and limit is not None:
            content += f"Usage: [red]{current}/{limit}[/red]\n"
        
        content += "\n"
        content += "" Wait for quota reset period\n"
        content += "" Upgrade your plan for higher limits\n"
        content += "" Use rate limiting to spread requests\n"
        content += "" Consider using multiple API keys"
        
        panel = Panel(
            content,
            title="API Quota Exceeded",
            border_style="red"
        )
        
        console.print()
        console.print(panel)
    
    def display_recovery_suggestions(
        self,
        operation: str,
        entity: Optional[str] = None,
        custom_suggestions: Optional[List[str]] = None
    ) -> None:
        """Display recovery suggestions for failed operations"""
        
        title = f"=� Recovery Suggestions"
        if entity:
            title += f" for '{entity}'"
        
        if custom_suggestions:
            suggestions = custom_suggestions
        else:
            suggestions = self._get_default_recovery_suggestions(operation)
        
        console.print(f"\n[bold]{title}:[/bold]")
        for suggestion in suggestions:
            console.print(f"" {suggestion}")
    
    def _initialize_error_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error type mappings"""
        return {
            'ConnectionError': {
                'title': 'Network Connection Error',
                'icon': '<',
                'color': 'red',
                'suggestions': [
                    'Check your internet connection',
                    'Verify the website URL is accessible',
                    'Try again in a few moments',
                    'Use --no-domain-discovery flag to skip website validation'
                ]
            },
            'TimeoutError': {
                'title': 'Operation Timeout',
                'icon': '�',
                'color': 'yellow',
                'suggestions': [
                    'Try increasing timeout with --timeout <seconds>',
                    'Check if the target website is responsive',
                    'Consider using --no-domain-discovery for faster research',
                    'Break large operations into smaller parts'
                ]
            },
            'ValidationError': {
                'title': 'Input Validation Error',
                'icon': '=�',
                'color': 'orange',
                'suggestions': [
                    'Check company name spelling and format',
                    'Verify website URL format (include http/https)',
                    'Remove special characters from company name',
                    'Try with quotes around company name if it contains spaces'
                ]
            },
            'AuthenticationError': {
                'title': 'Authentication Error',
                'icon': '=',
                'color': 'red',
                'suggestions': [
                    'Check your API credentials in configuration',
                    'Verify API key permissions and quotas',
                    'Ensure all required environment variables are set',
                    "Run 'theodore config validate' to check configuration"
                ]
            },
            'PermissionError': {
                'title': 'Permission Error',
                'icon': '=�',
                'color': 'red',
                'suggestions': [
                    'Check file and directory permissions',
                    'Run with appropriate user privileges',
                    'Verify write access to output directories',
                    'Check if files are locked by other processes'
                ]
            },
            'FileNotFoundError': {
                'title': 'File Not Found',
                'icon': '=�',
                'color': 'red',
                'suggestions': [
                    'Verify the file path is correct',
                    'Check if the file exists',
                    'Use absolute path instead of relative path',
                    'Check file permissions and access rights'
                ]
            },
            'JSONDecodeError': {
                'title': 'JSON Format Error',
                'icon': '=�',
                'color': 'red',
                'suggestions': [
                    'Check JSON file format and syntax',
                    'Verify file is not corrupted',
                    'Use a JSON validator to check format',
                    'Check for trailing commas or missing brackets'
                ]
            }
        }
    
    def _get_generic_error_info(self) -> Dict[str, Any]:
        """Get generic error information for unknown error types"""
        return {
            'title': 'Unexpected Error',
            'icon': 'L',
            'color': 'red',
            'suggestions': [
                'Try again with --verbose flag for detailed logs',
                'Check the input parameters',
                'Verify your internet connection',
                'Contact support if the problem persists'
            ]
        }
    
    def _display_error_panel(
        self,
        error: Exception,
        error_info: Dict[str, Any],
        context: Optional[ErrorContext]
    ) -> None:
        """Display main error panel"""
        
        content = f"[{error_info['color']}]{error_info['icon']} {error_info['title']}[/{error_info['color']}]\n\n"
        
        if context:
            if context.operation:
                content += f"Operation: [cyan]{context.operation}[/cyan]\n"
            if context.entity:
                content += f"Entity: [yellow]{context.entity}[/yellow]\n"
        
        content += f"Error: {str(error)}\n\n"
        
        # Add suggestions
        for suggestion in error_info['suggestions']:
            content += f"" {suggestion}\n"
        
        panel = Panel(
            content,
            title=error_info['title'],
            border_style=error_info['color']
        )
        
        console.print()
        console.print(panel)
    
    def _display_technical_details(self, error: Exception) -> None:
        """Display technical error details for verbose mode"""
        
        content = f"[dim]Exception Type:[/dim] {type(error).__name__}\n"
        content += f"[dim]Error Message:[/dim] {str(error)}\n"
        
        if hasattr(error, '__cause__') and error.__cause__:
            content += f"[dim]Caused by:[/dim] {error.__cause__}\n"
        
        # Add traceback
        content += "\n[dim]Traceback:[/dim]\n"
        tb_lines = traceback.format_tb(error.__traceback__)
        for line in tb_lines[-3:]:  # Show last 3 stack frames
            content += f"[dim]{line.strip()}[/dim]\n"
        
        panel = Panel(
            content,
            title="Technical Details",
            border_style="dim",
            padding=(1, 2)
        )
        
        console.print()
        console.print(panel)
    
    def _display_suggestions(
        self,
        error_info: Dict[str, Any],
        context: Optional[ErrorContext]
    ) -> None:
        """Display additional context-specific suggestions"""
        
        if context and context.operation:
            additional_suggestions = self._get_operation_suggestions(context.operation)
            if additional_suggestions:
                console.print(f"\n[bold]=� Additional suggestions for '{context.operation}':[/bold]")
                for suggestion in additional_suggestions:
                    console.print(f"" {suggestion}")
    
    def _display_context_suggestions(self, context: ErrorContext) -> None:
        """Display context-specific suggestions"""
        
        if context.operation:
            suggestions = self._get_operation_suggestions(context.operation)
            if suggestions:
                console.print(f"\n[bold]=� Suggestions for '{context.operation}':[/bold]")
                for suggestion in suggestions:
                    console.print(f"" {suggestion}")
    
    def _get_operation_suggestions(self, operation: str) -> List[str]:
        """Get operation-specific suggestions"""
        
        operation_suggestions = {
            'research': [
                'Try with simplified company name',
                'Add or remove website URL',
                'Use --no-domain-discovery flag',
                'Increase timeout with --timeout 120'
            ],
            'batch_research': [
                'Check input file format (CSV or JSON)',
                'Reduce parallel job count',
                'Split large files into smaller batches',
                'Verify all company names in the file'
            ],
            'export': [
                'Check output directory permissions',
                'Verify disk space availability',
                'Use absolute path for output file',
                'Choose different output format'
            ],
            'config': [
                'Check environment variables',
                'Verify API key format',
                'Test configuration with --validate flag',
                'Check configuration file syntax'
            ]
        }
        
        return operation_suggestions.get(operation, [])
    
    def _get_default_recovery_suggestions(self, operation: str) -> List[str]:
        """Get default recovery suggestions for operation"""
        
        default_suggestions = [
            'Try the operation again',
            'Check input parameters',
            'Verify system requirements',
            'Contact support if problem persists'
        ]
        
        return self._get_operation_suggestions(operation) or default_suggestions


@contextmanager
def cli_error_context(
    operation: str,
    entity: Optional[str] = None,
    verbose: bool = False,
    show_suggestions: bool = True
):
    """Context manager for handling CLI errors gracefully"""
    
    error_handler = CLIErrorHandler(verbose=verbose)
    context = ErrorContext(operation=operation, entity=entity)
    
    try:
        yield error_handler
    except click.Abort:
        # Re-raise click.Abort to maintain CLI behavior
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]�  Operation cancelled by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        error_handler.handle_error(e, context, show_suggestions)
        raise click.Abort()


def handle_click_exception(func):
    """Decorator for handling click command exceptions"""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except click.ClickException:
            # Let click handle its own exceptions
            raise
        except Exception as e:
            error_handler = CLIErrorHandler(verbose=kwargs.get('verbose', False))
            context = ErrorContext(operation=func.__name__)
            error_handler.handle_error(e, context)
            raise click.Abort()
    
    return wrapper


# Utility functions for common error scenarios
def suggest_command_alternatives(failed_command: str) -> List[str]:
    """Suggest alternative commands based on failed command"""
    
    command_alternatives = {
        'research': ['research --help', 'config validate', 'version'],
        'batch': ['research', 'export', 'config'],
        'export': ['research', 'config', 'help'],
        'config': ['research --help', 'version', 'help']
    }
    
    return command_alternatives.get(failed_command, ['help', 'version'])


def create_error_report(
    error: Exception,
    context: Optional[ErrorContext] = None,
    system_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create structured error report for debugging"""
    
    report = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': str(datetime.now()),
        'traceback': traceback.format_exception(type(error), error, error.__traceback__)
    }
    
    if context:
        report['context'] = {
            'operation': context.operation,
            'entity': context.entity,
            'details': context.details
        }
    
    if system_info:
        report['system_info'] = system_info
    
    return report


def display_error_summary(errors: List[Exception], operation: str) -> None:
    """Display summary of multiple errors"""
    
    if not errors:
        return
    
    table = Table(
        title=f"Error Summary for {operation}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold red"
    )
    
    table.add_column("Error Type", style="red")
    table.add_column("Count", style="yellow")
    table.add_column("Sample Message", style="white")
    
    # Group errors by type
    error_counts = {}
    error_samples = {}
    
    for error in errors:
        error_type = type(error).__name__
        error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        if error_type not in error_samples:
            error_samples[error_type] = str(error)[:100]
    
    # Add rows to table
    for error_type, count in error_counts.items():
        sample = error_samples[error_type]
        if len(sample) > 50:
            sample = sample[:47] + "..."
        
        table.add_row(error_type, str(count), sample)
    
    console.print()
    console.print(table)
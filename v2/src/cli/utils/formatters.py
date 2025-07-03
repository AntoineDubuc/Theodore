"""
CLI output formatters for Theodore v2.

This module provides utilities for formatting research results in multiple
output formats including table, JSON, YAML, and markdown.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


console = Console()


class OutputFormatter(ABC):
    """Abstract base class for output formatters"""
    
    @abstractmethod
    def format(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data for output"""
        pass
    
    @abstractmethod
    def display(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Display formatted data to console"""
        pass
    
    @abstractmethod
    def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        """Save formatted data to file"""
        pass


class TableFormatter(OutputFormatter):
    """Rich table formatter for console display"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def format(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as string representation (for saving)"""
        if isinstance(data, list):
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def display(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Display data as rich table"""
        if isinstance(data, list):
            self._display_multiple_results(data)
        else:
            self._display_single_result(data)
    
    def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        """Save table data as JSON to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]=¾ Results saved to: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]L Failed to save results: {e}[/red]")
    
    def _display_single_result(self, data: Dict[str, Any]) -> None:
        """Display single result as table"""
        table = Table(
            title=f"Company Research: {data.get('company_name', 'Unknown')}",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue"
        )
        
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        # Define field display order and labels
        field_labels = {
            'company_name': 'Company Name',
            'website': 'Website',
            'industry': 'Industry',
            'description': 'Description',
            'founding_year': 'Founded',
            'location': 'Location',
            'employee_count': 'Employees',
            'revenue_range': 'Revenue Range',
            'business_model': 'Business Model',
            'research_confidence': 'Confidence Score',
            'research_timestamp': 'Research Date'
        }
        
        for field, value in data.items():
            if not self.verbose and field in ['research_timestamp', 'research_confidence']:
                continue
                
            label = field_labels.get(field, field.replace('_', ' ').title())
            display_value = str(value) if value is not None else "[dim]Not available[/dim]"
            
            # Truncate long descriptions for table display
            if field == 'description' and len(display_value) > 100:
                display_value = display_value[:97] + "..."
            
            table.add_row(label, display_value)
        
        console.print()
        console.print(table)
    
    def _display_multiple_results(self, data: List[Dict[str, Any]]) -> None:
        """Display multiple results as table"""
        if not data:
            console.print("[yellow]No results to display[/yellow]")
            return
        
        # Create table with dynamic columns based on first result
        first_result = data[0]
        table = Table(
            title=f"Research Results ({len(data)} companies)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold blue"
        )
        
        # Add columns for key fields
        key_fields = ['company_name', 'website', 'industry', 'location', 'business_model']
        field_labels = {
            'company_name': 'Company',
            'website': 'Website',
            'industry': 'Industry',
            'location': 'Location',
            'business_model': 'Business Model'
        }
        
        for field in key_fields:
            if field in first_result:
                label = field_labels.get(field, field.replace('_', ' ').title())
                table.add_column(label, style="white")
        
        # Add rows
        for result in data:
            row_values = []
            for field in key_fields:
                if field in result:
                    value = str(result[field]) if result[field] is not None else "N/A"
                    # Truncate long values
                    if len(value) > 30:
                        value = value[:27] + "..."
                    row_values.append(value)
            
            table.add_row(*row_values)
        
        console.print()
        console.print(table)


class JSONFormatter(OutputFormatter):
    """JSON formatter for structured output"""
    
    def format(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as JSON string"""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def display(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Display JSON to console"""
        console.print(self.format(data))
    
    def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        """Save JSON to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]=¾ Results saved to: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]L Failed to save results: {e}[/red]")


class YAMLFormatter(OutputFormatter):
    """YAML formatter for human-readable structured output"""
    
    def format(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as YAML string"""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def display(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Display YAML to console"""
        console.print(self.format(data))
    
    def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        """Save YAML to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            console.print(f"[green]=¾ Results saved to: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]L Failed to save results: {e}[/red]")


class MarkdownFormatter(OutputFormatter):
    """Markdown formatter for documentation-friendly output"""
    
    def format(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as Markdown string"""
        if isinstance(data, list):
            return self._format_multiple_results(data)
        else:
            return self._format_single_result(data)
    
    def display(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Display Markdown to console"""
        console.print(self.format(data))
    
    def save(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        """Save Markdown to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.format(data))
            
            console.print(f"[green]=¾ Results saved to: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]L Failed to save results: {e}[/red]")
    
    def _format_single_result(self, data: Dict[str, Any]) -> str:
        """Format single result as Markdown"""
        company_name = data.get('company_name', 'Unknown Company')
        
        markdown = f"""# Company Research: {company_name}

## Basic Information
- **Company Name**: {data.get('company_name', 'N/A')}
- **Website**: {data.get('website', 'N/A')}
- **Industry**: {data.get('industry', 'N/A')}
- **Founded**: {data.get('founding_year', 'N/A')}
- **Location**: {data.get('location', 'N/A')}

## Business Details
- **Business Model**: {data.get('business_model', 'N/A')}
- **Employee Count**: {data.get('employee_count', 'N/A')}
- **Revenue Range**: {data.get('revenue_range', 'N/A')}

## Description
{data.get('description', 'No description available')}

## Research Metadata
- **Research Date**: {data.get('research_timestamp', 'N/A')}
- **Confidence Score**: {data.get('research_confidence', 'N/A')}
"""
        return markdown
    
    def _format_multiple_results(self, data: List[Dict[str, Any]]) -> str:
        """Format multiple results as Markdown"""
        markdown = f"""# Company Research Results

Research completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total companies: {len(data)}

---

"""
        
        for i, result in enumerate(data, 1):
            company_name = result.get('company_name', f'Company {i}')
            markdown += f"""## {i}. {company_name}

- **Website**: {result.get('website', 'N/A')}
- **Industry**: {result.get('industry', 'N/A')}
- **Location**: {result.get('location', 'N/A')}
- **Business Model**: {result.get('business_model', 'N/A')}

{result.get('description', 'No description available')[:200]}...

---

"""
        
        return markdown


class FormatterFactory:
    """Factory for creating output formatters"""
    
    _formatters = {
        'table': TableFormatter,
        'json': JSONFormatter,
        'yaml': YAMLFormatter,
        'markdown': MarkdownFormatter
    }
    
    @classmethod
    def create_formatter(
        self, 
        format_type: str, 
        verbose: bool = False
    ) -> OutputFormatter:
        """Create formatter instance"""
        format_type = format_type.lower()
        
        if format_type not in self._formatters:
            raise ValueError(f"Unsupported format: {format_type}")
        
        formatter_class = self._formatters[format_type]
        
        # Pass verbose flag to formatters that support it
        if format_type == 'table':
            return formatter_class(verbose=verbose)
        else:
            return formatter_class()
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported output formats"""
        return list(cls._formatters.keys())
    
    @classmethod
    def format_and_display(
        cls,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        format_type: str,
        save_path: Optional[str] = None,
        verbose: bool = False
    ) -> None:
        """Convenience method to format and display/save data"""
        formatter = cls.create_formatter(format_type, verbose=verbose)
        
        # Display to console
        formatter.display(data)
        
        # Save to file if requested
        if save_path:
            formatter.save(data, save_path)


# Utility functions for common formatting tasks
def format_company_summary(company_data: Dict[str, Any]) -> str:
    """Create a one-line summary of company data"""
    name = company_data.get('company_name', 'Unknown')
    industry = company_data.get('industry', 'Unknown Industry')
    location = company_data.get('location', 'Unknown Location')
    
    return f"{name} | {industry} | {location}"


def create_research_panel(
    company_name: str, 
    status: str, 
    details: Optional[str] = None
) -> Panel:
    """Create a rich panel for research status"""
    content = f"[bold]{company_name}[/bold]\n"
    content += f"Status: {status}\n"
    
    if details:
        content += f"Details: {details}"
    
    # Determine panel style based on status
    if "completed" in status.lower():
        border_style = "green"
        title = " Research Complete"
    elif "failed" in status.lower() or "error" in status.lower():
        border_style = "red"
        title = "L Research Failed"
    elif "progress" in status.lower() or "running" in status.lower():
        border_style = "yellow"
        title = "= Research In Progress"
    else:
        border_style = "blue"
        title = "=Ê Research Status"
    
    return Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2)
    )


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


def format_confidence_score(score: Optional[float]) -> str:
    """Format confidence score for display"""
    if score is None:
        return "N/A"
    
    percentage = int(score * 100)
    if percentage >= 90:
        return f"[green]{percentage}%[/green]"
    elif percentage >= 70:
        return f"[yellow]{percentage}%[/yellow]"
    else:
        return f"[red]{percentage}%[/red]"
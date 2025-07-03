"""
Output utilities for Theodore CLI.
"""

from enum import Enum
from rich.console import Console
from rich.theme import Theme
from typing import Any, Dict
from src.core.domain.entities.company import Company


class OutputFormat(Enum):
    """Available output formats for CLI commands."""
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"

# Custom theme for Theodore
theodore_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "progress": "blue",
    "header": "bold blue",
    "dim": "dim white"
})

console = Console(theme=theodore_theme)

def print_info(message: str):
    """Print info message with icon"""
    console.print(f"ℹ️  {message}", style="info")

def print_warning(message: str):
    """Print warning message with icon"""
    console.print(f"⚠️  {message}", style="warning")

def print_error(message: str):
    """Print error message with icon"""
    console.print(f"❌ {message}", style="error")

def print_success(message: str):
    """Print success message with icon"""
    console.print(f"✅ {message}", style="success")

def print_header(message: str):
    """Print header message"""
    console.print(f"\n{message}", style="header")

def format_dict_table(data: Dict[str, Any], title: str = "Results") -> None:
    """Format dictionary as a rich table"""
    from rich.table import Table
    
    table = Table(title=title)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in data.items():
        table.add_row(str(key), str(value))
    
    console.print(table)


def format_company_data(company: Company, output_format: OutputFormat) -> Dict[str, Any]:
    """Format company data for specific output format."""
    
    base_data = {
        'name': company.name,
        'website': company.website,
        'description': company.description
    }
    
    # Add any additional attributes that exist
    for attr in ['industry', 'size', 'location', 'founded_year', 'business_model']:
        if hasattr(company, attr):
            value = getattr(company, attr)
            if value is not None:
                # Handle enum values
                if hasattr(value, 'value'):
                    base_data[attr] = value.value
                else:
                    base_data[attr] = value
    
    return base_data
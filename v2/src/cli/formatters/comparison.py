"""
Comparison Formatter for Theodore CLI.

Provides side-by-side company analysis, similarity explanation visualization,
attribute comparison matrices, and difference highlighting.
"""

from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.align import Align

from src.core.domain.entities.company import Company


class ComparisonFormatter:
    """
    Formatter for side-by-side company comparisons with detailed
    similarity analysis and attribute visualization.
    """
    
    def __init__(self):
        self.console = Console()
    
    def format_company_comparison(
        self,
        target_company: Company,
        similar_companies: List[Company],
        similarity_scores: Dict[str, float],
        explanations: Optional[Dict[str, Dict[str, Any]]] = None,
        attributes: Optional[List[str]] = None
    ) -> Table:
        """
        Format side-by-side comparison of companies.
        
        Args:
            target_company: The reference company
            similar_companies: List of companies to compare
            similarity_scores: Similarity scores for each company
            explanations: Detailed similarity explanations
            attributes: Specific attributes to compare
            
        Returns:
            Rich table with company comparison
        """
        
        if attributes is None:
            attributes = [
                'name', 'website', 'industry', 'size', 'location',
                'founded_year', 'description'
            ]
        
        table = Table(
            title=f"🔍 Company Comparison Matrix",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            caption=f"Comparing {target_company.name} with {len(similar_companies)} similar companies"
        )
        
        # Add columns
        table.add_column("Attribute", style="bold white", min_width=15)
        table.add_column(f"🎯 {target_company.name}", style="bold green", min_width=20)
        
        # Add column for each similar company
        for i, company in enumerate(similar_companies[:4], 1):  # Limit to 4 for readability
            score = similarity_scores.get(company.name, 0.0)
            score_indicator = self._get_score_indicator(score)
            column_header = f"{score_indicator} {company.name}"
            table.add_column(column_header, style="white", min_width=20)
        
        # Add rows for each attribute
        for attr in attributes:
            if attr == 'similarity_score':
                continue  # Skip this as it's in the header
                
            row_data = [self._format_attribute_name(attr)]
            
            # Target company value
            target_value = self._get_company_attribute_value(target_company, attr)
            row_data.append(self._format_attribute_value(target_value, attr, is_target=True))
            
            # Similar companies values
            for company in similar_companies[:4]:
                value = self._get_company_attribute_value(company, attr)
                formatted_value = self._format_attribute_value(value, attr)
                
                # Highlight differences from target
                if self._values_differ(target_value, value, attr):
                    formatted_value = f"[yellow]{formatted_value}[/yellow]"
                
                row_data.append(formatted_value)
            
            table.add_row(*row_data)
        
        return table
    
    def format_similarity_breakdown(
        self,
        target_company: str,
        similar_company: str,
        similarity_score: float,
        explanation: Dict[str, Any]
    ) -> Panel:
        """
        Format detailed similarity breakdown between two companies.
        
        Args:
            target_company: Name of target company
            similar_company: Name of similar company
            similarity_score: Overall similarity score
            explanation: Detailed similarity explanation
            
        Returns:
            Rich panel with similarity breakdown
        """
        
        content = Text()
        
        # Header
        content.append(f"Similarity Analysis\n", style="bold cyan")
        content.append(f"{target_company} ↔ {similar_company}\n\n", style="bold white")
        
        # Overall score
        score_style = self._get_score_style(similarity_score)
        content.append(f"Overall Similarity: ", style="bold")
        content.append(f"{similarity_score:.2f} ", style=score_style)
        content.append(f"{self._create_score_bar(similarity_score)}\n\n", style=score_style)
        
        # Factor breakdown
        factors = explanation.get('factors', {})
        if factors:
            content.append("Factor Analysis:\n", style="bold yellow")
            
            # Sort factors by importance
            sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
            
            for factor, score in sorted_factors:
                factor_name = factor.replace('_', ' ').title()
                factor_style = self._get_score_style(score)
                score_bar = self._create_mini_score_bar(score)
                
                content.append(f"  • {factor_name:<20} ", style="white")
                content.append(f"{score:.2f} ", style=factor_style)
                content.append(f"{score_bar}\n", style="dim")
        
        # Natural language explanation
        if explanation.get('explanation'):
            content.append(f"\nDetailed Analysis:\n", style="bold green")
            content.append(f"{explanation['explanation']}\n", style="white")
        
        # Confidence and metadata
        confidence = explanation.get('confidence', 0.0)
        if confidence > 0:
            content.append(f"\nConfidence Level: ", style="bold")
            content.append(f"{confidence:.2f}", style=self._get_score_style(confidence))
        
        border_style = self._get_border_style_for_score(similarity_score)
        
        return Panel(
            content,
            title=f"📊 Similarity Breakdown",
            border_style=border_style,
            padding=(1, 2)
        )
    
    def format_attribute_matrix(
        self,
        companies: List[Company],
        attributes: List[str],
        target_company_name: str
    ) -> Table:
        """
        Format an attribute comparison matrix.
        
        Args:
            companies: List of companies to compare
            attributes: List of attributes to analyze
            target_company_name: Name of the target company
            
        Returns:
            Rich table with attribute matrix
        """
        
        table = Table(
            title="📋 Attribute Comparison Matrix",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # Find target company
        target_company = next((c for c in companies if c.name == target_company_name), None)
        if not target_company:
            target_company = companies[0] if companies else None
        
        # Add columns
        table.add_column("Company", style="bold green", min_width=20)
        for attr in attributes:
            table.add_column(self._format_attribute_name(attr), style="white", min_width=15)
        
        # Add target company first (if found)
        if target_company:
            self._add_company_row(table, target_company, attributes, is_target=True)
            remaining_companies = [c for c in companies if c.name != target_company.name]
        else:
            remaining_companies = companies
        
        # Add other companies
        for company in remaining_companies:
            self._add_company_row(table, company, attributes, is_target=False)
        
        return table
    
    def format_difference_highlight(
        self,
        target_company: Company,
        similar_company: Company,
        attributes: List[str]
    ) -> Panel:
        """
        Format highlighted differences between two companies.
        
        Args:
            target_company: Reference company
            similar_company: Company to compare
            attributes: Attributes to check for differences
            
        Returns:
            Rich panel highlighting key differences
        """
        
        content = Text()
        
        # Header
        content.append(f"Key Differences\n", style="bold red")
        content.append(f"{target_company.name} vs {similar_company.name}\n\n", style="bold white")
        
        differences_found = False
        
        for attr in attributes:
            target_value = self._get_company_attribute_value(target_company, attr)
            similar_value = self._get_company_attribute_value(similar_company, attr)
            
            if self._values_differ(target_value, similar_value, attr):
                differences_found = True
                attr_name = self._format_attribute_name(attr)
                
                content.append(f"• {attr_name}:\n", style="bold yellow")
                content.append(f"  Target:  {target_value or 'N/A'}\n", style="green")
                content.append(f"  Similar: {similar_value or 'N/A'}\n\n", style="cyan")
        
        if not differences_found:
            content.append("No significant differences found in compared attributes.", style="dim")
        
        return Panel(
            content,
            title="🔍 Difference Analysis",
            border_style="yellow",
            padding=(1, 2)
        )
    
    def format_similarity_heatmap(
        self,
        companies: List[Company],
        similarity_matrix: Dict[Tuple[str, str], float]
    ) -> Table:
        """
        Format a similarity heatmap between companies.
        
        Args:
            companies: List of companies
            similarity_matrix: Pairwise similarity scores
            
        Returns:
            Rich table showing similarity heatmap
        """
        
        table = Table(
            title="🌡️ Similarity Heatmap",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # Add columns
        table.add_column("Company", style="bold white", min_width=20)
        for company in companies:
            # Truncate long company names for headers
            header = company.name[:15] + "..." if len(company.name) > 15 else company.name
            table.add_column(header, width=10, justify="center")
        
        # Add rows
        for row_company in companies:
            row_data = [row_company.name]
            
            for col_company in companies:
                if row_company.name == col_company.name:
                    # Self-similarity
                    row_data.append("[bold green]1.00[/bold green]")
                else:
                    # Look up similarity score
                    key1 = (row_company.name, col_company.name)
                    key2 = (col_company.name, row_company.name)
                    
                    score = similarity_matrix.get(key1, similarity_matrix.get(key2, 0.0))
                    formatted_score = self._format_heatmap_cell(score)
                    row_data.append(formatted_score)
            
            table.add_row(*row_data)
        
        return table
    
    def format_comparison_summary(
        self,
        target_company: str,
        similar_companies: List[str],
        similarity_scores: Dict[str, float],
        key_insights: List[str]
    ) -> Panel:
        """
        Format a comparison summary with key insights.
        
        Args:
            target_company: Name of target company
            similar_companies: Names of similar companies
            similarity_scores: Similarity scores
            key_insights: List of key insights from comparison
            
        Returns:
            Rich panel with comparison summary
        """
        
        content = Text()
        
        # Header
        content.append(f"Comparison Summary\n", style="bold cyan")
        content.append(f"Target: {target_company}\n\n", style="bold green")
        
        # Top matches
        sorted_companies = sorted(
            similar_companies,
            key=lambda c: similarity_scores.get(c, 0.0),
            reverse=True
        )
        
        content.append("Top Matches:\n", style="bold yellow")
        for i, company in enumerate(sorted_companies[:3], 1):
            score = similarity_scores.get(company, 0.0)
            score_style = self._get_score_style(score)
            content.append(f"  {i}. {company} ", style="white")
            content.append(f"({score:.2f})\n", style=score_style)
        
        # Key insights
        if key_insights:
            content.append(f"\nKey Insights:\n", style="bold magenta")
            for insight in key_insights:
                content.append(f"  • {insight}\n", style="white")
        
        return Panel(
            content,
            title="📋 Summary",
            border_style="cyan",
            padding=(1, 2)
        )
    
    def _add_company_row(
        self,
        table: Table,
        company: Company,
        attributes: List[str],
        is_target: bool = False
    ) -> None:
        """Add a company row to the attribute matrix table."""
        row_data = []
        
        # Company name
        if is_target:
            row_data.append(f"🎯 {company.name}")
        else:
            row_data.append(company.name)
        
        # Attribute values
        for attr in attributes:
            value = self._get_company_attribute_value(company, attr)
            formatted_value = self._format_attribute_value(value, attr, is_target=is_target)
            row_data.append(formatted_value)
        
        # Add row with styling
        style = "on dark_green" if is_target else None
        table.add_row(*row_data, style=style)
    
    def _get_company_attribute_value(self, company: Company, attribute: str) -> Any:
        """Get attribute value from company object."""
        if attribute == 'name':
            return company.name
        elif attribute == 'website':
            return company.website
        elif attribute == 'description':
            return company.description
        else:
            return getattr(company, attribute, None)
    
    def _format_attribute_name(self, attribute: str) -> str:
        """Format attribute name for display."""
        return attribute.replace('_', ' ').title()
    
    def _format_attribute_value(
        self,
        value: Any,
        attribute: str,
        is_target: bool = False
    ) -> str:
        """Format attribute value for display."""
        if value is None:
            return "[dim]N/A[/dim]"
        
        # Truncate long values
        str_value = str(value)
        if len(str_value) > 30:
            str_value = str_value[:27] + "..."
        
        if is_target:
            return f"[bold]{str_value}[/bold]"
        else:
            return str_value
    
    def _values_differ(self, value1: Any, value2: Any, attribute: str) -> bool:
        """Check if two attribute values differ significantly."""
        if value1 is None or value2 is None:
            return value1 != value2
        
        # For strings, check case-insensitive equality
        if isinstance(value1, str) and isinstance(value2, str):
            return value1.lower() != value2.lower()
        
        return value1 != value2
    
    def _format_heatmap_cell(self, score: float) -> str:
        """Format a cell in the similarity heatmap."""
        if score >= 0.8:
            return f"[bold green]{score:.2f}[/bold green]"
        elif score >= 0.6:
            return f"[bold yellow]{score:.2f}[/bold yellow]"
        elif score >= 0.4:
            return f"[bold orange]{score:.2f}[/bold orange]"
        else:
            return f"[bold red]{score:.2f}[/bold red]"
    
    def _create_score_bar(self, score: float, width: int = 10) -> str:
        """Create a visual score bar."""
        filled = int(score * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty}"
    
    def _create_mini_score_bar(self, score: float, width: int = 6) -> str:
        """Create a compact score bar."""
        filled = int(score * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty}"
    
    def _get_score_style(self, score: float) -> str:
        """Get Rich style based on score."""
        if score >= 0.8:
            return "bold green"
        elif score >= 0.6:
            return "bold yellow"
        elif score >= 0.4:
            return "bold orange"
        else:
            return "bold red"
    
    def _get_score_indicator(self, score: float) -> str:
        """Get emoji indicator based on score."""
        if score >= 0.9:
            return "🟢"
        elif score >= 0.7:
            return "🟡"
        elif score >= 0.5:
            return "🟠"
        else:
            return "🔴"
    
    def _get_border_style_for_score(self, score: float) -> str:
        """Get border style based on similarity score."""
        if score >= 0.8:
            return "green"
        elif score >= 0.6:
            return "yellow"
        elif score >= 0.4:
            return "orange"
        else:
            return "red"
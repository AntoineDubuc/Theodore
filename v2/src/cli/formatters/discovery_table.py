"""
Rich Discovery Table Formatter for Theodore CLI.

Provides sophisticated table formatting for discovery results with
multi-column similarity scoring, interactive selection indicators,
and expandable company details.
"""

from typing import List, Dict, Any, Optional, Set
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.align import Align

from src.core.domain.entities.company import Company
from src.core.use_cases.discover_similar_companies import DiscoveryResult


class RichDiscoveryTableFormatter:
    """
    Advanced table formatter for discovery results with Rich styling
    and interactive features.
    """
    
    def __init__(self):
        self.console = Console()
        self.selected_companies: Set[str] = set()
    
    def format_discovery_results(
        self,
        discovery_result: DiscoveryResult,
        show_similarity_explanations: bool = False,
        show_selection_indicators: bool = False,
        expanded_companies: Optional[Set[str]] = None,
        max_description_length: int = 100
    ) -> Table:
        """
        Format discovery results in a comprehensive Rich table.
        
        Args:
            discovery_result: Discovery result with companies and metadata
            show_similarity_explanations: Include similarity explanation previews
            show_selection_indicators: Show selection checkboxes/indicators
            expanded_companies: Set of company names to show expanded details
            max_description_length: Maximum length for description column
            
        Returns:
            Rich table with formatted discovery results
        """
        
        # Determine table title
        title = f"🔍 Similar Companies to {discovery_result.target_company}"
        if discovery_result.source:
            title += f" (via {discovery_result.source.value})"
        
        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            caption=f"Found {len(discovery_result.companies)} companies in {discovery_result.search_time_ms:.0f}ms"
        )
        
        # Add columns based on options
        if show_selection_indicators:
            table.add_column("Select", width=6, justify="center")
        
        table.add_column("Rank", style="bold white", width=4, justify="center")
        table.add_column("Company", style="bold green", min_width=20)
        table.add_column("Similarity", style="bold yellow", width=15, justify="center")
        table.add_column("Website", style="dim blue", min_width=15)
        
        if show_similarity_explanations:
            table.add_column("Key Factors", style="dim cyan", min_width=20)
        
        if max_description_length > 0:
            table.add_column("Description", style="white", min_width=20, max_width=max_description_length)
        
        # Sort companies by similarity score
        sorted_companies = sorted(
            discovery_result.companies,
            key=lambda c: discovery_result.similarity_scores.get(c.name, 0.0),
            reverse=True
        )
        
        # Add rows
        for rank, company in enumerate(sorted_companies, 1):
            row_data = []
            
            # Selection indicator
            if show_selection_indicators:
                if company.name in self.selected_companies:
                    row_data.append("[green]✓[/green]")
                else:
                    row_data.append("[ ]")
            
            # Rank
            row_data.append(str(rank))
            
            # Company name with expansion indicator
            company_name = company.name
            if expanded_companies and company.name in expanded_companies:
                company_name = f"📖 {company_name}"
            row_data.append(company_name)
            
            # Similarity score with visual indicator
            score = discovery_result.similarity_scores.get(company.name, 0.0)
            similarity_display = self._format_similarity_cell(score)
            row_data.append(similarity_display)
            
            # Website
            website = company.website or "N/A"
            if len(website) > 30:
                website = website[:27] + "..."
            row_data.append(website)
            
            # Similarity explanations
            if show_similarity_explanations:
                explanations = getattr(discovery_result, 'explanations', {})
                if company.name in explanations:
                    key_factors = self._extract_key_factors(explanations[company.name])
                else:
                    key_factors = "N/A"
                row_data.append(key_factors)
            
            # Description
            if max_description_length > 0:
                description = company.description or "No description available"
                if len(description) > max_description_length:
                    description = description[:max_description_length-3] + "..."
                row_data.append(description)
            
            # Add row with appropriate styling
            style = self._get_row_style(rank, score)
            table.add_row(*row_data, style=style)
        
        return table
    
    def format_expanded_company_details(
        self,
        company: Company,
        similarity_score: float,
        explanation: Optional[Dict[str, Any]] = None
    ) -> Panel:
        """
        Format expanded details for a specific company.
        
        Args:
            company: Company object with details
            similarity_score: Similarity score for this company
            explanation: Detailed similarity explanation
            
        Returns:
            Rich panel with expanded company information
        """
        
        content = Text()
        
        # Company header
        content.append(f"{company.name}\n", style="bold green")
        if company.website:
            content.append(f"🌐 {company.website}\n", style="dim blue")
        content.append(f"🎯 Similarity: {similarity_score:.2f}\n\n", style="bold yellow")
        
        # Company details
        if company.description:
            content.append("Description:\n", style="bold white")
            content.append(f"{company.description}\n\n", style="white")
        
        if hasattr(company, 'industry') and company.industry:
            content.append(f"🏭 Industry: {company.industry}\n", style="cyan")
        
        if hasattr(company, 'size') and company.size:
            content.append(f"👥 Size: {company.size}\n", style="cyan")
        
        if hasattr(company, 'location') and company.location:
            content.append(f"📍 Location: {company.location}\n", style="cyan")
        
        if hasattr(company, 'founded_year') and company.founded_year:
            content.append(f"📅 Founded: {company.founded_year}\n", style="cyan")
        
        # Similarity explanation
        if explanation:
            content.append("\nSimilarity Factors:\n", style="bold yellow")
            factors = explanation.get('factors', {})
            for factor, score in sorted(factors.items(), key=lambda x: x[1], reverse=True):
                factor_name = factor.replace('_', ' ').title()
                score_bar = self._create_mini_score_bar(score)
                content.append(f"  • {factor_name}: {score:.2f} {score_bar}\n", style="white")
            
            if explanation.get('explanation'):
                content.append(f"\n{explanation['explanation']}", style="dim white")
        
        return Panel(
            content,
            title=f"🏢 {company.name} - Detailed View",
            border_style=self._get_border_style_for_score(similarity_score),
            padding=(1, 2)
        )
    
    def format_discovery_summary(
        self,
        discovery_result: DiscoveryResult,
        selected_companies: Optional[Set[str]] = None
    ) -> Panel:
        """
        Format a summary panel for discovery results.
        
        Args:
            discovery_result: Discovery result to summarize
            selected_companies: Set of selected company names
            
        Returns:
            Rich panel with discovery summary
        """
        
        content = Text()
        
        # Header
        content.append("Discovery Summary\n", style="bold cyan")
        content.append("=" * 40 + "\n\n", style="dim")
        
        # Basic stats
        content.append(f"🎯 Target: ", style="bold")
        content.append(f"{discovery_result.target_company}\n", style="green")
        
        content.append(f"📊 Found: ", style="bold")
        content.append(f"{len(discovery_result.companies)} similar companies\n", style="white")
        
        content.append(f"⚡ Source: ", style="bold")
        content.append(f"{discovery_result.source.value}\n", style="cyan")
        
        content.append(f"⏱️ Time: ", style="bold")
        content.append(f"{discovery_result.search_time_ms:.0f}ms\n\n", style="white")
        
        # Score statistics
        if discovery_result.similarity_scores:
            scores = list(discovery_result.similarity_scores.values())
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            content.append("Score Statistics:\n", style="bold yellow")
            content.append(f"  Average: {avg_score:.2f}\n", style="white")
            content.append(f"  Highest: {max_score:.2f}\n", style="white")
            content.append(f"  Lowest: {min_score:.2f}\n\n", style="white")
        
        # Selection info
        if selected_companies:
            content.append(f"✅ Selected: ", style="bold")
            content.append(f"{len(selected_companies)} companies\n", style="green")
        
        # Top matches preview
        if discovery_result.companies:
            content.append("Top Matches:\n", style="bold cyan")
            top_companies = sorted(
                discovery_result.companies[:3],
                key=lambda c: discovery_result.similarity_scores.get(c.name, 0.0),
                reverse=True
            )
            
            for i, company in enumerate(top_companies, 1):
                score = discovery_result.similarity_scores.get(company.name, 0.0)
                content.append(f"  {i}. {company.name} ({score:.2f})\n", style="white")
        
        return Panel(
            content,
            title="📋 Discovery Overview",
            border_style="blue",
            padding=(1, 2)
        )
    
    def format_interactive_controls(
        self,
        total_companies: int,
        selected_count: int = 0,
        current_page: int = 1,
        total_pages: int = 1
    ) -> Panel:
        """
        Format interactive control panel for discovery interface.
        
        Args:
            total_companies: Total number of companies found
            selected_count: Number of companies currently selected
            current_page: Current page number
            total_pages: Total number of pages
            
        Returns:
            Rich panel with interactive controls
        """
        
        content = Text()
        
        # Controls header
        content.append("Interactive Controls\n", style="bold cyan")
        content.append("=" * 30 + "\n\n", style="dim")
        
        # Navigation
        if total_pages > 1:
            content.append(f"📄 Page {current_page} of {total_pages}\n", style="white")
            content.append("  [N]ext page  [P]revious page\n\n", style="dim")
        
        # Selection
        content.append(f"✅ Selected: {selected_count}/{total_companies} companies\n", style="green")
        content.append("  [Space] Toggle selection\n", style="dim")
        content.append("  [A]ll  [C]lear selection\n\n", style="dim")
        
        # Actions
        content.append("Actions:\n", style="bold yellow")
        content.append("  [R]esearch selected\n", style="dim")
        content.append("  [E]xpand details\n", style="dim")
        content.append("  [S]ave results\n", style="dim")
        content.append("  [F]ilter results\n", style="dim")
        content.append("  [Q]uit\n\n", style="dim")
        
        # Help
        content.append("Press [H] for help", style="dim cyan")
        
        return Panel(
            content,
            title="🎮 Controls",
            border_style="yellow",
            padding=(1, 2)
        )
    
    def format_filter_status(
        self,
        active_filters: Dict[str, Any]
    ) -> Panel:
        """
        Format active filter status panel.
        
        Args:
            active_filters: Dictionary of active filter names and values
            
        Returns:
            Rich panel showing active filters
        """
        
        content = Text()
        
        if not active_filters:
            content.append("No active filters", style="dim")
        else:
            content.append("Active Filters:\n", style="bold cyan")
            
            for filter_name, filter_value in active_filters.items():
                content.append(f"  • {filter_name.replace('_', ' ').title()}: ", style="white")
                content.append(f"{filter_value}\n", style="yellow")
        
        return Panel(
            content,
            title="🔧 Filters",
            border_style="cyan",
            padding=(1, 1)
        )
    
    def toggle_company_selection(self, company_name: str) -> bool:
        """
        Toggle selection status of a company.
        
        Args:
            company_name: Name of company to toggle
            
        Returns:
            True if now selected, False if deselected
        """
        if company_name in self.selected_companies:
            self.selected_companies.remove(company_name)
            return False
        else:
            self.selected_companies.add(company_name)
            return True
    
    def select_all_companies(self, company_names: List[str]) -> None:
        """Select all companies."""
        self.selected_companies.update(company_names)
    
    def clear_selection(self) -> None:
        """Clear all selections."""
        self.selected_companies.clear()
    
    def get_selected_companies(self) -> Set[str]:
        """Get set of selected company names."""
        return self.selected_companies.copy()
    
    def _format_similarity_cell(self, score: float) -> str:
        """Format similarity score cell with visual indicator."""
        # Create score bar
        bar_length = 8
        filled = int(score * bar_length)
        empty = bar_length - filled
        
        if score >= 0.8:
            bar = f"[green]{'█' * filled}{'░' * empty}[/green]"
            score_style = "bold green"
        elif score >= 0.6:
            bar = f"[yellow]{'█' * filled}{'░' * empty}[/yellow]"
            score_style = "bold yellow"
        elif score >= 0.4:
            bar = f"[orange]{'█' * filled}{'░' * empty}[/orange]"
            score_style = "bold orange"
        else:
            bar = f"[red]{'█' * filled}{'░' * empty}[/red]"
            score_style = "bold red"
        
        return f"[{score_style}]{score:.2f}[/{score_style}]\n{bar}"
    
    def _create_mini_score_bar(self, score: float, width: int = 6) -> str:
        """Create a compact score bar."""
        filled = int(score * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty}"
    
    def _get_row_style(self, rank: int, score: float) -> Optional[str]:
        """Get row style based on rank and score."""
        if rank == 1:
            return "on dark_green"
        elif rank <= 3 and score >= 0.8:
            return "on dark_blue"
        elif score >= 0.9:
            return "on dark_magenta"
        return None
    
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
    
    def _extract_key_factors(self, explanation: Dict[str, Any]) -> str:
        """Extract key factors from explanation for table display."""
        factors = explanation.get('factors', {})
        if not factors:
            return "N/A"
        
        # Get top 2 factors
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:2]
        factor_strings = []
        
        for factor, score in top_factors:
            factor_name = factor.replace('_', ' ').title()
            factor_strings.append(f"{factor_name} ({score:.2f})")
        
        return ", ".join(factor_strings)
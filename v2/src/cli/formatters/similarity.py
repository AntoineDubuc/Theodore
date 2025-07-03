"""
Similarity Result Formatter for Theodore CLI.

Provides specialized formatting for similarity scores, explanations,
and ranked discovery results with visual scoring indicators.
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, BarColumn
from rich.align import Align

from src.core.domain.entities.company import Company
from src.core.use_cases.discover_similar_companies import DiscoveryResult, SimilarityScore


class SimilarityResultFormatter:
    """
    Formatter for similarity-based discovery results with visual scoring
    and detailed explanations.
    """
    
    def __init__(self):
        self.console = Console()
    
    def format_similarity_scores(
        self,
        companies: List[Company],
        similarity_scores: Dict[str, float],
        show_explanations: bool = False,
        explanations: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Table:
        """
        Format similarity scores in a rich table with visual indicators.
        
        Args:
            companies: List of similar companies
            similarity_scores: Company name to similarity score mapping
            show_explanations: Whether to include explanation preview
            explanations: Detailed similarity explanations
            
        Returns:
            Rich table with formatted similarity results
        """
        
        table = Table(
            title="🎯 Company Similarity Scores",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # Define columns
        table.add_column("Rank", style="bold white", width=4, justify="center")
        table.add_column("Company", style="bold green", min_width=20)
        table.add_column("Score", style="bold yellow", width=12, justify="center")
        table.add_column("Visual", width=15, justify="center")
        table.add_column("Website", style="dim blue", min_width=15)
        
        if show_explanations:
            table.add_column("Key Factors", style="dim cyan", min_width=20)
        
        # Sort companies by similarity score
        sorted_companies = sorted(
            companies,
            key=lambda c: similarity_scores.get(c.name, 0.0),
            reverse=True
        )
        
        for rank, company in enumerate(sorted_companies, 1):
            score = similarity_scores.get(company.name, 0.0)
            
            # Create visual score bar
            visual_score = self._create_score_bar(score)
            
            # Format score with color coding
            formatted_score = self._format_score_with_color(score)
            
            # Prepare row data
            row_data = [
                str(rank),
                company.name,
                formatted_score,
                visual_score,
                company.website or "N/A"
            ]
            
            # Add explanation preview if available
            if show_explanations and explanations and company.name in explanations:
                key_factors = self._extract_key_factors(explanations[company.name])
                row_data.append(key_factors)
            
            table.add_row(*row_data)
        
        return table
    
    def format_similarity_explanation(
        self,
        company_name: str,
        explanation: Dict[str, Any],
        target_company: str
    ) -> Panel:
        """
        Format detailed similarity explanation for a single company.
        
        Args:
            company_name: Name of the similar company
            explanation: Detailed similarity explanation data
            target_company: Name of the target company
            
        Returns:
            Rich panel with formatted explanation
        """
        
        content = Text()
        
        # Overall score
        overall_score = explanation.get('overall_score', 0.0)
        content.append("Overall Similarity: ", style="bold")
        content.append(f"{overall_score:.2f}\n\n", style=self._get_score_style(overall_score))
        
        # Factor breakdown
        factors = explanation.get('factors', {})
        if factors:
            content.append("Factor Breakdown:\n", style="bold cyan")
            
            for factor, score in sorted(factors.items(), key=lambda x: x[1], reverse=True):
                factor_name = factor.replace('_', ' ').title()
                score_bar = self._create_mini_score_bar(score)
                
                content.append(f"  • {factor_name}: ", style="white")
                content.append(f"{score:.2f} ", style=self._get_score_style(score))
                content.append(f"{score_bar}\n", style="dim")
        
        # Natural language explanation
        if explanation.get('explanation'):
            content.append("\nExplanation:\n", style="bold yellow")
            content.append(explanation['explanation'], style="dim white")
        
        # Confidence indicator
        confidence = explanation.get('confidence', 0.0)
        if confidence > 0:
            content.append(f"\n\nConfidence: ", style="bold")
            content.append(f"{confidence:.2f}", style=self._get_score_style(confidence))
        
        return Panel(
            content,
            title=f"🏢 {company_name} vs {target_company}",
            border_style=self._get_border_style(overall_score),
            padding=(1, 2)
        )
    
    def format_similarity_summary(
        self,
        discovery_result: DiscoveryResult,
        top_n: int = 5
    ) -> Panel:
        """
        Format a summary panel of top similarity matches.
        
        Args:
            discovery_result: Discovery result with companies and scores
            top_n: Number of top matches to include
            
        Returns:
            Rich panel with similarity summary
        """
        
        # Get top companies
        top_companies = sorted(
            discovery_result.companies[:top_n],
            key=lambda c: discovery_result.similarity_scores.get(c.name, 0.0),
            reverse=True
        )
        
        content = Text()
        content.append(f"Target Company: ", style="bold blue")
        content.append(f"{discovery_result.target_company}\n\n", style="bold white")
        
        content.append(f"Top {len(top_companies)} Similar Companies:\n", style="bold cyan")
        
        for i, company in enumerate(top_companies, 1):
            score = discovery_result.similarity_scores.get(company.name, 0.0)
            score_bar = self._create_mini_score_bar(score)
            
            content.append(f"{i}. ", style="bold white")
            content.append(f"{company.name} ", style="green")
            content.append(f"({score:.2f}) ", style=self._get_score_style(score))
            content.append(f"{score_bar}\n", style="dim")
        
        # Summary statistics
        if discovery_result.similarity_scores:
            avg_score = sum(discovery_result.similarity_scores.values()) / len(discovery_result.similarity_scores)
            max_score = max(discovery_result.similarity_scores.values())
            
            content.append(f"\nStatistics:\n", style="bold yellow")
            content.append(f"  Average Score: {avg_score:.2f}\n", style="white")
            content.append(f"  Highest Score: {max_score:.2f}\n", style="white")
            content.append(f"  Total Found: {len(discovery_result.companies)}", style="white")
        
        return Panel(
            content,
            title="📊 Similarity Summary",
            border_style="blue",
            padding=(1, 2)
        )
    
    def format_score_distribution(
        self,
        similarity_scores: Dict[str, float],
        bins: int = 5
    ) -> Table:
        """
        Format similarity score distribution in bins.
        
        Args:
            similarity_scores: Company name to score mapping
            bins: Number of score bins to create
            
        Returns:
            Rich table showing score distribution
        """
        
        if not similarity_scores:
            return Table(title="No scores to display")
        
        scores = list(similarity_scores.values())
        min_score = min(scores)
        max_score = max(scores)
        bin_size = (max_score - min_score) / bins
        
        # Create bins
        bin_counts = [0] * bins
        bin_ranges = []
        
        for i in range(bins):
            bin_start = min_score + i * bin_size
            bin_end = min_score + (i + 1) * bin_size
            bin_ranges.append((bin_start, bin_end))
        
        # Count scores in each bin
        for score in scores:
            bin_index = min(int((score - min_score) / bin_size), bins - 1)
            bin_counts[bin_index] += 1
        
        # Create table
        table = Table(
            title="📈 Score Distribution",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("Score Range", style="white", width=15)
        table.add_column("Count", style="bold yellow", width=8, justify="center")
        table.add_column("Percentage", style="green", width=12, justify="center")
        table.add_column("Visual", width=20)
        
        total_scores = len(scores)
        
        for i, (count, (start, end)) in enumerate(zip(bin_counts, bin_ranges)):
            percentage = (count / total_scores) * 100
            visual_bar = "█" * min(int(percentage / 5), 20)  # Scale to max 20 chars
            
            table.add_row(
                f"{start:.2f} - {end:.2f}",
                str(count),
                f"{percentage:.1f}%",
                visual_bar
            )
        
        return table
    
    def _create_score_bar(self, score: float, width: int = 10) -> str:
        """Create a visual score bar."""
        filled = int(score * width)
        empty = width - filled
        
        if score >= 0.8:
            bar_char = "█"
            style = "green"
        elif score >= 0.6:
            bar_char = "▓"
            style = "yellow"
        elif score >= 0.4:
            bar_char = "▒"
            style = "orange"
        else:
            bar_char = "░"
            style = "red"
        
        return f"[{style}]{bar_char * filled}[/]{' ' * empty}"
    
    def _create_mini_score_bar(self, score: float, width: int = 6) -> str:
        """Create a compact score bar."""
        filled = int(score * width)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty}"
    
    def _format_score_with_color(self, score: float) -> str:
        """Format score with appropriate color."""
        if score >= 0.8:
            return f"[bold green]{score:.2f}[/bold green]"
        elif score >= 0.6:
            return f"[bold yellow]{score:.2f}[/bold yellow]"
        elif score >= 0.4:
            return f"[bold orange]{score:.2f}[/bold orange]"
        else:
            return f"[bold red]{score:.2f}[/bold red]"
    
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
    
    def _get_border_style(self, score: float) -> str:
        """Get border style based on score."""
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
    
    def format_comparison_table(
        self,
        companies: List[Company],
        similarity_scores: Dict[str, float],
        target_company: str,
        attributes: List[str] = None
    ) -> Table:
        """
        Format a comparison table between target and similar companies.
        
        Args:
            companies: List of companies to compare
            similarity_scores: Similarity scores for each company
            target_company: Name of target company
            attributes: Specific attributes to compare
            
        Returns:
            Rich table with company comparison
        """
        
        if attributes is None:
            attributes = ['name', 'website', 'similarity_score']
        
        table = Table(
            title=f"🔍 Company Comparison vs {target_company}",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # Add columns dynamically based on attributes
        for attr in attributes:
            if attr == 'similarity_score':
                table.add_column("Similarity", style="bold yellow", width=12, justify="center")
            elif attr == 'name':
                table.add_column("Company", style="bold green", min_width=20)
            elif attr == 'website':
                table.add_column("Website", style="dim blue", min_width=15)
            else:
                table.add_column(attr.replace('_', ' ').title(), style="white", min_width=10)
        
        # Sort companies by similarity score
        sorted_companies = sorted(
            companies,
            key=lambda c: similarity_scores.get(c.name, 0.0),
            reverse=True
        )
        
        for company in sorted_companies:
            row_data = []
            
            for attr in attributes:
                if attr == 'similarity_score':
                    score = similarity_scores.get(company.name, 0.0)
                    row_data.append(self._format_score_with_color(score))
                elif attr == 'name':
                    row_data.append(company.name)
                elif attr == 'website':
                    row_data.append(company.website or "N/A")
                else:
                    # Get attribute value from company object
                    value = getattr(company, attr, "N/A")
                    row_data.append(str(value) if value is not None else "N/A")
            
            table.add_row(*row_data)
        
        return table
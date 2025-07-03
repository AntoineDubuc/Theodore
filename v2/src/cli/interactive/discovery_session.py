"""
Interactive Discovery Session for Theodore CLI.

Provides guided discovery workflows with progressive filter refinement.
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm

from src.core.domain.entities.company import Company
from src.core.use_cases.discover_similar_companies import DiscoveryResult


class InteractiveDiscoverySession:
    """Handles interactive discovery workflows."""
    
    def __init__(
        self,
        discovery_result: DiscoveryResult,
        discover_command,
        research_discovered: bool = False
    ):
        self.discovery_result = discovery_result
        self.discover_command = discover_command
        self.research_discovered = research_discovered
        self.console = Console()
        self.selected_companies: List[str] = []
    
    async def start_interactive_session(self) -> None:
        """Start the interactive discovery session."""
        
        self.console.print("\n🎮 [bold cyan]Interactive Discovery Mode[/bold cyan]")
        self.console.print("Use the following options to explore your results:\n")
        
        while True:
            # Display current results summary
            self._display_session_status()
            
            # Show menu options
            choice = Prompt.ask(
                "\nChoose an action",
                choices=["view", "select", "research", "filter", "export", "quit"],
                default="view"
            )
            
            if choice == "view":
                await self._view_companies()
            elif choice == "select":
                await self._select_companies()
            elif choice == "research":
                await self._research_selected()
            elif choice == "filter":
                await self._refine_filters()
            elif choice == "export":
                await self._export_results()
            elif choice == "quit":
                break
    
    def _display_session_status(self) -> None:
        """Display current session status."""
        total = len(self.discovery_result.companies)
        selected = len(self.selected_companies)
        
        self.console.print(f"📊 Found: {total} companies | Selected: {selected}")
        if selected > 0:
            self.console.print(f"Selected: {', '.join(self.selected_companies[:3])}" + 
                             (f" and {selected-3} more" if selected > 3 else ""))
    
    async def _view_companies(self) -> None:
        """View companies in detail."""
        self.console.print("\n📋 [bold]Company List:[/bold]")
        
        for i, company in enumerate(self.discovery_result.companies[:10], 1):
            score = self.discovery_result.similarity_scores.get(company.name, 0.0)
            selected = "✓" if company.name in self.selected_companies else " "
            
            self.console.print(f"{i:2d}. [{selected}] {company.name} ({score:.2f})")
            if company.website:
                self.console.print(f"     🌐 {company.website}")
    
    async def _select_companies(self) -> None:
        """Interactive company selection."""
        self.console.print("\n✅ [bold]Select Companies:[/bold]")
        
        for i, company in enumerate(self.discovery_result.companies[:10], 1):
            if Confirm.ask(f"Select {company.name}?", default=False):
                if company.name not in self.selected_companies:
                    self.selected_companies.append(company.name)
    
    async def _research_selected(self) -> None:
        """Research selected companies."""
        if not self.selected_companies:
            self.console.print("❌ No companies selected for research")
            return
        
        self.console.print(f"\n🔬 Researching {len(self.selected_companies)} companies...")
        
        # Get selected company objects
        selected_company_objects = [
            c for c in self.discovery_result.companies 
            if c.name in self.selected_companies
        ]
        
        await self.discover_command._auto_research_companies(selected_company_objects)
    
    async def _refine_filters(self) -> None:
        """Refine discovery filters."""
        self.console.print("\n🔧 [bold]Filter Refinement:[/bold]")
        self.console.print("(Filter refinement not implemented in simplified version)")
    
    async def _export_results(self) -> None:
        """Export discovery results."""
        filename = Prompt.ask("Export filename", default="discovery_results.json")
        
        if self.selected_companies:
            # Export only selected companies
            selected_company_objects = [
                c for c in self.discovery_result.companies 
                if c.name in self.selected_companies
            ]
            # Create a filtered result
            filtered_result = DiscoveryResult(
                companies=selected_company_objects,
                target_company=self.discovery_result.target_company,
                similarity_scores={
                    name: score for name, score in self.discovery_result.similarity_scores.items()
                    if name in self.selected_companies
                },
                source=self.discovery_result.source,
                search_time_ms=self.discovery_result.search_time_ms
            )
            await self.discover_command._save_results(filtered_result, filename, self.discover_command.OutputFormat.JSON)
        else:
            await self.discover_command._save_results(self.discovery_result, filename, self.discover_command.OutputFormat.JSON)
"""
Filter Suggestion Engine for Theodore CLI.

Provides intelligent filter recommendations and context-aware suggestions.
"""

from typing import List, Dict, Any
from src.core.use_cases.discover_similar_companies import DiscoveryFilters


class FilterSuggestionEngine:
    """Provides intelligent filter suggestions."""
    
    def __init__(self):
        pass
    
    async def get_contextual_suggestions(
        self,
        current_filters: DiscoveryFilters,
        result_count: int
    ) -> List[Dict[str, Any]]:
        """Get contextual filter suggestions based on current state."""
        suggestions = []
        
        if result_count == 0:
            suggestions.append({
                'type': 'loosen_filters',
                'description': 'Try lowering similarity threshold or removing some filters',
                'priority': 'high'
            })
        elif result_count > 50:
            suggestions.append({
                'type': 'tighten_filters', 
                'description': 'Add more specific filters to narrow results',
                'priority': 'medium'
            })
        
        return suggestions
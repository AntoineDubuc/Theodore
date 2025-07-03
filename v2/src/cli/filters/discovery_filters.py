"""
Discovery Filter Processor for Theodore CLI.

Provides advanced filtering logic, multi-dimensional filter application,
filter combination optimization, and smart filter suggestions.
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum
import re
from dataclasses import dataclass

from src.core.domain.entities.company import BusinessModel, CompanySize, GrowthStage
from src.core.use_cases.discover_similar_companies import DiscoveryFilters
from .filter_validators import FilterValidator
from .filter_suggestions import FilterSuggestionEngine


@dataclass
class FilterCombination:
    """Represents a combination of filters with optimization metadata."""
    filters: DiscoveryFilters
    estimated_results: int
    confidence: float
    optimization_notes: List[str]


class FilterConflictType(Enum):
    """Types of filter conflicts that can occur."""
    INCOMPATIBLE = "incompatible"
    REDUNDANT = "redundant" 
    OVERLY_RESTRICTIVE = "overly_restrictive"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"


@dataclass
class FilterConflict:
    """Represents a conflict between filters."""
    conflict_type: FilterConflictType
    filters_involved: List[str]
    description: str
    suggested_resolution: str


class DiscoveryFilterProcessor:
    """
    Advanced filter processor that handles multi-dimensional filtering,
    optimization, and intelligent suggestions for company discovery.
    """
    
    def __init__(self):
        self.validator = FilterValidator()
        self.suggestion_engine = FilterSuggestionEngine()
        
        # Industry hierarchies for fuzzy matching
        self.industry_hierarchies = {
            'technology': [
                'software', 'hardware', 'ai', 'machine learning', 'saas',
                'cloud computing', 'cybersecurity', 'fintech', 'edtech'
            ],
            'finance': [
                'banking', 'investment', 'insurance', 'payments', 'fintech',
                'cryptocurrency', 'lending', 'wealth management'
            ],
            'healthcare': [
                'biotechnology', 'pharmaceuticals', 'medical devices',
                'digital health', 'telemedicine', 'healthtech'
            ],
            'retail': [
                'e-commerce', 'fashion', 'consumer goods', 'marketplace',
                'grocery', 'luxury goods', 'automotive retail'
            ],
            'manufacturing': [
                'automotive', 'aerospace', 'industrial', 'consumer products',
                'chemicals', 'food processing', 'textiles'
            ]
        }
        
        # Business model compatibility matrix
        self.model_compatibility = {
            BusinessModel.B2B: [BusinessModel.ENTERPRISE, BusinessModel.SAAS],
            BusinessModel.B2C: [BusinessModel.ECOMMERCE, BusinessModel.MARKETPLACE],
            BusinessModel.SAAS: [BusinessModel.B2B, BusinessModel.ENTERPRISE],
            BusinessModel.ENTERPRISE: [BusinessModel.B2B, BusinessModel.SAAS],
            BusinessModel.ECOMMERCE: [BusinessModel.B2C, BusinessModel.MARKETPLACE],
            BusinessModel.MARKETPLACE: [BusinessModel.B2C, BusinessModel.ECOMMERCE]
        }
    
    async def process_filters(
        self,
        business_model: Optional[str] = None,
        company_size: Optional[str] = None,
        industry: Optional[str] = None,
        growth_stage: Optional[str] = None,
        location: Optional[str] = None,
        similarity_threshold: float = 0.6,
        founded_after: Optional[int] = None,
        founded_before: Optional[int] = None,
        exclude_competitors: bool = False,
        include_subsidiaries: bool = True,
        **additional_filters
    ) -> DiscoveryFilters:
        """
        Process and validate discovery filters with intelligent optimization.
        
        Args:
            business_model: Business model filter
            company_size: Company size filter
            industry: Industry sector filter
            growth_stage: Growth stage filter
            location: Geographic location filter
            similarity_threshold: Minimum similarity score
            founded_after: Founded after year
            founded_before: Founded before year
            exclude_competitors: Exclude direct competitors
            include_subsidiaries: Include subsidiary companies
            **additional_filters: Additional filter parameters
            
        Returns:
            Validated and optimized DiscoveryFilters object
        """
        
        # Parse and validate enum values
        parsed_business_model = self._parse_business_model(business_model)
        parsed_company_size = self._parse_company_size(company_size)
        parsed_growth_stage = self._parse_growth_stage(growth_stage)
        
        # Normalize and validate industry
        normalized_industry = await self._normalize_industry(industry)
        
        # Normalize location
        normalized_location = self._normalize_location(location)
        
        # Validate similarity threshold
        validated_threshold = self._validate_similarity_threshold(similarity_threshold)
        
        # Create initial filters
        filters = DiscoveryFilters(
            business_model=parsed_business_model,
            company_size=parsed_company_size,
            industry=normalized_industry,
            growth_stage=parsed_growth_stage,
            location=normalized_location,
            similarity_threshold=validated_threshold,
            founded_after=founded_after,
            founded_before=founded_before,
            exclude_competitors=exclude_competitors,
            include_subsidiaries=include_subsidiaries
        )
        
        # Apply additional filters
        for key, value in additional_filters.items():
            if hasattr(filters, key) and value is not None:
                setattr(filters, key, value)
        
        # Validate filter combinations
        conflicts = await self._detect_filter_conflicts(filters)
        if conflicts:
            optimized_filters = await self._resolve_filter_conflicts(filters, conflicts)
            return optimized_filters
        
        # Optimize filter combination
        optimized_filters = await self._optimize_filter_combination(filters)
        
        return optimized_filters
    
    async def suggest_filter_refinements(
        self,
        current_filters: DiscoveryFilters,
        result_count: int,
        target_result_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Suggest filter refinements based on current results.
        
        Args:
            current_filters: Current filter configuration
            result_count: Current number of results
            target_result_count: Desired number of results
            
        Returns:
            List of suggested filter refinements
        """
        
        suggestions = []
        
        if result_count == 0:
            # Too restrictive - suggest loosening filters
            suggestions.extend(await self._suggest_loosening_filters(current_filters))
        elif result_count > target_result_count * 3:
            # Too many results - suggest tightening filters
            suggestions.extend(await self._suggest_tightening_filters(current_filters))
        
        # Context-aware suggestions
        context_suggestions = await self.suggestion_engine.get_contextual_suggestions(
            current_filters, result_count
        )
        suggestions.extend(context_suggestions)
        
        return suggestions
    
    async def get_filter_combinations(
        self,
        base_filters: DiscoveryFilters,
        variations: int = 5
    ) -> List[FilterCombination]:
        """
        Generate intelligent filter combinations for exploration.
        
        Args:
            base_filters: Base filter configuration
            variations: Number of variations to generate
            
        Returns:
            List of optimized filter combinations
        """
        
        combinations = []
        
        # Generate variations
        for i in range(variations):
            variant_filters = await self._create_filter_variant(base_filters, i)
            
            # Estimate results and confidence
            estimated_results = await self._estimate_result_count(variant_filters)
            confidence = await self._calculate_filter_confidence(variant_filters)
            
            # Generate optimization notes
            notes = await self._generate_optimization_notes(variant_filters, base_filters)
            
            combination = FilterCombination(
                filters=variant_filters,
                estimated_results=estimated_results,
                confidence=confidence,
                optimization_notes=notes
            )
            
            combinations.append(combination)
        
        # Sort by estimated quality
        combinations.sort(key=lambda c: (c.confidence, -abs(c.estimated_results - 10)), reverse=True)
        
        return combinations
    
    def _parse_business_model(self, business_model: Optional[str]) -> Optional[BusinessModel]:
        """Parse business model string to enum."""
        if not business_model:
            return None
        
        model_mapping = {
            'b2b': BusinessModel.B2B,
            'b2c': BusinessModel.B2C,
            'marketplace': BusinessModel.MARKETPLACE,
            'saas': BusinessModel.SAAS,
            'ecommerce': BusinessModel.ECOMMERCE,
            'enterprise': BusinessModel.ENTERPRISE
        }
        
        return model_mapping.get(business_model.lower())
    
    def _parse_company_size(self, company_size: Optional[str]) -> Optional[CompanySize]:
        """Parse company size string to enum."""
        if not company_size:
            return None
        
        size_mapping = {
            'startup': CompanySize.STARTUP,
            'small': CompanySize.SMALL,
            'medium': CompanySize.MEDIUM,
            'large': CompanySize.LARGE,
            'enterprise': CompanySize.ENTERPRISE
        }
        
        return size_mapping.get(company_size.lower())
    
    def _parse_growth_stage(self, growth_stage: Optional[str]) -> Optional[GrowthStage]:
        """Parse growth stage string to enum."""
        if not growth_stage:
            return None
        
        stage_mapping = {
            'seed': GrowthStage.SEED,
            'series-a': GrowthStage.SERIES_A,
            'series-b': GrowthStage.SERIES_B,
            'growth': GrowthStage.GROWTH,
            'mature': GrowthStage.MATURE
        }
        
        return stage_mapping.get(growth_stage.lower())
    
    async def _normalize_industry(self, industry: Optional[str]) -> Optional[str]:
        """Normalize industry name with fuzzy matching."""
        if not industry:
            return None
        
        industry_lower = industry.lower().strip()
        
        # Direct match
        for parent, children in self.industry_hierarchies.items():
            if industry_lower == parent:
                return parent
            if industry_lower in children:
                return industry_lower
        
        # Fuzzy matching
        best_match = None
        best_score = 0
        
        for parent, children in self.industry_hierarchies.items():
            # Check parent match
            if industry_lower in parent or parent in industry_lower:
                score = len(set(industry_lower.split()) & set(parent.split())) / max(len(industry_lower.split()), len(parent.split()))
                if score > best_score:
                    best_match = parent
                    best_score = score
            
            # Check children matches
            for child in children:
                if industry_lower in child or child in industry_lower:
                    score = len(set(industry_lower.split()) & set(child.split())) / max(len(industry_lower.split()), len(child.split()))
                    if score > best_score:
                        best_match = child
                        best_score = score
        
        return best_match if best_score > 0.5 else industry
    
    def _normalize_location(self, location: Optional[str]) -> Optional[str]:
        """Normalize geographic location."""
        if not location:
            return None
        
        # Basic normalization
        location = location.strip()
        
        # Common location mappings
        location_mappings = {
            'usa': 'United States',
            'us': 'United States',
            'uk': 'United Kingdom',
            'sf': 'San Francisco',
            'ny': 'New York',
            'la': 'Los Angeles'
        }
        
        return location_mappings.get(location.lower(), location)
    
    def _validate_similarity_threshold(self, threshold: float) -> float:
        """Validate and normalize similarity threshold."""
        if threshold < 0.0:
            return 0.0
        elif threshold > 1.0:
            return 1.0
        return threshold
    
    async def _detect_filter_conflicts(self, filters: DiscoveryFilters) -> List[FilterConflict]:
        """Detect conflicts between filters."""
        conflicts = []
        
        # Business model and company size conflicts
        if (filters.business_model == BusinessModel.STARTUP and 
            filters.company_size in [CompanySize.LARGE, CompanySize.ENTERPRISE]):
            conflicts.append(FilterConflict(
                conflict_type=FilterConflictType.INCOMPATIBLE,
                filters_involved=['business_model', 'company_size'],
                description="Startup business model conflicts with large company size",
                suggested_resolution="Use 'startup' or 'small' company size with startup model"
            ))
        
        # Founding date conflicts
        if (filters.founded_after and filters.founded_before and 
            filters.founded_after >= filters.founded_before):
            conflicts.append(FilterConflict(
                conflict_type=FilterConflictType.LOGICAL_INCONSISTENCY,
                filters_involved=['founded_after', 'founded_before'],
                description="Founded after date is not before founded before date",
                suggested_resolution="Ensure founded_after < founded_before"
            ))
        
        # Overly high similarity threshold
        if filters.similarity_threshold > 0.9:
            conflicts.append(FilterConflict(
                conflict_type=FilterConflictType.OVERLY_RESTRICTIVE,
                filters_involved=['similarity_threshold'],
                description="Very high similarity threshold may yield no results",
                suggested_resolution="Consider lowering threshold to 0.7-0.8"
            ))
        
        return conflicts
    
    async def _resolve_filter_conflicts(
        self,
        filters: DiscoveryFilters,
        conflicts: List[FilterConflict]
    ) -> DiscoveryFilters:
        """Automatically resolve filter conflicts where possible."""
        
        resolved_filters = DiscoveryFilters(
            business_model=filters.business_model,
            company_size=filters.company_size,
            industry=filters.industry,
            growth_stage=filters.growth_stage,
            location=filters.location,
            similarity_threshold=filters.similarity_threshold,
            founded_after=filters.founded_after,
            founded_before=filters.founded_before,
            exclude_competitors=filters.exclude_competitors,
            include_subsidiaries=filters.include_subsidiaries
        )
        
        for conflict in conflicts:
            if conflict.conflict_type == FilterConflictType.OVERLY_RESTRICTIVE:
                if 'similarity_threshold' in conflict.filters_involved:
                    resolved_filters.similarity_threshold = 0.7
            
            elif conflict.conflict_type == FilterConflictType.INCOMPATIBLE:
                if 'business_model' in conflict.filters_involved and 'company_size' in conflict.filters_involved:
                    # Prioritize business model, adjust company size
                    if resolved_filters.business_model == BusinessModel.STARTUP:
                        resolved_filters.company_size = CompanySize.STARTUP
        
        return resolved_filters
    
    async def _optimize_filter_combination(self, filters: DiscoveryFilters) -> DiscoveryFilters:
        """Optimize filter combination for better results."""
        
        # Apply business model compatibility expansion
        if filters.business_model and not filters.industry:
            # Suggest compatible business models as alternatives
            compatible_models = self.model_compatibility.get(filters.business_model, [])
            # This could be used for alternative searches
        
        # Industry hierarchy expansion
        if filters.industry:
            # Could expand to include related industries
            pass
        
        return filters
    
    async def _suggest_loosening_filters(self, filters: DiscoveryFilters) -> List[Dict[str, Any]]:
        """Suggest ways to loosen filters to get more results."""
        suggestions = []
        
        if filters.similarity_threshold > 0.6:
            suggestions.append({
                'type': 'loosen_threshold',
                'description': f'Lower similarity threshold from {filters.similarity_threshold:.2f} to 0.6',
                'filter': 'similarity_threshold',
                'suggested_value': 0.6
            })
        
        if filters.business_model:
            compatible_models = self.model_compatibility.get(filters.business_model, [])
            if compatible_models:
                suggestions.append({
                    'type': 'expand_business_model',
                    'description': f'Include compatible business models: {", ".join([m.value for m in compatible_models])}',
                    'filter': 'business_model',
                    'suggested_value': None  # Remove restriction
                })
        
        if filters.location:
            suggestions.append({
                'type': 'remove_location',
                'description': 'Remove location restriction to include global companies',
                'filter': 'location',
                'suggested_value': None
            })
        
        return suggestions
    
    async def _suggest_tightening_filters(self, filters: DiscoveryFilters) -> List[Dict[str, Any]]:
        """Suggest ways to tighten filters to reduce results."""
        suggestions = []
        
        if filters.similarity_threshold < 0.8:
            suggestions.append({
                'type': 'raise_threshold',
                'description': f'Raise similarity threshold from {filters.similarity_threshold:.2f} to 0.8',
                'filter': 'similarity_threshold',
                'suggested_value': 0.8
            })
        
        if not filters.business_model:
            suggestions.append({
                'type': 'add_business_model',
                'description': 'Add business model filter to narrow results',
                'filter': 'business_model',
                'suggested_value': 'saas'  # Common default
            })
        
        if not filters.company_size:
            suggestions.append({
                'type': 'add_company_size',
                'description': 'Add company size filter to narrow results',
                'filter': 'company_size',
                'suggested_value': 'medium'  # Common default
            })
        
        return suggestions
    
    async def _create_filter_variant(self, base_filters: DiscoveryFilters, variant_index: int) -> DiscoveryFilters:
        """Create a variant of the base filters."""
        
        # Create copy of base filters
        variant = DiscoveryFilters(
            business_model=base_filters.business_model,
            company_size=base_filters.company_size,
            industry=base_filters.industry,
            growth_stage=base_filters.growth_stage,
            location=base_filters.location,
            similarity_threshold=base_filters.similarity_threshold,
            founded_after=base_filters.founded_after,
            founded_before=base_filters.founded_before,
            exclude_competitors=base_filters.exclude_competitors,
            include_subsidiaries=base_filters.include_subsidiaries
        )
        
        # Apply variations based on index
        if variant_index == 0:
            # Slightly lower threshold
            variant.similarity_threshold = max(0.4, variant.similarity_threshold - 0.1)
        elif variant_index == 1:
            # Remove business model restriction
            variant.business_model = None
        elif variant_index == 2:
            # Remove location restriction
            variant.location = None
        elif variant_index == 3:
            # More inclusive company size
            if variant.company_size == CompanySize.STARTUP:
                variant.company_size = CompanySize.SMALL
            elif variant.company_size == CompanySize.LARGE:
                variant.company_size = CompanySize.MEDIUM
        elif variant_index == 4:
            # Lower threshold and remove one filter
            variant.similarity_threshold = max(0.5, variant.similarity_threshold - 0.15)
            variant.growth_stage = None
        
        return variant
    
    async def _estimate_result_count(self, filters: DiscoveryFilters) -> int:
        """Estimate number of results for given filters."""
        # This is a simplified estimation
        base_estimate = 50
        
        # Reduce estimate for each restrictive filter
        if filters.business_model:
            base_estimate *= 0.6
        if filters.company_size:
            base_estimate *= 0.7
        if filters.industry:
            base_estimate *= 0.5
        if filters.location:
            base_estimate *= 0.4
        if filters.growth_stage:
            base_estimate *= 0.6
        
        # Similarity threshold impact
        threshold_factor = (1.0 - filters.similarity_threshold) + 0.1
        base_estimate *= threshold_factor
        
        return max(1, int(base_estimate))
    
    async def _calculate_filter_confidence(self, filters: DiscoveryFilters) -> float:
        """Calculate confidence score for filter combination."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for reasonable filters
        if 0.5 <= filters.similarity_threshold <= 0.8:
            confidence += 0.2
        
        if filters.business_model:
            confidence += 0.1
        
        if filters.industry:
            confidence += 0.15
        
        # Decrease confidence for overly restrictive combinations
        restrictive_count = sum([
            bool(filters.business_model),
            bool(filters.company_size),
            bool(filters.industry),
            bool(filters.location),
            bool(filters.growth_stage),
            filters.similarity_threshold > 0.8
        ])
        
        if restrictive_count > 4:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    async def _generate_optimization_notes(
        self,
        variant_filters: DiscoveryFilters,
        base_filters: DiscoveryFilters
    ) -> List[str]:
        """Generate optimization notes for filter variant."""
        notes = []
        
        if variant_filters.similarity_threshold != base_filters.similarity_threshold:
            if variant_filters.similarity_threshold < base_filters.similarity_threshold:
                notes.append("Lowered similarity threshold for broader matching")
            else:
                notes.append("Raised similarity threshold for more precise matching")
        
        if variant_filters.business_model != base_filters.business_model:
            if variant_filters.business_model is None:
                notes.append("Removed business model restriction for wider search")
            else:
                notes.append("Added business model filter for targeted results")
        
        if variant_filters.location != base_filters.location:
            if variant_filters.location is None:
                notes.append("Expanded search globally")
            else:
                notes.append("Added geographic focus")
        
        if not notes:
            notes.append("Alternative filter configuration")
        
        return notes
"""
Filter Validators for Theodore CLI.

Provides validation and normalization for discovery filters.
"""

from typing import Optional, List, Dict, Any
from src.core.domain.entities.company import BusinessModel, CompanySize, GrowthStage


class FilterValidator:
    """Validates and normalizes filter inputs."""
    
    def __init__(self):
        self.valid_business_models = [model.value for model in BusinessModel]
        self.valid_company_sizes = [size.value for size in CompanySize]
        self.valid_growth_stages = [stage.value for stage in GrowthStage]
    
    def validate_business_model(self, model: Optional[str]) -> bool:
        """Validate business model filter."""
        if model is None:
            return True
        return model.lower() in [m.lower() for m in self.valid_business_models]
    
    def validate_company_size(self, size: Optional[str]) -> bool:
        """Validate company size filter."""
        if size is None:
            return True
        return size.lower() in [s.lower() for s in self.valid_company_sizes]
    
    def validate_growth_stage(self, stage: Optional[str]) -> bool:
        """Validate growth stage filter."""
        if stage is None:
            return True
        return stage.lower() in [s.lower() for s in self.valid_growth_stages]
    
    def validate_similarity_threshold(self, threshold: float) -> bool:
        """Validate similarity threshold."""
        return 0.0 <= threshold <= 1.0
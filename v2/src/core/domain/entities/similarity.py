"""
Similarity discovery result domain entity.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid
from enum import Enum


class SimilarityMethod(str, Enum):
    """How similarity was determined"""
    VECTOR_SEARCH = "vector_search"
    GOOGLE_SEARCH = "google_search"
    LLM_SUGGESTION = "llm_suggestion"
    HYBRID = "hybrid"
    MANUAL = "manual"


class RelationshipType(str, Enum):
    """Type of business relationship"""
    COMPETITOR = "competitor"
    ALTERNATIVE = "alternative"
    COMPLEMENTARY = "complementary"
    PARTNER = "partner"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    SIMILAR = "similar"


class ConfidenceLevel(str, Enum):
    """Confidence in similarity assessment"""
    VERY_HIGH = "very_high"  # 0.9-1.0
    HIGH = "high"            # 0.7-0.9
    MEDIUM = "medium"        # 0.5-0.7
    LOW = "low"              # 0.3-0.5
    VERY_LOW = "very_low"    # 0.0-0.3


class SimilarityDimension(BaseModel):
    """A specific dimension of similarity"""
    dimension: str = Field(..., description="What aspect is similar")
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list, max_items=10)
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        if self.score >= 0.9: return ConfidenceLevel.VERY_HIGH
        elif self.score >= 0.7: return ConfidenceLevel.HIGH
        elif self.score >= 0.5: return ConfidenceLevel.MEDIUM
        elif self.score >= 0.3: return ConfidenceLevel.LOW
        else: return ConfidenceLevel.VERY_LOW


class SimilarCompany(BaseModel):
    """A company discovered as similar"""
    id: Optional[str] = Field(None, description="Company ID if in database")
    name: str = Field(..., description="Company name")
    website: Optional[str] = Field(None, description="Company website")
    
    # Basic info if available
    industry: Optional[str] = None
    business_model: Optional[str] = None
    company_size: Optional[str] = None
    description: Optional[str] = None
    
    # Discovery metadata
    discovery_method: SimilarityMethod
    discovery_source: Optional[str] = Field(None, description="Search query or source")
    requires_research: bool = Field(False, description="Needs full research")
    
    def needs_enrichment(self) -> bool:
        """Check if company needs more data"""
        return self.id is None or self.requires_research


class SimilarityResult(BaseModel):
    """
    Result from similarity discovery containing similar companies and analysis.
    """
    model_config = ConfigDict(validate_assignment=True)
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_company_id: Optional[str] = Field(None, description="Source company ID if exists")
    source_company_name: str = Field(..., description="Company we're finding similar to")
    
    # Results
    similar_companies: List[SimilarCompany] = Field(default_factory=list)
    total_found: int = Field(default=0)
    
    # Analysis
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    primary_method: SimilarityMethod = Field(..., description="Primary discovery method")
    methods_used: List[SimilarityMethod] = Field(default_factory=list)
    
    # Detailed similarity analysis
    similarity_dimensions: List[SimilarityDimension] = Field(default_factory=list)
    
    # Search metadata
    search_queries: List[str] = Field(default_factory=list, description="Queries used")
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance
    discovery_duration_seconds: float = Field(default=0.0)
    ai_tokens_used: int = Field(default=0)
    search_api_calls: int = Field(default=0)
    
    # Context
    requested_limit: int = Field(default=10)
    user_id: Optional[str] = None
    discovery_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def add_company(self, company: SimilarCompany, 
                   relationship: RelationshipType = RelationshipType.SIMILAR,
                   confidence: float = 0.5,
                   reasoning: List[str] = None):
        """Add a similar company with relationship details"""
        # Store relationship metadata with the company
        company_data = company.model_dump()
        company_data['relationship_type'] = relationship
        company_data['confidence'] = confidence
        company_data['reasoning'] = reasoning or []
        
        self.similar_companies.append(SimilarCompany(**company_data))
        self.total_found = len(self.similar_companies)
        self._update_overall_confidence()
    
    def add_dimension(self, dimension: str, score: float, evidence: List[str] = None):
        """Add a similarity dimension"""
        self.similarity_dimensions.append(
            SimilarityDimension(
                dimension=dimension,
                score=score,
                evidence=evidence or []
            )
        )
        self._update_overall_confidence()
    
    def _update_overall_confidence(self):
        """Recalculate overall confidence from dimensions"""
        if self.similarity_dimensions:
            scores = [d.score for d in self.similarity_dimensions]
            self.overall_confidence = sum(scores) / len(scores)
    
    def get_high_confidence_companies(self, min_confidence: float = 0.7) -> List[SimilarCompany]:
        """Get only high-confidence similar companies"""
        return [
            c for c in self.similar_companies 
            if hasattr(c, 'confidence') and c.confidence >= min_confidence
        ]
    
    def get_companies_by_relationship(self, relationship: RelationshipType) -> List[SimilarCompany]:
        """Get companies by relationship type"""
        return [
            c for c in self.similar_companies
            if hasattr(c, 'relationship_type') and c.relationship_type == relationship
        ]
    
    def needs_enrichment_count(self) -> int:
        """Count how many companies need enrichment"""
        return sum(1 for c in self.similar_companies if c.needs_enrichment())
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get overall confidence level"""
        if self.overall_confidence >= 0.9: return ConfidenceLevel.VERY_HIGH
        elif self.overall_confidence >= 0.7: return ConfidenceLevel.HIGH
        elif self.overall_confidence >= 0.5: return ConfidenceLevel.MEDIUM
        elif self.overall_confidence >= 0.3: return ConfidenceLevel.LOW
        else: return ConfidenceLevel.VERY_LOW
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of results"""
        return {
            "source_company": self.source_company_name,
            "total_found": self.total_found,
            "confidence_level": self.confidence_level.value,
            "primary_method": self.primary_method.value,
            "top_companies": [
                {
                    "name": c.name,
                    "website": c.website,
                    "confidence": getattr(c, 'confidence', 0.0)
                } 
                for c in self.similar_companies[:5]
            ],
            "needs_enrichment": self.needs_enrichment_count()
        }
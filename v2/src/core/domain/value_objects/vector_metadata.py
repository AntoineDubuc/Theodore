"""
Vector metadata value objects for Theodore.

This module defines specialized metadata structures for different
types of vector operations and entity types.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class VectorEntityType(str, Enum):
    """Types of entities that can be stored as vectors."""
    
    COMPANY = "company"
    RESEARCH = "research"
    SIMILARITY = "similarity"
    CONTENT = "content"
    ANALYSIS = "analysis"
    UNKNOWN = "unknown"


class VectorQuality(str, Enum):
    """Quality levels for vector embeddings."""
    
    HIGH = "high"          # >0.9 confidence
    GOOD = "good"          # 0.7-0.9 confidence  
    MEDIUM = "medium"      # 0.5-0.7 confidence
    LOW = "low"           # 0.3-0.5 confidence
    POOR = "poor"         # <0.3 confidence
    UNKNOWN = "unknown"   # No confidence score


class CompanyVectorMetadata(BaseModel):
    """Specialized metadata for company vectors."""
    
    # Company identification
    company_name: str = Field(description="Name of the company")
    company_domain: Optional[str] = Field(
        default=None,
        description="Company website domain"
    )
    company_id: Optional[str] = Field(
        default=None,
        description="Internal company identifier"
    )
    
    # Company characteristics  
    industry: Optional[str] = Field(
        default=None,
        description="Company industry classification"
    )
    size_category: Optional[str] = Field(
        default=None,
        description="Company size (startup, small, medium, large, enterprise)"
    )
    stage: Optional[str] = Field(
        default=None,
        description="Company stage (seed, series-a, growth, mature)"
    )
    business_model: Optional[str] = Field(
        default=None,
        description="Business model (b2b, b2c, marketplace, saas, etc.)"
    )
    
    # Location data
    headquarters: Optional[str] = Field(
        default=None,
        description="Company headquarters location"
    )
    regions: List[str] = Field(
        default_factory=list,
        description="Regions where company operates"
    )
    
    # Technology data
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies used by the company"
    )
    tech_sophistication: Optional[str] = Field(
        default=None,
        description="Technology sophistication level"
    )
    
    # Financial data
    funding_stage: Optional[str] = Field(
        default=None,
        description="Current funding stage"
    )
    revenue_range: Optional[str] = Field(
        default=None,
        description="Estimated revenue range"
    )
    
    # Research metadata
    research_date: Optional[datetime] = Field(
        default=None,
        description="When company was researched"
    )
    research_source: Optional[str] = Field(
        default=None,
        description="Source of company information"
    )
    research_quality: Optional[str] = Field(
        default=None,
        description="Quality of research data"
    )
    
    # Vector generation metadata
    content_sources: List[str] = Field(
        default_factory=list,
        description="Sources used to generate vector (website, crunchbase, etc.)"
    )
    extraction_method: Optional[str] = Field(
        default=None,
        description="Method used to extract company data"
    )
    
    def get_display_name(self) -> str:
        """Get display name for the company."""
        return self.company_name
    
    def get_primary_identifier(self) -> str:
        """Get primary identifier (company_id or domain or name)."""
        return self.company_id or self.company_domain or self.company_name
    
    def has_location_data(self) -> bool:
        """Check if location data is available."""
        return bool(self.headquarters or self.regions)
    
    def has_tech_data(self) -> bool:
        """Check if technology data is available."""
        return bool(self.tech_stack or self.tech_sophistication)
    
    def has_financial_data(self) -> bool:
        """Check if financial data is available."""
        return bool(self.funding_stage or self.revenue_range)


class ResearchVectorMetadata(BaseModel):
    """Specialized metadata for research content vectors."""
    
    # Research identification
    research_id: str = Field(description="Unique research identifier")
    research_type: str = Field(description="Type of research (company, market, competitor)")
    
    # Research content
    research_prompt: Optional[str] = Field(
        default=None,
        description="Research prompt used"
    )
    research_focus: Optional[str] = Field(
        default=None,
        description="Focus area of research"
    )
    
    # Research quality
    research_depth: Optional[str] = Field(
        default=None,
        description="Depth of research (surface, detailed, comprehensive)"
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Sources used for research"
    )
    
    # Research timing
    research_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When research was conducted"
    )
    expiry_date: Optional[datetime] = Field(
        default=None,
        description="When research data expires"
    )
    
    # Associated entities
    related_companies: List[str] = Field(
        default_factory=list,
        description="Companies related to this research"
    )
    related_topics: List[str] = Field(
        default_factory=list,
        description="Topics covered in research"
    )
    
    # Research metrics
    token_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of tokens in research content"
    )
    cost_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Cost of research in USD"
    )
    
    def is_expired(self) -> bool:
        """Check if research has expired."""
        if not self.expiry_date:
            return False
        return datetime.utcnow() > self.expiry_date
    
    def get_age_days(self) -> int:
        """Get age of research in days."""
        return (datetime.utcnow() - self.research_date).days
    
    def is_recent(self, days: int = 30) -> bool:
        """Check if research is recent (within specified days)."""
        return self.get_age_days() <= days


class ContentVectorMetadata(BaseModel):
    """Specialized metadata for content vectors."""
    
    # Content identification
    content_id: str = Field(description="Unique content identifier")
    content_type: str = Field(description="Type of content (webpage, document, article)")
    
    # Content source
    source_url: Optional[str] = Field(
        default=None,
        description="URL where content was found"
    )
    source_domain: Optional[str] = Field(
        default=None,
        description="Domain of content source"
    )
    source_title: Optional[str] = Field(
        default=None,
        description="Title of content source"
    )
    
    # Content characteristics
    content_length: int = Field(
        ge=0,
        description="Length of content in characters"
    )
    language: Optional[str] = Field(
        default="en",
        description="Language of content"
    )
    
    # Content quality
    readability_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Readability score (0-100)"
    )
    information_density: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Information density score"
    )
    
    # Content extraction
    extraction_method: str = Field(description="Method used to extract content")
    extraction_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When content was extracted"
    )
    
    # Content topics
    topics: List[str] = Field(
        default_factory=list,
        description="Topics identified in content"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords extracted from content"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Named entities found in content"
    )
    
    def get_word_count(self) -> int:
        """Estimate word count from character length."""
        return self.content_length // 5  # Rough estimate
    
    def is_high_quality(self) -> bool:
        """Check if content is high quality."""
        if self.readability_score and self.readability_score < 30:
            return False
        if self.information_density and self.information_density < 0.3:
            return False
        return self.content_length >= 500  # Minimum content length
    
    def has_rich_metadata(self) -> bool:
        """Check if content has rich metadata."""
        return bool(self.topics and self.keywords and len(self.entities) > 0)


class VectorEmbeddingMetadata(BaseModel):
    """Metadata about the embedding generation process."""
    
    # Embedding model info
    model_name: str = Field(description="Name of embedding model used")
    model_version: Optional[str] = Field(
        default=None,
        description="Version of embedding model"
    )
    model_provider: str = Field(description="Provider of embedding model")
    
    # Embedding characteristics
    dimensions: int = Field(
        ge=1,
        description="Number of dimensions in embedding"
    )
    normalization: bool = Field(
        default=True,
        description="Whether embedding is normalized"
    )
    
    # Generation metadata
    generation_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When embedding was generated"
    )
    generation_time_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Time taken to generate embedding"
    )
    
    # Quality metrics
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in embedding quality"
    )
    quality_level: VectorQuality = Field(
        default=VectorQuality.UNKNOWN,
        description="Quality assessment of embedding"
    )
    
    # Cost and usage
    token_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of tokens processed"
    )
    cost_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Cost of embedding generation in USD"
    )
    
    # Technical metadata
    input_hash: Optional[str] = Field(
        default=None,
        description="Hash of input text for deduplication"
    )
    preprocessing_steps: List[str] = Field(
        default_factory=list,
        description="Preprocessing steps applied to input"
    )
    
    def get_quality_score(self) -> float:
        """Get numeric quality score."""
        quality_scores = {
            VectorQuality.HIGH: 0.95,
            VectorQuality.GOOD: 0.8,
            VectorQuality.MEDIUM: 0.65,
            VectorQuality.LOW: 0.4,
            VectorQuality.POOR: 0.2,
            VectorQuality.UNKNOWN: 0.5
        }
        return quality_scores.get(self.quality_level, 0.5)
    
    def is_high_quality(self) -> bool:
        """Check if embedding is high quality."""
        return self.quality_level in {VectorQuality.HIGH, VectorQuality.GOOD}
    
    def is_normalized(self) -> bool:
        """Check if embedding is normalized."""
        return self.normalization
    
    def get_age_hours(self) -> float:
        """Get age of embedding in hours."""
        delta = datetime.utcnow() - self.generation_date
        return delta.total_seconds() / 3600


class UnifiedVectorMetadata(BaseModel):
    """Unified metadata structure combining all vector metadata types."""
    
    # Core metadata (always present)
    entity_id: str = Field(description="Unique identifier for entity")
    entity_type: VectorEntityType = Field(description="Type of entity")
    vector_id: str = Field(description="Unique vector identifier")
    
    # Embedding metadata (always present)
    embedding: VectorEmbeddingMetadata = Field(description="Embedding generation metadata")
    
    # Specialized metadata (conditional)
    company: Optional[CompanyVectorMetadata] = Field(
        default=None,
        description="Company-specific metadata"
    )
    research: Optional[ResearchVectorMetadata] = Field(
        default=None,
        description="Research-specific metadata"
    )
    content: Optional[ContentVectorMetadata] = Field(
        default=None,
        description="Content-specific metadata"
    )
    
    # Storage metadata
    index_name: str = Field(description="Name of vector index")
    namespace: Optional[str] = Field(
        default=None,
        description="Vector namespace"
    )
    
    # System metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When vector was stored"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When vector was last updated"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Version number for updates"
    )
    
    # Additional metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom fields"
    )
    
    @field_validator('company', 'research', 'content', mode='before')
    @classmethod 
    def validate_specialized_metadata(cls, v, info):
        """Validate that specialized metadata matches entity type."""
        # Skip validation if we don't have context
        if not info.data:
            return v
        
        entity_type = info.data.get('entity_type')
        field_name = info.field_name
        
        if entity_type == VectorEntityType.COMPANY and field_name == 'company':
            if v is None:
                raise ValueError("Company metadata required for company entities")
        elif entity_type == VectorEntityType.RESEARCH and field_name == 'research':
            if v is None:
                raise ValueError("Research metadata required for research entities")
        elif entity_type == VectorEntityType.CONTENT and field_name == 'content':
            if v is None:
                raise ValueError("Content metadata required for content entities")
        
        return v
    
    def get_display_name(self) -> str:
        """Get display name for the entity."""
        if self.company:
            return self.company.get_display_name()
        elif self.research:
            return f"Research: {self.research.research_type}"
        elif self.content:
            return self.content.source_title or f"Content: {self.content.content_type}"
        else:
            return f"{self.entity_type}: {self.entity_id}"
    
    def get_primary_identifier(self) -> str:
        """Get primary identifier for the entity."""
        if self.company:
            return self.company.get_primary_identifier()
        else:
            return self.entity_id
    
    def is_high_quality(self) -> bool:
        """Check if vector is high quality."""
        if not self.embedding.is_high_quality():
            return False
        
        if self.content and not self.content.is_high_quality():
            return False
        
        return True
    
    def has_tag(self, tag: str) -> bool:
        """Check if vector has a specific tag."""
        return tag in self.tags
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the vector."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field value."""
        return self.custom_fields.get(key, default)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field value."""
        self.custom_fields[key] = value
        self.updated_at = datetime.utcnow()
        self.version += 1
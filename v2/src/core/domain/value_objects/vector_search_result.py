"""
Vector search result value objects for Theodore.

This module defines the value objects for vector search operations,
including search results, configurations, and metadata structures.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass


class VectorSearchConfig(BaseModel):
    """Configuration for vector search operations."""
    
    top_k: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Number of most similar vectors to return"
    )
    
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0.0-1.0)"
    )
    
    distance_metric: str = Field(
        default="cosine",
        description="Distance metric for similarity calculation"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include metadata in results"
    )
    
    include_values: bool = Field(
        default=False,
        description="Whether to include vector values in results"
    )
    
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata filter conditions"
    )
    
    namespace: Optional[str] = Field(
        default=None,
        description="Vector namespace to search within"
    )
    
    @field_validator('distance_metric')
    @classmethod
    def validate_distance_metric(cls, v):
        valid_metrics = {'cosine', 'euclidean', 'dot_product', 'manhattan', 'chebyshev'}
        if v not in valid_metrics:
            raise ValueError(f"distance_metric must be one of {valid_metrics}")
        return v
    
    @classmethod
    def for_similarity_search(
        cls,
        top_k: int = 10,
        threshold: float = 0.7,
        include_metadata: bool = True
    ) -> 'VectorSearchConfig':
        """Create config optimized for similarity search."""
        return cls(
            top_k=top_k,
            similarity_threshold=threshold,
            distance_metric="cosine",
            include_metadata=include_metadata,
            include_values=False
        )
    
    @classmethod
    def for_discovery(
        cls,
        top_k: int = 20,
        threshold: float = 0.6
    ) -> 'VectorSearchConfig':
        """Create config optimized for company discovery."""
        return cls(
            top_k=top_k,
            similarity_threshold=threshold,
            distance_metric="cosine",
            include_metadata=True,
            include_values=False
        )


class VectorMetadata(BaseModel):
    """Metadata associated with a vector."""
    
    # Core identification
    entity_id: str = Field(description="Unique identifier for the entity")
    entity_type: str = Field(description="Type of entity (e.g., 'company', 'research')")
    
    # Content metadata
    content_hash: Optional[str] = Field(
        default=None,
        description="Hash of the content that generated this vector"
    )
    content_length: Optional[int] = Field(
        default=None,
        ge=0,
        description="Length of original content in characters"
    )
    
    # Vector metadata
    vector_dimensions: int = Field(ge=1, description="Number of dimensions in vector")
    embedding_model: Optional[str] = Field(
        default=None,
        description="Model used to generate embedding"
    )
    embedding_provider: Optional[str] = Field(
        default=None,
        description="Provider used for embedding generation"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When vector was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When vector was last updated"
    )
    
    # Quality metrics
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the embedding quality"
    )
    
    # Additional flexible metadata
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata fields"
    )
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom metadata field value."""
        return self.custom_fields.get(key, default)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom metadata field value."""
        self.custom_fields[key] = value
    
    def has_custom_field(self, key: str) -> bool:
        """Check if a custom metadata field exists."""
        return key in self.custom_fields


class VectorSearchMatch(BaseModel):
    """A single match from vector search."""
    
    # Match identification
    vector_id: str = Field(description="Unique identifier for the vector")
    entity_id: str = Field(description="Identifier for the entity this vector represents")
    
    # Similarity metrics
    similarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Similarity score (0.0-1.0, higher is more similar)"
    )
    distance: float = Field(
        ge=0.0,
        description="Distance metric value (lower is more similar)"
    )
    
    # Content and metadata
    metadata: Optional[VectorMetadata] = Field(
        default=None,
        description="Vector metadata if requested"
    )
    vector_values: Optional[List[float]] = Field(
        default=None,
        description="Vector values if requested"
    )
    
    # Search context
    rank: int = Field(
        default=1,
        ge=1,
        description="Rank in search results (1-based)"
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace where vector was found"
    )
    
    def meets_threshold(self, threshold: float) -> bool:
        """Check if this match meets the similarity threshold."""
        return self.similarity_score >= threshold
    
    def is_highly_similar(self, threshold: float = 0.8) -> bool:
        """Check if this is a high-similarity match."""
        return self.similarity_score >= threshold
    
    def get_metadata_field(self, key: str, default: Any = None) -> Any:
        """Get a metadata field value."""
        if not self.metadata:
            return default
        return self.metadata.get_custom_field(key, default)


class VectorSearchResult(BaseModel):
    """Complete result from a vector search operation."""
    
    # Search parameters
    query_vector: Optional[List[float]] = Field(
        default=None,
        description="Query vector used for search"
    )
    config: VectorSearchConfig = Field(description="Search configuration used")
    
    # Results
    matches: List[VectorSearchMatch] = Field(
        default_factory=list,
        description="List of matching vectors"
    )
    total_matches: int = Field(
        ge=0,
        description="Total number of matches found"
    )
    
    # Search metadata
    search_time_ms: float = Field(
        ge=0.0,
        description="Time taken for search in milliseconds"
    )
    index_name: str = Field(description="Name of index searched")
    namespace: Optional[str] = Field(
        default=None,
        description="Namespace searched"
    )
    
    # Quality metrics
    max_similarity: Optional[float] = Field(
        default=None,
        description="Highest similarity score in results"
    )
    min_similarity: Optional[float] = Field(
        default=None,
        description="Lowest similarity score in results"
    )
    avg_similarity: Optional[float] = Field(
        default=None,
        description="Average similarity score of results"
    )
    
    # Pagination
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset used in search"
    )
    has_more: bool = Field(
        default=False,
        description="Whether more results are available"
    )
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate derived metrics after initialization."""
        if self.matches:
            similarities = [match.similarity_score for match in self.matches]
            self.max_similarity = max(similarities)
            self.min_similarity = min(similarities)
            self.avg_similarity = sum(similarities) / len(similarities)
        else:
            self.max_similarity = None
            self.min_similarity = None
            self.avg_similarity = None
    
    def get_top_matches(self, k: int) -> List[VectorSearchMatch]:
        """Get top K matches."""
        return self.matches[:k]
    
    def filter_by_threshold(self, threshold: float) -> List[VectorSearchMatch]:
        """Filter matches by similarity threshold."""
        return [match for match in self.matches if match.similarity_score >= threshold]
    
    def get_highly_similar(self, threshold: float = 0.8) -> List[VectorSearchMatch]:
        """Get highly similar matches above threshold."""
        return self.filter_by_threshold(threshold)
    
    def has_good_matches(self, threshold: float = 0.7) -> bool:
        """Check if there are good quality matches."""
        return any(match.similarity_score >= threshold for match in self.matches)
    
    def get_entity_ids(self) -> List[str]:
        """Get list of entity IDs from matches."""
        return [match.entity_id for match in self.matches]
    
    def group_by_entity_type(self) -> Dict[str, List[VectorSearchMatch]]:
        """Group matches by entity type."""
        groups = {}
        for match in self.matches:
            if match.metadata:
                entity_type = match.metadata.entity_type
                if entity_type not in groups:
                    groups[entity_type] = []
                groups[entity_type].append(match)
        return groups


@dataclass
class VectorOperationResult:
    """Result from a vector storage operation."""
    
    success: bool
    operation: str  # 'upsert', 'delete', 'get', 'search'
    affected_count: int = 0
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(
        cls,
        operation: str,
        affected_count: int = 1,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'VectorOperationResult':
        """Create a successful operation result."""
        return cls(
            success=True,
            operation=operation,
            affected_count=affected_count,
            message=message,
            metadata=metadata
        )
    
    @classmethod
    def error_result(
        cls,
        operation: str,
        error: str,
        affected_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'VectorOperationResult':
        """Create an error operation result."""
        return cls(
            success=False,
            operation=operation,
            affected_count=affected_count,
            error=error,
            metadata=metadata
        )


@dataclass
class IndexStats:
    """Statistics about a vector index."""
    
    name: str
    total_vectors: int
    dimensions: int
    namespaces: List[str]
    
    # Size metrics
    size_bytes: Optional[int] = None
    avg_vector_size: Optional[float] = None
    
    # Performance metrics
    avg_search_time_ms: Optional[float] = None
    total_searches: Optional[int] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def size_mb(self) -> Optional[float]:
        """Get index size in megabytes."""
        if self.size_bytes is None:
            return None
        return self.size_bytes / (1024 * 1024)
    
    @property
    def is_empty(self) -> bool:
        """Check if index is empty."""
        return self.total_vectors == 0
    
    def get_namespace_count(self) -> int:
        """Get number of namespaces."""
        return len(self.namespaces)


# Filter operations for metadata filtering
class FilterOperation:
    """Constants for metadata filter operations."""
    
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class LogicalOperation:
    """Constants for logical operations in filters."""
    
    AND = "and"
    OR = "or"
    NOT = "not"


# Distance metrics
class DistanceMetric:
    """Constants for vector distance metrics."""
    
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    CHEBYSHEV = "chebyshev"
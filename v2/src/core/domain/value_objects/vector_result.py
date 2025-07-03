"""
Vector operation result value objects for Theodore.

This module provides comprehensive result objects for vector database
operations, including search results, insertion results, and bulk
operation outcomes with detailed metrics and error information.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import json


class OperationStatus(str, Enum):
    """Status of vector database operations"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class VectorOperationType(str, Enum):
    """Types of vector operations"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    BULK_INSERT = "bulk_insert"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    INDEX_CREATE = "index_create"
    INDEX_DELETE = "index_delete"
    HEALTH_CHECK = "health_check"


class VectorRecord(BaseModel):
    """Individual vector record with metadata"""
    
    # Core vector data
    id: str = Field(..., description="Unique identifier for the vector")
    vector: List[float] = Field(..., description="Vector values")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated metadata")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in vector quality")
    
    # Provenance
    source: Optional[str] = Field(None, description="Source of the vector data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @field_validator('vector')
    @classmethod
    def validate_vector_not_empty(cls, v):
        if not v:
            raise ValueError("Vector cannot be empty")
        return v
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Vector ID cannot be empty")
        return v.strip()
    
    @property
    def dimensions(self) -> int:
        """Get vector dimensions"""
        return len(self.vector)
    
    def magnitude(self) -> float:
        """Calculate vector magnitude (L2 norm)"""
        return sum(x**2 for x in self.vector) ** 0.5
    
    def is_normalized(self, tolerance: float = 1e-6) -> bool:
        """Check if vector is normalized"""
        mag = self.magnitude()
        return abs(mag - 1.0) < tolerance
    
    def normalize(self) -> 'VectorRecord':
        """Return normalized version of this vector"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        
        normalized_vector = [x / mag for x in self.vector]
        return self.model_copy(update={
            "vector": normalized_vector,
            "updated_at": datetime.utcnow()
        })
    
    def to_dict(self, include_vector: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "id": self.id,
            "metadata": self.metadata,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "dimensions": self.dimensions,
            "magnitude": self.magnitude(),
            "is_normalized": self.is_normalized()
        }
        
        if include_vector:
            result["vector"] = self.vector
        
        return result


class SearchMatch(BaseModel):
    """Individual search result match"""
    
    # Core match data
    record: VectorRecord = Field(..., description="Matched vector record")
    score: float = Field(..., description="Similarity score")
    
    # Search context
    rank: int = Field(..., ge=1, description="Rank in search results (1-based)")
    distance: Optional[float] = Field(None, description="Distance metric (if applicable)")
    
    # Quality indicators
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Match confidence")
    
    @property
    def similarity_percentage(self) -> float:
        """Convert score to percentage (0-100)"""
        return max(0, min(100, self.score * 100))
    
    def to_dict(self, include_vector: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "record": self.record.to_dict(include_vector=include_vector),
            "score": self.score,
            "rank": self.rank,
            "distance": self.distance,
            "confidence": self.confidence,
            "similarity_percentage": self.similarity_percentage
        }


class VectorSearchResult(BaseModel):
    """Result from vector similarity search"""
    
    # Search results
    matches: List[SearchMatch] = Field(..., description="Search matches")
    total_matches: int = Field(..., ge=0, description="Total number of matches found")
    
    # Search metadata
    query_vector: Optional[List[float]] = Field(None, description="Original query vector")
    search_id: str = Field(..., description="Unique search identifier")
    
    # Performance metrics
    search_time: float = Field(..., ge=0.0, description="Search execution time in seconds")
    index_search_time: Optional[float] = Field(None, ge=0.0, description="Index search time")
    
    # Search parameters used
    top_k: int = Field(..., gt=0, description="Number of results requested")
    similarity_threshold: Optional[float] = Field(None, description="Similarity threshold used")
    metadata_filter: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters applied")
    
    # Quality metrics
    max_score: Optional[float] = Field(None, description="Highest similarity score")
    min_score: Optional[float] = Field(None, description="Lowest similarity score")
    avg_score: Optional[float] = Field(None, description="Average similarity score")
    
    # Provider information
    provider_name: str = Field(..., description="Vector database provider")
    index_name: str = Field(..., description="Index searched")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate score statistics
        if self.matches:
            scores = [match.score for match in self.matches]
            self.max_score = max(scores) if not self.max_score else self.max_score
            self.min_score = min(scores) if not self.min_score else self.min_score
            self.avg_score = sum(scores) / len(scores) if not self.avg_score else self.avg_score
    
    @property
    def has_matches(self) -> bool:
        """Check if search returned any matches"""
        return len(self.matches) > 0
    
    @property
    def results_truncated(self) -> bool:
        """Check if results were truncated due to top_k limit"""
        return self.total_matches > len(self.matches)
    
    def get_top_matches(self, n: int) -> List[SearchMatch]:
        """Get top N matches"""
        return self.matches[:n]
    
    def filter_by_threshold(self, threshold: float) -> List[SearchMatch]:
        """Filter matches by minimum similarity threshold"""
        return [match for match in self.matches if match.score >= threshold]
    
    def to_dict(self, include_vectors: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "matches": [match.to_dict(include_vector=include_vectors) for match in self.matches],
            "total_matches": self.total_matches,
            "search_id": self.search_id,
            "search_time": self.search_time,
            "index_search_time": self.index_search_time,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "metadata_filter": self.metadata_filter,
            "max_score": self.max_score,
            "min_score": self.min_score,
            "avg_score": self.avg_score,
            "provider_name": self.provider_name,
            "index_name": self.index_name,
            "timestamp": self.timestamp.isoformat(),
            "has_matches": self.has_matches,
            "results_truncated": self.results_truncated
        }


class VectorOperationResult(BaseModel):
    """Result from vector database operations (insert, update, delete)"""
    
    # Operation details
    operation_type: VectorOperationType = Field(..., description="Type of operation performed")
    operation_id: str = Field(..., description="Unique operation identifier")
    status: OperationStatus = Field(..., description="Operation status")
    
    # Results
    successful_count: int = Field(0, ge=0, description="Number of successful operations")
    failed_count: int = Field(0, ge=0, description="Number of failed operations")
    total_count: int = Field(..., gt=0, description="Total number of operations attempted")
    
    # Performance metrics
    execution_time: float = Field(..., ge=0.0, description="Total execution time in seconds")
    throughput: float = Field(0.0, ge=0.0, description="Operations per second")
    
    # Error information
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")
    
    # Provider information
    provider_name: str = Field(..., description="Vector database provider")
    index_name: str = Field(..., description="Index operated on")
    
    # Detailed results (for operations that return data)
    affected_ids: List[str] = Field(default_factory=list, description="IDs of affected records")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate throughput
        if self.execution_time > 0:
            self.throughput = self.total_count / self.execution_time
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_count == 0:
            return 0.0
        return self.successful_count / self.total_count
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage"""
        return 1.0 - self.success_rate
    
    @property
    def is_successful(self) -> bool:
        """Check if operation was successful"""
        return self.status == OperationStatus.SUCCESS
    
    @property
    def is_partial_success(self) -> bool:
        """Check if operation had partial success"""
        return self.status == OperationStatus.PARTIAL_SUCCESS
    
    def add_error(self, error_message: str, error_code: Optional[str] = None, record_id: Optional[str] = None):
        """Add an error to the result"""
        error_entry = {
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_code:
            error_entry["code"] = error_code
        if record_id:
            error_entry["record_id"] = record_id
        
        self.errors.append(error_entry)
        self.failed_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_type": self.operation_type,
            "operation_id": self.operation_id,
            "status": self.status,
            "successful_count": self.successful_count,
            "failed_count": self.failed_count,
            "total_count": self.total_count,
            "execution_time": self.execution_time,
            "throughput": self.throughput,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "errors": self.errors,
            "provider_name": self.provider_name,
            "index_name": self.index_name,
            "affected_ids": self.affected_ids,
            "timestamp": self.timestamp.isoformat(),
            "is_successful": self.is_successful,
            "is_partial_success": self.is_partial_success
        }


class BulkOperationResult(BaseModel):
    """Result from bulk vector operations"""
    
    # Bulk operation metadata
    bulk_operation_id: str = Field(..., description="Unique bulk operation identifier")
    operation_type: VectorOperationType = Field(..., description="Type of bulk operation")
    status: OperationStatus = Field(..., description="Overall bulk operation status")
    
    # Batch results
    batch_results: List[VectorOperationResult] = Field(..., description="Results from individual batches")
    total_batches: int = Field(..., gt=0, description="Total number of batches")
    successful_batches: int = Field(0, ge=0, description="Number of successful batches")
    failed_batches: int = Field(0, ge=0, description="Number of failed batches")
    
    # Aggregated metrics
    total_records_processed: int = Field(0, ge=0, description="Total records processed")
    total_successful_records: int = Field(0, ge=0, description="Total successful records")
    total_failed_records: int = Field(0, ge=0, description="Total failed records")
    
    # Performance metrics
    total_execution_time: float = Field(..., ge=0.0, description="Total execution time in seconds")
    average_batch_time: float = Field(0.0, ge=0.0, description="Average time per batch")
    overall_throughput: float = Field(0.0, ge=0.0, description="Overall records per second")
    
    # Error summary
    error_summary: Dict[str, int] = Field(default_factory=dict, description="Summary of error types")
    
    # Resource usage
    peak_memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage in MB")
    cpu_time_seconds: Optional[float] = Field(None, description="Total CPU time used")
    
    # Provider information
    provider_name: str = Field(..., description="Vector database provider")
    index_name: str = Field(..., description="Index operated on")
    
    # Progress tracking
    started_at: datetime = Field(..., description="Bulk operation start time")
    completed_at: Optional[datetime] = Field(None, description="Bulk operation completion time")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate aggregated metrics from batch results
        if self.batch_results:
            self.total_records_processed = sum(batch.total_count for batch in self.batch_results)
            self.total_successful_records = sum(batch.successful_count for batch in self.batch_results)
            self.total_failed_records = sum(batch.failed_count for batch in self.batch_results)
            
            # Calculate throughput
            if self.total_execution_time > 0:
                self.overall_throughput = self.total_records_processed / self.total_execution_time
            
            # Calculate average batch time
            if self.total_batches > 0:
                self.average_batch_time = self.total_execution_time / self.total_batches
            
            # Generate error summary
            error_counts = {}
            for batch in self.batch_results:
                for error in batch.errors:
                    error_type = error.get("code", "unknown_error")
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
            self.error_summary = error_counts
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_records_processed == 0:
            return 0.0
        return self.total_successful_records / self.total_records_processed
    
    @property
    def batch_success_rate(self) -> float:
        """Calculate batch-level success rate"""
        if self.total_batches == 0:
            return 0.0
        return self.successful_batches / self.total_batches
    
    @property
    def is_complete(self) -> bool:
        """Check if bulk operation is complete"""
        return self.completed_at is not None
    
    @property
    def duration(self) -> Optional[float]:
        """Get total duration of bulk operation"""
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def get_failed_batches(self) -> List[VectorOperationResult]:
        """Get all failed batch results"""
        return [batch for batch in self.batch_results if not batch.is_successful]
    
    def get_most_common_errors(self, top_n: int = 5) -> List[tuple[str, int]]:
        """Get most common error types"""
        return sorted(self.error_summary.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def to_dict(self, include_batch_details: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "bulk_operation_id": self.bulk_operation_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "total_batches": self.total_batches,
            "successful_batches": self.successful_batches,
            "failed_batches": self.failed_batches,
            "total_records_processed": self.total_records_processed,
            "total_successful_records": self.total_successful_records,
            "total_failed_records": self.total_failed_records,
            "total_execution_time": self.total_execution_time,
            "average_batch_time": self.average_batch_time,
            "overall_throughput": self.overall_throughput,
            "overall_success_rate": self.overall_success_rate,
            "batch_success_rate": self.batch_success_rate,
            "error_summary": self.error_summary,
            "peak_memory_usage_mb": self.peak_memory_usage_mb,
            "cpu_time_seconds": self.cpu_time_seconds,
            "provider_name": self.provider_name,
            "index_name": self.index_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_complete": self.is_complete,
            "duration": self.duration,
            "most_common_errors": self.get_most_common_errors()
        }
        
        if include_batch_details:
            result["batch_results"] = [batch.to_dict() for batch in self.batch_results]
        
        return result


class IndexInfo(BaseModel):
    """Information about a vector index"""
    
    # Index identification
    name: str = Field(..., description="Index name")
    provider: str = Field(..., description="Vector database provider")
    
    # Index configuration
    dimensions: int = Field(..., gt=0, description="Vector dimensions")
    similarity_metric: str = Field(..., description="Similarity metric used")
    index_type: str = Field(..., description="Index algorithm type")
    
    # Statistics
    total_vectors: int = Field(0, ge=0, description="Total number of vectors in index")
    index_size_bytes: int = Field(0, ge=0, description="Index size in bytes")
    
    # Performance metrics
    average_query_latency: Optional[float] = Field(None, description="Average query latency in ms")
    queries_per_second: Optional[float] = Field(None, description="Queries per second capacity")
    
    # Health status
    status: str = Field("unknown", description="Index health status")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Resource usage
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    disk_usage_mb: Optional[float] = Field(None, description="Disk usage in MB")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "provider": self.provider,
            "dimensions": self.dimensions,
            "similarity_metric": self.similarity_metric,
            "index_type": self.index_type,
            "total_vectors": self.total_vectors,
            "index_size_bytes": self.index_size_bytes,
            "index_size_mb": self.index_size_bytes / (1024 * 1024) if self.index_size_bytes else 0,
            "average_query_latency": self.average_query_latency,
            "queries_per_second": self.queries_per_second,
            "status": self.status,
            "last_updated": self.last_updated.isoformat(),
            "memory_usage_mb": self.memory_usage_mb,
            "disk_usage_mb": self.disk_usage_mb
        }


# Utility functions for creating result objects
def create_successful_operation_result(
    operation_type: VectorOperationType,
    count: int,
    execution_time: float,
    provider_name: str,
    index_name: str,
    **kwargs
) -> VectorOperationResult:
    """Create a successful operation result"""
    return VectorOperationResult(
        operation_type=operation_type,
        operation_id=f"op_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        status=OperationStatus.SUCCESS,
        successful_count=count,
        failed_count=0,
        total_count=count,
        execution_time=execution_time,
        provider_name=provider_name,
        index_name=index_name,
        **kwargs
    )


def create_search_result_from_raw(
    matches_data: List[Dict[str, Any]],
    search_id: str,
    search_time: float,
    provider_name: str,
    index_name: str,
    **kwargs
) -> VectorSearchResult:
    """Create search result from raw match data"""
    matches = []
    for i, match_data in enumerate(matches_data):
        record = VectorRecord(
            id=match_data["id"],
            vector=match_data.get("vector", []),
            metadata=match_data.get("metadata", {}),
            confidence_score=match_data.get("confidence")
        )
        
        match = SearchMatch(
            record=record,
            score=match_data["score"],
            rank=i + 1,
            distance=match_data.get("distance"),
            confidence=match_data.get("confidence")
        )
        matches.append(match)
    
    return VectorSearchResult(
        matches=matches,
        total_matches=len(matches),
        search_id=search_id,
        search_time=search_time,
        provider_name=provider_name,
        index_name=index_name,
        **kwargs
    )
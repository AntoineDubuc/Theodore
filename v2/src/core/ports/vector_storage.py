"""
Vector storage port interface for Theodore.

This module defines the contract for vector storage providers,
supporting CRUD operations, similarity search, and index management.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from src.core.domain.value_objects.vector_config import (
    VectorConfig, SearchConfig, SimilarityMetric
)
from src.core.domain.value_objects.vector_result import (
    VectorRecord, VectorSearchResult, VectorOperationResult, SearchMatch, IndexInfo
)
from src.core.ports.progress import ProgressTracker


# Type aliases for cleaner signatures
from typing import Callable
ProgressCallback = Callable[[str, float, Optional[str]], None]
VectorId = str
Vector = List[float]
MetadataFilter = Dict[str, Any]


class VectorStorageException(Exception):
    """Base exception for all vector storage errors"""
    pass


class VectorIndexException(VectorStorageException):
    """Raised when vector index operations fail"""
    
    def __init__(self, index_name: str, operation: str, message: str):
        self.index_name = index_name
        self.operation = operation
        super().__init__(f"Index '{index_name}' {operation} failed: {message}")


class VectorNotFoundException(VectorStorageException):
    """Raised when requested vector is not found"""
    
    def __init__(self, vector_id: str, index_name: str = None):
        self.vector_id = vector_id
        self.index_name = index_name
        message = f"Vector '{vector_id}' not found"
        if index_name:
            message += f" in index '{index_name}'"
        super().__init__(message)


class VectorDimensionMismatchException(VectorStorageException):
    """Raised when vector dimensions don't match index"""
    
    def __init__(self, expected: int, actual: int, index_name: str = None):
        self.expected = expected
        self.actual = actual
        self.index_name = index_name
        message = f"Vector dimension mismatch: expected {expected}, got {actual}"
        if index_name:
            message += f" for index '{index_name}'"
        super().__init__(message)


class VectorQuotaExceededException(VectorStorageException):
    """Raised when vector storage quota is exceeded"""
    
    def __init__(self, quota_type: str, current: int, limit: int):
        self.quota_type = quota_type
        self.current = current
        self.limit = limit
        super().__init__(f"Vector quota exceeded: {current}/{limit} {quota_type}")


class InvalidVectorFilterException(VectorStorageException):
    """Raised when vector filter is invalid"""
    
    def __init__(self, filter_expr: str, reason: str):
        self.filter_expr = filter_expr
        self.reason = reason
        super().__init__(f"Invalid vector filter '{filter_expr}': {reason}")


class VectorStorage(ABC):
    """
    Port interface for vector storage providers.
    
    This interface defines the contract for all vector storage adapters,
    supporting CRUD operations, similarity search, and index management.
    """
    
    # Index Management Methods
    
    @abstractmethod
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = SimilarityMetric.COSINE,
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        """
        Create a new vector index.
        
        Args:
            index_name: Name of the index to create
            dimensions: Vector dimensionality 
            metric: Distance metric (cosine, euclidean, dot_product)
            metadata_config: Configuration for metadata fields
            **kwargs: Additional provider-specific options
            
        Returns:
            VectorOperationResult with creation status
            
        Raises:
            VectorIndexException: If index creation fails
            VectorStorageException: For other storage errors
        """
        pass
    
    @abstractmethod
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """
        Delete a vector index and all its data.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            VectorOperationResult with deletion status
            
        Raises:
            VectorIndexException: If index deletion fails
        """
        pass
    
    @abstractmethod
    async def list_indexes(self) -> List[str]:
        """
        List all available vector indexes.
        
        Returns:
            List of index names
            
        Raises:
            VectorStorageException: If listing fails
        """
        pass
    
    @abstractmethod
    async def get_index_stats(self, index_name: str) -> IndexInfo:
        """
        Get statistics for a vector index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            IndexInfo with detailed index information
            
        Raises:
            VectorIndexException: If index doesn't exist or stats unavailable
        """
        pass
    
    @abstractmethod
    async def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index to check
            
        Returns:
            True if index exists, False otherwise
        """
        pass
    
    # Vector CRUD Operations
    
    @abstractmethod
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        vector: Vector,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """
        Insert or update a single vector.
        
        Args:
            index_name: Name of the target index
            vector_id: Unique identifier for the vector
            vector: Vector values as list of floats
            metadata: Optional metadata for the vector
            namespace: Optional namespace for the vector
            
        Returns:
            VectorOperationResult with operation status
            
        Raises:
            VectorIndexException: If index doesn't exist
            VectorDimensionMismatchException: If vector dimensions don't match
            VectorStorageException: For other storage errors
        """
        pass
    
    @abstractmethod
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[Dict[str, Any]]]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """
        Insert or update multiple vectors efficiently.
        
        Args:
            index_name: Name of the target index
            vectors: List of (vector_id, vector, metadata) tuples
            namespace: Optional namespace for vectors
            batch_size: Number of vectors per batch
            progress_callback: Optional callback for progress updates
            
        Returns:
            VectorOperationResult with batch operation status
            
        Raises:
            Same exceptions as upsert_vector
        """
        pass
    
    @abstractmethod
    async def get_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> tuple[Optional[Vector], Optional[Dict[str, Any]]]:
        """
        Retrieve a single vector by ID.
        
        Args:
            index_name: Name of the source index
            vector_id: Unique identifier for the vector
            namespace: Optional namespace to search in
            include_values: Whether to include vector values
            include_metadata: Whether to include metadata
            
        Returns:
            Tuple of (vector_values, metadata) - None if not found
            
        Raises:
            VectorIndexException: If index doesn't exist
            VectorStorageException: For other storage errors
        """
        pass
    
    @abstractmethod
    async def get_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Dict[VectorId, tuple[Optional[Vector], Optional[Dict[str, Any]]]]:
        """
        Retrieve multiple vectors by ID efficiently.
        
        Args:
            index_name: Name of the source index
            vector_ids: List of vector identifiers
            namespace: Optional namespace to search in
            include_values: Whether to include vector values
            include_metadata: Whether to include metadata
            
        Returns:
            Dictionary mapping vector_id to (vector_values, metadata)
            
        Raises:
            Same exceptions as get_vector
        """
        pass
    
    @abstractmethod
    async def delete_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """
        Delete a single vector by ID.
        
        Args:
            index_name: Name of the source index
            vector_id: Unique identifier for the vector
            namespace: Optional namespace to delete from
            
        Returns:
            VectorOperationResult with deletion status
            
        Raises:
            VectorIndexException: If index doesn't exist
            VectorStorageException: For other storage errors
        """
        pass
    
    @abstractmethod
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """
        Delete multiple vectors efficiently.
        
        Args:
            index_name: Name of the source index
            vector_ids: List of vector identifiers to delete
            namespace: Optional namespace to delete from
            batch_size: Number of vectors per batch
            
        Returns:
            VectorOperationResult with batch deletion status
            
        Raises:
            Same exceptions as delete_vector
        """
        pass
    
    @abstractmethod
    async def delete_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """
        Delete vectors matching metadata filter.
        
        Args:
            index_name: Name of the source index
            metadata_filter: Filter conditions for deletion
            namespace: Optional namespace to delete from
            
        Returns:
            VectorOperationResult with deletion status
            
        Raises:
            InvalidVectorFilterException: If filter is invalid
            VectorIndexException: If index doesn't exist
        """
        pass
    
    # Vector Search Operations
    
    @abstractmethod
    async def search_similar(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """
        Search for similar vectors using a query vector.
        
        Args:
            index_name: Name of the index to search
            query_vector: Vector to find similarities for
            config: Search configuration
            namespace: Optional namespace to search in
            
        Returns:
            VectorSearchResult with matching vectors
            
        Raises:
            VectorIndexException: If index doesn't exist
            VectorDimensionMismatchException: If query vector dimensions don't match
            InvalidVectorFilterException: If metadata filter is invalid
        """
        pass
    
    @abstractmethod
    async def search_by_id(
        self,
        index_name: str,
        vector_id: VectorId,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """
        Search for vectors similar to a stored vector.
        
        Args:
            index_name: Name of the index to search
            vector_id: ID of vector to find similarities for
            config: Search configuration
            namespace: Optional namespace to search in
            
        Returns:
            VectorSearchResult with matching vectors
            
        Raises:
            VectorNotFoundException: If source vector doesn't exist
            Same exceptions as search_similar
        """
        pass
    
    @abstractmethod
    async def search_by_metadata(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        limit: int = 100,
        offset: int = 0,
        namespace: Optional[str] = None
    ) -> List[tuple[VectorId, Dict[str, Any]]]:
        """
        Search vectors by metadata only (no similarity).
        
        Args:
            index_name: Name of the index to search
            metadata_filter: Filter conditions
            limit: Maximum number of results
            offset: Number of results to skip
            namespace: Optional namespace to search in
            
        Returns:
            List of (vector_id, metadata) tuples
            
        Raises:
            InvalidVectorFilterException: If filter is invalid
            VectorIndexException: If index doesn't exist
        """
        pass
    
    # Advanced Operations
    
    @abstractmethod
    async def get_similar_entities(
        self,
        index_name: str,
        entity_id: str,
        entity_type: str,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """
        Find entities similar to a given entity.
        
        Args:
            index_name: Name of the index to search
            entity_id: ID of the entity to find similarities for
            entity_type: Type of entity being searched
            config: Search configuration
            namespace: Optional namespace to search in
            
        Returns:
            VectorSearchResult with similar entities
        """
        pass
    
    @abstractmethod
    async def count_vectors(
        self,
        index_name: str,
        metadata_filter: Optional[MetadataFilter] = None,
        namespace: Optional[str] = None
    ) -> int:
        """
        Count vectors matching optional filter.
        
        Args:
            index_name: Name of the index
            metadata_filter: Optional filter conditions
            namespace: Optional namespace to count in
            
        Returns:
            Number of matching vectors
        """
        pass
    
    @abstractmethod
    async def update_metadata(
        self,
        index_name: str,
        vector_id: VectorId,
        metadata: Dict[str, Any],
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """
        Update metadata for an existing vector.
        
        Args:
            index_name: Name of the index
            vector_id: ID of vector to update
            metadata: New metadata
            namespace: Optional namespace
            
        Returns:
            VectorOperationResult with update status
        """
        pass
    
    # Context Manager and Lifecycle
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
    
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        pass


class BatchVectorStorage(VectorStorage):
    """
    Extended interface for advanced batch operations.
    
    Provides methods for efficient large-scale vector operations
    with chunking and parallel processing.
    """
    
    @abstractmethod
    async def upsert_vectors_chunked(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[Dict[str, Any]]]],
        chunk_size: Optional[int] = None,
        max_parallel: int = 5,
        namespace: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """
        Upsert vectors with automatic chunking for large batches.
        
        Args:
            index_name: Name of the target index
            vectors: List of (vector_id, vector, metadata) tuples
            chunk_size: Size of each chunk (auto-calculated if None)
            max_parallel: Maximum parallel chunk processing
            namespace: Optional namespace
            progress_callback: Optional callback for progress updates
            
        Returns:
            VectorOperationResult with batch operation status
        """
        pass
    
    @abstractmethod
    async def search_multiple_vectors(
        self,
        index_name: str,
        query_vectors: List[Vector],
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar vectors using multiple query vectors.
        
        Args:
            index_name: Name of the index to search
            query_vectors: List of vectors to find similarities for
            config: Search configuration  
            namespace: Optional namespace to search in
            
        Returns:
            List of VectorSearchResult objects (one per query vector)
        """
        pass
    
    @abstractmethod
    async def bulk_update_metadata(
        self,
        index_name: str,
        updates: List[tuple[VectorId, Dict[str, Any]]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """
        Update metadata for multiple vectors efficiently.
        
        Args:
            index_name: Name of the index
            updates: List of (vector_id, metadata) tuples
            namespace: Optional namespace
            batch_size: Number of updates per batch
            
        Returns:
            VectorOperationResult with bulk update status
        """
        pass


class StreamingVectorStorage(VectorStorage):
    """
    Extended interface for streaming vector operations.
    
    Provides methods for real-time vector processing with
    streaming results and live updates.
    """
    
    @abstractmethod
    async def stream_search_results(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, float, Optional[Dict[str, Any]]]]:
        """
        Stream search results as they become available.
        
        Args:
            index_name: Name of the index to search
            query_vector: Vector to find similarities for
            config: Search configuration
            namespace: Optional namespace to search in
            
        Yields:
            Tuples of (vector_id, similarity_score, metadata)
        """
        pass
    
    @abstractmethod
    async def stream_vectors_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, Vector, Dict[str, Any]]]:
        """
        Stream vectors matching metadata filter.
        
        Args:
            index_name: Name of the index
            metadata_filter: Filter conditions
            namespace: Optional namespace
            
        Yields:
            Tuples of (vector_id, vector, metadata)
        """
        pass


class CacheableVectorStorage(VectorStorage):
    """
    Extended interface with caching capabilities.
    
    Provides methods for caching search results and vectors
    to improve performance.
    """
    
    @abstractmethod
    async def search_with_cache(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        cache_ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """
        Search with caching of results.
        
        Args:
            index_name: Name of the index to search
            query_vector: Vector to find similarities for
            config: Search configuration
            cache_ttl: Cache time-to-live in seconds
            namespace: Optional namespace to search in
            
        Returns:
            VectorSearchResult (may be from cache)
        """
        pass
    
    @abstractmethod
    async def clear_search_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached search results.
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            Number of cache entries cleared
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        pass


# Factory interface for creating vector storage providers
class VectorStorageFactory(ABC):
    """
    Factory for creating vector storage provider instances.
    
    Allows for flexible provider creation with different
    configurations and implementations.
    """
    
    @abstractmethod
    def create_storage(
        self,
        storage_type: str = "default",
        **kwargs
    ) -> VectorStorage:
        """
        Create a vector storage provider instance.
        
        Args:
            storage_type: Type of storage to create
                         Common types: "pinecone", "weaviate", "chroma", "inmemory"
            **kwargs: Additional configuration passed to storage constructor
            
        Returns:
            VectorStorage implementation
            
        Raises:
            ValueError: If storage_type is not supported
            VectorStorageException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_available_storage_types(self) -> List[str]:
        """
        Get list of available storage types.
        
        Returns:
            List of storage type names that can be created
        """
        pass
    
    @abstractmethod
    def get_storage_info(self, storage_type: str) -> Dict[str, Any]:
        """
        Get information about a specific storage type.
        
        Args:
            storage_type: Type of storage to get info for
            
        Returns:
            Dictionary with storage information
        """
        pass


# Constants for vector storage features
class VectorStorageFeatures:
    """Constants for common vector storage features"""
    
    SIMILARITY_SEARCH = "similarity_search"
    METADATA_FILTERING = "metadata_filtering"
    BATCH_OPERATIONS = "batch_operations"
    STREAMING = "streaming"
    CACHING = "caching"
    NAMESPACES = "namespaces"
    INDEX_MANAGEMENT = "index_management"
    REAL_TIME_UPDATES = "real_time_updates"
    BACKUP_RESTORE = "backup_restore"
    MONITORING = "monitoring"


# Utility functions for vector operations
def validate_vector_dimensions(vector: Vector, expected_dims: int) -> bool:
    """Validate that vector has expected dimensions."""
    return len(vector) == expected_dims


def normalize_vector(vector: Vector) -> Vector:
    """Normalize vector to unit length."""
    magnitude = sum(x * x for x in vector) ** 0.5
    if magnitude == 0:
        return vector
    return [x / magnitude for x in vector]


def calculate_vector_magnitude(vector: Vector) -> float:
    """Calculate magnitude (length) of vector."""
    return sum(x * x for x in vector) ** 0.5


def vectors_are_similar(vector1: Vector, vector2: Vector, threshold: float = 1e-6) -> bool:
    """Check if two vectors are approximately equal."""
    if len(vector1) != len(vector2):
        return False
    return all(abs(a - b) < threshold for a, b in zip(vector1, vector2))
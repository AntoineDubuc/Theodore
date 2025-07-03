"""
Unit tests for mock vector storage implementation.

Tests all aspects of the VectorStorage interface using comprehensive mock
implementations to validate interface compliance and behavior.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import Mock
from datetime import datetime, timedelta

from src.core.ports.vector_storage import (
    VectorStorage, VectorStorageException, VectorIndexException,
    VectorNotFoundException, VectorDimensionMismatchException,
    VectorQuotaExceededException, InvalidVectorFilterException,
    validate_vector_dimensions, normalize_vector, calculate_vector_magnitude,
    vectors_are_similar, VectorStorageFeatures, DistanceMetric
)
from src.core.domain.value_objects.vector_search_result import (
    VectorSearchConfig, VectorSearchResult, VectorSearchMatch,
    VectorOperationResult, IndexStats, VectorMetadata
)
from src.core.domain.value_objects.vector_metadata import (
    UnifiedVectorMetadata, VectorEntityType, VectorEmbeddingMetadata,
    CompanyVectorMetadata, VectorQuality
)
from src.core.ports.progress import ProgressTracker


class MockVectorStorage(VectorStorage):
    """
    Mock vector storage implementation for testing.
    
    Provides complete in-memory vector storage with realistic
    behavior simulation and comprehensive feature support.
    """
    
    def __init__(
        self,
        simulate_latency: bool = False,
        simulate_errors: bool = False,
        error_rate: float = 0.05,
        max_vectors_per_index: int = 10000
    ):
        self.simulate_latency = simulate_latency
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        self.max_vectors_per_index = max_vectors_per_index
        
        # In-memory storage
        self._indexes: Dict[str, Dict[str, Any]] = {}
        self._vectors: Dict[str, Dict[str, Dict[str, Any]]] = {}  # index -> namespace -> vector_id -> data
        self._operation_count = 0
        self._search_count = 0
        self._error_count = 0
        
        # Track if we're in context manager
        self._in_context = False
        
        # Default index settings
        self._default_dimensions = 1536
        self._default_metric = DistanceMetric.COSINE
    
    # Index Management Methods
    
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = DistanceMetric.COSINE,
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        """Create a new vector index"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        self._operation_count += 1
        
        if self.simulate_latency:
            await asyncio.sleep(0.1)  # 100ms latency
        
        if index_name in self._indexes:
            return VectorOperationResult.error_result(
                "create_index",
                f"Index '{index_name}' already exists"
            )
        
        # Create index configuration
        self._indexes[index_name] = {
            "dimensions": dimensions,
            "metric": metric,
            "metadata_config": metadata_config or {},
            "created_at": datetime.utcnow(),
            "vector_count": 0,
            **kwargs
        }
        
        # Initialize vector storage for index
        self._vectors[index_name] = {"": {}}  # Default namespace
        
        return VectorOperationResult.success_result(
            "create_index",
            1,
            f"Index '{index_name}' created successfully",
            {"index_name": index_name, "dimensions": dimensions}
        )
    
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """Delete a vector index and all its data"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        self._operation_count += 1
        
        if self.simulate_latency:
            await asyncio.sleep(0.05)
        
        if index_name not in self._indexes:
            return VectorOperationResult.error_result(
                "delete_index",
                f"Index '{index_name}' does not exist"
            )
        
        # Count vectors before deletion
        vector_count = sum(
            len(namespace_vectors) 
            for namespace_vectors in self._vectors.get(index_name, {}).values()
        )
        
        # Delete index and all its vectors
        del self._indexes[index_name]
        if index_name in self._vectors:
            del self._vectors[index_name]
        
        return VectorOperationResult.success_result(
            "delete_index",
            vector_count,
            f"Index '{index_name}' and {vector_count} vectors deleted",
            {"index_name": index_name, "vectors_deleted": vector_count}
        )
    
    async def list_indexes(self) -> List[str]:
        """List all available vector indexes"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if self.simulate_latency:
            await asyncio.sleep(0.01)
        
        return list(self._indexes.keys())
    
    async def get_index_stats(self, index_name: str) -> IndexStats:
        """Get statistics for a vector index"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "get_stats", "Index does not exist")
        
        if self.simulate_latency:
            await asyncio.sleep(0.02)
        
        index_config = self._indexes[index_name]
        index_vectors = self._vectors.get(index_name, {})
        
        # Calculate statistics
        total_vectors = sum(len(namespace_vectors) for namespace_vectors in index_vectors.values())
        namespaces = list(index_vectors.keys())
        
        # Estimate sizes
        avg_vector_size = index_config["dimensions"] * 4  # 4 bytes per float
        size_bytes = total_vectors * avg_vector_size
        
        return IndexStats(
            name=index_name,
            total_vectors=total_vectors,
            dimensions=index_config["dimensions"],
            namespaces=namespaces,
            size_bytes=size_bytes,
            avg_vector_size=avg_vector_size,
            avg_search_time_ms=50.0 if self.simulate_latency else 5.0,
            total_searches=self._search_count,
            created_at=index_config["created_at"],
            last_updated=datetime.utcnow(),
            metadata={"metric": index_config["metric"]}
        )
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        return index_name in self._indexes
    
    # Vector CRUD Operations
    
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: str,
        vector: List[float],
        metadata: Optional[UnifiedVectorMetadata] = None,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Insert or update a single vector"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        self._operation_count += 1
        
        if self.simulate_latency:
            await asyncio.sleep(0.01)
        
        # Simulate errors occasionally
        if self.simulate_errors and self._operation_count % 50 == 0:
            self._error_count += 1
            raise VectorStorageException("Simulated storage error")
        
        # Validate index exists
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "upsert", "Index does not exist")
        
        # Validate vector dimensions
        expected_dims = self._indexes[index_name]["dimensions"]
        if len(vector) != expected_dims:
            raise VectorDimensionMismatchException(expected_dims, len(vector), index_name)
        
        # Check quota
        current_count = sum(
            len(ns_vectors) for ns_vectors in self._vectors[index_name].values()
        )
        if current_count >= self.max_vectors_per_index:
            raise VectorQuotaExceededException("vectors", current_count, self.max_vectors_per_index)
        
        # Normalize namespace
        namespace = namespace or ""
        
        # Ensure namespace exists
        if namespace not in self._vectors[index_name]:
            self._vectors[index_name][namespace] = {}
        
        # Store vector data
        is_update = vector_id in self._vectors[index_name][namespace]
        existing_data = self._vectors[index_name][namespace].get(vector_id, {})
        self._vectors[index_name][namespace][vector_id] = {
            "vector": vector.copy(),
            "metadata": metadata,
            "created_at": existing_data.get("created_at", datetime.utcnow()),
            "updated_at": datetime.utcnow()
        }
        
        operation = "update" if is_update else "insert"
        return VectorOperationResult.success_result(
            f"upsert_{operation}",
            1,
            f"Vector '{vector_id}' {operation}d successfully",
            {"vector_id": vector_id, "namespace": namespace}
        )
    
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[Tuple[str, List[float], Optional[UnifiedVectorMetadata]]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None
    ) -> VectorOperationResult:
        """Insert or update multiple vectors efficiently"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if progress_callback:
            progress_callback(f"Starting batch upsert of {len(vectors)} vectors", 0.0, "Initializing")
        
        success_count = 0
        error_count = 0
        
        # Process in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            for j, (vector_id, vector, metadata) in enumerate(batch):
                try:
                    await self.upsert_vector(index_name, vector_id, vector, metadata, namespace)
                    success_count += 1
                except Exception:
                    error_count += 1
                
                if progress_callback:
                    overall_progress = (i + j + 1) / len(vectors)
                    progress_callback(
                        f"Processing vector {i + j + 1}/{len(vectors)}",
                        overall_progress,
                        f"Batch {i // batch_size + 1}"
                    )
        
        if progress_callback:
            progress_callback("Batch upsert complete", 1.0, f"{success_count} successful, {error_count} errors")
        
        return VectorOperationResult.success_result(
            "batch_upsert",
            success_count,
            f"Batch upsert completed: {success_count} successful, {error_count} errors",
            {"success_count": success_count, "error_count": error_count}
        )
    
    async def get_vector(
        self,
        index_name: str,
        vector_id: str,
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Tuple[Optional[List[float]], Optional[UnifiedVectorMetadata]]:
        """Retrieve a single vector by ID"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if self.simulate_latency:
            await asyncio.sleep(0.005)
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "get", "Index does not exist")
        
        namespace = namespace or ""
        
        if (namespace not in self._vectors.get(index_name, {}) or 
            vector_id not in self._vectors[index_name][namespace]):
            return None, None
        
        vector_data = self._vectors[index_name][namespace][vector_id]
        
        values = vector_data["vector"].copy() if include_values else None
        metadata = vector_data["metadata"] if include_metadata else None
        
        return values, metadata
    
    async def get_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[str],
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Dict[str, Tuple[Optional[List[float]], Optional[UnifiedVectorMetadata]]]:
        """Retrieve multiple vectors by ID efficiently"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if self.simulate_latency:
            await asyncio.sleep(0.01 * len(vector_ids))
        
        results = {}
        for vector_id in vector_ids:
            values, metadata = await self.get_vector(
                index_name, vector_id, namespace, include_values, include_metadata
            )
            results[vector_id] = (values, metadata)
        
        return results
    
    async def delete_vector(
        self,
        index_name: str,
        vector_id: str,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete a single vector by ID"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        self._operation_count += 1
        
        if self.simulate_latency:
            await asyncio.sleep(0.01)
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "delete", "Index does not exist")
        
        namespace = namespace or ""
        
        if (namespace not in self._vectors.get(index_name, {}) or 
            vector_id not in self._vectors[index_name][namespace]):
            raise VectorNotFoundException(vector_id, index_name)
        
        del self._vectors[index_name][namespace][vector_id]
        
        return VectorOperationResult.success_result(
            "delete",
            1,
            f"Vector '{vector_id}' deleted successfully",
            {"vector_id": vector_id, "namespace": namespace}
        )
    
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[str],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Delete multiple vectors efficiently"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        success_count = 0
        error_count = 0
        
        for vector_id in vector_ids:
            try:
                await self.delete_vector(index_name, vector_id, namespace)
                success_count += 1
            except VectorNotFoundException:
                error_count += 1
        
        return VectorOperationResult.success_result(
            "batch_delete",
            success_count,
            f"Batch delete completed: {success_count} successful, {error_count} not found",
            {"success_count": success_count, "error_count": error_count}
        )
    
    async def delete_by_filter(
        self,
        index_name: str,
        metadata_filter: Dict[str, Any],
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete vectors matching metadata filter"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        # Simple filter implementation - match exact values
        namespace = namespace or ""
        deleted_count = 0
        
        if index_name in self._vectors and namespace in self._vectors[index_name]:
            to_delete = []
            
            for vector_id, vector_data in self._vectors[index_name][namespace].items():
                metadata = vector_data.get("metadata")
                if metadata and self._matches_filter(metadata, metadata_filter):
                    to_delete.append(vector_id)
            
            for vector_id in to_delete:
                del self._vectors[index_name][namespace][vector_id]
                deleted_count += 1
        
        return VectorOperationResult.success_result(
            "delete_by_filter",
            deleted_count,
            f"Deleted {deleted_count} vectors matching filter",
            {"deleted_count": deleted_count}
        )
    
    # Vector Search Operations
    
    async def search_similar(
        self,
        index_name: str,
        query_vector: List[float],
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for similar vectors using a query vector"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        self._search_count += 1
        start_time = time.time()
        
        if self.simulate_latency:
            await asyncio.sleep(0.05)
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "search", "Index does not exist")
        
        # Validate query vector dimensions
        expected_dims = self._indexes[index_name]["dimensions"]
        if len(query_vector) != expected_dims:
            raise VectorDimensionMismatchException(expected_dims, len(query_vector), index_name)
        
        namespace = namespace or ""
        
        if namespace not in self._vectors.get(index_name, {}):
            # Return empty result for non-existent namespace
            result = VectorSearchResult(
                query_vector=query_vector if config.include_values else None,
                config=config,
                matches=[],
                total_matches=0,
                search_time_ms=(time.time() - start_time) * 1000,
                index_name=index_name,
                namespace=namespace
            )
            result.model_post_init(None)
            return result
        
        # Calculate similarities
        matches = []
        for vector_id, vector_data in self._vectors[index_name][namespace].items():
            stored_vector = vector_data["vector"]
            metadata = vector_data["metadata"]
            
            # Apply metadata filter if provided
            if config.metadata_filter and not self._matches_filter(metadata, config.metadata_filter):
                continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(
                query_vector, stored_vector, config.distance_metric
            )
            
            # Apply similarity threshold
            if config.similarity_threshold and similarity < config.similarity_threshold:
                continue
            
            # Create match
            match = VectorSearchMatch(
                vector_id=vector_id,
                entity_id=metadata.entity_id if metadata else vector_id,
                similarity_score=similarity,
                distance=1.0 - similarity,  # Simple distance calculation
                metadata=self._create_vector_metadata(metadata) if config.include_metadata and metadata else None,
                vector_values=stored_vector.copy() if config.include_values else None,
                rank=1,  # Temporary rank, will be set after sorting
                namespace=namespace
            )
            matches.append(match)
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        matches = matches[:config.top_k]
        
        # Set ranks
        for i, match in enumerate(matches):
            match.rank = i + 1
        
        search_time_ms = (time.time() - start_time) * 1000
        
        result = VectorSearchResult(
            query_vector=query_vector if config.include_values else None,
            config=config,
            matches=matches,
            total_matches=len(matches),
            search_time_ms=search_time_ms,
            index_name=index_name,
            namespace=namespace
        )
        
        # Calculate derived metrics
        result.model_post_init(None)
        
        return result
    
    async def search_by_id(
        self,
        index_name: str,
        vector_id: str,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for vectors similar to a stored vector"""
        # Get the stored vector
        stored_vector, _ = await self.get_vector(
            index_name, vector_id, namespace, include_values=True
        )
        
        if stored_vector is None:
            raise VectorNotFoundException(vector_id, index_name)
        
        # Use the stored vector as query
        return await self.search_similar(index_name, stored_vector, config, namespace)
    
    async def search_by_metadata(
        self,
        index_name: str,
        metadata_filter: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        namespace: Optional[str] = None
    ) -> List[Tuple[str, UnifiedVectorMetadata]]:
        """Search vectors by metadata only (no similarity)"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "search_metadata", "Index does not exist")
        
        namespace = namespace or ""
        results = []
        
        if namespace in self._vectors.get(index_name, {}):
            for vector_id, vector_data in self._vectors[index_name][namespace].items():
                metadata = vector_data.get("metadata")
                if metadata and self._matches_filter(metadata, metadata_filter):
                    results.append((vector_id, metadata))
        
        # Apply pagination
        return results[offset:offset + limit]
    
    # Advanced Operations
    
    async def get_similar_entities(
        self,
        index_name: str,
        entity_id: str,
        entity_type: VectorEntityType,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Find entities similar to a given entity"""
        # Find vector for the entity
        namespace = namespace or ""
        
        if index_name not in self._vectors or namespace not in self._vectors[index_name]:
            raise VectorNotFoundException(entity_id, index_name)
        
        # Search for vector with matching entity_id
        entity_vector = None
        for vector_id, vector_data in self._vectors[index_name][namespace].items():
            metadata = vector_data.get("metadata")
            if metadata and metadata.entity_id == entity_id and metadata.entity_type == entity_type:
                entity_vector = vector_data["vector"]
                break
        
        if entity_vector is None:
            raise VectorNotFoundException(entity_id, index_name)
        
        # Add entity type filter to search config
        enhanced_config = config.copy()
        if enhanced_config.metadata_filter is None:
            enhanced_config.metadata_filter = {}
        enhanced_config.metadata_filter["entity_type"] = entity_type.value
        
        return await self.search_similar(index_name, entity_vector, enhanced_config, namespace)
    
    async def count_vectors(
        self,
        index_name: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> int:
        """Count vectors matching optional filter"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        if index_name not in self._indexes:
            raise VectorIndexException(index_name, "count", "Index does not exist")
        
        namespace = namespace or ""
        count = 0
        
        if namespace in self._vectors.get(index_name, {}):
            for vector_data in self._vectors[index_name][namespace].values():
                metadata = vector_data.get("metadata")
                if metadata_filter is None or self._matches_filter(metadata, metadata_filter):
                    count += 1
        
        return count
    
    async def update_metadata(
        self,
        index_name: str,
        vector_id: str,
        metadata: UnifiedVectorMetadata,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Update metadata for an existing vector"""
        if not self._in_context:
            raise VectorStorageException("Storage must be used as async context manager")
        
        namespace = namespace or ""
        
        if (index_name not in self._vectors or 
            namespace not in self._vectors[index_name] or
            vector_id not in self._vectors[index_name][namespace]):
            raise VectorNotFoundException(vector_id, index_name)
        
        self._vectors[index_name][namespace][vector_id]["metadata"] = metadata
        self._vectors[index_name][namespace][vector_id]["updated_at"] = datetime.utcnow()
        
        return VectorOperationResult.success_result(
            "update_metadata",
            1,
            f"Metadata updated for vector '{vector_id}'",
            {"vector_id": vector_id}
        )
    
    # Context Manager and Lifecycle
    
    async def close(self) -> None:
        """Clean up resources and close connections"""
        self._operation_count = 0
        self._search_count = 0
        self._error_count = 0
        self._indexes.clear()
        self._vectors.clear()
        self._in_context = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._in_context = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        await self.close()
    
    # Helper methods
    
    def _matches_filter(self, metadata: Optional[UnifiedVectorMetadata], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter conditions"""
        if not metadata:
            return False
        
        for key, value in filter_dict.items():
            if key == "entity_type":
                if metadata.entity_type.value != value:
                    return False
            elif key == "entity_id":
                if metadata.entity_id != value:
                    return False
            elif hasattr(metadata, key):
                if getattr(metadata, key) != value:
                    return False
            elif key in metadata.custom_fields:
                if metadata.custom_fields[key] != value:
                    return False
            else:
                return False
        
        return True
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float], metric: str) -> float:
        """Calculate similarity between two vectors"""
        if metric == DistanceMetric.COSINE:
            return self._cosine_similarity(vec1, vec2)
        elif metric == DistanceMetric.EUCLIDEAN:
            distance = self._euclidean_distance(vec1, vec2)
            return 1.0 / (1.0 + distance)  # Convert distance to similarity
        elif metric == DistanceMetric.DOT_PRODUCT:
            return max(0.0, min(1.0, sum(a * b for a, b in zip(vec1, vec2))))
        else:
            return self._cosine_similarity(vec1, vec2)  # Default to cosine
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return max(0.0, min(1.0, dot_product / (norm1 * norm2)))
    
    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance"""
        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5
    
    def _create_vector_metadata(self, metadata: UnifiedVectorMetadata) -> VectorMetadata:
        """Create VectorMetadata from UnifiedVectorMetadata"""
        return VectorMetadata(
            entity_id=metadata.entity_id,
            entity_type=metadata.entity_type.value,
            content_hash=None,  # Could derive from metadata
            content_length=None,
            vector_dimensions=metadata.embedding.dimensions,
            embedding_model=metadata.embedding.model_name,
            embedding_provider=metadata.embedding.model_provider,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            confidence_score=metadata.embedding.confidence_score,
            custom_fields=metadata.custom_fields
        )


class TestMockVectorStorage:
    """Test suite for MockVectorStorage implementation"""
    
    @pytest_asyncio.fixture
    async def storage(self):
        """Create a mock vector storage for testing"""
        storage = MockVectorStorage(
            simulate_latency=False,
            simulate_errors=False
        )
        async with storage:
            yield storage
    
    @pytest.fixture
    def basic_metadata(self):
        """Basic unified vector metadata"""
        return UnifiedVectorMetadata(
            entity_id="test_entity_1",
            entity_type=VectorEntityType.COMPANY,
            vector_id="vector_1",
            embedding=VectorEmbeddingMetadata(
                model_name="test-model",
                model_provider="test-provider",
                dimensions=1536
            ),
            index_name="test_index"
        )
    
    @pytest.fixture
    def search_config(self):
        """Basic search configuration"""
        return VectorSearchConfig(
            top_k=10,
            similarity_threshold=0.5,
            distance_metric="cosine",
            include_metadata=True
        )
    
    # Index Management Tests
    
    @pytest.mark.asyncio
    async def test_create_index(self, storage):
        """Test index creation"""
        result = await storage.create_index("test_index", 1536, "cosine")
        
        assert result.success
        assert result.operation == "create_index"
        assert result.affected_count == 1
        assert "test_index" in result.message
        
        # Verify index exists
        assert await storage.index_exists("test_index")
        indexes = await storage.list_indexes()
        assert "test_index" in indexes
    
    @pytest.mark.asyncio
    async def test_create_duplicate_index(self, storage):
        """Test creating duplicate index fails"""
        await storage.create_index("test_index", 1536)
        
        result = await storage.create_index("test_index", 1536)
        assert not result.success
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_delete_index(self, storage):
        """Test index deletion"""
        await storage.create_index("test_index", 1536)
        
        # Add some vectors
        test_vector = [0.1] * 1536
        await storage.upsert_vector("test_index", "vec1", test_vector)
        
        result = await storage.delete_index("test_index")
        
        assert result.success
        assert result.operation == "delete_index"
        assert result.affected_count == 1  # 1 vector deleted
        
        # Verify index no longer exists
        assert not await storage.index_exists("test_index")
    
    @pytest.mark.asyncio
    async def test_index_stats(self, storage):
        """Test getting index statistics"""
        await storage.create_index("test_index", 1536, "cosine")
        
        stats = await storage.get_index_stats("test_index")
        
        assert stats.name == "test_index"
        assert stats.total_vectors == 0
        assert stats.dimensions == 1536
        assert stats.namespaces == [""]
        assert stats.size_bytes == 0
        assert stats.is_empty
    
    # Vector CRUD Tests
    
    @pytest.mark.asyncio
    async def test_upsert_vector(self, storage, basic_metadata):
        """Test single vector upsert"""
        await storage.create_index("test_index", 1536)
        
        test_vector = [0.1] * 1536
        result = await storage.upsert_vector(
            "test_index", "vec1", test_vector, basic_metadata
        )
        
        assert result.success
        assert result.operation == "upsert_insert"
        assert result.affected_count == 1
    
    @pytest.mark.asyncio
    async def test_upsert_vector_update(self, storage, basic_metadata):
        """Test vector update"""
        await storage.create_index("test_index", 1536)
        
        test_vector = [0.1] * 1536
        
        # Insert first
        await storage.upsert_vector("test_index", "vec1", test_vector, basic_metadata)
        
        # Update with different vector
        updated_vector = [0.2] * 1536
        result = await storage.upsert_vector("test_index", "vec1", updated_vector, basic_metadata)
        
        assert result.success
        assert result.operation == "upsert_update"
    
    @pytest.mark.asyncio
    async def test_upsert_dimension_mismatch(self, storage):
        """Test dimension mismatch error"""
        await storage.create_index("test_index", 1536)
        
        wrong_vector = [0.1] * 512  # Wrong dimensions
        
        with pytest.raises(VectorDimensionMismatchException) as exc_info:
            await storage.upsert_vector("test_index", "vec1", wrong_vector)
        
        assert exc_info.value.expected == 1536
        assert exc_info.value.actual == 512
    
    @pytest.mark.asyncio
    async def test_get_vector(self, storage, basic_metadata):
        """Test vector retrieval"""
        await storage.create_index("test_index", 1536)
        
        test_vector = [0.1] * 1536
        await storage.upsert_vector("test_index", "vec1", test_vector, basic_metadata)
        
        # Get with values
        values, metadata = await storage.get_vector(
            "test_index", "vec1", include_values=True
        )
        
        assert values == test_vector
        assert metadata.entity_id == "test_entity_1"
        
        # Get without values
        values, metadata = await storage.get_vector(
            "test_index", "vec1", include_values=False
        )
        
        assert values is None
        assert metadata is not None
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_vector(self, storage):
        """Test retrieving non-existent vector"""
        await storage.create_index("test_index", 1536)
        
        values, metadata = await storage.get_vector("test_index", "nonexistent")
        
        assert values is None
        assert metadata is None
    
    @pytest.mark.asyncio
    async def test_delete_vector(self, storage, basic_metadata):
        """Test vector deletion"""
        await storage.create_index("test_index", 1536)
        
        test_vector = [0.1] * 1536
        await storage.upsert_vector("test_index", "vec1", test_vector, basic_metadata)
        
        # Verify exists
        values, _ = await storage.get_vector("test_index", "vec1", include_values=True)
        assert values is not None
        
        # Delete
        result = await storage.delete_vector("test_index", "vec1")
        assert result.success
        
        # Verify deleted
        values, _ = await storage.get_vector("test_index", "vec1")
        assert values is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_vector(self, storage):
        """Test deleting non-existent vector"""
        await storage.create_index("test_index", 1536)
        
        with pytest.raises(VectorNotFoundException) as exc_info:
            await storage.delete_vector("test_index", "nonexistent")
        
        assert exc_info.value.vector_id == "nonexistent"
    
    # Batch Operations Tests
    
    @pytest.mark.asyncio
    async def test_batch_upsert(self, storage, basic_metadata):
        """Test batch vector upsert"""
        await storage.create_index("test_index", 1536)
        
        vectors = [
            ("vec1", [0.1] * 1536, basic_metadata),
            ("vec2", [0.2] * 1536, basic_metadata),
            ("vec3", [0.3] * 1536, basic_metadata)
        ]
        
        result = await storage.upsert_vectors_batch("test_index", vectors)
        
        assert result.success
        assert result.affected_count == 3
        
        # Verify all vectors were stored
        for vector_id, _, _ in vectors:
            values, _ = await storage.get_vector("test_index", vector_id, include_values=True)
            assert values is not None
    
    @pytest.mark.asyncio
    async def test_batch_get(self, storage, basic_metadata):
        """Test batch vector retrieval"""
        await storage.create_index("test_index", 1536)
        
        # Insert vectors
        vectors = {
            "vec1": [0.1] * 1536,
            "vec2": [0.2] * 1536,
            "vec3": [0.3] * 1536
        }
        
        for vector_id, vector in vectors.items():
            await storage.upsert_vector("test_index", vector_id, vector, basic_metadata)
        
        # Batch get
        results = await storage.get_vectors_batch(
            "test_index", list(vectors.keys()), include_values=True
        )
        
        assert len(results) == 3
        for vector_id, vector in vectors.items():
            values, metadata = results[vector_id]
            assert values == vector
            assert metadata is not None
    
    @pytest.mark.asyncio
    async def test_batch_delete(self, storage, basic_metadata):
        """Test batch vector deletion"""
        await storage.create_index("test_index", 1536)
        
        # Insert vectors
        vector_ids = ["vec1", "vec2", "vec3"]
        for vector_id in vector_ids:
            await storage.upsert_vector("test_index", vector_id, [0.1] * 1536, basic_metadata)
        
        # Batch delete
        result = await storage.delete_vectors_batch("test_index", vector_ids)
        
        assert result.success
        assert result.affected_count == 3
        
        # Verify all deleted
        for vector_id in vector_ids:
            values, _ = await storage.get_vector("test_index", vector_id)
            assert values is None
    
    # Search Tests
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, storage, basic_metadata, search_config):
        """Test similarity search"""
        await storage.create_index("test_index", 1536)
        
        # Insert test vectors
        vectors = {
            "vec1": [1.0] + [0.0] * 1535,  # Point along first axis
            "vec2": [0.9] + [0.1] * 1535,  # Similar to vec1
            "vec3": [0.0] + [1.0] + [0.0] * 1534,  # Point along second axis
        }
        
        for vector_id, vector in vectors.items():
            await storage.upsert_vector("test_index", vector_id, vector, basic_metadata)
        
        # Search with vec1 as query
        query_vector = [1.0] + [0.0] * 1535
        result = await storage.search_similar("test_index", query_vector, search_config)
        
        assert result.total_matches > 0
        assert len(result.matches) <= search_config.top_k
        
        # First match should be most similar
        if result.matches:
            assert result.matches[0].similarity_score >= result.matches[-1].similarity_score
    
    @pytest.mark.asyncio
    async def test_search_by_id(self, storage, basic_metadata, search_config):
        """Test search by stored vector ID"""
        await storage.create_index("test_index", 1536)
        
        # Insert test vectors
        test_vector = [1.0] + [0.0] * 1535
        await storage.upsert_vector("test_index", "vec1", test_vector, basic_metadata)
        await storage.upsert_vector("test_index", "vec2", [0.9] + [0.1] * 1535, basic_metadata)
        
        # Search using vec1 as query
        result = await storage.search_by_id("test_index", "vec1", search_config)
        
        assert result.total_matches > 0
        # Should find at least vec1 itself
        assert any(match.vector_id == "vec1" for match in result.matches)
    
    @pytest.mark.asyncio
    async def test_search_nonexistent_vector(self, storage, search_config):
        """Test search by non-existent vector ID"""
        await storage.create_index("test_index", 1536)
        
        with pytest.raises(VectorNotFoundException):
            await storage.search_by_id("test_index", "nonexistent", search_config)
    
    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, storage, search_config):
        """Test search with metadata filtering"""
        await storage.create_index("test_index", 1536)
        
        # Create different metadata
        metadata1 = UnifiedVectorMetadata(
            entity_id="entity1",
            entity_type=VectorEntityType.COMPANY,
            vector_id="vec1",
            embedding=VectorEmbeddingMetadata(
                model_name="test-model",
                model_provider="test-provider", 
                dimensions=1536
            ),
            index_name="test_index"
        )
        
        metadata2 = UnifiedVectorMetadata(
            entity_id="entity2",
            entity_type=VectorEntityType.RESEARCH,
            vector_id="vec2",
            embedding=VectorEmbeddingMetadata(
                model_name="test-model",
                model_provider="test-provider",
                dimensions=1536
            ),
            index_name="test_index"
        )
        
        # Insert vectors with different metadata
        await storage.upsert_vector("test_index", "vec1", [1.0] * 1536, metadata1)
        await storage.upsert_vector("test_index", "vec2", [1.0] * 1536, metadata2)
        
        # Search with entity type filter
        search_config.metadata_filter = {"entity_type": "company"}
        result = await storage.search_similar("test_index", [1.0] * 1536, search_config)
        
        # Should only find company entities
        for match in result.matches:
            if match.metadata:
                assert match.metadata.entity_type == "company"
    
    @pytest.mark.asyncio
    async def test_count_vectors(self, storage, basic_metadata):
        """Test vector counting"""
        await storage.create_index("test_index", 1536)
        
        # Insert test vectors
        for i in range(5):
            await storage.upsert_vector("test_index", f"vec{i}", [0.1] * 1536, basic_metadata)
        
        count = await storage.count_vectors("test_index")
        assert count == 5
        
        # Count with filter
        count_filtered = await storage.count_vectors(
            "test_index", 
            metadata_filter={"entity_type": "company"}
        )
        assert count_filtered == 5  # All vectors have company entity type
    
    @pytest.mark.asyncio
    async def test_context_manager_requirement(self):
        """Test that storage requires context manager usage"""
        storage = MockVectorStorage()
        
        with pytest.raises(VectorStorageException, match="context manager"):
            await storage.create_index("test", 1536)
    
    @pytest.mark.asyncio
    async def test_interface_compliance(self, storage):
        """Test that MockVectorStorage fully implements VectorStorage interface"""
        # Verify it's recognized as VectorStorage
        assert isinstance(storage, VectorStorage)
        
        # Verify all required methods exist
        required_methods = [
            'create_index', 'delete_index', 'list_indexes', 'get_index_stats',
            'index_exists', 'upsert_vector', 'upsert_vectors_batch', 'get_vector',
            'get_vectors_batch', 'delete_vector', 'delete_vectors_batch',
            'delete_by_filter', 'search_similar', 'search_by_id', 'search_by_metadata',
            'get_similar_entities', 'count_vectors', 'update_metadata',
            'close', '__aenter__', '__aexit__'
        ]
        
        for method_name in required_methods:
            assert hasattr(storage, method_name)
            assert callable(getattr(storage, method_name))


class TestVectorUtilityFunctions:
    """Test utility functions for vector operations"""
    
    def test_validate_vector_dimensions(self):
        """Test vector dimension validation"""
        vector = [1.0, 2.0, 3.0]
        
        assert validate_vector_dimensions(vector, 3) is True
        assert validate_vector_dimensions(vector, 4) is False
        assert validate_vector_dimensions(vector, 2) is False
    
    def test_normalize_vector(self):
        """Test vector normalization"""
        vector = [3.0, 4.0]  # Length 5
        normalized = normalize_vector(vector)
        
        # Should have unit length
        magnitude = calculate_vector_magnitude(normalized)
        assert abs(magnitude - 1.0) < 1e-6
        
        # Should preserve direction (allowing for floating point precision)
        expected_ratio = 3.0 / 4.0
        actual_ratio = normalized[0] / normalized[1]
        assert abs(actual_ratio - expected_ratio) < 1e-6
    
    def test_calculate_vector_magnitude(self):
        """Test vector magnitude calculation"""
        vector = [3.0, 4.0]
        magnitude = calculate_vector_magnitude(vector)
        assert abs(magnitude - 5.0) < 1e-6
        
        # Zero vector
        zero_vector = [0.0, 0.0, 0.0]
        magnitude = calculate_vector_magnitude(zero_vector)
        assert magnitude == 0.0
    
    def test_vectors_are_similar(self):
        """Test vector similarity comparison"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        vec3 = [1.1, 2.1, 3.1]
        
        assert vectors_are_similar(vec1, vec2) is True
        assert vectors_are_similar(vec1, vec3, threshold=0.2) is True
        assert vectors_are_similar(vec1, vec3, threshold=0.05) is False
        
        # Different dimensions
        vec4 = [1.0, 2.0]
        assert vectors_are_similar(vec1, vec4) is False


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
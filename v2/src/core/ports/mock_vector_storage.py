"""
Mock vector storage implementation for Theodore testing.

This module provides a complete in-memory mock implementation of the
VectorStorage interface for testing and development purposes.
"""

import asyncio
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Union, AsyncIterator, Set
from datetime import datetime
import random
import math

from src.core.ports.vector_storage import (
    VectorStorage, BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage,
    VectorStorageException, VectorIndexException, VectorNotFoundException,
    VectorDimensionMismatchException, VectorQuotaExceededException,
    InvalidVectorFilterException, ProgressCallback, VectorId, Vector, MetadataFilter
)
from src.core.domain.value_objects.vector_config import SearchConfig, SimilarityMetric
from src.core.domain.value_objects.vector_result import (
    VectorSearchResult, VectorOperationResult, IndexInfo, VectorRecord,
    SearchMatch, OperationStatus, VectorOperationType
)


class MockVectorIndex:
    """Mock vector index implementation"""
    
    def __init__(self, name: str, dimensions: int, metric: str = SimilarityMetric.COSINE):
        self.name = name
        self.dimensions = dimensions
        self.metric = metric
        self.created_at = datetime.utcnow()
        self.vectors: Dict[str, Dict[str, Any]] = {}  # namespace -> {vector_id: {vector, metadata}}
        self.total_operations = 0
        self.query_count = 0
        self.last_query_time = None
        
    def get_stats(self) -> IndexInfo:
        """Get index statistics"""
        total_vectors = sum(len(namespace_vectors) for namespace_vectors in self.vectors.values())
        
        return IndexInfo(
            name=self.name,
            provider="mock",
            dimensions=self.dimensions,
            similarity_metric=self.metric,
            index_type="flat",
            total_vectors=total_vectors,
            index_size_bytes=total_vectors * self.dimensions * 4,  # Estimate: 4 bytes per float
            average_query_latency=random.uniform(1.0, 10.0) if self.query_count > 0 else None,
            queries_per_second=self.query_count / max(1, (datetime.utcnow() - self.created_at).total_seconds()),
            status="healthy",
            last_updated=datetime.utcnow(),
            memory_usage_mb=(total_vectors * self.dimensions * 4) / (1024 * 1024),
            disk_usage_mb=0.0  # In-memory only
        )
    
    def add_vector(self, namespace: str, vector_id: str, vector: Vector, metadata: Optional[Dict[str, Any]] = None):
        """Add vector to index"""
        if len(vector) != self.dimensions:
            raise VectorDimensionMismatchException(self.dimensions, len(vector), self.name)
        
        if namespace not in self.vectors:
            self.vectors[namespace] = {}
        
        self.vectors[namespace][vector_id] = {
            "vector": vector.copy(),
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        self.total_operations += 1
    
    def get_vector(self, namespace: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector from index"""
        return self.vectors.get(namespace, {}).get(vector_id)
    
    def delete_vector(self, namespace: str, vector_id: str) -> bool:
        """Delete vector from index"""
        if namespace in self.vectors and vector_id in self.vectors[namespace]:
            del self.vectors[namespace][vector_id]
            self.total_operations += 1
            return True
        return False
    
    def search_vectors(
        self, 
        query_vector: Vector, 
        config: SearchConfig, 
        namespace: str = "default"
    ) -> List[tuple[str, float, Dict[str, Any]]]:
        """Search for similar vectors"""
        if len(query_vector) != self.dimensions:
            raise VectorDimensionMismatchException(self.dimensions, len(query_vector))
        
        self.query_count += 1
        self.last_query_time = datetime.utcnow()
        
        namespace_vectors = self.vectors.get(namespace, {})
        results = []
        
        for vector_id, vector_data in namespace_vectors.items():
            # Apply metadata filter
            if config.metadata_filter:
                if not self._matches_filter(vector_data["metadata"], config.metadata_filter):
                    continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(
                query_vector, 
                vector_data["vector"], 
                self.metric
            )
            
            # Apply similarity threshold
            if config.similarity_threshold and similarity < config.similarity_threshold:
                continue
            
            results.append((vector_id, similarity, vector_data))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return results[:config.top_k]
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter"""
        for key, expected_value in filter_dict.items():
            if key not in metadata:
                return False
            
            actual_value = metadata[key]
            
            # Handle different filter types
            if isinstance(expected_value, dict):
                # Range queries like {"$gte": 100, "$lt": 200}
                if "$gte" in expected_value and actual_value < expected_value["$gte"]:
                    return False
                if "$gt" in expected_value and actual_value <= expected_value["$gt"]:
                    return False
                if "$lte" in expected_value and actual_value > expected_value["$lte"]:
                    return False
                if "$lt" in expected_value and actual_value >= expected_value["$lt"]:
                    return False
                if "$eq" in expected_value and actual_value != expected_value["$eq"]:
                    return False
                if "$ne" in expected_value and actual_value == expected_value["$ne"]:
                    return False
            elif isinstance(expected_value, list):
                # "In" queries
                if actual_value not in expected_value:
                    return False
            else:
                # Exact match
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _calculate_similarity(self, vector1: Vector, vector2: Vector, metric: str) -> float:
        """Calculate similarity between two vectors"""
        if metric == SimilarityMetric.COSINE:
            return self._cosine_similarity(vector1, vector2)
        elif metric == SimilarityMetric.EUCLIDEAN:
            return 1.0 / (1.0 + self._euclidean_distance(vector1, vector2))
        elif metric == SimilarityMetric.DOT_PRODUCT:
            return self._dot_product(vector1, vector2)
        else:
            return self._cosine_similarity(vector1, vector2)
    
    def _cosine_similarity(self, vector1: Vector, vector2: Vector) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        norm1 = math.sqrt(sum(a * a for a in vector1))
        norm2 = math.sqrt(sum(b * b for b in vector2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _euclidean_distance(self, vector1: Vector, vector2: Vector) -> float:
        """Calculate Euclidean distance"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vector1, vector2)))
    
    def _dot_product(self, vector1: Vector, vector2: Vector) -> float:
        """Calculate dot product"""
        return sum(a * b for a, b in zip(vector1, vector2))


class MockVectorStorage(VectorStorage, BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage):
    """
    Mock vector storage implementation with full feature support.
    
    Provides an in-memory implementation suitable for testing and development
    with configurable behaviors for simulating real-world scenarios.
    """
    
    def __init__(
        self, 
        max_indexes: int = 100,
        max_vectors_per_index: int = 100000,
        simulate_latency: bool = False,
        error_rate: float = 0.0,
        enable_cache: bool = True
    ):
        self.indexes: Dict[str, MockVectorIndex] = {}
        self.max_indexes = max_indexes
        self.max_vectors_per_index = max_vectors_per_index
        self.simulate_latency = simulate_latency
        self.error_rate = error_rate
        self.enable_cache = enable_cache
        
        # Cache for search results
        self.search_cache: Dict[str, tuple[VectorSearchResult, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes default
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Statistics
        self.operation_count = 0
        self.error_count = 0
        self.created_at = datetime.utcnow()
    
    async def _maybe_simulate_latency(self):
        """Simulate network/processing latency"""
        if self.simulate_latency:
            await asyncio.sleep(random.uniform(0.001, 0.1))
    
    async def _maybe_simulate_error(self, operation: str):
        """Simulate random errors"""
        if random.random() < self.error_rate:
            self.error_count += 1
            raise VectorStorageException(f"Simulated error during {operation}")
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation ID"""
        return f"mock_op_{uuid.uuid4().hex[:8]}"
    
    # Index Management Methods
    
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = SimilarityMetric.COSINE,
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        """Create a new vector index"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("create_index")
        
        if len(self.indexes) >= self.max_indexes:
            raise VectorQuotaExceededException("indexes", len(self.indexes), self.max_indexes)
        
        if index_name in self.indexes:
            raise VectorIndexException(index_name, "create", "Index already exists")
        
        start_time = time.time()
        
        self.indexes[index_name] = MockVectorIndex(index_name, dimensions, metric)
        self.operation_count += 1
        
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.INDEX_CREATE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS,
            successful_count=1,
            failed_count=0,
            total_count=1,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=[index_name]
        )
    
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """Delete a vector index"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("delete_index")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "delete", "Index does not exist")
        
        start_time = time.time()
        
        # Count vectors being deleted
        index = self.indexes[index_name]
        total_vectors = sum(len(namespace_vectors) for namespace_vectors in index.vectors.values())
        
        del self.indexes[index_name]
        self.operation_count += 1
        
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.INDEX_DELETE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS,
            successful_count=total_vectors,
            failed_count=0,
            total_count=total_vectors,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=[index_name]
        )
    
    async def list_indexes(self) -> List[str]:
        """List all available vector indexes"""
        await self._maybe_simulate_latency()
        return list(self.indexes.keys())
    
    async def get_index_stats(self, index_name: str) -> IndexInfo:
        """Get statistics for a vector index"""
        await self._maybe_simulate_latency()
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "get_stats", "Index does not exist")
        
        return self.indexes[index_name].get_stats()
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists"""
        return index_name in self.indexes
    
    # Vector CRUD Operations
    
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        vector: Vector,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Insert or update a single vector"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("upsert_vector")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "upsert", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        # Check vector count limit
        index = self.indexes[index_name]
        total_vectors = sum(len(ns_vectors) for ns_vectors in index.vectors.values())
        
        if total_vectors >= self.max_vectors_per_index:
            raise VectorQuotaExceededException("vectors", total_vectors, self.max_vectors_per_index)
        
        index.add_vector(namespace, vector_id, vector, metadata)
        self.operation_count += 1
        
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.INSERT,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS,
            successful_count=1,
            failed_count=0,
            total_count=1,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=[vector_id]
        )
    
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[Dict[str, Any]]]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """Insert or update multiple vectors efficiently"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("upsert_vectors_batch")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "upsert_batch", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        successful_count = 0
        failed_count = 0
        affected_ids = []
        errors = []
        
        # Process vectors in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            for j, (vector_id, vector, metadata) in enumerate(batch):
                try:
                    # Check dimensions
                    if len(vector) != self.indexes[index_name].dimensions:
                        raise VectorDimensionMismatchException(
                            self.indexes[index_name].dimensions, 
                            len(vector), 
                            index_name
                        )
                    
                    self.indexes[index_name].add_vector(namespace, vector_id, vector, metadata)
                    successful_count += 1
                    affected_ids.append(vector_id)
                    
                except Exception as e:
                    failed_count += 1
                    errors.append({
                        "message": str(e),
                        "vector_id": vector_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Report progress
            if progress_callback:
                progress = min(1.0, (i + len(batch)) / len(vectors))
                progress_callback(
                    f"Processed {i + len(batch)}/{len(vectors)} vectors",
                    progress,
                    f"Batch {i // batch_size + 1}"
                )
            
            # Simulate batch processing delay
            if self.simulate_latency:
                await asyncio.sleep(0.01)
        
        execution_time = time.time() - start_time
        status = OperationStatus.SUCCESS if failed_count == 0 else OperationStatus.PARTIAL_SUCCESS
        
        result = VectorOperationResult(
            operation_type=VectorOperationType.BULK_INSERT,
            operation_id=self._generate_operation_id(),
            status=status,
            successful_count=successful_count,
            failed_count=failed_count,
            total_count=len(vectors),
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=affected_ids
        )
        
        # Add errors to result
        result.errors = errors
        
        return result
    
    async def get_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> tuple[Optional[Vector], Optional[Dict[str, Any]]]:
        """Retrieve a single vector by ID"""
        await self._maybe_simulate_latency()
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "get", "Index does not exist")
        
        namespace = namespace or "default"
        vector_data = self.indexes[index_name].get_vector(namespace, vector_id)
        
        if not vector_data:
            return None, None
        
        vector = vector_data["vector"] if include_values else None
        metadata = vector_data["metadata"] if include_metadata else None
        
        return vector, metadata
    
    async def get_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Dict[VectorId, tuple[Optional[Vector], Optional[Dict[str, Any]]]]:
        """Retrieve multiple vectors by ID efficiently"""
        await self._maybe_simulate_latency()
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "get_batch", "Index does not exist")
        
        namespace = namespace or "default"
        results = {}
        
        for vector_id in vector_ids:
            vector_data = self.indexes[index_name].get_vector(namespace, vector_id)
            
            if vector_data:
                vector = vector_data["vector"] if include_values else None
                metadata = vector_data["metadata"] if include_metadata else None
                results[vector_id] = (vector, metadata)
            else:
                results[vector_id] = (None, None)
        
        return results
    
    async def delete_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete a single vector by ID"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("delete_vector")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "delete", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        success = self.indexes[index_name].delete_vector(namespace, vector_id)
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.DELETE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS if success else OperationStatus.FAILED,
            successful_count=1 if success else 0,
            failed_count=0 if success else 1,
            total_count=1,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=[vector_id] if success else []
        )
    
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Delete multiple vectors efficiently"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("delete_vectors_batch")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "delete_batch", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        successful_count = 0
        affected_ids = []
        
        for vector_id in vector_ids:
            if self.indexes[index_name].delete_vector(namespace, vector_id):
                successful_count += 1
                affected_ids.append(vector_id)
        
        execution_time = time.time() - start_time
        failed_count = len(vector_ids) - successful_count
        
        return VectorOperationResult(
            operation_type=VectorOperationType.BULK_DELETE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS if failed_count == 0 else OperationStatus.PARTIAL_SUCCESS,
            successful_count=successful_count,
            failed_count=failed_count,
            total_count=len(vector_ids),
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=affected_ids
        )
    
    async def delete_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete vectors matching metadata filter"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("delete_by_filter")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "delete_by_filter", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        index = self.indexes[index_name]
        namespace_vectors = index.vectors.get(namespace, {})
        
        # Find matching vectors
        to_delete = []
        for vector_id, vector_data in namespace_vectors.items():
            if index._matches_filter(vector_data["metadata"], metadata_filter):
                to_delete.append(vector_id)
        
        # Delete matching vectors
        successful_count = 0
        for vector_id in to_delete:
            if index.delete_vector(namespace, vector_id):
                successful_count += 1
        
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.DELETE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS,
            successful_count=successful_count,
            failed_count=0,
            total_count=successful_count,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=to_delete
        )
    
    # Vector Search Operations
    
    async def search_similar(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for similar vectors using a query vector"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("search_similar")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "search", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{index_name}:{namespace}:{hash(str(query_vector))}:{hash(str(config.model_dump()))}"
        if self.enable_cache and cache_key in self.search_cache:
            cached_result, cached_time = self.search_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl:
                self.cache_hits += 1
                return cached_result
        
        self.cache_misses += 1
        
        # Perform search
        raw_results = self.indexes[index_name].search_vectors(query_vector, config, namespace)
        
        # Convert to SearchMatch objects
        matches = []
        for rank, (vector_id, similarity_score, vector_data) in enumerate(raw_results, 1):
            record = VectorRecord(
                id=vector_id,
                vector=vector_data["vector"],
                metadata=vector_data["metadata"],
                created_at=vector_data["created_at"],
                updated_at=vector_data["updated_at"]
            )
            
            match = SearchMatch(
                record=record,
                score=similarity_score,
                rank=rank,
                distance=1.0 - similarity_score if config.similarity_threshold else None,
                confidence=similarity_score
            )
            matches.append(match)
        
        execution_time = time.time() - start_time
        search_id = f"search_{uuid.uuid4().hex[:8]}"
        
        result = VectorSearchResult(
            matches=matches,
            total_matches=len(matches),
            query_vector=query_vector if config.include_vectors else None,
            search_id=search_id,
            search_time=execution_time,
            index_search_time=execution_time * 0.8,  # Most time spent in index
            top_k=config.top_k,
            similarity_threshold=config.similarity_threshold,
            metadata_filter=config.metadata_filter,
            provider_name="mock",
            index_name=index_name
        )
        
        # Cache result
        if self.enable_cache:
            self.search_cache[cache_key] = (result, datetime.utcnow())
        
        return result
    
    async def search_by_id(
        self,
        index_name: str,
        vector_id: VectorId,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for vectors similar to a stored vector"""
        # First get the vector
        vector, metadata = await self.get_vector(index_name, vector_id, namespace, include_values=True)
        
        if vector is None:
            raise VectorNotFoundException(vector_id, index_name)
        
        # Then search using that vector
        return await self.search_similar(index_name, vector, config, namespace)
    
    async def search_by_metadata(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        limit: int = 100,
        offset: int = 0,
        namespace: Optional[str] = None
    ) -> List[tuple[VectorId, Dict[str, Any]]]:
        """Search vectors by metadata only"""
        await self._maybe_simulate_latency()
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "search_metadata", "Index does not exist")
        
        namespace = namespace or "default"
        index = self.indexes[index_name]
        namespace_vectors = index.vectors.get(namespace, {})
        
        results = []
        for vector_id, vector_data in namespace_vectors.items():
            if index._matches_filter(vector_data["metadata"], metadata_filter):
                results.append((vector_id, vector_data["metadata"]))
        
        # Apply offset and limit
        return results[offset:offset + limit]
    
    # Advanced Operations
    
    async def get_similar_entities(
        self,
        index_name: str,
        entity_id: str,
        entity_type: str,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Find entities similar to a given entity"""
        # Add entity type to metadata filter
        enhanced_filter = config.metadata_filter.copy()
        enhanced_filter["entity_type"] = entity_type
        
        enhanced_config = config.model_copy(update={"metadata_filter": enhanced_filter})
        
        return await self.search_by_id(index_name, entity_id, enhanced_config, namespace)
    
    async def count_vectors(
        self,
        index_name: str,
        metadata_filter: Optional[MetadataFilter] = None,
        namespace: Optional[str] = None
    ) -> int:
        """Count vectors matching optional filter"""
        await self._maybe_simulate_latency()
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "count", "Index does not exist")
        
        namespace = namespace or "default"
        index = self.indexes[index_name]
        namespace_vectors = index.vectors.get(namespace, {})
        
        if not metadata_filter:
            return len(namespace_vectors)
        
        count = 0
        for vector_data in namespace_vectors.values():
            if index._matches_filter(vector_data["metadata"], metadata_filter):
                count += 1
        
        return count
    
    async def update_metadata(
        self,
        index_name: str,
        vector_id: VectorId,
        metadata: Dict[str, Any],
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Update metadata for an existing vector"""
        await self._maybe_simulate_latency()
        await self._maybe_simulate_error("update_metadata")
        
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "update", "Index does not exist")
        
        namespace = namespace or "default"
        start_time = time.time()
        
        vector_data = self.indexes[index_name].get_vector(namespace, vector_id)
        if not vector_data:
            raise VectorNotFoundException(vector_id, index_name)
        
        # Update metadata
        vector_data["metadata"].update(metadata)
        vector_data["updated_at"] = datetime.utcnow()
        
        execution_time = time.time() - start_time
        
        return VectorOperationResult(
            operation_type=VectorOperationType.UPDATE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS,
            successful_count=1,
            failed_count=0,
            total_count=1,
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=[vector_id]
        )
    
    # Context Manager and Lifecycle
    
    async def close(self) -> None:
        """Clean up resources and close connections"""
        self.indexes.clear()
        self.search_cache.clear()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        await self.close()
    
    # BatchVectorStorage methods
    
    async def upsert_vectors_chunked(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[Dict[str, Any]]]],
        chunk_size: Optional[int] = None,
        max_parallel: int = 5,
        namespace: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """Upsert vectors with automatic chunking"""
        chunk_size = chunk_size or min(1000, len(vectors) // max_parallel + 1)
        
        # Process in parallel chunks
        chunks = [vectors[i:i + chunk_size] for i in range(0, len(vectors), chunk_size)]
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def process_chunk(chunk):
            async with semaphore:
                return await self.upsert_vectors_batch(
                    index_name, chunk, namespace, batch_size=len(chunk)
                )
        
        start_time = time.time()
        results = await asyncio.gather(*[process_chunk(chunk) for chunk in chunks])
        execution_time = time.time() - start_time
        
        # Aggregate results
        total_successful = sum(r.successful_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        all_affected_ids = []
        all_errors = []
        
        for result in results:
            all_affected_ids.extend(result.affected_ids)
            all_errors.extend(result.errors)
        
        return VectorOperationResult(
            operation_type=VectorOperationType.BULK_INSERT,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS if total_failed == 0 else OperationStatus.PARTIAL_SUCCESS,
            successful_count=total_successful,
            failed_count=total_failed,
            total_count=len(vectors),
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=all_affected_ids,
            errors=all_errors
        )
    
    async def search_multiple_vectors(
        self,
        index_name: str,
        query_vectors: List[Vector],
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors using multiple query vectors"""
        # Execute searches in parallel
        search_tasks = [
            self.search_similar(index_name, query_vector, config, namespace)
            for query_vector in query_vectors
        ]
        
        return await asyncio.gather(*search_tasks)
    
    async def bulk_update_metadata(
        self,
        index_name: str,
        updates: List[tuple[VectorId, Dict[str, Any]]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Update metadata for multiple vectors efficiently"""
        start_time = time.time()
        successful_count = 0
        failed_count = 0
        affected_ids = []
        errors = []
        
        for vector_id, metadata in updates:
            try:
                await self.update_metadata(index_name, vector_id, metadata, namespace)
                successful_count += 1
                affected_ids.append(vector_id)
            except Exception as e:
                failed_count += 1
                errors.append({
                    "message": str(e),
                    "vector_id": vector_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        execution_time = time.time() - start_time
        
        result = VectorOperationResult(
            operation_type=VectorOperationType.BULK_UPDATE,
            operation_id=self._generate_operation_id(),
            status=OperationStatus.SUCCESS if failed_count == 0 else OperationStatus.PARTIAL_SUCCESS,
            successful_count=successful_count,
            failed_count=failed_count,
            total_count=len(updates),
            execution_time=execution_time,
            provider_name="mock",
            index_name=index_name,
            affected_ids=affected_ids,
            errors=errors
        )
        
        return result
    
    # StreamingVectorStorage methods
    
    async def stream_search_results(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, float, Optional[Dict[str, Any]]]]:
        """Stream search results as they become available"""
        result = await self.search_similar(index_name, query_vector, config, namespace)
        
        for match in result.matches:
            # Simulate streaming delay
            if self.simulate_latency:
                await asyncio.sleep(0.01)
            
            yield (match.record.id, match.score, match.record.metadata)
    
    async def stream_vectors_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, Vector, Dict[str, Any]]]:
        """Stream vectors matching metadata filter"""
        if index_name not in self.indexes:
            raise VectorIndexException(index_name, "stream", "Index does not exist")
        
        namespace = namespace or "default"
        index = self.indexes[index_name]
        namespace_vectors = index.vectors.get(namespace, {})
        
        for vector_id, vector_data in namespace_vectors.items():
            if index._matches_filter(vector_data["metadata"], metadata_filter):
                # Simulate streaming delay
                if self.simulate_latency:
                    await asyncio.sleep(0.001)
                
                yield (vector_id, vector_data["vector"], vector_data["metadata"])
    
    # CacheableVectorStorage methods
    
    async def search_with_cache(
        self,
        index_name: str,
        query_vector: Vector,
        config: SearchConfig,
        cache_ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search with caching of results"""
        # Use custom TTL if provided
        original_ttl = self.cache_ttl
        if cache_ttl is not None:
            self.cache_ttl = cache_ttl
        
        try:
            return await self.search_similar(index_name, query_vector, config, namespace)
        finally:
            self.cache_ttl = original_ttl
    
    async def clear_search_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cached search results"""
        if pattern is None:
            count = len(self.search_cache)
            self.search_cache.clear()
            return count
        
        # Simple pattern matching (contains)
        to_remove = []
        for key in self.search_cache:
            if pattern in key:
                to_remove.append(key)
        
        for key in to_remove:
            del self.search_cache[key]
        
        return len(to_remove)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "total_entries": len(self.search_cache),
            "hit_rate": hit_rate,
            "miss_rate": 1.0 - hit_rate,
            "size_bytes": len(str(self.search_cache)),  # Rough estimate
            "oldest_entry": min((cached_time for _, cached_time in self.search_cache.values()), default=None),
            "newest_entry": max((cached_time for _, cached_time in self.search_cache.values()), default=None),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses
        }


# Utility functions for creating mock instances

def create_mock_vector_storage(
    max_indexes: int = 10,
    max_vectors_per_index: int = 10000,
    simulate_latency: bool = False,
    error_rate: float = 0.0
) -> MockVectorStorage:
    """Create a mock vector storage with specified configuration"""
    return MockVectorStorage(
        max_indexes=max_indexes,
        max_vectors_per_index=max_vectors_per_index,
        simulate_latency=simulate_latency,
        error_rate=error_rate
    )


def create_test_vectors(count: int, dimensions: int) -> List[tuple[str, Vector, Dict[str, Any]]]:
    """Create test vectors for development and testing"""
    vectors = []
    
    for i in range(count):
        vector_id = f"test_vector_{i:04d}"
        vector = [random.uniform(-1.0, 1.0) for _ in range(dimensions)]
        metadata = {
            "category": random.choice(["technology", "business", "science", "arts"]),
            "priority": random.randint(1, 10),
            "created_by": "test_system",
            "tags": random.sample(["important", "draft", "reviewed", "archived"], k=random.randint(1, 3))
        }
        
        vectors.append((vector_id, vector, metadata))
    
    return vectors
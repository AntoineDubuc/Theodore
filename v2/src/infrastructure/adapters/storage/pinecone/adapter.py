"""
Pinecone vector storage adapter implementing the VectorStorage interface.

This module provides the main adapter class that implements all VectorStorage
interface methods with Pinecone-specific functionality.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, AsyncIterator, Tuple
from contextlib import asynccontextmanager
import time
import json

from src.core.ports.vector_storage import (
    VectorStorage, BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage,
    VectorStorageException, VectorIndexException, VectorNotFoundException,
    VectorDimensionMismatchException, VectorQuotaExceededException,
    InvalidVectorFilterException, VectorId, Vector, MetadataFilter, ProgressCallback
)
from src.core.domain.value_objects.vector_search_result import (
    VectorSearchConfig, VectorSearchResult, VectorSearchMatch, VectorMetadata,
    VectorOperationResult, IndexStats, DistanceMetric
)
from src.core.domain.value_objects.vector_metadata import (
    UnifiedVectorMetadata, VectorEntityType, VectorEmbeddingMetadata
)

from .config import PineconeConfig
from .client import PineconeClient
from .index import PineconeIndexManager
from .batch import PineconeBatchProcessor
from .query import PineconeQueryEngine
from .monitor import PineconeMonitor


logger = logging.getLogger(__name__)


class PineconeVectorStorage(BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage):
    """
    Comprehensive Pinecone implementation of the VectorStorage interface.
    
    Provides enterprise-grade vector storage with advanced features including
    batch operations, streaming, caching, and comprehensive monitoring.
    """
    
    def __init__(self, config: PineconeConfig):
        self.config = config
        self.client = PineconeClient(config)
        self.index_manager = PineconeIndexManager(self.client, config)
        self.batch_processor = PineconeBatchProcessor(self.client, config)
        self.query_engine = PineconeQueryEngine(self.client, config)
        self.monitor = PineconeMonitor(config)
        
        self._initialized = False
        self._closed = False
        
        logger.info(f"Initialized Pinecone vector storage adapter")
    
    async def _ensure_initialized(self) -> None:
        """Ensure adapter is properly initialized."""
        if self._closed:
            raise VectorStorageException("Vector storage has been closed")
        
        if not self._initialized:
            await self.client.initialize()
            self._initialized = True
    
    # Index Management Methods
    
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = DistanceMetric.COSINE,
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        """Create a new vector index."""
        await self._ensure_initialized()
        
        try:
            # Validate metric
            pinecone_metric = self._convert_metric_to_pinecone(metric)
            
            # Create index with Pinecone-specific configuration
            result = await self.index_manager.create_index(
                index_name=index_name,
                dimensions=dimensions,
                metric=pinecone_metric,
                metadata_config=metadata_config,
                **kwargs
            )
            
            self.monitor.record_operation("create_index", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("create_index", success=False)
            logger.error(f"Failed to create index {index_name}: {e}")
            raise VectorIndexException(index_name, "create", str(e))
    
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """Delete a vector index and all its data."""
        await self._ensure_initialized()
        
        try:
            result = await self.index_manager.delete_index(index_name)
            self.monitor.record_operation("delete_index", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("delete_index", success=False)
            logger.error(f"Failed to delete index {index_name}: {e}")
            raise VectorIndexException(index_name, "delete", str(e))
    
    async def list_indexes(self) -> List[str]:
        """List all available vector indexes."""
        await self._ensure_initialized()
        
        try:
            indexes = await self.client.list_indexes()
            self.monitor.record_operation("list_indexes", success=True)
            return indexes
            
        except Exception as e:
            self.monitor.record_operation("list_indexes", success=False)
            logger.error(f"Failed to list indexes: {e}")
            raise VectorStorageException(f"Failed to list indexes: {e}")
    
    async def get_index_stats(self, index_name: str) -> IndexStats:
        """Get statistics for a vector index."""
        await self._ensure_initialized()
        
        try:
            stats = await self.index_manager.get_index_stats(index_name)
            self.monitor.record_operation("get_index_stats", success=True)
            return stats
            
        except Exception as e:
            self.monitor.record_operation("get_index_stats", success=False)
            logger.error(f"Failed to get stats for index {index_name}: {e}")
            raise VectorIndexException(index_name, "get_stats", str(e))
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists."""
        await self._ensure_initialized()
        
        try:
            exists = await self.client.index_exists(index_name)
            return exists
        except Exception as e:
            logger.error(f"Failed to check if index {index_name} exists: {e}")
            return False
    
    # Vector CRUD Operations
    
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        vector: Vector,
        metadata: Optional[UnifiedVectorMetadata] = None,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Insert or update a single vector."""
        await self._ensure_initialized()
        
        try:
            # Validate vector dimensions
            await self._validate_vector_dimensions(index_name, vector)
            
            # Convert metadata to Pinecone format
            pinecone_metadata = self._convert_metadata_to_pinecone(metadata) if metadata else {}
            
            # Get index connection
            index = await self.client.get_index(index_name)
            
            # Upsert vector
            upsert_response = index.upsert(
                vectors=[(vector_id, vector, pinecone_metadata)],
                namespace=namespace
            )
            
            self.monitor.record_operation("upsert_vector", success=True)
            
            return VectorOperationResult.success_result(
                operation="upsert_vector",
                affected_count=upsert_response.upserted_count if hasattr(upsert_response, 'upserted_count') else 1,
                message=f"Vector {vector_id} upserted successfully"
            )
            
        except Exception as e:
            self.monitor.record_operation("upsert_vector", success=False)
            logger.error(f"Failed to upsert vector {vector_id}: {e}")
            
            if "dimension" in str(e).lower():
                raise VectorDimensionMismatchException(
                    expected=await self._get_index_dimensions(index_name),
                    actual=len(vector),
                    index_name=index_name
                )
            
            raise VectorStorageException(f"Failed to upsert vector {vector_id}: {e}")
    
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[UnifiedVectorMetadata]]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """Insert or update multiple vectors efficiently."""
        await self._ensure_initialized()
        
        try:
            result = await self.batch_processor.upsert_vectors_batch(
                index_name=index_name,
                vectors=vectors,
                namespace=namespace,
                batch_size=batch_size,
                progress_callback=progress_callback
            )
            
            self.monitor.record_operation("upsert_vectors_batch", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("upsert_vectors_batch", success=False)
            logger.error(f"Failed to upsert batch vectors: {e}")
            raise VectorStorageException(f"Failed to upsert batch vectors: {e}")
    
    async def get_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> tuple[Optional[Vector], Optional[UnifiedVectorMetadata]]:
        """Retrieve a single vector by ID."""
        await self._ensure_initialized()
        
        try:
            index = await self.client.get_index(index_name)
            
            fetch_response = index.fetch(
                ids=[vector_id],
                namespace=namespace
            )
            
            if vector_id not in fetch_response.vectors:
                return None, None
            
            vector_data = fetch_response.vectors[vector_id]
            
            # Extract vector values if requested
            vector_values = vector_data.values if include_values else None
            
            # Convert metadata back to UnifiedVectorMetadata if present
            metadata = None
            if include_metadata and vector_data.metadata:
                metadata = self._convert_metadata_from_pinecone(vector_data.metadata)
            
            self.monitor.record_operation("get_vector", success=True)
            return vector_values, metadata
            
        except Exception as e:
            self.monitor.record_operation("get_vector", success=False)
            logger.error(f"Failed to get vector {vector_id}: {e}")
            raise VectorStorageException(f"Failed to get vector {vector_id}: {e}")
    
    async def get_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Dict[VectorId, tuple[Optional[Vector], Optional[UnifiedVectorMetadata]]]:
        """Retrieve multiple vectors by ID efficiently."""
        await self._ensure_initialized()
        
        try:
            result = await self.batch_processor.get_vectors_batch(
                index_name=index_name,
                vector_ids=vector_ids,
                namespace=namespace,
                include_values=include_values,
                include_metadata=include_metadata
            )
            
            self.monitor.record_operation("get_vectors_batch", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("get_vectors_batch", success=False)
            logger.error(f"Failed to get batch vectors: {e}")
            raise VectorStorageException(f"Failed to get batch vectors: {e}")
    
    async def delete_vector(
        self,
        index_name: str,
        vector_id: VectorId,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete a single vector by ID."""
        await self._ensure_initialized()
        
        try:
            index = await self.client.get_index(index_name)
            
            delete_response = index.delete(
                ids=[vector_id],
                namespace=namespace
            )
            
            self.monitor.record_operation("delete_vector", success=True)
            
            return VectorOperationResult.success_result(
                operation="delete_vector",
                affected_count=1,
                message=f"Vector {vector_id} deleted successfully"
            )
            
        except Exception as e:
            self.monitor.record_operation("delete_vector", success=False)
            logger.error(f"Failed to delete vector {vector_id}: {e}")
            raise VectorStorageException(f"Failed to delete vector {vector_id}: {e}")
    
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Delete multiple vectors efficiently."""
        await self._ensure_initialized()
        
        try:
            result = await self.batch_processor.delete_vectors_batch(
                index_name=index_name,
                vector_ids=vector_ids,
                namespace=namespace,
                batch_size=batch_size
            )
            
            self.monitor.record_operation("delete_vectors_batch", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("delete_vectors_batch", success=False)
            logger.error(f"Failed to delete batch vectors: {e}")
            raise VectorStorageException(f"Failed to delete batch vectors: {e}")
    
    async def delete_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Delete vectors matching metadata filter."""
        await self._ensure_initialized()
        
        try:
            # Convert filter to Pinecone format
            pinecone_filter = self._convert_filter_to_pinecone(metadata_filter)
            
            index = await self.client.get_index(index_name)
            
            delete_response = index.delete(
                filter=pinecone_filter,
                namespace=namespace
            )
            
            self.monitor.record_operation("delete_by_filter", success=True)
            
            return VectorOperationResult.success_result(
                operation="delete_by_filter",
                message="Vectors deleted by filter successfully"
            )
            
        except Exception as e:
            self.monitor.record_operation("delete_by_filter", success=False)
            logger.error(f"Failed to delete by filter: {e}")
            
            if "filter" in str(e).lower():
                raise InvalidVectorFilterException(str(metadata_filter), str(e))
            
            raise VectorStorageException(f"Failed to delete by filter: {e}")
    
    # Vector Search Operations
    
    async def search_similar(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for similar vectors using a query vector."""
        await self._ensure_initialized()
        
        try:
            result = await self.query_engine.search_similar(
                index_name=index_name,
                query_vector=query_vector,
                config=config,
                namespace=namespace
            )
            
            self.monitor.record_operation("search_similar", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("search_similar", success=False)
            logger.error(f"Failed to search similar vectors: {e}")
            
            if "dimension" in str(e).lower():
                raise VectorDimensionMismatchException(
                    expected=await self._get_index_dimensions(index_name),
                    actual=len(query_vector),
                    index_name=index_name
                )
            
            if "filter" in str(e).lower():
                raise InvalidVectorFilterException(str(config.metadata_filter), str(e))
            
            raise VectorStorageException(f"Failed to search similar vectors: {e}")
    
    async def search_by_id(
        self,
        index_name: str,
        vector_id: VectorId,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for vectors similar to a stored vector."""
        await self._ensure_initialized()
        
        try:
            # First get the vector
            vector_values, _ = await self.get_vector(
                index_name=index_name,
                vector_id=vector_id,
                namespace=namespace,
                include_values=True,
                include_metadata=False
            )
            
            if vector_values is None:
                raise VectorNotFoundException(vector_id, index_name)
            
            # Then search using its values
            return await self.search_similar(
                index_name=index_name,
                query_vector=vector_values,
                config=config,
                namespace=namespace
            )
            
        except VectorNotFoundException:
            raise
        except Exception as e:
            self.monitor.record_operation("search_by_id", success=False)
            logger.error(f"Failed to search by ID {vector_id}: {e}")
            raise VectorStorageException(f"Failed to search by ID {vector_id}: {e}")
    
    async def search_by_metadata(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        limit: int = 100,
        offset: int = 0,
        namespace: Optional[str] = None
    ) -> List[tuple[VectorId, UnifiedVectorMetadata]]:
        """Search vectors by metadata only (no similarity)."""
        await self._ensure_initialized()
        
        try:
            result = await self.query_engine.search_by_metadata(
                index_name=index_name,
                metadata_filter=metadata_filter,
                limit=limit,
                offset=offset,
                namespace=namespace
            )
            
            self.monitor.record_operation("search_by_metadata", success=True)
            return result
            
        except Exception as e:
            self.monitor.record_operation("search_by_metadata", success=False)
            logger.error(f"Failed to search by metadata: {e}")
            
            if "filter" in str(e).lower():
                raise InvalidVectorFilterException(str(metadata_filter), str(e))
            
            raise VectorStorageException(f"Failed to search by metadata: {e}")
    
    # Advanced Operations
    
    async def get_similar_entities(
        self,
        index_name: str,
        entity_id: str,
        entity_type: VectorEntityType,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Find entities similar to a given entity."""
        await self._ensure_initialized()
        
        try:
            # Create metadata filter for entity type
            entity_filter = {"entity_type": entity_type.value, "entity_id": entity_id}
            
            # Combine with existing filter if present
            if config.metadata_filter:
                combined_filter = {"$and": [entity_filter, config.metadata_filter]}
            else:
                combined_filter = entity_filter
            
            # Update config with entity filter
            entity_config = VectorSearchConfig(
                top_k=config.top_k,
                similarity_threshold=config.similarity_threshold,
                distance_metric=config.distance_metric,
                include_metadata=config.include_metadata,
                include_values=config.include_values,
                metadata_filter=combined_filter,
                namespace=config.namespace
            )
            
            # Search by entity vector
            return await self.search_by_id(
                index_name=index_name,
                vector_id=entity_id,
                config=entity_config,
                namespace=namespace
            )
            
        except Exception as e:
            logger.error(f"Failed to get similar entities for {entity_id}: {e}")
            raise VectorStorageException(f"Failed to get similar entities: {e}")
    
    async def count_vectors(
        self,
        index_name: str,
        metadata_filter: Optional[MetadataFilter] = None,
        namespace: Optional[str] = None
    ) -> int:
        """Count vectors matching optional filter."""
        await self._ensure_initialized()
        
        try:
            # Get index stats first
            stats = await self.get_index_stats(index_name)
            
            # If no filter, return total count
            if not metadata_filter:
                return stats.total_vectors
            
            # For filtered counts, we need to query (Pinecone doesn't have direct count with filter)
            # This is an approximation using a small search
            config = VectorSearchConfig(
                top_k=1,
                metadata_filter=metadata_filter,
                include_metadata=False,
                include_values=False
            )
            
            # Use a dummy vector for search (we only care about metadata filter)
            dummy_vector = [0.0] * stats.dimensions
            
            result = await self.search_similar(
                index_name=index_name,
                query_vector=dummy_vector,
                config=config,
                namespace=namespace
            )
            
            # This is an approximation - Pinecone doesn't provide exact filtered counts
            logger.warning("Filtered vector count is an approximation")
            return result.total_matches
            
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            raise VectorStorageException(f"Failed to count vectors: {e}")
    
    async def update_metadata(
        self,
        index_name: str,
        vector_id: VectorId,
        metadata: UnifiedVectorMetadata,
        namespace: Optional[str] = None
    ) -> VectorOperationResult:
        """Update metadata for an existing vector."""
        await self._ensure_initialized()
        
        try:
            # Get existing vector
            vector_values, _ = await self.get_vector(
                index_name=index_name,
                vector_id=vector_id,
                namespace=namespace,
                include_values=True,
                include_metadata=False
            )
            
            if vector_values is None:
                raise VectorNotFoundException(vector_id, index_name)
            
            # Update metadata by upserting with new metadata
            return await self.upsert_vector(
                index_name=index_name,
                vector_id=vector_id,
                vector=vector_values,
                metadata=metadata,
                namespace=namespace
            )
            
        except VectorNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update metadata for {vector_id}: {e}")
            raise VectorStorageException(f"Failed to update metadata: {e}")
    
    # Context Manager and Lifecycle
    
    async def close(self) -> None:
        """Clean up resources and close connections."""
        if not self._closed:
            try:
                await self.client.close()
                self._closed = True
                logger.info("Pinecone vector storage closed successfully")
            except Exception as e:
                logger.error(f"Error closing Pinecone vector storage: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_initialized()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup."""
        await self.close()
    
    # BatchVectorStorage Implementation
    
    async def upsert_vectors_chunked(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[UnifiedVectorMetadata]]],
        chunk_size: Optional[int] = None,
        max_parallel: int = 5,
        namespace: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """Upsert vectors with automatic chunking for large batches."""
        return await self.batch_processor.upsert_vectors_chunked(
            index_name=index_name,
            vectors=vectors,
            chunk_size=chunk_size,
            max_parallel=max_parallel,
            namespace=namespace,
            progress_callback=progress_callback
        )
    
    async def search_multiple_vectors(
        self,
        index_name: str,
        query_vectors: List[Vector],
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors using multiple query vectors."""
        return await self.query_engine.search_multiple_vectors(
            index_name=index_name,
            query_vectors=query_vectors,
            config=config,
            namespace=namespace
        )
    
    async def bulk_update_metadata(
        self,
        index_name: str,
        updates: List[tuple[VectorId, UnifiedVectorMetadata]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Update metadata for multiple vectors efficiently."""
        return await self.batch_processor.bulk_update_metadata(
            index_name=index_name,
            updates=updates,
            namespace=namespace,
            batch_size=batch_size
        )
    
    # StreamingVectorStorage Implementation
    
    async def stream_search_results(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, float, Optional[UnifiedVectorMetadata]]]:
        """Stream search results as they become available."""
        async for result in self.query_engine.stream_search_results(
            index_name=index_name,
            query_vector=query_vector,
            config=config,
            namespace=namespace
        ):
            yield result
    
    async def stream_vectors_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, Vector, UnifiedVectorMetadata]]:
        """Stream vectors matching metadata filter."""
        async for result in self.query_engine.stream_vectors_by_filter(
            index_name=index_name,
            metadata_filter=metadata_filter,
            namespace=namespace
        ):
            yield result
    
    # CacheableVectorStorage Implementation
    
    async def search_with_cache(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        cache_ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search with caching of results."""
        return await self.query_engine.search_with_cache(
            index_name=index_name,
            query_vector=query_vector,
            config=config,
            cache_ttl=cache_ttl,
            namespace=namespace
        )
    
    async def clear_search_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cached search results."""
        return await self.query_engine.clear_search_cache(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return await self.query_engine.get_cache_stats()
    
    # Helper Methods
    
    def _convert_metric_to_pinecone(self, metric: str) -> str:
        """Convert standard metric to Pinecone format."""
        metric_mapping = {
            DistanceMetric.COSINE: "cosine",
            DistanceMetric.EUCLIDEAN: "euclidean", 
            DistanceMetric.DOT_PRODUCT: "dotproduct"
        }
        return metric_mapping.get(metric, "cosine")
    
    def _convert_metadata_to_pinecone(self, metadata: UnifiedVectorMetadata) -> Dict[str, Any]:
        """Convert UnifiedVectorMetadata to Pinecone metadata format."""
        # Pinecone metadata must be flat key-value pairs
        pinecone_metadata = {
            "entity_id": metadata.entity_id,
            "entity_type": metadata.entity_type.value,
            "vector_id": metadata.vector_id,
            "index_name": metadata.index_name,
            "created_at": metadata.created_at.isoformat(),
            "version": metadata.version
        }
        
        # Add namespace if present
        if metadata.namespace:
            pinecone_metadata["namespace"] = metadata.namespace
        
        # Add embedding metadata
        if metadata.embedding:
            pinecone_metadata.update({
                "model_name": metadata.embedding.model_name,
                "model_provider": metadata.embedding.model_provider,
                "dimensions": metadata.embedding.dimensions,
                "quality_level": metadata.embedding.quality_level.value
            })
        
        # Add entity-specific metadata
        if metadata.company:
            pinecone_metadata.update({
                "company_name": metadata.company.company_name,
                "industry": metadata.company.industry or "",
                "size_category": metadata.company.size_category or "",
                "business_model": metadata.company.business_model or ""
            })
        
        # Add custom fields (ensure they're JSON serializable)
        for key, value in metadata.custom_fields.items():
            if isinstance(value, (str, int, float, bool)):
                pinecone_metadata[f"custom_{key}"] = value
        
        return pinecone_metadata
    
    def _convert_metadata_from_pinecone(self, pinecone_metadata: Dict[str, Any]) -> UnifiedVectorMetadata:
        """Convert Pinecone metadata back to UnifiedVectorMetadata."""
        # This is a simplified conversion - full implementation would reconstruct
        # the complete UnifiedVectorMetadata structure
        
        # For now, return a basic structure
        from datetime import datetime
        
        embedding_metadata = VectorEmbeddingMetadata(
            model_name=pinecone_metadata.get("model_name", "unknown"),
            model_provider=pinecone_metadata.get("model_provider", "unknown"),
            dimensions=pinecone_metadata.get("dimensions", 1536)
        )
        
        return UnifiedVectorMetadata(
            entity_id=pinecone_metadata.get("entity_id", ""),
            entity_type=VectorEntityType(pinecone_metadata.get("entity_type", "unknown")),
            vector_id=pinecone_metadata.get("vector_id", ""),
            embedding=embedding_metadata,
            index_name=pinecone_metadata.get("index_name", ""),
            namespace=pinecone_metadata.get("namespace"),
            created_at=datetime.fromisoformat(pinecone_metadata.get("created_at", datetime.utcnow().isoformat())),
            version=pinecone_metadata.get("version", 1)
        )
    
    def _convert_filter_to_pinecone(self, metadata_filter: MetadataFilter) -> Dict[str, Any]:
        """Convert metadata filter to Pinecone filter format."""
        # Simplified filter conversion - Pinecone uses specific filter syntax
        return metadata_filter
    
    async def _validate_vector_dimensions(self, index_name: str, vector: Vector) -> None:
        """Validate vector dimensions against index."""
        try:
            stats = await self.get_index_stats(index_name)
            if len(vector) != stats.dimensions:
                raise VectorDimensionMismatchException(
                    expected=stats.dimensions,
                    actual=len(vector),
                    index_name=index_name
                )
        except VectorIndexException:
            # If we can't get stats, assume dimensions are correct
            pass
    
    async def _get_index_dimensions(self, index_name: str) -> int:
        """Get dimensions for an index."""
        try:
            stats = await self.get_index_stats(index_name)
            return stats.dimensions
        except Exception:
            return self.config.default_dimensions
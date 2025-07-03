"""
Pinecone batch processing for efficient large-scale operations.

This module handles batch operations with optimal chunking,
parallel processing, and progress tracking.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor
import math

from src.core.domain.value_objects.vector_search_result import VectorOperationResult
from src.core.domain.value_objects.vector_metadata import UnifiedVectorMetadata
from src.core.ports.vector_storage import VectorId, Vector, ProgressCallback

from .config import PineconeConfig


logger = logging.getLogger(__name__)


class PineconeBatchProcessor:
    """Handles efficient batch operations for Pinecone vector storage."""
    
    def __init__(self, client, config: PineconeConfig):
        from .client import PineconeClient
        self.client: PineconeClient = client
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_parallel_requests)
        
        logger.info("Initialized Pinecone batch processor")
    
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[tuple[VectorId, Vector, Optional[UnifiedVectorMetadata]]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[ProgressCallback] = None
    ) -> VectorOperationResult:
        """Insert or update multiple vectors efficiently."""
        try:
            total_vectors = len(vectors)
            if total_vectors == 0:
                return VectorOperationResult.success_result(
                    operation="upsert_vectors_batch",
                    affected_count=0,
                    message="No vectors to upsert"
                )
            
            # Get index connection
            index = await self.client.get_index(index_name)
            
            # Process in batches
            batch_size = min(batch_size, self.config.batch_size)
            total_batches = math.ceil(total_vectors / batch_size)
            total_upserted = 0
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_vectors)
                batch_vectors = vectors[start_idx:end_idx]
                
                # Convert batch to Pinecone format
                pinecone_vectors = []
                for vector_id, vector_values, metadata in batch_vectors:
                    pinecone_metadata = self._convert_metadata_to_pinecone(metadata) if metadata else {}
                    pinecone_vectors.append((vector_id, vector_values, pinecone_metadata))
                
                # Upsert batch
                upsert_response = index.upsert(
                    vectors=pinecone_vectors,
                    namespace=namespace
                )
                
                batch_upserted = getattr(upsert_response, 'upserted_count', len(batch_vectors))
                total_upserted += batch_upserted
                
                # Report progress
                if progress_callback:
                    progress = ((batch_idx + 1) / total_batches) * 100
                    progress_callback(
                        f"Upserted batch {batch_idx + 1}/{total_batches}",
                        progress,
                        f"Processed {end_idx}/{total_vectors} vectors"
                    )
                
                # Small delay between batches to avoid rate limiting
                if batch_idx < total_batches - 1:
                    await asyncio.sleep(0.1)
            
            return VectorOperationResult.success_result(
                operation="upsert_vectors_batch",
                affected_count=total_upserted,
                message=f"Successfully upserted {total_upserted} vectors in {total_batches} batches"
            )
            
        except Exception as e:
            logger.error(f"Failed to upsert batch vectors: {e}")
            return VectorOperationResult.error_result(
                operation="upsert_vectors_batch",
                error=str(e),
                affected_count=total_upserted
            )
    
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
        try:
            total_vectors = len(vectors)
            if total_vectors == 0:
                return VectorOperationResult.success_result(
                    operation="upsert_vectors_chunked",
                    affected_count=0
                )
            
            # Calculate optimal chunk size
            if chunk_size is None:
                chunk_size = self._calculate_optimal_chunk_size(total_vectors, max_parallel)
            
            # Split into chunks
            chunks = [
                vectors[i:i + chunk_size] 
                for i in range(0, total_vectors, chunk_size)
            ]
            
            total_chunks = len(chunks)
            total_upserted = 0
            
            # Process chunks in parallel batches
            semaphore = asyncio.Semaphore(max_parallel)
            
            async def process_chunk(chunk_idx: int, chunk: List) -> int:
                async with semaphore:
                    result = await self.upsert_vectors_batch(
                        index_name=index_name,
                        vectors=chunk,
                        namespace=namespace,
                        batch_size=self.config.batch_size
                    )
                    
                    if progress_callback:
                        progress = ((chunk_idx + 1) / total_chunks) * 100
                        progress_callback(
                            f"Completed chunk {chunk_idx + 1}/{total_chunks}",
                            progress,
                            f"Processed {result.affected_count} vectors"
                        )
                    
                    return result.affected_count
            
            # Execute all chunks
            tasks = [
                process_chunk(idx, chunk) 
                for idx, chunk in enumerate(chunks)
            ]
            
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            for result in chunk_results:
                if isinstance(result, Exception):
                    logger.error(f"Chunk processing failed: {result}")
                else:
                    total_upserted += result
            
            return VectorOperationResult.success_result(
                operation="upsert_vectors_chunked",
                affected_count=total_upserted,
                message=f"Processed {total_vectors} vectors in {total_chunks} chunks"
            )
            
        except Exception as e:
            logger.error(f"Failed to upsert chunked vectors: {e}")
            return VectorOperationResult.error_result(
                operation="upsert_vectors_chunked",
                error=str(e)
            )
    
    async def get_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        include_values: bool = False,
        include_metadata: bool = True
    ) -> Dict[VectorId, tuple[Optional[Vector], Optional[UnifiedVectorMetadata]]]:
        """Retrieve multiple vectors by ID efficiently."""
        try:
            if not vector_ids:
                return {}
            
            # Get index connection
            index = await self.client.get_index(index_name)
            
            # Fetch in batches (Pinecone has fetch limits)
            batch_size = 100  # Pinecone fetch limit
            result = {}
            
            for i in range(0, len(vector_ids), batch_size):
                batch_ids = vector_ids[i:i + batch_size]
                
                fetch_response = index.fetch(
                    ids=batch_ids,
                    namespace=namespace
                )
                
                # Process response
                for vector_id in batch_ids:
                    if vector_id in fetch_response.vectors:
                        vector_data = fetch_response.vectors[vector_id]
                        
                        # Extract vector values
                        vector_values = vector_data.values if include_values else None
                        
                        # Convert metadata
                        metadata = None
                        if include_metadata and vector_data.metadata:
                            metadata = self._convert_metadata_from_pinecone(vector_data.metadata)
                        
                        result[vector_id] = (vector_values, metadata)
                    else:
                        result[vector_id] = (None, None)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get batch vectors: {e}")
            raise
    
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[VectorId],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Delete multiple vectors efficiently."""
        try:
            if not vector_ids:
                return VectorOperationResult.success_result(
                    operation="delete_vectors_batch",
                    affected_count=0
                )
            
            # Get index connection
            index = await self.client.get_index(index_name)
            
            # Delete in batches
            batch_size = min(batch_size, 1000)  # Pinecone delete limit
            total_deleted = 0
            
            for i in range(0, len(vector_ids), batch_size):
                batch_ids = vector_ids[i:i + batch_size]
                
                delete_response = index.delete(
                    ids=batch_ids,
                    namespace=namespace
                )
                
                total_deleted += len(batch_ids)
            
            return VectorOperationResult.success_result(
                operation="delete_vectors_batch",
                affected_count=total_deleted,
                message=f"Deleted {total_deleted} vectors"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete batch vectors: {e}")
            return VectorOperationResult.error_result(
                operation="delete_vectors_batch",
                error=str(e)
            )
    
    async def bulk_update_metadata(
        self,
        index_name: str,
        updates: List[tuple[VectorId, UnifiedVectorMetadata]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> VectorOperationResult:
        """Update metadata for multiple vectors efficiently."""
        try:
            if not updates:
                return VectorOperationResult.success_result(
                    operation="bulk_update_metadata",
                    affected_count=0
                )
            
            # For metadata updates, we need to fetch existing vectors and upsert with new metadata
            vector_ids = [vector_id for vector_id, _ in updates]
            
            # Get existing vectors with values
            existing_vectors = await self.get_vectors_batch(
                index_name=index_name,
                vector_ids=vector_ids,
                namespace=namespace,
                include_values=True,
                include_metadata=False
            )
            
            # Prepare upsert data with new metadata
            upsert_data = []
            for vector_id, new_metadata in updates:
                existing_vector, _ = existing_vectors.get(vector_id, (None, None))
                if existing_vector is not None:
                    upsert_data.append((vector_id, existing_vector, new_metadata))
            
            if not upsert_data:
                return VectorOperationResult.error_result(
                    operation="bulk_update_metadata",
                    error="No existing vectors found for metadata update"
                )
            
            # Perform batch upsert with new metadata
            return await self.upsert_vectors_batch(
                index_name=index_name,
                vectors=upsert_data,
                namespace=namespace,
                batch_size=batch_size
            )
            
        except Exception as e:
            logger.error(f"Failed to bulk update metadata: {e}")
            return VectorOperationResult.error_result(
                operation="bulk_update_metadata",
                error=str(e)
            )
    
    async def parallel_operations(
        self,
        operations: List[tuple[str, Dict[str, Any]]],
        max_parallel: int = 10
    ) -> List[VectorOperationResult]:
        """Execute multiple operations in parallel."""
        try:
            semaphore = asyncio.Semaphore(max_parallel)
            
            async def execute_operation(operation_type: str, kwargs: Dict[str, Any]) -> VectorOperationResult:
                async with semaphore:
                    if operation_type == "upsert_batch":
                        return await self.upsert_vectors_batch(**kwargs)
                    elif operation_type == "delete_batch":
                        return await self.delete_vectors_batch(**kwargs)
                    elif operation_type == "update_metadata":
                        return await self.bulk_update_metadata(**kwargs)
                    else:
                        return VectorOperationResult.error_result(
                            operation=operation_type,
                            error=f"Unknown operation type: {operation_type}"
                        )
            
            tasks = [
                execute_operation(op_type, kwargs) 
                for op_type, kwargs in operations
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error results
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    op_type, _ = operations[i]
                    final_results.append(
                        VectorOperationResult.error_result(
                            operation=op_type,
                            error=str(result)
                        )
                    )
                else:
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            logger.error(f"Failed to execute parallel operations: {e}")
            return [
                VectorOperationResult.error_result(
                    operation="parallel_operations",
                    error=str(e)
                )
            ]
    
    def _calculate_optimal_chunk_size(self, total_vectors: int, max_parallel: int) -> int:
        """Calculate optimal chunk size based on total vectors and parallelism."""
        # Aim for each chunk to have roughly equal work
        base_chunk_size = max(100, total_vectors // (max_parallel * 2))
        
        # Ensure chunk size doesn't exceed batch size limits
        max_chunk_size = self.config.batch_size * 10
        
        return min(base_chunk_size, max_chunk_size)
    
    def _convert_metadata_to_pinecone(self, metadata: UnifiedVectorMetadata) -> Dict[str, Any]:
        """Convert UnifiedVectorMetadata to Pinecone format."""
        pinecone_metadata = {
            "entity_id": metadata.entity_id,
            "entity_type": metadata.entity_type.value,
            "vector_id": metadata.vector_id,
            "index_name": metadata.index_name,
            "created_at": metadata.created_at.isoformat(),
            "version": metadata.version
        }
        
        if metadata.namespace:
            pinecone_metadata["namespace"] = metadata.namespace
        
        if metadata.embedding:
            pinecone_metadata.update({
                "model_name": metadata.embedding.model_name,
                "model_provider": metadata.embedding.model_provider,
                "dimensions": metadata.embedding.dimensions,
                "quality_level": metadata.embedding.quality_level.value
            })
        
        if metadata.company:
            pinecone_metadata.update({
                "company_name": metadata.company.company_name,
                "industry": metadata.company.industry or "",
                "size_category": metadata.company.size_category or "",
                "business_model": metadata.company.business_model or ""
            })
        
        # Add custom fields
        for key, value in metadata.custom_fields.items():
            if isinstance(value, (str, int, float, bool)):
                pinecone_metadata[f"custom_{key}"] = value
        
        return pinecone_metadata
    
    def _convert_metadata_from_pinecone(self, pinecone_metadata: Dict[str, Any]) -> UnifiedVectorMetadata:
        """Convert Pinecone metadata back to UnifiedVectorMetadata."""
        from datetime import datetime
        from src.core.domain.value_objects.vector_metadata import VectorEntityType, VectorEmbeddingMetadata
        
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
    
    async def get_batch_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for batch operations."""
        client_stats = self.client.get_stats()
        
        return {
            'total_operations': client_stats.total_requests,
            'success_rate': client_stats.get_success_rate(),
            'average_latency_ms': client_stats.avg_latency_ms,
            'cache_hit_rate': client_stats.get_cache_hit_rate(),
            'configuration': {
                'max_parallel_requests': self.config.max_parallel_requests,
                'default_batch_size': self.config.batch_size,
                'connection_pool_size': self.config.connection_pool_size
            }
        }
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
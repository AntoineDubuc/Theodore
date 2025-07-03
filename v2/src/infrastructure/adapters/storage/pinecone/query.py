"""
Pinecone query engine for advanced search and filtering operations.

This module provides sophisticated query capabilities including
similarity search, metadata filtering, and streaming results.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple
import json
import time
import hashlib

from src.core.domain.value_objects.vector_search_result import (
    VectorSearchConfig, VectorSearchResult, VectorSearchMatch, VectorMetadata
)
from src.core.domain.value_objects.vector_metadata import UnifiedVectorMetadata, VectorEntityType
from src.core.ports.vector_storage import VectorId, Vector, MetadataFilter

from .config import PineconeConfig


logger = logging.getLogger(__name__)


class PineconeQueryEngine:
    """Advanced query engine for Pinecone vector operations."""
    
    def __init__(self, client, config: PineconeConfig):
        from .client import PineconeClient
        self.client: PineconeClient = client
        self.config = config
        
        # Search result cache
        self._search_cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_enabled = config.enable_caching
        self._cache_ttl = config.cache_ttl
        
        logger.info("Initialized Pinecone query engine")
    
    async def search_similar(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search for similar vectors using a query vector."""
        try:
            start_time = time.time()
            
            # Get index connection
            index = await self.client.get_index(index_name)
            
            # Build query parameters
            query_params = {
                'vector': query_vector,
                'top_k': config.top_k,
                'include_metadata': config.include_metadata,
                'include_values': config.include_values,
                'namespace': namespace
            }
            
            # Add metadata filter if specified
            if config.metadata_filter:
                query_params['filter'] = self._convert_filter_to_pinecone(config.metadata_filter)
            
            # Execute search
            search_response = index.query(**query_params)
            
            # Process results
            matches = []
            for idx, match in enumerate(search_response.matches):
                # Apply similarity threshold if specified
                if config.similarity_threshold and match.score < config.similarity_threshold:
                    continue
                
                # Convert metadata
                metadata = None
                if config.include_metadata and match.metadata:
                    metadata = self._convert_metadata_from_pinecone(match.metadata)
                
                # Create search match
                search_match = VectorSearchMatch(
                    vector_id=match.id,
                    entity_id=match.metadata.get('entity_id', match.id) if match.metadata else match.id,
                    similarity_score=match.score,
                    distance=1.0 - match.score,  # Convert score to distance
                    metadata=self._create_vector_metadata(match.metadata) if match.metadata else None,
                    vector_values=match.values if config.include_values else None,
                    rank=idx + 1,
                    namespace=namespace
                )
                matches.append(search_match)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Create search result
            result = VectorSearchResult(
                query_vector=query_vector if config.include_values else None,
                config=config,
                matches=matches,
                total_matches=len(matches),
                search_time_ms=search_time_ms,
                index_name=index_name,
                namespace=namespace
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            raise
    
    async def search_multiple_vectors(
        self,
        index_name: str,
        query_vectors: List[Vector],
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors using multiple query vectors."""
        try:
            # Execute searches in parallel
            semaphore = asyncio.Semaphore(self.config.max_parallel_requests)
            
            async def search_single(query_vector: Vector) -> VectorSearchResult:
                async with semaphore:
                    return await self.search_similar(
                        index_name=index_name,
                        query_vector=query_vector,
                        config=config,
                        namespace=namespace
                    )
            
            tasks = [search_single(qv) for qv in query_vectors]
            results = await asyncio.gather(*tasks)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search multiple vectors: {e}")
            raise
    
    async def search_by_metadata(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        limit: int = 100,
        offset: int = 0,
        namespace: Optional[str] = None
    ) -> List[tuple[VectorId, UnifiedVectorMetadata]]:
        """Search vectors by metadata only (no similarity)."""
        try:
            # Pinecone doesn't have direct metadata-only search
            # We use a dummy vector with filter-only search
            index = await self.client.get_index(index_name)
            
            # Get index dimensions for dummy vector
            index_stats = await self.client.get_index_stats(index_name)
            dummy_vector = [0.0] * index_stats.dimensions
            
            # Search with metadata filter
            query_params = {
                'vector': dummy_vector,
                'top_k': min(limit, 10000),  # Pinecone limit
                'include_metadata': True,
                'include_values': False,
                'filter': self._convert_filter_to_pinecone(metadata_filter),
                'namespace': namespace
            }
            
            search_response = index.query(**query_params)
            
            # Extract results with offset
            results = []
            for i, match in enumerate(search_response.matches):
                if i < offset:
                    continue
                if len(results) >= limit:
                    break
                
                metadata = self._convert_metadata_from_pinecone(match.metadata) if match.metadata else None
                results.append((match.id, metadata))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search by metadata: {e}")
            raise
    
    async def search_with_cache(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        cache_ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Search with caching of results."""
        if not self._cache_enabled:
            return await self.search_similar(index_name, query_vector, config, namespace)
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            index_name, query_vector, config, namespace
        )
        
        # Check cache
        cached_result = self._get_from_cache(cache_key, cache_ttl)
        if cached_result:
            return cached_result
        
        # Execute search
        result = await self.search_similar(index_name, query_vector, config, namespace)
        
        # Cache result
        self._set_cache(cache_key, result)
        
        return result
    
    async def stream_search_results(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, float, Optional[UnifiedVectorMetadata]]]:
        """Stream search results as they become available."""
        try:
            # For Pinecone, we get all results at once and stream them
            # This simulates streaming for interface compatibility
            result = await self.search_similar(index_name, query_vector, config, namespace)
            
            for match in result.matches:
                # Convert metadata back to UnifiedVectorMetadata
                unified_metadata = None
                if match.metadata and hasattr(match.metadata, 'custom_fields'):
                    # This would need proper conversion logic
                    pass
                
                yield match.vector_id, match.similarity_score, unified_metadata
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Failed to stream search results: {e}")
            raise
    
    async def stream_vectors_by_filter(
        self,
        index_name: str,
        metadata_filter: MetadataFilter,
        namespace: Optional[str] = None
    ) -> AsyncIterator[tuple[VectorId, Vector, UnifiedVectorMetadata]]:
        """Stream vectors matching metadata filter."""
        try:
            # Get vectors by metadata search
            metadata_results = await self.search_by_metadata(
                index_name=index_name,
                metadata_filter=metadata_filter,
                limit=10000,  # Stream in chunks
                namespace=namespace
            )
            
            # Get vector values for each result
            index = await self.client.get_index(index_name)
            
            for vector_id, metadata in metadata_results:
                # Fetch vector values
                fetch_response = index.fetch(ids=[vector_id], namespace=namespace)
                
                if vector_id in fetch_response.vectors:
                    vector_data = fetch_response.vectors[vector_id]
                    yield vector_id, vector_data.values, metadata
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Failed to stream vectors by filter: {e}")
            raise
    
    async def clear_search_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cached search results."""
        if not self._cache_enabled:
            return 0
        
        if pattern is None:
            # Clear all cache
            cleared_count = len(self._search_cache)
            self._search_cache.clear()
            return cleared_count
        
        # Clear cache entries matching pattern
        keys_to_remove = [
            key for key in self._search_cache.keys()
            if pattern in key
        ]
        
        for key in keys_to_remove:
            del self._search_cache[key]
        
        return len(keys_to_remove)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        if not self._cache_enabled:
            return {'cache_enabled': False}
        
        total_size = len(self._search_cache)
        
        # Calculate cache size in memory (approximate)
        cache_size_bytes = sum(
            len(json.dumps(result, default=str))
            for result, _ in self._search_cache.values()
        )
        
        # Get hit rate from client stats
        client_stats = self.client.get_stats()
        
        return {
            'cache_enabled': True,
            'total_entries': total_size,
            'cache_size_bytes': cache_size_bytes,
            'cache_size_mb': cache_size_bytes / (1024 * 1024),
            'cache_hit_rate': client_stats.get_cache_hit_rate(),
            'cache_hits': client_stats.cache_hits,
            'cache_misses': client_stats.cache_misses,
            'max_cache_size': self.config.max_cache_size,
            'cache_ttl_seconds': self._cache_ttl
        }
    
    def _convert_filter_to_pinecone(self, metadata_filter: MetadataFilter) -> Dict[str, Any]:
        """Convert metadata filter to Pinecone filter format."""
        # Pinecone uses specific filter syntax
        # This is a simplified conversion - production would need full implementation
        
        if isinstance(metadata_filter, dict):
            # Handle simple key-value filters
            pinecone_filter = {}
            
            for key, value in metadata_filter.items():
                if key.startswith('$'):
                    # Logical operators
                    if key == '$and':
                        pinecone_filter['$and'] = [
                            self._convert_filter_to_pinecone(f) for f in value
                        ]
                    elif key == '$or':
                        pinecone_filter['$or'] = [
                            self._convert_filter_to_pinecone(f) for f in value
                        ]
                else:
                    # Field filters
                    if isinstance(value, dict):
                        # Operator filters like {'$gt': 5}
                        pinecone_filter[key] = value
                    else:
                        # Simple equality
                        pinecone_filter[key] = {'$eq': value}
            
            return pinecone_filter
        
        return metadata_filter
    
    def _convert_metadata_from_pinecone(self, pinecone_metadata: Dict[str, Any]) -> UnifiedVectorMetadata:
        """Convert Pinecone metadata back to UnifiedVectorMetadata."""
        from datetime import datetime
        from src.core.domain.value_objects.vector_metadata import VectorEmbeddingMetadata
        
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
    
    def _create_vector_metadata(self, pinecone_metadata: Dict[str, Any]) -> VectorMetadata:
        """Create VectorMetadata from Pinecone metadata."""
        from datetime import datetime
        
        return VectorMetadata(
            entity_id=pinecone_metadata.get("entity_id", ""),
            entity_type=pinecone_metadata.get("entity_type", "unknown"),
            vector_dimensions=pinecone_metadata.get("dimensions", 1536),
            embedding_model=pinecone_metadata.get("model_name"),
            embedding_provider=pinecone_metadata.get("model_provider"),
            created_at=datetime.fromisoformat(
                pinecone_metadata.get("created_at", datetime.utcnow().isoformat())
            )
        )
    
    def _generate_cache_key(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        namespace: Optional[str]
    ) -> str:
        """Generate cache key for search parameters."""
        # Create hash of query vector for efficiency
        vector_hash = hashlib.md5(json.dumps(query_vector).encode()).hexdigest()[:8]
        
        cache_data = {
            'index': index_name,
            'vector_hash': vector_hash,
            'top_k': config.top_k,
            'threshold': config.similarity_threshold,
            'metric': config.distance_metric,
            'include_metadata': config.include_metadata,
            'include_values': config.include_values,
            'filter': config.metadata_filter,
            'namespace': namespace
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str, cache_ttl: Optional[int] = None) -> Optional[VectorSearchResult]:
        """Get result from cache if valid."""
        if cache_key not in self._search_cache:
            return None
        
        result, timestamp = self._search_cache[cache_key]
        ttl = cache_ttl if cache_ttl is not None else self._cache_ttl
        
        if time.time() - timestamp > ttl:
            del self._search_cache[cache_key]
            return None
        
        return result
    
    def _set_cache(self, cache_key: str, result: VectorSearchResult) -> None:
        """Set result in cache."""
        # Clean old entries if cache is full
        if len(self._search_cache) >= self.config.max_cache_size:
            oldest_key = min(self._search_cache.keys(), key=lambda k: self._search_cache[k][1])
            del self._search_cache[oldest_key]
        
        self._search_cache[cache_key] = (result, time.time())
    
    async def advanced_similarity_search(
        self,
        index_name: str,
        query_vector: Vector,
        config: VectorSearchConfig,
        rerank_function: Optional[callable] = None,
        namespace: Optional[str] = None
    ) -> VectorSearchResult:
        """Advanced similarity search with custom reranking."""
        try:
            # Perform initial search with higher top_k for reranking
            initial_config = VectorSearchConfig(
                top_k=min(config.top_k * 3, 1000),  # Get more results for reranking
                similarity_threshold=max(config.similarity_threshold - 0.1, 0.0) if config.similarity_threshold else None,
                distance_metric=config.distance_metric,
                include_metadata=config.include_metadata,
                include_values=config.include_values,
                metadata_filter=config.metadata_filter,
                namespace=config.namespace
            )
            
            initial_result = await self.search_similar(
                index_name=index_name,
                query_vector=query_vector,
                config=initial_config,
                namespace=namespace
            )
            
            # Apply custom reranking if provided
            if rerank_function and initial_result.matches:
                reranked_matches = await rerank_function(query_vector, initial_result.matches)
                initial_result.matches = reranked_matches[:config.top_k]
                initial_result.total_matches = len(reranked_matches)
            
            # Apply final similarity threshold
            if config.similarity_threshold:
                filtered_matches = [
                    match for match in initial_result.matches
                    if match.similarity_score >= config.similarity_threshold
                ]
                initial_result.matches = filtered_matches[:config.top_k]
                initial_result.total_matches = len(filtered_matches)
            
            return initial_result
            
        except Exception as e:
            logger.error(f"Failed advanced similarity search: {e}")
            raise
    
    async def get_query_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for query operations."""
        client_stats = self.client.get_stats()
        cache_stats = await self.get_cache_stats()
        
        return {
            'query_performance': {
                'total_searches': client_stats.total_requests,
                'success_rate': client_stats.get_success_rate(),
                'average_latency_ms': client_stats.avg_latency_ms,
                'failed_searches': client_stats.failed_requests
            },
            'cache_performance': cache_stats,
            'configuration': {
                'max_parallel_requests': self.config.max_parallel_requests,
                'cache_enabled': self._cache_enabled,
                'cache_ttl': self._cache_ttl
            }
        }
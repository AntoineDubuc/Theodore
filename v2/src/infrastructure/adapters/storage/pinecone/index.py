"""
Pinecone index management and optimization.

This module handles index lifecycle management, configuration,
and optimization strategies for Pinecone vector storage.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from src.core.domain.value_objects.vector_search_result import VectorOperationResult, IndexStats

from .config import PineconeConfig, PineconeIndexConfig


logger = logging.getLogger(__name__)


class PineconeIndexManager:
    """Manages Pinecone index operations and optimization."""
    
    def __init__(self, client, config: PineconeConfig):
        from .client import PineconeClient
        self.client: PineconeClient = client
        self.config = config
        self._index_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("Initialized Pinecone index manager")
    
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = "cosine",
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        """Create a new Pinecone index with optimization."""
        try:
            # Check if index already exists
            if await self.client.index_exists(index_name):
                return VectorOperationResult.error_result(
                    operation="create_index",
                    error=f"Index {index_name} already exists"
                )
            
            # Prepare index configuration
            index_config = {
                'dimension': dimensions,
                'metric': metric,
            }
            
            # Add pod configuration for performance
            pod_config = self._get_optimal_pod_config(dimensions, **kwargs)
            index_config.update(pod_config)
            
            # Add metadata configuration if provided
            if metadata_config:
                index_config['metadata_config'] = metadata_config
            
            # Create the index
            result = await self.client.create_index(
                index_name=index_name,
                **index_config
            )
            
            # Clear cache to force refresh
            self._clear_index_cache(index_name)
            
            logger.info(f"Created Pinecone index: {index_name} with {dimensions} dimensions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return VectorOperationResult.error_result(
                operation="create_index",
                error=str(e)
            )
    
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """Delete a Pinecone index."""
        try:
            # Check if index exists
            if not await self.client.index_exists(index_name):
                return VectorOperationResult.error_result(
                    operation="delete_index",
                    error=f"Index {index_name} does not exist"
                )
            
            # Delete the index
            result = await self.client.delete_index(index_name)
            
            # Clear cache
            self._clear_index_cache(index_name)
            
            logger.info(f"Deleted Pinecone index: {index_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return VectorOperationResult.error_result(
                operation="delete_index",
                error=str(e)
            )
    
    async def get_index_stats(self, index_name: str) -> IndexStats:
        """Get comprehensive statistics for an index."""
        try:
            # Check cache first
            cached_stats = self._get_cached_stats(index_name)
            if cached_stats:
                return cached_stats
            
            # Get index description from Pinecone
            client = self.client._client
            index_description = client.describe_index(index_name)
            
            # Get index for stats
            index = await self.client.get_index(index_name)
            
            # Get index statistics
            stats_response = index.describe_index_stats()
            
            # Create IndexStats object
            index_stats = IndexStats(
                name=index_name,
                total_vectors=stats_response.total_vector_count,
                dimensions=index_description.dimension,
                namespaces=list(stats_response.namespaces.keys()) if stats_response.namespaces else [],
                created_at=self._parse_index_creation_date(index_description),
                metadata={
                    'metric': index_description.metric,
                    'pod_type': getattr(index_description, 'pod_type', 'unknown'),
                    'pods': getattr(index_description, 'pods', 1),
                    'replicas': getattr(index_description, 'replicas', 1),
                    'status': index_description.status.state if hasattr(index_description, 'status') else 'unknown'
                }
            )
            
            # Add namespace details
            if stats_response.namespaces:
                for namespace, ns_stats in stats_response.namespaces.items():
                    index_stats.metadata[f'namespace_{namespace}_vectors'] = ns_stats.vector_count
            
            # Cache the stats
            self._cache_stats(index_name, index_stats)
            
            return index_stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for index {index_name}: {e}")
            raise
    
    async def optimize_index(self, index_name: str) -> VectorOperationResult:
        """Optimize index performance and configuration."""
        try:
            stats = await self.get_index_stats(index_name)
            
            optimization_actions = []
            
            # Analyze index size and suggest optimizations
            if stats.total_vectors > 1000000:  # 1M+ vectors
                optimization_actions.append("Consider using p2 pod type for better performance")
            
            if len(stats.namespaces) > 10:
                optimization_actions.append("Consider consolidating namespaces for better performance")
            
            # Check for empty namespaces
            empty_namespaces = []
            for namespace in stats.namespaces:
                if stats.metadata.get(f'namespace_{namespace}_vectors', 0) == 0:
                    empty_namespaces.append(namespace)
            
            if empty_namespaces:
                optimization_actions.append(f"Consider removing empty namespaces: {empty_namespaces}")
            
            return VectorOperationResult.success_result(
                operation="optimize_index",
                message="Index optimization analysis completed",
                metadata={
                    'optimizations': optimization_actions,
                    'current_performance': {
                        'total_vectors': stats.total_vectors,
                        'namespaces_count': len(stats.namespaces),
                        'pod_type': stats.metadata.get('pod_type', 'unknown')
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to optimize index {index_name}: {e}")
            return VectorOperationResult.error_result(
                operation="optimize_index",
                error=str(e)
            )
    
    async def backup_index_metadata(self, index_name: str) -> Dict[str, Any]:
        """Backup index metadata and configuration."""
        try:
            stats = await self.get_index_stats(index_name)
            
            backup_data = {
                'index_name': index_name,
                'backup_timestamp': datetime.utcnow().isoformat(),
                'configuration': {
                    'dimensions': stats.dimensions,
                    'metric': stats.metadata.get('metric', 'cosine'),
                    'pod_type': stats.metadata.get('pod_type'),
                    'pods': stats.metadata.get('pods'),
                    'replicas': stats.metadata.get('replicas')
                },
                'statistics': {
                    'total_vectors': stats.total_vectors,
                    'namespaces': stats.namespaces,
                    'created_at': stats.created_at.isoformat() if stats.created_at else None
                }
            }
            
            logger.info(f"Backed up metadata for index: {index_name}")
            return backup_data
            
        except Exception as e:
            logger.error(f"Failed to backup metadata for index {index_name}: {e}")
            raise
    
    async def validate_index_health(self, index_name: str) -> Dict[str, Any]:
        """Validate index health and performance."""
        try:
            stats = await self.get_index_stats(index_name)
            
            health_report = {
                'index_name': index_name,
                'status': 'healthy',
                'checks': [],
                'warnings': [],
                'errors': []
            }
            
            # Check if index is accessible
            try:
                index = await self.client.get_index(index_name)
                health_report['checks'].append("Index accessibility: PASS")
            except Exception as e:
                health_report['errors'].append(f"Index accessibility: FAIL - {e}")
                health_report['status'] = 'unhealthy'
            
            # Check vector count
            if stats.total_vectors == 0:
                health_report['warnings'].append("Index is empty (no vectors)")
            else:
                health_report['checks'].append(f"Vector count: {stats.total_vectors}")
            
            # Check namespace distribution
            if len(stats.namespaces) > 20:
                health_report['warnings'].append(f"High namespace count ({len(stats.namespaces)})")
            
            # Check index age
            if stats.created_at:
                age_days = (datetime.utcnow() - stats.created_at).days
                if age_days > 365:
                    health_report['warnings'].append(f"Index is {age_days} days old")
            
            return health_report
            
        except Exception as e:
            logger.error(f"Failed to validate health for index {index_name}: {e}")
            return {
                'index_name': index_name,
                'status': 'error',
                'errors': [str(e)]
            }
    
    def _get_optimal_pod_config(self, dimensions: int, **kwargs) -> Dict[str, Any]:
        """Get optimal pod configuration based on requirements."""
        pod_config = {}
        
        # Default pod configuration
        if dimensions <= 768:
            pod_config['pod_type'] = 'p1.x1'
        elif dimensions <= 1536:
            pod_config['pod_type'] = 'p1.x2'
        else:
            pod_config['pod_type'] = 'p1.x4'
        
        # Override with user-provided values
        pod_config.update({
            k: v for k, v in kwargs.items() 
            if k in ['pod_type', 'pods', 'replicas']
        })
        
        # Ensure minimum configuration
        pod_config.setdefault('pods', 1)
        pod_config.setdefault('replicas', 1)
        
        return pod_config
    
    def _get_cached_stats(self, index_name: str) -> Optional[IndexStats]:
        """Get cached index statistics if valid."""
        if index_name not in self._index_cache:
            return None
        
        cache_entry = self._index_cache[index_name]
        if time.time() - cache_entry['timestamp'] > self._cache_ttl:
            del self._index_cache[index_name]
            return None
        
        return cache_entry['stats']
    
    def _cache_stats(self, index_name: str, stats: IndexStats) -> None:
        """Cache index statistics."""
        self._index_cache[index_name] = {
            'stats': stats,
            'timestamp': time.time()
        }
    
    def _clear_index_cache(self, index_name: str) -> None:
        """Clear cached data for an index."""
        if index_name in self._index_cache:
            del self._index_cache[index_name]
    
    def _parse_index_creation_date(self, index_description) -> Optional[datetime]:
        """Parse index creation date from description."""
        try:
            # Pinecone doesn't always provide creation date
            # This is a placeholder for when it becomes available
            if hasattr(index_description, 'created_at'):
                return datetime.fromisoformat(index_description.created_at)
            return None
        except Exception:
            return None
    
    async def list_index_configurations(self) -> Dict[str, Dict[str, Any]]:
        """List configurations for all indexes."""
        try:
            indexes = await self.client.list_indexes()
            configurations = {}
            
            for index_name in indexes:
                try:
                    stats = await self.get_index_stats(index_name)
                    configurations[index_name] = {
                        'dimensions': stats.dimensions,
                        'total_vectors': stats.total_vectors,
                        'namespaces_count': len(stats.namespaces),
                        'configuration': stats.metadata
                    }
                except Exception as e:
                    configurations[index_name] = {'error': str(e)}
            
            return configurations
            
        except Exception as e:
            logger.error(f"Failed to list index configurations: {e}")
            return {}
    
    async def cleanup_empty_namespaces(self, index_name: str) -> VectorOperationResult:
        """Clean up empty namespaces in an index."""
        try:
            stats = await self.get_index_stats(index_name)
            
            empty_namespaces = []
            for namespace in stats.namespaces:
                vector_count = stats.metadata.get(f'namespace_{namespace}_vectors', 0)
                if vector_count == 0:
                    empty_namespaces.append(namespace)
            
            if not empty_namespaces:
                return VectorOperationResult.success_result(
                    operation="cleanup_empty_namespaces",
                    message="No empty namespaces found"
                )
            
            # Note: Pinecone doesn't have direct namespace deletion
            # This would require deleting all vectors in the namespace
            logger.info(f"Found {len(empty_namespaces)} empty namespaces in {index_name}")
            
            return VectorOperationResult.success_result(
                operation="cleanup_empty_namespaces",
                message=f"Identified {len(empty_namespaces)} empty namespaces",
                metadata={'empty_namespaces': empty_namespaces}
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup empty namespaces: {e}")
            return VectorOperationResult.error_result(
                operation="cleanup_empty_namespaces",
                error=str(e)
            )
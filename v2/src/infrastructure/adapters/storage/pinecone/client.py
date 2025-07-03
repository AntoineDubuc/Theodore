"""
Pinecone client implementation with connection management.

This module provides the core Pinecone client with connection pooling,
retry logic, and error handling for reliable vector operations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager
import time
from dataclasses import dataclass
import json

try:
    import pinecone
    from pinecone import Pinecone, Index
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone = None
    Pinecone = None
    Index = None

from .config import PineconeConfig, PineconeCredentials, PineconeConnectionPool
from src.core.domain.value_objects.vector_search_result import VectorOperationResult


logger = logging.getLogger(__name__)


@dataclass
class PineconeClientStats:
    """Statistics for Pinecone client operations."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def add_request(self, latency_ms: float, success: bool = True):
        """Add request statistics."""
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.total_requests
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100


class PineconeRetryPolicy:
    """Retry policy for Pinecone operations."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if operation should be retried."""
        if attempt >= self.max_retries:
            return False
        
        # Retry on network errors, timeouts, and service unavailable
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return True
        
        # Check for specific Pinecone errors that are retryable
        error_msg = str(exception).lower()
        retryable_errors = [
            'timeout', 'connection', 'service unavailable',
            'rate limit', 'throttled', 'temporary'
        ]
        
        return any(error in error_msg for error in retryable_errors)
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for retry attempt with exponential backoff."""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)


class PineconeClient:
    """Enhanced Pinecone client with enterprise features."""
    
    def __init__(self, config: PineconeConfig):
        if not PINECONE_AVAILABLE:
            raise RuntimeError("Pinecone library not available. Install with: pip install pinecone-client")
        
        self.config = config
        self.credentials = PineconeCredentials.from_env()
        self.retry_policy = PineconeRetryPolicy(
            max_retries=config.max_retries,
            base_delay=config.retry_delay
        )
        self.stats = PineconeClientStats()
        
        # Initialize Pinecone client
        self._client: Optional[Pinecone] = None
        self._indexes: Dict[str, Index] = {}
        self._connection_pool = PineconeConnectionPool(
            max_connections=config.connection_pool_size
        )
        
        # Cache for results
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_enabled = config.enable_caching
        self._cache_ttl = config.cache_ttl
        
        logger.info(f"Initialized Pinecone client for environment: {config.environment}")
    
    async def initialize(self) -> None:
        """Initialize Pinecone connection."""
        try:
            if not self.credentials.validate():
                raise ValueError("Invalid Pinecone credentials")
            
            self._client = Pinecone(
                api_key=self.credentials.api_key,
                environment=self.credentials.environment
            )
            
            logger.info("Pinecone client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise
    
    async def close(self) -> None:
        """Close Pinecone connections and cleanup resources."""
        try:
            self._indexes.clear()
            self._client = None
            self._cache.clear()
            logger.info("Pinecone client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Pinecone client: {e}")
    
    def _ensure_initialized(self) -> None:
        """Ensure client is initialized."""
        if self._client is None:
            raise RuntimeError("Pinecone client not initialized. Call initialize() first.")
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation."""
        key_data = {'op': operation, **kwargs}
        return json.dumps(key_data, sort_keys=True)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get result from cache if valid."""
        if not self._cache_enabled or cache_key not in self._cache:
            self.stats.cache_misses += 1
            return None
        
        result, timestamp = self._cache[cache_key]
        if time.time() - timestamp > self._cache_ttl:
            del self._cache[cache_key]
            self.stats.cache_misses += 1
            return None
        
        self.stats.cache_hits += 1
        return result
    
    def _set_cache(self, cache_key: str, result: Any) -> None:
        """Set result in cache."""
        if not self._cache_enabled:
            return
        
        # Clean old entries if cache is full
        if len(self._cache) >= self.config.max_cache_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[cache_key] = (result, time.time())
    
    async def _execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
        """Execute operation with retry logic."""
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                result = await operation_func(*args, **kwargs)
                
                # Record successful operation
                latency_ms = (time.time() - start_time) * 1000
                self.stats.add_request(latency_ms, success=True)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.retry_policy.should_retry(attempt, e):
                    break
                
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    logger.warning(
                        f"Operation {operation_name} failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        # Record failed operation
        latency_ms = (time.time() - start_time) * 1000
        self.stats.add_request(latency_ms, success=False)
        
        logger.error(f"Operation {operation_name} failed after {self.retry_policy.max_retries + 1} attempts")
        raise last_exception
    
    async def get_index(self, index_name: str) -> Index:
        """Get or create index connection."""
        self._ensure_initialized()
        
        if index_name not in self._indexes:
            try:
                index = self._client.Index(index_name)
                self._indexes[index_name] = index
                logger.debug(f"Connected to Pinecone index: {index_name}")
            except Exception as e:
                logger.error(f"Failed to connect to index {index_name}: {e}")
                raise
        
        return self._indexes[index_name]
    
    async def list_indexes(self) -> List[str]:
        """List all available indexes."""
        self._ensure_initialized()
        
        cache_key = self._get_cache_key("list_indexes")
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        async def _list_indexes():
            indexes_info = self._client.list_indexes()
            return [idx.name for idx in indexes_info.indexes]
        
        result = await self._execute_with_retry("list_indexes", _list_indexes)
        self._set_cache(cache_key, result)
        return result
    
    async def create_index(self, index_name: str, dimension: int, metric: str = "cosine", **kwargs) -> VectorOperationResult:
        """Create a new Pinecone index."""
        self._ensure_initialized()
        
        async def _create_index():
            spec = {
                'name': index_name,
                'dimension': dimension,
                'metric': metric,
                **kwargs
            }
            
            self._client.create_index(**spec)
            
            # Wait for index to be ready
            await self._wait_for_index_ready(index_name)
            
            return VectorOperationResult.success_result(
                operation="create_index",
                message=f"Index {index_name} created successfully"
            )
        
        return await self._execute_with_retry("create_index", _create_index)
    
    async def delete_index(self, index_name: str) -> VectorOperationResult:
        """Delete a Pinecone index."""
        self._ensure_initialized()
        
        async def _delete_index():
            self._client.delete_index(index_name)
            
            # Remove from local cache
            if index_name in self._indexes:
                del self._indexes[index_name]
            
            return VectorOperationResult.success_result(
                operation="delete_index",
                message=f"Index {index_name} deleted successfully"
            )
        
        return await self._execute_with_retry("delete_index", _delete_index)
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if index exists."""
        try:
            indexes = await self.list_indexes()
            return index_name in indexes
        except Exception as e:
            logger.error(f"Error checking if index {index_name} exists: {e}")
            return False
    
    async def _wait_for_index_ready(self, index_name: str, timeout: float = 300.0) -> None:
        """Wait for index to become ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                index_info = self._client.describe_index(index_name)
                if index_info.status.ready:
                    logger.info(f"Index {index_name} is ready")
                    return
                    
                logger.debug(f"Waiting for index {index_name} to be ready...")
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking index status: {e}")
                await asyncio.sleep(5)
        
        raise TimeoutError(f"Index {index_name} not ready after {timeout}s")
    
    def get_stats(self) -> PineconeClientStats:
        """Get client statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset client statistics."""
        self.stats = PineconeClientStats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Pinecone connection."""
        try:
            self._ensure_initialized()
            
            # Test basic connectivity
            start_time = time.time()
            indexes = await self.list_indexes()
            latency = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'latency_ms': latency,
                'indexes_count': len(indexes),
                'connection_stats': {
                    'total_requests': self.stats.total_requests,
                    'success_rate': self.stats.get_success_rate(),
                    'avg_latency_ms': self.stats.avg_latency_ms
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_stats': {
                    'total_requests': self.stats.total_requests,
                    'success_rate': self.stats.get_success_rate()
                }
            }
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection with automatic resource management."""
        try:
            if self._client is None:
                await self.initialize()
            yield self
        finally:
            # Connection cleanup is handled by the connection pool
            pass
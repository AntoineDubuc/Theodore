"""
Embedding provider port interfaces for Theodore.

This module defines the contracts for text embedding providers,
supporting single and batch embedding generation with comprehensive
cost tracking and quality metrics.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncIterator
import asyncio
from contextlib import asynccontextmanager

from src.core.domain.value_objects.ai_config import EmbeddingConfig, ModelInfo
from src.core.domain.value_objects.ai_response import EmbeddingResult, AnalysisError
from src.core.ports.progress import ProgressTracker


# Type aliases for cleaner signatures
from typing import Callable
ProgressCallback = Callable[[str, float, Optional[str]], None]
EmbeddingVector = List[float]


class EmbeddingProviderException(Exception):
    """Base exception for all embedding provider errors"""
    pass


class EmbeddingRateLimitedException(EmbeddingProviderException):
    """Raised when rate limited by embedding provider"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after
        message = f"Rate limited by {provider}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message)


class EmbeddingQuotaExceededException(EmbeddingProviderException):
    """Raised when embedding quota is exceeded"""
    
    def __init__(self, provider: str, quota_type: str = "embeddings"):
        self.provider = provider
        self.quota_type = quota_type
        super().__init__(f"Embedding quota exceeded for {provider}: {quota_type}")


class EmbeddingModelNotAvailableException(EmbeddingProviderException):
    """Raised when requested embedding model is not available"""
    
    def __init__(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name
        super().__init__(f"Embedding model {model_name} not available on {provider}")


class InvalidEmbeddingConfigException(EmbeddingProviderException):
    """Raised when embedding configuration is invalid"""
    
    def __init__(self, message: str, config_field: Optional[str] = None):
        self.config_field = config_field
        super().__init__(message)


class EmbeddingDimensionMismatchException(EmbeddingProviderException):
    """Raised when embedding dimensions don't match expectations"""
    
    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(f"Expected {expected} dimensions, got {actual}")


class EmbeddingProvider(ABC):
    """
    Port interface for text embedding providers.
    
    This interface defines the contract for all embedding generation adapters,
    from simple single embeddings to batch processing with progress tracking.
    """
    
    @abstractmethod
    async def get_embedding(
        self,
        text: str,
        config: EmbeddingConfig,
        progress_callback: Optional[ProgressCallback] = None
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            config: Embedding configuration
            progress_callback: Optional callback for progress updates
                Signature: callback(message: str, progress: float, details: str)
            
        Returns:
            EmbeddingResult with vector and metadata
            
        Raises:
            EmbeddingRateLimitedException: If rate limited
            EmbeddingQuotaExceededException: If quota exceeded
            EmbeddingModelNotAvailableException: If model not available
            InvalidEmbeddingConfigException: If configuration is invalid
            EmbeddingProviderException: For other provider errors
        """
        pass
    
    @abstractmethod
    async def get_embeddings_batch(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts to embed
            config: Embedding configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of EmbeddingResult objects (same order as input)
            
        Raises:
            Same exceptions as get_embedding
        """
        pass
    
    @abstractmethod
    async def get_embeddings_with_progress(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_tracker: ProgressTracker
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings with integrated progress tracking.
        
        Args:
            texts: List of input texts to embed
            config: Embedding configuration
            progress_tracker: Progress tracking interface
            
        Returns:
            List of EmbeddingResult objects with progress information
        """
        pass
    
    @abstractmethod
    async def get_embedding_dimensions(self, model_name: str) -> int:
        """
        Get the vector dimensions for a model.
        
        Args:
            model_name: Name of the embedding model
            
        Returns:
            Number of dimensions in the embedding vectors
            
        Raises:
            EmbeddingModelNotAvailableException: If model not available
        """
        pass
    
    @abstractmethod
    async def estimate_embedding_cost(
        self,
        text_count: int,
        total_tokens: int,
        model_name: str
    ) -> float:
        """
        Estimate cost for embedding generation.
        
        Args:
            text_count: Number of texts to embed
            total_tokens: Total number of tokens across all texts
            model_name: Embedding model to use
            
        Returns:
            Estimated cost in USD
            
        Raises:
            EmbeddingModelNotAvailableException: If model not available
        """
        pass
    
    @abstractmethod
    async def count_embedding_tokens(
        self,
        texts: Union[str, List[str]],
        model_name: str
    ) -> Union[int, List[int]]:
        """
        Count tokens for embedding cost estimation.
        
        Args:
            texts: Single text or list of texts
            model_name: Model to use for counting
            
        Returns:
            Token count (int) for single text or list of counts for multiple texts
            
        Raises:
            EmbeddingModelNotAvailableException: If model not available
        """
        pass
    
    @abstractmethod
    async def validate_embedding_config(self, config: EmbeddingConfig) -> bool:
        """
        Validate embedding configuration.
        
        Args:
            config: Embedding configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            InvalidEmbeddingConfigException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def get_supported_models(self) -> List[str]:
        """
        Get list of supported embedding models.
        
        Returns:
            List of model names available for embedding
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check embedding provider health and availability.
        
        Returns:
            Dictionary with health information including:
            - status: "healthy", "degraded", or "unhealthy"
            - latency_ms: Average embedding latency
            - embeddings_per_minute: Current throughput
            - error_rate: Error rate as float (0.0-1.0)
            - quota_remaining: Remaining quota (if available)
            - models_available: Number of available models
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        pass
    
    # Context manager support for resource management
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup"""
        pass


class BatchEmbeddingProvider(EmbeddingProvider):
    """
    Extended interface for advanced batch embedding capabilities.
    
    Provides methods for efficient large-scale embedding generation
    with chunking and parallel processing.
    """
    
    @abstractmethod
    async def get_embeddings_chunked(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        chunk_size: Optional[int] = None,
        max_parallel: int = 5,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings with automatic chunking for large batches.
        
        Args:
            texts: List of input texts to embed
            config: Embedding configuration
            chunk_size: Size of each chunk (auto-calculated if None)
            max_parallel: Maximum parallel chunk processing
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of EmbeddingResult objects
        """
        pass
    
    @abstractmethod
    async def get_embeddings_streaming(
        self,
        texts: List[str],
        config: EmbeddingConfig
    ) -> AsyncIterator[EmbeddingResult]:
        """
        Generate embeddings with streaming results.
        
        Args:
            texts: List of input texts to embed
            config: Embedding configuration
            
        Yields:
            EmbeddingResult objects as they complete
        """
        pass


class CacheableEmbeddingProvider(EmbeddingProvider):
    """
    Extended interface with caching capabilities for embeddings.
    
    Provides methods for caching embeddings to improve performance
    and reduce costs for repeated texts.
    """
    
    @abstractmethod
    async def get_embedding_with_cache(
        self,
        text: str,
        config: EmbeddingConfig,
        cache_ttl: Optional[int] = None,
        cache_key: Optional[str] = None
    ) -> EmbeddingResult:
        """
        Generate embedding with caching support.
        
        Args:
            text: Input text to embed
            config: Embedding configuration
            cache_ttl: Cache time-to-live in seconds (None for default)
            cache_key: Custom cache key (auto-generated if None)
            
        Returns:
            EmbeddingResult (may be from cache)
        """
        pass
    
    @abstractmethod
    async def get_embeddings_batch_with_cache(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        cache_ttl: Optional[int] = None
    ) -> List[EmbeddingResult]:
        """
        Generate batch embeddings with caching.
        
        Args:
            texts: List of input texts to embed
            config: Embedding configuration
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            List of EmbeddingResult objects (some may be from cache)
        """
        pass
    
    @abstractmethod
    async def clear_embedding_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear embedding cache.
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            Number of cache entries cleared
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get embedding cache statistics.
        
        Returns:
            Dictionary with cache metrics:
            - total_entries: Number of cached embeddings
            - hit_rate: Cache hit rate as float (0.0-1.0)
            - miss_rate: Cache miss rate as float (0.0-1.0)
            - memory_usage_mb: Cache memory usage in MB
            - average_embedding_size: Average embedding size in bytes
        """
        pass


class SimilarityEmbeddingProvider(EmbeddingProvider):
    """
    Extended interface with similarity computation capabilities.
    
    Provides methods for computing similarity directly without
    retrieving the full embedding vectors.
    """
    
    @abstractmethod
    async def compute_similarity(
        self,
        text1: str,
        text2: str,
        config: EmbeddingConfig,
        similarity_metric: str = "cosine"
    ) -> float:
        """
        Compute similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            config: Embedding configuration
            similarity_metric: Similarity metric ("cosine", "euclidean", "dot")
            
        Returns:
            Similarity score (0.0-1.0 for cosine, varies for others)
        """
        pass
    
    @abstractmethod
    async def find_most_similar(
        self,
        query_text: str,
        candidate_texts: List[str],
        config: EmbeddingConfig,
        top_k: int = 5,
        similarity_metric: str = "cosine"
    ) -> List[tuple[str, float]]:
        """
        Find most similar texts to a query.
        
        Args:
            query_text: Query text
            candidate_texts: List of candidate texts
            config: Embedding configuration
            top_k: Number of most similar texts to return
            similarity_metric: Similarity metric to use
            
        Returns:
            List of (text, similarity_score) tuples, sorted by similarity
        """
        pass
    
    @abstractmethod
    async def compute_similarity_matrix(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        similarity_metric: str = "cosine"
    ) -> List[List[float]]:
        """
        Compute pairwise similarity matrix for all texts.
        
        Args:
            texts: List of texts
            config: Embedding configuration
            similarity_metric: Similarity metric to use
            
        Returns:
            Square matrix where [i][j] is similarity between texts[i] and texts[j]
        """
        pass


# Factory interface for creating embedding providers
class EmbeddingProviderFactory(ABC):
    """
    Factory for creating embedding provider instances.
    
    Allows for flexible provider creation with different
    configurations and implementations.
    """
    
    @abstractmethod
    def create_provider(
        self,
        provider_type: str = "default",
        **kwargs
    ) -> EmbeddingProvider:
        """
        Create an embedding provider instance.
        
        Args:
            provider_type: Type of provider to create
                          Common types: "openai", "cohere", "huggingface", "sentence-transformers"
            **kwargs: Additional configuration passed to provider constructor
            
        Returns:
            EmbeddingProvider implementation
            
        Raises:
            ValueError: If provider_type is not supported
            InvalidEmbeddingConfigException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_available_providers(self) -> List[str]:
        """
        Get list of available embedding provider types.
        
        Returns:
            List of provider type names that can be created
        """
        pass
    
    @abstractmethod
    def get_provider_info(self, provider_type: str) -> Dict[str, Any]:
        """
        Get information about a specific embedding provider type.
        
        Args:
            provider_type: Type of provider to get info for
            
        Returns:
            Dictionary with provider information:
            - name: Human-readable name
            - description: Detailed description
            - supported_models: List of supported embedding models
            - dimensions: Mapping of models to dimensions
            - max_batch_size: Maximum batch size supported
            - pricing: Pricing information per 1K tokens
            - rate_limits: Rate limiting information
        """
        pass


# Utility classes for common patterns
class EmbeddingProviderMiddleware(ABC):
    """
    Base class for embedding provider middleware.
    
    Middleware can be used to add cross-cutting concerns
    like logging, metrics, caching, or normalization.
    """
    
    @abstractmethod
    async def before_embed(
        self,
        text: str,
        config: EmbeddingConfig
    ) -> tuple[str, EmbeddingConfig]:
        """
        Called before embedding text.
        
        Args:
            text: Input text
            config: Embedding configuration
            
        Returns:
            Potentially modified (text, config)
        """
        pass
    
    @abstractmethod
    async def after_embed(
        self,
        text: str,
        config: EmbeddingConfig,
        result: EmbeddingResult
    ) -> EmbeddingResult:
        """
        Called after embedding text.
        
        Args:
            text: Input text that was embedded
            config: Embedding configuration used
            result: Embedding result
            
        Returns:
            Potentially modified result
        """
        pass
    
    @abstractmethod
    async def on_error(
        self,
        text: str,
        config: EmbeddingConfig,
        error: Exception
    ) -> Optional[EmbeddingResult]:
        """
        Called when embedding fails.
        
        Args:
            text: Input text that failed
            config: Embedding configuration used
            error: The exception that occurred
            
        Returns:
            Optional EmbeddingResult to use instead of error,
            or None to let error propagate
        """
        pass


class EmbeddingProviderPool:
    """
    Pool of embedding providers for load distribution.
    
    Manages multiple embedding provider instances to handle high-volume
    embedding operations efficiently.
    """
    
    def __init__(self, factory: EmbeddingProviderFactory, pool_size: int = 3):
        self.factory = factory
        self.pool_size = pool_size
        self._providers: List[EmbeddingProvider] = []
        self._available = asyncio.Queue()
        self._initialized = False
    
    async def initialize(self, provider_type: str = "default", **kwargs) -> None:
        """Initialize the embedding provider pool"""
        if self._initialized:
            return
        
        for _ in range(self.pool_size):
            provider = self.factory.create_provider(provider_type, **kwargs)
            await provider.__aenter__()
            self._providers.append(provider)
            await self._available.put(provider)
        
        self._initialized = True
    
    @asynccontextmanager
    async def get_provider(self):
        """Get a provider from the pool"""
        if not self._initialized:
            raise RuntimeError("Embedding provider pool not initialized")
        
        provider = await self._available.get()
        try:
            yield provider
        finally:
            await self._available.put(provider)
    
    async def close(self) -> None:
        """Close all embedding providers in the pool"""
        for provider in self._providers:
            await provider.__aexit__(None, None, None)
        self._providers.clear()
        self._initialized = False


# Constants for embedding provider features
class EmbeddingProviderFeatures:
    """Constants for common embedding provider features"""
    
    BATCH_PROCESSING = "batch_processing"
    CHUNKING = "chunking"
    STREAMING = "streaming"
    CACHING = "caching"
    SIMILARITY_COMPUTATION = "similarity_computation"
    NORMALIZATION = "normalization"
    CUSTOM_DIMENSIONS = "custom_dimensions"
    MULTILINGUAL = "multilingual"
    FINE_TUNING = "fine_tuning"
    REAL_TIME = "real_time"


# Utility functions for embedding operations
def calculate_cosine_similarity(embedding1: EmbeddingVector, embedding2: EmbeddingVector) -> float:
    """Calculate cosine similarity between two embeddings"""
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings must have the same dimensions")
    
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def calculate_euclidean_distance(embedding1: EmbeddingVector, embedding2: EmbeddingVector) -> float:
    """Calculate Euclidean distance between two embeddings"""
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings must have the same dimensions")
    
    return sum((a - b) ** 2 for a, b in zip(embedding1, embedding2)) ** 0.5


def normalize_embedding(embedding: EmbeddingVector) -> EmbeddingVector:
    """Normalize an embedding to unit length"""
    magnitude = sum(x * x for x in embedding) ** 0.5
    if magnitude == 0:
        return embedding
    return [x / magnitude for x in embedding]
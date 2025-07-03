"""
AI provider port interfaces for Theodore.

This module defines the contracts for AI text analysis providers,
supporting single and streaming analysis, cost estimation, and
comprehensive provider management.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional, List, Union
import asyncio
from contextlib import asynccontextmanager

from src.core.domain.value_objects.ai_config import (
    AnalysisConfig, ModelInfo, StreamingConfig, RetryConfig
)
from src.core.domain.value_objects.ai_response import (
    AnalysisResult, StreamingChunk, AnalysisError, TokenUsage, BatchResult
)
from src.core.ports.progress import ProgressTracker


# Type aliases for cleaner signatures
from typing import Callable
ProgressCallback = Callable[[str, float, Optional[str]], None]
ValidationCallback = Callable[[str], bool]


class AIProviderException(Exception):
    """Base exception for all AI provider errors"""
    pass


class RateLimitedException(AIProviderException):
    """Raised when rate limited by AI provider"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        self.provider = provider
        self.retry_after = retry_after
        message = f"Rate limited by {provider}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message)


class QuotaExceededException(AIProviderException):
    """Raised when quota is exceeded"""
    
    def __init__(self, provider: str, quota_type: str = "requests"):
        self.provider = provider
        self.quota_type = quota_type
        super().__init__(f"Quota exceeded for {provider}: {quota_type}")


class ModelNotAvailableException(AIProviderException):
    """Raised when requested model is not available"""
    
    def __init__(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name
        super().__init__(f"Model {model_name} not available on {provider}")


class InvalidConfigurationException(AIProviderException):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, config_field: Optional[str] = None):
        self.config_field = config_field
        super().__init__(message)


class ProviderTimeoutException(AIProviderException):
    """Raised when provider request times out"""
    
    def __init__(self, provider: str, timeout: float):
        self.provider = provider
        self.timeout = timeout
        super().__init__(f"Timeout after {timeout}s for {provider}")


class AIProvider(ABC):
    """
    Port interface for AI text analysis providers.
    
    This interface defines the contract for all AI analysis adapters,
    from simple completions to complex streaming analysis with function calling.
    """
    
    @abstractmethod
    async def get_provider_info(self) -> ModelInfo:
        """
        Get information about this provider and available models.
        
        Returns:
            ModelInfo with provider capabilities and model details
            
        Raises:
            AIProviderException: If provider info cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> AnalysisResult:
        """
        Analyze text and return structured results.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            system_prompt: Optional system prompt (overrides config default)
            progress_callback: Optional callback for progress updates
                Signature: callback(message: str, progress: float, details: str)
            
        Returns:
            AnalysisResult with generated content and metadata
            
        Raises:
            RateLimitedException: If rate limited
            QuotaExceededException: If quota exceeded
            ModelNotAvailableException: If model not available
            InvalidConfigurationException: If configuration is invalid
            ProviderTimeoutException: If request times out
            AIProviderException: For other provider errors
        """
        pass
    
    @abstractmethod
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        streaming_config: Optional[StreamingConfig] = None
    ) -> AsyncIterator[StreamingChunk]:
        """
        Analyze text with streaming response.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            system_prompt: Optional system prompt
            streaming_config: Optional streaming configuration
            
        Yields:
            StreamingChunk objects as analysis progresses
            
        Raises:
            Same exceptions as analyze_text
        """
        pass
    
    @abstractmethod
    async def analyze_batch(
        self,
        texts: List[str],
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchResult:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of input texts to analyze
            config: Analysis configuration
            system_prompt: Optional system prompt
            progress_callback: Optional callback for progress updates
            
        Returns:
            BatchResult with all individual results and aggregated metrics
            
        Raises:
            Same exceptions as analyze_text
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model_name: str) -> int:
        """
        Count tokens for cost estimation.
        
        Args:
            text: Text to count tokens for
            model_name: Model to use for counting
            
        Returns:
            Number of tokens
            
        Raises:
            ModelNotAvailableException: If model not available
            AIProviderException: For other errors
        """
        pass
    
    @abstractmethod
    async def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ) -> float:
        """
        Estimate cost in USD for the given usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            model_name: Model being used
            
        Returns:
            Estimated cost in USD
            
        Raises:
            ModelNotAvailableException: If model not available
        """
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: AnalysisConfig) -> bool:
        """
        Validate the provider configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            InvalidConfigurationException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and availability.
        
        Returns:
            Dictionary with health information including:
            - status: "healthy", "degraded", or "unhealthy"
            - latency_ms: Average response latency
            - requests_per_minute: Current throughput
            - error_rate: Error rate as float (0.0-1.0)
            - quota_remaining: Remaining quota (if available)
            - last_error: Last error encountered (if any)
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


class StreamingAIProvider(AIProvider):
    """
    Extended interface for advanced streaming capabilities.
    
    Provides methods for real-time streaming with enhanced control
    and monitoring capabilities.
    """
    
    @abstractmethod
    async def analyze_with_progress(
        self,
        text: str,
        config: AnalysisConfig,
        progress_tracker: ProgressTracker,
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze with integrated progress tracking.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            progress_tracker: Progress tracking interface
            system_prompt: Optional system prompt
            
        Returns:
            AnalysisResult with detailed progress information
        """
        pass
    
    @abstractmethod
    async def stream_with_callback(
        self,
        text: str,
        config: AnalysisConfig,
        chunk_callback: Callable[[StreamingChunk], None],
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        """
        Stream with real-time chunk processing.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            chunk_callback: Callback for each streaming chunk
            system_prompt: Optional system prompt
            
        Returns:
            Final AnalysisResult after streaming completes
        """
        pass


class CacheableAIProvider(AIProvider):
    """
    Extended interface with caching capabilities.
    
    Provides methods for caching responses to improve performance
    and reduce costs.
    """
    
    @abstractmethod
    async def analyze_with_cache(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        cache_key: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze with caching support.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            system_prompt: Optional system prompt
            cache_ttl: Cache time-to-live in seconds (None for default)
            cache_key: Custom cache key (auto-generated if None)
            
        Returns:
            AnalysisResult (may be from cache)
        """
        pass
    
    @abstractmethod
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cached results.
        
        Args:
            pattern: Optional pattern to match cache keys
                    (clears all if None)
            
        Returns:
            Number of cache entries cleared
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics:
            - total_entries: Number of cached entries
            - hit_rate: Cache hit rate as float (0.0-1.0)
            - miss_rate: Cache miss rate as float (0.0-1.0)
            - size_bytes: Total cache size in bytes
            - oldest_entry: Timestamp of oldest cached entry
            - newest_entry: Timestamp of newest cached entry
        """
        pass


class MultiModelAIProvider(AIProvider):
    """
    Extended interface for providers supporting multiple models.
    
    Allows dynamic model selection and fallback strategies.
    """
    
    @abstractmethod
    async def analyze_with_model_selection(
        self,
        text: str,
        config: AnalysisConfig,
        preferred_models: List[str],
        fallback_strategy: str = "cheapest",
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze with intelligent model selection.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            preferred_models: List of preferred models (in order)
            fallback_strategy: Strategy for fallback ("cheapest", "fastest", "best")
            system_prompt: Optional system prompt
            
        Returns:
            AnalysisResult with model selection metadata
        """
        pass
    
    @abstractmethod
    async def compare_models(
        self,
        text: str,
        config: AnalysisConfig,
        models: List[str],
        system_prompt: Optional[str] = None
    ) -> Dict[str, AnalysisResult]:
        """
        Compare results across multiple models.
        
        Args:
            text: Input text to analyze
            config: Analysis configuration
            models: List of models to compare
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary mapping model names to results
        """
        pass


# Factory interface for creating AI providers
class AIProviderFactory(ABC):
    """
    Factory for creating AI provider instances.
    
    Allows for flexible provider creation with different
    configurations and implementations.
    """
    
    @abstractmethod
    def create_provider(
        self,
        provider_type: str = "default",
        **kwargs
    ) -> AIProvider:
        """
        Create an AI provider instance.
        
        Args:
            provider_type: Type of provider to create
                          Common types: "bedrock", "openai", "gemini", "anthropic"
            **kwargs: Additional configuration passed to provider constructor
            
        Returns:
            AIProvider implementation
            
        Raises:
            ValueError: If provider_type is not supported
            InvalidConfigurationException: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_available_providers(self) -> List[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider type names that can be created
        """
        pass
    
    @abstractmethod
    def get_provider_info(self, provider_type: str) -> Dict[str, Any]:
        """
        Get information about a specific provider type.
        
        Args:
            provider_type: Type of provider to get info for
            
        Returns:
            Dictionary with provider information:
            - name: Human-readable name
            - description: Detailed description
            - supported_models: List of supported models
            - capabilities: List of supported features
            - requirements: List of dependencies
            - pricing: Pricing information
            - rate_limits: Rate limiting information
        """
        pass


# Utility classes for common patterns
class AIProviderMiddleware(ABC):
    """
    Base class for AI provider middleware.
    
    Middleware can be used to add cross-cutting concerns
    like logging, metrics, caching, or rate limiting.
    """
    
    @abstractmethod
    async def before_analyze(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None
    ) -> tuple[str, AnalysisConfig, Optional[str]]:
        """
        Called before analyzing text.
        
        Args:
            text: Input text
            config: Analysis configuration
            system_prompt: System prompt
            
        Returns:
            Potentially modified (text, config, system_prompt)
        """
        pass
    
    @abstractmethod
    async def after_analyze(
        self,
        text: str,
        config: AnalysisConfig,
        result: AnalysisResult
    ) -> AnalysisResult:
        """
        Called after analyzing text.
        
        Args:
            text: Input text that was analyzed
            config: Analysis configuration used
            result: Analysis result
            
        Returns:
            Potentially modified result
        """
        pass
    
    @abstractmethod
    async def on_error(
        self,
        text: str,
        config: AnalysisConfig,
        error: Exception
    ) -> Optional[AnalysisResult]:
        """
        Called when analysis fails.
        
        Args:
            text: Input text that failed
            config: Analysis configuration used
            error: The exception that occurred
            
        Returns:
            Optional AnalysisResult to use instead of error,
            or None to let error propagate
        """
        pass


class AIProviderPool:
    """
    Pool of AI providers for load distribution.
    
    Manages multiple provider instances to handle high-volume
    analysis operations efficiently.
    """
    
    def __init__(self, factory: AIProviderFactory, pool_size: int = 5):
        self.factory = factory
        self.pool_size = pool_size
        self._providers: List[AIProvider] = []
        self._available = asyncio.Queue()
        self._initialized = False
    
    async def initialize(self, provider_type: str = "default", **kwargs) -> None:
        """Initialize the provider pool"""
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
            raise RuntimeError("Pool not initialized")
        
        provider = await self._available.get()
        try:
            yield provider
        finally:
            await self._available.put(provider)
    
    async def close(self) -> None:
        """Close all providers in the pool"""
        for provider in self._providers:
            await provider.__aexit__(None, None, None)
        self._providers.clear()
        self._initialized = False


# Constants for provider features
class AIProviderFeatures:
    """Constants for common AI provider features"""
    
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    JSON_MODE = "json_mode"
    SYSTEM_PROMPTS = "system_prompts"
    CUSTOM_STOPPING = "custom_stopping"
    BATCH_PROCESSING = "batch_processing"
    FINE_TUNING = "fine_tuning"
    EMBEDDINGS = "embeddings"
    CONTENT_FILTERING = "content_filtering"
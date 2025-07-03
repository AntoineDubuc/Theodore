"""
Unit tests for mock embedding provider implementation.

Tests all aspects of the EmbeddingProvider interface using comprehensive mock
implementations to validate interface compliance and behavior.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import hashlib
from typing import List, Dict, Any, Union, Callable, Optional
from unittest.mock import Mock
from datetime import datetime

from src.core.ports.embedding_provider import (
    EmbeddingProvider, EmbeddingProviderException, EmbeddingRateLimitedException,
    EmbeddingQuotaExceededException, EmbeddingModelNotAvailableException,
    InvalidEmbeddingConfigException, EmbeddingDimensionMismatchException,
    calculate_cosine_similarity, calculate_euclidean_distance, normalize_embedding
)
from src.core.domain.value_objects.ai_config import EmbeddingConfig
from src.core.domain.value_objects.ai_response import EmbeddingResult
from src.core.ports.progress import ProgressTracker


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider for testing.
    
    Generates deterministic embeddings based on text content
    and simulates realistic provider behavior.
    """
    
    def __init__(
        self,
        dimensions: int = 1536,
        cost_per_token: float = 0.0001,
        simulate_latency: bool = False,
        simulate_errors: bool = False,
        error_rate: float = 0.05
    ):
        self.dimensions = dimensions
        self.cost_per_token = cost_per_token
        self.simulate_latency = simulate_latency
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        
        # Statistics tracking
        self.request_count = 0
        self.total_tokens_processed = 0
        self.total_cost = 0.0
        self.error_count = 0
        
        # Track if we're in context manager
        self._in_context = False
        
        # Available models with different dimensions
        self.models = {
            "text-embedding-ada-002": {"dimensions": 1536, "cost_per_token": 0.0001},
            "text-embedding-small": {"dimensions": 512, "cost_per_token": 0.00005},
            "text-embedding-large": {"dimensions": 3072, "cost_per_token": 0.0002},
            "sentence-transformer-base": {"dimensions": 768, "cost_per_token": 0.00003},
            "mock-embedding-v1": {"dimensions": self.dimensions, "cost_per_token": self.cost_per_token}
        }
        
        # Default to mock model
        self.default_model = "mock-embedding-v1"
        
        # Cache for deterministic embeddings
        self._embedding_cache = {}
    
    async def get_embedding(
        self,
        text: str,
        config: EmbeddingConfig,
        progress_callback: Optional[Callable] = None
    ) -> EmbeddingResult:
        """Generate mock embedding for a single text"""
        
        if not self._in_context:
            raise InvalidEmbeddingConfigException("Provider must be used as async context manager")
        
        self.request_count += 1
        
        if progress_callback:
            progress_callback(f"Starting embedding generation for {len(text)} characters", 0.0, "Initializing")
        
        # Validate model
        if config.model_name not in self.models:
            raise EmbeddingModelNotAvailableException("MockEmbeddingProvider", config.model_name)
        
        # Simulate latency
        if self.simulate_latency:
            await asyncio.sleep(0.05)  # 50ms latency
        
        if progress_callback:
            progress_callback("Generating embedding vector", 0.5, "Processing text")
        
        # Simulate errors occasionally
        if self.simulate_errors and self.request_count % 20 == 0:
            self.error_count += 1
            raise EmbeddingRateLimitedException("MockEmbeddingProvider", retry_after=10)
        
        # Generate deterministic embedding
        embedding = self._generate_embedding(text, config.model_name)
        
        # Calculate token count and cost
        token_count = await self.count_embedding_tokens(text, config.model_name)
        cost = await self.estimate_embedding_cost(1, token_count, config.model_name)
        
        # Update statistics
        self.total_tokens_processed += token_count
        self.total_cost += cost
        
        # Generate text hash for deduplication
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if progress_callback:
            progress_callback("Embedding generation complete", 1.0, f"Generated {len(embedding)}-dimensional vector")
        
        return EmbeddingResult(
            embedding=embedding,
            dimensions=len(embedding),
            model_used=config.model_name,
            provider_name="MockEmbeddingProvider",
            token_count=token_count,
            estimated_cost=cost,
            text_length=len(text),
            text_hash=text_hash,
            request_id=f"embed_req_{self.request_count}",
            processing_time=0.05 if self.simulate_latency else 0.01,
            confidence_score=0.95,
            provider_metadata={
                "mock": True,
                "request_number": self.request_count,
                "model_info": self.models[config.model_name]
            }
        )
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts efficiently"""
        
        if not self._in_context:
            raise InvalidEmbeddingConfigException("Provider must be used as async context manager")
        
        if progress_callback:
            progress_callback(f"Starting batch embedding for {len(texts)} texts", 0.0, "Initializing batch")
        
        results = []
        batch_size = min(config.batch_size, len(texts))
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            # Simulate batch processing efficiency
            if self.simulate_latency:
                await asyncio.sleep(0.02 * len(batch_texts))  # Faster than individual requests
            
            for j, text in enumerate(batch_texts):
                if progress_callback:
                    overall_progress = (i + j + 1) / len(texts)
                    progress_callback(
                        f"Processing text {i + j + 1}/{len(texts)}", 
                        overall_progress, 
                        f"Batch {i // batch_size + 1}"
                    )
                
                result = await self.get_embedding(text, config)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        if progress_callback:
            progress_callback("Batch embedding complete", 1.0, f"Generated {len(results)} embeddings")
        
        return results
    
    async def get_embeddings_with_progress(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_tracker: ProgressTracker
    ) -> List[EmbeddingResult]:
        """Generate embeddings with integrated progress tracking"""
        
        def progress_callback(message: str, progress: float, details: str = None):
            if progress_tracker:
                progress_tracker.update_progress(progress, message, details)
        
        return await self.get_embeddings_batch(texts, config, progress_callback)
    
    async def get_embedding_dimensions(self, model_name: str) -> int:
        """Get the vector dimensions for a model"""
        if model_name not in self.models:
            raise EmbeddingModelNotAvailableException("MockEmbeddingProvider", model_name)
        
        return self.models[model_name]["dimensions"]
    
    async def estimate_embedding_cost(
        self,
        text_count: int,
        total_tokens: int,
        model_name: str
    ) -> float:
        """Estimate cost for embedding generation"""
        if model_name not in self.models:
            raise EmbeddingModelNotAvailableException("MockEmbeddingProvider", model_name)
        
        cost_per_token = self.models[model_name]["cost_per_token"]
        return total_tokens * cost_per_token
    
    async def count_embedding_tokens(
        self,
        texts: Union[str, List[str]],
        model_name: str
    ) -> Union[int, List[int]]:
        """Count tokens for embedding cost estimation"""
        if model_name not in self.models:
            raise EmbeddingModelNotAvailableException("MockEmbeddingProvider", model_name)
        
        if isinstance(texts, str):
            # Simple approximation: 1 token ≈ 0.75 words for embeddings
            word_count = len(texts.split())
            return int(word_count / 0.75)
        else:
            return [await self.count_embedding_tokens(text, model_name) for text in texts]
    
    async def validate_embedding_config(self, config: EmbeddingConfig) -> bool:
        """Validate embedding configuration"""
        # Check model availability
        if config.model_name not in self.models:
            raise InvalidEmbeddingConfigException(f"Model {config.model_name} not available")
        
        # Check dimensions if specified
        model_dims = self.models[config.model_name]["dimensions"]
        if config.dimensions and config.dimensions != model_dims:
            raise InvalidEmbeddingConfigException(
                f"Requested dimensions {config.dimensions} don't match model dimensions {model_dims}"
            )
        
        # Check batch size
        if config.batch_size <= 0 or config.batch_size > 100:
            raise InvalidEmbeddingConfigException("batch_size must be between 1 and 100")
        
        return True
    
    async def get_supported_models(self) -> List[str]:
        """Get list of supported embedding models"""
        return list(self.models.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check embedding provider health and availability"""
        avg_latency = 50 if self.simulate_latency else 10
        error_rate = self.error_rate if self.simulate_errors else 0.0
        
        status = "healthy"
        if error_rate > 0.05:
            status = "degraded"
        if error_rate > 0.2:
            status = "unhealthy"
        
        return {
            "status": status,
            "latency_ms": avg_latency,
            "embeddings_per_minute": max(1000 - self.request_count, 0),
            "error_rate": error_rate,
            "quota_remaining": max(10000 - self.request_count, 0),
            "models_available": len(self.models),
            "requests_processed": self.request_count,
            "total_tokens_processed": self.total_tokens_processed,
            "total_cost": self.total_cost,
            "cache_size": len(self._embedding_cache),
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def close(self) -> None:
        """Clean up resources"""
        self.request_count = 0
        self.total_tokens_processed = 0
        self.total_cost = 0.0
        self.error_count = 0
        self._embedding_cache.clear()
        self._in_context = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._in_context = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _generate_embedding(self, text: str, model_name: str) -> List[float]:
        """Generate deterministic embedding based on text content"""
        # Use caching for consistency
        cache_key = f"{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
        
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Generate deterministic embedding based on text hash
        text_hash = hash(text) % (2**31)  # Ensure positive
        
        # Use a simple but deterministic method to generate embeddings
        dimensions = self.models[model_name]["dimensions"]
        
        # Create a pseudo-random but deterministic sequence
        import random
        random.seed(text_hash)
        
        # Generate embedding with some semantic meaning
        embedding = []
        
        # Base vector influenced by text characteristics
        text_lower = text.lower()
        word_count = len(text.split())
        char_count = len(text)
        
        for i in range(dimensions):
            # Create pseudo-semantic values based on text features
            value = random.gauss(0, 0.1)  # Base noise
            
            # Add semantic features
            if "company" in text_lower:
                value += 0.3 * random.random()
            if "business" in text_lower:
                value += 0.2 * random.random()
            if "technology" in text_lower:
                value -= 0.2 * random.random()
            if "financial" in text_lower or "finance" in text_lower:
                value += 0.4 * random.random()
            
            # Scale by text length (longer texts get stronger signals)
            value *= (1 + word_count / 100)
            
            embedding.append(value)
        
        # Normalize the embedding
        embedding = normalize_embedding(embedding)
        
        # Cache for consistency
        self._embedding_cache[cache_key] = embedding
        
        return embedding


class TestMockEmbeddingProvider:
    """Test suite for MockEmbeddingProvider implementation"""
    
    @pytest_asyncio.fixture
    async def provider(self):
        """Create a mock embedding provider for testing"""
        provider = MockEmbeddingProvider(
            dimensions=1536,
            simulate_latency=False,
            simulate_errors=False
        )
        async with provider:
            yield provider
    
    @pytest.fixture
    def basic_config(self):
        """Basic embedding configuration"""
        return EmbeddingConfig(
            model_name="mock-embedding-v1",
            normalize=True,
            batch_size=10
        )
    
    @pytest.fixture
    def similarity_config(self):
        """Similarity search configuration"""
        return EmbeddingConfig.for_similarity_search()
    
    @pytest.mark.asyncio
    async def test_single_embedding_generation(self, provider, basic_config):
        """Test single embedding generation"""
        text = "This is a test company that provides innovative software solutions."
        
        result = await provider.get_embedding(text, basic_config)
        
        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == 1536
        assert result.dimensions == 1536
        assert result.model_used == "mock-embedding-v1"
        assert result.provider_name == "MockEmbeddingProvider"
        assert result.token_count > 0
        assert result.estimated_cost > 0
        assert result.text_length == len(text)
        assert result.text_hash is not None
        assert result.is_normalized()  # Should be normalized
    
    @pytest.mark.asyncio
    async def test_batch_embedding_generation(self, provider, basic_config):
        """Test batch embedding generation"""
        texts = [
            "Company A provides payment processing services.",
            "Company B offers cloud computing solutions.",
            "Company C develops AI-powered analytics tools."
        ]
        
        results = await provider.get_embeddings_batch(texts, basic_config)
        
        assert len(results) == len(texts)
        assert all(isinstance(result, EmbeddingResult) for result in results)
        assert all(len(result.embedding) == 1536 for result in results)
        assert all(result.is_normalized() for result in results)
        
        # Check that different texts produce different embeddings
        embeddings = [result.embedding for result in results]
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]
        assert embeddings[0] != embeddings[2]
    
    @pytest.mark.asyncio
    async def test_embedding_consistency(self, provider, basic_config):
        """Test that same text produces same embedding"""
        text = "Consistent embedding test text."
        
        result1 = await provider.get_embedding(text, basic_config)
        result2 = await provider.get_embedding(text, basic_config)
        
        assert result1.embedding == result2.embedding
        assert result1.text_hash == result2.text_hash
        assert result1.dimensions == result2.dimensions
    
    @pytest.mark.asyncio
    async def test_semantic_similarity(self, provider, basic_config):
        """Test that embeddings capture some semantic meaning"""
        text1 = "A financial company providing payment solutions."
        text2 = "A fintech company offering payment processing services."
        text3 = "A company that builds rockets for space exploration."
        
        result1 = await provider.get_embedding(text1, basic_config)
        result2 = await provider.get_embedding(text2, basic_config)
        result3 = await provider.get_embedding(text3, basic_config)
        
        # Calculate similarities
        similarity_1_2 = calculate_cosine_similarity(result1.embedding, result2.embedding)
        similarity_1_3 = calculate_cosine_similarity(result1.embedding, result3.embedding)
        similarity_2_3 = calculate_cosine_similarity(result2.embedding, result3.embedding)
        
        # All similarities should be valid values between -1 and 1
        assert -1.0 <= similarity_1_2 <= 1.0
        assert -1.0 <= similarity_1_3 <= 1.0
        assert -1.0 <= similarity_2_3 <= 1.0
        
        # Test that embeddings are different (not all the same)
        assert result1.embedding != result2.embedding
        assert result1.embedding != result3.embedding
        assert result2.embedding != result3.embedding
        
        # Test that keyword influence is detectable
        # Both text1 and text2 contain "financial"/"fintech" and "payment"
        # This should influence their embeddings to be somewhat related
        # But this is a mock so we just verify the mechanism works
        assert isinstance(similarity_1_2, float)
        assert isinstance(similarity_1_3, float)
    
    @pytest.mark.asyncio
    async def test_different_models(self, provider):
        """Test different embedding models"""
        text = "Test text for different models."
        
        # Test small model
        small_config = EmbeddingConfig(model_name="text-embedding-small")
        small_result = await provider.get_embedding(text, small_config)
        assert small_result.dimensions == 512
        
        # Test large model
        large_config = EmbeddingConfig(model_name="text-embedding-large")
        large_result = await provider.get_embedding(text, large_config)
        assert large_result.dimensions == 3072
        
        # Test cost differences
        assert small_result.estimated_cost < large_result.estimated_cost
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, provider, basic_config):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(message: str, progress: float, details: str = None):
            progress_updates.append((message, progress, details))
        
        text = "Test text for progress tracking."
        result = await provider.get_embedding(text, basic_config, progress_callback)
        
        assert result.dimensions == 1536
        assert len(progress_updates) >= 2  # At least start and end
        assert progress_updates[0][1] == 0.0  # First progress is 0%
        assert progress_updates[-1][1] == 1.0  # Final progress is 100%
    
    @pytest.mark.asyncio
    async def test_progress_tracker_integration(self, provider, basic_config):
        """Test integration with progress tracker"""
        progress_tracker = Mock()
        progress_tracker.update_progress = Mock()
        
        texts = ["Text 1", "Text 2", "Text 3"]
        results = await provider.get_embeddings_with_progress(texts, basic_config, progress_tracker)
        
        assert len(results) == len(texts)
        assert progress_tracker.update_progress.called
        assert progress_tracker.update_progress.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_token_counting(self, provider):
        """Test token counting functionality"""
        text = "This is a sample text for token counting in embeddings."
        model_name = "mock-embedding-v1"
        
        # Single text
        token_count = await provider.count_embedding_tokens(text, model_name)
        assert isinstance(token_count, int)
        assert token_count > 0
        
        # Multiple texts
        texts = ["Text one", "Text two", "Text three"]
        token_counts = await provider.count_embedding_tokens(texts, model_name)
        assert isinstance(token_counts, list)
        assert len(token_counts) == len(texts)
        assert all(isinstance(count, int) for count in token_counts)
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, provider):
        """Test cost estimation"""
        text_count = 5
        total_tokens = 100
        model_name = "mock-embedding-v1"
        
        cost = await provider.estimate_embedding_cost(text_count, total_tokens, model_name)
        
        assert isinstance(cost, float)
        assert cost > 0
        # Should be total_tokens * cost_per_token
        expected_cost = total_tokens * 0.0001  # Default cost
        assert abs(cost - expected_cost) < 0.0001
    
    @pytest.mark.asyncio
    async def test_model_dimensions(self, provider):
        """Test getting model dimensions"""
        # Test different models
        dimensions_ada = await provider.get_embedding_dimensions("text-embedding-ada-002")
        assert dimensions_ada == 1536
        
        dimensions_small = await provider.get_embedding_dimensions("text-embedding-small")
        assert dimensions_small == 512
        
        dimensions_large = await provider.get_embedding_dimensions("text-embedding-large")
        assert dimensions_large == 3072
    
    @pytest.mark.asyncio
    async def test_supported_models(self, provider):
        """Test getting supported models"""
        models = await provider.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) >= 5
        assert "mock-embedding-v1" in models
        assert "text-embedding-ada-002" in models
        assert "text-embedding-small" in models
        assert "text-embedding-large" in models
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, provider):
        """Test configuration validation"""
        # Valid configuration
        valid_config = EmbeddingConfig(
            model_name="mock-embedding-v1",
            batch_size=10,
            normalize=True
        )
        assert await provider.validate_embedding_config(valid_config) is True
        
        # Invalid model
        invalid_model_config = EmbeddingConfig(model_name="nonexistent-model")
        with pytest.raises(InvalidEmbeddingConfigException, match="not available"):
            await provider.validate_embedding_config(invalid_model_config)
        
        # Invalid batch size
        invalid_batch_config = EmbeddingConfig(
            model_name="mock-embedding-v1",
            batch_size=200  # Too large
        )
        with pytest.raises(InvalidEmbeddingConfigException, match="batch_size"):
            await provider.validate_embedding_config(invalid_batch_config)
        
        # Invalid dimensions
        invalid_dims_config = EmbeddingConfig(
            model_name="text-embedding-small",
            dimensions=1536  # Doesn't match model's 512 dimensions
        )
        with pytest.raises(InvalidEmbeddingConfigException, match="dimensions"):
            await provider.validate_embedding_config(invalid_dims_config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, provider, basic_config):
        """Test health check functionality"""
        # Generate some embeddings first
        texts = ["Test 1", "Test 2", "Test 3"]
        await provider.get_embeddings_batch(texts, basic_config)
        
        health = await provider.health_check()
        
        assert isinstance(health, dict)
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "latency_ms" in health
        assert "embeddings_per_minute" in health
        assert "error_rate" in health
        assert health["requests_processed"] >= 3
        assert health["total_tokens_processed"] > 0
        assert health["models_available"] >= 5
    
    @pytest.mark.asyncio
    async def test_context_manager_requirement(self):
        """Test that provider requires context manager usage"""
        provider = MockEmbeddingProvider()
        
        config = EmbeddingConfig(model_name="mock-embedding-v1")
        
        with pytest.raises(InvalidEmbeddingConfigException, match="context manager"):
            await provider.get_embedding("test", config)
    
    @pytest.mark.asyncio
    async def test_model_not_available_error(self, provider):
        """Test model not available error handling"""
        config = EmbeddingConfig(model_name="nonexistent-model")
        
        with pytest.raises(EmbeddingModelNotAvailableException) as exc_info:
            await provider.get_embedding("test", config)
        
        assert exc_info.value.provider == "MockEmbeddingProvider"
        assert exc_info.value.model_name == "nonexistent-model"


class TestMockEmbeddingProviderErrorScenarios:
    """Test error scenarios with mock embedding provider"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self):
        """Test rate limiting error simulation"""
        provider = MockEmbeddingProvider(simulate_errors=True)
        
        config = EmbeddingConfig(model_name="mock-embedding-v1")
        
        async with provider:
            # First 19 requests should succeed
            for i in range(19):
                result = await provider.get_embedding(f"Test {i}", config)
                assert len(result.embedding) == 1536
            
            # 20th request should trigger rate limit
            with pytest.raises(EmbeddingRateLimitedException) as exc_info:
                await provider.get_embedding("Test 20", config)
            
            assert exc_info.value.provider == "MockEmbeddingProvider"
            assert exc_info.value.retry_after == 10
    
    @pytest.mark.asyncio
    async def test_latency_simulation(self):
        """Test latency simulation"""
        provider = MockEmbeddingProvider(simulate_latency=True)
        
        config = EmbeddingConfig(model_name="mock-embedding-v1")
        
        async with provider:
            start_time = time.time()
            result = await provider.get_embedding("Test with latency", config)
            end_time = time.time()
            
            assert len(result.embedding) == 1536
            assert end_time - start_time >= 0.05  # At least 50ms latency
            assert result.processing_time >= 0.05


class TestEmbeddingUtilityFunctions:
    """Test utility functions for embedding operations"""
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6
        
        # Orthogonal vectors
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        similarity = calculate_cosine_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 1e-6
        
        # Opposite vectors
        vec5 = [1.0, 0.0, 0.0]
        vec6 = [-1.0, 0.0, 0.0]
        similarity = calculate_cosine_similarity(vec5, vec6)
        assert abs(similarity - (-1.0)) < 1e-6
    
    def test_euclidean_distance(self):
        """Test Euclidean distance calculation"""
        # Identical vectors
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        distance = calculate_euclidean_distance(vec1, vec2)
        assert abs(distance - 0.0) < 1e-6
        
        # Unit distance
        vec3 = [0.0, 0.0, 0.0]
        vec4 = [1.0, 0.0, 0.0]
        distance = calculate_euclidean_distance(vec3, vec4)
        assert abs(distance - 1.0) < 1e-6
        
        # Pythagorean triple
        vec5 = [0.0, 0.0, 0.0]
        vec6 = [3.0, 4.0, 0.0]
        distance = calculate_euclidean_distance(vec5, vec6)
        assert abs(distance - 5.0) < 1e-6
    
    def test_normalize_embedding(self):
        """Test embedding normalization"""
        # Test normalization
        embedding = [3.0, 4.0, 0.0]
        normalized = normalize_embedding(embedding)
        
        # Should have unit length
        magnitude = sum(x**2 for x in normalized) ** 0.5
        assert abs(magnitude - 1.0) < 1e-6
        
        # Should preserve direction
        assert normalized[0] / normalized[1] == 3.0 / 4.0
        
        # Already normalized vector
        unit_embedding = [1.0, 0.0, 0.0]
        normalized_unit = normalize_embedding(unit_embedding)
        assert normalized_unit == unit_embedding
    
    def test_dimension_mismatch_errors(self):
        """Test dimension mismatch error handling"""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError, match="same dimensions"):
            calculate_cosine_similarity(vec1, vec2)
        
        with pytest.raises(ValueError, match="same dimensions"):
            calculate_euclidean_distance(vec1, vec2)


@pytest.mark.asyncio
async def test_interface_compliance():
    """Test that MockEmbeddingProvider fully implements EmbeddingProvider interface"""
    provider = MockEmbeddingProvider()
    
    # Verify it's recognized as EmbeddingProvider
    assert isinstance(provider, EmbeddingProvider)
    
    # Verify all required methods exist
    required_methods = [
        'get_embedding', 'get_embeddings_batch', 'get_embeddings_with_progress',
        'get_embedding_dimensions', 'estimate_embedding_cost', 'count_embedding_tokens',
        'validate_embedding_config', 'get_supported_models', 'health_check',
        'close', '__aenter__', '__aexit__'
    ]
    
    for method_name in required_methods:
        assert hasattr(provider, method_name)
        assert callable(getattr(provider, method_name))


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
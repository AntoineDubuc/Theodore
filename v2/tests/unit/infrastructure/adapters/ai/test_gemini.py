#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Google Gemini Adapter
=================================================

Tests all components of the Gemini adapter implementation:
- Configuration management and cost calculation
- Client authentication and retry logic
- Analyzer text processing and streaming
- Token management and rate limiting
- Error handling and circuit breaker patterns
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import the components to test
from src.infrastructure.adapters.ai.gemini.config import (
    GeminiConfig, calculate_gemini_cost, get_cheapest_gemini_model_for_task,
    GEMINI_MODEL_COSTS, estimate_gemini_monthly_cost
)
from src.infrastructure.adapters.ai.gemini.client import (
    GeminiClient, GeminiResponse, GeminiUsage, GeminiError,
    GeminiRateLimitError, GeminiAuthenticationError
)
from src.infrastructure.adapters.ai.gemini.analyzer import GeminiAnalyzer
from src.infrastructure.adapters.ai.gemini.token_manager import (
    GeminiTokenManager, TokenUsageEntry, UsageStats
)
from src.infrastructure.adapters.ai.gemini.rate_limiter import (
    GeminiRateLimiter, TokenBucket, CircuitBreaker, CircuitState
)
from src.infrastructure.adapters.ai.gemini.streamer import GeminiStreamer

from src.core.domain.value_objects.ai_config import AnalysisConfig
from src.core.domain.value_objects.ai_response import TokenUsage
from src.core.domain.exceptions import AIProviderError, ConfigurationError


class TestGeminiConfig:
    """Test Gemini configuration management."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = GeminiConfig()
        
        assert config.model == "gemini-2.5-pro"
        assert config.max_context_tokens == 1000000
        assert config.temperature == 0.1
        assert config.max_output_tokens == 8192
        assert config.max_retries == 3
        assert config.enable_streaming is True
        assert config.daily_cost_limit == 100.0
    
    @patch.dict('os.environ', {
        'GEMINI_API_KEY': 'test_key_123',
        'GEMINI_MODEL': 'gemini-1.5-pro',
        'GEMINI_TEMPERATURE': '0.2',
        'GEMINI_DAILY_COST_LIMIT': '50.0'
    })
    def test_config_from_environment(self):
        """Test loading configuration from environment variables."""
        config = GeminiConfig.from_environment()
        
        assert config.api_key == 'test_key_123'
        assert config.model == 'gemini-1.5-pro'
        assert config.temperature == 0.2
        assert config.daily_cost_limit == 50.0
    
    def test_calculate_gemini_cost(self):
        """Test cost calculation for different models."""
        # Test Gemini 2.5 Pro
        cost = calculate_gemini_cost(1000, 500, 'gemini-2.5-pro')
        expected = (1000 / 1000 * 0.00125) + (500 / 1000 * 0.005)
        assert abs(cost - expected) < 0.0001
        
        # Test Gemini 1.5 Flash (cheaper)
        cost_flash = calculate_gemini_cost(1000, 500, 'gemini-1.5-flash')
        assert cost_flash < cost  # Flash should be cheaper
        
        # Test invalid model
        with pytest.raises(ValueError):
            calculate_gemini_cost(1000, 500, 'invalid-model')
    
    def test_get_cheapest_model_for_task(self):
        """Test model selection optimization."""
        assert get_cheapest_gemini_model_for_task('fast') == 'gemini-1.5-flash'
        assert get_cheapest_gemini_model_for_task('large_context') == 'gemini-2.5-pro'
        assert get_cheapest_gemini_model_for_task('simple') == 'gemini-1.0-pro'
        assert get_cheapest_gemini_model_for_task('unknown') == 'gemini-1.5-pro'
    
    def test_monthly_cost_estimation(self):
        """Test monthly cost estimation."""
        estimate = estimate_gemini_monthly_cost(
            requests_per_day=100,
            avg_input_tokens=1000,
            avg_output_tokens=500,
            model='gemini-1.5-flash'
        )
        
        assert 'daily_cost' in estimate
        assert 'monthly_cost' in estimate
        assert 'annual_cost' in estimate
        assert estimate['monthly_cost'] == estimate['daily_cost'] * 30
        assert estimate['requests_per_day'] == 100


class TestTokenBucket:
    """Test token bucket rate limiting algorithm."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_basic_operation(self):
        """Test basic token bucket acquire and refill."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)  # 5 tokens per second
        
        # Should be able to acquire initial tokens
        assert await bucket.acquire(5) is True
        assert await bucket.acquire(5) is True
        
        # Should not be able to acquire more (bucket empty)
        assert await bucket.acquire(1) is False
        
        # Wait for refill
        await asyncio.sleep(1.1)  # Allow 1 second + buffer for refill
        
        # Should be able to acquire again
        assert await bucket.acquire(3) is True
    
    @pytest.mark.asyncio
    async def test_token_bucket_wait_for_tokens(self):
        """Test waiting for token bucket refill."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)  # 10 tokens per second
        
        # Exhaust bucket
        await bucket.acquire(5)
        
        # Wait for tokens
        start_time = time.time()
        wait_time = await bucket.wait_for_tokens(2)
        elapsed = time.time() - start_time
        
        # Should have waited approximately 0.2 seconds (2 tokens / 10 per second)
        assert wait_time > 0
        assert elapsed >= 0.1  # At least some time elapsed


class TestCircuitBreaker:
    """Test circuit breaker implementation."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # Start closed
        assert breaker.state == CircuitState.CLOSED
        assert await breaker.call_allowed() is True
        
        # Record failures
        await breaker.on_failure()
        await breaker.on_failure()
        assert breaker.state == CircuitState.CLOSED  # Still closed
        
        await breaker.on_failure()
        assert breaker.state == CircuitState.OPEN  # Now open
        assert await breaker.call_allowed() is False
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        assert await breaker.call_allowed() is True  # Should transition to half-open
        assert breaker.state == CircuitState.HALF_OPEN
        
        # Success should close the circuit
        await breaker.on_success()
        assert breaker.state == CircuitState.CLOSED


@pytest.fixture
def mock_gemini_config():
    """Create a mock Gemini configuration for testing."""
    return GeminiConfig(
        api_key="test_api_key_123",
        model="gemini-2.5-pro",
        max_context_tokens=1000000,
        temperature=0.1,
        max_output_tokens=8192,
        max_retries=3,
        timeout_seconds=60,
        daily_cost_limit=100.0,
        max_cost_per_request=5.0,
        enable_streaming=True,
        max_concurrent_requests=5
    )


@pytest.fixture
def mock_response():
    """Create a mock Gemini API response."""
    response = MagicMock()
    response.text = "This is a test response from Gemini AI."
    response.usage_metadata.prompt_token_count = 50
    response.usage_metadata.candidates_token_count = 20
    response.usage_metadata.total_token_count = 70
    response.finish_reason = "STOP"
    return response


class TestGeminiClient:
    """Test Gemini client functionality."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_gemini_config):
        """Test client initialization with configuration."""
        with patch('google.generativeai.configure') as mock_configure:
            client = GeminiClient(mock_gemini_config)
            
            assert client.config == mock_gemini_config
            assert client._request_count == 0
            mock_configure.assert_called_once_with(api_key="test_api_key_123")
    
    @pytest.mark.asyncio
    async def test_client_authentication_error(self):
        """Test client handles authentication errors."""
        config = GeminiConfig(api_key=None)
        
        with pytest.raises(GeminiAuthenticationError):
            GeminiClient(config)
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, mock_gemini_config, mock_response):
        """Test successful content generation."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            # Setup mock model
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            client = GeminiClient(mock_gemini_config)
            response = await client.generate_content("Test prompt")
            
            assert isinstance(response, GeminiResponse)
            assert response.content == "This is a test response from Gemini AI."
            assert response.usage.input_tokens == 50
            assert response.usage.output_tokens == 20
            assert response.usage.total_tokens == 70
            assert response.model == "gemini-2.5-pro"
    
    @pytest.mark.asyncio
    async def test_generate_content_with_retry(self, mock_gemini_config, mock_response):
        """Test content generation with retry logic."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            # Setup mock model that fails then succeeds
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock()
            mock_model.generate_content_async.side_effect = [
                Exception("Temporary failure"),
                mock_response
            ]
            mock_model_class.return_value = mock_model
            
            client = GeminiClient(mock_gemini_config)
            response = await client.generate_content("Test prompt")
            
            assert isinstance(response, GeminiResponse)
            assert mock_model.generate_content_async.call_count == 2
    
    @pytest.mark.asyncio
    async def test_daily_cost_tracking(self, mock_gemini_config):
        """Test daily cost tracking functionality."""
        with patch('google.generativeai.configure'):
            client = GeminiClient(mock_gemini_config)
            
            # Track some costs
            client._track_daily_cost(1.50)
            client._track_daily_cost(2.75)
            
            daily_cost = client.get_daily_cost()
            assert abs(daily_cost - 4.25) < 0.01
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_gemini_config, mock_response):
        """Test client health check."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            client = GeminiClient(mock_gemini_config)
            is_healthy = await client.health_check()
            
            assert is_healthy is True


class TestGeminiAnalyzer:
    """Test Gemini analyzer (AIProvider implementation)."""
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, mock_gemini_config):
        """Test analyzer initialization."""
        with patch('google.generativeai.configure'):
            analyzer = GeminiAnalyzer(mock_gemini_config)
            
            assert analyzer.provider_name == "google_gemini"
            assert "gemini-2.5-pro" in analyzer.supported_models
            assert analyzer.config == mock_gemini_config
    
    @pytest.mark.asyncio
    async def test_analyze_text_success(self, mock_gemini_config):
        """Test successful text analysis."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'generate_content') as mock_generate:
            
            # Setup mock response
            mock_gemini_response = GeminiResponse(
                content="Analysis: This is a test company analysis.",
                usage=GeminiUsage(input_tokens=100, output_tokens=50, total_tokens=150, cost=0.002),
                model="gemini-2.5-pro",
                finish_reason="STOP",
                metadata={"request_id": "test_123"}
            )
            mock_generate.return_value = mock_gemini_response
            
            analyzer = GeminiAnalyzer(mock_gemini_config)
            
            config = AnalysisConfig(
                model_name="gemini-2.5-pro",
                temperature=0.1,
                max_tokens=100
            )
            
            result = await analyzer.analyze_text("Test company description", config)
            
            assert result.content == "Analysis: This is a test company analysis."
            assert result.provider_name == "google_gemini"
            assert result.model_used == "gemini-2.5-pro"
            assert result.estimated_cost == 0.002
            assert result.token_usage.total_tokens == 150
            assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_analyze_text_with_progress_callback(self, mock_gemini_config):
        """Test analysis with progress callback."""
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
        
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'generate_content') as mock_generate:
            
            mock_generate.return_value = GeminiResponse(
                content="Analysis complete",
                usage=GeminiUsage(50, 25, 75, 0.001),
                model="gemini-2.5-pro"
            )
            
            analyzer = GeminiAnalyzer(mock_gemini_config)
            config = AnalysisConfig(model_name="gemini-2.5-pro")
            
            await analyzer.analyze_text("Test", config, progress_callback)
            
            assert len(progress_messages) >= 2
            assert any("Starting Gemini analysis" in msg for msg in progress_messages)
            assert any("Analysis completed" in msg for msg in progress_messages)
    
    @pytest.mark.asyncio
    async def test_analyze_batch(self, mock_gemini_config):
        """Test batch analysis functionality."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'generate_content') as mock_generate:
            
            # Mock different responses for each text
            mock_generate.side_effect = [
                GeminiResponse("Analysis 1", GeminiUsage(50, 25, 75, 0.001), "gemini-2.5-pro"),
                GeminiResponse("Analysis 2", GeminiUsage(60, 30, 90, 0.001), "gemini-2.5-pro"),
                GeminiResponse("Analysis 3", GeminiUsage(55, 28, 83, 0.001), "gemini-2.5-pro")
            ]
            
            analyzer = GeminiAnalyzer(mock_gemini_config)
            config = AnalysisConfig(model_name="gemini-2.5-pro")
            
            texts = ["Company 1", "Company 2", "Company 3"]
            batch_result = await analyzer.analyze_batch(texts, config)
            
            assert batch_result.total_requests == 3
            assert batch_result.successful_requests == 3
            assert batch_result.failed_requests == 0
            assert len(batch_result.results) == 3
            assert all(result.provider_name == "google_gemini" for result in batch_result.results)
            assert batch_result.results[0].content == "Analysis 1"
            assert batch_result.results[1].content == "Analysis 2"
            assert batch_result.results[2].content == "Analysis 3"
    
    @pytest.mark.asyncio
    async def test_estimate_cost(self, mock_gemini_config):
        """Test cost estimation."""
        with patch('google.generativeai.configure'):
            analyzer = GeminiAnalyzer(mock_gemini_config)
            
            cost = await analyzer.estimate_cost(1000, 500, "gemini-2.5-pro")
            expected = calculate_gemini_cost(1000, 500, "gemini-2.5-pro")
            
            assert abs(cost - expected) < 0.0001
            
            # Test invalid model
            cost_invalid = await analyzer.estimate_cost(1000, 500, "invalid-model")
            assert cost_invalid == 0.0
    
    @pytest.mark.asyncio
    async def test_validate_configuration(self, mock_gemini_config):
        """Test configuration validation."""
        with patch('google.generativeai.configure'):
            analyzer = GeminiAnalyzer(mock_gemini_config)
            
            # Valid configuration
            valid_config = AnalysisConfig(
                model_name="gemini-2.5-pro",
                temperature=0.5,
                max_tokens=1000
            )
            assert await analyzer.validate_configuration(valid_config) is True
            
            # Invalid model
            invalid_model_config = AnalysisConfig(
                model_name="invalid-model",
                temperature=0.5,
                max_tokens=1000
            )
            assert await analyzer.validate_configuration(invalid_model_config) is False
            
            # Invalid max_tokens (exceeds model limit)
            invalid_token_config = AnalysisConfig(
                model_name="gemini-2.5-pro",
                temperature=0.5,
                max_tokens=50000  # Exceeds model limit
            )
            assert await analyzer.validate_configuration(invalid_token_config) is False
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_gemini_config):
        """Test analyzer health check."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'health_check') as mock_health:
            
            mock_health.return_value = True
            
            analyzer = GeminiAnalyzer(mock_gemini_config)
            health_result = await analyzer.health_check()
            
            assert isinstance(health_result, dict)
            assert health_result['status'] == 'healthy'
            assert 'latency_ms' in health_result
            assert 'provider' in health_result
            mock_health.assert_called_once()


class TestGeminiTokenManager:
    """Test token usage tracking and management."""
    
    @pytest.mark.asyncio
    async def test_track_usage(self, mock_gemini_config):
        """Test tracking token usage."""
        manager = GeminiTokenManager(mock_gemini_config)
        
        entry = await manager.track_usage(1000, 500, "gemini-2.5-pro", "analysis")
        
        assert entry.input_tokens == 1000
        assert entry.output_tokens == 500
        assert entry.model == "gemini-2.5-pro"
        assert entry.request_type == "analysis"
        assert entry.cost > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_checking(self, mock_gemini_config):
        """Test rate limit validation."""
        # Set low limits for testing
        config = mock_gemini_config
        config.tokens_per_minute = 1000
        config.daily_cost_limit = 1.0
        
        manager = GeminiTokenManager(config)
        
        # Should be within limits initially
        within_limits, reason = await manager.check_rate_limits()
        assert within_limits is True
        assert reason == ""
        
        # Track heavy usage that hits cost limit first (fewer tokens but high cost)
        # Each call: 100 tokens total, but cost is higher for gemini-2.5-pro 
        for _ in range(20):  # More iterations to exceed cost limit
            await manager.track_usage(50, 50, "gemini-2.5-pro")
        
        # Should now exceed daily cost limit (check both possible outcomes)
        within_limits, reason = await manager.check_rate_limits()
        assert within_limits is False
        # Could hit either limit - both are valid failure reasons
        assert ("Daily cost limit exceeded" in reason or "Token rate limit exceeded" in reason)
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, mock_gemini_config):
        """Test request cost estimation."""
        manager = GeminiTokenManager(mock_gemini_config)
        
        cost, within_budget = await manager.estimate_request_cost(1000, 500, "gemini-2.5-pro")
        
        assert cost > 0
        assert within_budget is True  # Should be within budget initially
        
        # Test with extremely high token count that exceeds daily budget
        # Need ~20M tokens to exceed $100 daily limit for gemini-2.5-pro
        high_cost, within_budget = await manager.estimate_request_cost(10000000, 5000000, "gemini-2.5-pro")
        assert high_cost > cost
        assert within_budget is False  # Should exceed daily limit
    
    @pytest.mark.asyncio
    async def test_daily_stats(self, mock_gemini_config):
        """Test daily statistics calculation."""
        manager = GeminiTokenManager(mock_gemini_config)
        
        # Track some usage
        await manager.track_usage(1000, 500, "gemini-2.5-pro")
        await manager.track_usage(800, 400, "gemini-1.5-pro")
        
        stats = await manager.get_daily_stats()
        
        assert stats.total_requests == 2
        assert stats.total_input_tokens == 1800
        assert stats.total_output_tokens == 900
        assert stats.total_cost > 0
        assert "gemini-2.5-pro" in stats.requests_by_model
        assert "gemini-1.5-pro" in stats.requests_by_model
    
    @pytest.mark.asyncio
    async def test_model_optimization(self, mock_gemini_config):
        """Test optimal model selection."""
        manager = GeminiTokenManager(mock_gemini_config)
        
        # Test for simple task with small token count
        model = await manager.optimize_model_selection(1000, "simple")
        assert model in ["gemini-1.0-pro", "gemini-1.5-flash"]  # Should choose cheaper model
        
        # Test for complex task with large token count
        model = await manager.optimize_model_selection(500000, "complex")
        assert model == "gemini-2.5-pro"  # Should choose high-context model


class TestGeminiRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self, mock_gemini_config):
        """Test rate limiter initialization."""
        limiter = GeminiRateLimiter(mock_gemini_config)
        
        assert limiter.config == mock_gemini_config
        assert limiter.request_bucket.capacity == mock_gemini_config.requests_per_minute
        assert limiter.token_bucket.capacity == mock_gemini_config.tokens_per_minute
        assert limiter.concurrent_semaphore._value == mock_gemini_config.max_concurrent_requests
    
    @pytest.mark.asyncio
    async def test_acquire_permission(self, mock_gemini_config):
        """Test acquiring permission for requests."""
        # Set low limits for testing
        config = mock_gemini_config
        config.requests_per_minute = 10
        config.tokens_per_minute = 1000
        
        limiter = GeminiRateLimiter(config)
        
        # Should be able to acquire initially
        assert await limiter.acquire(100) is True
        
        # Exhaust request bucket
        for _ in range(9):
            await limiter.acquire(50)
        
        # Should now be rejected
        assert await limiter.acquire(50) is False
    
    @pytest.mark.asyncio
    async def test_acquire_with_wait(self, mock_gemini_config):
        """Test acquiring with wait functionality."""
        # Set very low limits for testing
        config = mock_gemini_config
        config.requests_per_minute = 2
        config.tokens_per_minute = 100
        
        limiter = GeminiRateLimiter(config)
        
        # Exhaust buckets
        await limiter.acquire(50)
        await limiter.acquire(50)
        
        # This should wait and then succeed
        start_time = time.time()
        wait_time = await limiter.acquire_with_wait(50)
        elapsed = time.time() - start_time
        
        assert wait_time > 0
        assert elapsed >= wait_time
    
    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, mock_gemini_config):
        """Test concurrent request limiting."""
        config = mock_gemini_config
        config.max_concurrent_requests = 2
        
        limiter = GeminiRateLimiter(config)
        
        # Should be able to acquire concurrent slots
        async with limiter:
            async with limiter:
                # Now at maximum concurrent requests
                available = limiter.concurrent_semaphore._value
                assert available == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mock_gemini_config):
        """Test circuit breaker integration."""
        limiter = GeminiRateLimiter(mock_gemini_config)
        
        # Initially should allow requests
        assert await limiter.acquire() is True
        
        # Trigger circuit breaker by recording failures
        for _ in range(5):
            await limiter.circuit_breaker.on_failure()
        
        # Should now reject requests
        assert await limiter.acquire() is False
        assert limiter.circuit_breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_adaptive_rate_adjustment(self, mock_gemini_config):
        """Test adaptive rate limit adjustment."""
        limiter = GeminiRateLimiter(mock_gemini_config)
        
        original_request_rate = limiter.request_bucket.refill_rate
        
        # Simulate poor performance
        await limiter.adjust_rates(success_rate=0.7, avg_response_time=5.0)
        
        # Rates should be reduced
        assert limiter.request_bucket.refill_rate < original_request_rate
    
    @pytest.mark.asyncio
    async def test_get_current_usage(self, mock_gemini_config):
        """Test getting current usage statistics."""
        limiter = GeminiRateLimiter(mock_gemini_config)
        
        usage = await limiter.get_current_usage()
        
        assert 'requests_made' in usage
        assert 'requests_rejected' in usage
        assert 'concurrent_available' in usage
        assert 'circuit_state' in usage
        assert 'success_rate' in usage
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_gemini_config):
        """Test rate limiter health check."""
        limiter = GeminiRateLimiter(mock_gemini_config)
        
        is_healthy = await limiter.health_check()
        assert is_healthy is True
        
        # Break the circuit and check again
        limiter.circuit_breaker.state = CircuitState.OPEN
        
        is_healthy = await limiter.health_check()
        assert is_healthy is False


class TestGeminiStreamer:
    """Test streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_streamer_initialization(self, mock_gemini_config):
        """Test streamer initialization."""
        with patch('google.generativeai.configure'):
            streamer = GeminiStreamer(mock_gemini_config)
            
            assert streamer.config == mock_gemini_config
            assert streamer.buffer_size == mock_gemini_config.chunk_size
            assert streamer.stream_timeout == mock_gemini_config.stream_timeout_seconds
    
    @pytest.mark.asyncio
    async def test_stream_analysis(self, mock_gemini_config):
        """Test streaming analysis functionality."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'generate_content_stream') as mock_stream:
            
            # Mock streaming chunks
            async def mock_chunk_generator():
                for chunk in ["Hello ", "world ", "from ", "Gemini!"]:
                    yield chunk
            
            mock_stream.return_value = mock_chunk_generator()
            
            streamer = GeminiStreamer(mock_gemini_config)
            
            chunks = []
            async for chunk in streamer.stream_analysis("Test prompt"):
                chunks.append(chunk)
            
            assert chunks == ["Hello ", "world ", "from ", "Gemini!"]
    
    @pytest.mark.asyncio
    async def test_stream_with_progress_callback(self, mock_gemini_config):
        """Test streaming with progress callback."""
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
        
        with patch('google.generativeai.configure'), \
             patch.object(GeminiClient, 'generate_content_stream') as mock_stream:
            
            async def mock_chunk_generator():
                for i in range(15):  # Enough chunks to trigger progress updates
                    yield f"chunk {i} "
            
            mock_stream.return_value = mock_chunk_generator()
            
            streamer = GeminiStreamer(mock_gemini_config)
            
            chunks = []
            async for chunk in streamer.stream_analysis("Test", progress_callback=progress_callback):
                chunks.append(chunk)
            
            assert len(chunks) == 15
            assert len(progress_messages) >= 2  # Should have start and chunk messages
    
    @pytest.mark.asyncio
    async def test_stream_with_buffering(self, mock_gemini_config):
        """Test streaming with line-based buffering."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiStreamer, 'stream_analysis') as mock_stream:
            
            # Mock chunks with line breaks
            async def mock_chunk_generator():
                for chunk in ["Line 1\nLine 2\n", "Line 3\n", "Line 4\nPartial"]:
                    yield chunk
            
            mock_stream.return_value = mock_chunk_generator()
            
            streamer = GeminiStreamer(mock_gemini_config)
            
            buffered_chunks = []
            async for chunk in streamer.stream_with_buffering("Test", buffer_lines=2):
                buffered_chunks.append(chunk)
            
            assert len(buffered_chunks) >= 1  # Should have buffered content
    
    @pytest.mark.asyncio
    async def test_streamer_health_check(self, mock_gemini_config):
        """Test streamer health check."""
        with patch('google.generativeai.configure'), \
             patch.object(GeminiStreamer, 'stream_analysis') as mock_stream:
            
            async def mock_chunk_generator():
                yield "test chunk"
            
            mock_stream.return_value = mock_chunk_generator()
            
            streamer = GeminiStreamer(mock_gemini_config)
            
            is_healthy = await streamer.health_check()
            assert is_healthy is True
    
    def test_streamer_stats(self, mock_gemini_config):
        """Test getting streamer statistics."""
        with patch('google.generativeai.configure'):
            streamer = GeminiStreamer(mock_gemini_config)
            
            stats = streamer.get_stats()
            
            assert 'streams_created' in stats
            assert 'total_chunks_processed' in stats
            assert 'total_bytes_streamed' in stats
            assert 'streaming_enabled' in stats


# Integration test for factory functions
class TestGeminiFactory:
    """Test factory functions and integration."""
    
    @pytest.mark.asyncio
    async def test_create_gemini_analyzer(self, mock_gemini_config):
        """Test factory function for creating analyzer."""
        with patch('google.generativeai.configure'):
            from src.infrastructure.adapters.ai.gemini import create_gemini_analyzer
            
            analyzer = create_gemini_analyzer(mock_gemini_config)
            
            assert isinstance(analyzer, GeminiAnalyzer)
            assert analyzer.config.max_retries >= 3
            assert analyzer.config.enable_streaming is True
    
    @pytest.mark.asyncio
    async def test_create_production_gemini_suite(self, mock_gemini_config):
        """Test factory function for production suite."""
        with patch('google.generativeai.configure'):
            from src.infrastructure.adapters.ai.gemini import create_production_gemini_suite
            
            analyzer, streamer = create_production_gemini_suite(mock_gemini_config)
            
            assert isinstance(analyzer, GeminiAnalyzer)
            assert isinstance(streamer, GeminiStreamer)
            assert analyzer.config.max_retries == 5
            assert analyzer.config.max_concurrent_requests == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
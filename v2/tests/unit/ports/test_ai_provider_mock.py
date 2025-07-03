"""
Unit tests for mock AI provider implementation.

Tests all aspects of the AIProvider interface using comprehensive mock
implementations to validate interface compliance and behavior.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import AsyncIterator, Dict, Any, List, Callable, Optional
from unittest.mock import Mock
from datetime import datetime
import json

from src.core.ports.ai_provider import (
    AIProvider, AIProviderException, RateLimitedException,
    QuotaExceededException, ModelNotAvailableException,
    InvalidConfigurationException, ProviderTimeoutException,
    AIProviderFeatures
)
from src.core.domain.value_objects.ai_config import (
    AnalysisConfig, ModelInfo, ModelType, StreamingConfig
)
from src.core.domain.value_objects.ai_response import (
    AnalysisResult, StreamingChunk, ResponseStatus, FinishReason,
    TokenUsage, AnalysisError
)
from src.core.ports.progress import ProgressTracker


class MockAIProvider(AIProvider):
    """
    Mock AI provider for testing.
    
    Generates realistic test data and simulates various
    AI provider scenarios including successes, failures, and rate limits.
    """
    
    def __init__(
        self,
        simulate_latency: bool = False,
        simulate_errors: bool = False,
        cost_per_token: float = 0.001,
        error_rate: float = 0.1
    ):
        self.simulate_latency = simulate_latency
        self.simulate_errors = simulate_errors
        self.cost_per_token = cost_per_token
        self.error_rate = error_rate
        
        # Mock statistics
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.error_count = 0
        self.last_request_time = None
        
        # Track if we're in context manager
        self._in_context = False
        
        # Pre-defined responses for testing
        self.responses = {
            "company_analysis": {
                "content": """Based on the provided information, this company appears to be a B2B SaaS provider 
                focused on payment processing solutions. Key insights:
                
                1. Business Model: Transaction-based revenue with subscription components
                2. Market Position: Competing with established players like Stripe and Square
                3. Technical Sophistication: High-level API-first architecture
                4. Growth Stage: Series B funding stage with rapid customer acquisition
                5. Competitive Advantages: Developer-friendly API, competitive pricing
                
                The company shows strong potential for continued growth in the fintech sector.""".strip(),
                "tokens": 150
            },
            "industry_classification": {
                "content": "Financial Technology (FinTech) - Payment Processing",
                "tokens": 20
            },
            "competitor_analysis": {
                "content": """Direct competitors include:
                1. Stripe - Similar developer-first approach, stronger brand recognition
                2. Square - Focus on SMB market, established merchant services
                3. Adyen - Enterprise-focused platform, global payment processing
                4. PayPal - Established market leader, consumer and business solutions
                5. Braintree - Developer-friendly APIs, strong mobile payment solutions
                
                Competitive positioning requires focus on unique value propositions.""".strip(),
                "tokens": 120
            },
            "similarity_analysis": {
                "content": """{"similarity_score": 0.85, "key_similarities": ["B2B SaaS model", "API-first approach", "Fintech sector"], "differences": ["Market focus", "Pricing strategy", "Geographic coverage"]}""",
                "tokens": 80
            }
        }
    
    async def get_provider_info(self) -> ModelInfo:
        """Return mock provider information"""
        if not self._in_context:
            raise InvalidConfigurationException("Provider must be used as async context manager")
        
        return ModelInfo(
            provider_name="MockAIProvider",
            provider_version="2.0.0",
            available_models=[
                "mock-analysis-v1", "mock-fast-v1", "mock-premium-v1",
                "mock-company-specialist", "mock-similarity-expert"
            ],
            model_types={
                "mock-analysis-v1": ModelType.TEXT_ANALYSIS,
                "mock-fast-v1": ModelType.TEXT_ANALYSIS,
                "mock-premium-v1": ModelType.TEXT_ANALYSIS,
                "mock-company-specialist": ModelType.TEXT_ANALYSIS,
                "mock-similarity-expert": ModelType.TEXT_ANALYSIS
            },
            default_models={
                ModelType.TEXT_ANALYSIS: "mock-analysis-v1",
                ModelType.CHAT: "mock-analysis-v1",
                ModelType.COMPLETION: "mock-fast-v1"
            },
            supports_streaming=True,
            supports_system_prompts=True,
            supports_function_calling=False,
            supports_vision=False,
            supports_json_mode=True,
            max_context_tokens={
                "mock-analysis-v1": 128000,
                "mock-fast-v1": 32000,
                "mock-premium-v1": 200000,
                "mock-company-specialist": 100000,
                "mock-similarity-expert": 50000
            },
            max_output_tokens={
                "mock-analysis-v1": 4096,
                "mock-fast-v1": 1024,
                "mock-premium-v1": 8192,
                "mock-company-specialist": 2048,
                "mock-similarity-expert": 1024
            },
            input_token_cost={
                "mock-analysis-v1": 0.001,
                "mock-fast-v1": 0.0005,
                "mock-premium-v1": 0.003,
                "mock-company-specialist": 0.002,
                "mock-similarity-expert": 0.001
            },
            output_token_cost={
                "mock-analysis-v1": 0.002,
                "mock-fast-v1": 0.001,
                "mock-premium-v1": 0.006,
                "mock-company-specialist": 0.004,
                "mock-similarity-expert": 0.002
            },
            requests_per_minute=100,
            requests_per_day=10000,
            available_regions=["us-east-1", "us-west-2", "eu-west-1"]
        )
    
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> AnalysisResult:
        """Mock text analysis with realistic behavior"""
        
        if not self._in_context:
            raise InvalidConfigurationException("Provider must be used as async context manager")
        
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        
        if progress_callback:
            progress_callback(f"Starting analysis of {len(text)} characters", 0.0, "Initializing")
        
        # Simulate latency
        if self.simulate_latency:
            await asyncio.sleep(0.1)  # 100ms latency
        
        if progress_callback:
            progress_callback("Processing with AI model", 0.5, "Analyzing content")
        
        # Simulate errors occasionally
        if self.simulate_errors and self.request_count % 10 == 0:
            self.error_count += 1
            raise RateLimitedException("MockAIProvider", retry_after=30)
        
        # Check model availability
        provider_info = await self.get_provider_info()
        if config.model_name not in provider_info.available_models:
            raise ModelNotAvailableException("MockAIProvider", config.model_name)
        
        # Generate mock response based on content
        response_data = self._select_response(text, config)
        content = response_data["content"]
        base_tokens = response_data["tokens"]
        
        # Calculate realistic token usage
        prompt_tokens = len(text.split()) + (len(system_prompt.split()) if system_prompt else 0)
        completion_tokens = base_tokens
        total_tokens = prompt_tokens + completion_tokens
        
        # Update statistics
        self.total_tokens_used += total_tokens
        cost = await self.estimate_cost(prompt_tokens, completion_tokens, config.model_name)
        self.total_cost += cost
        
        if progress_callback:
            progress_callback("Analysis complete", 1.0, f"Generated {completion_tokens} tokens")
        
        return AnalysisResult(
            content=content,
            status=ResponseStatus.SUCCESS,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ),
            model_used=config.model_name,
            provider_name="MockAIProvider",
            request_id=f"mock_req_{self.request_count}",
            estimated_cost=cost,
            confidence_score=0.85 + (0.1 * (hash(content) % 10) / 10),
            finish_reason=FinishReason.STOP,
            processing_time=0.1 if self.simulate_latency else 0.01,
            content_length=len(content),
            provider_metadata={
                "mock": True,
                "request_number": self.request_count,
                "model_tier": self._get_model_tier(config.model_name)
            }
        )
    
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        streaming_config: Optional[StreamingConfig] = None
    ) -> AsyncIterator[StreamingChunk]:
        """Mock streaming response"""
        
        if not self._in_context:
            raise InvalidConfigurationException("Provider must be used as async context manager")
        
        # Get the full response first
        result = await self.analyze_text(text, config, system_prompt)
        words = result.content.split()
        
        chunk_size = streaming_config.chunk_size if streaming_config else 1
        
        # Stream it in chunks
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            if i + chunk_size < len(words):
                chunk_content += " "
            
            if self.simulate_latency:
                await asyncio.sleep(0.02)  # 20ms per chunk
            
            is_final = (i + chunk_size >= len(words))
            
            chunk = StreamingChunk(
                content=chunk_content,
                chunk_index=i // chunk_size,
                is_final=is_final,
                tokens_in_chunk=len(chunk_words),
                cumulative_tokens=result.token_usage.prompt_tokens + min(i + chunk_size, len(words))
            )
            
            # Add final information to last chunk
            if is_final:
                chunk.final_token_usage = result.token_usage
                chunk.finish_reason = result.finish_reason
            
            yield chunk
    
    async def analyze_batch(
        self,
        texts: List[str],
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> None:  # Return type to be implemented based on BatchResult
        """Mock batch analysis - placeholder implementation"""
        # This would return a BatchResult in full implementation
        results = []
        
        for i, text in enumerate(texts):
            if progress_callback:
                progress = (i + 1) / len(texts)
                progress_callback(f"Processing text {i + 1}/{len(texts)}", progress, f"Analyzing batch")
            
            result = await self.analyze_text(text, config, system_prompt)
            results.append(result)
        
        return results  # Simplified return for mock
    
    async def count_tokens(self, text: str, model_name: str) -> int:
        """Mock token counting (simplified word-based)"""
        # Simple approximation: 1 token ≈ 0.75 words
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    async def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ) -> float:
        """Mock cost estimation with realistic pricing"""
        provider_info = await self.get_provider_info()
        
        input_cost = provider_info.input_token_cost.get(model_name, 0.001)
        output_cost = provider_info.output_token_cost.get(model_name, 0.002)
        
        return (input_tokens * input_cost / 1000) + (output_tokens * output_cost / 1000)
    
    async def validate_configuration(self, config: AnalysisConfig) -> bool:
        """Mock validation with realistic checks"""
        provider_info = await self.get_provider_info()
        
        # Check model availability
        if config.model_name not in provider_info.available_models:
            raise InvalidConfigurationException(f"Model {config.model_name} not available")
        
        # Check token limits
        max_output = provider_info.max_output_tokens.get(config.model_name, 4096)
        if config.max_tokens and config.max_tokens > max_output:
            raise InvalidConfigurationException(f"max_tokens exceeds limit: {max_output}")
        
        # Check temperature range
        if not 0.0 <= config.temperature <= 2.0:
            raise InvalidConfigurationException("temperature must be between 0.0 and 2.0")
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check with realistic metrics"""
        avg_latency = 100 if self.simulate_latency else 10
        error_rate = self.error_rate if self.simulate_errors else 0.0
        
        status = "healthy"
        if error_rate > 0.1:
            status = "degraded"
        if error_rate > 0.5:
            status = "unhealthy"
        
        return {
            "status": status,
            "latency_ms": avg_latency,
            "requests_per_minute": max(60 - self.request_count, 0),  # Simulate decreasing capacity
            "error_rate": error_rate,
            "quota_remaining": max(1000 - self.request_count, 0),
            "last_error": "Rate limit exceeded" if self.error_count > 0 else None,
            "requests_processed": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "models_available": 5,
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def close(self) -> None:
        """Clean up resources"""
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.error_count = 0
        self._in_context = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._in_context = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _select_response(self, text: str, config: AnalysisConfig) -> Dict[str, Any]:
        """Select appropriate response based on input"""
        text_lower = text.lower()
        
        if "company" in text_lower and ("analysis" in text_lower or "analyze" in text_lower):
            return self.responses["company_analysis"]
        elif "industry" in text_lower or "classification" in text_lower:
            return self.responses["industry_classification"]
        elif "competitor" in text_lower or "competition" in text_lower:
            return self.responses["competitor_analysis"]
        elif "similar" in text_lower or config.response_format == "json":
            return self.responses["similarity_analysis"]
        else:
            # Generic response
            return {
                "content": f"Mock analysis of: {text[:100]}...\nGenerated by {config.model_name}",
                "tokens": 25 + len(text.split()) // 10
            }
    
    def _get_model_tier(self, model_name: str) -> str:
        """Get model tier for metadata"""
        if "fast" in model_name:
            return "fast"
        elif "premium" in model_name:
            return "premium"
        elif "specialist" in model_name:
            return "specialist"
        else:
            return "standard"


class TestMockAIProvider:
    """Test suite for MockAIProvider implementation"""
    
    @pytest_asyncio.fixture
    async def provider(self):
        """Create a mock provider for testing"""
        provider = MockAIProvider(
            simulate_latency=False,  # Fast for testing
            simulate_errors=False,   # No errors by default
            cost_per_token=0.001
        )
        async with provider:
            yield provider
    
    @pytest.fixture
    def basic_config(self):
        """Basic analysis configuration"""
        return AnalysisConfig(
            model_name="mock-analysis-v1",
            temperature=0.7,
            max_tokens=1000
        )
    
    @pytest.fixture
    def company_analysis_config(self):
        """Company analysis configuration"""
        return AnalysisConfig.for_company_analysis()
    
    @pytest.mark.asyncio
    async def test_provider_info(self, provider):
        """Test provider information retrieval"""
        info = await provider.get_provider_info()
        
        assert isinstance(info, ModelInfo)
        assert info.provider_name == "MockAIProvider"
        assert len(info.available_models) >= 5
        assert "mock-analysis-v1" in info.available_models
        assert info.supports_streaming is True
        assert info.supports_json_mode is True
        assert info.max_context_tokens["mock-analysis-v1"] == 128000
    
    @pytest.mark.asyncio
    async def test_basic_text_analysis(self, provider, basic_config):
        """Test basic text analysis functionality"""
        text = "Analyze this company: Stripe Inc. They provide payment processing services."
        
        result = await provider.analyze_text(text, basic_config)
        
        assert isinstance(result, AnalysisResult)
        assert result.status == ResponseStatus.SUCCESS
        assert result.model_used == "mock-analysis-v1"
        assert result.provider_name == "MockAIProvider"
        assert len(result.content) > 0
        assert result.token_usage.total_tokens > 0
        assert result.estimated_cost > 0
        assert result.finish_reason == FinishReason.STOP
        assert result.is_successful()
        assert result.is_complete()
    
    @pytest.mark.asyncio
    async def test_company_analysis_response(self, provider, company_analysis_config):
        """Test company-specific analysis response"""
        text = "Please analyze this company and provide detailed business insights."
        
        result = await provider.analyze_text(text, company_analysis_config)
        
        assert "B2B SaaS" in result.content
        assert "Business Model" in result.content
        assert result.confidence_score >= 0.8
        assert result.token_usage.completion_tokens >= 100  # Substantial response
    
    @pytest.mark.asyncio
    async def test_streaming_analysis(self, provider, basic_config):
        """Test streaming analysis functionality"""
        text = "Provide a streaming analysis of this company data."
        streaming_config = StreamingConfig(chunk_size=2)
        
        chunks = []
        async for chunk in provider.analyze_text_streaming(text, basic_config, streaming_config=streaming_config):
            chunks.append(chunk)
            assert isinstance(chunk, StreamingChunk)
            assert chunk.chunk_index >= 0
            assert len(chunk.content) > 0
        
        # Verify streaming behavior
        assert len(chunks) > 1  # Multiple chunks
        assert chunks[-1].is_final  # Last chunk marked as final
        assert chunks[-1].final_token_usage is not None
        assert chunks[-1].finish_reason == FinishReason.STOP
        
        # Verify content consistency
        full_content = "".join(chunk.content for chunk in chunks)
        assert len(full_content.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, provider, basic_config):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(message: str, progress: float, details: str = None):
            progress_updates.append((message, progress, details))
        
        text = "Analyze this text with progress tracking."
        result = await provider.analyze_text(text, basic_config, progress_callback=progress_callback)
        
        assert result.is_successful()
        assert len(progress_updates) >= 2  # At least start and end
        assert progress_updates[0][1] == 0.0  # First progress is 0%
        assert progress_updates[-1][1] == 1.0  # Final progress is 100%
        assert "complete" in progress_updates[-1][0].lower()
    
    @pytest.mark.asyncio
    async def test_token_counting(self, provider):
        """Test token counting functionality"""
        text = "This is a sample text for token counting."
        model_name = "mock-analysis-v1"
        
        token_count = await provider.count_tokens(text, model_name)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        # Roughly 1 token per 0.75 words
        word_count = len(text.split())
        expected_tokens = int(word_count / 0.75)
        assert abs(token_count - expected_tokens) <= 2  # Allow small variance
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, provider):
        """Test cost estimation functionality"""
        input_tokens = 100
        output_tokens = 200
        model_name = "mock-analysis-v1"
        
        cost = await provider.estimate_cost(input_tokens, output_tokens, model_name)
        
        assert isinstance(cost, float)
        assert cost > 0
        # Verify cost calculation: (100 * 0.001 / 1000) + (200 * 0.002 / 1000) = 0.0005
        expected_cost = (input_tokens * 0.001 / 1000) + (output_tokens * 0.002 / 1000)
        assert abs(cost - expected_cost) < 0.0001
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, provider):
        """Test configuration validation"""
        # Valid configuration
        valid_config = AnalysisConfig(
            model_name="mock-analysis-v1",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert await provider.validate_configuration(valid_config) is True
        
        # Invalid model
        invalid_model_config = AnalysisConfig(
            model_name="nonexistent-model",
            temperature=0.5
        )
        
        with pytest.raises(InvalidConfigurationException, match="not available"):
            await provider.validate_configuration(invalid_model_config)
        
        # Invalid temperature
        invalid_temp_config = AnalysisConfig(
            model_name="mock-analysis-v1",
            temperature=3.0  # Too high
        )
        
        with pytest.raises(InvalidConfigurationException, match="temperature"):
            await provider.validate_configuration(invalid_temp_config)
        
        # Invalid max_tokens
        invalid_tokens_config = AnalysisConfig(
            model_name="mock-analysis-v1",
            max_tokens=10000  # Exceeds limit
        )
        
        with pytest.raises(InvalidConfigurationException, match="exceeds limit"):
            await provider.validate_configuration(invalid_tokens_config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, provider):
        """Test health check functionality"""
        # Make a few requests first
        config = AnalysisConfig(model_name="mock-analysis-v1")
        await provider.analyze_text("Test 1", config)
        await provider.analyze_text("Test 2", config)
        
        health = await provider.health_check()
        
        assert isinstance(health, dict)
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "latency_ms" in health
        assert "requests_per_minute" in health
        assert "error_rate" in health
        assert health["requests_processed"] >= 2
        assert health["total_tokens_used"] > 0
        assert health["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_context_manager_requirement(self):
        """Test that provider requires context manager usage"""
        provider = MockAIProvider()
        
        config = AnalysisConfig(model_name="mock-analysis-v1")
        
        with pytest.raises(InvalidConfigurationException, match="context manager"):
            await provider.analyze_text("test", config)
    
    @pytest.mark.asyncio
    async def test_model_not_available_error(self, provider):
        """Test model not available error handling"""
        config = AnalysisConfig(model_name="nonexistent-model")
        
        with pytest.raises(ModelNotAvailableException) as exc_info:
            await provider.analyze_text("test", config)
        
        assert exc_info.value.provider == "MockAIProvider"
        assert exc_info.value.model_name == "nonexistent-model"
    
    @pytest.mark.asyncio
    async def test_batch_analysis(self, provider, basic_config):
        """Test batch analysis functionality"""
        texts = [
            "Analyze company A",
            "Analyze company B", 
            "Analyze company C"
        ]
        
        progress_updates = []
        def progress_callback(message: str, progress: float, details: str = None):
            progress_updates.append((message, progress, details))
        
        results = await provider.analyze_batch(texts, basic_config, progress_callback=progress_callback)
        
        assert len(results) == len(texts)
        assert all(isinstance(result, AnalysisResult) for result in results)
        assert all(result.is_successful() for result in results)
        assert len(progress_updates) >= len(texts)  # Progress for each text
    
    @pytest.mark.asyncio
    async def test_json_response_format(self, provider):
        """Test JSON response format handling"""
        config = AnalysisConfig(
            model_name="mock-similarity-expert",
            response_format="json",
            temperature=0.1
        )
        
        text = "Compare these companies for similarity analysis."
        result = await provider.analyze_text(text, config)
        
        assert result.is_successful()
        # Should get similarity analysis response which is JSON
        json_content = result.extract_json()
        assert json_content is not None
        assert "similarity_score" in json_content
    
    @pytest.mark.asyncio
    async def test_different_model_tiers(self, provider):
        """Test different model performance characteristics"""
        text = "Analyze this company information."
        
        # Fast model - should be cheaper and faster
        fast_config = AnalysisConfig(model_name="mock-fast-v1")
        fast_result = await provider.analyze_text(text, fast_config)
        
        # Premium model - should be more expensive
        premium_config = AnalysisConfig(model_name="mock-premium-v1")
        premium_result = await provider.analyze_text(text, premium_config)
        
        assert fast_result.estimated_cost < premium_result.estimated_cost
        assert fast_result.provider_metadata["model_tier"] == "fast"
        assert premium_result.provider_metadata["model_tier"] == "premium"


class TestMockAIProviderErrorScenarios:
    """Test error scenarios with mock AI provider"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self):
        """Test rate limiting error simulation"""
        provider = MockAIProvider(simulate_errors=True)
        
        config = AnalysisConfig(model_name="mock-analysis-v1")
        
        async with provider:
            # First 9 requests should succeed
            for i in range(9):
                result = await provider.analyze_text(f"Test {i}", config)
                assert result.status == ResponseStatus.SUCCESS
            
            # 10th request should trigger rate limit
            with pytest.raises(RateLimitedException) as exc_info:
                await provider.analyze_text("Test 10", config)
            
            assert exc_info.value.provider == "MockAIProvider"
            assert exc_info.value.retry_after == 30
    
    @pytest.mark.asyncio
    async def test_latency_simulation(self):
        """Test latency simulation"""
        provider = MockAIProvider(simulate_latency=True)
        
        config = AnalysisConfig(model_name="mock-analysis-v1")
        
        async with provider:
            start_time = time.time()
            result = await provider.analyze_text("Test with latency", config)
            end_time = time.time()
            
            assert result.is_successful()
            assert end_time - start_time >= 0.1  # At least 100ms latency
            assert result.processing_time >= 0.1


@pytest.mark.asyncio
async def test_interface_compliance():
    """Test that MockAIProvider fully implements AIProvider interface"""
    provider = MockAIProvider()
    
    # Verify it's recognized as AIProvider
    assert isinstance(provider, AIProvider)
    
    # Verify all required methods exist
    required_methods = [
        'get_provider_info', 'analyze_text', 'analyze_text_streaming',
        'analyze_batch', 'count_tokens', 'estimate_cost',
        'validate_configuration', 'health_check', 'close',
        '__aenter__', '__aexit__'
    ]
    
    for method_name in required_methods:
        assert hasattr(provider, method_name)
        assert callable(getattr(provider, method_name))


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
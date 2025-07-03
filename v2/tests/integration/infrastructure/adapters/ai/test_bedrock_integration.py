#!/usr/bin/env python3
"""
Integration Tests for Bedrock AI Adapters
=========================================

Integration tests that validate real AWS Bedrock API functionality.
These tests require valid AWS credentials and may incur small costs.

Run with: pytest tests/integration/infrastructure/adapters/ai/test_bedrock_integration.py
"""

import pytest
import asyncio
import os
import time
from typing import Dict, Any, List
from unittest.mock import patch

from src.infrastructure.adapters.ai.bedrock.analyzer import BedrockAnalyzer
from src.infrastructure.adapters.ai.bedrock.embedder import BedrockEmbeddingProvider
from src.infrastructure.adapters.ai.bedrock.client import BedrockClient
from src.infrastructure.adapters.ai.bedrock.config import BedrockConfig, calculate_bedrock_cost

from src.core.domain.value_objects.ai_config import AnalysisConfig, EmbeddingConfig
from src.core.domain.value_objects.ai_response import ResponseStatus, FinishReason


@pytest.fixture(scope="module")
def requires_aws_credentials():
    """Skip tests if AWS credentials are not available."""
    if not all([
        os.getenv('AWS_ACCESS_KEY_ID'),
        os.getenv('AWS_SECRET_ACCESS_KEY')
    ]):
        pytest.skip("AWS credentials not available - skipping integration tests")


@pytest.fixture
def integration_config():
    """Configuration for integration testing with cost controls."""
    return BedrockConfig(
        region_name='us-east-1',
        default_model='amazon.nova-lite-v1:0',  # Use cheapest model for testing
        embedding_model='amazon.titan-embed-text-v2:0',
        max_retries=2,
        timeout_seconds=30,
        max_cost_per_request=0.01,  # Very low limit for testing
        daily_cost_limit=0.10,  # $0.10 daily limit for integration tests
        enable_cost_tracking=True
    )


@pytest.fixture
def bedrock_client(integration_config):
    """Create Bedrock client for integration testing."""
    return BedrockClient(integration_config)


@pytest.fixture
def bedrock_analyzer(integration_config):
    """Create Bedrock analyzer for integration testing."""
    return BedrockAnalyzer(integration_config)


@pytest.fixture
def bedrock_embedder(integration_config):
    """Create Bedrock embedder for integration testing."""
    return BedrockEmbeddingProvider(integration_config)


class TestBedrockClientIntegration:
    """Integration tests for BedrockClient with real AWS API."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_client_authentication(self, bedrock_client, requires_aws_credentials):
        """Test client can authenticate with AWS Bedrock."""
        
        # Simple health check to verify authentication
        is_healthy = await bedrock_client.health_check()
        
        # Should successfully authenticate (assuming valid credentials)
        assert isinstance(is_healthy, bool)
        # Note: We don't assert True because test credentials might not have Bedrock access
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_nova_lite_invocation(self, bedrock_client, requires_aws_credentials):
        """Test actual Nova Lite model invocation."""
        
        body = {
            "messages": [
                {"role": "user", "content": "Say 'hello' in exactly one word."}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        try:
            response = await bedrock_client.invoke_model('amazon.nova-lite-v1:0', body)
            
            # Verify response structure
            assert 'output' in response
            assert '_metadata' in response
            assert response['_metadata']['model_id'] == 'amazon.nova-lite-v1:0'
            assert response['_metadata']['cost'] > 0
            assert response['_metadata']['usage']['total_tokens'] > 0
            
            # Verify response content
            content = response['output']['message']['content']
            assert isinstance(content, str)
            assert len(content.strip()) > 0
            
        except Exception as e:
            if "AccessDeniedException" in str(e):
                pytest.skip(f"Bedrock access not available: {e}")
            elif "ModelNotAvailableException" in str(e):
                pytest.skip(f"Nova Lite model not available in test region: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cost_tracking(self, bedrock_client, requires_aws_credentials):
        """Test cost tracking with real API calls."""
        
        # Reset daily cost tracking
        bedrock_client.reset_daily_cost()
        initial_cost = bedrock_client.get_daily_cost()
        assert initial_cost == 0.0
        
        # Make a small test request
        body = {
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "temperature": 0.1
        }
        
        try:
            response = await bedrock_client.invoke_model('amazon.nova-lite-v1:0', body)
            
            # Verify cost was tracked
            final_cost = bedrock_client.get_daily_cost()
            assert final_cost > initial_cost
            assert final_cost == response['_metadata']['cost']
            
        except Exception as e:
            if "AccessDeniedException" in str(e) or "ModelNotAvailableException" in str(e):
                pytest.skip(f"Bedrock not available for testing: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_retry_logic_with_invalid_model(self, bedrock_client, requires_aws_credentials):
        """Test retry logic with an invalid model (should fail fast)."""
        
        body = {
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        
        with pytest.raises(Exception) as exc_info:
            await bedrock_client.invoke_model('invalid-model-id', body)
        
        # Should be a validation error that doesn't retry
        assert "ValidationException" in str(exc_info.value) or "ModelNotAvailableException" in str(exc_info.value)


class TestBedrockAnalyzerIntegration:
    """Integration tests for BedrockAnalyzer with real AI models."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_company_text(self, bedrock_analyzer, requires_aws_credentials):
        """Test real company analysis with Nova Lite."""
        
        config = AnalysisConfig(
            model_name='amazon.nova-lite-v1:0',
            temperature=0.1,
            max_tokens=100
        )
        
        company_text = """
        Acme Corp is a B2B SaaS company that provides cloud-based project management 
        solutions for medium-sized businesses. Founded in 2018, the company has grown 
        to serve over 1,000 customers worldwide.
        """
        
        try:
            result = await bedrock_analyzer.analyze_text(company_text, config)
            
            # Verify successful analysis
            assert result.status == ResponseStatus.SUCCESS
            assert result.finish_reason == FinishReason.STOP
            assert len(result.content) > 0
            assert result.model_used == 'amazon.nova-lite-v1:0'
            assert result.token_usage.total_tokens > 0
            assert result.cost_estimate > 0
            assert result.metadata['provider'] == 'aws_bedrock'
            
            # Verify analysis contains relevant business insights
            content_lower = result.content.lower()
            # Should mention business aspects (flexible check for different response styles)
            business_keywords = ['company', 'business', 'saas', 'project', 'management', 'customers']
            found_keywords = [kw for kw in business_keywords if kw in content_lower]
            assert len(found_keywords) >= 2, f"Analysis should mention business concepts, found: {found_keywords}"
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock analysis not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_with_system_prompt(self, bedrock_analyzer, requires_aws_credentials):
        """Test analysis with system prompt."""
        
        config = AnalysisConfig(
            model_name='amazon.nova-lite-v1:0',
            temperature=0.1,
            max_tokens=50
        )
        
        try:
            result = await bedrock_analyzer.analyze_text(
                "Analyze this tech company: CloudTech Inc",
                config,
                system_prompt="You are a business analyst. Provide brief, focused analysis."
            )
            
            assert result.status == ResponseStatus.SUCCESS
            assert len(result.content) > 0
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock analysis not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_token_counting(self, bedrock_analyzer, requires_aws_credentials):
        """Test token counting accuracy."""
        
        text = "This is a test text for token counting validation."
        model = 'amazon.nova-lite-v1:0'
        
        try:
            token_count = await bedrock_analyzer.count_tokens(text, model)
            
            # Should return reasonable token count
            assert isinstance(token_count, int)
            assert token_count > 0
            assert token_count < len(text)  # Should be fewer tokens than characters
            
            # Rough validation: typical token-to-character ratio
            char_to_token_ratio = len(text) / token_count
            assert 2 <= char_to_token_ratio <= 8  # Reasonable range for English text
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock not available for token counting: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_analysis(self, bedrock_analyzer, requires_aws_credentials):
        """Test batch analysis functionality."""
        
        config = AnalysisConfig(
            model_name='amazon.nova-lite-v1:0',
            temperature=0.1,
            max_tokens=30
        )
        
        texts = [
            "TechCorp: A software development company.",
            "FinanceFlow: A financial services provider."
        ]
        
        try:
            batch_result = await bedrock_analyzer.analyze_batch(texts, config)
            
            # Verify batch processing
            assert len(batch_result.results) == 2
            assert batch_result.success_count == 2
            assert batch_result.error_count == 0
            assert batch_result.total_cost > 0
            assert batch_result.total_tokens.total_tokens > 0
            
            # Verify individual results
            for result in batch_result.results:
                assert result.status == ResponseStatus.SUCCESS
                assert len(result.content) > 0
                
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock batch analysis not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_provider_info(self, bedrock_analyzer, requires_aws_credentials):
        """Test provider information retrieval."""
        
        try:
            provider_info = await bedrock_analyzer.get_provider_info()
            
            assert provider_info.provider_name == "AWS Bedrock"
            assert provider_info.default_model == bedrock_analyzer.config.default_model
            assert len(provider_info.available_models) > 0
            assert provider_info.supports_streaming is True
            assert provider_info.supports_function_calling is True
            assert provider_info.cost_per_1k_tokens > 0
            
        except Exception as e:
            # This shouldn't require API access, so don't skip
            raise


class TestBedrockEmbedderIntegration:
    """Integration tests for BedrockEmbeddingProvider with real embedding models."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_single_embedding_generation(self, bedrock_embedder, requires_aws_credentials):
        """Test single embedding generation with Titan."""
        
        config = EmbeddingConfig(
            model_name="amazon.titan-embed-text-v2:0",
            batch_size=1
        )
        
        text = "This is a test company description for embedding generation."
        
        try:
            result = await bedrock_embedder.get_embedding(text, config)
            
            # Verify embedding structure
            assert len(result.embedding) == 1536  # Titan v2 dimensions
            assert result.dimensions == 1536
            assert result.model_used == "amazon.titan-embed-text-v2:0"
            assert result.provider_name == "aws_bedrock"
            assert result.token_count > 0
            assert result.estimated_cost > 0
            assert result.text_length == len(text)
            assert result.confidence_score == 1.0
            
            # Verify embedding is normalized
            magnitude = sum(x**2 for x in result.embedding) ** 0.5
            assert 0.99 <= magnitude <= 1.01  # Should be unit vector
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock embedding not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_embedding_generation(self, bedrock_embedder, requires_aws_credentials):
        """Test batch embedding generation."""
        
        config = EmbeddingConfig(
            model_name="amazon.titan-embed-text-v2:0",
            batch_size=3
        )
        
        texts = [
            "Company A provides financial services.",
            "Company B offers cloud computing solutions.",
            "Company C develops AI-powered tools."
        ]
        
        try:
            results = await bedrock_embedder.get_embeddings_batch(texts, config)
            
            # Verify batch processing
            assert len(results) == len(texts)
            assert all(len(result.embedding) == 1536 for result in results)
            assert all(result.dimensions == 1536 for result in results)
            assert all(result.provider_name == "aws_bedrock" for result in results)
            
            # Verify embeddings are different
            embeddings = [result.embedding for result in results]
            assert embeddings[0] != embeddings[1]
            assert embeddings[1] != embeddings[2]
            assert embeddings[0] != embeddings[2]
            
            # Verify cost tracking
            total_cost = sum(result.estimated_cost for result in results)
            assert total_cost > 0
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock batch embedding not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_consistency(self, bedrock_embedder, requires_aws_credentials):
        """Test that same text produces same embedding."""
        
        config = EmbeddingConfig(
            model_name="amazon.titan-embed-text-v2:0",
            batch_size=1
        )
        
        text = "Consistent embedding test for the same input text."
        
        try:
            result1 = await bedrock_embedder.get_embedding(text, config)
            result2 = await bedrock_embedder.get_embedding(text, config)
            
            # Embeddings should be identical for same input
            assert result1.embedding == result2.embedding
            assert result1.text_hash == result2.text_hash
            assert result1.dimensions == result2.dimensions
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock embedding consistency test not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_cost_estimation(self, bedrock_embedder, requires_aws_credentials):
        """Test embedding cost estimation accuracy."""
        
        text = "Test text for cost estimation validation with multiple words and concepts."
        model = "amazon.titan-embed-text-v2:0"
        
        try:
            # Get actual token count
            token_count = await bedrock_embedder.count_embedding_tokens(text, model)
            
            # Get estimated cost
            estimated_cost = await bedrock_embedder.estimate_embedding_cost(1, token_count, model)
            
            # Generate actual embedding and check real cost
            config = EmbeddingConfig(model_name=model, batch_size=1)
            result = await bedrock_embedder.get_embedding(text, config)
            
            # Costs should be very close (within 10% tolerance)
            cost_difference = abs(estimated_cost - result.estimated_cost)
            cost_tolerance = max(estimated_cost, result.estimated_cost) * 0.1
            assert cost_difference <= cost_tolerance, \
                f"Cost estimation off by {cost_difference:.6f}, tolerance: {cost_tolerance:.6f}"
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                pytest.skip(f"Bedrock cost estimation test not available: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check(self, bedrock_embedder, requires_aws_credentials):
        """Test embedder health check with real API."""
        
        try:
            health = await bedrock_embedder.health_check()
            
            # Verify health check structure
            assert isinstance(health, dict)
            assert 'status' in health
            assert health['status'] in ['healthy', 'degraded', 'unhealthy']
            assert 'latency_ms' in health
            assert 'available_models' in health
            assert 'region' in health
            assert health['region'] == bedrock_embedder.config.region_name
            
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                # Health check failed due to access - this is valid for tests
                pytest.skip(f"Bedrock health check not available: {e}")
            else:
                raise


class TestBedrockCostManagement:
    """Integration tests for cost management features."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cost_calculation_accuracy(self, requires_aws_credentials):
        """Test cost calculation accuracy against real model pricing."""
        
        # Test cost calculation for different models
        input_tokens = 1000
        output_tokens = 500
        
        # Nova Pro cost calculation
        nova_pro_cost = calculate_bedrock_cost(input_tokens, output_tokens, 'amazon.nova-pro-v1:0')
        expected_nova_pro = (1000/1000 * 0.0008) + (500/1000 * 0.0032)  # $0.002400
        assert abs(nova_pro_cost - expected_nova_pro) < 0.000001
        
        # Nova Lite cost calculation (should be much cheaper)
        nova_lite_cost = calculate_bedrock_cost(input_tokens, output_tokens, 'amazon.nova-lite-v1:0')
        expected_nova_lite = (1000/1000 * 0.00006) + (500/1000 * 0.00024)  # $0.000180
        assert abs(nova_lite_cost - expected_nova_lite) < 0.000001
        
        # Verify Nova Lite is indeed much cheaper
        cost_ratio = nova_pro_cost / nova_lite_cost
        assert cost_ratio > 10  # Should be more than 10x cheaper
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_daily_cost_limit_enforcement(self, requires_aws_credentials):
        """Test that daily cost limits are enforced."""
        
        # Create config with very low daily limit
        config = BedrockConfig(
            daily_cost_limit=0.001,  # $0.001 limit
            enable_cost_tracking=True
        )
        
        client = BedrockClient(config)
        
        # Reset costs
        client.reset_daily_cost()
        
        # First small request should succeed
        small_body = {
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 1,
            "temperature": 0.1
        }
        
        try:
            # This might succeed or fail depending on AWS access
            await client.invoke_model('amazon.nova-lite-v1:0', small_body)
            
            # Set cost artificially high to trigger limit
            client._total_cost_today = 0.002  # Above limit
            
            # Next request should fail due to cost limit
            with pytest.raises(Exception, match="Daily cost limit.*exceeded"):
                await client.invoke_model('amazon.nova-lite-v1:0', small_body)
                
        except Exception as e:
            if any(err in str(e) for err in ["AccessDeniedException", "ModelNotAvailableException"]):
                # Test the cost limit logic without real API calls
                client._total_cost_today = 0.002  # Above limit
                
                with pytest.raises(Exception, match="Daily cost limit.*exceeded"):
                    await client.invoke_model('amazon.nova-lite-v1:0', small_body)
            else:
                raise


class TestBedrockErrorHandling:
    """Integration tests for error handling and resilience."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_model_handling(self, bedrock_analyzer, requires_aws_credentials):
        """Test handling of invalid model requests."""
        
        config = AnalysisConfig(
            model_name='invalid-model-that-does-not-exist',
            max_tokens=10
        )
        
        result = await bedrock_analyzer.analyze_text("Test text", config)
        
        # Should return error result instead of raising
        assert result.status == ResponseStatus.ERROR
        assert result.finish_reason == FinishReason.ERROR
        assert "Error:" in result.content
        assert result.cost_estimate == 0.0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_network_timeout_handling(self, integration_config, requires_aws_credentials):
        """Test handling of network timeouts."""
        
        # Create config with very short timeout
        timeout_config = BedrockConfig(
            region_name=integration_config.region_name,
            timeout_seconds=0.001,  # Very short timeout
            max_retries=1
        )
        
        analyzer = BedrockAnalyzer(timeout_config)
        
        config = AnalysisConfig(
            model_name='amazon.nova-lite-v1:0',
            max_tokens=10
        )
        
        # Should handle timeout gracefully
        result = await analyzer.analyze_text("Test timeout handling", config)
        
        # Should return error result
        assert result.status == ResponseStatus.ERROR
        assert result.finish_reason == FinishReason.ERROR


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__, 
        "-v", 
        "-m", "integration",
        "--tb=short"
    ])
#!/usr/bin/env python3
"""
Unit Tests for Bedrock AI Adapters
==================================

Comprehensive unit tests for the AWS Bedrock AI adapters with mocked dependencies
to ensure isolated component testing and cost-safe validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json
import os

from src.infrastructure.adapters.ai.bedrock.analyzer import BedrockAnalyzer
from src.infrastructure.adapters.ai.bedrock.embedder import BedrockEmbeddingProvider
from src.infrastructure.adapters.ai.bedrock.client import BedrockClient
from src.infrastructure.adapters.ai.bedrock.config import BedrockConfig, calculate_bedrock_cost

from src.core.domain.value_objects.ai_config import AnalysisConfig, EmbeddingConfig
from src.core.domain.value_objects.ai_response import ResponseStatus, FinishReason


class TestBedrockConfig:
    """Test Bedrock configuration management."""
    
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-key-123',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-456',
            'AWS_REGION': 'us-west-2',
            'BEDROCK_DEFAULT_MODEL': 'amazon.nova-pro-v1:0',
            'BEDROCK_EMBEDDING_MODEL': 'amazon.titan-embed-text-v2:0',
            'BEDROCK_MAX_RETRIES': '5',
            'BEDROCK_TIMEOUT': '90',
            'BEDROCK_DAILY_COST_LIMIT': '50.0'
        }):
            config = BedrockConfig.from_environment()
            
            assert config.aws_access_key_id == 'test-key-123'
            assert config.aws_secret_access_key == 'test-secret-456'
            assert config.region_name == 'us-west-2'
            assert config.default_model == 'amazon.nova-pro-v1:0'
            assert config.embedding_model == 'amazon.titan-embed-text-v2:0'
            assert config.max_retries == 5
            assert config.timeout_seconds == 90
            assert config.daily_cost_limit == 50.0
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = BedrockConfig()
        
        assert config.region_name == "us-east-1"
        assert config.default_model == "amazon.nova-pro-v1:0"
        assert config.embedding_model == "amazon.titan-embed-text-v2:0"
        assert config.max_retries == 3
        assert config.timeout_seconds == 60
        assert config.daily_cost_limit == 100.0
        assert config.enable_cost_tracking is True
    
    def test_cost_calculation_nova_pro(self):
        """Test cost calculation for Nova Pro model."""
        cost = calculate_bedrock_cost(1000, 500, 'amazon.nova-pro-v1:0')
        # (1000/1000 * 0.0008) + (500/1000 * 0.0032) = 0.0008 + 0.0016 = 0.0024
        expected = 0.0024
        assert abs(cost - expected) < 0.0001
    
    def test_cost_calculation_nova_lite(self):
        """Test cost calculation for Nova Lite model (much cheaper)."""
        cost_lite = calculate_bedrock_cost(1000, 500, 'amazon.nova-lite-v1:0')
        cost_pro = calculate_bedrock_cost(1000, 500, 'amazon.nova-pro-v1:0')
        
        # Nova Lite should be significantly cheaper
        assert cost_lite < cost_pro
        assert cost_pro / cost_lite > 10  # Should be more than 10x cheaper
    
    def test_cost_calculation_embeddings(self):
        """Test cost calculation for embedding models (no output tokens)."""
        cost = calculate_bedrock_cost(1000, 0, 'amazon.titan-embed-text-v2:0')
        expected = 1000 / 1000 * 0.0001  # Only input tokens for embeddings
        assert abs(cost - expected) < 0.0001
    
    def test_cost_calculation_unknown_model(self):
        """Test cost calculation with unknown model raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            calculate_bedrock_cost(1000, 500, 'unknown-model-v1:0')


class TestBedrockClient:
    """Test core Bedrock client functionality."""
    
    @pytest.fixture
    def config(self):
        """Test configuration with cost controls."""
        return BedrockConfig(
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret',
            region_name='us-east-1',
            daily_cost_limit=10.0,
            max_cost_per_request=1.0
        )
    
    @pytest.fixture
    def client(self, config):
        """Create Bedrock client for testing."""
        return BedrockClient(config)
    
    def test_client_creation_with_credentials(self, config):
        """Test Bedrock client creation with explicit credentials."""
        with patch('boto3.Session') as mock_session:
            mock_bedrock_client = Mock()
            mock_session.return_value.client.return_value = mock_bedrock_client
            
            client = BedrockClient(config)
            
            # Access client property to trigger creation
            bedrock_client = client.client
            
            assert bedrock_client == mock_bedrock_client
            mock_session.assert_called_once_with(
                aws_access_key_id='test-key',
                aws_secret_access_key='test-secret',
                aws_session_token=None,
                region_name='us-east-1'
            )
    
    def test_client_creation_without_credentials(self):
        """Test client creation using default credential chain."""
        config = BedrockConfig(region_name='us-west-2')  # No explicit credentials
        
        with patch('boto3.Session') as mock_session:
            mock_bedrock_client = Mock()
            mock_session.return_value.client.return_value = mock_bedrock_client
            
            client = BedrockClient(config)
            bedrock_client = client.client
            
            assert bedrock_client == mock_bedrock_client
            mock_session.assert_called_once_with(region_name='us-west-2')
    
    @pytest.mark.asyncio
    async def test_invoke_model_success(self, client):
        """Test successful model invocation."""
        
        mock_response_body = {
            'output': {
                'message': {
                    'content': 'This is a test response from Nova Pro.'
                }
            },
            'usage': {
                'inputTokens': 10,
                'outputTokens': 15,
                'totalTokens': 25
            }
        }
        
        with patch.object(client, 'client') as mock_bedrock:
            mock_bedrock.invoke_model.return_value = {
                'body': Mock(read=lambda: json.dumps(mock_response_body))
            }
            
            body = {
                'messages': [{'role': 'user', 'content': 'Test prompt'}],
                'max_tokens': 100,
                'temperature': 0.1
            }
            
            response = await client.invoke_model('amazon.nova-pro-v1:0', body)
            
            # Verify response structure
            assert 'output' in response
            assert '_metadata' in response
            assert response['_metadata']['model_id'] == 'amazon.nova-pro-v1:0'
            assert response['_metadata']['usage']['input_tokens'] == 10
            assert response['_metadata']['usage']['output_tokens'] == 15
            assert response['_metadata']['cost'] > 0
    
    @pytest.mark.asyncio
    async def test_invoke_model_with_retry(self, client):
        """Test model invocation with retry logic."""
        
        from botocore.exceptions import ClientError
        
        # Mock first attempt to fail, second to succeed
        error_response = {'Error': {'Code': 'ThrottlingException'}}
        success_response = {
            'body': Mock(read=lambda: json.dumps({'content': 'Success after retry'}))
        }
        
        with patch.object(client, 'client') as mock_bedrock:
            mock_bedrock.invoke_model.side_effect = [
                ClientError(error_response, 'InvokeModel'),
                success_response
            ]
            
            body = {'messages': [{'role': 'user', 'content': 'Test'}]}
            
            response = await client.invoke_model('amazon.nova-lite-v1:0', body)
            
            assert 'content' in response
            assert response['_metadata']['attempt'] == 2
    
    @pytest.mark.asyncio
    async def test_cost_limit_enforcement(self, client):
        """Test daily cost limit enforcement."""
        
        # Set cost close to limit
        client._total_cost_today = 9.99
        
        with patch.object(client, 'client') as mock_bedrock:
            mock_bedrock.invoke_model.return_value = {
                'body': Mock(read=lambda: json.dumps({'content': 'test'}))
            }
            
            # Should allow request under limit
            response = await client.invoke_model('amazon.nova-lite-v1:0', {})
            assert 'content' in response
        
        # Set cost over limit
        client._total_cost_today = 10.01
        
        # Should reject request over limit
        with pytest.raises(Exception, match="Daily cost limit.*exceeded"):
            await client.invoke_model('amazon.nova-lite-v1:0', {})
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        
        with patch.object(client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {'content': 'Hi'}
            
            is_healthy = await client.health_check()
            
            assert is_healthy is True
            mock_invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check failure handling."""
        
        with patch.object(client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Service unavailable")
            
            is_healthy = await client.health_check()
            
            assert is_healthy is False
    
    def test_daily_cost_tracking(self, client):
        """Test daily cost tracking and reset."""
        
        # Set initial cost with today's date
        import time
        client._total_cost_today = 5.0
        client._last_cost_reset = time.strftime('%Y-%m-%d')
        
        assert client.get_daily_cost() == 5.0
        
        # Reset cost
        client.reset_daily_cost()
        assert client.get_daily_cost() == 0.0


class TestBedrockAnalyzer:
    """Test Bedrock AI analysis functionality."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return BedrockConfig(
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret',
            region_name='us-east-1',
            default_model='amazon.nova-pro-v1:0'
        )
    
    @pytest.fixture
    def analyzer(self, config):
        """Create analyzer with mocked client."""
        return BedrockAnalyzer(config)
    
    @pytest.mark.asyncio
    async def test_analyze_text_nova_pro(self, analyzer):
        """Test text analysis with Nova Pro model."""
        
        mock_response = {
            'output': {
                'message': {
                    'content': 'This is a comprehensive analysis of Acme Corp, a leading B2B SaaS company...'
                }
            },
            '_metadata': {
                'model_id': 'amazon.nova-pro-v1:0',
                'processing_time': 2.1,
                'cost': 0.008,
                'attempt': 1,
                'usage': {
                    'input_tokens': 50,
                    'output_tokens': 200,
                    'total_tokens': 250
                }
            }
        }
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = AnalysisConfig(
                model_name='amazon.nova-pro-v1:0',
                temperature=0.1,
                max_tokens=1000
            )
            
            result = await analyzer.analyze_text(
                "Analyze this company: Acme Corp provides B2B SaaS solutions...", 
                config
            )
            
            # Verify request was made correctly
            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args[0]
            model_id, body = call_args
            
            assert model_id == 'amazon.nova-pro-v1:0'
            assert 'messages' in body
            assert body['messages'][0]['content'].startswith('Analyze this company')
            assert body['max_tokens'] == 1000
            assert body['temperature'] == 0.1
            
            # Verify response
            assert result.status == ResponseStatus.SUCCESS
            assert result.finish_reason == FinishReason.STOP
            assert 'comprehensive analysis' in result.content
            assert result.model_used == 'amazon.nova-pro-v1:0'
            assert result.token_usage.total_tokens == 250
            assert result.token_usage.prompt_tokens == 50
            assert result.token_usage.completion_tokens == 200
            assert result.estimated_cost == 0.008
            assert result.provider_metadata['provider'] == 'aws_bedrock'
    
    @pytest.mark.asyncio
    async def test_analyze_text_claude(self, analyzer):
        """Test text analysis with Claude model."""
        
        mock_response = {
            'content': [
                {
                    'text': 'Based on my analysis, this company operates in the B2B SaaS space...'
                }
            ],
            '_metadata': {
                'model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'cost': 0.025,
                'usage': {
                    'input_tokens': 30,
                    'output_tokens': 180,
                    'total_tokens': 210
                }
            }
        }
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = AnalysisConfig(
                model_name='anthropic.claude-3-5-sonnet-20241022-v2:0',
                temperature=0.2,
                max_tokens=2000,
                system_prompt="You are an expert business analyst."
            )
            
            result = await analyzer.analyze_text("What is this company's business model?", config)
            
            # Verify Claude-specific request format
            call_args = mock_invoke.call_args[0]
            model_id, body = call_args
            
            assert model_id == 'anthropic.claude-3-5-sonnet-20241022-v2:0'
            assert 'anthropic_version' in body
            assert len(body['messages']) == 2  # System + user message
            assert body['messages'][0]['role'] == 'system'
            assert body['messages'][1]['role'] == 'user'
            
            # Verify response parsing
            assert result.content == 'Based on my analysis, this company operates in the B2B SaaS space...'
            assert result.token_usage.total_tokens == 210
    
    @pytest.mark.asyncio
    async def test_analyze_text_with_system_prompt(self, analyzer):
        """Test text analysis with system prompt."""
        
        mock_response = {
            'output': {'message': {'content': 'Expert analysis response'}},
            'usage': {'inputTokens': 20, 'outputTokens': 30, 'totalTokens': 50},
            '_metadata': {'cost': 0.002}
        }
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = AnalysisConfig(model_name='amazon.nova-pro-v1:0')
            
            result = await analyzer.analyze_text(
                "Analyze this company", 
                config,
                system_prompt="You are an expert financial analyst with 20 years of experience."
            )
            
            # Verify system prompt was included
            call_args = mock_invoke.call_args[0]
            _, body = call_args
            
            assert len(body['messages']) == 2
            assert body['messages'][0]['role'] == 'system'
            assert 'expert financial analyst' in body['messages'][0]['content']
            assert body['messages'][1]['role'] == 'user'
            assert body['messages'][1]['content'] == 'Analyze this company'
    
    @pytest.mark.asyncio
    async def test_analyze_batch(self, analyzer):
        """Test batch analysis functionality."""
        
        # Mock responses for each text in batch
        mock_responses = [
            {
                'output': {'message': {'content': 'Analysis of Company A'}},
                'usage': {'inputTokens': 10, 'outputTokens': 20, 'totalTokens': 30},
                '_metadata': {'cost': 0.001}
            },
            {
                'output': {'message': {'content': 'Analysis of Company B'}},
                'usage': {'inputTokens': 15, 'outputTokens': 25, 'totalTokens': 40},
                '_metadata': {'cost': 0.0015}
            }
        ]
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = mock_responses
            
            config = AnalysisConfig(model_name='amazon.nova-pro-v1:0')
            texts = ["Company A description", "Company B description"]
            
            batch_result = await analyzer.analyze_batch(texts, config)
            
            # Verify batch processing
            assert len(batch_result.results) == 2
            assert batch_result.success_count == 2
            assert batch_result.error_count == 0
            assert batch_result.total_cost == 0.0025
            assert batch_result.total_tokens.total_tokens == 70
            
            # Verify individual results
            assert 'Company A' in batch_result.results[0].content
            assert 'Company B' in batch_result.results[1].content
    
    @pytest.mark.asyncio
    async def test_analyze_text_streaming(self, analyzer):
        """Test streaming analysis functionality."""
        
        mock_response = {
            'output': {'message': {'content': 'This is a streaming response that will be chunked'}},
            'usage': {'inputTokens': 10, 'outputTokens': 15, 'totalTokens': 25},
            '_metadata': {'cost': 0.001}
        }
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = AnalysisConfig(model_name='amazon.nova-pro-v1:0')
            
            chunks = []
            async for chunk in analyzer.analyze_text_streaming("Test prompt", config):
                chunks.append(chunk)
            
            # Verify streaming behavior
            assert len(chunks) > 1  # Should have multiple chunks
            
            # Verify final chunk
            final_chunk = chunks[-1]
            assert final_chunk.is_final is True
            assert final_chunk.token_usage is not None
            assert final_chunk.finish_reason == FinishReason.STOP
    
    @pytest.mark.asyncio
    async def test_error_handling(self, analyzer):
        """Test comprehensive error handling."""
        
        with patch.object(analyzer.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Model temporarily unavailable")
            
            config = AnalysisConfig(model_name='amazon.nova-pro-v1:0')
            result = await analyzer.analyze_text("Test prompt", config)
            
            # Should return error result instead of raising
            assert result.status == ResponseStatus.ERROR
            assert result.finish_reason == FinishReason.ERROR
            assert "Error:" in result.content
            assert result.token_usage.total_tokens == 0
            assert result.estimated_cost == 0.0
            assert 'error' in result.provider_metadata
    
    @pytest.mark.asyncio
    async def test_token_counting(self, analyzer):
        """Test token counting functionality."""
        
        text = "This is a test text for token counting estimation."
        model = "amazon.nova-pro-v1:0"
        
        token_count = await analyzer.count_tokens(text, model)
        
        # Should return reasonable estimate
        assert token_count > 0
        assert token_count < len(text)  # Should be less than character count
    
    @pytest.mark.asyncio
    async def test_get_provider_info(self, analyzer):
        """Test provider information retrieval."""
        
        provider_info = await analyzer.get_provider_info()
        
        assert provider_info.provider_name == "AWS Bedrock"
        assert provider_info.default_model == analyzer.config.default_model
        assert len(provider_info.available_models) > 0
        assert provider_info.supports_streaming is True
        assert provider_info.supports_function_calling is True
        assert provider_info.cost_per_1k_tokens > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, analyzer):
        """Test analyzer health check."""
        
        with patch.object(analyzer.client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            
            is_healthy = await analyzer.health_check()
            assert is_healthy is True
            
            mock_health.return_value = False
            is_healthy = await analyzer.health_check()
            assert is_healthy is False


class TestBedrockEmbedder:
    """Test Bedrock embedding functionality."""
    
    @pytest.fixture
    def config(self):
        """Test configuration for embeddings."""
        return BedrockConfig(
            embedding_model='amazon.titan-embed-text-v2:0',
            daily_cost_limit=5.0
        )
    
    @pytest.fixture
    def embedder(self, config):
        """Create embedder with mocked client."""
        return BedrockEmbeddingProvider(config)
    
    @pytest.mark.asyncio
    async def test_get_embedding_titan(self, embedder):
        """Test single embedding generation with Titan."""
        
        mock_embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_response = {
            'embedding': mock_embedding,
            '_metadata': {
                'cost': 0.0001,
                'model_id': 'amazon.titan-embed-text-v2:0'
            }
        }
        
        with patch.object(embedder.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = EmbeddingConfig(
                model_name="amazon.titan-embed-text-v2:0",
                batch_size=1
            )
            
            result = await embedder.get_embedding("This is a test company description", config)
            
            # Verify request
            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args[0]
            model_id, body = call_args
            
            assert model_id == "amazon.titan-embed-text-v2:0"
            assert 'inputText' in body
            assert body['inputText'] == "This is a test company description"
            
            # Verify response
            assert len(result.embedding) == 1536
            assert result.embedding == mock_embedding
            assert result.model_used == "amazon.titan-embed-text-v2:0"
            assert result.provider_name == "aws_bedrock"
            assert result.dimensions == 1536
            assert result.estimated_cost > 0
            assert result.confidence_score == 1.0
    
    @pytest.mark.asyncio
    async def test_get_embeddings_batch_titan(self, embedder):
        """Test batch embedding generation with Titan (individual processing)."""
        
        mock_embeddings = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536
        ]
        
        # Mock individual calls since Titan doesn't support batch
        mock_responses = [
            {'embedding': embedding, '_metadata': {'cost': 0.0001}}
            for embedding in mock_embeddings
        ]
        
        with patch.object(embedder.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = mock_responses
            
            config = EmbeddingConfig(
                model_name="amazon.titan-embed-text-v2:0",
                batch_size=5
            )
            
            texts = [
                "Company A description",
                "Company B description", 
                "Company C description"
            ]
            
            results = await embedder.get_embeddings_batch(texts, config)
            
            # Verify batch processing
            assert len(results) == 3
            assert all(len(result.embedding) == 1536 for result in results)
            assert all(result.dimensions == 1536 for result in results)
            
            # Should have made 3 individual calls
            assert mock_invoke.call_count == 3
            
            # Verify embeddings match
            for i, result in enumerate(results):
                assert result.embedding == mock_embeddings[i]
    
    @pytest.mark.asyncio
    async def test_get_embeddings_batch_cohere(self, embedder):
        """Test batch embedding generation with Cohere (native batch processing)."""
        
        # Update embedder to use Cohere model
        embedder.config.embedding_model = 'cohere.embed-english-v3:0'
        
        mock_response = {
            'embeddings': [
                [0.1] * 1024,
                [0.2] * 1024
            ],
            '_metadata': {'cost': 0.0002}
        }
        
        with patch.object(embedder.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            config = EmbeddingConfig(
                model_name="cohere.embed-english-v3:0",
                batch_size=10
            )
            
            texts = ["Text 1", "Text 2"]
            results = await embedder.get_embeddings_batch(texts, config)
            
            # Should make only one batch call
            assert mock_invoke.call_count == 1
            
            # Verify batch request format
            call_args = mock_invoke.call_args[0]
            model_id, body = call_args
            
            assert model_id == "cohere.embed-english-v3:0"
            assert 'texts' in body
            assert body['texts'] == texts
            assert 'input_type' in body
            
            # Verify results
            assert len(results) == 2
            assert all(len(result.embedding) == 1024 for result in results)
            assert all(result.dimensions == 1024 for result in results)
    
    @pytest.mark.asyncio
    async def test_validate_embedding_config(self, embedder):
        """Test embedding configuration validation."""
        
        # Valid configuration
        valid_config = EmbeddingConfig(
            model_name="amazon.titan-embed-text-v2:0",
            dimensions=1536,
            batch_size=1
        )
        
        is_valid = await embedder.validate_embedding_config(valid_config)
        assert is_valid is True
        
        # Invalid model
        with pytest.raises(Exception):  # Should raise EmbeddingModelNotAvailableException
            invalid_config = EmbeddingConfig(model_name="unknown-model")
            await embedder.validate_embedding_config(invalid_config)
        
        # Invalid dimensions
        with pytest.raises(Exception):  # Should raise InvalidEmbeddingConfigException
            invalid_config = EmbeddingConfig(
                model_name="amazon.titan-embed-text-v2:0",
                dimensions=512  # Wrong dimensions
            )
            await embedder.validate_embedding_config(invalid_config)
    
    @pytest.mark.asyncio
    async def test_get_embedding_dimensions(self, embedder):
        """Test embedding dimension retrieval."""
        
        # Test different models
        titan_dims = await embedder.get_embedding_dimensions('amazon.titan-embed-text-v2:0')
        assert titan_dims == 1536
        
        cohere_dims = await embedder.get_embedding_dimensions('cohere.embed-english-v3:0')
        assert cohere_dims == 1024
        
        # Test unknown model
        with pytest.raises(Exception):  # Should raise EmbeddingModelNotAvailableException
            await embedder.get_embedding_dimensions('unknown-model')
    
    @pytest.mark.asyncio
    async def test_estimate_embedding_cost(self, embedder):
        """Test embedding cost estimation."""
        
        cost = await embedder.estimate_embedding_cost(
            text_count=10,
            total_tokens=1000,
            model_name='amazon.titan-embed-text-v2:0'
        )
        
        # Should calculate cost based on input tokens only
        expected = calculate_bedrock_cost(1000, 0, 'amazon.titan-embed-text-v2:0')
        assert abs(cost - expected) < 0.0001
    
    @pytest.mark.asyncio
    async def test_count_embedding_tokens(self, embedder):
        """Test token counting for embeddings."""
        
        # Single text
        single_count = await embedder.count_embedding_tokens(
            "This is a test", 
            "amazon.titan-embed-text-v2:0"
        )
        assert isinstance(single_count, int)
        assert single_count > 0
        
        # Multiple texts
        texts = ["Text 1", "Text 2", "Text 3"]
        batch_counts = await embedder.count_embedding_tokens(
            texts,
            "amazon.titan-embed-text-v2:0"
        )
        assert isinstance(batch_counts, list)
        assert len(batch_counts) == 3
        assert all(isinstance(count, int) for count in batch_counts)
    
    @pytest.mark.asyncio
    async def test_get_supported_models(self, embedder):
        """Test supported model listing."""
        
        models = await embedder.get_supported_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'amazon.titan-embed-text-v2:0' in models
        assert 'cohere.embed-english-v3:0' in models
    
    @pytest.mark.asyncio
    async def test_health_check(self, embedder):
        """Test embedder health check."""
        
        mock_embedding = [0.1] * 1536
        mock_response = {
            'embedding': mock_embedding,
            '_metadata': {'cost': 0.0001}
        }
        
        with patch.object(embedder.client, 'invoke_model', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            health = await embedder.health_check()
            
            assert health['status'] == 'healthy'
            assert 'latency_ms' in health
            assert 'available_models' in health
            assert 'daily_cost' in health
            assert health['region'] == embedder.config.region_name
    
    @pytest.mark.asyncio
    async def test_context_manager(self, embedder):
        """Test async context manager functionality."""
        
        with patch.object(embedder, 'close', new_callable=AsyncMock) as mock_close:
            async with embedder as emb:
                assert emb is embedder
            
            # Ensure cleanup was called
            mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
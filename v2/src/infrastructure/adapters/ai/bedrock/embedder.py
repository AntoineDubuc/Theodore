#!/usr/bin/env python3
"""
Bedrock Embedding Provider
=========================

Bedrock adapter for embedding generation implementing the EmbeddingProvider interface.
Supports Titan and Cohere embedding models with batch processing and cost optimization.
"""

import time
import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.core.ports.embedding_provider import (
    EmbeddingProvider, EmbeddingProviderException,
    EmbeddingRateLimitedException, EmbeddingQuotaExceededException,
    EmbeddingModelNotAvailableException, InvalidEmbeddingConfigException,
    EmbeddingDimensionMismatchException, ProgressCallback
)
from src.core.domain.value_objects.ai_config import EmbeddingConfig
from src.core.domain.value_objects.ai_response import EmbeddingResult
from src.core.ports.progress import ProgressTracker

from .client import BedrockClient
from .config import BedrockConfig, calculate_bedrock_cost
import logging


class BedrockEmbeddingProvider(EmbeddingProvider):
    """Bedrock adapter specialized for embedding generation."""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.client = BedrockClient(config)
        self.logger = logging.getLogger(__name__)
        
        # Embedding model capabilities
        self.model_capabilities = {
            'amazon.titan-embed-text-v1:0': {
                'dimensions': 1536,
                'max_input_tokens': 8192,
                'supports_batch': False,
                'batch_size': 1,
                'cost_per_1k_tokens': 0.0001
            },
            'amazon.titan-embed-text-v2:0': {
                'dimensions': 1536,
                'max_input_tokens': 8192,
                'supports_batch': False,
                'batch_size': 1,
                'cost_per_1k_tokens': 0.0001
            },
            'cohere.embed-english-v3:0': {
                'dimensions': 1024,
                'max_input_tokens': 512,
                'supports_batch': True,
                'batch_size': 96,
                'cost_per_1k_tokens': 0.0001
            },
            'cohere.embed-multilingual-v3:0': {
                'dimensions': 1024,
                'max_input_tokens': 512,
                'supports_batch': True,
                'batch_size': 96,
                'cost_per_1k_tokens': 0.0001
            }
        }
    
    async def get_embedding(
        self, 
        text: str, 
        config: EmbeddingConfig,
        progress_callback: Optional[ProgressCallback] = None
    ) -> EmbeddingResult:
        """Generate embedding for a single text."""
        
        start_time = time.time()
        
        try:
            if progress_callback:
                progress_callback("Validating embedding configuration", 0.1, None)
            
            # Validate configuration
            await self.validate_embedding_config(config)
            
            if progress_callback:
                progress_callback("Preparing embedding request", 0.3, None)
            
            # Prepare and execute request
            model = config.model_name or self.config.embedding_model
            body = self._prepare_embedding_request(text, model, config)
            
            if progress_callback:
                progress_callback("Generating embedding", 0.6, None)
            
            response = await self.client.invoke_model(model, body)
            
            if progress_callback:
                progress_callback("Processing embedding response", 0.9, None)
            
            # Extract embedding and calculate metadata
            embedding = self._extract_embedding(response, model)
            dimensions = len(embedding)
            
            # Validate dimensions
            expected_dimensions = self.model_capabilities[model]['dimensions']
            if dimensions != expected_dimensions:
                raise EmbeddingDimensionMismatchException(
                    f"Expected {expected_dimensions} dimensions, got {dimensions}"
                )
            
            # Calculate token count and cost
            token_count = self._estimate_tokens(text)
            processing_time = time.time() - start_time
            cost = response.get('_metadata', {}).get('cost', 0.0)
            
            if progress_callback:
                progress_callback("Embedding generation completed", 1.0, None)
            
            return EmbeddingResult(
                embedding=embedding,
                dimensions=dimensions,
                model_used=model,
                provider_name="aws_bedrock",
                token_count=token_count,
                estimated_cost=cost,
                text_length=len(text),
                text_hash=hashlib.md5(text.encode()).hexdigest(),
                timestamp=datetime.now(),
                request_id=f"bedrock-{int(time.time() * 1000)}",
                processing_time=processing_time,
                confidence_score=1.0,  # Bedrock doesn't provide confidence scores
                provider_metadata={
                    'region': self.config.region_name,
                    'model_capabilities': self.model_capabilities[model],
                    'attempt_count': response.get('_metadata', {}).get('attempt', 1)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            processing_time = time.time() - start_time
            
            # Map exceptions to appropriate types
            if "throttling" in str(e).lower() or "rate" in str(e).lower():
                raise EmbeddingRateLimitedException("aws_bedrock", 60)
            elif "quota" in str(e).lower():
                raise EmbeddingQuotaExceededException("aws_bedrock", "daily_quota")
            elif "model" in str(e).lower() and "not" in str(e).lower():
                raise EmbeddingModelNotAvailableException("aws_bedrock", config.model_name)
            
            # Return error result with zero embedding
            model = config.model_name or self.config.embedding_model
            dimensions = self.model_capabilities.get(model, {}).get('dimensions', 1536)
            
            return EmbeddingResult(
                embedding=[0.0] * dimensions,
                dimensions=dimensions,
                model_used=model,
                provider_name="aws_bedrock",
                token_count=0,
                estimated_cost=0.0,
                text_length=len(text),
                text_hash=hashlib.md5(text.encode()).hexdigest(),
                timestamp=datetime.now(),
                request_id=f"bedrock-error-{int(time.time() * 1000)}",
                processing_time=processing_time,
                confidence_score=0.0,
                provider_metadata={
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts with batch optimization."""
        
        if not texts:
            return []
        
        start_time = time.time()
        model = config.model_name or self.config.embedding_model
        
        try:
            # Validate configuration (but allow batch size adjustment)
            await self._validate_model_available(config)
            
            model_caps = self.model_capabilities[model]
            supports_batch = model_caps['supports_batch']
            max_batch_size = min(model_caps['batch_size'], config.batch_size)
            
            results = []
            total_batches = (len(texts) + max_batch_size - 1) // max_batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * max_batch_size
                end_idx = min(start_idx + max_batch_size, len(texts))
                batch_texts = texts[start_idx:end_idx]
                
                if progress_callback:
                    progress = (batch_idx + 1) / total_batches
                    progress_callback(
                        f"Processing batch {batch_idx + 1} of {total_batches}", 
                        progress, 
                        None
                    )
                
                if supports_batch and len(batch_texts) > 1:
                    # Use native batch processing
                    batch_results = await self._process_batch_native(batch_texts, model, config)
                else:
                    # Process individually
                    batch_results = await self._process_batch_individual(batch_texts, model, config)
                
                results.extend(batch_results)
                
                # Rate limiting between batches
                if batch_idx < total_batches - 1:
                    await asyncio.sleep(0.1)
            
            total_time = time.time() - start_time
            self.logger.info(
                f"Batch embedding completed: {len(results)} embeddings in {total_time:.2f}s "
                f"({len(results)/total_time:.1f} embeddings/sec)"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch embedding failed: {e}")
            
            # Return error results for all texts
            model = config.model_name or self.config.embedding_model
            dimensions = self.model_capabilities.get(model, {}).get('dimensions', 1536)
            
            error_results = []
            for text in texts:
                error_result = EmbeddingResult(
                    embedding=[0.0] * dimensions,
                    dimensions=dimensions,
                    model_used=model,
                    provider_name="aws_bedrock",
                    token_count=0,
                    estimated_cost=0.0,
                    text_length=len(text),
                    text_hash=hashlib.md5(text.encode()).hexdigest(),
                    timestamp=datetime.now(),
                    request_id=f"bedrock-batch-error-{int(time.time() * 1000)}",
                    processing_time=0.0,
                    confidence_score=0.0,
                    provider_metadata={'batch_error': str(e)}
                )
                error_results.append(error_result)
            
            return error_results
    
    async def get_embeddings_with_progress(
        self,
        texts: List[str],
        config: EmbeddingConfig,
        progress_tracker: ProgressTracker
    ) -> List[EmbeddingResult]:
        """Generate embeddings with integrated progress tracking."""
        
        def progress_callback(message: str, progress: float, details: Optional[str]):
            progress_tracker.update_progress(progress, message, details)
        
        return await self.get_embeddings_batch(texts, config, progress_callback)
    
    async def get_embedding_dimensions(self, model_name: str) -> int:
        """Return vector dimensions for specified model."""
        
        if model_name not in self.model_capabilities:
            raise EmbeddingModelNotAvailableException("aws_bedrock", model_name)
        
        return self.model_capabilities[model_name]['dimensions']
    
    async def estimate_embedding_cost(
        self, 
        text_count: int, 
        total_tokens: int, 
        model_name: str
    ) -> float:
        """Calculate estimated cost for embedding generation."""
        
        if model_name not in self.model_capabilities:
            raise EmbeddingModelNotAvailableException("aws_bedrock", model_name)
        
        # For embeddings, output tokens are 0
        return calculate_bedrock_cost(total_tokens, 0, model_name)
    
    async def count_embedding_tokens(
        self, 
        texts: Union[str, List[str]], 
        model_name: str
    ) -> Union[int, List[int]]:
        """Count tokens for cost estimation."""
        
        if isinstance(texts, str):
            return self._estimate_tokens(texts)
        else:
            return [self._estimate_tokens(text) for text in texts]
    
    async def validate_embedding_config(self, config: EmbeddingConfig) -> bool:
        """Validate configuration against Bedrock capabilities."""
        
        model = config.model_name or self.config.embedding_model
        
        if model not in self.model_capabilities:
            raise EmbeddingModelNotAvailableException("aws_bedrock", model)
        
        model_caps = self.model_capabilities[model]
        
        # Check dimensions if specified
        if config.dimensions and config.dimensions != model_caps['dimensions']:
            raise InvalidEmbeddingConfigException(
                f"Model {model} only supports {model_caps['dimensions']} dimensions, "
                f"but {config.dimensions} requested"
            )
        
        # Check batch size
        if config.batch_size > model_caps['batch_size']:
            raise InvalidEmbeddingConfigException(
                f"Model {model} max batch size is {model_caps['batch_size']}, "
                f"but {config.batch_size} requested"
            )
        
        return True
    
    async def get_supported_models(self) -> List[str]:
        """Return list of available Bedrock embedding models."""
        return list(self.model_capabilities.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Bedrock embedding service health."""
        
        try:
            # Test with minimal embedding request
            test_config = EmbeddingConfig(
                model_name=self.config.embedding_model,
                batch_size=1
            )
            
            start_time = time.time()
            result = await self.get_embedding("test", test_config)
            latency = time.time() - start_time
            
            return {
                'status': 'healthy' if result.embedding != [0.0] * result.dimensions else 'degraded',
                'latency_ms': latency * 1000,
                'available_models': await self.get_supported_models(),
                'region': self.config.region_name,
                'daily_cost': self.client.get_daily_cost(),
                'cost_limit': self.config.daily_cost_limit,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'region': self.config.region_name,
                'last_check': datetime.now().isoformat()
            }
    
    async def close(self) -> None:
        """Clean up embedding provider resources."""
        await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
    
    # Helper methods
    
    async def _process_batch_native(
        self, 
        texts: List[str], 
        model: str, 
        config: EmbeddingConfig
    ) -> List[EmbeddingResult]:
        """Process batch using native model batch capabilities."""
        
        # Currently only Cohere models support native batching
        if not model.startswith('cohere.embed'):
            return await self._process_batch_individual(texts, model, config)
        
        body = {
            "texts": texts,
            "input_type": "search_document",
            "truncate": "NONE" if not config.truncate else "END"
        }
        
        start_time = time.time()
        response = await self.client.invoke_model(model, body)
        processing_time = time.time() - start_time
        
        # Extract embeddings
        embeddings = self._extract_batch_embeddings(response, model)
        
        # Build results
        results = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            token_count = self._estimate_tokens(text)
            cost = response.get('_metadata', {}).get('cost', 0.0) / len(texts)
            
            result = EmbeddingResult(
                embedding=embedding,
                dimensions=len(embedding),
                model_used=model,
                provider_name="aws_bedrock",
                token_count=token_count,
                estimated_cost=cost,
                text_length=len(text),
                text_hash=hashlib.md5(text.encode()).hexdigest(),
                timestamp=datetime.now(),
                request_id=f"bedrock-batch-{int(time.time() * 1000)}-{i}",
                processing_time=processing_time / len(texts),
                confidence_score=1.0,
                provider_metadata={
                    'batch_size': len(texts),
                    'batch_index': i
                }
            )
            results.append(result)
        
        return results
    
    async def _process_batch_individual(
        self, 
        texts: List[str], 
        model: str, 
        config: EmbeddingConfig
    ) -> List[EmbeddingResult]:
        """Process batch by making individual requests."""
        
        results = []
        
        for text in texts:
            individual_config = EmbeddingConfig(
                model_name=model,
                dimensions=config.dimensions,
                normalize=config.normalize,
                truncate=config.truncate,
                batch_size=1,
                provider_config=config.provider_config,
                encoding_format=config.encoding_format
            )
            
            result = await self.get_embedding(text, individual_config)
            results.append(result)
        
        return results
    
    def _prepare_embedding_request(self, text: str, model: str, config: EmbeddingConfig) -> Dict[str, Any]:
        """Prepare embedding request body based on model type."""
        
        if model.startswith('amazon.titan-embed'):
            return {
                "inputText": text
            }
        elif model.startswith('cohere.embed'):
            return {
                "texts": [text],
                "input_type": "search_document",
                "truncate": "NONE" if not config.truncate else "END"
            }
        else:
            # Generic format
            return {
                "inputText": text
            }
    
    def _extract_embedding(self, response: Dict[str, Any], model: str) -> List[float]:
        """Extract embedding vector from response."""
        
        if model.startswith('amazon.titan-embed'):
            if 'embedding' in response:
                return response['embedding']
        elif model.startswith('cohere.embed'):
            if 'embeddings' in response and response['embeddings']:
                return response['embeddings'][0]
        
        # Generic fallback
        for key in ['embedding', 'embeddings', 'vector']:
            if key in response:
                value = response[key]
                if isinstance(value, list):
                    if value and isinstance(value[0], list):
                        return value[0]  # First embedding from batch
                    return value
        
        # Last resort: return zero vector
        dimensions = self.model_capabilities.get(model, {}).get('dimensions', 1536)
        self.logger.warning(f"Could not extract embedding, returning zero vector: {response}")
        return [0.0] * dimensions
    
    def _extract_batch_embeddings(self, response: Dict[str, Any], model: str) -> List[List[float]]:
        """Extract multiple embeddings from batch response."""
        
        if 'embeddings' in response:
            return response['embeddings']
        
        # Fallback to single embedding extraction
        single_embedding = self._extract_embedding(response, model)
        return [single_embedding]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: 1 token ≈ 4 characters for most models
        return max(1, len(text) // 4)
    
    async def _validate_model_available(self, config: EmbeddingConfig) -> bool:
        """Validate that the model is available (without strict batch size check)."""
        model = config.model_name or self.config.embedding_model
        
        if model not in self.model_capabilities:
            raise EmbeddingModelNotAvailableException("aws_bedrock", model)
        
        # Check dimensions if specified (but be flexible on batch size)
        model_caps = self.model_capabilities[model]
        if config.dimensions and config.dimensions != model_caps['dimensions']:
            raise InvalidEmbeddingConfigException(
                f"Model {model} only supports {model_caps['dimensions']} dimensions, "
                f"but {config.dimensions} requested"
            )
        
        return True
#!/usr/bin/env python3
"""
Bedrock AI Analyzer
==================

Bedrock adapter for AI text analysis implementing the AIProvider interface.
Supports Nova Pro/Lite, Claude, and Titan models with comprehensive error handling.
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime

from src.core.ports.ai_provider import (
    AIProvider, ProgressCallback, AIProviderException, 
    RateLimitedException, QuotaExceededException, 
    ModelNotAvailableException, ProviderTimeoutException
)
from src.core.domain.value_objects.ai_config import AnalysisConfig, ModelInfo, StreamingConfig
from src.core.domain.value_objects.ai_response import (
    AnalysisResult, StreamingChunk, TokenUsage, BatchResult,
    ResponseStatus, FinishReason
)

from .client import BedrockClient
from .config import BedrockConfig
import logging


class BedrockAnalyzer(AIProvider):
    """Bedrock adapter for AI text analysis and generation."""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.client = BedrockClient(config)
        self.logger = logging.getLogger(__name__)
        
        # Model capabilities mapping
        self.model_capabilities = {
            'amazon.nova-pro-v1:0': {
                'max_tokens': 300000,
                'supports_streaming': True,
                'supports_function_calling': False,
                'context_window': 300000
            },
            'amazon.nova-lite-v1:0': {
                'max_tokens': 300000,
                'supports_streaming': True,
                'supports_function_calling': False,
                'context_window': 300000
            },
            'amazon.nova-micro-v1:0': {
                'max_tokens': 300000,
                'supports_streaming': True,
                'supports_function_calling': False,
                'context_window': 300000
            },
            'anthropic.claude-3-5-sonnet-20241022-v2:0': {
                'max_tokens': 8192,
                'supports_streaming': True,
                'supports_function_calling': True,
                'context_window': 200000
            },
            'anthropic.claude-3-5-haiku-20241022-v1:0': {
                'max_tokens': 8192,
                'supports_streaming': True,
                'supports_function_calling': True,
                'context_window': 200000
            },
            'amazon.titan-text-premier-v1:0': {
                'max_tokens': 3000,
                'supports_streaming': False,
                'supports_function_calling': False,
                'context_window': 32000
            }
        }
    
    async def get_provider_info(self) -> ModelInfo:
        """Get information about this provider and available models."""
        
        return ModelInfo(
            provider_name="AWS Bedrock",
            provider_version="2024-12",
            default_model=self.config.default_model,
            available_models=list(self.model_capabilities.keys()),
            supports_streaming=True,
            supports_function_calling=True,
            supports_batch_processing=True,
            max_context_length=max(
                caps['context_window'] for caps in self.model_capabilities.values()
            ),
            cost_per_1k_tokens=0.0008,  # Nova Pro input cost
            rate_limits={
                'requests_per_minute': 60,
                'tokens_per_minute': 100000
            }
        )
    
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> AnalysisResult:
        """Analyze text using Bedrock models."""
        
        start_time = time.time()
        model = config.model_name or self.config.default_model
        
        try:
            if progress_callback:
                progress_callback("Preparing Bedrock request", 0.1, None)
            
            # Prepare request body based on model type
            body = self._prepare_request_body(text, config, system_prompt, model)
            
            if progress_callback:
                progress_callback("Sending request to Bedrock", 0.3, None)
            
            # Make the API call
            response = await self.client.invoke_model(model, body)
            
            if progress_callback:
                progress_callback("Processing Bedrock response", 0.8, None)
            
            # Extract content and build result
            content = self._extract_content(response, model)
            metadata = response.get('_metadata', {})
            usage_info = metadata.get('usage', {})
            
            # Build token usage
            token_usage = TokenUsage(
                prompt_tokens=usage_info.get('input_tokens', 0),
                completion_tokens=usage_info.get('output_tokens', 0),
                total_tokens=usage_info.get('total_tokens', 0)
            )
            
            if progress_callback:
                progress_callback("Analysis completed", 1.0, None)
            
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                content=content,
                status=ResponseStatus.SUCCESS,
                finish_reason=FinishReason.STOP,
                model_used=model,
                provider_name="aws_bedrock",
                token_usage=token_usage,
                processing_time=processing_time,
                estimated_cost=metadata.get('cost', 0.0),
                timestamp=datetime.now(),
                provider_metadata={
                    'provider': 'aws_bedrock',
                    'region': self.config.region_name,
                    'attempt_count': metadata.get('attempt', 1),
                    'estimated_tokens': usage_info.get('estimated', False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Bedrock text analysis failed: {e}")
            processing_time = time.time() - start_time
            
            # Map exceptions to appropriate types
            if "throttling" in str(e).lower() or "rate" in str(e).lower():
                raise RateLimitedException("aws_bedrock", 60)
            elif "quota" in str(e).lower():
                raise QuotaExceededException("aws_bedrock", "daily_quota")
            elif "timeout" in str(e).lower():
                raise ProviderTimeoutException("aws_bedrock", self.config.timeout_seconds)
            elif "model" in str(e).lower() and "not" in str(e).lower():
                raise ModelNotAvailableException("aws_bedrock", model)
            
            # Return error result instead of raising for unknown errors
            return AnalysisResult(
                content=f"Error: {str(e)}",
                status=ResponseStatus.ERROR,
                finish_reason=FinishReason.ERROR,
                model_used=model,
                provider_name="aws_bedrock",
                token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                processing_time=processing_time,
                estimated_cost=0.0,
                timestamp=datetime.now(),
                provider_metadata={
                    'provider': 'aws_bedrock',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
    
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        streaming_config: Optional[StreamingConfig] = None
    ) -> AsyncIterator[StreamingChunk]:
        """Analyze text with streaming response (simulated for Bedrock)."""
        
        # Bedrock doesn't support streaming natively for all models
        # We'll simulate streaming by chunking the response
        
        result = await self.analyze_text(text, config, system_prompt)
        
        if result.status != ResponseStatus.SUCCESS:
            yield StreamingChunk(
                content=result.content,
                finish_reason=result.finish_reason,
                token_usage=result.token_usage,
                is_final=True,
                metadata=result.metadata
            )
            return
        
        # Simulate streaming by yielding content in chunks
        content = result.content
        chunk_size = 50  # Characters per chunk
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            is_final = i + chunk_size >= len(content)
            
            yield StreamingChunk(
                content=chunk,
                finish_reason=result.finish_reason if is_final else None,
                token_usage=result.token_usage if is_final else None,
                is_final=is_final,
                metadata=result.provider_metadata if is_final else {}
            )
            
            # Small delay to simulate streaming
            await asyncio.sleep(0.05)
    
    async def analyze_batch(
        self,
        texts: List[str],
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchResult:
        """Analyze multiple texts in batch."""
        
        start_time = time.time()
        results = []
        total_cost = 0.0
        total_tokens = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        
        for i, text in enumerate(texts):
            if progress_callback:
                progress = (i + 1) / len(texts)
                progress_callback(f"Processing text {i + 1} of {len(texts)}", progress, None)
            
            try:
                result = await self.analyze_text(text, config, system_prompt)
                results.append(result)
                
                # Accumulate metrics
                total_cost += result.estimated_cost
                total_tokens.prompt_tokens += result.token_usage.prompt_tokens
                total_tokens.completion_tokens += result.token_usage.completion_tokens
                total_tokens.total_tokens += result.token_usage.total_tokens
                
            except Exception as e:
                # Create error result for failed analysis
                error_result = AnalysisResult(
                    content=f"Error: {str(e)}",
                    status=ResponseStatus.ERROR,
                    finish_reason=FinishReason.ERROR,
                    model_used=config.model_name or self.config.default_model,
                    provider_name="aws_bedrock",
                    token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    processing_time=0.0,
                    estimated_cost=0.0,
                    timestamp=datetime.now(),
                    provider_metadata={'error': str(e)}
                )
                results.append(error_result)
        
        processing_time = time.time() - start_time
        
        return BatchResult(
            results=results,
            total_cost=total_cost,
            total_tokens=total_tokens,
            processing_time=processing_time,
            success_count=sum(1 for r in results if r.status == ResponseStatus.SUCCESS),
            error_count=sum(1 for r in results if r.status == ResponseStatus.ERROR),
            metadata={
                'provider': 'aws_bedrock',
                'batch_size': len(texts),
                'model_used': config.model_name or self.config.default_model
            }
        )
    
    async def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for cost estimation."""
        
        # For Bedrock, we'll use a simple estimation
        # In production, you might use tiktoken or model-specific tokenizers
        
        if model_name not in self.model_capabilities:
            raise ModelNotAvailableException("aws_bedrock", model_name)
        
        # Rough estimation: 1 token ≈ 4 characters for most models
        estimated_tokens = len(text) // 4
        
        self.logger.debug(f"Estimated {estimated_tokens} tokens for {len(text)} characters")
        
        return estimated_tokens
    
    def _prepare_request_body(
        self, 
        text: str, 
        config: AnalysisConfig, 
        system_prompt: Optional[str],
        model: str
    ) -> Dict[str, Any]:
        """Prepare request body based on model type."""
        
        effective_system_prompt = system_prompt or config.system_prompt
        
        if model.startswith('amazon.nova'):
            return self._prepare_nova_request(text, config, effective_system_prompt)
        elif model.startswith('anthropic.claude'):
            return self._prepare_claude_request(text, config, effective_system_prompt)
        elif model.startswith('amazon.titan'):
            return self._prepare_titan_request(text, config, effective_system_prompt)
        else:
            raise ModelNotAvailableException("aws_bedrock", model)
    
    def _prepare_nova_request(self, text: str, config: AnalysisConfig, system_prompt: Optional[str]) -> Dict[str, Any]:
        """Prepare request body for Nova models."""
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": text
        })
        
        body = {
            "messages": messages,
            "max_tokens": config.max_tokens or 2000,
            "temperature": config.temperature,
            "top_p": config.top_p or 0.9
        }
        
        if config.stop_sequences:
            body["stop_sequences"] = config.stop_sequences
        
        return body
    
    def _prepare_claude_request(self, text: str, config: AnalysisConfig, system_prompt: Optional[str]) -> Dict[str, Any]:
        """Prepare request body for Claude models via Bedrock."""
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": text
        })
        
        body = {
            "messages": messages,
            "max_tokens": config.max_tokens or 2000,
            "temperature": config.temperature,
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        if config.top_p is not None:
            body["top_p"] = config.top_p
        
        if config.stop_sequences:
            body["stop_sequences"] = config.stop_sequences
        
        return body
    
    def _prepare_titan_request(self, text: str, config: AnalysisConfig, system_prompt: Optional[str]) -> Dict[str, Any]:
        """Prepare request body for Titan models."""
        
        # Titan uses a different format
        input_text = text
        if system_prompt:
            input_text = f"{system_prompt}\n\n{text}"
        
        return {
            "inputText": input_text,
            "textGenerationConfig": {
                "maxTokenCount": config.max_tokens or 2000,
                "temperature": config.temperature,
                "topP": config.top_p or 0.9,
                "stopSequences": config.stop_sequences or []
            }
        }
    
    def _extract_content(self, response: Dict[str, Any], model: str) -> str:
        """Extract text content from model response."""
        
        if model.startswith('amazon.nova'):
            # Nova response format
            if 'output' in response:
                output = response['output']
                if isinstance(output, dict) and 'message' in output:
                    return output['message'].get('content', '')
                elif isinstance(output, str):
                    return output
            
            # Fallback for Nova
            if 'content' in response:
                return response['content']
                
        elif model.startswith('anthropic.claude'):
            # Claude response format
            if 'content' in response:
                content_blocks = response['content']
                if isinstance(content_blocks, list) and content_blocks:
                    return content_blocks[0].get('text', '')
                elif isinstance(content_blocks, str):
                    return content_blocks
                    
        elif model.startswith('amazon.titan'):
            # Titan response format
            if 'results' in response:
                results = response['results']
                if isinstance(results, list) and results:
                    return results[0].get('outputText', '')
        
        # Generic fallback
        for key in ['content', 'text', 'completion', 'output']:
            if key in response:
                value = response[key]
                if isinstance(value, str):
                    return value
        
        self.logger.warning(f"Could not extract content from response: {response}")
        return str(response)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check analyzer health and return status information."""
        
        try:
            client_healthy = await self.client.health_check()
            
            return {
                'status': 'healthy' if client_healthy else 'unhealthy',
                'provider': 'aws_bedrock',
                'region': self.config.region_name,
                'default_model': self.config.default_model,
                'daily_cost': self.client.get_daily_cost(),
                'cost_limit': self.config.daily_cost_limit,
                'last_check': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': 'aws_bedrock', 
                'error': str(e),
                'last_check': time.time()
            }
    
    async def estimate_cost(self, input_tokens: int, output_tokens: int, model_name: str) -> float:
        """Estimate cost in USD for the given usage."""
        from .config import calculate_bedrock_cost
        return calculate_bedrock_cost(input_tokens, output_tokens, model_name)
    
    async def validate_configuration(self, config: AnalysisConfig) -> bool:
        """Validate the provider configuration."""
        from .config import BEDROCK_MODEL_COSTS
        
        # Check if model is supported
        model = config.model_name or self.config.default_model
        if model not in BEDROCK_MODEL_COSTS:
            raise Exception(f"Model {model} not supported by Bedrock adapter")
        
        # Validate temperature range
        if config.temperature is not None and (config.temperature < 0 or config.temperature > 1):
            raise Exception("Temperature must be between 0 and 1")
        
        # Validate max_tokens
        if config.max_tokens is not None and config.max_tokens <= 0:
            raise Exception("max_tokens must be positive")
        
        return True
    
    async def close(self) -> None:
        """Clean up analyzer resources."""
        await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
    
    def calculate_cost(self, token_usage: TokenUsage, model: str) -> float:
        """Calculate cost for given usage."""
        from .config import calculate_bedrock_cost
        return calculate_bedrock_cost(
            token_usage.prompt_tokens, 
            token_usage.completion_tokens, 
            model
        )
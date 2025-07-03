#!/usr/bin/env python3
"""
Google Gemini AI Provider Adapter
=================================

Enterprise-grade implementation of the AIProvider interface for Google Gemini models.
Supports Gemini 2.5 Pro with 1M token context for comprehensive company analysis.

Features:
- Complete AIProvider interface implementation
- Support for all Gemini models (2.5 Pro, 1.5 Pro, 1.5 Flash, 1.0 Pro)
- Large context processing up to 1M tokens
- Streaming analysis for real-time feedback
- Advanced error handling and monitoring
- Cost optimization and budget management
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime

from src.core.ports.ai_provider import AIProvider
from src.core.domain.value_objects.ai_config import AnalysisConfig
from src.core.domain.value_objects.ai_response import AnalysisResult, TokenUsage, ResponseStatus, StreamingChunk, BatchResult
from src.core.domain.value_objects.ai_config import ModelInfo
from src.core.domain.exceptions import AIProviderError, ConfigurationError

from .client import GeminiClient, GeminiError, GeminiRateLimitError, GeminiAuthenticationError
from .config import GeminiConfig, calculate_gemini_cost, GEMINI_MODEL_CAPABILITIES


logger = logging.getLogger(__name__)


class GeminiAnalyzer(AIProvider):
    """
    Enterprise-grade Google Gemini AI provider.
    
    Implements the complete AIProvider interface with support for:
    - Large context analysis (up to 1M tokens with Gemini 2.5 Pro)
    - Streaming responses for real-time feedback
    - Comprehensive cost tracking and budget management
    - Advanced error handling and retry logic
    - Production monitoring and health checks
    """
    
    def __init__(self, config: GeminiConfig):
        """Initialize Gemini analyzer with configuration."""
        self.config = config
        self.client = GeminiClient(config)
        self._provider_name = "google_gemini"
        self._supported_models = list(GEMINI_MODEL_CAPABILITIES.keys())
        
        logger.info(f"🚀 Gemini analyzer initialized with {config.model}")
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name
    
    @property
    def supported_models(self) -> List[str]:
        """Get list of supported models."""
        return self._supported_models.copy()
    
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        progress_callback: Optional[callable] = None
    ) -> AnalysisResult:
        """
        Analyze text using Gemini models.
        
        Args:
            text: Text content to analyze
            config: Analysis configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        start_time = time.time()
        
        try:
            # Validate configuration
            if not await self.validate_configuration(config):
                raise ConfigurationError(f"Invalid configuration for model {config.model_name}")
            
            if progress_callback:
                progress_callback("🔍 Starting Gemini analysis...")
            
            # Check model capabilities
            model_caps = GEMINI_MODEL_CAPABILITIES.get(config.model_name, {})
            max_context = model_caps.get('max_context', self.config.max_context_tokens)
            
            # Estimate input tokens (rough estimate: 4 chars per token)
            estimated_tokens = len(text) // 4
            
            if estimated_tokens > max_context:
                logger.warning(f"⚠️ Input may exceed context limit: {estimated_tokens} > {max_context}")
                # Truncate text if necessary
                text = text[:max_context * 4]
                estimated_tokens = max_context
            
            if progress_callback:
                progress_callback(f"📊 Processing {estimated_tokens:,} tokens with {config.model_name}")
            
            # Generate analysis
            response = await self.client.generate_content(
                prompt=text,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            if progress_callback:
                progress_callback("✅ Analysis completed")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Build result
            token_usage = TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            provider_metadata = {
                'model': response.model,
                'finish_reason': response.finish_reason,
                'processing_time_seconds': processing_time,
                'daily_cost': self.client.get_daily_cost(),
                'session_stats': self.client.get_stats(),
                'model_capabilities': model_caps
            }
            
            if response.metadata:
                provider_metadata.update(response.metadata)
            
            result = AnalysisResult(
                content=response.content,
                status=ResponseStatus.SUCCESS,
                token_usage=token_usage,
                model_used=response.model,
                provider_name=self.provider_name,
                estimated_cost=response.usage.cost,
                processing_time=processing_time,
                provider_metadata=provider_metadata
            )
            
            logger.info(f"✅ Gemini analysis completed: {token_usage.total_tokens} tokens, ${response.usage.cost:.4f}, {processing_time:.1f}s")
            
            return result
            
        except GeminiAuthenticationError as e:
            error_msg = f"Gemini authentication failed: {e}"
            logger.error(f"🔐 {error_msg}")
            raise AIProviderError(error_msg)
        
        except GeminiRateLimitError as e:
            error_msg = f"Gemini rate limit exceeded: {e}"
            logger.error(f"⏳ {error_msg}")
            raise AIProviderError(error_msg)
        
        except GeminiError as e:
            error_msg = f"Gemini API error: {e}"
            logger.error(f"❌ {error_msg}")
            raise AIProviderError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error in Gemini analysis: {e}"
            logger.error(f"💥 {error_msg}")
            raise AIProviderError(error_msg)
    
    async def analyze_text_stream(
        self,
        text: str,
        config: AnalysisConfig,
        progress_callback: Optional[callable] = None
    ) -> AsyncIterator[str]:
        """
        Analyze text with streaming response.
        
        Args:
            text: Text content to analyze
            config: Analysis configuration
            progress_callback: Optional callback for progress updates
            
        Yields:
            Content chunks as they're generated
        """
        try:
            if not self.config.enable_streaming:
                # Fall back to non-streaming
                if progress_callback:
                    progress_callback("📝 Streaming not enabled, using standard analysis")
                
                result = await self.analyze_text(text, config, progress_callback)
                yield result.content
                return
            
            if progress_callback:
                progress_callback("🌊 Starting streaming analysis...")
            
            # Validate configuration
            if not await self.validate_configuration(config):
                raise ConfigurationError(f"Invalid configuration for model {config.model_name}")
            
            chunk_count = 0
            async for chunk in self.client.generate_content_stream(
                prompt=text,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            ):
                chunk_count += 1
                if progress_callback and chunk_count % 10 == 0:
                    progress_callback(f"📤 Streaming chunk {chunk_count}")
                
                yield chunk
            
            if progress_callback:
                progress_callback(f"✅ Streaming completed ({chunk_count} chunks)")
                
        except GeminiError as e:
            error_msg = f"Gemini streaming error: {e}"
            logger.error(f"🌊❌ {error_msg}")
            raise AIProviderError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error in Gemini streaming: {e}"
            logger.error(f"🌊💥 {error_msg}")
            raise AIProviderError(error_msg)
    
    async def analyze_batch(
        self,
        texts: List[str],
        config: AnalysisConfig,
        progress_callback: Optional[callable] = None
    ) -> List[AnalysisResult]:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of text contents to analyze
            config: Analysis configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of AnalysisResults
        """
        results = []
        total_texts = len(texts)
        
        try:
            if progress_callback:
                progress_callback(f"📋 Starting batch analysis of {total_texts} texts")
            
            # Process with controlled concurrency
            semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
            
            async def analyze_single(text: str, index: int) -> AnalysisResult:
                async with semaphore:
                    if progress_callback:
                        progress_callback(f"🔍 Analyzing text {index + 1}/{total_texts}")
                    
                    return await self.analyze_text(text, config)
            
            # Execute all analyses concurrently
            tasks = [analyze_single(text, i) for i, text in enumerate(texts)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions in results
            processed_results = []
            failed_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Text {i + 1} failed: {result}")
                    failed_count += 1
                    
                    # Create error result
                    error_result = AnalysisResult(
                        content=f"Analysis failed: {result}",
                        status=ResponseStatus.ERROR,
                        token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                        model_used=config.model_name,
                        provider_name=self.provider_name,
                        estimated_cost=0.0,
                        processing_time=0.0,
                        provider_metadata={'error': str(result)}
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)
            
            if progress_callback:
                success_count = total_texts - failed_count
                progress_callback(f"✅ Batch analysis completed: {success_count}/{total_texts} successful")
            
            logger.info(f"📋 Batch analysis completed: {total_texts - failed_count}/{total_texts} successful")
            
            return processed_results
            
        except Exception as e:
            error_msg = f"Batch analysis failed: {e}"
            logger.error(f"📋❌ {error_msg}")
            raise AIProviderError(error_msg)
    
    async def estimate_cost(self, input_tokens: int, output_tokens: int, model_name: str) -> float:
        """
        Estimate cost for the given usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_name: Model to calculate cost for
            
        Returns:
            Estimated cost in USD
        """
        try:
            return calculate_gemini_cost(input_tokens, output_tokens, model_name)
        except ValueError as e:
            logger.warning(f"⚠️ Cost estimation failed for {model_name}: {e}")
            return 0.0
    
    async def validate_configuration(self, config: AnalysisConfig) -> bool:
        """
        Validate the provider configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check if model is supported
            if config.model_name not in GEMINI_MODEL_CAPABILITIES:
                logger.warning(f"⚠️ Unsupported model: {config.model_name}")
                return False
            
            # Check model capabilities
            model_caps = GEMINI_MODEL_CAPABILITIES[config.model_name]
            
            # Validate token limits
            if config.max_tokens is not None and config.max_tokens > model_caps.get('max_output', 8192):
                logger.warning(f"⚠️ Max tokens {config.max_tokens} exceeds model limit {model_caps.get('max_output', 8192)}")
                return False
            
            # Validate temperature range
            if not (0.0 <= config.temperature <= 2.0):
                logger.warning(f"⚠️ Temperature {config.temperature} outside valid range [0.0, 2.0]")
                return False
            
            # Check API key
            if not self.config.api_key:
                logger.warning("⚠️ GEMINI_API_KEY not configured")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Perform health check on the provider.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Use client health check
            return await self.client.health_check()
            
        except Exception as e:
            logger.error(f"❌ Gemini health check failed: {e}")
            return False
    
    async def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Model to get info for (defaults to config.model)
            
        Returns:
            Model information dictionary
        """
        model_key = model_name or self.config.model
        
        try:
            # Get info from client
            client_info = await self.client.get_model_info(model_key)
            
            # Add capability information
            model_caps = GEMINI_MODEL_CAPABILITIES.get(model_key, {})
            
            return {
                **client_info,
                'capabilities': model_caps,
                'cost_per_1k_input_tokens': calculate_gemini_cost(1000, 0, model_key),
                'cost_per_1k_output_tokens': calculate_gemini_cost(0, 1000, model_key),
                'provider': self.provider_name,
                'supports_streaming': self.config.enable_streaming,
                'current_daily_cost': self.client.get_daily_cost(),
                'daily_cost_limit': self.config.daily_cost_limit
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get model info for {model_key}: {e}")
            return {
                'name': model_key,
                'provider': self.provider_name,
                'error': str(e)
            }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get provider usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'provider': self.provider_name,
            'daily_cost': self.client.get_daily_cost(),
            'cost_limit': self.config.daily_cost_limit,
            'requests_made': self.client.get_stats()['requests_made'],
            'session_duration_minutes': self.client.get_stats()['session_duration_minutes'],
            'supported_models': self.supported_models,
            'current_model': self.config.model,
            'streaming_enabled': self.config.enable_streaming,
            'max_context_tokens': self.config.max_context_tokens
        }
    
    async def get_provider_info(self) -> ModelInfo:
        """
        Get information about this provider and available models.
        
        Returns:
            ModelInfo with provider capabilities and model details
        """
        try:
            return ModelInfo(
                provider_name=self.provider_name,
                models=self.supported_models,
                default_model=self.config.model,
                max_tokens=self.config.max_output_tokens,
                supports_streaming=self.config.enable_streaming,
                supports_function_calling=True,  # Gemini supports function calling
                cost_per_1k_tokens=calculate_gemini_cost(1000, 0, self.config.model),
                rate_limits={
                    'requests_per_minute': self.config.requests_per_minute,
                    'tokens_per_minute': self.config.tokens_per_minute
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to get provider info: {e}")
            raise AIProviderError(f"Could not get provider info: {e}")
    
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        streaming_config: Optional[Any] = None
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
        """
        try:
            if not self.config.enable_streaming:
                logger.warning("🌊 Streaming not enabled, falling back to non-streaming")
                result = await self.analyze_text(text, config)
                yield StreamingChunk(
                    content=result.content,
                    chunk_index=0,
                    is_final=True,
                    final_token_usage=result.token_usage
                )
                return
            
            # Validate configuration
            if not await self.validate_configuration(config):
                raise ConfigurationError(f"Invalid configuration for model {config.model_name}")
            
            # Combine system prompt with text if provided
            if system_prompt:
                prompt = f"{system_prompt}\n\n{text}"
            else:
                prompt = text
            
            chunk_index = 0
            cumulative_content = ""
            
            async for chunk_content in self.client.generate_content_stream(
                prompt=prompt,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            ):
                cumulative_content += chunk_content
                
                # Estimate tokens (rough)
                tokens_in_chunk = len(chunk_content) // 4
                cumulative_tokens = len(cumulative_content) // 4
                
                yield StreamingChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    is_final=False,
                    tokens_in_chunk=tokens_in_chunk,
                    cumulative_tokens=cumulative_tokens
                )
                
                chunk_index += 1
            
            # Final chunk with complete token usage
            final_tokens = len(cumulative_content) // 4
            final_token_usage = TokenUsage(
                prompt_tokens=len(prompt) // 4,
                completion_tokens=final_tokens,
                total_tokens=len(prompt) // 4 + final_tokens
            )
            
            yield StreamingChunk(
                content="",
                chunk_index=chunk_index,
                is_final=True,
                final_token_usage=final_token_usage
            )
            
        except Exception as e:
            error_msg = f"Streaming analysis failed: {e}"
            logger.error(f"🌊❌ {error_msg}")
            raise AIProviderError(error_msg)
    
    async def analyze_batch(
        self,
        texts: List[str],
        config: AnalysisConfig,
        system_prompt: Optional[str] = None,
        progress_callback: Optional[callable] = None
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
        """
        batch_id = f"gemini_batch_{int(time.time())}"
        start_time = datetime.now()
        
        try:
            if progress_callback:
                progress_callback(f"📋 Starting batch analysis of {len(texts)} texts", 0.0, "initialization")
            
            # Process with controlled concurrency
            semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
            
            async def analyze_single(text: str, index: int) -> AnalysisResult:
                async with semaphore:
                    if progress_callback:
                        progress = (index / len(texts)) * 100
                        progress_callback(f"🔍 Analyzing text {index + 1}/{len(texts)}", progress, f"processing_item_{index}")
                    
                    return await self.analyze_text(text, config, system_prompt)
            
            # Execute all analyses concurrently
            tasks = [analyze_single(text, i) for i, text in enumerate(texts)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and calculate metrics
            successful_results = []
            failed_count = 0
            total_tokens = 0
            total_cost = 0.0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    # Create error result placeholder
                    error_result = AnalysisResult(
                        content=f"Analysis failed: {result}",
                        status=ResponseStatus.ERROR,
                        token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                        model_used=config.model_name,
                        provider_name=self.provider_name,
                        estimated_cost=0.0,
                        processing_time=0.0,
                        provider_metadata={'error': str(result)}
                    )
                    successful_results.append(error_result)
                else:
                    successful_results.append(result)
                    total_tokens += result.token_usage.total_tokens
                    total_cost += result.estimated_cost or 0.0
            
            # Final statistics
            success_count = len(texts) - failed_count
            completion_time = datetime.now()
            processing_time = (completion_time - start_time).total_seconds()
            
            if progress_callback:
                progress_callback(f"✅ Batch analysis completed: {success_count}/{len(texts)} successful", 100.0, "completed")
            
            return BatchResult(
                batch_id=batch_id,
                total_requests=len(texts),
                successful_requests=success_count,
                failed_requests=failed_count,
                results=successful_results,
                started_at=start_time,
                completed_at=completion_time,
                total_processing_time=processing_time,
                total_tokens_used=total_tokens,
                total_estimated_cost=total_cost
            )
            
        except Exception as e:
            error_msg = f"Batch analysis failed: {e}"
            logger.error(f"📋❌ {error_msg}")
            raise AIProviderError(error_msg)
    
    async def count_tokens(self, text: str, model_name: str) -> int:
        """
        Count tokens for cost estimation.
        
        Args:
            text: Text to count tokens for
            model_name: Model to use for counting
            
        Returns:
            Number of tokens
        """
        try:
            # Gemini doesn't provide a direct token counting API
            # Use approximation: roughly 4 characters per token
            estimated_tokens = len(text) // 4
            
            # Adjust based on model characteristics
            if model_name in GEMINI_MODEL_CAPABILITIES:
                # Some models may have different tokenization
                return max(1, estimated_tokens)
            else:
                logger.warning(f"⚠️ Unknown model {model_name}, using approximation")
                return max(1, estimated_tokens)
                
        except Exception as e:
            logger.error(f"❌ Token counting failed: {e}")
            return len(text) // 4  # Fallback approximation
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and availability.
        
        Returns:
            Dictionary with health information
        """
        try:
            start_time = time.time()
            
            # Test basic connectivity
            client_healthy = await self.client.health_check()
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Get current usage stats
            usage_stats = await self.get_usage_stats()
            
            # Determine overall status
            if client_healthy and latency_ms < 5000:  # 5 second threshold
                status = "healthy"
            elif client_healthy:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                "status": status,
                "latency_ms": latency_ms,
                "requests_per_minute": usage_stats.get('requests_made', 0),
                "error_rate": 0.0,  # Would need to track errors for accurate rate
                "quota_remaining": max(0, self.config.daily_cost_limit - usage_stats.get('daily_cost', 0)),
                "last_error": None,  # Would need error tracking
                "provider": self.provider_name,
                "model": self.config.model,
                "streaming_enabled": self.config.enable_streaming,
                "daily_cost": usage_stats.get('daily_cost', 0),
                "cost_limit": self.config.daily_cost_limit
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "latency_ms": float('inf'),
                "error_rate": 1.0,
                "last_error": str(e),
                "provider": self.provider_name
            }
    
    async def close(self) -> None:
        """Clean up analyzer resources."""
        await self.client.close()
        logger.info("🧹 Gemini analyzer resources cleaned up")
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
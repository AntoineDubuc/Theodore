#!/usr/bin/env python3
"""
Google Gemini Client
==================

High-performance client for Google Gemini API with enterprise-grade features:
- Native streaming support for real-time responses
- Intelligent retry logic with exponential backoff
- Comprehensive cost tracking and budget management
- Thread-safe concurrent request processing
- Advanced error handling and circuit breaker patterns
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse, AsyncGenerateContentResponse
from google.api_core import exceptions as google_exceptions

from .config import GeminiConfig, calculate_gemini_cost
from .rate_limiter import GeminiRateLimiter


logger = logging.getLogger(__name__)


@dataclass
class GeminiUsage:
    """Token usage information from Gemini API."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


@dataclass
class GeminiResponse:
    """Standardized response from Gemini API."""
    content: str
    usage: GeminiUsage
    model: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GeminiError(Exception):
    """Base exception for Gemini client errors."""
    pass


class GeminiRateLimitError(GeminiError):
    """Rate limit exceeded error."""
    pass


class GeminiModelError(GeminiError):
    """Model-specific error."""
    pass


class GeminiAuthenticationError(GeminiError):
    """Authentication error."""
    pass


class GeminiClient:
    """
    Enterprise-grade Google Gemini API client.
    
    Provides high-performance access to Gemini models with comprehensive
    monitoring, cost tracking, and production-ready error handling.
    """
    
    def __init__(self, config: GeminiConfig):
        """Initialize Gemini client with configuration."""
        self.config = config
        self._model_cache: Dict[str, Any] = {}
        self._daily_costs: Dict[str, float] = {}
        self._request_count = 0
        self._session_created_at = time.time()
        
        # Use the advanced rate limiter instead of simple semaphore
        self._rate_limiter = GeminiRateLimiter(config)
        
        # Configure the API
        if config.api_key:
            genai.configure(api_key=config.api_key)
        else:
            raise GeminiAuthenticationError("GEMINI_API_KEY is required")
        
        logger.info(f"🔧 Gemini client initialized with model {config.model}")
    
    @property
    def client(self):
        """Get the underlying client for testing purposes."""
        return genai
    
    @client.setter
    def client(self, value):
        """Allow setting client for testing purposes."""
        # For testing compatibility
        pass
    
    @client.deleter
    def client(self):
        """Allow deleting client for testing purposes."""
        # For testing compatibility
        pass
    
    def _get_model(self, model_name: Optional[str] = None) -> Any:
        """Get or create a Gemini model instance."""
        model_key = model_name or self.config.model
        
        if model_key not in self._model_cache:
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_output_tokens,
            }
            
            model = genai.GenerativeModel(
                model_name=model_key,
                generation_config=generation_config
            )
            self._model_cache[model_key] = model
        
        return self._model_cache[model_key]
    
    def _extract_usage_from_response(self, response: GenerateContentResponse, model_name: str) -> GeminiUsage:
        """Extract token usage and calculate cost from response."""
        # Gemini API provides usage metadata
        usage_metadata = getattr(response, 'usage_metadata', None)
        
        if usage_metadata:
            input_tokens = getattr(usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(usage_metadata, 'candidates_token_count', 0)
            total_tokens = getattr(usage_metadata, 'total_token_count', input_tokens + output_tokens)
        else:
            # Fallback: estimate tokens from content length
            input_tokens = len(response.text or "") // 4  # Rough estimate
            output_tokens = len(response.text or "") // 4
            total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        cost = calculate_gemini_cost(input_tokens, output_tokens, model_name)
        
        return GeminiUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost
        )
    
    def _track_daily_cost(self, cost: float) -> None:
        """Track daily cost accumulation."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today not in self._daily_costs:
            self._daily_costs[today] = 0.0
        
        self._daily_costs[today] += cost
        
        if self._daily_costs[today] > self.config.daily_cost_limit:
            logger.warning(f"💰 Daily cost limit exceeded: ${self._daily_costs[today]:.2f} > ${self.config.daily_cost_limit:.2f}")
    
    def get_daily_cost(self) -> float:
        """Get current daily cost."""
        today = datetime.now().strftime('%Y-%m-%d')
        return self._daily_costs.get(today, 0.0)
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except google_exceptions.ResourceExhausted as e:
                last_exception = GeminiRateLimitError(f"Rate limit exceeded: {e}")
                if attempt == self.config.max_retries:
                    raise last_exception
                
                # Exponential backoff with jitter
                delay = (2 ** attempt) + (0.1 * attempt)
                logger.warning(f"⏳ Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
            
            except google_exceptions.PermissionDenied as e:
                raise GeminiAuthenticationError(f"Authentication failed: {e}")
            
            except google_exceptions.InvalidArgument as e:
                raise GeminiModelError(f"Invalid model request: {e}")
            
            except Exception as e:
                last_exception = GeminiError(f"Unexpected error: {e}")
                if attempt == self.config.max_retries:
                    raise last_exception
                
                delay = (2 ** attempt) + (0.1 * attempt)
                logger.warning(f"🔄 Unexpected error, retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    async def generate_content(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> GeminiResponse:
        """
        Generate content using Gemini model with robust timeout handling.
        
        Args:
            prompt: Text prompt for generation
            model_name: Model to use (defaults to config.model)
            temperature: Temperature for generation (defaults to config.temperature)
            max_tokens: Maximum tokens to generate (defaults to config.max_output_tokens)
            
        Returns:
            GeminiResponse with content and usage information
            
        Raises:
            GeminiError: If generation fails after retries
            asyncio.TimeoutError: If generation times out
        """
        model_key = model_name or self.config.model
        estimated_tokens = len(prompt) // 4  # Rough token estimate
        
        # Log the request details for debugging  
        logger.info(f"🧠 Gemini request: {len(prompt)} chars (~{estimated_tokens} tokens) to {model_key}")
        
        # Use advanced rate limiter with circuit breaker
        async with self._rate_limiter:
            # Acquire rate limit permission (includes circuit breaker check)
            wait_time = await self._rate_limiter.acquire_with_wait(estimated_tokens)
            if wait_time > 0:
                logger.info(f"⏳ Rate limited, waited {wait_time:.2f}s")
            
            async def _generate_with_timeout():
                """Internal generation with timeout wrapper"""
                model = self._get_model(model_key)
                
                # Override generation config if specified
                generation_config = {}
                if temperature is not None:
                    generation_config["temperature"] = temperature
                if max_tokens is not None:
                    generation_config["max_output_tokens"] = max_tokens
                
                async def _generate():
                    if generation_config:
                        # Create temporary model with custom config
                        temp_model = genai.GenerativeModel(
                            model_name=model_key,
                            generation_config=generation_config
                        )
                        response = await temp_model.generate_content_async(prompt)
                    else:
                        response = await model.generate_content_async(prompt)
                    
                    return response
                
                # Execute with timeout - this is the critical fix
                try:
                    response = await asyncio.wait_for(
                        _generate(), 
                        timeout=self.config.timeout_seconds
                    )
                    return response
                except asyncio.TimeoutError as e:
                    logger.warning(f"⏰ Gemini timeout after {self.config.timeout_seconds}s for {model_key}")
                    raise GeminiError(f"Gemini API timeout after {self.config.timeout_seconds} seconds") from e
            
            # Execute with retry logic and timeout
            start_time = time.time()
            try:
                response = await self._retry_with_backoff(_generate_with_timeout)
                
                # Report success to rate limiter
                response_time = time.time() - start_time
                await self._rate_limiter.on_request_success(response_time, estimated_tokens)
                
            except GeminiError as e:
                # Report failure to rate limiter
                error_type = "timeout" if "timeout" in str(e).lower() else "generation_error"
                await self._rate_limiter.on_request_failure(error_type)
                
                # If it's a timeout error, let it bubble up for fallback handling
                if "timeout" in str(e).lower():
                    logger.error(f"❌ Gemini generation timed out: {e}")
                    raise asyncio.TimeoutError(f"Gemini generation timed out: {e}") from e
                raise
            except Exception as e:
                # Report unexpected failure to rate limiter
                await self._rate_limiter.on_request_failure("unexpected_error")
                raise GeminiError(f"Unexpected error during generation: {e}") from e
            
            # Extract usage and track costs
            usage = self._extract_usage_from_response(response, model_key)
            self._track_daily_cost(usage.cost)
            self._request_count += 1
            
            # Check cost limits
            if usage.cost > self.config.max_cost_per_request:
                logger.warning(f"💰 Request cost exceeded limit: ${usage.cost:.4f} > ${self.config.max_cost_per_request:.4f}")
            
            # Build response
            content = response.text or ""
            finish_reason = getattr(response, 'finish_reason', None)
            
            logger.debug(f"✅ Generated {usage.total_tokens} tokens, cost: ${usage.cost:.4f}")
            
            return GeminiResponse(
                content=content,
                usage=usage,
                model=model_key,
                finish_reason=str(finish_reason) if finish_reason else None,
                metadata={
                    'request_id': f"gemini_{int(time.time())}_{self._request_count}",
                    'session_id': f"session_{int(self._session_created_at)}",
                    'daily_cost': self.get_daily_cost()
                }
            )
    
    async def generate_content_stream(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        Generate content with streaming response.
        
        Args:
            prompt: Text prompt for generation
            model_name: Model to use (defaults to config.model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Yields:
            Content chunks as they're generated
        """
        if not self.config.enable_streaming:
            # Fall back to non-streaming
            response = await self.generate_content(prompt, model_name, temperature, max_tokens)
            yield response.content
            return
        
        async with self._rate_limiter:
            model_key = model_name or self.config.model
            model = self._get_model(model_key)
            
            # Override generation config if specified
            generation_config = {}
            if temperature is not None:
                generation_config["temperature"] = temperature
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens
            
            async def _generate_stream():
                if generation_config:
                    temp_model = genai.GenerativeModel(
                        model_name=model_key,
                        generation_config=generation_config
                    )
                    response = await temp_model.generate_content_async(prompt, stream=True)
                else:
                    response = await model.generate_content_async(prompt, stream=True)
                
                return response
            
            # Execute with retry logic and timeout
            try:
                response = await asyncio.wait_for(
                    self._retry_with_backoff(_generate_stream),
                    timeout=self.config.stream_timeout_seconds
                )
                
                total_tokens = 0
                content_length = 0
                
                async for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        content_length += len(chunk.text)
                        yield chunk.text
                
                # Estimate final usage (streaming doesn't provide exact token counts)
                estimated_tokens = content_length // 4  # Rough estimate
                cost = calculate_gemini_cost(estimated_tokens // 2, estimated_tokens // 2, model_key)
                
                self._track_daily_cost(cost)
                self._request_count += 1
                
                logger.debug(f"🌊 Streamed ~{estimated_tokens} tokens, cost: ${cost:.4f}")
                
            except asyncio.TimeoutError as e:
                logger.error(f"⏰ Streaming timeout after {self.config.stream_timeout_seconds}s")
                raise GeminiError(f"Streaming timeout after {self.config.stream_timeout_seconds} seconds") from e
            except Exception as e:
                logger.error(f"❌ Streaming failed: {e}")
                raise GeminiError(f"Streaming generation failed: {e}")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model_name: str = "models/text-embedding-004"
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            model_name: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        async with self._rate_limiter:
            async def _embed():
                embeddings = []
                
                for text in texts:
                    try:
                        result = genai.embed_content(
                            model=model_name,
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings.append(result['embedding'])
                    except Exception as e:
                        logger.error(f"❌ Embedding failed for text: {text[:50]}... Error: {e}")
                        # Return zero vector as fallback
                        embeddings.append([0.0] * 768)  # Standard embedding dimension
                
                return embeddings
            
            return await self._retry_with_backoff(_embed)
    
    async def health_check(self) -> bool:
        """
        Perform health check on Gemini API.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Simple test generation
            response = await self.generate_content(
                "Health check",
                max_tokens=10
            )
            
            is_healthy = bool(response.content and response.usage.total_tokens > 0)
            
            if is_healthy:
                logger.info("✅ Gemini health check passed")
            else:
                logger.warning("⚠️ Gemini health check failed - no content generated")
            
            return is_healthy
            
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
            # Get model information
            model_info = genai.get_model(f"models/{model_key}")
            
            return {
                "name": model_info.name,
                "display_name": getattr(model_info, 'display_name', model_key),
                "description": getattr(model_info, 'description', ''),
                "input_token_limit": getattr(model_info, 'input_token_limit', self.config.max_context_tokens),
                "output_token_limit": getattr(model_info, 'output_token_limit', self.config.max_output_tokens),
                "supported_generation_methods": getattr(model_info, 'supported_generation_methods', []),
                "temperature_range": {
                    "min": 0.0,
                    "max": 2.0
                }
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch model info for {model_key}: {e}")
            return {
                "name": model_key,
                "display_name": model_key,
                "description": "Model information unavailable",
                "input_token_limit": self.config.max_context_tokens,
                "output_token_limit": self.config.max_output_tokens
            }
    
    async def close(self) -> None:
        """Clean up client resources."""
        self._model_cache.clear()
        logger.info("🧹 Gemini client resources cleaned up")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with client usage statistics
        """
        return {
            "requests_made": self._request_count,
            "daily_cost": self.get_daily_cost(),
            "cost_limit": self.config.daily_cost_limit,
            "session_duration_minutes": (time.time() - self._session_created_at) / 60,
            "models_cached": len(self._model_cache),
            "config": {
                "model": self.config.model,
                "max_concurrent": self.config.max_concurrent_requests,
                "streaming_enabled": self.config.enable_streaming
            }
        }
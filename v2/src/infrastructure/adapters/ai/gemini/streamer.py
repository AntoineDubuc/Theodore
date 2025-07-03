#!/usr/bin/env python3
"""
Google Gemini Streaming Response Handler
=======================================

Specialized streaming handler for Google Gemini API with advanced features:
- Real-time content streaming with buffering
- Token-level streaming control
- Connection monitoring and recovery
- Performance optimization for large responses
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Optional, Callable, Dict, Any
from datetime import datetime

from .client import GeminiClient, GeminiError
from .config import GeminiConfig


logger = logging.getLogger(__name__)


class GeminiStreamer:
    """
    Advanced streaming handler for Gemini API responses.
    
    Provides high-performance streaming with:
    - Real-time content delivery
    - Connection monitoring and recovery
    - Performance optimization
    - Error handling and fallbacks
    """
    
    def __init__(
        self, 
        config: GeminiConfig,
        token_manager: Optional['GeminiTokenManager'] = None,
        rate_limiter: Optional['GeminiRateLimiter'] = None
    ):
        """Initialize Gemini streamer."""
        self.config = config
        self.client = GeminiClient(config)
        self.token_manager = token_manager
        self.rate_limiter = rate_limiter
        
        # Streaming configuration
        self.buffer_size = config.chunk_size
        self.stream_timeout = config.stream_timeout_seconds
        
        # Performance tracking
        self._stream_count = 0
        self._total_chunks = 0
        self._total_bytes = 0
        
        logger.info(f"🌊 Gemini streamer initialized with {config.chunk_size} byte chunks")
    
    async def stream_analysis(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """
        Stream analysis response in real-time.
        
        Args:
            prompt: Text prompt for analysis
            model_name: Model to use for streaming
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            progress_callback: Optional callback for progress updates
            
        Yields:
            Content chunks as they're generated
        """
        stream_id = f"stream_{int(time.time())}_{self._stream_count}"
        self._stream_count += 1
        
        try:
            if progress_callback:
                progress_callback(f"🌊 Starting stream {stream_id}")
            
            # Apply rate limiting if available
            if self.rate_limiter:
                await self.rate_limiter.acquire()
            
            chunk_count = 0
            total_content = ""
            start_time = time.time()
            
            # Start streaming from client
            async for chunk in self.client.generate_content_stream(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                chunk_count += 1
                self._total_chunks += 1
                self._total_bytes += len(chunk)
                total_content += chunk
                
                # Apply buffering if needed
                if len(chunk) >= self.buffer_size or chunk_count % 10 == 0:
                    if progress_callback:
                        progress_callback(f"📤 Streamed chunk {chunk_count} ({len(chunk)} chars)")
                
                yield chunk
                
                # Check for timeout
                if time.time() - start_time > self.stream_timeout:
                    logger.warning(f"⏰ Stream {stream_id} timeout after {self.stream_timeout}s")
                    break
            
            # Final statistics
            duration = time.time() - start_time
            chars_per_second = len(total_content) / duration if duration > 0 else 0
            
            if progress_callback:
                progress_callback(f"✅ Stream completed: {chunk_count} chunks, {len(total_content)} chars, {chars_per_second:.1f} chars/s")
            
            logger.info(f"🌊 Stream {stream_id} completed: {chunk_count} chunks, {len(total_content)} chars in {duration:.1f}s")
            
            # Update token manager if available
            if self.token_manager:
                estimated_tokens = len(total_content) // 4  # Rough estimate
                await self.token_manager.track_usage(estimated_tokens, estimated_tokens // 2)
            
        except GeminiError as e:
            error_msg = f"Streaming failed for {stream_id}: {e}"
            logger.error(f"🌊❌ {error_msg}")
            
            if progress_callback:
                progress_callback(f"❌ Streaming error: {e}")
            
            raise GeminiError(error_msg)
        
        except asyncio.TimeoutError:
            error_msg = f"Stream {stream_id} timed out after {self.stream_timeout}s"
            logger.error(f"⏰ {error_msg}")
            
            if progress_callback:
                progress_callback(f"⏰ Stream timeout")
            
            raise GeminiError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected streaming error for {stream_id}: {e}"
            logger.error(f"🌊💥 {error_msg}")
            
            if progress_callback:
                progress_callback(f"💥 Unexpected error: {e}")
            
            raise GeminiError(error_msg)
        
        finally:
            # Release rate limiter if used
            if self.rate_limiter:
                self.rate_limiter.release()
    
    async def stream_with_buffering(
        self,
        prompt: str,
        buffer_lines: int = 5,
        model_name: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """
        Stream with line-based buffering for smoother output.
        
        Args:
            prompt: Text prompt for analysis
            buffer_lines: Number of lines to buffer before yielding
            model_name: Model to use for streaming
            progress_callback: Optional callback for progress updates
            
        Yields:
            Buffered content chunks
        """
        buffer = []
        line_count = 0
        
        try:
            async for chunk in self.stream_analysis(prompt, model_name=model_name, progress_callback=progress_callback):
                # Split chunk into lines
                lines = chunk.split('\n')
                
                for i, line in enumerate(lines):
                    if i == len(lines) - 1 and not chunk.endswith('\n'):
                        # Last line might be incomplete, add to buffer
                        buffer.append(line)
                    else:
                        # Complete line
                        if buffer:
                            buffer.append(line)
                            complete_line = ''.join(buffer)
                            buffer = []
                        else:
                            complete_line = line
                        
                        line_count += 1
                        
                        # Buffer until we have enough lines
                        if line_count % buffer_lines == 0:
                            yield complete_line + '\n'
                        else:
                            # Store in buffer
                            if not buffer:
                                buffer = [complete_line + '\n']
                            else:
                                buffer.append(complete_line + '\n')
            
            # Yield any remaining buffered content
            if buffer:
                yield ''.join(buffer)
                
        except Exception as e:
            logger.error(f"🌊📦 Buffered streaming failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Perform health check on streaming capabilities.
        
        Returns:
            True if streaming is functional, False otherwise
        """
        try:
            # Test streaming with minimal content
            test_prompt = "Test streaming"
            chunks_received = 0
            
            async for chunk in self.stream_analysis(test_prompt, max_tokens=10):
                chunks_received += 1
                if chunks_received >= 1:  # At least one chunk
                    break
            
            is_healthy = chunks_received > 0
            
            if is_healthy:
                logger.info("✅ Gemini streaming health check passed")
            else:
                logger.warning("⚠️ Gemini streaming health check failed")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"❌ Gemini streaming health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get streaming statistics.
        
        Returns:
            Dictionary with streaming performance stats
        """
        return {
            'streams_created': self._stream_count,
            'total_chunks_processed': self._total_chunks,
            'total_bytes_streamed': self._total_bytes,
            'average_chunk_size': self._total_bytes / self._total_chunks if self._total_chunks > 0 else 0,
            'buffer_size': self.buffer_size,
            'stream_timeout': self.stream_timeout,
            'streaming_enabled': self.config.enable_streaming
        }
    
    async def close(self) -> None:
        """Clean up streamer resources."""
        await self.client.close()
        logger.info("🧹 Gemini streamer resources cleaned up")
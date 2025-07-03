#!/usr/bin/env python3
"""
Google Gemini Rate Limiting System
=================================

Advanced rate limiting for Google Gemini API with enterprise features:
- Token bucket algorithm for smooth rate limiting
- Adaptive rate limiting based on API responses
- Concurrent request management
- Circuit breaker patterns for reliability
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .config import GeminiConfig


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class RateLimitStats:
    """Rate limiting statistics."""
    requests_made: int = 0
    requests_rejected: int = 0
    requests_per_minute: float = 0.0
    tokens_per_minute: float = 0.0
    average_wait_time: float = 0.0
    circuit_state: CircuitState = CircuitState.CLOSED
    last_reset: Optional[datetime] = None


class TokenBucket:
    """
    Token bucket implementation for rate limiting.
    
    Provides smooth rate limiting with burst capability.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens_needed: int = 1) -> bool:
        """
        Try to acquire tokens from bucket.
        
        Args:
            tokens_needed: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self._lock:
            now = time.time()
            
            # Refill bucket based on time elapsed
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens_needed: int = 1) -> float:
        """
        Wait until tokens are available.
        
        Args:
            tokens_needed: Number of tokens needed
            
        Returns:
            Time waited in seconds
        """
        start_time = time.time()
        
        while not await self.acquire(tokens_needed):
            # Calculate wait time
            shortage = tokens_needed - self.tokens
            wait_time = shortage / self.refill_rate
            
            # Wait for a fraction of the needed time
            await asyncio.sleep(min(wait_time, 0.1))
        
        return time.time() - start_time


class CircuitBreaker:
    """
    Circuit breaker for API reliability.
    
    Implements circuit breaker pattern to handle API failures gracefully.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying half-open state
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call_allowed(self) -> bool:
        """
        Check if a call is allowed through the circuit.
        
        Returns:
            True if call is allowed, False otherwise
        """
        async with self._lock:
            now = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if now - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("🔄 Circuit breaker transitioning to HALF_OPEN")
                    return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
            
            return False
    
    async def on_success(self):
        """Record successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("✅ Circuit breaker closed after successful recovery")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)  # Gradually reduce failure count
    
    async def on_failure(self):
        """Record failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("🔴 Circuit breaker opened after half-open failure")
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"🔴 Circuit breaker opened after {self.failure_count} failures")


class GeminiRateLimiter:
    """
    Advanced rate limiter for Google Gemini API.
    
    Provides comprehensive rate limiting with:
    - Request rate limiting (requests per minute)
    - Token rate limiting (tokens per minute)
    - Concurrent request limiting
    - Circuit breaker protection
    - Adaptive rate adjustment
    """
    
    def __init__(self, config: GeminiConfig):
        """Initialize rate limiter with configuration."""
        self.config = config
        
        # Token buckets for different rate limits
        self.request_bucket = TokenBucket(
            capacity=config.requests_per_minute,
            refill_rate=config.requests_per_minute / 60.0  # requests per second
        )
        
        self.token_bucket = TokenBucket(
            capacity=config.tokens_per_minute,
            refill_rate=config.tokens_per_minute / 60.0  # tokens per second
        )
        
        # Concurrent request limiting
        self.concurrent_semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()
        
        # Statistics tracking
        self.stats = RateLimitStats()
        self._request_times: List[float] = []
        self._wait_times: List[float] = []
        
        logger.info(f"🚦 Rate limiter initialized: {config.requests_per_minute} req/min, {config.tokens_per_minute} tokens/min, {config.max_concurrent_requests} concurrent")
    
    async def acquire(self, estimated_tokens: int = 1000) -> bool:
        """
        Try to acquire permission for a request.
        
        Args:
            estimated_tokens: Estimated tokens for the request
            
        Returns:
            True if permission granted, False otherwise
        """
        # Check circuit breaker first
        if not await self.circuit_breaker.call_allowed():
            self.stats.requests_rejected += 1
            logger.warning("🔴 Request rejected by circuit breaker")
            return False
        
        # Try to acquire request token
        if not await self.request_bucket.acquire(1):
            self.stats.requests_rejected += 1
            logger.debug("⏳ Request rejected by request rate limit")
            return False
        
        # Try to acquire token budget
        if not await self.token_bucket.acquire(estimated_tokens):
            self.stats.requests_rejected += 1
            logger.debug(f"⏳ Request rejected by token rate limit ({estimated_tokens} tokens)")
            return False
        
        self.stats.requests_made += 1
        return True
    
    async def acquire_with_wait(self, estimated_tokens: int = 1000) -> float:
        """
        Acquire permission for a request, waiting if necessary.
        
        Args:
            estimated_tokens: Estimated tokens for the request
            
        Returns:
            Time waited in seconds
        """
        start_time = time.time()
        
        # Check circuit breaker
        while not await self.circuit_breaker.call_allowed():
            logger.info("🔴 Waiting for circuit breaker to recover...")
            await asyncio.sleep(1.0)
        
        # Wait for request slot
        request_wait = await self.request_bucket.wait_for_tokens(1)
        
        # Wait for token budget
        token_wait = await self.token_bucket.wait_for_tokens(estimated_tokens)
        
        total_wait = time.time() - start_time
        self._wait_times.append(total_wait)
        
        # Keep only recent wait times for averaging
        if len(self._wait_times) > 100:
            self._wait_times = self._wait_times[-100:]
        
        self.stats.average_wait_time = sum(self._wait_times) / len(self._wait_times)
        self.stats.requests_made += 1
        
        logger.debug(f"⏳ Acquired after {total_wait:.2f}s wait")
        
        return total_wait
    
    async def __aenter__(self):
        """Async context manager entry - acquire concurrent slot."""
        await self.concurrent_semaphore.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - release concurrent slot."""
        self.concurrent_semaphore.release()
        
        # Update circuit breaker based on success/failure
        if exc_type is None:
            await self.circuit_breaker.on_success()
        else:
            await self.circuit_breaker.on_failure()
    
    def release(self):
        """Release a concurrent request slot (for manual management)."""
        self.concurrent_semaphore.release()
    
    async def on_request_success(self, response_time: float, tokens_used: int):
        """
        Record successful request for adaptive rate limiting.
        
        Args:
            response_time: Response time in seconds
            tokens_used: Actual tokens used
        """
        self._request_times.append(response_time)
        
        # Keep only recent times for analysis
        if len(self._request_times) > 100:
            self._request_times = self._request_times[-100:]
        
        await self.circuit_breaker.on_success()
        
        # Update statistics
        self._update_rate_stats()
    
    async def on_request_failure(self, error_type: str):
        """
        Record failed request.
        
        Args:
            error_type: Type of error encountered
        """
        await self.circuit_breaker.on_failure()
        
        # Update statistics
        self._update_rate_stats()
        
        logger.warning(f"🔴 Request failed: {error_type}")
    
    def _update_rate_stats(self):
        """Update rate limiting statistics."""
        now = time.time()
        minute_ago = now - 60
        
        # Calculate requests per minute
        recent_requests = sum(1 for t in self._request_times if t > minute_ago)
        self.stats.requests_per_minute = recent_requests
        
        # Update circuit state
        self.stats.circuit_state = self.circuit_breaker.state
    
    async def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current rate limiting usage.
        
        Returns:
            Dictionary with current usage information
        """
        return {
            'requests_made': self.stats.requests_made,
            'requests_rejected': self.stats.requests_rejected,
            'requests_per_minute': self.stats.requests_per_minute,
            'request_rate_limit': self.config.requests_per_minute,
            'token_rate_limit': self.config.tokens_per_minute,
            'concurrent_limit': self.config.max_concurrent_requests,
            'concurrent_available': self.concurrent_semaphore._value,
            'average_wait_time': self.stats.average_wait_time,
            'circuit_state': self.stats.circuit_state.value,
            'success_rate': (self.stats.requests_made / (self.stats.requests_made + self.stats.requests_rejected)) * 100 if (self.stats.requests_made + self.stats.requests_rejected) > 0 else 100
        }
    
    async def adjust_rates(self, success_rate: float, avg_response_time: float):
        """
        Adaptively adjust rate limits based on performance.
        
        Args:
            success_rate: Recent success rate (0.0 to 1.0)
            avg_response_time: Average response time in seconds
        """
        # If success rate is low, reduce rates
        if success_rate < 0.8:
            reduction_factor = 0.8
            logger.warning(f"🔻 Reducing rates due to low success rate: {success_rate:.1%}")
        
        # If response time is high, reduce rates
        elif avg_response_time > 10.0:
            reduction_factor = 0.9
            logger.warning(f"🔻 Reducing rates due to high response time: {avg_response_time:.1f}s")
        
        # If everything is good, gradually increase rates
        elif success_rate > 0.95 and avg_response_time < 5.0:
            reduction_factor = 1.1
            logger.info("🔺 Gradually increasing rates due to good performance")
        
        else:
            return  # No adjustment needed
        
        # Apply rate adjustments
        new_request_rate = min(
            self.config.requests_per_minute * reduction_factor,
            self.config.requests_per_minute  # Don't exceed original config
        )
        
        new_token_rate = min(
            self.config.tokens_per_minute * reduction_factor,
            self.config.tokens_per_minute  # Don't exceed original config
        )
        
        # Update token buckets
        self.request_bucket.refill_rate = new_request_rate / 60.0
        self.token_bucket.refill_rate = new_token_rate / 60.0
        
        logger.info(f"🚦 Rate limits adjusted: {new_request_rate:.0f} req/min, {new_token_rate:.0f} tokens/min")
    
    def reset_stats(self):
        """Reset rate limiting statistics."""
        self.stats = RateLimitStats()
        self._request_times.clear()
        self._wait_times.clear()
        logger.info("📊 Rate limiter statistics reset")
    
    async def health_check(self) -> bool:
        """
        Perform health check on rate limiter.
        
        Returns:
            True if rate limiter is functioning properly
        """
        try:
            # Test token bucket acquisition
            can_acquire = await self.request_bucket.acquire(1)
            if can_acquire:
                # Return the token
                self.request_bucket.tokens += 1
            
            # Check circuit breaker state
            circuit_ok = self.circuit_breaker.state != CircuitState.OPEN
            
            # Check concurrent semaphore
            semaphore_ok = self.concurrent_semaphore._value > 0
            
            is_healthy = circuit_ok and semaphore_ok
            
            if is_healthy:
                logger.info("✅ Rate limiter health check passed")
            else:
                logger.warning("⚠️ Rate limiter health check failed")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"❌ Rate limiter health check failed: {e}")
            return False
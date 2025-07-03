#!/usr/bin/env python3
"""
Google Gemini AI Adapter Package
===============================

This package provides production-ready adapters for Google Gemini AI services,
supporting large-scale content analysis with 1M+ token context windows,
streaming responses, and comprehensive monitoring.

Features:
- Gemini 2.5 Pro model support with 1M token context
- Streaming response handling for real-time feedback
- Thread-safe concurrent request processing
- Comprehensive cost tracking and rate limiting
- Content aggregation and optimization for large-scale analysis
- Production-grade error handling and monitoring

Cost Optimization:
- Gemini 2.5 Pro: Competitive pricing for large context processing
- Intelligent content optimization to maximize context utilization
- Rate limiting to prevent quota exhaustion
- Cost tracking with detailed usage analytics

Usage:
```python
from src.infrastructure.adapters.ai.gemini import create_gemini_analyzer

# Create with environment configuration
analyzer = create_gemini_analyzer()

# Or with custom configuration
config = GeminiConfig(
    api_key="your_api_key",
    model="gemini-2.5-pro",
    max_context_tokens=1000000
)
analyzer = create_gemini_analyzer(config)
```

Production Recommendations:
- Use Gemini 2.5 Pro for large content aggregation
- Enable streaming for long-running analysis
- Set appropriate rate limits for production usage
- Monitor token usage and costs
- Use thread-local storage for concurrent operations
- Implement proper error handling and fallbacks
"""

from .analyzer import GeminiAnalyzer
from .client import GeminiClient
from .config import GeminiConfig, calculate_gemini_cost
from .streamer import GeminiStreamer
from .token_manager import GeminiTokenManager
from .rate_limiter import GeminiRateLimiter

__all__ = [
    "GeminiAnalyzer",
    "GeminiClient", 
    "GeminiConfig",
    "GeminiStreamer",
    "GeminiTokenManager",
    "GeminiRateLimiter",
    "calculate_gemini_cost",
    "create_gemini_analyzer",
    "create_gemini_streamer",
    "create_production_gemini_suite"
]


# Production factory functions
def create_gemini_analyzer(config: 'GeminiConfig' = None) -> 'GeminiAnalyzer':
    """Create a production-ready Gemini analyzer with optimal settings."""
    
    if config is None:
        config = GeminiConfig.from_environment()
    
    # Apply production optimizations
    config.max_retries = max(config.max_retries, 3)
    config.timeout_seconds = max(config.timeout_seconds, 120)  # Longer for large context
    config.enable_cost_tracking = True
    config.enable_streaming = True
    
    analyzer = GeminiAnalyzer(config)
    
    return analyzer


def create_gemini_streamer(config: 'GeminiConfig' = None) -> 'GeminiStreamer':
    """Create a production-ready Gemini streamer for real-time responses."""
    
    if config is None:
        config = GeminiConfig.from_environment()
    
    # Apply streaming-specific optimizations
    config.enable_streaming = True
    config.stream_timeout_seconds = 300  # 5 minutes for long streams
    config.chunk_size = 1024
    
    streamer = GeminiStreamer(config)
    
    return streamer


def create_production_gemini_suite(config: 'GeminiConfig' = None) -> tuple:
    """Create a complete production Gemini suite with shared components."""
    
    if config is None:
        config = GeminiConfig.from_environment()
    
    # Production settings for high-throughput usage
    config.max_retries = 5
    config.timeout_seconds = 180
    config.enable_cost_tracking = True
    config.enable_streaming = True
    config.max_concurrent_requests = 10
    
    # Shared components
    token_manager = GeminiTokenManager(config)
    rate_limiter = GeminiRateLimiter(config)
    
    # Create analyzer and streamer (they create their own internal components)
    analyzer = GeminiAnalyzer(config)
    streamer = GeminiStreamer(config)
    
    return analyzer, streamer


# Health monitoring utilities
async def check_gemini_health(config: 'GeminiConfig' = None) -> dict:
    """Comprehensive health check for Gemini services."""
    import time
    
    if config is None:
        config = GeminiConfig.from_environment()
    
    analyzer = GeminiAnalyzer(config)
    
    health_status = {
        'analyzer': False,
        'streaming': False,
        'overall': False,
        'model': config.model,
        'timestamp': time.time()
    }
    
    try:
        # Test analyzer
        health_status['analyzer'] = await analyzer.health_check()
        
        # Test streaming capability
        streamer = GeminiStreamer(config)
        health_status['streaming'] = await streamer.health_check()
        
        # Overall health
        health_status['overall'] = health_status['analyzer'] and health_status['streaming']
        
    except Exception as e:
        health_status['error'] = str(e)
    
    return health_status


# Cost monitoring utilities  
def get_gemini_cost_estimates(input_tokens: int = 1000, output_tokens: int = 500) -> dict:
    """Get cost estimates for Gemini models."""
    
    estimates = {}
    models = ['gemini-2.5-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']
    
    for model in models:
        try:
            total_cost = calculate_gemini_cost(input_tokens, output_tokens, model)
            estimates[model] = {
                'total_cost': total_cost,
                'cost_per_1k_tokens': total_cost / ((input_tokens + output_tokens) / 1000),
                'context_capacity': 1000000 if 'pro' in model else 128000
            }
        except ValueError:
            continue
    
    return estimates


# Configuration helpers
def create_cost_optimized_config(daily_budget: float = 20.0) -> 'GeminiConfig':
    """Create a cost-optimized configuration for budget-conscious usage."""
    
    return GeminiConfig(
        model="gemini-1.5-flash",  # Cheaper model
        max_context_tokens=128000,  # Smaller context
        daily_cost_limit=daily_budget,
        max_cost_per_request=min(daily_budget * 0.1, 2.0),
        enable_cost_tracking=True,
        max_retries=3,
        timeout_seconds=60,
        max_concurrent_requests=3  # Lower for cost optimization
    )


def create_performance_optimized_config(daily_budget: float = 100.0) -> 'GeminiConfig':
    """Create a performance-optimized configuration for high-throughput usage."""
    
    return GeminiConfig(
        model="gemini-2.5-pro",  # Best quality and context
        max_context_tokens=1000000,  # Full context window
        daily_cost_limit=daily_budget,
        max_cost_per_request=10.0,
        enable_cost_tracking=True,
        enable_streaming=True,
        max_retries=5,
        timeout_seconds=300,
        max_concurrent_requests=10,
        enable_caching=True,
        cache_ttl_seconds=7200  # 2 hour cache
    )
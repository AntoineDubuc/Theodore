#!/usr/bin/env python3
"""
AWS Bedrock AI Adapter Package
==============================

This package provides production-ready adapters for AWS Bedrock AI services,
supporting both text analysis and embedding generation with comprehensive
cost tracking and monitoring.

Features:
- Nova Pro/Lite model support for cost optimization
- Claude and Titan model support  
- Batch embedding processing
- Comprehensive retry logic with exponential backoff
- Real-time cost tracking and limits
- Health monitoring and circuit breakers
- Production-grade error handling

Cost Optimization:
- Nova Pro: 6x cheaper than OpenAI GPT-4 ($0.11 vs $0.66 per analysis)
- Nova Lite: 13x cheaper than Nova Pro for simple tasks
- Titan Embeddings: $0.0001 per 1K tokens vs $0.0002 for competitors

Usage:
```python
from src.infrastructure.adapters.ai.bedrock import create_bedrock_analyzer, create_bedrock_embedder

# Create with environment configuration
analyzer = create_bedrock_analyzer()
embedder = create_bedrock_embedder()

# Or with custom configuration
config = BedrockConfig(
    region_name="us-west-2",
    default_model="amazon.nova-pro-v1:0",
    daily_cost_limit=50.0
)
analyzer = create_bedrock_analyzer(config)
```

Production Recommendations:
- Use Nova Pro for complex analysis (best quality/cost ratio)
- Use Nova Lite for simple classification tasks
- Set appropriate daily cost limits
- Monitor health checks and implement circuit breakers
- Use batch processing for embeddings when possible
"""

from .analyzer import BedrockAnalyzer
from .embedder import BedrockEmbeddingProvider
from .client import BedrockClient
from .config import BedrockConfig, BEDROCK_MODEL_COSTS, calculate_bedrock_cost

__all__ = [
    "BedrockAnalyzer",
    "BedrockEmbeddingProvider", 
    "BedrockClient",
    "BedrockConfig",
    "BEDROCK_MODEL_COSTS",
    "calculate_bedrock_cost",
    "create_bedrock_analyzer",
    "create_bedrock_embedder",
    "create_production_bedrock_suite"
]


# Production factory functions
def create_bedrock_analyzer(config: 'BedrockConfig' = None) -> 'BedrockAnalyzer':
    """Create a production-ready Bedrock analyzer with optimal settings."""
    
    if config is None:
        config = BedrockConfig.from_environment()
    
    # Apply production optimizations
    config.max_retries = max(config.max_retries, 3)
    config.timeout_seconds = max(config.timeout_seconds, 60)
    config.enable_cost_tracking = True
    
    analyzer = BedrockAnalyzer(config)
    
    return analyzer


def create_bedrock_embedder(config: 'BedrockConfig' = None) -> 'BedrockEmbeddingProvider':
    """Create a production-ready Bedrock embedder with optimal settings."""
    
    if config is None:
        config = BedrockConfig.from_environment()
    
    # Apply embedding-specific optimizations
    config.connection_pool_size = max(config.connection_pool_size, 20)  # Higher for embeddings
    config.enable_caching = True
    
    embedder = BedrockEmbeddingProvider(config)
    
    return embedder


def create_production_bedrock_suite(config: 'BedrockConfig' = None) -> tuple:
    """Create a complete production Bedrock suite with shared client."""
    
    if config is None:
        config = BedrockConfig.from_environment()
    
    # Production settings for high-throughput usage
    config.connection_pool_size = 25
    config.max_retries = 5
    config.timeout_seconds = 90
    config.enable_cost_tracking = True
    config.enable_caching = True
    
    analyzer = BedrockAnalyzer(config)
    embedder = BedrockEmbeddingProvider(config)
    
    return analyzer, embedder


# Health monitoring utilities
async def check_bedrock_health(config: 'BedrockConfig' = None) -> dict:
    """Comprehensive health check for Bedrock services."""
    import time
    
    if config is None:
        config = BedrockConfig.from_environment()
    
    analyzer = BedrockAnalyzer(config)
    embedder = BedrockEmbeddingProvider(config)
    
    health_status = {
        'analyzer': False,
        'embedder': False,
        'overall': False,
        'region': config.region_name,
        'timestamp': time.time()
    }
    
    try:
        # Test analyzer
        health_status['analyzer'] = await analyzer.health_check()
        
        # Test embedder
        health_status['embedder'] = await embedder.health_check()
        
        # Overall health
        health_status['overall'] = health_status['analyzer'] and health_status['embedder']
        
    except Exception as e:
        health_status['error'] = str(e)
    
    return health_status


# Cost monitoring utilities
def get_model_cost_estimates(input_tokens: int = 1000, output_tokens: int = 500) -> dict:
    """Get cost estimates for all supported Bedrock models."""
    
    estimates = {}
    
    for model_id, costs in BEDROCK_MODEL_COSTS.items():
        total_cost = calculate_bedrock_cost(input_tokens, output_tokens, model_id)
        estimates[model_id] = {
            'total_cost': total_cost,
            'input_cost': (input_tokens / 1000) * costs['input_cost_per_1k_tokens'],
            'output_cost': (output_tokens / 1000) * costs['output_cost_per_1k_tokens'],
            'cost_per_1k_tokens': total_cost / ((input_tokens + output_tokens) / 1000)
        }
    
    return estimates


# Configuration helpers
def create_cost_optimized_config(daily_budget: float = 10.0) -> 'BedrockConfig':
    """Create a cost-optimized configuration for budget-conscious usage."""
    
    return BedrockConfig(
        default_model="amazon.nova-lite-v1:0",  # Cheapest model
        embedding_model="amazon.titan-embed-text-v2:0",
        daily_cost_limit=daily_budget,
        max_cost_per_request=min(daily_budget * 0.1, 1.0),
        enable_cost_tracking=True,
        max_retries=3,
        timeout_seconds=30,
        connection_pool_size=5  # Lower for cost optimization
    )


def create_performance_optimized_config(daily_budget: float = 100.0) -> 'BedrockConfig':
    """Create a performance-optimized configuration for high-throughput usage."""
    
    return BedrockConfig(
        default_model="amazon.nova-pro-v1:0",  # Best quality
        embedding_model="amazon.titan-embed-text-v2:0",
        daily_cost_limit=daily_budget,
        max_cost_per_request=5.0,
        enable_cost_tracking=True,
        max_retries=5,
        timeout_seconds=90,
        connection_pool_size=25,
        enable_caching=True,
        cache_ttl_seconds=3600
    )
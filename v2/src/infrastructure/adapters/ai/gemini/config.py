#!/usr/bin/env python3
"""
Gemini Configuration and Cost Management
=======================================

Configuration management and cost calculation utilities for Google Gemini adapters.
Provides enterprise-grade cost tracking and budget management capabilities.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import os


@dataclass
class GeminiConfig:
    """Configuration for Google Gemini adapter."""
    
    # API Configuration
    api_key: Optional[str] = None
    model: str = "gemini-2.5-pro"
    max_context_tokens: int = 1000000  # 1M token context for 2.5 Pro
    
    # Request Configuration
    temperature: float = 0.1
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    
    # Retry and Timeout
    max_retries: int = 3
    timeout_seconds: int = 120
    
    # Streaming Configuration
    enable_streaming: bool = True
    stream_timeout_seconds: int = 300
    chunk_size: int = 1024
    
    # Cost Control
    max_cost_per_request: float = 5.0
    daily_cost_limit: float = 100.0
    enable_cost_tracking: bool = True
    
    # Performance
    max_concurrent_requests: int = 5
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    
    # Rate Limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 1000000
    
    @classmethod
    def from_environment(cls) -> 'GeminiConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv('GEMINI_API_KEY'),
            model=os.getenv('GEMINI_MODEL', 'gemini-2.5-pro'),
            max_context_tokens=int(os.getenv('GEMINI_MAX_CONTEXT_TOKENS', '1000000')),
            temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
            max_output_tokens=int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192')),
            max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '3')),
            timeout_seconds=int(os.getenv('GEMINI_TIMEOUT', '120')),
            max_cost_per_request=float(os.getenv('GEMINI_MAX_COST_PER_REQUEST', '5.0')),
            daily_cost_limit=float(os.getenv('GEMINI_DAILY_COST_LIMIT', '100.0')),
            enable_streaming=os.getenv('GEMINI_ENABLE_STREAMING', 'true').lower() == 'true',
            max_concurrent_requests=int(os.getenv('GEMINI_MAX_CONCURRENT', '5'))
        )


# Cost models for different Gemini models (as of December 2024)
GEMINI_MODEL_COSTS = {
    'gemini-2.5-pro': {
        'input_cost_per_1k_tokens': 0.00125,  # $1.25 per 1M tokens
        'output_cost_per_1k_tokens': 0.005,   # $5.00 per 1M tokens  
        'context_limit': 1000000,
        'output_limit': 8192,
        'currency': 'USD'
    },
    'gemini-1.5-pro': {
        'input_cost_per_1k_tokens': 0.00125,  # $1.25 per 1M tokens
        'output_cost_per_1k_tokens': 0.005,   # $5.00 per 1M tokens
        'context_limit': 128000,
        'output_limit': 8192,
        'currency': 'USD'
    },
    'gemini-1.5-flash': {
        'input_cost_per_1k_tokens': 0.000075,  # $0.075 per 1M tokens
        'output_cost_per_1k_tokens': 0.0003,   # $0.30 per 1M tokens
        'context_limit': 128000,
        'output_limit': 8192,
        'currency': 'USD'
    },
    'gemini-1.0-pro': {
        'input_cost_per_1k_tokens': 0.0005,   # $0.50 per 1M tokens
        'output_cost_per_1k_tokens': 0.0015,  # $1.50 per 1M tokens
        'context_limit': 32000,
        'output_limit': 2048,
        'currency': 'USD'
    }
}


def calculate_gemini_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate cost for Gemini API usage.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
        
    Returns:
        Total cost in USD
        
    Raises:
        ValueError: If model is not supported
    """
    
    if model not in GEMINI_MODEL_COSTS:
        raise ValueError(f"Unknown model: {model}")
    
    costs = GEMINI_MODEL_COSTS[model]
    
    input_cost = (input_tokens / 1000) * costs['input_cost_per_1k_tokens']
    output_cost = (output_tokens / 1000) * costs['output_cost_per_1k_tokens']
    
    return input_cost + output_cost


def get_cheapest_gemini_model_for_task(task_type: str = "analysis") -> str:
    """
    Get the most cost-effective Gemini model for a given task type.
    
    Args:
        task_type: Type of task ("analysis", "large_context", "fast", "simple")
        
    Returns:
        Model identifier for the most cost-effective option
    """
    
    if task_type == "large_context":
        return "gemini-2.5-pro"  # Only model with 1M context
    elif task_type == "fast":
        return "gemini-1.5-flash"  # Fastest and cheapest
    elif task_type == "simple":
        return "gemini-1.0-pro"   # Basic analysis
    elif task_type == "analysis":
        return "gemini-1.5-pro"   # Good balance
    else:
        return "gemini-1.5-pro"   # Default


def compare_gemini_model_costs(input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """
    Compare costs across all available Gemini models.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Dictionary mapping model names to total costs (sorted by cost)
    """
    
    costs = {}
    
    for model in GEMINI_MODEL_COSTS:
        try:
            cost = calculate_gemini_cost(input_tokens, output_tokens, model)
            costs[model] = cost
        except ValueError:
            continue
    
    return dict(sorted(costs.items(), key=lambda x: x[1]))


def estimate_gemini_monthly_cost(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str
) -> Dict[str, float]:
    """
    Estimate monthly costs for consistent Gemini usage patterns.
    
    Args:
        requests_per_day: Average requests per day
        avg_input_tokens: Average input tokens per request
        avg_output_tokens: Average output tokens per request
        model: Model identifier
        
    Returns:
        Dictionary with cost breakdown
    """
    
    daily_cost = calculate_gemini_cost(
        avg_input_tokens * requests_per_day,
        avg_output_tokens * requests_per_day,
        model
    )
    
    return {
        'daily_cost': daily_cost,
        'weekly_cost': daily_cost * 7,
        'monthly_cost': daily_cost * 30,
        'annual_cost': daily_cost * 365,
        'cost_per_request': daily_cost / requests_per_day,
        'model': model,
        'requests_per_day': requests_per_day,
        'context_capacity': GEMINI_MODEL_COSTS[model]['context_limit']
    }


def get_optimal_gemini_model_for_content_size(token_count: int, budget_per_request: float = 1.0) -> str:
    """
    Get the optimal Gemini model based on content size and budget.
    
    Args:
        token_count: Estimated token count for the content
        budget_per_request: Maximum budget per request
        
    Returns:
        Recommended model identifier
    """
    
    # Check if we need large context
    if token_count > 128000:
        return "gemini-2.5-pro"  # Only option for large context
    
    # Compare costs for normal context models
    models_to_consider = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    
    for model in models_to_consider:
        # Estimate cost (assuming 10% output tokens)
        estimated_cost = calculate_gemini_cost(token_count, token_count // 10, model)
        
        if estimated_cost <= budget_per_request:
            return model
    
    # If budget is very tight, use the cheapest
    return "gemini-1.5-flash"


# Model capability matrix
GEMINI_MODEL_CAPABILITIES = {
    'gemini-2.5-pro': {
        'max_context': 1000000,
        'max_output': 8192,
        'supports_streaming': True,
        'supports_function_calling': True,
        'best_for': ['large_context', 'complex_analysis', 'content_aggregation'],
        'relative_speed': 'medium',
        'relative_cost': 'high'
    },
    'gemini-1.5-pro': {
        'max_context': 128000,
        'max_output': 8192,
        'supports_streaming': True,
        'supports_function_calling': True,
        'best_for': ['general_analysis', 'balanced_performance'],
        'relative_speed': 'medium',
        'relative_cost': 'medium'
    },
    'gemini-1.5-flash': {
        'max_context': 128000,
        'max_output': 8192,
        'supports_streaming': True,
        'supports_function_calling': True,
        'best_for': ['fast_analysis', 'cost_optimization', 'high_throughput'],
        'relative_speed': 'fast',
        'relative_cost': 'low'
    },
    'gemini-1.0-pro': {
        'max_context': 32000,
        'max_output': 2048,
        'supports_streaming': True,
        'supports_function_calling': False,
        'best_for': ['simple_analysis', 'legacy_compatibility'],
        'relative_speed': 'medium',
        'relative_cost': 'low'
    }
}
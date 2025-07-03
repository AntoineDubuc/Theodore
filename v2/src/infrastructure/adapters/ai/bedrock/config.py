#!/usr/bin/env python3
"""
Bedrock Configuration and Cost Management
=========================================

Configuration management and cost calculation utilities for AWS Bedrock adapters.
Provides enterprise-grade cost tracking and budget management capabilities.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import os


@dataclass
class BedrockConfig:
    """Configuration for AWS Bedrock adapter."""
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    region_name: str = "us-east-1"
    
    # Model Configuration
    default_model: str = "amazon.nova-pro-v1:0"
    embedding_model: str = "amazon.titan-embed-text-v2:0"
    max_retries: int = 3
    timeout_seconds: int = 60
    
    # Cost Control
    max_cost_per_request: float = 1.0
    daily_cost_limit: float = 100.0
    enable_cost_tracking: bool = True
    
    # Performance
    connection_pool_size: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    
    @classmethod
    def from_environment(cls) -> 'BedrockConfig':
        """Create configuration from environment variables."""
        return cls(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            default_model=os.getenv('BEDROCK_DEFAULT_MODEL', 'amazon.nova-pro-v1:0'),
            embedding_model=os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0'),
            max_retries=int(os.getenv('BEDROCK_MAX_RETRIES', '3')),
            timeout_seconds=int(os.getenv('BEDROCK_TIMEOUT', '60')),
            max_cost_per_request=float(os.getenv('BEDROCK_MAX_COST_PER_REQUEST', '1.0')),
            daily_cost_limit=float(os.getenv('BEDROCK_DAILY_COST_LIMIT', '100.0'))
        )


# Cost models for different Bedrock models (as of December 2024)
BEDROCK_MODEL_COSTS = {
    'amazon.nova-pro-v1:0': {
        'input_cost_per_1k_tokens': 0.0008,
        'output_cost_per_1k_tokens': 0.0032,
        'currency': 'USD'
    },
    'amazon.nova-lite-v1:0': {
        'input_cost_per_1k_tokens': 0.00006,
        'output_cost_per_1k_tokens': 0.00024,
        'currency': 'USD'
    },
    'amazon.nova-micro-v1:0': {
        'input_cost_per_1k_tokens': 0.000035,
        'output_cost_per_1k_tokens': 0.00014,
        'currency': 'USD'
    },
    'anthropic.claude-3-5-sonnet-20241022-v2:0': {
        'input_cost_per_1k_tokens': 0.003,
        'output_cost_per_1k_tokens': 0.015,
        'currency': 'USD'
    },
    'anthropic.claude-3-5-haiku-20241022-v1:0': {
        'input_cost_per_1k_tokens': 0.00025,
        'output_cost_per_1k_tokens': 0.00125,
        'currency': 'USD'
    },
    'amazon.titan-text-premier-v1:0': {
        'input_cost_per_1k_tokens': 0.0005,
        'output_cost_per_1k_tokens': 0.0015,
        'currency': 'USD'
    },
    'amazon.titan-embed-text-v1:0': {
        'input_cost_per_1k_tokens': 0.0001,
        'output_cost_per_1k_tokens': 0.0,
        'currency': 'USD'
    },
    'amazon.titan-embed-text-v2:0': {
        'input_cost_per_1k_tokens': 0.0001,
        'output_cost_per_1k_tokens': 0.0,
        'currency': 'USD'
    },
    'cohere.embed-english-v3:0': {
        'input_cost_per_1k_tokens': 0.0001,
        'output_cost_per_1k_tokens': 0.0,
        'currency': 'USD'
    },
    'cohere.embed-multilingual-v3:0': {
        'input_cost_per_1k_tokens': 0.0001,
        'output_cost_per_1k_tokens': 0.0,
        'currency': 'USD'
    }
}


def calculate_bedrock_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate cost for Bedrock API usage.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
        
    Returns:
        Total cost in USD
        
    Raises:
        ValueError: If model is not supported
    """
    
    if model not in BEDROCK_MODEL_COSTS:
        raise ValueError(f"Unknown model: {model}")
    
    costs = BEDROCK_MODEL_COSTS[model]
    
    input_cost = (input_tokens / 1000) * costs['input_cost_per_1k_tokens']
    output_cost = (output_tokens / 1000) * costs['output_cost_per_1k_tokens']
    
    return input_cost + output_cost


def get_cheapest_model_for_task(task_type: str = "analysis") -> str:
    """
    Get the most cost-effective model for a given task type.
    
    Args:
        task_type: Type of task ("analysis", "embedding", "simple")
        
    Returns:
        Model identifier for the most cost-effective option
    """
    
    if task_type == "embedding":
        return "amazon.titan-embed-text-v2:0"
    elif task_type == "simple":
        return "amazon.nova-micro-v1:0"
    elif task_type == "analysis":
        return "amazon.nova-lite-v1:0"
    elif task_type == "complex":
        return "amazon.nova-pro-v1:0"
    else:
        return "amazon.nova-pro-v1:0"  # Default to best quality/cost ratio


def compare_model_costs(input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """
    Compare costs across all available models for given token usage.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Dictionary mapping model names to total costs
    """
    
    costs = {}
    
    for model in BEDROCK_MODEL_COSTS:
        try:
            cost = calculate_bedrock_cost(input_tokens, output_tokens, model)
            costs[model] = cost
        except ValueError:
            continue
    
    return dict(sorted(costs.items(), key=lambda x: x[1]))


def estimate_monthly_cost(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str
) -> Dict[str, float]:
    """
    Estimate monthly costs for consistent usage patterns.
    
    Args:
        requests_per_day: Average requests per day
        avg_input_tokens: Average input tokens per request
        avg_output_tokens: Average output tokens per request
        model: Model identifier
        
    Returns:
        Dictionary with cost breakdown
    """
    
    daily_cost = calculate_bedrock_cost(
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
        'requests_per_day': requests_per_day
    }
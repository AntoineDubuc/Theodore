#!/usr/bin/env python3
"""
Theodore v2 AI Configuration Value Objects

Comprehensive configuration system for AI operations including
model selection, parameters, cost management, and provider-specific options.
"""

from typing import Optional, Dict, Any, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
import json


class AIModelProvider(str, Enum):
    """Supported AI model providers"""
    BEDROCK = "bedrock"
    GEMINI = "gemini" 
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class AIModelType(str, Enum):
    """Types of AI models"""
    TEXT_GENERATION = "text_generation"
    EMBEDDING = "embedding"
    CHAT = "chat"
    COMPLETION = "completion"
    IMAGE_GENERATION = "image_generation"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"


class AIModelSize(str, Enum):
    """AI model size categories"""
    NANO = "nano"        # < 1B parameters
    SMALL = "small"      # 1B - 10B parameters  
    MEDIUM = "medium"    # 10B - 50B parameters
    LARGE = "large"      # 50B - 200B parameters
    XLARGE = "xlarge"    # > 200B parameters


class ResponseFormat(str, Enum):
    """AI response formats"""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"
    STREAMING = "streaming"
    RAW = "raw"


@dataclass
class TokenLimits:
    """Token limits and pricing configuration"""
    max_input_tokens: int = 4096
    max_output_tokens: int = 1024
    max_total_tokens: int = 8192
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    cost_currency: str = "USD"


@dataclass
class RetryConfig:
    """Retry configuration for AI requests"""
    max_attempts: int = 3
    base_delay: float = 1.0
    exponential_backoff: bool = True
    retry_on_errors: List[str] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                "rate_limit_exceeded",
                "service_unavailable", 
                "timeout",
                "internal_error"
            ]


class AIConfig(BaseModel):
    """Comprehensive AI model configuration"""
    
    # Model identification
    provider: AIModelProvider = AIModelProvider.BEDROCK
    model_id: str = Field(..., description="Unique model identifier")
    model_type: AIModelType = AIModelType.TEXT_GENERATION
    model_size: Optional[AIModelSize] = None
    
    # Generation parameters
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=1, le=100000)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=1, le=100)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    
    # Response configuration
    response_format: ResponseFormat = ResponseFormat.TEXT
    stop_sequences: List[str] = Field(default_factory=list)
    seed: Optional[int] = None
    
    # Performance and reliability
    timeout: float = Field(30.0, ge=1.0, le=300.0)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    token_limits: TokenLimits = Field(default_factory=TokenLimits)
    
    # Streaming and callbacks
    stream_response: bool = False
    enable_token_counting: bool = True
    enable_cost_tracking: bool = True
    
    # Provider-specific options
    provider_options: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom parameters
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('model_id cannot be empty')
        return v.strip()
    
    @validator('stop_sequences')
    def validate_stop_sequences(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 stop sequences allowed')
        return v
    
    @validator('provider_options')
    def validate_provider_options(cls, v, values):
        """Validate provider-specific options"""
        provider = values.get('provider')
        
        # Provider-specific validation could be added here
        if provider == AIModelProvider.BEDROCK:
            # Validate Bedrock-specific options
            pass
        elif provider == AIModelProvider.GEMINI:
            # Validate Gemini-specific options
            pass
        
        return v
    
    def get_effective_max_tokens(self) -> int:
        """Get the effective max tokens considering both config and limits"""
        return min(self.max_tokens, self.token_limits.max_output_tokens)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for given token usage"""
        input_cost = input_tokens * self.token_limits.cost_per_input_token
        output_cost = output_tokens * self.token_limits.cost_per_output_token
        return input_cost + output_cost
    
    def to_provider_params(self) -> Dict[str, Any]:
        """Convert to provider-specific parameters"""
        base_params = {
            "temperature": self.temperature,
            "max_tokens": self.get_effective_max_tokens(),
            "top_p": self.top_p,
        }
        
        # Add optional parameters
        if self.top_k is not None:
            base_params["top_k"] = self.top_k
        
        if self.stop_sequences:
            base_params["stop"] = self.stop_sequences
        
        if self.seed is not None:
            base_params["seed"] = self.seed
        
        # Add provider-specific options
        base_params.update(self.provider_options)
        base_params.update(self.custom_parameters)
        
        return base_params
    
    @classmethod
    def for_company_analysis(cls) -> 'AIConfig':
        """Preset configuration for company analysis tasks"""
        return cls(
            model_id="amazon.nova-pro-v1:0",
            provider=AIModelProvider.BEDROCK,
            model_type=AIModelType.TEXT_GENERATION,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=2048,
            top_p=0.8,
            response_format=ResponseFormat.STRUCTURED,
            enable_cost_tracking=True,
            token_limits=TokenLimits(
                max_input_tokens=16384,
                max_output_tokens=2048,
                cost_per_input_token=0.0008,
                cost_per_output_token=0.0032
            )
        )
    
    @classmethod
    def for_embeddings(cls) -> 'AIConfig':
        """Preset configuration for embedding generation"""
        return cls(
            model_id="amazon.titan-embed-text-v1",
            provider=AIModelProvider.BEDROCK,
            model_type=AIModelType.EMBEDDING,
            temperature=0.0,  # Not used for embeddings but set for consistency
            max_tokens=512,
            response_format=ResponseFormat.RAW,
            enable_cost_tracking=True,
            token_limits=TokenLimits(
                max_input_tokens=8192,
                max_output_tokens=1536,  # Embedding dimensions
                cost_per_input_token=0.0001,
                cost_per_output_token=0.0
            )
        )
    
    @classmethod
    def for_fast_completion(cls) -> 'AIConfig':
        """Preset configuration for fast completions"""
        return cls(
            model_id="gpt-4o-mini",
            provider=AIModelProvider.OPENAI,
            model_type=AIModelType.COMPLETION,
            temperature=0.7,
            max_tokens=512,
            timeout=10.0,
            response_format=ResponseFormat.TEXT,
            retry_config=RetryConfig(max_attempts=2),
            token_limits=TokenLimits(
                max_input_tokens=4096,
                max_output_tokens=512,
                cost_per_input_token=0.00015,
                cost_per_output_token=0.0006
            )
        )
    
    @classmethod
    def for_streaming_chat(cls) -> 'AIConfig':
        """Preset configuration for streaming chat"""
        return cls(
            model_id="gemini-2.0-flash-exp",
            provider=AIModelProvider.GEMINI,
            model_type=AIModelType.CHAT,
            temperature=0.8,
            max_tokens=1024,
            stream_response=True,
            response_format=ResponseFormat.STREAMING,
            token_limits=TokenLimits(
                max_input_tokens=32768,
                max_output_tokens=1024,
                cost_per_input_token=0.00075,
                cost_per_output_token=0.003
            )
        )


class EmbeddingConfig(BaseModel):
    """Specialized configuration for embedding models"""
    
    # Model identification
    provider: AIModelProvider = AIModelProvider.BEDROCK
    model_id: str = Field(..., description="Embedding model identifier")
    
    # Embedding parameters
    dimensions: Optional[int] = Field(None, ge=128, le=4096)
    normalize: bool = True
    truncate: bool = True
    
    # Batch processing
    batch_size: int = Field(100, ge=1, le=1000)
    max_text_length: int = Field(8192, ge=1, le=32768)
    
    # Performance
    timeout: float = Field(30.0, ge=1.0, le=300.0)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    
    # Cost tracking
    cost_per_token: float = Field(0.0001, ge=0.0)
    enable_cost_tracking: bool = True
    
    # Provider-specific options
    provider_options: Dict[str, Any] = Field(default_factory=dict)
    
    def estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost for embedding generation"""
        return total_tokens * self.cost_per_token
    
    @classmethod
    def for_company_vectors(cls) -> 'EmbeddingConfig':
        """Preset for company data vectorization"""
        return cls(
            model_id="amazon.titan-embed-text-v1",
            provider=AIModelProvider.BEDROCK,
            dimensions=1536,
            batch_size=50,
            max_text_length=8192,
            cost_per_token=0.0001
        )
    
    @classmethod
    def for_fast_similarity(cls) -> 'EmbeddingConfig':
        """Preset for fast similarity calculations"""
        return cls(
            model_id="text-embedding-3-small",
            provider=AIModelProvider.OPENAI,
            dimensions=1536,
            batch_size=200,
            max_text_length=4096,
            cost_per_token=0.00002
        )


# Model registry for easy access to common configurations
class ModelRegistry:
    """Registry of common model configurations"""
    
    BEDROCK_MODELS = {
        "nova-pro": AIConfig.for_company_analysis(),
        "claude-haiku": AIConfig(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            provider=AIModelProvider.BEDROCK,
            temperature=0.5,
            max_tokens=1024,
            token_limits=TokenLimits(cost_per_input_token=0.00025, cost_per_output_token=0.00125)
        ),
        "titan-embed": EmbeddingConfig.for_company_vectors()
    }
    
    OPENAI_MODELS = {
        "gpt-4o": AIConfig(
            model_id="gpt-4o",
            provider=AIModelProvider.OPENAI,
            temperature=0.7,
            max_tokens=2048,
            token_limits=TokenLimits(cost_per_input_token=0.005, cost_per_output_token=0.015)
        ),
        "gpt-4o-mini": AIConfig.for_fast_completion(),
        "text-embedding-3-large": EmbeddingConfig(
            model_id="text-embedding-3-large",
            provider=AIModelProvider.OPENAI,
            dimensions=3072,
            cost_per_token=0.00013
        )
    }
    
    GEMINI_MODELS = {
        "gemini-2.0-flash": AIConfig.for_streaming_chat(),
        "gemini-pro": AIConfig(
            model_id="gemini-pro",
            provider=AIModelProvider.GEMINI,
            temperature=0.6,
            max_tokens=1024,
            token_limits=TokenLimits(cost_per_input_token=0.00075, cost_per_output_token=0.003)
        )
    }
    
    @classmethod
    def get_model(cls, provider: str, model_name: str) -> Union[AIConfig, EmbeddingConfig]:
        """Get a model configuration by provider and name"""
        provider_models = getattr(cls, f"{provider.upper()}_MODELS", {})
        if model_name not in provider_models:
            raise ValueError(f"Model {model_name} not found for provider {provider}")
        return provider_models[model_name]
    
    @classmethod
    def list_models(cls, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """List available models by provider"""
        if provider:
            provider_models = getattr(cls, f"{provider.upper()}_MODELS", {})
            return {provider: list(provider_models.keys())}
        
        return {
            "bedrock": list(cls.BEDROCK_MODELS.keys()),
            "openai": list(cls.OPENAI_MODELS.keys()),
            "gemini": list(cls.GEMINI_MODELS.keys())
        }


# Utility functions

def create_ai_config(
    model_id: str,
    provider: Union[str, AIModelProvider],
    **kwargs
) -> AIConfig:
    """Create an AI config with simplified parameters"""
    if isinstance(provider, str):
        provider = AIModelProvider(provider)
    
    return AIConfig(
        model_id=model_id,
        provider=provider,
        **kwargs
    )


def create_embedding_config(
    model_id: str,
    provider: Union[str, AIModelProvider],
    **kwargs
) -> EmbeddingConfig:
    """Create an embedding config with simplified parameters"""
    if isinstance(provider, str):
        provider = AIModelProvider(provider)
    
    return EmbeddingConfig(
        model_id=model_id,
        provider=provider,
        **kwargs
    )
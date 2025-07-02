# TICKET-008: AI Provider Port Definition

## Overview
Define the AIProvider port/interface that will be implemented by different AI services (Bedrock, Gemini, OpenAI).

## Acceptance Criteria
- [ ] Define AIProvider interface for text analysis
- [ ] Define EmbeddingProvider interface for vector generation  
- [ ] Support streaming responses for real-time updates
- [ ] Include token counting methods
- [ ] Define standard response formats
- [ ] Support for different model parameters

## Technical Details
- Separate interfaces for analysis vs embeddings
- Include cost estimation methods
- Support both sync and async operations
- Use Union types for flexible model configurations
- Include retry and fallback in interface design

## Testing
- Create mock providers for testing
- Test interface with different response types
- Verify token counting accuracy
- Test streaming response handling

## Estimated Time: 2-3 hours

## Dependencies
- TICKET-001 (for domain models)

## Files to Create
- `v2/src/core/ports/ai_provider.py`
- `v2/src/core/ports/embedding_provider.py`
- `v2/src/core/domain/value_objects/ai_config.py`
- `v2/src/core/domain/value_objects/ai_response.py`
- `v2/tests/unit/ports/test_ai_provider_mock.py`
- `v2/tests/unit/ports/test_embedding_provider_mock.py`

---

# Udemy Tutorial Script: Designing AI Provider Interfaces for Multi-Model Applications

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Flexible AI Provider Interfaces with Clean Architecture"]**

"Welcome to this critical tutorial on designing AI provider interfaces! Today we're going to create the foundation that allows Theodore to work with any AI service - from AWS Bedrock to Google Gemini to OpenAI - without being locked into any single provider.

By the end of this tutorial, you'll understand how to design interfaces that handle streaming responses, cost estimation, token counting, and model configuration. You'll learn patterns that make your applications future-proof as new AI models emerge.

This is architecture that adapts to the AI landscape, not the other way around!"

## Section 1: Understanding AI Provider Complexity (5 minutes)

**[SLIDE 2: The Multi-Provider Challenge]**

"Let's start by understanding why AI provider interfaces are complex. Look at this naive approach:

```python
# ❌ The NAIVE approach - tightly coupled to one provider
import openai

def analyze_company(text):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": text}]
    )
    return response.choices[0].message.content

# Problems:
# 1. Locked into OpenAI forever
# 2. No cost tracking
# 3. No error handling
# 4. Can't A/B test different models
# 5. No streaming support
```

This approach makes your application brittle and expensive!"

**[SLIDE 3: Real-World AI Provider Differences]**

"Here's what we're actually dealing with in production:

```python
# Different API styles:
# OpenAI: openai.chat.completions.create(model="gpt-4", messages=[...])
# Bedrock: bedrock.invoke_model(modelId="anthropic.claude-v2", body=json.dumps(...))
# Gemini: model.generate_content(contents=[...], generation_config=...)

# Different response formats:
# OpenAI: response.choices[0].message.content
# Bedrock: json.loads(response['body'].read())['completion']
# Gemini: response.text

# Different pricing models:
# OpenAI: $0.03/1K tokens input, $0.06/1K tokens output
# Bedrock: $0.008/1K tokens (Claude Haiku)
# Gemini: $0.001/1K tokens (Gemini Flash)

# Different capabilities:
# Some support streaming, others don't
# Different context window sizes
# Different model configurations
```

We need to abstract all this complexity!"

**[SLIDE 4: The Solution - Port Pattern]**

"With the Port/Adapter pattern, we create clean interfaces:

```python
# ✅ The CLEAN approach
async def analyze_company(text: str, provider: AIProvider) -> AnalysisResult:
    config = AnalysisConfig(
        model_name="company_analysis_model",
        temperature=0.2,
        max_tokens=2000
    )
    
    result = await provider.analyze_text(text, config)
    return result

# Benefits:
# 1. Switch providers with dependency injection
# 2. A/B test different models
# 3. Fallback to cheaper models for simple tasks
# 4. Cost tracking across all providers
# 5. Consistent error handling
```

Let's build this!"

## Section 2: Designing the Core AI Provider Interface (10 minutes)

**[SLIDE 5: Interface Design Principles]**

"Before we code, let's establish our design principles:

1. **Separation of Concerns**: Analysis vs embeddings vs streaming
2. **Cost Transparency**: Always track and estimate costs
3. **Configuration Flexibility**: Support different model parameters
4. **Async First**: Built for high-performance applications
5. **Error Resilience**: Graceful handling of provider failures

Now let's create the interfaces:"

**[SLIDE 6: AI Provider Port]**

"Let's start with the main AI provider interface:

```python
# v2/src/core/ports/ai_provider.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional, Union
from v2.src.core.domain.value_objects.ai_config import AnalysisConfig, ModelInfo
from v2.src.core.domain.value_objects.ai_response import AnalysisResult, TokenUsage

class AIProvider(ABC):
    \"\"\"Port interface for AI text analysis providers\"\"\"
    
    @abstractmethod
    async def get_provider_info(self) -> ModelInfo:
        \"\"\"Get information about this provider and available models\"\"\"
        pass
    
    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        \"\"\"Analyze text and return structured results\"\"\"
        pass
    
    @abstractmethod
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        \"\"\"Analyze text with streaming response\"\"\"
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model_name: str) -> int:
        \"\"\"Count tokens for cost estimation\"\"\"
        pass
    
    @abstractmethod
    async def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ) -> float:
        \"\"\"Estimate cost in USD for the given usage\"\"\"
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        \"\"\"Validate the provider is properly configured\"\"\"
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        \"\"\"Check provider health and availability\"\"\"
        pass
```

**[SLIDE 7: Understanding the Interface]**

"Let me explain each method:

- **get_provider_info()**: Returns metadata about available models and capabilities
- **analyze_text()**: Main analysis method with full response
- **analyze_text_streaming()**: For real-time UIs with streaming responses
- **count_tokens()**: Essential for cost prediction
- **estimate_cost()**: Convert token usage to dollar costs
- **validate_configuration()**: Check API keys, endpoints, etc.
- **health_check()**: Monitor provider status for production"

**[SLIDE 8: Embedding Provider Interface]**

"Now let's create a separate interface for embeddings:

```python
# v2/src/core/ports/embedding_provider.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from v2.src.core.domain.value_objects.ai_config import EmbeddingConfig
from v2.src.core.domain.value_objects.ai_response import EmbeddingResult

class EmbeddingProvider(ABC):
    \"\"\"Port interface for text embedding providers\"\"\"
    
    @abstractmethod
    async def get_embedding(
        self,
        text: str,
        config: EmbeddingConfig
    ) -> EmbeddingResult:
        \"\"\"Generate embedding for a single text\"\"\"
        pass
    
    @abstractmethod
    async def get_embeddings_batch(
        self,
        texts: List[str],
        config: EmbeddingConfig
    ) -> List[EmbeddingResult]:
        \"\"\"Generate embeddings for multiple texts efficiently\"\"\"
        pass
    
    @abstractmethod
    async def get_embedding_dimensions(self, model_name: str) -> int:
        \"\"\"Get the vector dimensions for a model\"\"\"
        pass
    
    @abstractmethod
    async def estimate_embedding_cost(
        self,
        text_count: int,
        total_tokens: int,
        model_name: str
    ) -> float:
        \"\"\"Estimate cost for embedding generation\"\"\"
        pass
    
    @abstractmethod
    async def validate_embedding_config(self, config: EmbeddingConfig) -> bool:
        \"\"\"Validate embedding configuration\"\"\"
        pass
```

**[PRACTICAL INSIGHT]** "Notice we separate embeddings from text analysis. This is crucial because:
1. Different providers excel at different tasks
2. Embedding models are often cheaper and faster
3. You might use OpenAI for analysis but Voyage for embeddings"

## Section 3: Creating Value Objects for Configuration (8 minutes)

**[SLIDE 9: Configuration Value Objects]**

"Now let's create robust configuration objects:

```python
# v2/src/core/domain/value_objects/ai_config.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum

class ModelType(str, Enum):
    \"\"\"Types of AI models\"\"\"
    TEXT_ANALYSIS = \"text_analysis\"
    EMBEDDING = \"embedding\"
    CHAT = \"chat\"
    COMPLETION = \"completion\"

class AnalysisConfig(BaseModel):
    \"\"\"Configuration for text analysis\"\"\"
    model_name: str = Field(..., description=\"Model identifier\")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description=\"Creativity level\")
    max_tokens: Optional[int] = Field(None, gt=0, description=\"Maximum output tokens\")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description=\"Nucleus sampling\")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    stop_sequences: Optional[List[str]] = Field(None, description=\"Stop generation tokens\")
    
    # Provider-specific configurations
    provider_config: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
        
    def for_provider(self, provider_name: str) -> Dict[str, Any]:
        \"\"\"Get provider-specific configuration\"\"\"
        base_config = {
            \"temperature\": self.temperature,
            \"max_tokens\": self.max_tokens,
        }
        
        # Add provider-specific settings
        if provider_name in self.provider_config:
            base_config.update(self.provider_config[provider_name])
            
        return {k: v for k, v in base_config.items() if v is not None}

class EmbeddingConfig(BaseModel):
    \"\"\"Configuration for embedding generation\"\"\"
    model_name: str = Field(..., description=\"Embedding model identifier\")
    dimensions: Optional[int] = Field(None, description=\"Output dimensions (if supported)\")
    normalize: bool = Field(True, description=\"Normalize vectors\")
    batch_size: int = Field(10, gt=0, description=\"Batch size for multiple texts\")
    
    # Provider-specific settings
    provider_config: Dict[str, Any] = Field(default_factory=dict)
    
    def for_provider(self, provider_name: str) -> Dict[str, Any]:
        \"\"\"Get provider-specific configuration\"\"\"
        base_config = {
            \"model\": self.model_name,
            \"dimensions\": self.dimensions,
        }
        
        if provider_name in self.provider_config:
            base_config.update(self.provider_config[provider_name])
            
        return {k: v for k, v in base_config.items() if v is not None}

class ModelInfo(BaseModel):
    \"\"\"Information about an AI provider and its models\"\"\"
    provider_name: str = Field(..., description=\"Provider identifier\")
    provider_version: str = Field(..., description=\"API version\")
    available_models: List[str] = Field(..., description=\"Available model names\")
    model_types: Dict[str, ModelType] = Field(..., description=\"Model type mapping\")
    default_models: Dict[ModelType, str] = Field(..., description=\"Default model per type\")
    
    # Capabilities
    supports_streaming: bool = Field(True, description=\"Supports streaming responses\")
    supports_system_prompts: bool = Field(True, description=\"Supports system prompts\")
    supports_function_calling: bool = Field(False, description=\"Supports function calls\")
    
    # Limits
    max_context_tokens: Dict[str, int] = Field(..., description=\"Context limits per model\")
    max_output_tokens: Dict[str, int] = Field(..., description=\"Output limits per model\")
    
    def get_default_model(self, model_type: ModelType) -> str:
        \"\"\"Get the default model for a specific type\"\"\"
        if model_type not in self.default_models:
            raise ValueError(f\"No default model for type {model_type}\")
        return self.default_models[model_type]
    
    def validate_model(self, model_name: str) -> bool:
        \"\"\"Check if a model is available\"\"\"
        return model_name in self.available_models
```

**[SLIDE 10: Configuration Benefits]**

"This configuration system provides:

1. **Type Safety**: Pydantic validates all parameters
2. **Provider Flexibility**: Each provider can add custom settings
3. **Sensible Defaults**: Works out of the box
4. **Range Validation**: Temperature must be 0-2, etc.
5. **Documentation**: Every field is self-documenting"

## Section 4: Designing Response Value Objects (8 minutes)

**[SLIDE 11: Response Objects]**

"Now let's create standardized response objects:

```python
# v2/src/core/domain/value_objects/ai_response.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    \"\"\"Status of AI provider response\"\"\"
    SUCCESS = \"success\"
    PARTIAL = \"partial\"
    ERROR = \"error\"
    RATE_LIMITED = \"rate_limited\"
    QUOTA_EXCEEDED = \"quota_exceeded\"

class TokenUsage(BaseModel):
    \"\"\"Token usage information\"\"\"
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    
    @property
    def efficiency_ratio(self) -> float:
        \"\"\"Ratio of output to input tokens\"\"\"
        if self.prompt_tokens == 0:
            return 0.0
        return self.completion_tokens / self.prompt_tokens

class AnalysisResult(BaseModel):
    \"\"\"Result from text analysis\"\"\"
    content: str = Field(..., description=\"Generated text content\")
    status: ResponseStatus = Field(..., description=\"Response status\")
    token_usage: TokenUsage = Field(..., description=\"Token consumption\")
    
    # Metadata
    model_used: str = Field(..., description=\"Model that generated this result\")
    provider_name: str = Field(..., description=\"Provider that handled the request\")
    request_id: Optional[str] = Field(None, description=\"Provider request ID\")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(None, description=\"Estimated cost in USD\")
    
    # Provider-specific data
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    finish_reason: Optional[str] = Field(None, description=\"Why generation stopped\")
    
    def is_complete(self) -> bool:
        \"\"\"Check if the response is complete\"\"\"
        return self.status == ResponseStatus.SUCCESS and self.finish_reason != \"length\"
    
    def cost_per_token(self) -> float:
        \"\"\"Calculate cost per token\"\"\"
        if not self.estimated_cost or self.token_usage.total_tokens == 0:
            return 0.0
        return self.estimated_cost / self.token_usage.total_tokens

class EmbeddingResult(BaseModel):
    \"\"\"Result from embedding generation\"\"\"
    embedding: List[float] = Field(..., description=\"Embedding vector\")
    dimensions: int = Field(..., gt=0, description=\"Vector dimensions\")
    model_used: str = Field(..., description=\"Embedding model\")
    provider_name: str = Field(..., description=\"Provider name\")
    
    # Usage tracking
    token_count: int = Field(..., ge=0, description=\"Tokens processed\")
    estimated_cost: Optional[float] = Field(None, description=\"Cost in USD\")
    
    # Metadata
    text_length: int = Field(..., ge=0, description=\"Original text length\")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None)
    
    def magnitude(self) -> float:
        \"\"\"Calculate vector magnitude\"\"\"
        return sum(x**2 for x in self.embedding) ** 0.5
    
    def is_normalized(self) -> bool:
        \"\"\"Check if vector is normalized\"\"\"
        mag = self.magnitude()
        return abs(mag - 1.0) < 1e-6

class AnalysisError(BaseModel):
    \"\"\"Error information from AI provider\"\"\"
    error_type: str = Field(..., description=\"Error category\")
    error_message: str = Field(..., description=\"Human-readable error\")
    error_code: Optional[str] = Field(None, description=\"Provider error code\")
    retryable: bool = Field(False, description=\"Whether the request can be retried\")
    retry_after: Optional[int] = Field(None, description=\"Seconds to wait before retry\")
    provider_name: str = Field(..., description=\"Provider that raised the error\")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**[SLIDE 12: Response Design Benefits]**

"Our response objects provide:

1. **Comprehensive Tracking**: Tokens, costs, timing, and metadata
2. **Error Handling**: Structured error information with retry guidance
3. **Quality Metrics**: Confidence scores and completion status
4. **Provider Agnostic**: Same format regardless of underlying provider
5. **Analytics Ready**: Rich data for performance analysis"

## Section 5: Building Mock Implementations for Testing (10 minutes)

**[SLIDE 13: Mock AI Provider]**

"Testing AI applications is challenging and expensive. Let's create comprehensive mocks:

```python
# v2/tests/unit/ports/test_ai_provider_mock.py

import pytest
from typing import AsyncIterator, Dict, Any
import asyncio
from datetime import datetime

class MockAIProvider(AIProvider):
    \"\"\"Mock AI provider for testing\"\"\"
    
    def __init__(self, 
                 simulate_latency: bool = False,
                 simulate_errors: bool = False,
                 cost_per_token: float = 0.001):
        self.simulate_latency = simulate_latency
        self.simulate_errors = simulate_errors
        self.cost_per_token = cost_per_token
        self.request_count = 0
        self.total_tokens_used = 0
        
        # Pre-defined responses for testing
        self.responses = {
            \"company_analysis\": \"\"\"
            Based on the provided information, this company appears to be a B2B SaaS provider 
            focused on payment processing solutions. Key insights:
            
            1. Business Model: Transaction-based revenue with subscription components
            2. Market Position: Competing with established players like Stripe and Square
            3. Technical Sophistication: High-level API-first architecture
            4. Growth Stage: Series B funding stage with rapid customer acquisition
            \"\"\".strip(),
            
            \"industry_classification\": \"Financial Technology (FinTech) - Payment Processing\",
            
            \"competitor_analysis\": \"\"\"
            Direct competitors include:
            1. Stripe - Similar developer-first approach
            2. Square - Focus on SMB market
            3. Adyen - Enterprise-focused platform
            4. PayPal - Established market leader
            \"\"\".strip()
        }
    
    async def get_provider_info(self) -> ModelInfo:
        \"\"\"Return mock provider information\"\"\"
        return ModelInfo(
            provider_name=\"MockProvider\",
            provider_version=\"1.0.0\",
            available_models=[\"mock-analysis-v1\", \"mock-fast-v1\", \"mock-premium-v1\"],
            model_types={
                \"mock-analysis-v1\": ModelType.TEXT_ANALYSIS,
                \"mock-fast-v1\": ModelType.TEXT_ANALYSIS,
                \"mock-premium-v1\": ModelType.TEXT_ANALYSIS
            },
            default_models={
                ModelType.TEXT_ANALYSIS: \"mock-analysis-v1\"
            },
            supports_streaming=True,
            supports_system_prompts=True,
            supports_function_calling=False,
            max_context_tokens={
                \"mock-analysis-v1\": 128000,
                \"mock-fast-v1\": 32000,
                \"mock-premium-v1\": 200000
            },
            max_output_tokens={
                \"mock-analysis-v1\": 4096,
                \"mock-fast-v1\": 1024,
                \"mock-premium-v1\": 8192
            }
        )
    
    async def analyze_text(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        \"\"\"Mock text analysis with realistic behavior\"\"\"
        
        self.request_count += 1
        
        # Simulate latency
        if self.simulate_latency:
            await asyncio.sleep(0.1)  # 100ms latency
        
        # Simulate errors occasionally
        if self.simulate_errors and self.request_count % 10 == 0:
            raise Exception(\"Mock provider error - simulated failure\")
        
        # Generate mock response based on content
        if \"company\" in text.lower() and \"analysis\" in text.lower():
            content = self.responses[\"company_analysis\"]
        elif \"industry\" in text.lower():
            content = self.responses[\"industry_classification\"]
        elif \"competitor\" in text.lower():
            content = self.responses[\"competitor_analysis\"]
        else:
            content = f\"Mock analysis of: {text[:100]}...\nGenerated by {config.model_name}\"
        
        # Calculate realistic token usage
        prompt_tokens = len(text.split()) + (len(system_prompt.split()) if system_prompt else 0)
        completion_tokens = len(content.split())
        total_tokens = prompt_tokens + completion_tokens
        
        self.total_tokens_used += total_tokens
        
        return AnalysisResult(
            content=content,
            status=ResponseStatus.SUCCESS,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            ),
            model_used=config.model_name,
            provider_name=\"MockProvider\",
            request_id=f\"mock_req_{self.request_count}\",
            estimated_cost=total_tokens * self.cost_per_token,
            confidence_score=0.85,
            finish_reason=\"stop\"
        )
    
    async def analyze_text_streaming(
        self,
        text: str,
        config: AnalysisConfig,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        \"\"\"Mock streaming response\"\"\"
        
        # Get the full response first
        result = await self.analyze_text(text, config, system_prompt)
        words = result.content.split()
        
        # Stream it word by word
        for word in words:
            if self.simulate_latency:
                await asyncio.sleep(0.01)  # 10ms per word
            yield f\"{word} \"
        
        # Final newline
        yield \"\\n\"
    
    async def count_tokens(self, text: str, model_name: str) -> int:
        \"\"\"Mock token counting (simplified word-based)\"\"\"
        # Simple approximation: 1 token ≈ 0.75 words
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    async def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str
    ) -> float:
        \"\"\"Mock cost estimation\"\"\"
        # Different pricing for different models
        pricing = {
            \"mock-fast-v1\": 0.0005,      # Cheap model
            \"mock-analysis-v1\": 0.001,   # Standard model
            \"mock-premium-v1\": 0.003     # Premium model
        }
        
        rate = pricing.get(model_name, 0.001)
        return (input_tokens + output_tokens) * rate
    
    async def validate_configuration(self) -> bool:
        \"\"\"Mock validation - always succeeds\"\"\"
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        \"\"\"Mock health check\"\"\"
        return {
            \"status\": \"healthy\",
            \"requests_processed\": self.request_count,
            \"total_tokens_used\": self.total_tokens_used,
            \"average_latency_ms\": 100 if self.simulate_latency else 10,
            \"error_rate\": 0.1 if self.simulate_errors else 0.0,
            \"last_check\": datetime.utcnow().isoformat()
        }

# Test cases
class TestMockAIProvider:
    
    @pytest.mark.asyncio
    async def test_basic_analysis(self):
        \"\"\"Test basic text analysis\"\"\"
        provider = MockAIProvider()
        
        config = AnalysisConfig(
            model_name=\"mock-analysis-v1\",
            temperature=0.7
        )
        
        result = await provider.analyze_text(
            \"Analyze this company: Stripe Inc.\",
            config
        )
        
        assert result.status == ResponseStatus.SUCCESS
        assert \"B2B SaaS\" in result.content
        assert result.token_usage.total_tokens > 0
        assert result.estimated_cost > 0
    
    @pytest.mark.asyncio
    async def test_streaming_response(self):
        \"\"\"Test streaming analysis\"\"\"
        provider = MockAIProvider()
        
        config = AnalysisConfig(model_name=\"mock-fast-v1\")
        
        chunks = []
        async for chunk in provider.analyze_text_streaming(
            \"Quick analysis please\",
            config
        ):
            chunks.append(chunk)
        
        full_response = \"\".join(chunks)
        assert len(chunks) > 1  # Multiple chunks
        assert \"Mock analysis\" in full_response
    
    @pytest.mark.asyncio
    async def test_error_simulation(self):
        \"\"\"Test error handling\"\"\"
        provider = MockAIProvider(simulate_errors=True)
        
        config = AnalysisConfig(model_name=\"mock-analysis-v1\")
        
        # First 9 requests should succeed
        for i in range(9):
            result = await provider.analyze_text(\"test\", config)
            assert result.status == ResponseStatus.SUCCESS
        
        # 10th request should fail
        with pytest.raises(Exception, match=\"Mock provider error\"):
            await provider.analyze_text(\"test\", config)
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self):
        \"\"\"Test cost tracking\"\"\"
        provider = MockAIProvider(cost_per_token=0.002)
        
        config = AnalysisConfig(model_name=\"mock-premium-v1\")
        
        result = await provider.analyze_text(
            \"Short text\",
            config
        )
        
        expected_cost = result.token_usage.total_tokens * 0.003  # Premium pricing
        assert abs(result.estimated_cost - expected_cost) < 0.001
    
    @pytest.mark.asyncio
    async def test_provider_info(self):
        \"\"\"Test provider metadata\"\"\"
        provider = MockAIProvider()
        
        info = await provider.get_provider_info()
        
        assert info.provider_name == \"MockProvider\"
        assert \"mock-analysis-v1\" in info.available_models
        assert info.supports_streaming is True
        assert info.max_context_tokens[\"mock-analysis-v1\"] == 128000
```

**[SLIDE 14: Mock Embedding Provider]**

"Let's also create a mock embedding provider:

```python
# v2/tests/unit/ports/test_embedding_provider_mock.py

import numpy as np
from typing import List

class MockEmbeddingProvider(EmbeddingProvider):
    \"\"\"Mock embedding provider for testing\"\"\"
    
    def __init__(self, dimensions: int = 1536, cost_per_token: float = 0.0001):
        self.dimensions = dimensions
        self.cost_per_token = cost_per_token
        self.request_count = 0
        
        # Consistent seed for reproducible tests
        np.random.seed(42)
    
    async def get_embedding(
        self,
        text: str,
        config: EmbeddingConfig
    ) -> EmbeddingResult:
        \"\"\"Generate mock embedding\"\"\"
        self.request_count += 1
        
        # Generate deterministic embedding based on text hash
        text_hash = hash(text) % (2**31)  # Ensure positive
        np.random.seed(text_hash)
        
        # Generate normalized embedding
        embedding = np.random.normal(0, 1, self.dimensions)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize
        
        token_count = len(text.split())
        
        return EmbeddingResult(
            embedding=embedding.tolist(),
            dimensions=self.dimensions,
            model_used=config.model_name,
            provider_name=\"MockEmbeddingProvider\",
            token_count=token_count,
            estimated_cost=token_count * self.cost_per_token,
            text_length=len(text),
            request_id=f\"embed_req_{self.request_count}\"
        )
    
    async def get_embeddings_batch(
        self,
        texts: List[str],
        config: EmbeddingConfig
    ) -> List[EmbeddingResult]:
        \"\"\"Generate batch embeddings\"\"\"
        results = []
        for text in texts:
            result = await self.get_embedding(text, config)
            results.append(result)
        return results
    
    async def get_embedding_dimensions(self, model_name: str) -> int:
        \"\"\"Return embedding dimensions\"\"\"
        return self.dimensions
    
    async def estimate_embedding_cost(
        self,
        text_count: int,
        total_tokens: int,
        model_name: str
    ) -> float:
        \"\"\"Estimate embedding cost\"\"\"
        return total_tokens * self.cost_per_token
    
    async def validate_embedding_config(self, config: EmbeddingConfig) -> bool:
        \"\"\"Validate configuration\"\"\"
        return config.dimensions <= self.dimensions
```

**[TESTING STRATEGY]** "These mocks enable:
1. **Fast Tests**: No API calls, instant results
2. **Deterministic**: Same input always produces same output
3. **Error Simulation**: Test failure scenarios safely
4. **Cost Tracking**: Verify billing calculations
5. **Performance Testing**: Measure without external dependencies"

## Section 6: Advanced Patterns and Production Considerations (8 minutes)

**[SLIDE 15: Provider Composition Patterns]**

"Let's explore advanced patterns for production use:

```python
# Fallback Provider Pattern
class FallbackAIProvider(AIProvider):
    \"\"\"Provider that falls back to alternatives on failure\"\"\"
    
    def __init__(self, primary: AIProvider, fallbacks: List[AIProvider]):
        self.primary = primary
        self.fallbacks = fallbacks
        
    async def analyze_text(self, text: str, config: AnalysisConfig, system_prompt: Optional[str] = None) -> AnalysisResult:
        providers = [self.primary] + self.fallbacks
        
        for i, provider in enumerate(providers):
            try:
                result = await provider.analyze_text(text, config, system_prompt)
                if i > 0:  # Used fallback
                    result.provider_metadata[\"fallback_used\"] = True
                    result.provider_metadata[\"fallback_index\"] = i
                return result
            except Exception as e:
                if i == len(providers) - 1:  # Last provider failed
                    raise
                continue

# Cost-Optimized Provider Pattern
class CostOptimizedProvider(AIProvider):
    \"\"\"Provider that selects models based on cost constraints\"\"\"
    
    def __init__(self, providers: Dict[str, AIProvider], cost_thresholds: Dict[str, float]):
        self.providers = providers  # {\"cheap\": provider1, \"premium\": provider2}
        self.cost_thresholds = cost_thresholds
    
    async def analyze_text(self, text: str, config: AnalysisConfig, system_prompt: Optional[str] = None) -> AnalysisResult:
        # Estimate cost with cheapest provider first
        input_tokens = await self.providers[\"cheap\"].count_tokens(text, config.model_name)
        estimated_cost = await self.providers[\"cheap\"].estimate_cost(input_tokens, 1000, config.model_name)
        
        # Select provider based on cost
        if estimated_cost <= self.cost_thresholds[\"cheap\"]:
            provider = self.providers[\"cheap\"]
        else:
            provider = self.providers[\"premium\"]
        
        return await provider.analyze_text(text, config, system_prompt)

# Rate-Limited Provider Pattern
class RateLimitedProvider(AIProvider):
    \"\"\"Provider with built-in rate limiting\"\"\"
    
    def __init__(self, provider: AIProvider, requests_per_minute: int = 60):
        self.provider = provider
        self.rate_limiter = AsyncRateLimiter(requests_per_minute)
    
    async def analyze_text(self, text: str, config: AnalysisConfig, system_prompt: Optional[str] = None) -> AnalysisResult:
        async with self.rate_limiter:
            return await self.provider.analyze_text(text, config, system_prompt)
```

**[SLIDE 16: Monitoring and Observability]**

"Production AI providers need comprehensive monitoring:

```python
# Instrumented Provider Pattern
from opentelemetry import trace, metrics

class InstrumentedAIProvider(AIProvider):
    \"\"\"Provider with OpenTelemetry instrumentation\"\"\"
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Metrics
        self.request_counter = self.meter.create_counter(
            \"ai_provider_requests\",
            description=\"Number of AI provider requests\"
        )
        self.token_counter = self.meter.create_counter(
            \"ai_provider_tokens\",
            description=\"Tokens consumed by AI provider\"
        )
        self.cost_counter = self.meter.create_counter(
            \"ai_provider_cost\",
            description=\"Cost incurred by AI provider\"
        )
        self.latency_histogram = self.meter.create_histogram(
            \"ai_provider_latency\",
            description=\"AI provider response latency\"
        )
    
    async def analyze_text(self, text: str, config: AnalysisConfig, system_prompt: Optional[str] = None) -> AnalysisResult:
        with self.tracer.start_as_current_span(
            \"ai_provider_analyze\",
            attributes={
                \"provider\": self.provider.__class__.__name__,
                \"model\": config.model_name,
                \"text_length\": len(text)
            }
        ) as span:
            
            start_time = time.time()
            
            try:
                result = await self.provider.analyze_text(text, config, system_prompt)
                
                # Record success metrics
                self.request_counter.add(1, {
                    \"provider\": result.provider_name,
                    \"model\": result.model_used,
                    \"status\": \"success\"
                })
                
                self.token_counter.add(result.token_usage.total_tokens, {
                    \"provider\": result.provider_name,
                    \"model\": result.model_used
                })
                
                if result.estimated_cost:
                    self.cost_counter.add(result.estimated_cost, {
                        \"provider\": result.provider_name,
                        \"model\": result.model_used
                    })
                
                # Add span attributes
                span.set_attributes({
                    \"tokens.prompt\": result.token_usage.prompt_tokens,
                    \"tokens.completion\": result.token_usage.completion_tokens,
                    \"tokens.total\": result.token_usage.total_tokens,
                    \"cost.estimated\": result.estimated_cost or 0,
                    \"model.used\": result.model_used
                })
                
                return result
                
            except Exception as e:
                # Record error metrics
                self.request_counter.add(1, {
                    \"provider\": self.provider.__class__.__name__,
                    \"status\": \"error\"
                })
                
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            finally:
                latency = time.time() - start_time
                self.latency_histogram.record(latency, {
                    \"provider\": self.provider.__class__.__name__
                })
                span.set_attribute(\"latency_seconds\", latency)
```

**[SLIDE 17: Configuration Management]**

"Dynamic configuration for different environments:

```python
# Configuration-driven provider selection
class ConfigurableProviderFactory:
    \"\"\"Factory for creating providers based on configuration\"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def create_analysis_provider(self) -> AIProvider:
        \"\"\"Create an AI provider based on configuration\"\"\"
        provider_config = self.config.get(\"ai_providers\", {})
        
        # Create base providers
        providers = {}
        for name, config in provider_config.items():
            if config.get(\"enabled\", False):
                providers[name] = self._create_provider(name, config)
        
        if not providers:
            raise ValueError(\"No AI providers configured\")
        
        # Apply patterns based on configuration
        primary_provider = providers[self.config.get(\"primary_provider\", list(providers.keys())[0])]
        
        # Add fallbacks if configured
        if self.config.get(\"enable_fallbacks\", False):
            fallback_names = self.config.get(\"fallback_providers\", [])
            fallbacks = [providers[name] for name in fallback_names if name in providers]
            if fallbacks:
                primary_provider = FallbackAIProvider(primary_provider, fallbacks)
        
        # Add rate limiting if configured
        if \"rate_limit\" in self.config:
            primary_provider = RateLimitedProvider(
                primary_provider, 
                self.config[\"rate_limit\"][\"requests_per_minute\"]
            )
        
        # Add monitoring if configured
        if self.config.get(\"enable_monitoring\", False):
            primary_provider = InstrumentedAIProvider(primary_provider)
        
        return primary_provider
    
    def _create_provider(self, name: str, config: Dict[str, Any]) -> AIProvider:
        \"\"\"Create a specific provider implementation\"\"\"
        provider_type = config[\"type\"]
        
        if provider_type == \"bedrock\":
            return BedrockProvider(
                region=config.get(\"region\", \"us-east-1\"),
                model_id=config.get(\"model_id\"),
                **config.get(\"extra_params\", {})
            )
        elif provider_type == \"openai\":
            return OpenAIProvider(
                api_key=config.get(\"api_key\"),
                base_url=config.get(\"base_url\"),
                **config.get(\"extra_params\", {})
            )
        elif provider_type == \"gemini\": 
            return GeminiProvider(
                api_key=config.get(\"api_key\"),
                **config.get(\"extra_params\", {})
            )
        else:
            raise ValueError(f\"Unknown provider type: {provider_type}\")

# Example configuration
config = {
    \"primary_provider\": \"bedrock\",
    \"enable_fallbacks\": True,
    \"fallback_providers\": [\"openai\", \"gemini\"],
    \"enable_monitoring\": True,
    \"rate_limit\": {
        \"requests_per_minute\": 100
    },
    \"ai_providers\": {
        \"bedrock\": {
            \"enabled\": True,
            \"type\": \"bedrock\",
            \"region\": \"us-west-2\",
            \"model_id\": \"anthropic.claude-v2\"
        },
        \"openai\": {
            \"enabled\": True,
            \"type\": \"openai\",
            \"api_key\": \"${OPENAI_API_KEY}\"
        },
        \"gemini\": {
            \"enabled\": True,
            \"type\": \"gemini\",
            \"api_key\": \"${GEMINI_API_KEY}\"
        }
    }
}
```

## Section 7: Integration Testing Strategies (5 minutes)

**[SLIDE 18: Integration Test Patterns]**

"Testing AI providers requires special strategies:

```python
# Integration test with real providers (use sparingly)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_provider_integration():
    \"\"\"Test with real provider - use environment variables\"\"\"
    api_key = os.getenv(\"TEST_OPENAI_API_KEY\")
    if not api_key:
        pytest.skip(\"No test API key available\")
    
    provider = OpenAIProvider(api_key=api_key)
    
    config = AnalysisConfig(
        model_name=\"gpt-3.5-turbo\",
        temperature=0.1,
        max_tokens=100
    )
    
    result = await provider.analyze_text(
        \"This is a test. Please respond with 'Test successful'.\",
        config
    )
    
    assert result.status == ResponseStatus.SUCCESS
    assert \"test successful\" in result.content.lower()
    assert result.token_usage.total_tokens > 0

# Contract testing
@pytest.mark.parametrize(\"provider_class\", [
    MockAIProvider,
    # Add real providers when available
])
@pytest.mark.asyncio
async def test_provider_contract(provider_class):
    \"\"\"Test all providers implement the contract correctly\"\"\"
    provider = provider_class()
    
    # Test required methods exist
    assert hasattr(provider, \"analyze_text\")
    assert hasattr(provider, \"count_tokens\")
    assert hasattr(provider, \"estimate_cost\")
    
    # Test provider info
    info = await provider.get_provider_info()
    assert isinstance(info, ModelInfo)
    assert len(info.available_models) > 0
    
    # Test basic analysis
    config = AnalysisConfig(
        model_name=info.available_models[0],
        temperature=0.5
    )
    
    result = await provider.analyze_text(\"Test\", config)
    assert isinstance(result, AnalysisResult)
    assert result.content
    assert result.token_usage.total_tokens > 0
```

**[PERFORMANCE TESTING]** "For production, also test:
1. **Latency**: Response times under load
2. **Cost**: Actual vs estimated costs
3. **Rate Limits**: Behavior when limits are hit
4. **Retries**: Recovery from transient failures"

## Conclusion (3 minutes)

**[SLIDE 19: What We Built]**

"Congratulations! You've built a production-ready AI provider interface system. Let's recap what we accomplished:

✅ **Flexible Interfaces**: Support any AI provider with consistent APIs
✅ **Comprehensive Configuration**: Type-safe, validated configuration objects
✅ **Rich Response Objects**: Full metadata, cost tracking, and error handling
✅ **Advanced Patterns**: Fallbacks, rate limiting, cost optimization
✅ **Production Monitoring**: OpenTelemetry integration for observability
✅ **Testing Strategy**: Mocks, contracts, and integration tests

**[SLIDE 20: Next Steps]**

Your homework:
1. Implement adapters for Bedrock, Gemini, and OpenAI using these interfaces
2. Add function calling support to the interfaces
3. Create a caching layer to reduce costs
4. Build a provider selection algorithm based on task complexity

**[FINAL THOUGHT]**
"Remember, these interfaces are your insurance policy against the rapidly changing AI landscape. As new models emerge, you can adapt without rewriting your application. That's the power of good architecture!

Thank you for joining me in this comprehensive tutorial. If you have questions, leave them in the comments below. Happy coding!"

---

## Instructor Notes:
- Total runtime: ~55 minutes
- Include complete code repository in video description
- Emphasize the importance of mocking for cost control
- Consider follow-up video on implementing specific provider adapters
- Demonstrate async/await patterns correctly in live coding sections
"""
AI response value objects for Theodore.

This module provides comprehensive response objects that capture
all aspects of AI provider responses, from token usage to error
information and quality metrics.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import json


class ResponseStatus(str, Enum):
    """Status of AI provider response"""
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"


class FinishReason(str, Enum):
    """Reason why text generation finished"""
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"
    ERROR = "error"
    TIMEOUT = "timeout"


class TokenUsage(BaseModel):
    """Token usage information with detailed breakdown"""
    
    # Core token counts
    prompt_tokens: int = Field(..., ge=0, description="Input tokens used")
    completion_tokens: int = Field(..., ge=0, description="Output tokens generated")
    total_tokens: int = Field(..., ge=0, description="Total tokens consumed")
    
    # Additional breakdowns (optional)
    system_tokens: Optional[int] = Field(None, ge=0, description="System prompt tokens")
    function_tokens: Optional[int] = Field(None, ge=0, description="Function definition tokens")
    cached_tokens: Optional[int] = Field(None, ge=0, description="Cached tokens (if supported)")
    
    @field_validator('total_tokens')
    @classmethod
    def validate_total_tokens(cls, v, info):
        """Validate that total equals prompt + completion"""
        data = info.data if hasattr(info, 'data') else {}
        prompt = data.get('prompt_tokens', 0)
        completion = data.get('completion_tokens', 0)
        
        expected_total = prompt + completion
        if v != expected_total:
            # Allow for small discrepancies due to provider differences
            if abs(v - expected_total) > 10:
                raise ValueError(f"Total tokens ({v}) should equal prompt ({prompt}) + completion ({completion})")
        
        return v
    
    @property
    def efficiency_ratio(self) -> float:
        """Ratio of output to input tokens"""
        if self.prompt_tokens == 0:
            return 0.0
        return self.completion_tokens / self.prompt_tokens
    
    @property
    def compression_ratio(self) -> float:
        """How much the input was compressed (lower is more compressed)"""
        if self.completion_tokens == 0:
            return float('inf')
        return self.prompt_tokens / self.completion_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "system_tokens": self.system_tokens,
            "function_tokens": self.function_tokens,
            "cached_tokens": self.cached_tokens,
            "efficiency_ratio": self.efficiency_ratio,
            "compression_ratio": self.compression_ratio
        }


class AnalysisResult(BaseModel):
    """Result from text analysis operations"""
    
    # Core response data
    content: str = Field(..., description="Generated text content")
    status: ResponseStatus = Field(..., description="Response status")
    token_usage: TokenUsage = Field(..., description="Token consumption details")
    
    # Metadata
    model_used: str = Field(..., description="Model that generated this result")
    provider_name: str = Field(..., description="Provider that handled the request")
    request_id: Optional[str] = Field(None, description="Provider request ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(None, ge=0.0, description="Estimated cost in USD")
    
    # Quality and completion info
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Response confidence")
    finish_reason: Optional[FinishReason] = Field(None, description="Why generation stopped")
    
    # Provider-specific data
    provider_metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific info")
    
    # Processing metrics
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time in seconds")
    queue_time: Optional[float] = Field(None, ge=0.0, description="Time spent in queue")
    
    # Content analysis
    language_detected: Optional[str] = Field(None, description="Detected language")
    content_length: int = Field(0, ge=0, description="Length of generated content")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate content length if not provided
        if self.content_length == 0:
            self.content_length = len(self.content)
    
    def is_complete(self) -> bool:
        """Check if the response is complete"""
        return (
            self.status == ResponseStatus.SUCCESS and 
            self.finish_reason not in [FinishReason.LENGTH, FinishReason.ERROR, FinishReason.TIMEOUT]
        )
    
    def is_successful(self) -> bool:
        """Check if the response was successful"""
        return self.status in [ResponseStatus.SUCCESS, ResponseStatus.PARTIAL]
    
    def cost_per_token(self) -> float:
        """Calculate cost per token"""
        if not self.estimated_cost or self.token_usage.total_tokens == 0:
            return 0.0
        return self.estimated_cost / self.token_usage.total_tokens
    
    def words_per_token(self) -> float:
        """Estimate words per token in the output"""
        if self.token_usage.completion_tokens == 0:
            return 0.0
        word_count = len(self.content.split())
        return word_count / self.token_usage.completion_tokens
    
    def extract_json(self) -> Optional[Dict[str, Any]]:
        """Extract JSON from content if present"""
        try:
            # Try to parse the entire content as JSON
            return json.loads(self.content)
        except json.JSONDecodeError:
            # Try to find JSON blocks in the content
            import re
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, self.content, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            # Try to find any JSON-like structure
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, self.content)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            return None
    
    def get_content_preview(self, max_length: int = 200) -> str:
        """Get a preview of the content"""
        if len(self.content) <= max_length:
            return self.content
        
        preview = self.content[:max_length]
        # Try to break at a word boundary
        last_space = preview.rfind(' ')
        if last_space > max_length * 0.8:  # Only if we don't lose too much
            preview = preview[:last_space]
        
        return preview + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "content_preview": self.get_content_preview(),
            "status": self.status,
            "token_usage": self.token_usage.to_dict(),
            "model_used": self.model_used,
            "provider_name": self.provider_name,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "estimated_cost": self.estimated_cost,
            "confidence_score": self.confidence_score,
            "finish_reason": self.finish_reason,
            "processing_time": self.processing_time,
            "queue_time": self.queue_time,
            "language_detected": self.language_detected,
            "content_length": self.content_length,
            "is_complete": self.is_complete(),
            "is_successful": self.is_successful(),
            "cost_per_token": self.cost_per_token(),
            "words_per_token": self.words_per_token()
        }


class EmbeddingResult(BaseModel):
    """Result from embedding generation"""
    
    # Core embedding data
    embedding: List[float] = Field(..., description="Embedding vector")
    dimensions: int = Field(..., gt=0, description="Vector dimensions")
    
    # Model information
    model_used: str = Field(..., description="Embedding model used")
    provider_name: str = Field(..., description="Provider name")
    
    # Usage tracking
    token_count: int = Field(..., ge=0, description="Tokens processed")
    estimated_cost: Optional[float] = Field(None, ge=0.0, description="Cost in USD")
    
    # Input metadata
    text_length: int = Field(..., ge=0, description="Original text length")
    text_hash: Optional[str] = Field(None, description="Hash of input text for deduplication")
    
    # Processing metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    request_id: Optional[str] = Field(None, description="Provider request ID")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time in seconds")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Embedding confidence")
    
    # Provider-specific data
    provider_metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific info")
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding_dimensions(cls, v, info):
        """Validate embedding dimensions match declared dimensions"""
        data = info.data if hasattr(info, 'data') else {}
        expected_dims = data.get('dimensions')
        
        if expected_dims and len(v) != expected_dims:
            raise ValueError(f"Embedding has {len(v)} dimensions, expected {expected_dims}")
        
        return v
    
    @field_validator('dimensions')
    @classmethod
    def validate_dimensions_match_embedding(cls, v, info):
        """Validate dimensions match embedding length"""
        data = info.data if hasattr(info, 'data') else {}
        embedding = data.get('embedding', [])
        
        if len(embedding) != v:
            raise ValueError(f"Dimensions ({v}) don't match embedding length ({len(embedding)})")
        
        return v
    
    def magnitude(self) -> float:
        """Calculate vector magnitude (L2 norm)"""
        return sum(x**2 for x in self.embedding) ** 0.5
    
    def is_normalized(self, tolerance: float = 1e-6) -> bool:
        """Check if vector is normalized"""
        mag = self.magnitude()
        return abs(mag - 1.0) < tolerance
    
    def normalize(self) -> 'EmbeddingResult':
        """Return a normalized version of this embedding"""
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize zero vector")
        
        normalized_embedding = [x / mag for x in self.embedding]
        
        # Create a copy with normalized embedding
        return self.model_copy(update={"embedding": normalized_embedding})
    
    def dot_product(self, other: 'EmbeddingResult') -> float:
        """Calculate dot product with another embedding"""
        if self.dimensions != other.dimensions:
            raise ValueError(f"Dimension mismatch: {self.dimensions} vs {other.dimensions}")
        
        return sum(a * b for a, b in zip(self.embedding, other.embedding))
    
    def cosine_similarity(self, other: 'EmbeddingResult') -> float:
        """Calculate cosine similarity with another embedding"""
        dot_prod = self.dot_product(other)
        mag_product = self.magnitude() * other.magnitude()
        
        if mag_product == 0:
            return 0.0
        
        return dot_prod / mag_product
    
    def euclidean_distance(self, other: 'EmbeddingResult') -> float:
        """Calculate Euclidean distance to another embedding"""
        if self.dimensions != other.dimensions:
            raise ValueError(f"Dimension mismatch: {self.dimensions} vs {other.dimensions}")
        
        return sum((a - b)**2 for a, b in zip(self.embedding, other.embedding)) ** 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "dimensions": self.dimensions,
            "model_used": self.model_used,
            "provider_name": self.provider_name,
            "token_count": self.token_count,
            "estimated_cost": self.estimated_cost,
            "text_length": self.text_length,
            "text_hash": self.text_hash,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score,
            "magnitude": self.magnitude(),
            "is_normalized": self.is_normalized(),
            "provider_metadata": self.provider_metadata
        }
    
    def to_vector_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including the embedding vector"""
        result = self.to_dict()
        result["embedding"] = self.embedding
        return result


class StreamingChunk(BaseModel):
    """Individual chunk from a streaming response"""
    
    # Chunk data
    content: str = Field(..., description="Content of this chunk")
    chunk_index: int = Field(..., ge=0, description="Index of this chunk")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Chunk timestamp")
    
    # Token information (if available)
    tokens_in_chunk: Optional[int] = Field(None, ge=0, description="Tokens in this chunk")
    cumulative_tokens: Optional[int] = Field(None, ge=0, description="Total tokens so far")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Chunk confidence")
    
    # Final chunk information
    final_token_usage: Optional[TokenUsage] = Field(None, description="Final token usage (final chunk only)")
    finish_reason: Optional[FinishReason] = Field(None, description="Finish reason (final chunk only)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "chunk_index": self.chunk_index,
            "is_final": self.is_final,
            "timestamp": self.timestamp.isoformat(),
            "tokens_in_chunk": self.tokens_in_chunk,
            "cumulative_tokens": self.cumulative_tokens,
            "confidence_score": self.confidence_score,
            "final_token_usage": self.final_token_usage.to_dict() if self.final_token_usage else None,
            "finish_reason": self.finish_reason
        }


class AnalysisError(BaseModel):
    """Error information from AI provider"""
    
    # Error categorization
    error_type: str = Field(..., description="Error category")
    error_message: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(None, description="Provider-specific error code")
    
    # Retry information
    retryable: bool = Field(False, description="Whether the request can be retried")
    retry_after: Optional[int] = Field(None, ge=0, description="Seconds to wait before retry")
    suggested_action: Optional[str] = Field(None, description="Suggested action to resolve error")
    
    # Context
    provider_name: str = Field(..., description="Provider that raised the error")
    model_name: Optional[str] = Field(None, description="Model being used when error occurred")
    request_id: Optional[str] = Field(None, description="Request ID if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    # Technical details
    http_status_code: Optional[int] = Field(None, description="HTTP status code")
    raw_error: Optional[Dict[str, Any]] = Field(None, description="Raw error from provider")
    
    # User context
    user_id: Optional[str] = Field(None, description="User ID if available")
    session_id: Optional[str] = Field(None, description="Session ID if available")
    
    def is_client_error(self) -> bool:
        """Check if this is a client-side error (4xx)"""
        return self.http_status_code is not None and 400 <= self.http_status_code < 500
    
    def is_server_error(self) -> bool:
        """Check if this is a server-side error (5xx)"""
        return self.http_status_code is not None and 500 <= self.http_status_code < 600
    
    def is_rate_limit_error(self) -> bool:
        """Check if this is a rate limiting error"""
        return (
            self.http_status_code == 429 or
            "rate" in self.error_type.lower() or
            "rate" in self.error_message.lower()
        )
    
    def is_quota_error(self) -> bool:
        """Check if this is a quota exceeded error"""
        return (
            "quota" in self.error_type.lower() or
            "quota" in self.error_message.lower() or
            "limit" in self.error_message.lower()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and serialization"""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "suggested_action": self.suggested_action,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "http_status_code": self.http_status_code,
            "is_client_error": self.is_client_error(),
            "is_server_error": self.is_server_error(),
            "is_rate_limit_error": self.is_rate_limit_error(),
            "is_quota_error": self.is_quota_error(),
            "user_id": self.user_id,
            "session_id": self.session_id
        }


class BatchResult(BaseModel):
    """Result from batch processing multiple requests"""
    
    # Batch metadata
    batch_id: str = Field(..., description="Unique batch identifier")
    total_requests: int = Field(..., gt=0, description="Total number of requests")
    successful_requests: int = Field(..., ge=0, description="Number of successful requests")
    failed_requests: int = Field(..., ge=0, description="Number of failed requests")
    
    # Results
    results: List[Union[AnalysisResult, EmbeddingResult]] = Field(..., description="Individual results")
    errors: List[AnalysisError] = Field(default_factory=list, description="Errors encountered")
    
    # Processing metrics
    started_at: datetime = Field(..., description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")
    total_processing_time: Optional[float] = Field(None, ge=0.0, description="Total processing time")
    
    # Aggregated metrics
    total_tokens_used: int = Field(0, ge=0, description="Total tokens across all requests")
    total_estimated_cost: float = Field(0.0, ge=0.0, description="Total estimated cost")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage"""
        return 1.0 - self.success_rate
    
    @property
    def average_cost_per_request(self) -> float:
        """Calculate average cost per request"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_estimated_cost / self.successful_requests
    
    @property
    def requests_per_second(self) -> float:
        """Calculate processing rate"""
        if not self.total_processing_time or self.total_processing_time == 0:
            return 0.0
        return self.total_requests / self.total_processing_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "batch_id": self.batch_id,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_processing_time": self.total_processing_time,
            "total_tokens_used": self.total_tokens_used,
            "total_estimated_cost": self.total_estimated_cost,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_cost_per_request": self.average_cost_per_request,
            "requests_per_second": self.requests_per_second,
            "errors_count": len(self.errors)
        }
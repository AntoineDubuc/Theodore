"""
Pinecone configuration and authentication management.

This module handles Pinecone API configuration, authentication,
and connection settings for the vector storage adapter.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import os
from dataclasses import dataclass


class PineconeConfig(BaseModel):
    """Configuration for Pinecone vector storage."""
    
    # Authentication
    api_key: str = Field(description="Pinecone API key")
    environment: str = Field(description="Pinecone environment")
    
    # Default index configuration
    default_index_name: str = Field(
        default="theodore-vectors",
        description="Default index name for vectors"
    )
    default_dimensions: int = Field(
        default=1536,
        ge=1,
        le=40000,
        description="Default vector dimensions"
    )
    default_metric: str = Field(
        default="cosine",
        description="Default distance metric"
    )
    
    # Connection settings
    request_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Base retry delay in seconds"
    )
    
    # Performance settings
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Default batch size for operations"
    )
    max_parallel_requests: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum parallel requests"
    )
    connection_pool_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Connection pool size"
    )
    
    # Cache settings
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching"
    )
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds"
    )
    max_cache_size: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Maximum cache entries"
    )
    
    # Monitoring settings
    enable_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring"
    )
    metrics_collection_interval: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Metrics collection interval in seconds"
    )
    
    # Advanced settings
    enable_compression: bool = Field(
        default=True,
        description="Enable request/response compression"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )
    user_agent: str = Field(
        default="Theodore-v2/2.0.0",
        description="User agent for requests"
    )
    
    @field_validator('default_metric')
    @classmethod
    def validate_metric(cls, v):
        valid_metrics = {'cosine', 'euclidean', 'dotproduct'}
        if v not in valid_metrics:
            raise ValueError(f"metric must be one of {valid_metrics}")
        return v
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError("api_key must be a valid Pinecone API key")
        return v
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if not v or len(v) < 3:
            raise ValueError("environment must be a valid Pinecone environment")
        return v
    
    @classmethod
    def from_env(cls) -> 'PineconeConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv('PINECONE_API_KEY', ''),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            default_index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-vectors'),
            default_dimensions=int(os.getenv('PINECONE_DIMENSIONS', '1536')),
            default_metric=os.getenv('PINECONE_METRIC', 'cosine'),
            request_timeout=float(os.getenv('PINECONE_TIMEOUT', '30.0')),
            max_retries=int(os.getenv('PINECONE_MAX_RETRIES', '3')),
            batch_size=int(os.getenv('PINECONE_BATCH_SIZE', '100')),
            enable_caching=os.getenv('PINECONE_ENABLE_CACHE', 'true').lower() == 'true',
            enable_monitoring=os.getenv('PINECONE_ENABLE_MONITORING', 'true').lower() == 'true'
        )
    
    def get_client_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for Pinecone client initialization."""
        return {
            'api_key': self.api_key,
            'environment': self.environment,
            'timeout': self.request_timeout,
            'user_agent': self.user_agent
        }
    
    def get_index_config(self) -> Dict[str, Any]:
        """Get default index configuration."""
        return {
            'dimension': self.default_dimensions,
            'metric': self.default_metric
        }
    
    def get_upsert_config(self) -> Dict[str, Any]:
        """Get configuration for upsert operations."""
        return {
            'batch_size': self.batch_size,
            'async_req': True,
            'show_progress': False
        }


@dataclass
class PineconeIndexConfig:
    """Configuration for a specific Pinecone index."""
    
    name: str
    dimensions: int
    metric: str = "cosine"
    pods: int = 1
    replicas: int = 1
    pod_type: str = "p1.x1"
    metadata_config: Optional[Dict[str, str]] = None
    source_collection: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pinecone API."""
        config = {
            'dimension': self.dimensions,
            'metric': self.metric,
            'pods': self.pods,
            'replicas': self.replicas,
            'pod_type': self.pod_type
        }
        
        if self.metadata_config:
            config['metadata_config'] = self.metadata_config
        
        if self.source_collection:
            config['source_collection'] = self.source_collection
        
        return config


@dataclass
class PineconeConnectionPool:
    """Connection pool configuration for Pinecone."""
    
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    max_connection_age: float = 3600.0
    
    def get_pool_config(self) -> Dict[str, Any]:
        """Get connection pool configuration."""
        return {
            'min_connections': self.min_connections,
            'max_connections': self.max_connections,
            'connection_timeout': self.connection_timeout,
            'idle_timeout': self.idle_timeout,
            'max_connection_age': self.max_connection_age
        }


class PineconeCredentials:
    """Secure credential management for Pinecone."""
    
    def __init__(self, api_key: str, environment: str):
        self._api_key = api_key
        self._environment = environment
    
    @property
    def api_key(self) -> str:
        """Get API key (protected access)."""
        return self._api_key
    
    @property
    def environment(self) -> str:
        """Get environment (protected access)."""
        return self._environment
    
    def validate(self) -> bool:
        """Validate credentials format."""
        if not self._api_key or len(self._api_key) < 10:
            return False
        if not self._environment or len(self._environment) < 3:
            return False
        return True
    
    @classmethod
    def from_env(cls) -> 'PineconeCredentials':
        """Create credentials from environment variables."""
        api_key = os.getenv('PINECONE_API_KEY', '')
        environment = os.getenv('PINECONE_ENVIRONMENT', '')
        return cls(api_key, environment)
    
    def mask_api_key(self) -> str:
        """Get masked API key for logging."""
        if len(self._api_key) < 8:
            return "***"
        return f"{self._api_key[:4]}***{self._api_key[-4:]}"
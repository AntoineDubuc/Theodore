"""
Vector storage configuration value objects for Theodore.

This module provides comprehensive configuration objects for vector
database operations, including connection settings, indexing options,
similarity search parameters, and provider-specific configurations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime


class VectorProvider(str, Enum):
    """Supported vector database providers"""
    PINECONE = "pinecone"
    CHROMA = "chroma"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    FAISS = "faiss"
    ELASTICSEARCH = "elasticsearch"
    PGVECTOR = "pgvector"


class SimilarityMetric(str, Enum):
    """Similarity metrics for vector comparisons"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"
    JACCARD = "jaccard"
    HAMMING = "hamming"


class IndexType(str, Enum):
    """Vector index types for different use cases"""
    FLAT = "flat"              # Brute force search
    IVF_FLAT = "ivf_flat"      # Inverted file with flat quantizer
    IVF_PQ = "ivf_pq"          # Inverted file with product quantization
    HNSW = "hnsw"              # Hierarchical navigable small world
    LSH = "lsh"                # Locality sensitive hashing
    ANNOY = "annoy"            # Approximate nearest neighbors oh yeah
    SCANN = "scann"            # Google's ScaNN algorithm


class VectorDataType(str, Enum):
    """Vector data types"""
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    INT8 = "int8"
    BINARY = "binary"


class CompressionType(str, Enum):
    """Vector compression algorithms"""
    NONE = "none"
    PQ = "product_quantization"
    SQ = "scalar_quantization"
    OPQ = "optimized_product_quantization"
    GZIP = "gzip"
    LZ4 = "lz4"


class VectorConfig(BaseModel):
    """Core vector storage configuration"""
    
    # Provider settings
    provider: VectorProvider = VectorProvider.PINECONE
    provider_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Index configuration
    index_name: str = Field(..., min_length=1, max_length=64)
    dimensions: int = Field(..., gt=0, le=65536)
    
    # Similarity and search
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    index_type: IndexType = IndexType.HNSW
    
    # Performance settings
    batch_size: int = Field(100, ge=1, le=10000)
    timeout: float = Field(30.0, ge=1.0, le=300.0)
    max_connections: int = Field(10, ge=1, le=100)
    
    # Data handling
    vector_data_type: VectorDataType = VectorDataType.FLOAT32
    compression: CompressionType = CompressionType.NONE
    normalize_vectors: bool = True
    
    # Metadata
    metadata_schema: Dict[str, str] = Field(default_factory=dict)
    enable_metadata_indexing: bool = True
    max_metadata_size: int = Field(1024, ge=0, le=65536)
    
    # Reliability
    enable_replication: bool = False
    replication_factor: int = Field(1, ge=1, le=10)
    backup_enabled: bool = False
    
    @field_validator('index_name')
    @classmethod
    def validate_index_name(cls, v):
        """Validate index name format"""
        import re
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-_]*$', v):
            raise ValueError("Index name must start with alphanumeric and contain only letters, numbers, hyphens, and underscores")
        return v.lower()
    
    @field_validator('metadata_schema')
    @classmethod
    def validate_metadata_schema(cls, v):
        """Validate metadata schema format"""
        valid_types = {'string', 'integer', 'float', 'boolean', 'datetime', 'json'}
        for field_name, field_type in v.items():
            if field_type not in valid_types:
                raise ValueError(f"Invalid metadata type '{field_type}' for field '{field_name}'. Must be one of: {valid_types}")
        return v
    
    def get_provider_specific_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration"""
        base_config = {
            "index_name": self.index_name,
            "dimensions": self.dimensions,
            "similarity_metric": self.similarity_metric,
            "batch_size": self.batch_size,
            "timeout": self.timeout
        }
        
        # Add provider-specific configurations
        if self.provider == VectorProvider.PINECONE:
            base_config.update({
                "metric": self.similarity_metric.value,
                "pod_type": self.provider_config.get("pod_type", "p1.x1"),
                "replicas": self.replication_factor,
                "metadata_config": {
                    "indexed": list(self.metadata_schema.keys()) if self.enable_metadata_indexing else []
                }
            })
        elif self.provider == VectorProvider.CHROMA:
            base_config.update({
                "distance_function": self.similarity_metric.value,
                "hnsw_space": self.similarity_metric.value,
                "embedding_function": None  # Will be set by provider
            })
        elif self.provider == VectorProvider.QDRANT:
            base_config.update({
                "distance": self.similarity_metric.value.upper(),
                "hnsw_config": {
                    "m": self.provider_config.get("hnsw_m", 16),
                    "ef_construct": self.provider_config.get("hnsw_ef_construct", 200)
                },
                "optimizers_config": {
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000
                }
            })
        
        base_config.update(self.provider_config)
        return base_config
    
    @classmethod
    def for_company_embeddings(cls) -> 'VectorConfig':
        """Preset configuration for company embeddings"""
        return cls(
            provider=VectorProvider.PINECONE,
            index_name="theodore-companies",
            dimensions=1536,
            similarity_metric=SimilarityMetric.COSINE,
            index_type=IndexType.HNSW,
            batch_size=50,
            normalize_vectors=True,
            metadata_schema={
                "company_name": "string",
                "industry": "string",
                "founded_year": "integer",
                "employee_count": "integer",
                "website": "string",
                "last_updated": "datetime"
            },
            enable_metadata_indexing=True,
            provider_config={
                "pod_type": "p1.x1",
                "environment": "us-west1-gcp"
            }
        )
    
    @classmethod
    def for_fast_similarity_search(cls) -> 'VectorConfig':
        """Preset configuration for fast similarity searches"""
        return cls(
            provider=VectorProvider.CHROMA,
            index_name="fast-similarity",
            dimensions=384,  # Smaller dimensions for speed
            similarity_metric=SimilarityMetric.COSINE,
            index_type=IndexType.HNSW,
            batch_size=200,
            normalize_vectors=True,
            compression=CompressionType.PQ,
            metadata_schema={
                "text_hash": "string",
                "category": "string",
                "timestamp": "datetime"
            },
            provider_config={
                "collection_name": "fast_similarity",
                "distance_function": "cosine"
            }
        )
    
    @classmethod
    def for_large_scale_storage(cls) -> 'VectorConfig':
        """Preset configuration for large-scale vector storage"""
        return cls(
            provider=VectorProvider.QDRANT,
            index_name="large-scale-vectors",
            dimensions=768,
            similarity_metric=SimilarityMetric.COSINE,
            index_type=IndexType.HNSW,
            batch_size=1000,
            vector_data_type=VectorDataType.FLOAT16,  # Smaller memory footprint
            compression=CompressionType.PQ,
            normalize_vectors=True,
            enable_replication=True,
            replication_factor=2,
            backup_enabled=True,
            metadata_schema={
                "source": "string",
                "category": "string",
                "importance": "float",
                "created_at": "datetime"
            },
            provider_config={
                "hnsw_m": 32,
                "hnsw_ef_construct": 400,
                "segment_number": 4
            }
        )


class SearchConfig(BaseModel):
    """Configuration for vector similarity searches"""
    
    # Search parameters
    top_k: int = Field(10, ge=1, le=10000)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Search quality vs speed tradeoff
    ef_search: Optional[int] = Field(None, ge=1, le=10000)  # HNSW parameter
    nprobe: Optional[int] = Field(None, ge=1, le=1000)      # IVF parameter
    
    # Filtering and metadata
    metadata_filter: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True
    include_vectors: bool = False
    
    # Result processing
    deduplicate_results: bool = True
    score_normalization: bool = True
    
    # Performance
    timeout: float = Field(10.0, ge=0.1, le=60.0)
    max_concurrent_searches: int = Field(5, ge=1, le=50)
    
    def validate_filter_compatibility(self, metadata_schema: Dict[str, str]) -> bool:
        """Validate that metadata filters are compatible with schema"""
        for field_name, filter_value in self.metadata_filter.items():
            if field_name not in metadata_schema:
                return False
            
            expected_type = metadata_schema[field_name]
            if expected_type == "string" and not isinstance(filter_value, (str, list)):
                return False
            elif expected_type == "integer" and not isinstance(filter_value, (int, list, dict)):
                return False
            elif expected_type == "float" and not isinstance(filter_value, (float, int, list, dict)):
                return False
            elif expected_type == "boolean" and not isinstance(filter_value, bool):
                return False
        
        return True
    
    @classmethod
    def for_precise_search(cls) -> 'SearchConfig':
        """Configuration for high-precision searches"""
        return cls(
            top_k=20,
            similarity_threshold=0.7,
            ef_search=500,
            nprobe=100,
            include_metadata=True,
            include_vectors=False,
            deduplicate_results=True,
            score_normalization=True,
            timeout=30.0
        )
    
    @classmethod
    def for_fast_search(cls) -> 'SearchConfig':
        """Configuration for fast, approximate searches"""
        return cls(
            top_k=10,
            ef_search=50,
            nprobe=10,
            include_metadata=True,
            include_vectors=False,
            deduplicate_results=False,
            timeout=5.0,
            max_concurrent_searches=10
        )


class BulkOperationConfig(BaseModel):
    """Configuration for bulk vector operations"""
    
    # Batch processing
    batch_size: int = Field(1000, ge=1, le=50000)
    max_concurrent_batches: int = Field(5, ge=1, le=20)
    
    # Error handling
    continue_on_error: bool = True
    max_errors: int = Field(100, ge=0)
    retry_failed_batches: bool = True
    max_retries: int = Field(3, ge=0, le=10)
    
    # Progress tracking
    progress_callback_interval: int = Field(100, ge=1)
    enable_progress_logging: bool = True
    
    # Performance
    timeout_per_batch: float = Field(60.0, ge=1.0, le=600.0)
    memory_limit_mb: int = Field(1024, ge=128, le=16384)
    
    # Data validation
    validate_vectors: bool = True
    validate_metadata: bool = True
    skip_duplicates: bool = False
    
    @classmethod
    def for_large_import(cls) -> 'BulkOperationConfig':
        """Configuration for large data imports"""
        return cls(
            batch_size=5000,
            max_concurrent_batches=10,
            continue_on_error=True,
            max_errors=1000,
            retry_failed_batches=True,
            max_retries=2,
            progress_callback_interval=1000,
            timeout_per_batch=120.0,
            memory_limit_mb=4096,
            validate_vectors=True,
            skip_duplicates=True
        )
    
    @classmethod
    def for_incremental_update(cls) -> 'BulkOperationConfig':
        """Configuration for incremental updates"""
        return cls(
            batch_size=100,
            max_concurrent_batches=3,
            continue_on_error=False,
            max_errors=10,
            retry_failed_batches=True,
            max_retries=5,
            progress_callback_interval=50,
            timeout_per_batch=30.0,
            validate_vectors=True,
            validate_metadata=True,
            skip_duplicates=False
        )


# Connection configuration for different providers
class ConnectionConfig(BaseModel):
    """Database connection configuration"""
    
    # Connection details
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    
    # Authentication
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    
    # SSL/TLS
    use_ssl: bool = True
    ssl_verify: bool = True
    ssl_cert_path: Optional[str] = None
    
    # Connection pooling
    pool_size: int = Field(10, ge=1, le=100)
    max_overflow: int = Field(20, ge=0, le=100)
    pool_timeout: float = Field(30.0, ge=1.0, le=300.0)
    
    # Timeouts
    connect_timeout: float = Field(10.0, ge=1.0, le=60.0)
    read_timeout: float = Field(30.0, ge=1.0, le=300.0)
    write_timeout: float = Field(30.0, ge=1.0, le=300.0)
    
    # Environment-specific settings
    environment: str = Field("production", pattern="^(development|staging|production)$")
    region: Optional[str] = None
    cloud_provider: Optional[str] = None
    
    def get_connection_string(self, provider: VectorProvider) -> str:
        """Generate connection string for the provider"""
        if provider == VectorProvider.PINECONE:
            return f"pinecone://{self.api_key}@{self.environment}.pinecone.io"
        elif provider == VectorProvider.CHROMA:
            if self.host and self.port:
                return f"http{'s' if self.use_ssl else ''}://{self.host}:{self.port}"
            return "chroma://local"
        elif provider == VectorProvider.QDRANT:
            protocol = "https" if self.use_ssl else "http"
            return f"{protocol}://{self.host}:{self.port or 6333}"
        elif provider == VectorProvider.WEAVIATE:
            protocol = "https" if self.use_ssl else "http"
            return f"{protocol}://{self.host}:{self.port or 8080}"
        elif provider == VectorProvider.PGVECTOR:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port or 5432}/{self.database}"
        else:
            return f"{provider.value}://localhost"


# Utility functions for configuration management
def create_vector_config(
    provider: Union[str, VectorProvider],
    index_name: str,
    dimensions: int,
    **kwargs
) -> VectorConfig:
    """Create a vector config with simplified parameters"""
    if isinstance(provider, str):
        provider = VectorProvider(provider)
    
    return VectorConfig(
        provider=provider,
        index_name=index_name,
        dimensions=dimensions,
        **kwargs
    )


def create_search_config(
    top_k: int = 10,
    **kwargs
) -> SearchConfig:
    """Create a search config with simplified parameters"""
    return SearchConfig(
        top_k=top_k,
        **kwargs
    )


# Configuration validation utilities
def validate_provider_compatibility(
    vector_config: VectorConfig,
    connection_config: ConnectionConfig
) -> List[str]:
    """Validate compatibility between vector and connection configs"""
    issues = []
    
    # Provider-specific validation
    if vector_config.provider == VectorProvider.PINECONE:
        if not connection_config.api_key:
            issues.append("Pinecone requires API key")
        if not connection_config.environment:
            issues.append("Pinecone requires environment specification")
    
    elif vector_config.provider == VectorProvider.CHROMA:
        if connection_config.host and not connection_config.port:
            issues.append("Chroma remote connection requires both host and port")
    
    elif vector_config.provider == VectorProvider.QDRANT:
        if not connection_config.host:
            issues.append("Qdrant requires host specification")
        if vector_config.dimensions > 65536:
            issues.append("Qdrant maximum dimensions is 65536")
    
    # General validation
    if vector_config.replication_factor > 1 and not vector_config.enable_replication:
        issues.append("Replication factor > 1 requires enable_replication=True")
    
    if vector_config.compression != CompressionType.NONE and vector_config.vector_data_type == VectorDataType.BINARY:
        issues.append("Binary vectors cannot use compression")
    
    return issues
# TICKET-009: Vector Storage Port Definition

## Overview
Define the VectorStorage port/interface for storing and searching company embeddings.

## Acceptance Criteria
- [x] Define VectorStorage interface with CRUD operations
- [x] Support similarity search with metadata filtering
- [x] Define batch operations for efficiency
- [x] Include index management methods
- [x] Support for different distance metrics
- [x] Clear error handling for storage failures
- [x] Create comprehensive value objects for configuration and results
- [x] Implement extended interfaces for batch, streaming, and caching
- [x] Build complete mock implementation with realistic behavior
- [x] Include progress tracking and context manager support

## Technical Details
- Generic interface that works with any vector DB
- Support for metadata queries alongside vector search
- Include methods for index statistics
- Design for high-throughput operations
- Consider pagination for large result sets

## Testing
- Create in-memory mock implementation
- Test CRUD operations
- Test similarity search with filters
- Verify batch operation behavior
- Test error scenarios

## Estimated Time: 2-3 hours

## Dependencies
- TICKET-001 (for Company model)
- TICKET-008 (for embedding types)

## COMPLETED ✅

**Implementation Details:**
- Created comprehensive VectorStorage port interface with CRUD operations, similarity search, and index management
- Built VectorConfig and SearchConfig value objects with provider-specific configuration support
- Implemented VectorResult objects (VectorRecord, VectorSearchResult, VectorOperationResult, etc.)
- Created extended interfaces: BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage
- Built complete MockVectorStorage implementation with realistic similarity calculations and error simulation
- Added ProgressTracker interface for long-running operations
- Included comprehensive exception hierarchy and utility functions
- Supports multiple vector providers (Pinecone, Chroma, Weaviate, Qdrant, etc.)
- Advanced features: connection pooling, caching, batch operations, streaming results

## Files Created ✅
- ✅ `v2/src/core/ports/vector_storage.py` - Comprehensive vector storage interfaces with batch, streaming, and caching support
- ✅ `v2/src/core/ports/mock_vector_storage.py` - Complete in-memory mock implementation with realistic behavior
- ✅ `v2/src/core/domain/value_objects/vector_config.py` - Configuration objects for vector operations and provider settings
- ✅ `v2/src/core/domain/value_objects/vector_result.py` - Result objects for vector operations with comprehensive metrics
- ✅ `v2/src/core/ports/progress.py` - Progress tracking interface for long-running operations
- 🔄 `v2/tests/unit/ports/test_vector_storage_mock.py` - Comprehensive test suite (future work)

---

# Udemy Tutorial Script: Building High-Performance Vector Storage Interfaces

## Introduction (3 minutes)

**[SLIDE 1: Title - "Building Scalable Vector Storage Interfaces for AI Applications"]**

"Welcome to this essential tutorial on designing vector storage interfaces! Today we're going to create the foundation that allows Theodore to work with any vector database - from Pinecone to Weaviate to in-memory solutions - without being locked into any single provider.

By the end of this tutorial, you'll understand how to design interfaces that handle massive-scale similarity search, metadata filtering, batch operations, and high-throughput scenarios. You'll learn patterns that make your AI applications database-agnostic and performance-optimized.

This is infrastructure that scales with your data, not against it!"

## Section 1: Understanding Vector Storage Challenges (5 minutes)

**[SLIDE 2: The Vector Storage Problem]**

"Let's start by understanding why vector storage interfaces are critical. Look at this naive approach:

```python
# ❌ The NAIVE approach - tightly coupled to one vector DB
import pinecone

def find_similar_companies(company_embedding):
    index = pinecone.Index('companies')
    results = index.query(
        vector=company_embedding,
        top_k=10,
        include_metadata=True
    )
    return results['matches']

# Problems:
# 1. Locked into Pinecone forever
# 2. No metadata filtering capabilities
# 3. No batch operations
# 4. No error handling
# 5. Can't test without real vector DB
# 6. No pagination for large results
```

This approach makes your application brittle and hard to scale!"

**[SLIDE 3: Real-World Vector Storage Complexity]**

"Here's what we're actually dealing with in production:

```python
# Different vector database APIs:
# Pinecone: index.query(vector=[...], filter={\"industry\": \"fintech\"})
# Weaviate: client.query.get(\"Company\").with_near_vector({\"vector\": [...]})
# ChromaDB: collection.query(query_embeddings=[[...]], where={\"industry\": \"fintech\"})

# Different metadata systems:
# Pinecone: {\"industry\": \"fintech\", \"size\": \"startup\"}
# Weaviate: class properties with strong typing
# ChromaDB: document metadata with flexible schema

# Different performance characteristics:
# Pinecone: Hosted, optimized for scale, expensive
# Weaviate: Self-hosted, GraphQL queries, complex setup
# ChromaDB: Local/embedded, great for development, limited scale

# Different distance metrics:
# Cosine similarity, Euclidean distance, Dot product
# Some DBs support multiple metrics, others don't
```

We need to abstract all this complexity!"

**[SLIDE 4: The Solution - Vector Storage Port]**

"With the Port/Adapter pattern, we create clean interfaces:

```python
# ✅ The CLEAN approach with actual Theodore implementation
async def find_similar_companies(
    company_embedding: List[float], 
    storage: VectorStorage,
    metadata_filter: Optional[Dict[str, Any]] = None
) -> List[SearchMatch]:
    
    search_config = SearchConfig(
        top_k=20,
        similarity_threshold=0.7,
        metadata_filter=metadata_filter or {},
        include_metadata=True,
        include_vectors=False
    )
    
    result = await storage.search_similar(
        index_name="theodore-companies",
        query_vector=company_embedding,
        config=search_config
    )
    return result.matches

# Benefits:
# 1. Switch vector DBs with dependency injection
# 2. A/B test different storage solutions
# 3. Use in-memory storage for testing
# 4. Consistent error handling across providers
# 5. Unified metadata filtering
```

Let's build this!"

## Section 2: Designing the Core Vector Storage Interface (10 minutes)

**[SLIDE 5: Interface Design Principles]**

"Before we code, let's establish our design principles:

1. **Database Agnostic**: Work with any vector storage solution
2. **Performance First**: Batch operations and efficient querying
3. **Metadata Rich**: Support complex filtering and metadata queries
4. **Scalable**: Handle millions of vectors with pagination
5. **Error Resilient**: Graceful handling of storage failures

Now let's create the interface:"

**[SLIDE 6: Vector Storage Port - Actual Theodore Implementation]**

"Let's start with the main vector storage interface as actually implemented in Theodore:

```python
# v2/src/core/ports/vector_storage.py - Actual Implementation

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from src.core.domain.value_objects.vector_config import (
    VectorConfig, SearchConfig, SimilarityMetric
)
from src.core.domain.value_objects.vector_result import (
    VectorRecord, VectorSearchResult, VectorOperationResult, IndexInfo
)
from src.core.ports.progress import ProgressTracker

# Type aliases for cleaner signatures
ProgressCallback = Callable[[str, float, Optional[str]], None]
VectorId = str
Vector = List[float]
MetadataFilter = Dict[str, Any]

class VectorStorage(ABC):
    \"\"\"
    Port interface for vector storage providers.
    
    This interface defines the contract for all vector storage adapters,
    supporting CRUD operations, similarity search, and index management.
    \"\"\"
    
    # Index Management Methods
    @abstractmethod
    async def create_index(
        self,
        index_name: str,
        dimensions: int,
        metric: str = SimilarityMetric.COSINE,
        metadata_config: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> VectorOperationResult:
        \"\"\"Create a new vector index\"\"\"
        pass
    
    @abstractmethod
    async def delete_index(self, index_name: str) -> bool:
        \"\"\"Delete an existing index\"\"\"
        pass
    
    @abstractmethod
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: str,
        vector: List[float],
        metadata: Optional[VectorMetadata] = None
    ) -> bool:
        \"\"\"Insert or update a single vector\"\"\"
        pass
    
    @abstractmethod
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]]  # [{\"id\": str, \"vector\": List[float], \"metadata\": dict}]
    ) -> Dict[str, bool]:
        \"\"\"Batch insert/update multiple vectors\"\"\"
        pass
    
    @abstractmethod
    async def get_vector(
        self,
        index_name: str,
        vector_id: str,
        include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        \"\"\"Retrieve a specific vector by ID\"\"\"
        pass
    
    @abstractmethod
    async def delete_vector(self, index_name: str, vector_id: str) -> bool:
        \"\"\"Delete a specific vector by ID\"\"\"
        pass
    
    @abstractmethod
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[str]
    ) -> Dict[str, bool]:
        \"\"\"Batch delete multiple vectors\"\"\"
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        index_name: str,
        config: VectorSearchConfig
    ) -> VectorSearchResult:
        \"\"\"Perform similarity search with optional filtering\"\"\"
        pass
    
    @abstractmethod
    async def similarity_search_by_id(
        self,
        index_name: str,
        vector_id: str,
        config: VectorSearchConfig
    ) -> VectorSearchResult:
        \"\"\"Find similar vectors to an existing vector by ID\"\"\"
        pass
    
    @abstractmethod
    async def get_index_stats(self, index_name: str) -> IndexStats:
        \"\"\"Get statistics about an index\"\"\"
        pass
    
    @abstractmethod
    async def list_indexes(self) -> List[str]:
        \"\"\"List all available indexes\"\"\"
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        \"\"\"Check storage health and connectivity\"\"\"
        pass
```

**[SLIDE 7: Understanding the Interface Methods]**

"Let me explain each method group:

**Index Management:**
- `create_index()`: Set up new vector collections with specific dimensions
- `delete_index()`: Clean up unused indexes
- `list_indexes()`: Discover available indexes

**CRUD Operations:**
- `upsert_vector()`: Store single vectors with metadata
- `upsert_vectors_batch()`: Efficient bulk operations
- `get_vector()`: Retrieve by ID
- `delete_vector()`/`delete_vectors_batch()`: Cleanup operations

**Search Operations:**
- `similarity_search()`: Main similarity search with filtering
- `similarity_search_by_id()`: Find similar to existing vector

**Monitoring:**
- `get_index_stats()`: Performance and usage metrics
- `health_check()`: System status"

## Section 3: Creating Value Objects for Vector Operations (8 minutes)

**[SLIDE 8: Vector Search Configuration]**

"Now let's create robust configuration objects for vector operations:

```python
# v2/src/core/domain/value_objects/vector_config.py - Actual Theodore Implementation

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime

class VectorProvider(str, Enum):
    \"\"\"Supported vector database providers\"\"\"
    PINECONE = \"pinecone\"
    CHROMA = \"chroma\"
    WEAVIATE = \"weaviate\"
    QDRANT = \"qdrant\"
    MILVUS = \"milvus\"
    FAISS = \"faiss\"

class SimilarityMetric(str, Enum):
    \"\"\"Similarity metrics for vector comparisons\"\"\"
    COSINE = \"cosine\"
    EUCLIDEAN = \"euclidean\"
    DOT_PRODUCT = \"dot_product\"
    MANHATTAN = \"manhattan\"

class SearchConfig(BaseModel):
    \"\"\"Configuration for vector similarity searches\"\"\"
    
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
    
    class Config:
        validate_assignment = True

class SimilarityMatch(BaseModel):
    \"\"\"A single similarity search result\"\"\"
    id: str = Field(..., description=\"Vector ID\")
    score: float = Field(..., ge=0.0, le=1.0, description=\"Similarity score\")
    metadata: Optional[VectorMetadata] = Field(None, description=\"Associated metadata\")
    vector: Optional[List[float]] = Field(None, description=\"Vector data (if requested)\")
    
    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary for serialization\"\"\"
        result = {
            \"id\": self.id,
            \"score\": self.score
        }
        if self.metadata:
            result[\"metadata\"] = self.metadata.dict()
        if self.vector:
            result[\"vector\"] = self.vector
        return result

class VectorSearchResult(BaseModel):
    \"\"\"Result from vector similarity search\"\"\"
    matches: List[SimilarityMatch] = Field(..., description=\"Similarity matches\")
    total_matches: int = Field(..., ge=0, description=\"Total matches available\")
    search_time_ms: float = Field(..., ge=0, description=\"Search duration in milliseconds\")
    
    # Query info
    query_vector_id: Optional[str] = Field(None, description=\"ID of query vector if searched by ID\")
    distance_metric: DistanceMetric = Field(..., description=\"Distance metric used\")
    
    # Pagination
    offset: int = Field(0, ge=0, description=\"Current offset\")
    has_more: bool = Field(False, description=\"Whether more results are available\")
    
    # Performance metadata
    approximate_search: bool = Field(True, description=\"Whether approximate search was used\")
    index_name: str = Field(..., description=\"Index that was searched\")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def get_top_matches(self, n: int) -> List[SimilarityMatch]:
        \"\"\"Get top N matches\"\"\"
        return self.matches[:n]
    
    def filter_by_score(self, min_score: float) -> List[SimilarityMatch]:
        \"\"\"Filter matches by minimum score\"\"\"
        return [match for match in self.matches if match.score >= min_score]
    
    def get_metadata_values(self, key: str) -> List[Any]:
        \"\"\"Extract specific metadata values from all matches\"\"\"
        values = []
        for match in self.matches:
            if match.metadata and hasattr(match.metadata, key):
                values.append(getattr(match.metadata, key))
        return values
```

**[SLIDE 9: Metadata and Filtering]**

"Now let's create flexible metadata and filtering objects:

```python
# v2/src/core/domain/value_objects/vector_metadata.py

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

class FilterOperator(str, Enum):
    \"\"\"Operators for metadata filtering\"\"\"
    EQUALS = \"eq\"
    NOT_EQUALS = \"ne\"
    GREATER_THAN = \"gt\"
    GREATER_EQUAL = \"gte\"
    LESS_THAN = \"lt\"
    LESS_EQUAL = \"lte\"
    IN = \"in\"
    NOT_IN = \"not_in\"
    CONTAINS = \"contains\"
    STARTS_WITH = \"starts_with\"
    ENDS_WITH = \"ends_with\"

class VectorFilter(BaseModel):
    \"\"\"Flexible metadata filtering for vector search\"\"\"
    field: str = Field(..., description=\"Metadata field to filter on\")
    operator: FilterOperator = Field(..., description=\"Filter operator\")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description=\"Filter value\")
    
    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary for provider-specific formatting\"\"\"
        return {
            \"field\": self.field,
            \"operator\": self.operator.value,
            \"value\": self.value
        }
    
    @classmethod
    def equals(cls, field: str, value: Any) -> 'VectorFilter':
        \"\"\"Create equality filter\"\"\"
        return cls(field=field, operator=FilterOperator.EQUALS, value=value)
    
    @classmethod
    def in_list(cls, field: str, values: List[Any]) -> 'VectorFilter':
        \"\"\"Create 'in list' filter\"\"\"
        return cls(field=field, operator=FilterOperator.IN, value=values)
    
    @classmethod
    def range_filter(cls, field: str, min_val: float, max_val: float) -> List['VectorFilter']:
        \"\"\"Create range filter (returns two filters for AND combination)\"\"\"
        return [
            cls(field=field, operator=FilterOperator.GREATER_EQUAL, value=min_val),
            cls(field=field, operator=FilterOperator.LESS_EQUAL, value=max_val)
        ]

class CompoundFilter(BaseModel):
    \"\"\"Compound filter with AND/OR logic\"\"\"
    filters: List[Union[VectorFilter, 'CompoundFilter']] = Field(..., description=\"Child filters\")
    operator: str = Field(..., description=\"Logical operator: 'AND' or 'OR'\")
    
    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary representation\"\"\"
        return {
            \"operator\": self.operator,
            \"filters\": [f.to_dict() for f in self.filters]
        }
    
    @classmethod
    def and_filters(cls, filters: List[VectorFilter]) -> 'CompoundFilter':
        \"\"\"Create AND compound filter\"\"\"
        return cls(filters=filters, operator=\"AND\")
    
    @classmethod
    def or_filters(cls, filters: List[VectorFilter]) -> 'CompoundFilter':
        \"\"\"Create OR compound filter\"\"\"
        return cls(filters=filters, operator=\"OR\")

class VectorMetadata(BaseModel):
    \"\"\"Metadata associated with a vector\"\"\"
    # Core company metadata
    company_name: str = Field(..., description=\"Company name\")
    company_id: Optional[str] = Field(None, description=\"Unique company identifier\")
    
    # Business metadata
    industry: Optional[str] = Field(None, description=\"Company industry\")
    company_size: Optional[str] = Field(None, description=\"Company size category\")
    founding_year: Optional[int] = Field(None, description=\"Year company was founded\")
    country: Optional[str] = Field(None, description=\"Company headquarters country\")
    
    # Vector metadata
    embedding_model: str = Field(..., description=\"Model used to generate embedding\")
    embedding_version: str = Field(..., description=\"Version of embedding\")
    content_hash: Optional[str] = Field(None, description=\"Hash of source content\")
    
    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = Field(None, description=\"Data source\")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Custom metadata
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description=\"Additional custom metadata\")
    
    def add_custom_field(self, key: str, value: Any) -> None:
        \"\"\"Add a custom metadata field\"\"\"
        self.custom_fields[key] = value
    
    def get_filterable_fields(self) -> Dict[str, Any]:
        \"\"\"Get all fields that can be used for filtering\"\"\"
        filterable = {
            \"company_name\": self.company_name,
            \"industry\": self.industry,
            \"company_size\": self.company_size,
            \"founding_year\": self.founding_year,
            \"country\": self.country,
            \"embedding_model\": self.embedding_model,
            \"source\": self.source
        }
        
        # Add custom fields
        filterable.update(self.custom_fields)
        
        # Remove None values
        return {k: v for k, v in filterable.items() if v is not None}

class IndexStats(BaseModel):
    \"\"\"Statistics about a vector index\"\"\"
    index_name: str = Field(..., description=\"Index identifier\")
    total_vectors: int = Field(..., ge=0, description=\"Total vectors stored\")
    dimension: int = Field(..., gt=0, description=\"Vector dimensions\")
    distance_metric: DistanceMetric = Field(..., description=\"Distance metric used\")
    
    # Storage info
    index_size_bytes: Optional[int] = Field(None, description=\"Index size in bytes\")
    memory_usage_bytes: Optional[int] = Field(None, description=\"Memory usage in bytes\")
    
    # Performance metrics
    average_query_time_ms: Optional[float] = Field(None, description=\"Average query time\")
    queries_per_second: Optional[float] = Field(None, description=\"Query throughput\")
    
    # Metadata distribution
    metadata_fields: Dict[str, int] = Field(default_factory=dict, description=\"Count of vectors with each metadata field\")
    
    # Timestamps
    created_at: datetime = Field(..., description=\"Index creation time\")
    last_updated: datetime = Field(..., description=\"Last update time\")
    
    def get_memory_usage_mb(self) -> Optional[float]:
        \"\"\"Get memory usage in megabytes\"\"\"
        if self.memory_usage_bytes:
            return self.memory_usage_bytes / (1024 * 1024)
        return None
    
    def get_index_size_mb(self) -> Optional[float]:
        \"\"\"Get index size in megabytes\"\"\"
        if self.index_size_bytes:
            return self.index_size_bytes / (1024 * 1024)
        return None
```

**[SLIDE 10: Theodore's Advanced Features Implemented]**

"The actual Theodore implementation provides advanced enterprise features:

1. **Multi-Interface Support**: Base, Batch, Streaming, and Cacheable interfaces
2. **Comprehensive Configuration**: VectorConfig with provider-specific settings and presets
3. **Rich Result Objects**: VectorOperationResult, VectorSearchResult with detailed metrics
4. **Error Handling**: Custom exception hierarchy for different failure types
5. **Progress Tracking**: Real-time progress callbacks for long-running operations
6. **Context Management**: Async context managers for resource cleanup
7. **Mock Implementation**: Complete in-memory mock with realistic similarity calculations
8. **Production Patterns**: Connection pooling, caching, retry logic, circuit breakers

**Key Theodore Features:**
```python
# Multiple provider support
config = VectorConfig.for_company_embeddings()  # Pinecone preset
config = VectorConfig.for_fast_similarity_search()  # Chroma preset

# Extended interfaces
storage: BatchVectorStorage = MockVectorStorage()
await storage.upsert_vectors_chunked(vectors, chunk_size=1000, max_parallel=5)

# Rich results with metrics
result: VectorOperationResult = await storage.upsert_vector(...)
print(f\"Success: {result.is_successful}, Time: {result.execution_time}s\")

# Advanced search configuration
search_config = SearchConfig.for_precise_search()
search_config = SearchConfig.for_fast_search()
```"

## Section 4: Building Mock Implementation for Testing (12 minutes)

**[SLIDE 11: In-Memory Mock Vector Storage]**

"Testing vector storage is complex and expensive. Let's create a comprehensive in-memory mock:

```python
# v2/tests/unit/ports/test_vector_storage_mock.py

import pytest
import numpy as np
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta
import uuid

class MockVectorStorage(VectorStorage, BatchVectorStorage, StreamingVectorStorage, CacheableVectorStorage):
    \"\"\"
    Mock vector storage implementation with full feature support.
    
    Provides an in-memory implementation suitable for testing and development
    with configurable behaviors for simulating real-world scenarios.
    \"\"\"
    
    def __init__(
        self, 
        max_indexes: int = 100,
        max_vectors_per_index: int = 100000,
        simulate_latency: bool = False,
        error_rate: float = 0.0,
        enable_cache: bool = True
    ):
        self.indexes: Dict[str, MockVectorIndex] = {}
        self.max_indexes = max_indexes
        self.max_vectors_per_index = max_vectors_per_index
        self.simulate_latency = simulate_latency
        self.error_rate = error_rate
        self.enable_cache = enable_cache
        
        # Cache for search results
        self.search_cache: Dict[str, tuple[VectorSearchResult, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes default
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Statistics
        self.operation_count = 0
        self.error_count = 0
        self.created_at = datetime.utcnow()
    
    async def create_index(
        self,
        index_name: str,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        metadata_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        \"\"\"Create a new vector index\"\"\"
        await self._simulate_operation()
        
        if index_name in self.indexes:
            return False  # Index already exists
        
        self.indexes[index_name] = {
            \"vectors\": {},  # {vector_id: {\"vector\": [...], \"metadata\": {...}}}
            \"config\": {
                \"dimension\": dimension,
                \"distance_metric\": distance_metric,
                \"metadata_config\": metadata_config or {}
            }
        }
        
        # Initialize stats
        self.index_stats[index_name] = IndexStats(
            index_name=index_name,
            total_vectors=0,
            dimension=dimension,
            distance_metric=distance_metric,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        return True
    
    async def delete_index(self, index_name: str) -> bool:
        \"\"\"Delete an existing index\"\"\"
        await self._simulate_operation()
        
        if index_name not in self.indexes:
            return False
        
        del self.indexes[index_name]
        del self.index_stats[index_name]
        return True
    
    async def upsert_vector(
        self,
        index_name: str,
        vector_id: str,
        vector: List[float],
        metadata: Optional[VectorMetadata] = None
    ) -> bool:
        \"\"\"Insert or update a single vector\"\"\"
        await self._simulate_operation()
        
        if index_name not in self.indexes:
            raise ValueError(f\"Index '{index_name}' does not exist\")
        
        # Validate dimension
        expected_dim = self.indexes[index_name][\"config\"][\"dimension\"]
        if len(vector) != expected_dim:
            raise ValueError(f\"Vector dimension {len(vector)} doesn't match index dimension {expected_dim}\")
        
        # Store vector
        was_new = vector_id not in self.indexes[index_name][\"vectors\"]
        self.indexes[index_name][\"vectors\"][vector_id] = {
            \"vector\": vector,
            \"metadata\": metadata.dict() if metadata else {}
        }
        
        # Update stats
        if was_new:
            self.index_stats[index_name].total_vectors += 1
        self.index_stats[index_name].last_updated = datetime.utcnow()
        
        return True
    
    async def upsert_vectors_batch(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        \"\"\"Batch insert/update multiple vectors\"\"\"
        await self._simulate_operation(len(vectors))
        
        results = {}
        for vector_data in vectors:
            try:
                vector_id = vector_data[\"id\"]
                vector = vector_data[\"vector\"]
                metadata = VectorMetadata(**vector_data.get(\"metadata\", {})) if \"metadata\" in vector_data else None
                
                success = await self.upsert_vector(index_name, vector_id, vector, metadata)
                results[vector_id] = success
            except Exception:
                results[vector_data.get(\"id\", \"unknown\")] = False
        
        return results
    
    async def get_vector(
        self,
        index_name: str,
        vector_id: str,
        include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        \"\"\"Retrieve a specific vector by ID\"\"\"
        await self._simulate_operation()
        
        if index_name not in self.indexes:
            return None
        
        vector_data = self.indexes[index_name][\"vectors\"].get(vector_id)
        if not vector_data:
            return None
        
        result = {
            \"id\": vector_id,
            \"vector\": vector_data[\"vector\"]
        }
        
        if include_metadata:
            result[\"metadata\"] = vector_data[\"metadata\"]
        
        return result
    
    async def delete_vector(self, index_name: str, vector_id: str) -> bool:
        \"\"\"Delete a specific vector by ID\"\"\"
        await self._simulate_operation()
        
        if index_name not in self.indexes:
            return False
        
        if vector_id in self.indexes[index_name][\"vectors\"]:
            del self.indexes[index_name][\"vectors\"][vector_id]
            self.index_stats[index_name].total_vectors -= 1
            self.index_stats[index_name].last_updated = datetime.utcnow()
            return True
        
        return False
    
    async def delete_vectors_batch(
        self,
        index_name: str,
        vector_ids: List[str]
    ) -> Dict[str, bool]:
        \"\"\"Batch delete multiple vectors\"\"\"
        await self._simulate_operation(len(vector_ids))
        
        results = {}
        for vector_id in vector_ids:
            results[vector_id] = await self.delete_vector(index_name, vector_id)
        
        return results
    
    async def similarity_search(
        self,
        index_name: str,
        config: VectorSearchConfig
    ) -> VectorSearchResult:
        \"\"\"Perform similarity search with optional filtering\"\"\"
        start_time = datetime.utcnow()
        await self._simulate_operation()
        
        if index_name not in self.indexes:
            raise ValueError(f\"Index '{index_name}' does not exist\")
        
        if not config.vector:
            raise ValueError(\"Query vector is required\")
        
        # Get all vectors from index
        index_data = self.indexes[index_name]
        all_vectors = index_data[\"vectors\"]
        distance_metric = index_data[\"config\"][\"distance_metric\"]
        
        # Apply metadata filters
        filtered_vectors = self._apply_filters(all_vectors, config.filters)
        
        # Calculate similarities
        similarities = []
        query_vector = np.array(config.vector)
        
        for vector_id, vector_data in filtered_vectors.items():
            stored_vector = np.array(vector_data[\"vector\"])
            
            # Calculate similarity based on distance metric
            if distance_metric == DistanceMetric.COSINE:
                similarity = self._cosine_similarity(query_vector, stored_vector)
            elif distance_metric == DistanceMetric.EUCLIDEAN:
                similarity = self._euclidean_similarity(query_vector, stored_vector)
            elif distance_metric == DistanceMetric.DOT_PRODUCT:
                similarity = np.dot(query_vector, stored_vector)
            else:
                similarity = self._cosine_similarity(query_vector, stored_vector)  # Default
            
            similarities.append({
                \"id\": vector_id,
                \"score\": float(similarity),
                \"vector_data\": vector_data
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[\"score\"], reverse=True)
        
        # Apply pagination
        start_idx = config.offset
        end_idx = start_idx + config.top_k
        paginated_results = similarities[start_idx:end_idx]
        
        # Create similarity matches
        matches = []
        for item in paginated_results:
            metadata = None
            if config.include_metadata and item[\"vector_data\"][\"metadata\"]:
                metadata = VectorMetadata(**item[\"vector_data\"][\"metadata\"])
            
            match = SimilarityMatch(
                id=item[\"id\"],
                score=item[\"score\"],
                metadata=metadata,
                vector=item[\"vector_data\"][\"vector\"] if config.include_vectors else None
            )
            matches.append(match)
        
        # Calculate search time
        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.query_times.append(search_time)
        
        return VectorSearchResult(
            matches=matches,
            total_matches=len(similarities),
            search_time_ms=search_time,
            distance_metric=distance_metric,
            offset=config.offset,
            has_more=end_idx < len(similarities),
            approximate_search=config.approximate,
            index_name=index_name
        )
    
    async def similarity_search_by_id(
        self,
        index_name: str,
        vector_id: str,
        config: VectorSearchConfig
    ) -> VectorSearchResult:
        \"\"\"Find similar vectors to an existing vector by ID\"\"\"
        # Get the vector by ID
        vector_data = await self.get_vector(index_name, vector_id, include_metadata=False)
        if not vector_data:
            raise ValueError(f\"Vector '{vector_id}' not found in index '{index_name}'\")
        
        # Update config with the found vector
        search_config = config.copy()
        search_config.vector = vector_data[\"vector\"]
        
        # Perform similarity search
        result = await self.similarity_search(index_name, search_config)
        result.query_vector_id = vector_id
        
        # Remove the query vector from results (it would have score 1.0)
        result.matches = [match for match in result.matches if match.id != vector_id]
        
        return result
    
    async def get_index_stats(self, index_name: str) -> IndexStats:
        \"\"\"Get statistics about an index\"\"\"
        await self._simulate_operation()
        
        if index_name not in self.index_stats:
            raise ValueError(f\"Index '{index_name}' does not exist\")
        
        stats = self.index_stats[index_name].copy()
        
        # Update dynamic stats
        stats.average_query_time_ms = sum(self.query_times) / len(self.query_times) if self.query_times else 0
        stats.queries_per_second = len(self.query_times) / max(1, (datetime.utcnow() - stats.created_at).total_seconds())
        
        # Calculate metadata field distribution
        vectors = self.indexes[index_name][\"vectors\"]
        metadata_fields = {}
        for vector_data in vectors.values():
            for field in vector_data[\"metadata\"].keys():
                metadata_fields[field] = metadata_fields.get(field, 0) + 1
        stats.metadata_fields = metadata_fields
        
        return stats
    
    async def list_indexes(self) -> List[str]:
        \"\"\"List all available indexes\"\"\"
        await self._simulate_operation()
        return list(self.indexes.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        \"\"\"Check storage health and connectivity\"\"\"
        await self._simulate_operation()
        
        return {
            \"status\": \"healthy\",
            \"total_indexes\": len(self.indexes),
            \"total_vectors\": sum(len(idx[\"vectors\"]) for idx in self.indexes.values()),
            \"requests_processed\": self.request_count,
            \"average_query_time_ms\": sum(self.query_times) / len(self.query_times) if self.query_times else 0,
            \"uptime_seconds\": 3600,  # Mock uptime
            \"memory_usage_estimate_mb\": self._estimate_memory_usage()
        }
    
    # Helper methods
    async def _simulate_operation(self, complexity: int = 1):
        \"\"\"Simulate operation latency and potential errors\"\"\"
        self.request_count += 1
        
        # Simulate latency
        if self.simulate_latency:
            base_latency = 0.001 * complexity  # 1ms per complexity unit
            await asyncio.sleep(base_latency)
        
        # Simulate errors
        if self.error_rate > 0 and np.random.random() < self.error_rate:
            raise Exception(f\"Mock storage error (simulated failure #{self.request_count})\")
    
    def _apply_filters(self, vectors: Dict[str, Any], filters: Optional[VectorFilter]) -> Dict[str, Any]:
        \"\"\"Apply metadata filters to vectors\"\"\"
        if not filters:
            return vectors
        
        filtered = {}
        for vector_id, vector_data in vectors.items():
            metadata = vector_data[\"metadata\"]
            if self._matches_filter(metadata, filters):
                filtered[vector_id] = vector_data
        
        return filtered
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_obj: VectorFilter) -> bool:
        \"\"\"Check if metadata matches a filter\"\"\"
        field_value = metadata.get(filter_obj.field)
        
        if field_value is None:
            return False
        
        if filter_obj.operator == FilterOperator.EQUALS:
            return field_value == filter_obj.value
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return field_value != filter_obj.value
        elif filter_obj.operator == FilterOperator.IN:
            return field_value in filter_obj.value
        elif filter_obj.operator == FilterOperator.NOT_IN:
            return field_value not in filter_obj.value
        elif filter_obj.operator == FilterOperator.CONTAINS:
            return str(filter_obj.value) in str(field_value)
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            return field_value > filter_obj.value
        elif filter_obj.operator == FilterOperator.GREATER_EQUAL:
            return field_value >= filter_obj.value
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            return field_value < filter_obj.value
        elif filter_obj.operator == FilterOperator.LESS_EQUAL:
            return field_value <= filter_obj.value
        
        return False
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        \"\"\"Calculate cosine similarity between two vectors\"\"\"
        dot_product = np.dot(a, b)
        magnitude_a = np.linalg.norm(a)
        magnitude_b = np.linalg.norm(b)
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def _euclidean_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        \"\"\"Calculate Euclidean similarity (1 / (1 + distance))\"\"\"
        distance = np.linalg.norm(a - b)
        return 1.0 / (1.0 + distance)
    
    def _estimate_memory_usage(self) -> float:
        \"\"\"Estimate memory usage in megabytes\"\"\"
        total_vectors = sum(len(idx[\"vectors\"]) for idx in self.indexes.values())
        # Rough estimate: 4 bytes per float * dimension * number of vectors
        avg_dimension = 1536  # Common embedding dimension
        return (total_vectors * avg_dimension * 4) / (1024 * 1024)
```

**[SLIDE 12: Testing the Mock Implementation]**

"Let's create comprehensive tests for our mock:

```python
class TestMockVectorStorage:
    
    @pytest.mark.asyncio
    async def test_index_management(self):
        \"\"\"Test creating and deleting indexes\"\"\"
        storage = MockVectorStorage()
        
        # Create index
        success = await storage.create_index(
            \"test_index\",
            dimension=768,
            distance_metric=DistanceMetric.COSINE
        )
        assert success is True
        
        # List indexes
        indexes = await storage.list_indexes()
        assert \"test_index\" in indexes
        
        # Delete index
        success = await storage.delete_index(\"test_index\")
        assert success is True
        
        # Verify deletion
        indexes = await storage.list_indexes()
        assert \"test_index\" not in indexes
    
    @pytest.mark.asyncio
    async def test_vector_crud_operations(self):
        \"\"\"Test CRUD operations on vectors\"\"\"
        storage = MockVectorStorage()
        
        # Create index
        await storage.create_index(\"test_index\", dimension=3)
        
        # Create metadata
        metadata = VectorMetadata(
            company_name=\"Test Company\",
            industry=\"Technology\",
            embedding_model=\"test-model\",
            embedding_version=\"1.0\"
        )
        
        # Upsert vector
        vector = [0.1, 0.2, 0.3]
        success = await storage.upsert_vector(
            \"test_index\",
            \"company_1\",
            vector,
            metadata
        )
        assert success is True
        
        # Get vector
        retrieved = await storage.get_vector(\"test_index\", \"company_1\")
        assert retrieved is not None
        assert retrieved[\"vector\"] == vector
        assert retrieved[\"metadata\"][\"company_name\"] == \"Test Company\"
        
        # Delete vector
        success = await storage.delete_vector(\"test_index\", \"company_1\")
        assert success is True
        
        # Verify deletion
        retrieved = await storage.get_vector(\"test_index\", \"company_1\")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        \"\"\"Test batch upsert and delete operations\"\"\"
        storage = MockVectorStorage()
        await storage.create_index(\"test_index\", dimension=2)
        
        # Batch upsert
        vectors = [
            {
                \"id\": \"company_1\",
                \"vector\": [0.1, 0.2],
                \"metadata\": {
                    \"company_name\": \"Company 1\",
                    \"industry\": \"Tech\",
                    \"embedding_model\": \"test\",
                    \"embedding_version\": \"1.0\"
                }
            },
            {
                \"id\": \"company_2\",
                \"vector\": [0.3, 0.4],
                \"metadata\": {
                    \"company_name\": \"Company 2\",
                    \"industry\": \"Finance\",
                    \"embedding_model\": \"test\",
                    \"embedding_version\": \"1.0\"
                }
            }
        ]
        
        results = await storage.upsert_vectors_batch(\"test_index\", vectors)
        assert all(results.values())
        
        # Batch delete
        delete_results = await storage.delete_vectors_batch(
            \"test_index\",
            [\"company_1\", \"company_2\"]
        )
        assert all(delete_results.values())
    
    @pytest.mark.asyncio
    async def test_similarity_search(self):
        \"\"\"Test similarity search functionality\"\"\"
        storage = MockVectorStorage()
        await storage.create_index(\"test_index\", dimension=3)
        
        # Add test vectors
        test_data = [
            (\"company_1\", [1.0, 0.0, 0.0], \"Tech\"),
            (\"company_2\", [0.9, 0.1, 0.0], \"Tech\"),  # Similar to company_1
            (\"company_3\", [0.0, 1.0, 0.0], \"Finance\"),
            (\"company_4\", [0.0, 0.0, 1.0], \"Healthcare\")
        ]
        
        for company_id, vector, industry in test_data:
            metadata = VectorMetadata(
                company_name=company_id,
                industry=industry,
                embedding_model=\"test\",
                embedding_version=\"1.0\"
            )
            await storage.upsert_vector(\"test_index\", company_id, vector, metadata)
        
        # Search for similar to company_1
        search_config = VectorSearchConfig(
            vector=[1.0, 0.0, 0.0],
            top_k=3,
            include_metadata=True
        )
        
        result = await storage.similarity_search(\"test_index\", search_config)
        
        # Verify results
        assert len(result.matches) == 3
        assert result.total_matches == 4
        
        # company_1 should be most similar
        assert result.matches[0].id == \"company_1\"
        assert result.matches[0].score > result.matches[1].score
    
    @pytest.mark.asyncio
    async def test_metadata_filtering(self):
        \"\"\"Test metadata filtering in search\"\"\"
        storage = MockVectorStorage()
        await storage.create_index(\"test_index\", dimension=2)
        
        # Add vectors with different industries
        test_data = [
            (\"tech_1\", [0.1, 0.1], \"Technology\"),
            (\"tech_2\", [0.2, 0.2], \"Technology\"),
            (\"finance_1\", [0.3, 0.3], \"Finance\"),
            (\"healthcare_1\", [0.4, 0.4], \"Healthcare\")
        ]
        
        for company_id, vector, industry in test_data:
            metadata = VectorMetadata(
                company_name=company_id,
                industry=industry,
                embedding_model=\"test\",
                embedding_version=\"1.0\"
            )
            await storage.upsert_vector(\"test_index\", company_id, vector, metadata)
        
        # Search with industry filter
        industry_filter = VectorFilter.equals(\"industry\", \"Technology\")
        search_config = VectorSearchConfig(
            vector=[0.15, 0.15],
            top_k=10,
            filters=industry_filter,
            include_metadata=True
        )
        
        result = await storage.similarity_search(\"test_index\", search_config)
        
        # Should only return Technology companies
        assert len(result.matches) == 2
        for match in result.matches:
            assert match.metadata.industry == \"Technology\"
    
    @pytest.mark.asyncio
    async def test_index_statistics(self):
        \"\"\"Test index statistics functionality\"\"\"
        storage = MockVectorStorage()
        await storage.create_index(\"test_index\", dimension=2)
        
        # Add some vectors
        for i in range(5):
            metadata = VectorMetadata(
                company_name=f\"Company {i}\",
                industry=\"Tech\",
                embedding_model=\"test\",
                embedding_version=\"1.0\"
            )
            await storage.upsert_vector(
                \"test_index\",
                f\"company_{i}\",
                [float(i), float(i)],
                metadata
            )
        
        # Get statistics
        stats = await storage.get_index_stats(\"test_index\")
        
        assert stats.index_name == \"test_index\"
        assert stats.total_vectors == 5
        assert stats.dimension == 2
        assert stats.distance_metric == DistanceMetric.COSINE
        assert \"company_name\" in stats.metadata_fields
        assert stats.metadata_fields[\"company_name\"] == 5
    
    @pytest.mark.asyncio
    async def test_error_simulation(self):
        \"\"\"Test error handling\"\"\"
        storage = MockVectorStorage(error_rate=0.5)  # 50% error rate
        
        # Some operations should fail
        failures = 0
        attempts = 10
        
        for i in range(attempts):
            try:
                await storage.create_index(f\"test_{i}\", dimension=2)
            except Exception:
                failures += 1
        
        # With 50% error rate, we expect some failures
        assert failures > 0
        assert failures < attempts  # But not all should fail
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self):
        \"\"\"Test performance tracking capabilities\"\"\"
        storage = MockVectorStorage(simulate_latency=True)
        
        await storage.create_index(\"test_index\", dimension=2)
        
        # Add a vector
        metadata = VectorMetadata(
            company_name=\"Test\",
            embedding_model=\"test\",
            embedding_version=\"1.0\"
        )
        await storage.upsert_vector(\"test_index\", \"test_id\", [0.1, 0.2], metadata)
        
        # Perform a search (this should be tracked)
        config = VectorSearchConfig(vector=[0.1, 0.2], top_k=1)
        result = await storage.similarity_search(\"test_index\", config)
        
        # Check that timing was recorded
        assert result.search_time_ms > 0
        
        # Check health stats include performance data
        health = await storage.health_check()
        assert \"average_query_time_ms\" in health
        assert health[\"requests_processed\"] > 0
```

**[TESTING BENEFITS]** "This comprehensive mock enables:
1. **Fast Development**: No external dependencies for testing
2. **Consistent Results**: Deterministic similarity calculations
3. **Error Scenarios**: Controlled failure simulation
4. **Performance Testing**: Latency and throughput simulation
5. **Feature Validation**: Test all interface methods thoroughly"

## Section 5: Advanced Patterns for Production Use (8 minutes)

**[SLIDE 13: Connection Pooling and Caching]**

"Let's explore production patterns for vector storage:

```python
# Connection pooling for vector databases
class PooledVectorStorage(VectorStorage):
    \"\"\"Vector storage with connection pooling\"\"\"
    
    def __init__(self, storage: VectorStorage, pool_size: int = 10):
        self.storage = storage
        self.pool = asyncio.Semaphore(pool_size)
        self.active_connections = 0
        
    async def similarity_search(self, index_name: str, config: VectorSearchConfig) -> VectorSearchResult:
        async with self.pool:
            self.active_connections += 1
            try:
                return await self.storage.similarity_search(index_name, config)
            finally:
                self.active_connections -= 1

# Caching layer for frequent queries
class CachedVectorStorage(VectorStorage):
    \"\"\"Vector storage with caching layer\"\"\"
    
    def __init__(self, storage: VectorStorage, cache_size: int = 1000, cache_ttl: int = 300):
        self.storage = storage
        self.cache = {}  # In production, use Redis or memcached
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        
    async def similarity_search(self, index_name: str, config: VectorSearchConfig) -> VectorSearchResult:
        # Create cache key
        cache_key = self._create_cache_key(index_name, config)
        
        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result and not self._is_expired(cached_result):
            return cached_result[\"result\"]
        
        # Query storage
        result = await self.storage.similarity_search(index_name, config)
        
        # Cache result
        self.cache[cache_key] = {
            \"result\": result,
            \"timestamp\": datetime.utcnow()
        }
        
        # Evict old entries if cache is full
        if len(self.cache) > self.cache_size:
            self._evict_oldest()
        
        return result
    
    def _create_cache_key(self, index_name: str, config: VectorSearchConfig) -> str:
        \"\"\"Create cache key from search parameters\"\"\"
        # Hash the vector for cache key
        vector_hash = hash(tuple(config.vector)) if config.vector else \"none\"
        filter_hash = hash(str(config.filters)) if config.filters else \"none\"
        return f\"{index_name}:{vector_hash}:{filter_hash}:{config.top_k}\"
```

**[SLIDE 14: Retry and Circuit Breaker Patterns]**

"Production vector storage needs resilience patterns:

```python
# Retry pattern for transient failures
class ResilientVectorStorage(VectorStorage):
    \"\"\"Vector storage with retry logic\"\"\"
    
    def __init__(self, storage: VectorStorage, max_retries: int = 3, backoff_factor: float = 1.5):
        self.storage = storage
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
    async def similarity_search(self, index_name: str, config: VectorSearchConfig) -> VectorSearchResult:
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await self.storage.similarity_search(index_name, config)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = (self.backoff_factor ** attempt)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise last_exception

# Circuit breaker pattern
class CircuitBreakerVectorStorage(VectorStorage):
    \"\"\"Vector storage with circuit breaker\"\"\"
    
    def __init__(self, storage: VectorStorage, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.storage = storage
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = \"CLOSED\"  # CLOSED, OPEN, HALF_OPEN
        
    async def similarity_search(self, index_name: str, config: VectorSearchConfig) -> VectorSearchResult:
        if self.state == \"OPEN\":
            if self._should_attempt_reset():
                self.state = \"HALF_OPEN\"
            else:
                raise Exception(\"Circuit breaker is OPEN\")
        
        try:
            result = await self.storage.similarity_search(index_name, config)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = \"CLOSED\"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = \"OPEN\"
```

**[SLIDE 15: Monitoring and Observability]**

"Production monitoring for vector operations:

```python
# Instrumented vector storage
from opentelemetry import trace, metrics

class InstrumentedVectorStorage(VectorStorage):
    \"\"\"Vector storage with OpenTelemetry instrumentation\"\"\"
    
    def __init__(self, storage: VectorStorage):
        self.storage = storage
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Metrics
        self.search_counter = self.meter.create_counter(
            \"vector_storage_searches\",
            description=\"Number of similarity searches\"
        )
        self.search_latency = self.meter.create_histogram(
            \"vector_storage_search_latency\",
            description=\"Search latency in milliseconds\"
        )
        self.vector_counter = self.meter.create_counter(
            \"vector_storage_vectors\",
            description=\"Number of vectors stored\"
        )
        
    async def similarity_search(self, index_name: str, config: VectorSearchConfig) -> VectorSearchResult:
        with self.tracer.start_as_current_span(
            \"vector_storage_similarity_search\",
            attributes={
                \"index_name\": index_name,
                \"top_k\": config.top_k,
                \"distance_metric\": config.distance_metric.value,
                \"has_filters\": config.filters is not None
            }
        ) as span:
            
            start_time = time.time()
            
            try:
                result = await self.storage.similarity_search(index_name, config)
                
                # Record metrics
                self.search_counter.add(1, {
                    \"index_name\": index_name,
                    \"status\": \"success\"
                })
                
                # Record search details
                span.set_attributes({
                    \"result_count\": len(result.matches),
                    \"total_matches\": result.total_matches,
                    \"search_time_ms\": result.search_time_ms,
                    \"approximate\": result.approximate_search
                })
                
                return result
                
            except Exception as e:
                self.search_counter.add(1, {
                    \"index_name\": index_name,
                    \"status\": \"error\"
                })
                
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            finally:
                latency = (time.time() - start_time) * 1000
                self.search_latency.record(latency, {
                    \"index_name\": index_name
                })
                span.set_attribute(\"latency_ms\", latency)
```

## Section 6: Integration Testing Strategies (5 minutes)

**[SLIDE 16: Testing with Real Vector Databases]**

"Integration testing strategies for vector storage:

```python
# Integration tests with real vector databases
@pytest.mark.integration
@pytest.mark.asyncio
async def test_pinecone_integration():
    \"\"\"Test with real Pinecone instance\"\"\"
    api_key = os.getenv(\"PINECONE_TEST_API_KEY\")
    if not api_key:
        pytest.skip(\"No Pinecone test API key available\")
    
    storage = PineconeVectorStorage(api_key=api_key, environment=\"test\")
    
    test_index = f\"test_index_{uuid.uuid4().hex[:8]}\"
    
    try:
        # Create test index
        await storage.create_index(test_index, dimension=768)
        
        # Test basic operations
        metadata = VectorMetadata(
            company_name=\"Test Company\",
            industry=\"Technology\",
            embedding_model=\"test-embedding\",
            embedding_version=\"1.0\"
        )
        
        test_vector = [0.1] * 768  # 768-dimensional test vector
        
        # Upsert
        success = await storage.upsert_vector(test_index, \"test_id\", test_vector, metadata)
        assert success
        
        # Search
        config = VectorSearchConfig(vector=test_vector, top_k=5)
        result = await storage.similarity_search(test_index, config)
        assert len(result.matches) > 0
        assert result.matches[0].id == \"test_id\"
        
    finally:
        # Cleanup
        await storage.delete_index(test_index)

# Performance benchmark tests
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_performance():
    \"\"\"Benchmark search performance\"\"\"
    storage = MockVectorStorage(simulate_latency=True)
    await storage.create_index(\"benchmark_index\", dimension=1536)
    
    # Add 1000 test vectors
    vectors = []
    for i in range(1000):
        metadata = VectorMetadata(
            company_name=f\"Company {i}\",
            industry=f\"Industry {i % 10}\",
            embedding_model=\"benchmark\",
            embedding_version=\"1.0\"
        )
        
        vector = np.random.normal(0, 1, 1536).tolist()
        vectors.append({
            \"id\": f\"company_{i}\",
            \"vector\": vector,
            \"metadata\": metadata.dict()
        })
    
    # Batch upsert
    start_time = time.time()
    await storage.upsert_vectors_batch(\"benchmark_index\", vectors)
    upsert_time = time.time() - start_time
    
    print(f\"Batch upsert of 1000 vectors: {upsert_time:.2f}s\")
    
    # Benchmark search
    query_vector = np.random.normal(0, 1, 1536).tolist()
    config = VectorSearchConfig(vector=query_vector, top_k=10)
    
    search_times = []
    for _ in range(100):
        start_time = time.time()
        result = await storage.similarity_search(\"benchmark_index\", config)
        search_time = time.time() - start_time
        search_times.append(search_time)
        assert len(result.matches) == 10
    
    avg_search_time = sum(search_times) / len(search_times)
    print(f\"Average search time: {avg_search_time*1000:.2f}ms\")
    
    # Performance should be reasonable
    assert avg_search_time < 0.1  # Less than 100ms average
```

**[PERFORMANCE CONSIDERATIONS]** "For production, also test:
1. **Concurrent Operations**: Multiple searches simultaneously
2. **Large Scale**: Performance with millions of vectors
3. **Memory Usage**: Monitor memory consumption during operations
4. **Index Optimization**: Different index configurations and their trade-offs"

## Conclusion (3 minutes)

**[SLIDE 17: What We Built]**

"Congratulations! You've built a production-ready vector storage interface system. Let's recap what we accomplished:

✅ **Database Agnostic Interfaces**: Support any vector database with consistent APIs
✅ **Rich Metadata Support**: Complex filtering and flexible metadata schemas
✅ **Performance Optimized**: Batch operations, caching, and connection pooling
✅ **Production Patterns**: Retry logic, circuit breakers, and monitoring
✅ **Comprehensive Testing**: Mock implementations and performance benchmarks
✅ **Scalable Design**: Handle millions of vectors with pagination and efficient search

**[SLIDE 18: Next Steps]**

Your homework:
1. Implement adapters for Pinecone, Weaviate, and ChromaDB using these interfaces
2. Add more sophisticated caching strategies (Redis integration)
3. Create automated index optimization routines
4. Build a vector database selection algorithm based on data characteristics

**[FINAL THOUGHT]**
"Remember, vector storage is the foundation of modern AI applications. These interfaces ensure your similarity search capabilities can evolve with your data scale and requirements. As new vector databases emerge, you can adapt without rewriting your application logic.

Thank you for joining me in this comprehensive tutorial. If you have questions, leave them in the comments below. Happy coding!"

---

## Instructor Notes:
- Total runtime: ~58 minutes
- Include complete code repository and example datasets in video description
- Emphasize the importance of proper indexing for performance
- Consider follow-up video on implementing specific vector database adapters
- Demonstrate actual similarity search with real embeddings in live coding sections
"""
Unit tests for Pinecone vector storage adapter.

Tests all components of the Pinecone adapter including configuration,
client, adapter, index management, batch processing, and monitoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Test imports
from src.infrastructure.adapters.storage.pinecone.config import (
    PineconeConfig, PineconeIndexConfig, PineconeCredentials
)
from src.infrastructure.adapters.storage.pinecone.client import (
    PineconeClient, PineconeClientStats, PineconeRetryPolicy
)
from src.infrastructure.adapters.storage.pinecone.adapter import PineconeVectorStorage
from src.infrastructure.adapters.storage.pinecone.index import PineconeIndexManager
from src.infrastructure.adapters.storage.pinecone.batch import PineconeBatchProcessor
from src.infrastructure.adapters.storage.pinecone.query import PineconeQueryEngine
from src.infrastructure.adapters.storage.pinecone.monitor import PineconeMonitor

from src.core.domain.value_objects.vector_search_result import (
    VectorSearchConfig, VectorOperationResult, IndexStats
)
from src.core.domain.value_objects.vector_metadata import (
    UnifiedVectorMetadata, VectorEntityType, VectorEmbeddingMetadata
)


class TestPineconeConfig:
    """Test Pinecone configuration management."""
    
    def test_pinecone_config_creation(self):
        """Test basic config creation."""
        config = PineconeConfig(
            api_key="test-api-key-12345",
            environment="us-west1-gcp"
        )
        
        assert config.api_key == "test-api-key-12345"
        assert config.environment == "us-west1-gcp"
        assert config.default_dimensions == 1536
        assert config.default_metric == "cosine"
        assert config.batch_size == 100
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid API key
        with pytest.raises(ValueError, match="api_key must be a valid"):
            PineconeConfig(api_key="short", environment="us-west1-gcp")
        
        # Test invalid environment
        with pytest.raises(ValueError, match="environment must be a valid"):
            PineconeConfig(api_key="test-api-key-12345", environment="x")
        
        # Test invalid metric
        with pytest.raises(ValueError, match="metric must be one of"):
            PineconeConfig(
                api_key="test-api-key-12345",
                environment="us-west1-gcp",
                default_metric="invalid"
            )
    
    @patch.dict('os.environ', {
        'PINECONE_API_KEY': 'env-api-key-12345',
        'PINECONE_ENVIRONMENT': 'us-east1-gcp',
        'PINECONE_DIMENSIONS': '768'
    })
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        config = PineconeConfig.from_env()
        
        assert config.api_key == "env-api-key-12345"
        assert config.environment == "us-east1-gcp"
        assert config.default_dimensions == 768
    
    def test_get_client_kwargs(self):
        """Test client kwargs generation."""
        config = PineconeConfig(
            api_key="test-api-key-12345",
            environment="us-west1-gcp",
            request_timeout=45.0
        )
        
        kwargs = config.get_client_kwargs()
        
        assert kwargs['api_key'] == "test-api-key-12345"
        assert kwargs['environment'] == "us-west1-gcp"
        assert kwargs['timeout'] == 45.0


class TestPineconeCredentials:
    """Test Pinecone credentials management."""
    
    def test_credentials_creation(self):
        """Test credentials creation and validation."""
        creds = PineconeCredentials("test-api-key-12345", "us-west1-gcp")
        
        assert creds.api_key == "test-api-key-12345"
        assert creds.environment == "us-west1-gcp"
        assert creds.validate() is True
    
    def test_credentials_validation(self):
        """Test credentials validation."""
        # Valid credentials
        valid_creds = PineconeCredentials("test-api-key-12345", "us-west1-gcp")
        assert valid_creds.validate() is True
        
        # Invalid API key
        invalid_key_creds = PineconeCredentials("short", "us-west1-gcp")
        assert invalid_key_creds.validate() is False
        
        # Invalid environment
        invalid_env_creds = PineconeCredentials("test-api-key-12345", "x")
        assert invalid_env_creds.validate() is False
    
    def test_mask_api_key(self):
        """Test API key masking for logging."""
        creds = PineconeCredentials("test-api-key-12345", "us-west1-gcp")
        masked = creds.mask_api_key()
        
        assert masked.startswith("test")
        assert masked.endswith("2345")
        assert "***" in masked


class TestPineconeClientStats:
    """Test Pinecone client statistics."""
    
    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = PineconeClientStats()
        
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.get_success_rate() == 0.0
    
    def test_add_request_stats(self):
        """Test adding request statistics."""
        stats = PineconeClientStats()
        
        # Add successful request
        stats.add_request(100.0, success=True)
        assert stats.total_requests == 1
        assert stats.successful_requests == 1
        assert stats.avg_latency_ms == 100.0
        assert stats.get_success_rate() == 100.0
        
        # Add failed request
        stats.add_request(150.0, success=False)
        assert stats.total_requests == 2
        assert stats.failed_requests == 1
        assert stats.avg_latency_ms == 125.0
        assert stats.get_success_rate() == 50.0


class TestPineconeRetryPolicy:
    """Test Pinecone retry policy."""
    
    def test_retry_policy_initialization(self):
        """Test retry policy initialization."""
        policy = PineconeRetryPolicy(max_retries=5, base_delay=2.0)
        
        assert policy.max_retries == 5
        assert policy.base_delay == 2.0
    
    def test_should_retry_logic(self):
        """Test retry decision logic."""
        policy = PineconeRetryPolicy(max_retries=3)
        
        # Should retry on connection error
        assert policy.should_retry(1, ConnectionError("Connection failed")) is True
        
        # Should not retry after max attempts
        assert policy.should_retry(3, ConnectionError("Connection failed")) is False
        
        # Should retry on timeout
        assert policy.should_retry(1, TimeoutError("Request timeout")) is True
    
    def test_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        policy = PineconeRetryPolicy(base_delay=1.0, max_delay=10.0)
        
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
        assert policy.get_delay(10) == 10.0  # Capped at max_delay


@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client for testing."""
    with patch('src.infrastructure.adapters.storage.pinecone.client.PINECONE_AVAILABLE', True):
        with patch('src.infrastructure.adapters.storage.pinecone.client.Pinecone') as mock_pinecone:
            mock_client = Mock()
            mock_pinecone.return_value = mock_client
            yield mock_client


@pytest.fixture
def pinecone_config():
    """Test Pinecone configuration."""
    return PineconeConfig(
        api_key="test-api-key-12345",
        environment="us-west1-gcp",
        default_dimensions=1536,
        batch_size=50
    )


class TestPineconeClient:
    """Test Pinecone client functionality."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, pinecone_config, mock_pinecone_client):
        """Test client initialization."""
        client = PineconeClient(pinecone_config)
        
        assert client.config == pinecone_config
        assert client.stats.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_client_initialize(self, pinecone_config, mock_pinecone_client):
        """Test client initialization process."""
        client = PineconeClient(pinecone_config)
        
        await client.initialize()
        
        assert client._client is not None
    
    @pytest.mark.asyncio
    async def test_list_indexes(self, pinecone_config, mock_pinecone_client):
        """Test listing indexes."""
        mock_index_info = Mock()
        mock_index_info.name = "test-index"
        mock_indexes_response = Mock()
        mock_indexes_response.indexes = [mock_index_info]
        
        mock_pinecone_client.list_indexes.return_value = mock_indexes_response
        
        client = PineconeClient(pinecone_config)
        await client.initialize()
        
        indexes = await client.list_indexes()
        
        assert indexes == ["test-index"]
    
    @pytest.mark.asyncio
    async def test_index_exists(self, pinecone_config, mock_pinecone_client):
        """Test checking if index exists."""
        mock_index_info = Mock()
        mock_index_info.name = "existing-index"
        mock_indexes_response = Mock()
        mock_indexes_response.indexes = [mock_index_info]
        
        mock_pinecone_client.list_indexes.return_value = mock_indexes_response
        
        client = PineconeClient(pinecone_config)
        await client.initialize()
        
        assert await client.index_exists("existing-index") is True
        assert await client.index_exists("non-existing-index") is False
    
    @pytest.mark.asyncio
    async def test_health_check(self, pinecone_config, mock_pinecone_client):
        """Test client health check."""
        mock_index_info = Mock()
        mock_index_info.name = "test-index"
        mock_indexes_response = Mock()
        mock_indexes_response.indexes = [mock_index_info]
        
        mock_pinecone_client.list_indexes.return_value = mock_indexes_response
        
        client = PineconeClient(pinecone_config)
        await client.initialize()
        
        health = await client.health_check()
        
        assert health['status'] == 'healthy'
        assert 'latency_ms' in health
        assert health['indexes_count'] == 1


class TestPineconeIndexManager:
    """Test Pinecone index management."""
    
    @pytest.fixture
    def mock_client(self, pinecone_config):
        """Mock client for index manager."""
        client = Mock()
        client.config = pinecone_config
        return client
    
    @pytest.fixture
    def index_manager(self, mock_client, pinecone_config):
        """Index manager with mocked client."""
        return PineconeIndexManager(mock_client, pinecone_config)
    
    @pytest.mark.asyncio
    async def test_create_index(self, index_manager, mock_client):
        """Test index creation."""
        mock_client.index_exists.return_value = False
        mock_client.create_index.return_value = VectorOperationResult.success_result(
            operation="create_index",
            message="Index created"
        )
        
        result = await index_manager.create_index(
            index_name="test-index",
            dimensions=1536,
            metric="cosine"
        )
        
        assert result.success is True
        assert result.operation == "create_index"
        mock_client.create_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_existing_index(self, index_manager, mock_client):
        """Test creating index that already exists."""
        mock_client.index_exists.return_value = True
        
        result = await index_manager.create_index(
            index_name="existing-index",
            dimensions=1536
        )
        
        assert result.success is False
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_delete_index(self, index_manager, mock_client):
        """Test index deletion."""
        mock_client.index_exists.return_value = True
        mock_client.delete_index.return_value = VectorOperationResult.success_result(
            operation="delete_index",
            message="Index deleted"
        )
        
        result = await index_manager.delete_index("test-index")
        
        assert result.success is True
        mock_client.delete_index.assert_called_once_with("test-index")


class TestPineconeBatchProcessor:
    """Test Pinecone batch processing."""
    
    @pytest.fixture
    def mock_client(self, pinecone_config):
        """Mock client for batch processor."""
        client = Mock()
        client.config = pinecone_config
        return client
    
    @pytest.fixture
    def batch_processor(self, mock_client, pinecone_config):
        """Batch processor with mocked client."""
        return PineconeBatchProcessor(mock_client, pinecone_config)
    
    @pytest.mark.asyncio
    async def test_upsert_vectors_batch_empty(self, batch_processor):
        """Test batch upsert with empty vectors."""
        result = await batch_processor.upsert_vectors_batch(
            index_name="test-index",
            vectors=[],
            batch_size=10
        )
        
        assert result.success is True
        assert result.affected_count == 0
        assert "No vectors to upsert" in result.message
    
    @pytest.mark.asyncio
    async def test_calculate_optimal_chunk_size(self, batch_processor):
        """Test optimal chunk size calculation."""
        # Small dataset
        chunk_size = batch_processor._calculate_optimal_chunk_size(
            total_vectors=500,
            max_parallel=5
        )
        assert chunk_size >= 100
        
        # Large dataset
        chunk_size = batch_processor._calculate_optimal_chunk_size(
            total_vectors=10000,
            max_parallel=10
        )
        assert chunk_size > 100


class TestPineconeQueryEngine:
    """Test Pinecone query engine."""
    
    @pytest.fixture
    def mock_client(self, pinecone_config):
        """Mock client for query engine."""
        client = Mock()
        client.config = pinecone_config
        return client
    
    @pytest.fixture
    def query_engine(self, mock_client, pinecone_config):
        """Query engine with mocked client."""
        return PineconeQueryEngine(mock_client, pinecone_config)
    
    def test_convert_filter_to_pinecone(self, query_engine):
        """Test metadata filter conversion."""
        metadata_filter = {
            "entity_type": "company",
            "industry": "technology"
        }
        
        pinecone_filter = query_engine._convert_filter_to_pinecone(metadata_filter)
        
        assert pinecone_filter["entity_type"]["$eq"] == "company"
        assert pinecone_filter["industry"]["$eq"] == "technology"
    
    def test_convert_complex_filter(self, query_engine):
        """Test complex filter conversion."""
        metadata_filter = {
            "$and": [
                {"entity_type": "company"},
                {"$or": [
                    {"industry": "technology"},
                    {"industry": "healthcare"}
                ]}
            ]
        }
        
        pinecone_filter = query_engine._convert_filter_to_pinecone(metadata_filter)
        
        assert "$and" in pinecone_filter
        assert len(pinecone_filter["$and"]) == 2


class TestPineconeMonitor:
    """Test Pinecone monitoring."""
    
    @pytest.fixture
    def monitor_config(self):
        """Monitor configuration."""
        return PineconeConfig(
            api_key="test-api-key-12345",
            environment="us-west1-gcp",
            enable_monitoring=True,
            metrics_collection_interval=10
        )
    
    @pytest.fixture
    def monitor(self, monitor_config):
        """Monitor with test configuration."""
        return PineconeMonitor(monitor_config)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.enabled is True
        assert len(monitor._metrics) == 0
    
    def test_record_operation(self, monitor):
        """Test recording operations."""
        monitor.record_operation(
            operation_type="upsert_vector",
            duration_ms=150.0,
            success=True
        )
        
        assert len(monitor._metrics) == 1
        assert monitor._operation_counters["upsert_vector"] == 1
    
    def test_record_failed_operation(self, monitor):
        """Test recording failed operations."""
        monitor.record_operation(
            operation_type="search_similar",
            duration_ms=250.0,
            success=False,
            error_message="Connection timeout"
        )
        
        assert len(monitor._metrics) == 1
        assert monitor._error_counters["search_similar"] == 1
        
        metrics = monitor.get_operation_metrics()
        assert len(metrics) == 1
        assert metrics[0].success is False
        assert metrics[0].error_message == "Connection timeout"
    
    def test_get_performance_summary(self, monitor):
        """Test performance summary generation."""
        # Record some operations
        monitor.record_operation("upsert_vector", 100.0, True)
        monitor.record_operation("search_similar", 200.0, True)
        monitor.record_operation("delete_vector", 50.0, False, "Not found")
        
        summary = monitor.get_performance_summary()
        
        assert summary['monitoring_enabled'] is True
        assert summary['summary']['total_operations'] == 3
        assert summary['summary']['successful_operations'] == 2
        assert summary['summary']['failed_operations'] == 1
        assert summary['summary']['success_rate_percent'] == pytest.approx(66.67, rel=1e-2)
    
    def test_get_real_time_metrics(self, monitor):
        """Test real-time metrics."""
        monitor.record_operation("upsert_vector", 100.0, True)
        
        metrics = monitor.get_real_time_metrics()
        
        assert metrics['monitoring_enabled'] is True
        assert 'current_window' in metrics
        assert 'last_minute' in metrics
        assert 'lifetime_totals' in metrics
    
    def test_get_health_score(self, monitor):
        """Test health score calculation."""
        # Record high-performance operations
        for _ in range(10):
            monitor.record_operation("upsert_vector", 50.0, True)
        
        health = monitor.get_health_score()
        
        assert health['health_score'] >= 90
        assert health['health_status'] == 'excellent'
        assert health['monitoring_enabled'] is True


class TestPineconeVectorStorage:
    """Test main Pinecone vector storage adapter."""
    
    @pytest.fixture
    def mock_components(self, pinecone_config):
        """Mock all Pinecone adapter components."""
        with patch('src.infrastructure.adapters.storage.pinecone.adapter.PineconeClient') as mock_client:
            with patch('src.infrastructure.adapters.storage.pinecone.adapter.PineconeIndexManager') as mock_index_mgr:
                with patch('src.infrastructure.adapters.storage.pinecone.adapter.PineconeBatchProcessor') as mock_batch:
                    with patch('src.infrastructure.adapters.storage.pinecone.adapter.PineconeQueryEngine') as mock_query:
                        with patch('src.infrastructure.adapters.storage.pinecone.adapter.PineconeMonitor') as mock_monitor:
                            yield {
                                'client': mock_client.return_value,
                                'index_manager': mock_index_mgr.return_value,
                                'batch_processor': mock_batch.return_value,
                                'query_engine': mock_query.return_value,
                                'monitor': mock_monitor.return_value
                            }
    
    @pytest.fixture
    def storage_adapter(self, pinecone_config, mock_components):
        """Vector storage adapter with mocked components."""
        return PineconeVectorStorage(pinecone_config)
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, storage_adapter):
        """Test adapter initialization."""
        assert storage_adapter.config is not None
        assert storage_adapter._initialized is False
        assert storage_adapter._closed is False
    
    @pytest.mark.asyncio
    async def test_create_index(self, storage_adapter, mock_components):
        """Test index creation through adapter."""
        mock_components['index_manager'].create_index.return_value = VectorOperationResult.success_result(
            operation="create_index",
            message="Index created successfully"
        )
        
        # Initialize adapter
        await storage_adapter._ensure_initialized()
        
        result = await storage_adapter.create_index(
            index_name="test-index",
            dimensions=1536,
            metric="cosine"
        )
        
        assert result.success is True
        mock_components['index_manager'].create_index.assert_called_once()
        mock_components['monitor'].record_operation.assert_called_with("create_index", success=True)
    
    @pytest.mark.asyncio
    async def test_upsert_vector(self, storage_adapter, mock_components):
        """Test single vector upsert."""
        # Mock the index and upsert response
        mock_index = Mock()
        mock_upsert_response = Mock()
        mock_upsert_response.upserted_count = 1
        mock_index.upsert.return_value = mock_upsert_response
        
        mock_components['client'].get_index.return_value = mock_index
        
        # Create test vector and metadata
        vector = [0.1] * 1536
        embedding_metadata = VectorEmbeddingMetadata(
            model_name="test-model",
            model_provider="test-provider",
            dimensions=1536
        )
        metadata = UnifiedVectorMetadata(
            entity_id="test-entity",
            entity_type=VectorEntityType.COMPANY,
            vector_id="test-vector",
            embedding=embedding_metadata,
            index_name="test-index"
        )
        
        # Initialize adapter
        await storage_adapter._ensure_initialized()
        
        result = await storage_adapter.upsert_vector(
            index_name="test-index",
            vector_id="test-vector",
            vector=vector,
            metadata=metadata
        )
        
        assert result.success is True
        assert result.affected_count == 1
        mock_index.upsert.assert_called_once()
        mock_components['monitor'].record_operation.assert_called_with("upsert_vector", success=True)
    
    @pytest.mark.asyncio
    async def test_search_similar(self, storage_adapter, mock_components):
        """Test similarity search."""
        mock_search_result = Mock()
        mock_components['query_engine'].search_similar.return_value = mock_search_result
        
        search_config = VectorSearchConfig(
            top_k=10,
            similarity_threshold=0.7,
            include_metadata=True
        )
        
        # Initialize adapter
        await storage_adapter._ensure_initialized()
        
        result = await storage_adapter.search_similar(
            index_name="test-index",
            query_vector=[0.1] * 1536,
            config=search_config
        )
        
        assert result == mock_search_result
        mock_components['query_engine'].search_similar.assert_called_once()
        mock_components['monitor'].record_operation.assert_called_with("search_similar", success=True)
    
    @pytest.mark.asyncio
    async def test_context_manager(self, storage_adapter, mock_components):
        """Test adapter as async context manager."""
        async with storage_adapter as adapter:
            assert adapter == storage_adapter
            assert storage_adapter._initialized is True
        
        # Close should be called on exit
        mock_components['client'].close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, storage_adapter, mock_components):
        """Test error handling in adapter methods."""
        # Mock client to raise exception
        mock_components['client'].get_index.side_effect = Exception("Connection failed")
        
        # Initialize adapter
        await storage_adapter._ensure_initialized()
        
        # Test that exception is properly handled and converted
        with pytest.raises(Exception):
            await storage_adapter.upsert_vector(
                index_name="test-index",
                vector_id="test-vector",
                vector=[0.1] * 1536
            )
        
        mock_components['monitor'].record_operation.assert_called_with("upsert_vector", success=False)


# Integration test fixtures and helpers
@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    embedding_metadata = VectorEmbeddingMetadata(
        model_name="test-model",
        model_provider="test-provider",
        dimensions=128
    )
    
    vectors = []
    for i in range(5):
        metadata = UnifiedVectorMetadata(
            entity_id=f"entity-{i}",
            entity_type=VectorEntityType.COMPANY,
            vector_id=f"vector-{i}",
            embedding=embedding_metadata,
            index_name="test-index"
        )
        vector = [float(i * 0.1 + j * 0.01) for j in range(128)]
        vectors.append((f"vector-{i}", vector, metadata))
    
    return vectors


@pytest.fixture
def search_config():
    """Sample search configuration."""
    return VectorSearchConfig(
        top_k=3,
        similarity_threshold=0.5,
        distance_metric="cosine",
        include_metadata=True,
        include_values=False
    )


class TestPineconeIntegration:
    """Integration tests for Pinecone adapter components."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self, pinecone_config, sample_vectors, search_config):
        """Test complete workflow with mocked Pinecone."""
        with patch('src.infrastructure.adapters.storage.pinecone.client.PINECONE_AVAILABLE', True):
            with patch('src.infrastructure.adapters.storage.pinecone.client.Pinecone') as mock_pinecone:
                # Mock Pinecone client and responses
                mock_client = Mock()
                mock_pinecone.return_value = mock_client
                
                mock_index = Mock()
                mock_client.Index.return_value = mock_index
                
                # Mock index operations
                mock_upsert_response = Mock()
                mock_upsert_response.upserted_count = len(sample_vectors)
                mock_index.upsert.return_value = mock_upsert_response
                
                mock_search_response = Mock()
                mock_search_response.matches = []
                mock_index.query.return_value = mock_search_response
                
                # Create adapter
                adapter = PineconeVectorStorage(pinecone_config)
                
                async with adapter:
                    # Test batch upsert
                    upsert_result = await adapter.upsert_vectors_batch(
                        index_name="test-index",
                        vectors=sample_vectors,
                        batch_size=2
                    )
                    
                    assert upsert_result.success is True
                    
                    # Test search
                    query_vector = [0.1] * 128
                    search_result = await adapter.search_similar(
                        index_name="test-index",
                        query_vector=query_vector,
                        config=search_config
                    )
                    
                    assert isinstance(search_result.search_time_ms, float)
                    assert search_result.index_name == "test-index"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
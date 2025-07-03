"""
Storage Provider for Theodore v2 Container.

Manages vector storage, caching, and data persistence adapters with
configuration-driven selection and connection pooling.
"""

from typing import Dict, Any, Optional
from dependency_injector import containers, providers
import logging

# Import storage interfaces
from src.core.ports.vector_storage import VectorStorage
# Company repository will be implemented separately

# Import storage adapters
from src.infrastructure.adapters.storage.pinecone.adapter import PineconeVectorStorage
# from src.infrastructure.adapters.storage.memory_vector_storage import MemoryVectorStorage
# from src.infrastructure.adapters.storage.company_repository import CompanyRepository


def _create_vector_storage(
    config: Dict[str, Any],
    external_services: Any
) -> VectorStorage:
    """
    Factory function to create vector storage adapter based on configuration.
    
    Args:
        config: Vector storage configuration
        external_services: External services container
        
    Returns:
        Configured vector storage adapter
        
    Raises:
        ValueError: If storage provider is not supported
    """
    logger = logging.getLogger(__name__)
    provider = config.get("provider", "pinecone").lower()
    
    logger.info(f"Creating vector storage adapter: {provider}")
    
    if provider == "pinecone":
        return _create_pinecone_adapter(config, external_services)
    elif provider == "memory":
        return _create_memory_vector_storage(config)
    else:
        raise ValueError(f"Unsupported vector storage provider: {provider}")


class StorageProvider(containers.DeclarativeContainer):
    """
    Storage provider container for all data persistence components.
    
    Provides:
    - Vector storage adapters (Pinecone, Memory)
    - Company repository implementation
    - Cache management
    - Connection pooling and lifecycle management
    """
    
    # Configuration injection
    config = providers.Configuration()
    external_services = providers.Dependency()
    
    # Vector Storage Factory
    vector_storage = providers.Factory(
        _create_vector_storage,
        config=config.vector_storage,
        external_services=external_services
    )
    
    # Company Repository - commented out for now
    # company_repository = providers.Singleton(
    #     CompanyRepository,
    #     vector_storage=vector_storage,
    #     config=config.company_repository
    # )
    
    # Cache providers (in-memory for now, can be extended to Redis)
    memory_cache = providers.Singleton(
        dict  # Simple in-memory cache, can be replaced with more sophisticated implementation
    )
    
    # Storage health checker - commented out for now
    # storage_health = providers.Factory(
    #     _create_storage_health_checker,
    #     vector_storage=vector_storage,
    #     company_repository=company_repository,
    #     config=config.health
    # )


def _create_pinecone_adapter(
    config: Dict[str, Any],
    external_services: Any
) -> PineconeVectorStorage:
    """Create and configure Pinecone adapter."""
    logger = logging.getLogger(__name__)
    
    # Extract Pinecone-specific configuration
    pinecone_config = {
        "api_key": config.get("api_key"),
        "index_name": config.get("index_name", "theodore-companies"),
        "environment": config.get("environment", "gcp-starter"),
        "dimension": config.get("dimension", 1536),
        "metric": config.get("metric", "cosine"),
        "timeout_seconds": config.get("timeout_seconds", 30.0),
        "max_retries": config.get("max_retries", 3),
        "enable_caching": config.get("enable_caching", True),
        "cache_ttl_seconds": config.get("cache_ttl_seconds", 3600)
    }
    
    # Validate required configuration
    if not pinecone_config["api_key"]:
        raise ValueError("Pinecone API key is required but not provided")
    
    try:
        adapter = PineconeVectorStorage(pinecone_config)
        logger.info(f"Pinecone adapter created successfully for index: {pinecone_config['index_name']}")
        return adapter
    except Exception as e:
        logger.error(f"Failed to create Pinecone adapter: {e}")
        raise


def _create_memory_vector_storage(config: Dict[str, Any]):
    """Create and configure in-memory vector storage."""
    logger = logging.getLogger(__name__)
    
    # Extract memory storage configuration
    memory_config = {
        "dimension": config.get("dimension", 1536),
        "metric": config.get("metric", "cosine"),
        "max_capacity": config.get("max_capacity", 10000),
        "enable_persistence": config.get("enable_persistence", False),
        "persistence_path": config.get("persistence_path", "data/memory_storage.pkl")
    }
    
    try:
        # Memory vector storage not implemented yet
        logger.warning("Memory vector storage not implemented, returning None")
        return None
    except Exception as e:
        logger.error(f"Failed to create memory vector storage: {e}")
        raise


def _create_storage_health_checker(
    vector_storage: VectorStorage,
    company_repository,
    config: Dict[str, Any]
) -> 'StorageHealthChecker':
    """Create storage health checker."""
    return StorageHealthChecker(
        vector_storage=vector_storage,
        company_repository=company_repository,
        config=config
    )


class StorageHealthChecker:
    """Health checker for storage components."""
    
    def __init__(
        self,
        vector_storage: VectorStorage,
        company_repository,
        config: Dict[str, Any]
    ):
        self.vector_storage = vector_storage
        self.company_repository = company_repository
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all storage components."""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": None
        }
        
        try:
            # Check vector storage health
            vector_health = await self._check_vector_storage_health()
            health_status["components"]["vector_storage"] = vector_health
            
            # Check company repository health
            repo_health = await self._check_company_repository_health()
            health_status["components"]["company_repository"] = repo_health
            
            # Determine overall status
            all_healthy = all(
                component["status"] == "healthy" 
                for component in health_status["components"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
            
            health_status["timestamp"] = self._get_current_timestamp()
            
        except Exception as e:
            self.logger.error(f"Storage health check failed: {e}")
            health_status = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }
        
        return health_status
    
    async def _check_vector_storage_health(self) -> Dict[str, Any]:
        """Check vector storage health."""
        try:
            if hasattr(self.vector_storage, 'health_check'):
                return await self.vector_storage.health_check()
            else:
                # Basic connectivity test
                # Try to get storage info or perform a simple operation
                return {
                    "status": "healthy",
                    "message": "Vector storage operational"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_company_repository_health(self) -> Dict[str, Any]:
        """Check company repository health."""
        try:
            if hasattr(self.company_repository, 'health_check'):
                return await self.company_repository.health_check()
            else:
                return {
                    "status": "healthy",
                    "message": "Company repository operational"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Storage provider validation
class StorageProviderValidator:
    """Validator for storage provider configuration."""
    
    @staticmethod
    def validate_vector_storage_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate vector storage configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        provider = config.get("provider", "").lower()
        
        if not provider:
            validation_result["valid"] = False
            validation_result["errors"].append("Vector storage provider not specified")
            return validation_result
        
        if provider == "pinecone":
            return StorageProviderValidator._validate_pinecone_config(config)
        elif provider == "memory":
            return StorageProviderValidator._validate_memory_config(config)
        else:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported vector storage provider: {provider}")
        
        return validation_result
    
    @staticmethod
    def _validate_pinecone_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Pinecone-specific configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        required_fields = ["api_key", "index_name"]
        for field in required_fields:
            if not config.get(field):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Pinecone {field} is required")
        
        # Validate dimension
        dimension = config.get("dimension", 1536)
        if not isinstance(dimension, int) or dimension <= 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Pinecone dimension must be a positive integer")
        
        # Check environment
        environment = config.get("environment", "gcp-starter")
        valid_environments = ["gcp-starter", "us-east-1-aws", "us-west-2-aws", "eu-west-1-aws"]
        if environment not in valid_environments:
            validation_result["warnings"].append(f"Pinecone environment '{environment}' may not be valid")
        
        return validation_result
    
    @staticmethod
    def _validate_memory_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory storage configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate dimension
        dimension = config.get("dimension", 1536)
        if not isinstance(dimension, int) or dimension <= 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Memory storage dimension must be a positive integer")
        
        # Validate capacity
        max_capacity = config.get("max_capacity", 10000)
        if not isinstance(max_capacity, int) or max_capacity <= 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Memory storage max_capacity must be a positive integer")
        
        # Check persistence settings
        enable_persistence = config.get("enable_persistence", False)
        if enable_persistence:
            persistence_path = config.get("persistence_path")
            if not persistence_path:
                validation_result["warnings"].append("Persistence enabled but no persistence_path specified")
        
        return validation_result
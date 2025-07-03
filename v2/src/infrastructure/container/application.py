"""
Theodore v2 Main Application Container.

Central dependency injection container that wires all components together
using the dependency-injector library with clean architecture principles.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .providers.config import ConfigProvider
from .providers.storage import StorageProvider
from .providers.ai_services import AIServicesProvider
from .providers.mcp_search import MCPSearchProvider
from .providers.use_cases import UseCasesProvider
from .providers.external import ExternalServicesProvider
from .lifecycle import ContainerLifecycleManager
from .health import HealthCheckAggregator


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Main application container for Theodore v2.
    
    Orchestrates all dependency injection using a layered provider approach:
    - Configuration layer (environment-aware settings)
    - Infrastructure layer (adapters and external services)
    - Domain layer (use cases and business logic)
    - Application layer (CLI, API, health checks)
    """
    
    # Container metadata - wiring disabled for initial CLI testing
    # wiring_config = containers.WiringConfiguration(
    #     modules=[
    #         "src.application.cli",
    #         "src.application.api", 
    #         "src.core.use_cases",
    #     ]
    # )
    
    # Core Configuration Provider - simplified for CLI testing
    config = providers.Configuration()
    
    # External Services Provider
    external_services = providers.Container(
        ExternalServicesProvider,
        config=config
    )
    
    # Storage Provider  
    storage = providers.Container(
        StorageProvider,
        config=config,
        external_services=external_services
    )
    
    # AI Services Provider
    ai_services = providers.Container(
        AIServicesProvider,
        config=config,
        external_services=external_services
    )
    
    # MCP Search Provider
    mcp_search = providers.Container(
        MCPSearchProvider,
        config=config,
        external_services=external_services
    )
    
    # Use Cases Provider (Domain Layer)
    use_cases = providers.Container(
        UseCasesProvider,
        storage=storage,
        ai_services=ai_services,
        mcp_search=mcp_search,
        config=config
    )
    
    # Application Services - commented out for initial CLI testing
    # lifecycle_manager = providers.Singleton(
    #     ContainerLifecycleManager,
    #     container=providers.Self(),
    #     config=config.lifecycle
    # )
    
    # health_aggregator = providers.Singleton(
    #     HealthCheckAggregator,
    #     storage=storage,
    #     ai_services=ai_services,
    #     mcp_search=mcp_search,
    #     config=config.health
    # )
    
    # Logger
    logger = providers.Singleton(
        logging.getLogger,
        name="theodore.container"
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize application container."""
        super().__init__(*args, **kwargs)
        self._initialized = False
        self._startup_tasks = []
        self._shutdown_tasks = []
    
    def init_resources(self) -> None:
        """Initialize container resources - simplified for CLI testing."""
        if self._initialized:
            return
        
        try:
            # Simplified initialization without wiring
            self._initialized = True
            self.logger().info("Container initialized successfully")
            
        except Exception as e:
            self.logger().error(f"Container initialization failed: {e}")
            raise
    
    async def startup(self) -> None:
        """Perform async startup sequence - simplified for CLI testing."""
        if not self._initialized:
            self.init_resources()
        
        self.logger().info("Starting container lifecycle")
        
        try:
            # Simplified startup - no complex lifecycle management
            self.logger().info("Container startup completed")
            
        except Exception as e:
            self.logger().error(f"Container startup failed: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Perform graceful shutdown sequence - simplified for CLI testing."""
        self.logger().info("Starting container shutdown")
        
        try:
            # Simplified shutdown
            self._initialized = False
            self.logger().info("Container shutdown completed")
            
        except Exception as e:
            self.logger().error(f"Container shutdown failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components - simplified for CLI testing."""
        if not self._initialized:
            return {
                "status": "unhealthy",
                "error": "Container not initialized"
            }
        
        try:
            # Simplified health check
            return {
                "status": "healthy",
                "message": "Container is operational"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e)
            }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate container configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Validate configuration provider
            config_provider = self.config()
            config_validation = config_provider.validate()
            
            if not config_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(config_validation["errors"])
            
            validation_result["warnings"].extend(config_validation.get("warnings", []))
            
            # Validate required providers
            required_providers = [
                "storage", "ai_services", "mcp_search", "use_cases"
            ]
            
            for provider_name in required_providers:
                try:
                    provider = getattr(self, provider_name)()
                    if hasattr(provider, 'validate'):
                        provider_validation = provider.validate()
                        if not provider_validation.get("valid", True):
                            validation_result["valid"] = False
                            validation_result["errors"].append(
                                f"{provider_name} validation failed: {provider_validation.get('error', 'Unknown error')}"
                            )
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Failed to validate {provider_name}: {e}")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Container validation failed: {e}")
        
        return validation_result
    
    def get_provider_status(self) -> Dict[str, str]:
        """Get status of all providers."""
        providers_status = {}
        
        provider_names = [
            "config", "storage", "ai_services", 
            "mcp_search", "use_cases", "external_services"
        ]
        
        for provider_name in provider_names:
            try:
                provider = getattr(self, provider_name)
                if provider.provided:
                    providers_status[provider_name] = "available"
                else:
                    providers_status[provider_name] = "not_configured"
            except Exception as e:
                providers_status[provider_name] = f"error: {e}"
        
        return providers_status
    
    # Convenience methods for accessing common components
    
    @inject
    def get_research_use_case(
        self,
        research_use_case=Provide["use_cases.research_company"]
    ):
        """Get research company use case."""
        return research_use_case
    
    @inject
    def get_discovery_use_case(
        self,
        discovery_use_case=Provide["use_cases.discover_similar"]
    ):
        """Get discover similar use case."""
        return discovery_use_case
    
    @inject
    def get_vector_storage(
        self,
        vector_storage=Provide["storage.vector_storage"]
    ):
        """Get vector storage adapter."""
        return vector_storage
    
    @inject
    def get_llm_provider(
        self,
        llm_provider=Provide["ai_services.llm_provider"]
    ):
        """Get LLM provider."""
        return llm_provider
    
    @inject
    def get_search_orchestrator(
        self,
        search_orchestrator=Provide["mcp_search.orchestrator"]
    ):
        """Get MCP search orchestrator."""
        return search_orchestrator
    
    def __str__(self) -> str:
        """String representation of container."""
        status = "initialized" if self._initialized else "not_initialized"
        providers = list(self.get_provider_status().keys())
        return f"ApplicationContainer(status={status}, providers={len(providers)})"
    
    def __repr__(self) -> str:
        """Detailed representation of container."""
        return (
            f"ApplicationContainer("
            f"initialized={self._initialized}, "
            f"providers={self.get_provider_status()}"
            f")"
        )


# Context managers for container lifecycle
class ContainerContext:
    """Async context manager for container lifecycle."""
    
    def __init__(self, container: ApplicationContainer):
        self.container = container
    
    async def __aenter__(self) -> ApplicationContainer:
        """Enter context and startup container."""
        await self.container.startup()
        return self.container
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and shutdown container."""
        await self.container.shutdown()


# Factory function for creating container with context manager
def create_container_context(
    environment: str = "development",
    config_overrides: Optional[Dict[str, Any]] = None
) -> ContainerContext:
    """
    Create container with async context manager.
    
    Usage:
        async with create_container_context() as container:
            research_use_case = container.get_research_use_case()
            result = await research_use_case.execute(request)
    """
    from . import ContainerFactory, ContainerEnvironment
    
    env = ContainerEnvironment(environment)
    container = ContainerFactory.create_container(
        environment=env,
        overrides=config_overrides
    )
    
    return ContainerContext(container)
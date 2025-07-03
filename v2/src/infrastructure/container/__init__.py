"""
Theodore v2 Dependency Injection Container.

Production-ready dependency injection system with environment-aware configuration,
lifecycle management, and comprehensive component wiring.
"""

from typing import Dict, Any, Optional, Type, Union
from enum import Enum
import asyncio
import logging
from pathlib import Path

from .application import ApplicationContainer
from .lifecycle import ContainerLifecycleManager
from .health import HealthCheckAggregator
from .overrides import TestingOverrides


class ContainerEnvironment(str, Enum):
    """Supported container environments."""
    
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    CLI = "cli"


class ContainerContext(str, Enum):
    """Container usage contexts."""
    
    CLI_APPLICATION = "cli_application"
    API_SERVER = "api_server"
    BACKGROUND_WORKER = "background_worker"
    TESTING = "testing"


class ContainerFactory:
    """
    Factory for creating environment-specific container instances.
    
    Provides centralized container creation with proper configuration,
    lifecycle management, and testing support.
    """
    
    _instances: Dict[str, ApplicationContainer] = {}
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def create_container(
        cls,
        environment: ContainerEnvironment = ContainerEnvironment.DEVELOPMENT,
        context: ContainerContext = ContainerContext.CLI_APPLICATION,
        config_path: Optional[Path] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> ApplicationContainer:
        """
        Create a configured container instance.
        
        Args:
            environment: Target environment (dev, test, prod, cli)
            context: Usage context (cli, api, worker, testing)
            config_path: Optional custom configuration path
            overrides: Optional configuration overrides
            
        Returns:
            Configured ApplicationContainer instance
            
        Raises:
            ContainerConfigurationError: If configuration is invalid
            ContainerInitializationError: If container setup fails
        """
        container_key = f"{environment.value}_{context.value}"
        
        # Return existing instance if available (singleton per env+context)
        if container_key in cls._instances:
            return cls._instances[container_key]
        
        cls._logger.info(f"Creating container for {environment.value} environment, {context.value} context")
        
        try:
            # Create container instance
            container = ApplicationContainer()
            
            # Configure for environment
            cls._configure_environment(container, environment, config_path)
            
            # Configure for context
            cls._configure_context(container, context)
            
            # Apply overrides if provided
            if overrides:
                cls._apply_overrides(container, overrides)
            
            # Initialize container
            container.init_resources()
            
            # Store instance
            cls._instances[container_key] = container
            
            cls._logger.info(f"Container created successfully: {container_key}")
            return container
            
        except Exception as e:
            cls._logger.error(f"Failed to create container {container_key}: {e}")
            raise ContainerInitializationError(f"Container creation failed: {e}") from e
    
    @classmethod
    def create_cli_container(
        cls,
        environment: ContainerEnvironment = ContainerEnvironment.CLI,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> ApplicationContainer:
        """
        Create container optimized for CLI usage.
        
        Args:
            environment: Environment configuration
            config_overrides: Optional configuration overrides
            
        Returns:
            CLI-optimized container
        """
        return cls.create_container(
            environment=environment,
            context=ContainerContext.CLI_APPLICATION,
            overrides=config_overrides
        )
    
    @classmethod
    def create_api_container(
        cls,
        environment: ContainerEnvironment = ContainerEnvironment.PRODUCTION,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> ApplicationContainer:
        """
        Create container optimized for API server usage.
        
        Args:
            environment: Environment configuration
            config_overrides: Optional configuration overrides
            
        Returns:
            API-optimized container
        """
        return cls.create_container(
            environment=environment,
            context=ContainerContext.API_SERVER,
            overrides=config_overrides
        )
    
    @classmethod
    def create_test_container(
        cls,
        test_overrides: Optional[Dict[str, Any]] = None
    ) -> ApplicationContainer:
        """
        Create container for testing with mocked dependencies.
        
        Args:
            test_overrides: Testing-specific overrides
            
        Returns:
            Test-optimized container with mocked dependencies
        """
        # Combine default test overrides with provided ones
        default_overrides = TestingOverrides.get_default_overrides()
        if test_overrides:
            default_overrides.update(test_overrides)
        
        return cls.create_container(
            environment=ContainerEnvironment.TESTING,
            context=ContainerContext.TESTING,
            overrides=default_overrides
        )
    
    @classmethod
    def create_worker_container(
        cls,
        environment: ContainerEnvironment = ContainerEnvironment.PRODUCTION,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> ApplicationContainer:
        """
        Create container optimized for background worker usage.
        
        Args:
            environment: Environment configuration
            config_overrides: Optional configuration overrides
            
        Returns:
            Worker-optimized container
        """
        return cls.create_container(
            environment=environment,
            context=ContainerContext.BACKGROUND_WORKER,
            overrides=config_overrides
        )
    
    @classmethod
    def _configure_environment(
        cls,
        container: ApplicationContainer,
        environment: ContainerEnvironment,
        config_path: Optional[Path]
    ) -> None:
        """Configure container for specific environment."""
        if config_path:
            config_file = config_path
        else:
            config_file = Path(f"config/environments/{environment.value}.yml")
        
        # Load environment-specific configuration
        if config_file.exists():
            container.config.from_yaml(str(config_file))
        else:
            cls._logger.warning(f"Configuration file not found: {config_file}")
        
        # Set environment-specific providers
        if environment == ContainerEnvironment.TESTING:
            cls._configure_testing_environment(container)
        elif environment == ContainerEnvironment.PRODUCTION:
            cls._configure_production_environment(container)
        elif environment == ContainerEnvironment.CLI:
            cls._configure_cli_environment(container)
    
    @classmethod
    def _configure_context(
        cls,
        container: ApplicationContainer,
        context: ContainerContext
    ) -> None:
        """Configure container for specific usage context."""
        if context == ContainerContext.API_SERVER:
            # Enable API-specific providers
            pass
        elif context == ContainerContext.CLI_APPLICATION:
            # Enable CLI-specific providers
            pass
        elif context == ContainerContext.BACKGROUND_WORKER:
            # Enable worker-specific providers
            pass
        elif context == ContainerContext.TESTING:
            # Enable testing-specific providers
            pass
    
    @classmethod
    def _configure_testing_environment(cls, container: ApplicationContainer) -> None:
        """Configure container for testing environment."""
        # Override with in-memory/mock providers
        container.config.vector_storage.provider.override("memory")
        container.config.llm_provider.primary.override("mock")
    
    @classmethod
    def _configure_production_environment(cls, container: ApplicationContainer) -> None:
        """Configure container for production environment."""
        # Ensure production-ready configurations
        container.config.logging.level.override("INFO")
        container.config.monitoring.enabled.override(True)
    
    @classmethod
    def _configure_cli_environment(cls, container: ApplicationContainer) -> None:
        """Configure container for CLI environment."""
        # CLI-specific optimizations
        container.config.logging.level.override("WARNING")  # Quieter logging
        container.config.api_server.enabled.override(False)  # Disable API server
    
    @classmethod
    def _apply_overrides(
        cls,
        container: ApplicationContainer,
        overrides: Dict[str, Any]
    ) -> None:
        """Apply configuration overrides to container."""
        for key, value in overrides.items():
            if hasattr(container.config, key):
                getattr(container.config, key).override(value)
            else:
                cls._logger.warning(f"Unknown configuration override: {key}")
    
    @classmethod
    async def shutdown_all_containers(cls) -> None:
        """Shutdown all created container instances."""
        shutdown_tasks = []
        
        for container_key, container in cls._instances.items():
            cls._logger.info(f"Shutting down container: {container_key}")
            shutdown_tasks.append(cls._shutdown_container(container))
        
        # Wait for all containers to shutdown
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        # Clear instances
        cls._instances.clear()
        cls._logger.info("All containers shut down successfully")
    
    @classmethod
    async def _shutdown_container(cls, container: ApplicationContainer) -> None:
        """Shutdown a single container instance."""
        try:
            await container.shutdown()
        except Exception as e:
            cls._logger.error(f"Error shutting down container: {e}")
    
    @classmethod
    def get_container(
        cls,
        environment: ContainerEnvironment,
        context: ContainerContext
    ) -> Optional[ApplicationContainer]:
        """Get existing container instance if available."""
        container_key = f"{environment.value}_{context.value}"
        return cls._instances.get(container_key)
    
    @classmethod
    def list_containers(cls) -> Dict[str, ApplicationContainer]:
        """List all created container instances."""
        return cls._instances.copy()


class ContainerConfigurationError(Exception):
    """Raised when container configuration is invalid."""
    pass


class ContainerInitializationError(Exception):
    """Raised when container initialization fails."""
    pass


# Public API exports
__all__ = [
    "ContainerFactory",
    "ContainerEnvironment", 
    "ContainerContext",
    "ApplicationContainer",
    "ContainerLifecycleManager",
    "HealthCheckAggregator",
    "TestingOverrides",
    "ContainerConfigurationError",
    "ContainerInitializationError"
]

# Convenience functions for common use cases
def create_cli_container(**kwargs) -> ApplicationContainer:
    """Create CLI container with default settings."""
    return ContainerFactory.create_cli_container(**kwargs)

def create_api_container(**kwargs) -> ApplicationContainer:
    """Create API container with default settings."""
    return ContainerFactory.create_api_container(**kwargs)

def create_test_container(**kwargs) -> ApplicationContainer:
    """Create test container with mocked dependencies."""
    return ContainerFactory.create_test_container(**kwargs)

async def shutdown_containers() -> None:
    """Shutdown all container instances."""
    await ContainerFactory.shutdown_all_containers()
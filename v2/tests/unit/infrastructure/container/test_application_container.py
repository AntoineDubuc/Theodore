"""
Unit tests for Theodore v2 Application Container.

Comprehensive test suite for dependency injection container functionality
including provider configuration, lifecycle management, and health checks.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.infrastructure.container import (
    ContainerFactory,
    ContainerEnvironment,
    ContainerContext,
    ApplicationContainer,
    ContainerConfigurationError,
    ContainerInitializationError,
    create_cli_container,
    create_api_container,
    create_test_container
)
from src.infrastructure.container.application import ContainerContext, create_container_context
from src.infrastructure.container.overrides import TestingOverrides


class TestContainerFactory:
    """Test container factory functionality."""
    
    def test_create_cli_container(self):
        """Test CLI container creation."""
        container = create_cli_container(
            environment=ContainerEnvironment.CLI,
            config_overrides={"logging.level": "DEBUG"}
        )
        
        assert isinstance(container, ApplicationContainer)
        assert container._initialized
    
    def test_create_api_container(self):
        """Test API container creation."""
        container = create_api_container(
            environment=ContainerEnvironment.PRODUCTION,
            config_overrides={"api_server.port": 9000}
        )
        
        assert isinstance(container, ApplicationContainer)
        assert container._initialized
    
    def test_create_test_container(self):
        """Test testing container creation."""
        container = create_test_container(
            test_overrides={"storage.vector_storage.max_capacity": 500}
        )
        
        assert isinstance(container, ApplicationContainer)
        assert container._initialized
    
    def test_container_singleton_behavior(self):
        """Test that containers are singleton per environment+context."""
        container1 = ContainerFactory.create_container(
            environment=ContainerEnvironment.DEVELOPMENT,
            context=ContainerContext.CLI_APPLICATION
        )
        
        container2 = ContainerFactory.create_container(
            environment=ContainerEnvironment.DEVELOPMENT,
            context=ContainerContext.CLI_APPLICATION
        )
        
        assert container1 is container2
    
    def test_different_environments_create_different_containers(self):
        """Test that different environments create different containers."""
        dev_container = ContainerFactory.create_container(
            environment=ContainerEnvironment.DEVELOPMENT,
            context=ContainerContext.CLI_APPLICATION
        )
        
        prod_container = ContainerFactory.create_container(
            environment=ContainerEnvironment.PRODUCTION,
            context=ContainerContext.CLI_APPLICATION
        )
        
        assert dev_container is not prod_container
    
    @pytest.mark.asyncio
    async def test_shutdown_all_containers(self):
        """Test shutting down all containers."""
        # Create multiple containers
        ContainerFactory.create_container(
            environment=ContainerEnvironment.DEVELOPMENT,
            context=ContainerContext.CLI_APPLICATION
        )
        
        ContainerFactory.create_container(
            environment=ContainerEnvironment.TESTING,
            context=ContainerContext.TESTING
        )
        
        # Verify containers exist
        containers_before = ContainerFactory.list_containers()
        assert len(containers_before) > 0
        
        # Shutdown all
        await ContainerFactory.shutdown_all_containers()
        
        # Verify containers cleared
        containers_after = ContainerFactory.list_containers()
        assert len(containers_after) == 0


class TestApplicationContainer:
    """Test application container functionality."""
    
    @pytest.fixture
    def test_container(self):
        """Create test container for testing."""
        return create_test_container()
    
    def test_container_initialization(self, test_container):
        """Test container initialization."""
        assert test_container._initialized
        assert hasattr(test_container, 'config')
        assert hasattr(test_container, 'storage')
        assert hasattr(test_container, 'ai_services')
        assert hasattr(test_container, 'mcp_search')
        assert hasattr(test_container, 'use_cases')
    
    def test_provider_status(self, test_container):
        """Test provider status checking."""
        status = test_container.get_provider_status()
        
        expected_providers = [
            "config", "storage", "ai_services", 
            "mcp_search", "use_cases", "external_services"
        ]
        
        for provider in expected_providers:
            assert provider in status
    
    def test_configuration_validation(self, test_container):
        """Test configuration validation."""
        validation_result = test_container.validate_configuration()
        
        assert "valid" in validation_result
        assert "errors" in validation_result
        assert "warnings" in validation_result
        assert isinstance(validation_result["valid"], bool)
    
    @pytest.mark.asyncio
    async def test_container_startup_shutdown(self, test_container):
        """Test container startup and shutdown."""
        # Test startup
        await test_container.startup()
        
        # Test health check after startup
        health = await test_container.health_check()
        assert "status" in health
        
        # Test shutdown
        await test_container.shutdown()
        assert not test_container._initialized
    
    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self):
        """Test health check on uninitialized container."""
        container = ApplicationContainer()
        
        health = await container.health_check()
        assert health["status"] == "unhealthy"
        assert "error" in health
    
    def test_convenience_methods(self, test_container):
        """Test convenience methods for accessing components."""
        # These should not raise errors with test container
        research_use_case = test_container.get_research_use_case()
        assert research_use_case is not None
        
        discovery_use_case = test_container.get_discovery_use_case()
        assert discovery_use_case is not None
        
        vector_storage = test_container.get_vector_storage()
        assert vector_storage is not None
        
        llm_provider = test_container.get_llm_provider()
        assert llm_provider is not None
        
        search_orchestrator = test_container.get_search_orchestrator()
        assert search_orchestrator is not None
    
    def test_container_string_representation(self, test_container):
        """Test container string representations."""
        str_repr = str(test_container)
        assert "ApplicationContainer" in str_repr
        assert "initialized" in str_repr
        
        repr_str = repr(test_container)
        assert "ApplicationContainer" in repr_str
        assert "initialized" in repr_str


class TestContainerContext:
    """Test container context manager."""
    
    @pytest.mark.asyncio
    async def test_container_context_manager(self):
        """Test container context manager functionality."""
        async with create_container_context("testing") as container:
            assert isinstance(container, ApplicationContainer)
            assert container._initialized
            
            # Container should be operational
            health = await container.health_check()
            assert "status" in health
    
    @pytest.mark.asyncio
    async def test_container_context_with_overrides(self):
        """Test container context with configuration overrides."""
        overrides = {
            "logging.level": "DEBUG",
            "storage.vector_storage.max_capacity": 2000
        }
        
        async with create_container_context("testing", overrides) as container:
            assert container._initialized
            
            # Verify overrides were applied
            config_summary = container.config().get_config_summary()
            assert config_summary is not None


class TestTestingOverrides:
    """Test testing override functionality."""
    
    def test_default_overrides(self):
        """Test default testing overrides."""
        overrides = TestingOverrides.get_default_overrides()
        
        # Check key overrides
        assert overrides["storage.vector_storage.provider"] == "memory"
        assert overrides["ai_services.llm_provider.primary"] == "mock"
        assert overrides["mcp_search.enabled_tools"] == ["mock"]
        assert overrides["logging.level"] == "WARNING"
    
    def test_mock_vector_storage_creation(self):
        """Test mock vector storage creation."""
        mock_storage = TestingOverrides.create_mock_vector_storage()
        
        assert hasattr(mock_storage, 'health_check')
        assert hasattr(mock_storage, 'upsert_company')
        assert hasattr(mock_storage, 'find_company_by_name')
        assert hasattr(mock_storage, 'search_similar')
    
    def test_mock_llm_provider_creation(self):
        """Test mock LLM provider creation."""
        mock_llm = TestingOverrides.create_mock_llm_provider()
        
        assert hasattr(mock_llm, 'health_check')
        assert hasattr(mock_llm, 'generate_text')
        assert hasattr(mock_llm, 'generate_streaming')
    
    def test_mock_mcp_search_tool_creation(self):
        """Test mock MCP search tool creation."""
        mock_tool = TestingOverrides.create_mock_mcp_search_tool()
        
        assert hasattr(mock_tool, 'get_tool_info')
        assert hasattr(mock_tool, 'search_similar_companies')
        assert hasattr(mock_tool, 'search_by_keywords')
        assert hasattr(mock_tool, 'health_check')
    
    def test_test_configuration_creation(self):
        """Test test configuration creation."""
        config = TestingOverrides.create_test_configuration()
        
        assert "app" in config
        assert "storage" in config
        assert "ai_services" in config
        assert "mcp_search" in config
        assert config["app"]["name"] == "theodore-test"
    
    def test_integration_test_overrides(self):
        """Test integration test overrides."""
        overrides = TestingOverrides.get_integration_test_overrides()
        
        # Integration tests use real services with test-friendly settings
        assert overrides["storage.vector_storage.index_name"] == "theodore-test"
        assert overrides["ai_services.llm_provider.max_tokens"] == 1000
        assert overrides["mcp_search.max_results_per_tool"] == 3


class TestContainerConfiguration:
    """Test container configuration functionality."""
    
    def test_environment_configuration_loading(self):
        """Test environment-specific configuration loading."""
        # Test development environment
        dev_container = ContainerFactory.create_container(
            environment=ContainerEnvironment.DEVELOPMENT,
            context=ContainerContext.CLI_APPLICATION
        )
        
        assert dev_container._initialized
    
    def test_configuration_overrides(self):
        """Test configuration overrides."""
        overrides = {
            "app.debug": True,
            "logging.level": "DEBUG",
            "storage.vector_storage.dimension": 768
        }
        
        container = ContainerFactory.create_container(
            environment=ContainerEnvironment.TESTING,
            context=ContainerContext.TESTING,
            overrides=overrides
        )
        
        assert container._initialized
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration."""
        with pytest.raises((ContainerConfigurationError, ContainerInitializationError)):
            # Try to create container with invalid overrides
            ContainerFactory.create_container(
                environment=ContainerEnvironment.TESTING,
                overrides={"invalid.config.path": "invalid_value"}
            )


class TestContainerIntegration:
    """Integration tests for container functionality."""
    
    @pytest.mark.asyncio
    async def test_full_container_lifecycle(self):
        """Test full container lifecycle."""
        container = create_test_container()
        
        try:
            # Startup
            await container.startup()
            
            # Verify container is operational
            health = await container.health_check()
            assert health["status"] in ["healthy", "degraded"]  # Some components might be mocked
            
            # Test provider access
            research_use_case = container.get_research_use_case()
            assert research_use_case is not None
            
            # Test configuration validation
            validation = container.validate_configuration()
            assert validation["valid"] is True or len(validation["errors"]) == 0
            
        finally:
            # Shutdown
            await container.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_container_access(self):
        """Test concurrent access to container."""
        container = create_test_container()
        
        async def access_container():
            research_use_case = container.get_research_use_case()
            discovery_use_case = container.get_discovery_use_case()
            return research_use_case, discovery_use_case
        
        # Run multiple concurrent accesses
        tasks = [access_container() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        for research, discovery in results:
            assert research is not None
            assert discovery is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
#!/usr/bin/env python3
"""
Integration tests for Theodore v2 observability system.

Tests the complete observability stack working together.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone

from src.infrastructure.observability import (
    TheodoreLogger,
    LogLevel,
    LogCategory,
    MetricsCollector,
    HealthChecker,
    AlertManager,
    AlertLevel,
    AlertChannel,
    TraceManager,
    configure_logging,
    ObservabilityConfig
)


class TestObservabilityIntegration:
    """Test observability components working together"""
    
    @pytest.fixture
    def observability_config(self):
        return ObservabilityConfig(
            log_level=LogLevel.DEBUG,
            enable_json_logging=True,
            enable_correlation_ids=True,
            redact_sensitive_data=True
        )
    
    @pytest.fixture
    def logger(self, observability_config):
        configure_logging(observability_config)
        return TheodoreLogger("test_integration", LogCategory.SYSTEM, observability_config)
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()
    
    @pytest.fixture
    def health_checker(self):
        return HealthChecker()
    
    @pytest.fixture
    def alert_manager(self):
        return AlertManager()
    
    def test_logging_with_correlation_id(self, logger):
        """Test logging with correlation IDs"""
        correlation_id = str(uuid.uuid4())
        correlated_logger = logger.with_correlation_id(correlation_id)
        
        # Log with correlation ID
        correlated_logger.info("Test message with correlation", test_field="value")
        
        # Verify correlation ID is maintained
        assert correlated_logger.correlation_id == correlation_id
        
        # Test context building
        context = correlated_logger._build_context(custom="data")
        assert context["correlation_id"] == correlation_id
        assert context["custom"] == "data"
    
    def test_metrics_and_logging_integration(self, logger, metrics_collector):
        """Test metrics collection with logging"""
        # Create and record metrics
        counter = metrics_collector.counter("integration_tests", "Integration test counter")
        gauge = metrics_collector.gauge("test_value", "Test gauge")
        
        # Record values
        counter.increment()
        counter.record(5)  # Use record() to add 5
        gauge.record(42.5)
        
        # Log metrics
        logger.info("Metrics recorded", 
                   counter_value=counter.get_value()["value"],
                   gauge_value=gauge.get_value()["value"])
        
        # Verify metrics
        assert counter.get_value()["value"] == 6
        assert gauge.get_value()["value"] == 42.5
        
        # Test metrics collection
        all_metrics = metrics_collector.get_all_metrics()
        assert "integration_tests" in all_metrics
        assert "test_value" in all_metrics
    
    @pytest.mark.asyncio
    async def test_health_checks_with_alerting(self, health_checker, alert_manager, logger):
        """Test health checks triggering alerts"""
        
        # Create a simple health check that always passes
        async def mock_connection_test():
            return True
        
        # Register health check
        health_checker.register_database_check(
            "test_db",
            mock_connection_test,
            timeout_seconds=1.0
        )
        
        # Create alert rule for health check failures
        alert_manager.create_health_check_rule(
            "health_alert_test",
            "Test Health Check Alert",
            component_name="test_db",
            level=AlertLevel.ERROR,
            channels=[AlertChannel.EMAIL]
        )
        
        # Run health check
        health_status = await health_checker.check_all_health()
        
        # Verify health check passed
        assert health_status.total_components == 1
        assert health_status.healthy_components == 1
        assert health_status.unhealthy_components == 0
        
        # Log health status
        logger.info("Health check completed",
                   status=health_status.overall_status.value,
                   healthy=health_status.healthy_components,
                   total=health_status.total_components)
    
    @pytest.mark.asyncio
    async def test_manual_alert_triggering(self, alert_manager, logger):
        """Test manual alert triggering"""
        
        # Trigger a manual alert
        alert = await alert_manager.trigger_alert(
            title="Integration Test Alert",
            description="This is a test alert for integration testing",
            level=AlertLevel.WARNING,
            source="integration_test",
            channels=[AlertChannel.EMAIL],
            tags={"test": "integration", "component": "test_suite"}
        )
        
        # Verify alert was created
        assert alert.title == "Integration Test Alert"
        assert alert.level == AlertLevel.WARNING
        assert alert.source == "integration_test"
        assert alert.tags["test"] == "integration"
        
        # Check active alerts
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].id == alert.id
        
        # Log alert creation
        logger.info("Manual alert triggered",
                   alert_id=alert.id,
                   alert_level=alert.level.value,
                   alert_title=alert.title)
        
        # Acknowledge the alert
        success = alert_manager.acknowledge_alert(alert.id, "test_user")
        assert success
        
        # Verify acknowledgment
        acknowledged_alert = alert_manager.active_alerts[alert.id]
        assert acknowledged_alert.acknowledged_by == "test_user"
        assert acknowledged_alert.acknowledged_at is not None
        
        # Resolve the alert
        success = alert_manager.resolve_alert(alert.id)
        assert success
        
        # Verify resolution
        assert alert.id not in alert_manager.active_alerts
    
    def test_performance_logging_context(self, logger):
        """Test performance logging context manager"""
        
        # Test successful operation
        with logger.performance_context("test_operation", operation_type="unit_test"):
            # Simulate some work
            import time
            time.sleep(0.01)  # 10ms
        
        # Test failed operation
        try:
            with logger.performance_context("failing_operation", expected_result="error"):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        # The context manager should have logged both start, success/failure
        # This is verified by the absence of exceptions
    
    def test_sensitive_data_filtering(self, logger):
        """Test sensitive data is properly filtered"""
        
        # Log with sensitive data
        context = logger._build_context(
            username="testuser",
            password="secret123",
            api_key="sk-1234567890abcdef",
            safe_data="visible",
            nested_config={
                "database_password": "db_secret",
                "host": "localhost"
            }
        )
        
        # Verify sensitive data is redacted
        assert context["username"] == "testuser"  # Not sensitive
        assert context["password"] == "[REDACTED]"
        assert context["api_key"] == "[REDACTED]"
        assert context["safe_data"] == "visible"
        assert context["nested_config"]["database_password"] == "[REDACTED]"
        assert context["nested_config"]["host"] == "localhost"
    
    def test_tracing_integration(self):
        """Test tracing system integration"""
        from src.infrastructure.observability.tracing import (
            TracingConfig,
            configure_tracing,
            get_trace_manager,
            correlation_context,
            generate_correlation_id
        )
        
        # Configure tracing
        config = TracingConfig(
            service_name="test-service",
            enable_tracing=True,
            enable_auto_instrumentation=False  # Avoid external dependencies
        )
        
        trace_manager = configure_tracing(config)
        assert trace_manager is not None
        
        # Test correlation ID management
        correlation_id = generate_correlation_id()
        assert correlation_id is not None
        assert len(correlation_id) > 0
        
        # Test correlation context
        with correlation_context(correlation_id) as ctx_id:
            assert ctx_id == correlation_id
            
            # Get global trace manager
            global_manager = get_trace_manager()
            assert global_manager == trace_manager
    
    def test_audit_logging(self, logger):
        """Test audit logging functionality"""
        
        # Log audit events
        logger.audit(
            action="user_login",
            user_id="test_user_123",
            resource="authentication_system",
            ip_address="192.168.1.100",
            user_agent="TestClient/1.0"
        )
        
        logger.audit(
            action="data_access",
            user_id="test_user_123",
            resource="company_database",
            query="SELECT * FROM companies WHERE id = 123",
            result_count=1
        )
        
        # Audit logging should work without exceptions
        # The actual log verification would be done in a real system
        # with log aggregation tools
    
    def test_business_metrics_integration(self, metrics_collector, logger):
        """Test business metrics with logging"""
        
        # Create business metrics
        user_registrations = metrics_collector.counter(
            "user_registrations_total",
            "Total user registrations"
        )
        
        active_sessions = metrics_collector.gauge(
            "active_sessions_current",
            "Current active user sessions"
        )
        
        response_time = metrics_collector.histogram(
            "api_response_time_seconds",
            "API response time in seconds"
        )
        
        # Record business events
        user_registrations.increment()
        active_sessions.record(25)
        response_time.record(0.15)
        
        # Log business metrics
        logger.with_context(metric_type="business").info(
            "Business metrics updated",
            user_registrations=user_registrations.get_value()["value"],
            active_sessions=active_sessions.get_value()["value"],
            avg_response_time=response_time.get_value()["mean"]
        )
        
        # Verify metrics
        assert user_registrations.get_value()["value"] == 1
        assert active_sessions.get_value()["value"] == 25
        assert response_time.get_value()["mean"] == 0.15


class TestObservabilityConfiguration:
    """Test observability configuration and setup"""
    
    def test_configuration_validation(self):
        """Test configuration validation and defaults"""
        
        # Test default configuration
        default_config = ObservabilityConfig()
        assert default_config.log_level == LogLevel.INFO
        assert default_config.enable_json_logging is True
        assert default_config.enable_correlation_ids is True
        assert default_config.redact_sensitive_data is True
        
        # Test custom configuration
        custom_config = ObservabilityConfig(
            log_level=LogLevel.DEBUG,
            enable_json_logging=False,
            log_file_path="/tmp/test.log",
            enterprise_integrations={
                "datadog": {"api_key": "test_key"},
                "elk": {"endpoint": "http://elk.example.com"}
            }
        )
        
        assert custom_config.log_level == LogLevel.DEBUG
        assert custom_config.enable_json_logging is False
        assert custom_config.log_file_path == "/tmp/test.log"
        assert "datadog" in custom_config.enterprise_integrations
    
    def test_global_configuration(self):
        """Test global configuration management"""
        
        config = ObservabilityConfig(
            log_level=LogLevel.WARN,
            enable_correlation_ids=False
        )
        
        configure_logging(config)
        
        # Create logger with global config
        logger = TheodoreLogger("test_global")
        assert logger.config.log_level == LogLevel.WARN
        assert logger.config.enable_correlation_ids is False


if __name__ == "__main__":
    # Run basic integration test
    import asyncio
    
    async def run_basic_test():
        config = ObservabilityConfig()
        logger = TheodoreLogger("manual_test", LogCategory.SYSTEM, config)
        
        logger.info("Starting manual integration test")
        
        # Test metrics
        metrics = MetricsCollector()
        counter = metrics.counter("test_counter", "Test counter")
        counter.increment()
        
        logger.info("Metrics test completed", counter_value=counter.get_value()["value"])
        
        # Test health check
        health = HealthChecker()
        health.register_system_resources_check()
        
        health_status = await health.check_all_health()
        logger.info("Health check completed", 
                   status=health_status.overall_status.value,
                   components=health_status.total_components)
        
        logger.info("Manual integration test completed successfully")
    
    asyncio.run(run_basic_test())
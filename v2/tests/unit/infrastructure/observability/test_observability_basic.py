#!/usr/bin/env python3
"""
Basic unit tests for Theodore v2 observability system.

Tests core functionality without external dependencies.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.infrastructure.observability.logging import (
    LogLevel,
    LogCategory,
    SensitiveDataFilter,
    ObservabilityConfig,
    TheodoreLogger
)

from src.infrastructure.observability.metrics import (
    MetricType,
    MetricUnit,
    Counter,
    Gauge,
    MetricsRegistry
)

from src.infrastructure.observability.health import (
    HealthStatus,
    ComponentType,
    HealthCheckResult
)

from src.infrastructure.observability.alerting import (
    AlertLevel,
    AlertChannel,
    Alert
)


class TestLogLevelsAndCategories:
    """Test log levels and categories enums"""
    
    def test_log_levels_defined(self):
        """Test all expected log levels are defined"""
        expected_levels = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL", "AUDIT"}
        actual_levels = {level.value.upper() for level in LogLevel}
        
        assert expected_levels.issubset(actual_levels)
    
    def test_log_categories_defined(self):
        """Test all expected log categories are defined"""
        expected_categories = {
            "system", "security", "audit", "performance", "business"
        }
        actual_categories = {cat.value for cat in LogCategory}
        
        assert expected_categories.issubset(actual_categories)


class TestSensitiveDataFilter:
    """Test sensitive data filtering"""
    
    def test_filter_password_fields(self):
        """Test filtering of password and secret fields"""
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "sk-1234567890",
            "safe_field": "visible_data"
        }
        
        filtered = SensitiveDataFilter.filter_sensitive_data(data)
        
        assert filtered["username"] == "testuser"
        assert filtered["password"] == "[REDACTED]"
        assert filtered["api_key"] == "[REDACTED]"
        assert filtered["safe_field"] == "visible_data"
    
    def test_filter_nested_data(self):
        """Test filtering of nested sensitive data"""
        data = {
            "config": {
                "database": {
                    "password": "db_secret",
                    "host": "localhost"
                }
            }
        }
        
        filtered = SensitiveDataFilter.filter_sensitive_data(data)
        
        assert filtered["config"]["database"]["password"] == "[REDACTED]"
        assert filtered["config"]["database"]["host"] == "localhost"


class TestObservabilityConfig:
    """Test observability configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ObservabilityConfig()
        
        assert config.log_level == LogLevel.INFO
        assert config.enable_json_logging is True
        assert config.enable_correlation_ids is True
        assert config.redact_sensitive_data is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = ObservabilityConfig(
            log_level=LogLevel.DEBUG,
            enable_json_logging=False,
            log_file_path="/tmp/test.log"
        )
        
        assert config.log_level == LogLevel.DEBUG
        assert config.enable_json_logging is False
        assert config.log_file_path == "/tmp/test.log"


class TestTheodoreLogger:
    """Test Theodore logger (basic functionality)"""
    
    @pytest.fixture
    def config(self):
        return ObservabilityConfig()
    
    @pytest.fixture
    def logger(self, config):
        return TheodoreLogger("test_component", LogCategory.SYSTEM, config)
    
    def test_logger_creation(self, logger):
        """Test logger creation"""
        assert logger.component == "test_component"
        assert logger.category == LogCategory.SYSTEM
        assert logger.correlation_id is None
    
    def test_with_correlation_id(self, logger):
        """Test correlation ID context"""
        correlation_id = str(uuid.uuid4())
        logger_with_id = logger.with_correlation_id(correlation_id)
        
        assert logger_with_id.correlation_id == correlation_id
        assert logger_with_id.component == logger.component
        assert logger.correlation_id is None  # Original unchanged
    
    def test_with_context(self, logger):
        """Test context addition"""
        context_logger = logger.with_context(
            user_id="test_user",
            operation="test_operation"
        )
        
        assert context_logger._context["user_id"] == "test_user"
        assert context_logger._context["operation"] == "test_operation"
    
    def test_build_context(self, logger):
        """Test context building"""
        context = logger._build_context(
            custom_field="test_value",
            user_id="test_user"
        )
        
        assert context["component"] == "test_component"
        assert context["category"] == LogCategory.SYSTEM.value
        assert context["custom_field"] == "test_value"
        assert context["user_id"] == "test_user"
        assert "timestamp" in context
        assert "environment" in context


class TestMetrics:
    """Test metrics system"""
    
    def test_metric_types_defined(self):
        """Test metric types are defined"""
        expected_types = {"COUNTER", "GAUGE", "HISTOGRAM", "TIMER"}
        actual_types = {mt.value.upper() for mt in MetricType}
        
        assert expected_types.issubset(actual_types)
    
    def test_metric_units_defined(self):
        """Test metric units are defined"""
        expected_units = {"seconds", "bytes", "count", "percent"}
        actual_units = {unit.value for unit in MetricUnit if unit.value}
        
        assert expected_units.issubset(actual_units)
    
    def test_counter_basic(self):
        """Test basic counter functionality"""
        counter = Counter("test_counter", "Test counter")
        
        assert counter.name == "test_counter"
        assert counter.get_value()["value"] == 0.0
        
        counter.record(5)
        assert counter.get_value()["value"] == 5.0
        
        counter.increment()
        assert counter.get_value()["value"] == 6.0
    
    def test_counter_negative_value(self):
        """Test counter rejects negative values"""
        counter = Counter("test_counter", "Test counter")
        
        with pytest.raises(ValueError):
            counter.record(-1)
    
    def test_gauge_basic(self):
        """Test basic gauge functionality"""
        gauge = Gauge("test_gauge", "Test gauge")
        
        assert gauge.name == "test_gauge"
        assert gauge.get_value()["value"] == 0.0
        
        gauge.record(10.5)
        assert gauge.get_value()["value"] == 10.5
        
        gauge.increment(2.5)
        assert gauge.get_value()["value"] == 13.0
        
        gauge.decrement(3.0)
        assert gauge.get_value()["value"] == 10.0
    
    def test_metrics_registry(self):
        """Test metrics registry"""
        registry = MetricsRegistry()
        
        # Test counter creation
        counter = registry.counter("test_counter", "Test counter")
        assert isinstance(counter, Counter)
        assert counter.name == "test_counter"
        
        # Test gauge creation
        gauge = registry.gauge("test_gauge", "Test gauge")
        assert isinstance(gauge, Gauge)
        assert gauge.name == "test_gauge"
        
        # Test retrieval
        assert registry.get_metric("test_counter") == counter
        assert registry.get_metric("test_gauge") == gauge
        assert registry.get_metric("nonexistent") is None
        
        # Test duplicate registration
        with pytest.raises(ValueError):
            registry.register(Counter("test_counter", "Duplicate"))
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        registry = MetricsRegistry()
        
        counter = registry.counter("requests", "Request count")
        gauge = registry.gauge("memory", "Memory usage")
        
        counter.record(100)
        gauge.record(75.5)
        
        all_metrics = registry.collect_all()
        
        assert "requests" in all_metrics
        assert "memory" in all_metrics
        assert all_metrics["requests"]["value"] == 100
        assert all_metrics["memory"]["value"] == 75.5


class TestHealthChecks:
    """Test health check system"""
    
    def test_health_status_enum(self):
        """Test health status enum"""
        expected_statuses = {"healthy", "degraded", "unhealthy", "unknown"}
        actual_statuses = {status.value for status in HealthStatus}
        
        assert expected_statuses == actual_statuses
    
    def test_component_types_defined(self):
        """Test component types are defined"""
        expected_types = {"database", "ai_service", "external_api", "system_resource"}
        actual_types = {ct.value for ct in ComponentType}
        
        assert expected_types.issubset(actual_types)
    
    def test_health_check_result(self):
        """Test health check result creation"""
        result = HealthCheckResult(
            component_name="test_component",
            component_type=ComponentType.DATABASE,
            status=HealthStatus.HEALTHY,
            message="Database is healthy",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert result.component_name == "test_component"
        assert result.component_type == ComponentType.DATABASE
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Database is healthy"
        assert result.response_time_ms is None


class TestAlerting:
    """Test alerting system"""
    
    def test_alert_levels_defined(self):
        """Test alert levels are defined"""
        expected_levels = {"info", "warning", "error", "critical"}
        actual_levels = {level.value for level in AlertLevel}
        
        assert expected_levels == actual_levels
    
    def test_alert_channels_defined(self):
        """Test alert channels are defined"""
        expected_channels = {"email", "slack", "webhook"}
        actual_channels = {channel.value for channel in AlertChannel}
        
        assert expected_channels.issubset(actual_channels)
    
    def test_alert_creation(self):
        """Test alert creation"""
        alert = Alert(
            id="test_alert_123",
            title="Test Alert",
            description="This is a test alert",
            level=AlertLevel.WARNING,
            source="test_system",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert alert.id == "test_alert_123"
        assert alert.title == "Test Alert"
        assert alert.level == AlertLevel.WARNING
        assert alert.source == "test_system"
    
    def test_alert_to_dict(self):
        """Test alert serialization"""
        timestamp = datetime.now(timezone.utc)
        alert = Alert(
            id="test_alert_123",
            title="Test Alert",
            description="This is a test alert",
            level=AlertLevel.ERROR,
            source="test_system",
            timestamp=timestamp,
            tags={"component": "database"}
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["id"] == "test_alert_123"
        assert alert_dict["title"] == "Test Alert"
        assert alert_dict["level"] == "error"
        assert alert_dict["source"] == "test_system"
        assert alert_dict["tags"]["component"] == "database"
        assert alert_dict["timestamp"] == timestamp.isoformat()


class TestIntegration:
    """Integration tests without external dependencies"""
    
    def test_observability_imports(self):
        """Test that all main components can be imported"""
        from src.infrastructure.observability import (
            TheodoreLogger,
            LogLevel,
            MetricsCollector,
            HealthChecker,
            AlertManager
        )
        
        # Should not raise any exceptions
        assert TheodoreLogger is not None
        assert LogLevel is not None
        assert MetricsCollector is not None
        assert HealthChecker is not None
        assert AlertManager is not None
    
    def test_basic_logging_flow(self):
        """Test basic logging flow without external deps"""
        config = ObservabilityConfig(redact_sensitive_data=True)
        logger = TheodoreLogger("test", LogCategory.SYSTEM, config)
        
        # This should not raise exceptions
        context = logger._build_context(
            test_field="value",
            password="secret"  # Should be filtered
        )
        
        assert context["test_field"] == "value"
        assert context["password"] == "[REDACTED]"
    
    def test_metrics_and_health_integration(self):
        """Test metrics and health check integration"""
        from src.infrastructure.observability.metrics import get_metrics_collector
        from src.infrastructure.observability.health import get_health_checker
        
        metrics = get_metrics_collector()
        health = get_health_checker()
        
        # Should create instances
        assert metrics is not None
        assert health is not None
        
        # Should be singletons
        assert get_metrics_collector() is metrics
        assert get_health_checker() is health
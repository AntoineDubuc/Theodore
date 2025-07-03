#!/usr/bin/env python3
"""
Unit tests for Theodore v2 logging system.

Tests structured logging, context management, correlation IDs,
and sensitive data filtering capabilities.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.infrastructure.observability.logging import (
    TheodoreLogger,
    LogLevel,
    LogCategory,
    ObservabilityConfig,
    SensitiveDataFilter,
    configure_logging,
    get_logger
)

from src.infrastructure.observability.tracing import (
    correlation_context
)


class TestSensitiveDataFilter:
    """Test sensitive data filtering functionality"""
    
    def test_filter_password_field(self):
        """Test filtering of password fields"""
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "sk-1234567890abcdef"
        }
        
        filtered = SensitiveDataFilter.filter_sensitive_data(data)
        
        assert filtered["username"] == "testuser"
        assert filtered["password"] == "[REDACTED]"
        assert filtered["api_key"] == "[REDACTED]"
    
    def test_filter_nested_sensitive_data(self):
        """Test filtering of nested sensitive data"""
        data = {
            "user": {
                "name": "testuser",
                "credentials": {
                    "password": "secret123",
                    "token": "bearer_token_12345"
                }
            },
            "config": {
                "database_url": "postgres://user:pass@host:5432/db"
            }
        }
        
        filtered = SensitiveDataFilter.filter_sensitive_data(data)
        
        assert filtered["user"]["name"] == "testuser"
        assert filtered["user"]["credentials"]["password"] == "[REDACTED]"
        assert filtered["user"]["credentials"]["token"] == "[REDACTED]"
        assert filtered["config"]["database_url"] == "postgres://user:pass@host:5432/db"
    
    def test_mask_long_tokens(self):
        """Test masking of long token-like strings"""
        data = {
            "short_value": "abc",
            "api_key": "sk-1234567890abcdefghijklmnop",
            "normal_text": "This is just normal text that happens to be long"
        }
        
        filtered = SensitiveDataFilter.filter_sensitive_data(data)
        
        assert filtered["short_value"] == "abc"
        assert filtered["api_key"] == "sk-1...nop"
        assert "normal_text" in filtered


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
        """Test custom configuration values"""
        config = ObservabilityConfig(
            log_level=LogLevel.DEBUG,
            enable_json_logging=False,
            log_file_path="/tmp/test.log"
        )
        
        assert config.log_level == LogLevel.DEBUG
        assert config.enable_json_logging is False
        assert config.log_file_path == "/tmp/test.log"


class TestTheodoreLogger:
    """Test Theodore logger functionality"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return ObservabilityConfig(
            enable_correlation_ids=True,
            redact_sensitive_data=True
        )
    
    @pytest.fixture
    def logger(self, config):
        """Test logger instance"""
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
    
    def test_with_user(self, logger):
        """Test user context helper"""
        user_logger = logger.with_user("user123", "session456")
        
        assert user_logger._context["user_id"] == "user123"
        assert user_logger._context["session_id"] == "session456"
    
    def test_with_operation(self, logger):
        """Test operation context helper"""
        op_logger = logger.with_operation("research_company", company="TestCorp")
        
        assert op_logger._context["operation"] == "research_company"
        assert op_logger._context["company"] == "TestCorp"
    
    @patch('src.infrastructure.observability.logging.structlog')
    def test_build_context(self, mock_structlog, logger):
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
    
    @patch('src.infrastructure.observability.logging.structlog')
    def test_logging_methods(self, mock_structlog, logger):
        """Test various logging methods"""
        mock_bound_logger = MagicMock()
        mock_structlog.get_logger.return_value.bind.return_value = mock_bound_logger
        
        # Test different log levels
        logger.debug("Debug message", extra_field="value")
        logger.info("Info message", extra_field="value")
        logger.warn("Warning message", extra_field="value")
        logger.error("Error message", extra_field="value")
        logger.critical("Critical message", extra_field="value")
        
        # Verify structlog was called for each level
        assert mock_bound_logger.log.call_count == 5
    
    def test_error_with_exception(self, logger):
        """Test error logging with exception"""
        with patch.object(logger, '_log') as mock_log:
            test_exception = ValueError("Test error")
            
            logger.error("Something went wrong", error=test_exception)
            
            # Verify error details were added
            call_args = mock_log.call_args
            kwargs = call_args[1]
            
            assert kwargs["error_type"] == "ValueError"
            assert kwargs["error_message"] == "Test error"
            assert "error_traceback" in kwargs
    
    def test_audit_logging(self, logger):
        """Test audit logging"""
        with patch.object(logger, '_log') as mock_log:
            logger.audit(
                "user_login",
                user_id="user123",
                resource="dashboard",
                ip_address="192.168.1.1"
            )
            
            call_args = mock_log.call_args
            kwargs = call_args[1]
            
            assert kwargs["action"] == "user_login"
            assert kwargs["user_id"] == "user123"
            assert kwargs["resource"] == "dashboard"
            assert kwargs["ip_address"] == "192.168.1.1"
            assert kwargs["category"] == LogCategory.AUDIT.value
    
    def test_performance_context(self, logger):
        """Test performance context manager"""
        with patch.object(logger, 'debug') as mock_debug, \
             patch.object(logger, 'info') as mock_info:
            
            with logger.performance_context("test_operation", param="value"):
                pass  # Simulate work
            
            # Verify start and completion logs
            assert mock_debug.called  # Start log
            assert mock_info.called   # Completion log
            
            # Check completion log contains duration
            completion_call = mock_info.call_args
            kwargs = completion_call[1]
            assert "duration_seconds" in kwargs
            assert kwargs["status"] == "success"
    
    def test_performance_context_with_error(self, logger):
        """Test performance context with exception"""
        with patch.object(logger, 'debug') as mock_debug, \
             patch.object(logger, 'error') as mock_error:
            
            with pytest.raises(ValueError):
                with logger.performance_context("test_operation"):
                    raise ValueError("Test error")
            
            # Verify error logging
            assert mock_debug.called  # Start log
            assert mock_error.called  # Error log
            
            error_call = mock_error.call_args
            kwargs = error_call[1]
            assert kwargs["status"] == "error"
            assert "duration_seconds" in kwargs


class TestLoggingConfiguration:
    """Test logging configuration and setup"""
    
    def test_configure_logging(self):
        """Test logging configuration"""
        config = ObservabilityConfig(
            log_level=LogLevel.DEBUG,
            enable_json_logging=True
        )
        
        # Should not raise exception
        configure_logging(config)
    
    def test_get_logger_factory(self):
        """Test logger factory function"""
        logger = get_logger("test_component", LogCategory.BUSINESS)
        
        assert isinstance(logger, TheodoreLogger)
        assert logger.component == "test_component"
        assert logger.category == LogCategory.BUSINESS
    
    def test_correlation_context_manager(self):
        """Test correlation context manager"""
        test_id = str(uuid.uuid4())
        
        with correlation_context(test_id) as correlation_id:
            assert correlation_id == test_id
            # In a real scenario, this would be stored in context vars


class TestLogLevelsAndCategories:
    """Test log levels and categories"""
    
    def test_log_levels(self):
        """Test all log levels are defined"""
        expected_levels = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL", "AUDIT"}
        actual_levels = {level.value.upper() for level in LogLevel}
        
        assert actual_levels >= expected_levels
    
    def test_log_categories(self):
        """Test all log categories are defined"""
        expected_categories = {
            "system", "security", "audit", "performance", "business",
            "ai_operations", "user_activity", "api_access", "data_processing",
            "integration", "scraping", "batch_processing"
        }
        actual_categories = {cat.value for cat in LogCategory}
        
        assert actual_categories >= expected_categories


class TestIntegration:
    """Integration tests for logging system"""
    
    def test_end_to_end_logging_flow(self):
        """Test complete logging flow"""
        # Configure logging
        config = ObservabilityConfig(
            enable_correlation_ids=True,
            redact_sensitive_data=True
        )
        configure_logging(config)
        
        # Create logger with context
        logger = get_logger("integration_test", LogCategory.BUSINESS)
        correlation_id = str(uuid.uuid4())
        
        context_logger = (logger
                         .with_correlation_id(correlation_id)
                         .with_user("test_user", "session123")
                         .with_context(test_run=True))
        
        # Log various types of messages
        with patch.object(context_logger, '_log') as mock_log:
            context_logger.info("Test message", 
                               password="secret123",  # Should be filtered
                               normal_data="visible")
            
            # Verify logging was called
            assert mock_log.called
            
            # Check context was properly built
            call_args = mock_log.call_args
            level, message = call_args[0]
            kwargs = call_args[1]
            
            assert level == LogLevel.INFO
            assert message == "Test message"
            assert kwargs.get("password") == "[REDACTED]"
            assert kwargs.get("normal_data") == "visible"
    
    def test_multiple_logger_instances(self):
        """Test multiple logger instances don't interfere"""
        logger1 = get_logger("component1", LogCategory.SYSTEM)
        logger2 = get_logger("component2", LogCategory.BUSINESS)
        
        # Add different contexts
        ctx_logger1 = logger1.with_context(service="auth")
        ctx_logger2 = logger2.with_context(service="billing")
        
        # Verify isolation
        assert ctx_logger1.component == "component1"
        assert ctx_logger2.component == "component2"
        assert ctx_logger1._context["service"] == "auth"
        assert ctx_logger2._context["service"] == "billing"
        assert "service" not in logger1._context
        assert "service" not in logger2._context
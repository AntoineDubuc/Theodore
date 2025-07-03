#!/usr/bin/env python3
"""
Theodore v2 Structured Logging System
====================================

Enterprise-grade structured logging with contextual metadata, correlation IDs,
security features, and integration with distributed tracing systems.

This module provides comprehensive logging capabilities including:
- Structured JSON logging with rich metadata
- Correlation ID tracking across distributed operations
- Security-focused audit logging with sensitive data protection
- Performance logging with timing and resource metrics
- Integration with OpenTelemetry distributed tracing
- Multi-level configuration and component-specific settings
"""

import logging
import sys
import os
import traceback
import uuid
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import contextmanager

# Try to import structlog, provide fallback if not available
try:
    import structlog
    from structlog.processors import JSONRenderer, TimeStamper, add_log_level
    from structlog.contextvars import bind_contextvars, clear_contextvars
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    
    # Fallback implementations
    class MockStructlog:
        @staticmethod
        def get_logger(name):
            return logging.getLogger(name)
        
        @staticmethod
        def configure(**kwargs):
            pass
    
    structlog = MockStructlog()

try:
    from opentelemetry import trace
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False


class LogLevel(str, Enum):
    """Log levels following RFC 5424 standard with Theodore extensions"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"


class LogCategory(str, Enum):
    """Log categories for structured event classification"""
    SYSTEM = "system"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    AI_OPERATIONS = "ai_operations"
    USER_ACTIVITY = "user_activity"
    API_ACCESS = "api_access"
    DATA_PROCESSING = "data_processing"
    INTEGRATION = "integration"
    SCRAPING = "scraping"
    BATCH_PROCESSING = "batch_processing"


class SensitiveDataFilter:
    """Filter to protect sensitive data in logs"""
    
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'secret', 'key', 'token', 'credential',
        'authorization', 'auth', 'jwt', 'api_key', 'access_token',
        'refresh_token', 'private_key', 'cert', 'certificate'
    }
    
    @classmethod
    def filter_sensitive_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive data from log entries"""
        filtered = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if field name indicates sensitive data
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_FIELDS):
                filtered[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered[key] = cls.filter_sensitive_data(value)
            elif isinstance(value, str) and len(value) > 20:
                # Mask potential tokens/keys
                if any(sensitive in key_lower for sensitive in ['token', 'key', 'secret']):
                    filtered[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    filtered[key] = value
            else:
                filtered[key] = value
                
        return filtered


class ObservabilityConfig:
    """Configuration for Theodore observability system"""
    
    def __init__(
        self,
        log_level: LogLevel = LogLevel.INFO,
        enable_json_logging: bool = True,
        enable_correlation_ids: bool = True,
        enable_tracing: bool = True,
        log_file_path: Optional[str] = None,
        max_log_file_size: int = 100 * 1024 * 1024,  # 100MB
        log_retention_days: int = 30,
        enable_audit_logging: bool = True,
        enable_performance_logging: bool = True,
        redact_sensitive_data: bool = True,
        enterprise_integrations: Optional[Dict[str, Any]] = None
    ):
        self.log_level = log_level
        self.enable_json_logging = enable_json_logging
        self.enable_correlation_ids = enable_correlation_ids
        self.enable_tracing = enable_tracing
        self.log_file_path = log_file_path
        self.max_log_file_size = max_log_file_size
        self.log_retention_days = log_retention_days
        self.enable_audit_logging = enable_audit_logging
        self.enable_performance_logging = enable_performance_logging
        self.redact_sensitive_data = redact_sensitive_data
        self.enterprise_integrations = enterprise_integrations or {}


class TheodoreLogger:
    """Enterprise-grade structured logger with contextual metadata"""
    
    def __init__(
        self, 
        component: str, 
        category: LogCategory = LogCategory.SYSTEM,
        config: Optional[ObservabilityConfig] = None
    ):
        self.component = component
        self.category = category
        self.config = config or _get_global_config()
        self.logger = structlog.get_logger(component)
        self.correlation_id = None
        self._context = {}
        
    def with_correlation_id(self, correlation_id: str) -> 'TheodoreLogger':
        """Create logger instance with correlation ID"""
        new_logger = TheodoreLogger(self.component, self.category, self.config)
        new_logger.correlation_id = correlation_id
        new_logger._context = self._context.copy()
        return new_logger
        
    def with_context(self, **context) -> 'TheodoreLogger':
        """Add contextual metadata to logger"""
        new_logger = TheodoreLogger(self.component, self.category, self.config)
        new_logger.correlation_id = self.correlation_id
        new_logger._context = {**self._context, **context}
        return new_logger
    
    def with_user(self, user_id: str, session_id: Optional[str] = None) -> 'TheodoreLogger':
        """Add user context to logger"""
        user_context = {'user_id': user_id}
        if session_id:
            user_context['session_id'] = session_id
        return self.with_context(**user_context)
    
    def with_operation(self, operation: str, **metadata) -> 'TheodoreLogger':
        """Add operation context to logger"""
        op_context = {'operation': operation, **metadata}
        return self.with_context(**op_context)
        
    def _build_context(self, **kwargs) -> Dict[str, Any]:
        """Build complete logging context with metadata"""
        context = {
            'component': self.component,
            'category': self.category.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': os.getenv('THEODORE_ENV', 'development')
        }
        
        # Add correlation ID if available
        if self.correlation_id:
            context['correlation_id'] = self.correlation_id
        elif self.config.enable_correlation_ids:
            context['correlation_id'] = str(uuid.uuid4())
            
        # Add tracing context if available
        if TRACING_AVAILABLE and self.config.enable_tracing:
            span = trace.get_current_span()
            if span.is_recording():
                span_context = span.get_span_context()
                context.update({
                    'trace_id': format(span_context.trace_id, '032x'),
                    'span_id': format(span_context.span_id, '016x')
                })
        
        # Add stored context
        context.update(self._context)
        
        # Add call-specific context
        context.update(kwargs)
        
        # Filter sensitive data if enabled
        if self.config.redact_sensitive_data:
            context = SensitiveDataFilter.filter_sensitive_data(context)
            
        return context
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method with full context"""
        context = self._build_context(**kwargs)
        
        # Map Theodore log levels to Python logging levels
        level_mapping = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.AUDIT: logging.INFO
        }
        
        python_level = level_mapping.get(level, logging.INFO)
        
        # Bind context and log
        if STRUCTLOG_AVAILABLE:
            bound_logger = self.logger.bind(**context)
            bound_logger.log(python_level, message, level=level.value)
        else:
            # Fallback to standard logging with JSON context
            log_data = {
                "message": message,
                "level": level.value,
                **context
            }
            self.logger.log(python_level, json.dumps(log_data))
        
    def trace(self, message: str, **kwargs):
        """Log trace level message (most verbose debugging)"""
        self._log(LogLevel.TRACE, message, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug level message with context"""
        self._log(LogLevel.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info level message with context"""
        self._log(LogLevel.INFO, message, **kwargs)
        
    def warn(self, message: str, **kwargs):
        """Log warning level message with context"""
        self._log(LogLevel.WARN, message, **kwargs)
        
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error level message with exception context"""
        if error:
            kwargs.update({
                'error_type': error.__class__.__name__,
                'error_message': str(error),
                'error_traceback': self._safe_traceback(error)
            })
        self._log(LogLevel.ERROR, message, **kwargs)
        
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical level message with immediate alerting"""
        if error:
            kwargs.update({
                'error_type': error.__class__.__name__,
                'error_message': str(error),
                'error_traceback': self._safe_traceback(error)
            })
        self._log(LogLevel.CRITICAL, message, **kwargs)
        
        # TODO: Integrate with alerting system
        # self._trigger_critical_alert(message, kwargs)
    
    def audit(
        self, 
        action: str, 
        user_id: Optional[str] = None, 
        resource: Optional[str] = None, 
        **kwargs
    ):
        """Log audit event for compliance tracking"""
        if not self.config.enable_audit_logging:
            return
            
        audit_context = {
            'action': action,
            'user_id': user_id,
            'resource': resource,
            'audit_timestamp': datetime.now(timezone.utc).isoformat(),
            'category': LogCategory.AUDIT.value
        }
        audit_context.update(kwargs)
        self._log(LogLevel.AUDIT, f"Audit: {action}", **audit_context)
    
    @contextmanager
    def performance_context(self, operation: str, **metadata):
        """Context manager for performance logging"""
        if not self.config.enable_performance_logging:
            yield
            return
            
        start_time = datetime.now(timezone.utc)
        self.debug(f"Starting {operation}", operation=operation, **metadata)
        
        try:
            yield
            # Success case
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.info(
                f"Completed {operation}",
                operation=operation,
                duration_seconds=duration,
                status="success",
                **metadata
            )
        except Exception as e:
            # Error case
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.error(
                f"Failed {operation}",
                error=e,
                operation=operation,
                duration_seconds=duration,
                status="error",
                **metadata
            )
            raise
    
    def _safe_traceback(self, error: Exception) -> str:
        """Safely extract traceback from exception"""
        try:
            return ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))
        except Exception:
            return f"Error extracting traceback: {str(error)}"


# Global configuration instance
_global_config: Optional[ObservabilityConfig] = None


def configure_logging(config: ObservabilityConfig) -> None:
    """Configure global logging system"""
    global _global_config
    _global_config = config
    
    if STRUCTLOG_AVAILABLE:
        # Configure structlog
        processors = [
            structlog.stdlib.filter_by_level,
            add_log_level,
            structlog.stdlib.add_logger_name,
        ]
        
        if config.enable_json_logging:
            processors.extend([
                TimeStamper(fmt="ISO"),
                JSONRenderer()
            ])
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    # Configure Python logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if config.enable_json_logging and not STRUCTLOG_AVAILABLE:
        log_format = "%(message)s"  # JSON will be in message
    
    logging.basicConfig(
        level=getattr(logging, config.log_level.value),
        format=log_format,
        stream=sys.stdout
    )
    
    # Configure file logging if specified
    if config.log_file_path:
        _configure_file_logging(config)


def _configure_file_logging(config: ObservabilityConfig) -> None:
    """Configure file-based logging with rotation"""
    from logging.handlers import RotatingFileHandler
    
    log_path = Path(config.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        config.log_file_path,
        maxBytes=config.max_log_file_size,
        backupCount=config.log_retention_days
    )
    
    # Configure formatter for file output
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def _get_global_config() -> ObservabilityConfig:
    """Get global configuration, creating default if needed"""
    global _global_config
    if _global_config is None:
        _global_config = ObservabilityConfig()
        configure_logging(_global_config)
    return _global_config


def get_logger(
    component: str, 
    category: LogCategory = LogCategory.SYSTEM
) -> TheodoreLogger:
    """Factory function to create Theodore loggers"""
    return TheodoreLogger(component, category, _get_global_config())


# Convenience functions for common logging scenarios
def get_system_logger(component: str) -> TheodoreLogger:
    """Get logger for system components"""
    return get_logger(component, LogCategory.SYSTEM)


def get_security_logger(component: str) -> TheodoreLogger:
    """Get logger for security events"""
    return get_logger(component, LogCategory.SECURITY)


def get_audit_logger(component: str) -> TheodoreLogger:
    """Get logger for audit events"""
    return get_logger(component, LogCategory.AUDIT)


def get_performance_logger(component: str) -> TheodoreLogger:
    """Get logger for performance tracking"""
    return get_logger(component, LogCategory.PERFORMANCE)


def get_business_logger(component: str) -> TheodoreLogger:
    """Get logger for business events"""
    return get_logger(component, LogCategory.BUSINESS)
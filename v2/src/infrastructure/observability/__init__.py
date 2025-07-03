#!/usr/bin/env python3
"""
Theodore v2 Observability Infrastructure Package
==============================================

Enterprise-grade observability system providing structured logging,
distributed tracing, metrics collection, and real-time monitoring.

This package implements the three pillars of observability:
- **Logs**: Structured, contextual event recording
- **Metrics**: System and business performance indicators  
- **Traces**: Distributed request flow analysis

Key Features:
- Structured logging with correlation IDs
- OpenTelemetry distributed tracing
- Real-time metrics and alerting
- Enterprise integrations (Datadog, ELK, New Relic)
- Security-focused audit logging
- Cost tracking and performance analytics
"""

from .logging import (
    TheodoreLogger,
    LogLevel,
    LogCategory,
    ObservabilityConfig,
    configure_logging,
    get_logger
)

from .metrics import (
    MetricsCollector,
    MetricType,
    MetricsRegistry,
    BusinessMetrics
)

from .tracing import (
    TraceManager,
    configure_tracing,
    trace_operation,
    get_correlation_id
)

from .health import (
    HealthChecker,
    HealthStatus,
    SystemHealth
)

from .alerting import (
    AlertManager,
    AlertLevel,
    AlertChannel
)

__all__ = [
    # Logging
    "TheodoreLogger",
    "LogLevel", 
    "LogCategory",
    "ObservabilityConfig",
    "configure_logging",
    "get_logger",
    
    # Metrics
    "MetricsCollector",
    "MetricType",
    "MetricsRegistry", 
    "BusinessMetrics",
    
    # Tracing
    "TraceManager",
    "configure_tracing",
    "trace_operation",
    "get_correlation_id",
    
    # Health
    "HealthChecker",
    "HealthStatus",
    "SystemHealth",
    
    # Alerting
    "AlertManager",
    "AlertLevel",
    "AlertChannel"
]

# Version information
__version__ = "2.0.0"
__author__ = "Theodore Team"
__description__ = "Enterprise observability infrastructure for Theodore v2"
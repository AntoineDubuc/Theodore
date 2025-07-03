#!/usr/bin/env python3
"""
Theodore v2 Distributed Tracing System
=====================================

Comprehensive distributed tracing using OpenTelemetry for request flow analysis,
performance monitoring, and system debugging across Theodore's AI workflows.

This module provides:
- OpenTelemetry distributed tracing integration
- Correlation ID management for request tracking
- Performance span instrumentation
- Custom attributes and metrics
- Integration with external tracing systems (Jaeger, Zipkin, Datadog)
"""

import uuid
import time
import functools
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager, asynccontextmanager
from contextvars import ContextVar

try:
    from opentelemetry import trace, baggage
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
    from opentelemetry.instrumentation.asyncio import AsyncIOInstrumentor
    from opentelemetry.propagate import inject, extract
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    
    # Mock implementations for when OpenTelemetry is not available
    class SpanKind:
        INTERNAL = "internal"
        SERVER = "server"
        CLIENT = "client"
        PRODUCER = "producer"
        CONSUMER = "consumer"
    
    class Status:
        def __init__(self, status_code, description=""):
            self.status_code = status_code
            self.description = description
    
    class StatusCode:
        OK = "ok"
        ERROR = "error"


# Context variable for correlation ID
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class TracingConfig:
    """Configuration for distributed tracing"""
    
    def __init__(
        self,
        service_name: str = "theodore-v2",
        enable_tracing: bool = True,
        jaeger_endpoint: Optional[str] = None,
        zipkin_endpoint: Optional[str] = None,
        datadog_endpoint: Optional[str] = None,
        sample_rate: float = 1.0,
        enable_auto_instrumentation: bool = True,
        export_timeout: int = 30,
        max_export_batch_size: int = 512
    ):
        self.service_name = service_name
        self.enable_tracing = enable_tracing
        self.jaeger_endpoint = jaeger_endpoint
        self.zipkin_endpoint = zipkin_endpoint
        self.datadog_endpoint = datadog_endpoint
        self.sample_rate = sample_rate
        self.enable_auto_instrumentation = enable_auto_instrumentation
        self.export_timeout = export_timeout
        self.max_export_batch_size = max_export_batch_size


class TraceManager:
    """Central manager for distributed tracing operations"""
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self.tracer = None
        self._initialized = False
        
        if TRACING_AVAILABLE and config.enable_tracing:
            self._initialize_tracing()
    
    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        if self._initialized:
            return
            
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        
        # Configure exporters
        exporters = []
        
        if self.config.jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_endpoint.split(':')[0],
                agent_port=int(self.config.jaeger_endpoint.split(':')[1]) if ':' in self.config.jaeger_endpoint else 14268,
            )
            exporters.append(jaeger_exporter)
        
        if self.config.zipkin_endpoint:
            zipkin_exporter = ZipkinExporter(
                endpoint=self.config.zipkin_endpoint
            )
            exporters.append(zipkin_exporter)
        
        # Add batch processors for exporters
        for exporter in exporters:
            processor = BatchSpanProcessor(
                exporter,
                export_timeout_millis=self.config.export_timeout * 1000,
                max_export_batch_size=self.config.max_export_batch_size
            )
            trace.get_tracer_provider().add_span_processor(processor)
        
        # Get tracer
        self.tracer = trace.get_tracer(
            self.config.service_name,
            version="2.0.0"
        )
        
        # Enable auto-instrumentation
        if self.config.enable_auto_instrumentation:
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()
            AsyncIOInstrumentor().instrument()
        
        self._initialized = True
    
    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        span_kind: SpanKind = SpanKind.INTERNAL
    ):
        """Context manager for tracing operations"""
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(
            operation_name,
            kind=span_kind,
            attributes=attributes or {}
        ) as span:
            try:
                # Set correlation ID if available
                correlation_id = get_correlation_id()
                if correlation_id:
                    span.set_attribute("correlation_id", correlation_id)
                
                # Add Theodore-specific attributes
                span.set_attribute("service.name", self.config.service_name)
                span.set_attribute("service.version", "2.0.0")
                
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record error
                span.record_exception(e)
                span.set_status(
                    Status(StatusCode.ERROR, f"Operation failed: {str(e)}")
                )
                raise
    
    @asynccontextmanager
    async def trace_async_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        span_kind: SpanKind = SpanKind.INTERNAL
    ):
        """Async context manager for tracing operations"""
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(
            operation_name,
            kind=span_kind,
            attributes=attributes or {}
        ) as span:
            try:
                # Set correlation ID if available
                correlation_id = get_correlation_id()
                if correlation_id:
                    span.set_attribute("correlation_id", correlation_id)
                
                # Add Theodore-specific attributes
                span.set_attribute("service.name", self.config.service_name)
                span.set_attribute("service.version", "2.0.0")
                
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record error
                span.record_exception(e)
                span.set_status(
                    Status(StatusCode.ERROR, f"Operation failed: {str(e)}")
                )
                raise
    
    def create_child_span(
        self,
        operation_name: str,
        parent_span=None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Create a child span for nested operations"""
        if not self.tracer:
            return None
        
        return self.tracer.start_span(
            operation_name,
            context=trace.set_span_in_context(parent_span) if parent_span else None,
            attributes=attributes or {}
        )
    
    def add_span_attributes(self, attributes: Dict[str, Any]):
        """Add attributes to current span"""
        if not TRACING_AVAILABLE:
            return
            
        current_span = trace.get_current_span()
        if current_span.is_recording():
            for key, value in attributes.items():
                current_span.set_attribute(key, value)
    
    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span"""
        if not TRACING_AVAILABLE:
            return
            
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.add_event(name, attributes or {})
    
    def record_exception(self, exception: Exception):
        """Record exception in current span"""
        if not TRACING_AVAILABLE:
            return
            
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.record_exception(exception)


# Global trace manager instance
_global_trace_manager: Optional[TraceManager] = None


def configure_tracing(config: TracingConfig) -> TraceManager:
    """Configure global tracing system"""
    global _global_trace_manager
    _global_trace_manager = TraceManager(config)
    return _global_trace_manager


def get_trace_manager() -> Optional[TraceManager]:
    """Get global trace manager"""
    return _global_trace_manager


def trace_operation(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    span_kind: SpanKind = SpanKind.INTERNAL
):
    """Decorator for tracing functions"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            trace_manager = get_trace_manager()
            if not trace_manager:
                return func(*args, **kwargs)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with trace_manager.trace_operation(
                op_name,
                attributes=attributes,
                span_kind=span_kind
            ) as span:
                # Add function-specific attributes
                if span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_async_operation(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    span_kind: SpanKind = SpanKind.INTERNAL
):
    """Decorator for tracing async functions"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            trace_manager = get_trace_manager()
            if not trace_manager:
                return await func(*args, **kwargs)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            async with trace_manager.trace_async_operation(
                op_name,
                attributes=attributes,
                span_kind=span_kind
            ) as span:
                # Add function-specific attributes
                if span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Correlation ID management
def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in current context"""
    correlation_id_context.set(correlation_id)
    
    # Also set in baggage for cross-service propagation
    if TRACING_AVAILABLE:
        baggage.set_baggage("correlation_id", correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context"""
    # Try context variable first
    correlation_id = correlation_id_context.get()
    if correlation_id:
        return correlation_id
    
    # Try baggage
    if TRACING_AVAILABLE:
        correlation_id = baggage.get_baggage("correlation_id")
        if correlation_id:
            return correlation_id
    
    # Try current span
    if TRACING_AVAILABLE:
        current_span = trace.get_current_span()
        if current_span.is_recording():
            return current_span.get_span_context().trace_id
    
    return None


def ensure_correlation_id() -> str:
    """Ensure correlation ID exists, creating one if needed"""
    correlation_id = get_correlation_id()
    if not correlation_id:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
    return correlation_id


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID scope"""
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Store previous correlation ID
    previous_id = get_correlation_id()
    
    try:
        set_correlation_id(correlation_id)
        yield correlation_id
    finally:
        # Restore previous correlation ID
        if previous_id:
            set_correlation_id(previous_id)
        else:
            correlation_id_context.set(None)


# Propagation helpers for cross-service calls
def get_trace_headers() -> Dict[str, str]:
    """Get headers for trace propagation"""
    if not TRACING_AVAILABLE:
        return {}
    
    headers = {}
    inject(headers)
    
    # Add correlation ID header
    correlation_id = get_correlation_id()
    if correlation_id:
        headers['X-Correlation-ID'] = correlation_id
    
    return headers


def extract_trace_context(headers: Dict[str, str]) -> None:
    """Extract trace context from headers"""
    if not TRACING_AVAILABLE:
        return
    
    # Extract OpenTelemetry context
    extract(headers)
    
    # Extract correlation ID
    correlation_id = headers.get('X-Correlation-ID')
    if correlation_id:
        set_correlation_id(correlation_id)


# Performance timing utilities
class PerformanceTimer:
    """Helper for measuring operation performance"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self):
        """Stop timing and record"""
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        # Add to current span if available
        trace_manager = get_trace_manager()
        if trace_manager:
            trace_manager.add_span_attributes({
                f"{self.operation_name}.duration_seconds": duration,
                f"{self.operation_name}.completed_at": datetime.now(timezone.utc).isoformat()
            })
        
        return duration
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def measure_performance(operation_name: str):
    """Decorator for measuring function performance"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTimer(f"{func.__name__}"):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Business-specific tracing helpers
def trace_company_research(company_name: str, research_type: str = "full"):
    """Context manager for tracing company research operations"""
    trace_manager = get_trace_manager()
    if not trace_manager:
        return contextmanager(lambda: iter([None]))()
    
    return trace_manager.trace_operation(
        "company_research",
        attributes={
            "company.name": company_name,
            "research.type": research_type,
            "operation.category": "ai_operations"
        },
        span_kind=SpanKind.INTERNAL
    )


def trace_batch_processing(batch_id: str, batch_size: int):
    """Context manager for tracing batch processing operations"""
    trace_manager = get_trace_manager()
    if not trace_manager:
        return contextmanager(lambda: iter([None]))()
    
    return trace_manager.trace_operation(
        "batch_processing", 
        attributes={
            "batch.id": batch_id,
            "batch.size": batch_size,
            "operation.category": "batch_processing"
        },
        span_kind=SpanKind.INTERNAL
    )
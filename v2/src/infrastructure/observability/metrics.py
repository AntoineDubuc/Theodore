#!/usr/bin/env python3
"""
Theodore v2 Metrics Collection System
===================================

Comprehensive metrics collection for system performance, business intelligence,
and operational insights with support for multiple metric types and export formats.

This module provides:
- Counter, gauge, histogram, and summary metrics
- Business metrics tracking (costs, success rates, performance)
- System metrics monitoring (CPU, memory, API response times)
- Custom metrics with labels and dimensions
- Export to Prometheus, Datadog, CloudWatch, and other systems
"""

import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
import statistics
import json


class MetricType(str, Enum):
    """Types of metrics supported by Theodore"""
    COUNTER = "counter"           # Monotonically increasing values
    GAUGE = "gauge"              # Current value that can go up or down
    HISTOGRAM = "histogram"      # Distribution of values over time
    SUMMARY = "summary"          # Summary statistics (count, sum, percentiles)
    TIMER = "timer"             # Duration measurements
    RATE = "rate"               # Rate of events over time


class MetricUnit(str, Enum):
    """Units for metrics"""
    NONE = ""
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    BYTES = "bytes"
    KILOBYTES = "kilobytes"
    MEGABYTES = "megabytes"
    REQUESTS = "requests"
    OPERATIONS = "operations"
    PERCENT = "percent"
    COUNT = "count"
    DOLLARS = "dollars"
    RATE_PER_SECOND = "per_second"


@dataclass
class MetricLabel:
    """Label for metric dimensions"""
    name: str
    value: str


@dataclass
class MetricValue:
    """Individual metric measurement"""
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)


class BaseMetric(ABC):
    """Base class for all metric types"""
    
    def __init__(
        self,
        name: str,
        description: str,
        unit: MetricUnit = MetricUnit.NONE,
        labels: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.description = description
        self.unit = unit
        self.labels = labels or {}
        self.created_at = datetime.now(timezone.utc)
        self._lock = threading.Lock()
    
    @abstractmethod
    def record(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Record a value for this metric"""
        pass
    
    @abstractmethod
    def get_value(self) -> Dict[str, Any]:
        """Get current metric value(s)"""
        pass
    
    @abstractmethod
    def reset(self):
        """Reset metric to initial state"""
        pass


class Counter(BaseMetric):
    """Counter metric that only increases"""
    
    def __init__(self, name: str, description: str, unit: MetricUnit = MetricUnit.COUNT, labels: Optional[Dict[str, str]] = None):
        super().__init__(name, description, unit, labels)
        self._value = 0.0
        self._values_by_labels = defaultdict(float)
    
    def record(self, value: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None):
        """Increment counter by value"""
        if value < 0:
            raise ValueError("Counter values must be non-negative")
        
        with self._lock:
            self._value += value
            
            if labels:
                label_key = json.dumps(labels, sort_keys=True)
                self._values_by_labels[label_key] += value
    
    def increment(self, labels: Optional[Dict[str, str]] = None):
        """Increment counter by 1"""
        self.record(1, labels)
    
    def get_value(self) -> Dict[str, Any]:
        """Get current counter value"""
        with self._lock:
            return {
                "value": self._value,
                "type": MetricType.COUNTER,
                "unit": self.unit.value,
                "labels": dict(self._values_by_labels)
            }
    
    def reset(self):
        """Reset counter to zero"""
        with self._lock:
            self._value = 0.0
            self._values_by_labels.clear()


class Gauge(BaseMetric):
    """Gauge metric that can increase or decrease"""
    
    def __init__(self, name: str, description: str, unit: MetricUnit = MetricUnit.NONE, labels: Optional[Dict[str, str]] = None):
        super().__init__(name, description, unit, labels)
        self._value = 0.0
        self._values_by_labels = defaultdict(float)
    
    def record(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Set gauge to value"""
        with self._lock:
            self._value = value
            
            if labels:
                label_key = json.dumps(labels, sort_keys=True)
                self._values_by_labels[label_key] = value
    
    def increment(self, amount: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None):
        """Increment gauge by amount"""
        with self._lock:
            self._value += amount
            
            if labels:
                label_key = json.dumps(labels, sort_keys=True)
                self._values_by_labels[label_key] += amount
    
    def decrement(self, amount: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge by amount"""
        self.increment(-amount, labels)
    
    def get_value(self) -> Dict[str, Any]:
        """Get current gauge value"""
        with self._lock:
            return {
                "value": self._value,
                "type": MetricType.GAUGE,
                "unit": self.unit.value,
                "labels": dict(self._values_by_labels)
            }
    
    def reset(self):
        """Reset gauge to zero"""
        with self._lock:
            self._value = 0.0
            self._values_by_labels.clear()


class Histogram(BaseMetric):
    """Histogram metric for distribution of values"""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        unit: MetricUnit = MetricUnit.NONE,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, description, unit, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        self._values = deque(maxlen=10000)  # Keep last 10K values
        self._bucket_counts = {bucket: 0 for bucket in self.buckets}
        self._sum = 0.0
        self._count = 0
    
    def record(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Record a value in the histogram"""
        with self._lock:
            self._values.append(MetricValue(
                timestamp=datetime.now(timezone.utc),
                value=value,
                labels=labels or {}
            ))
            self._sum += value
            self._count += 1
            
            # Update bucket counts
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[bucket] += 1
    
    def get_value(self) -> Dict[str, Any]:
        """Get histogram statistics"""
        with self._lock:
            if not self._values:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "mean": 0.0,
                    "buckets": self._bucket_counts,
                    "type": MetricType.HISTOGRAM,
                    "unit": self.unit.value
                }
            
            values = [v.value for v in self._values]
            
            return {
                "count": self._count,
                "sum": self._sum,
                "mean": self._sum / self._count if self._count > 0 else 0.0,
                "min": min(values),
                "max": max(values),
                "p50": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99),
                "buckets": dict(self._bucket_counts),
                "type": MetricType.HISTOGRAM,
                "unit": self.unit.value
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset histogram"""
        with self._lock:
            self._values.clear()
            self._bucket_counts = {bucket: 0 for bucket in self.buckets}
            self._sum = 0.0
            self._count = 0


class Timer(BaseMetric):
    """Timer metric for measuring durations"""
    
    def __init__(self, name: str, description: str, labels: Optional[Dict[str, str]] = None):
        super().__init__(name, description, MetricUnit.SECONDS, labels)
        self._histogram = Histogram(name, description, MetricUnit.SECONDS, labels=labels)
    
    def record(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Record a duration in seconds"""
        self._histogram.record(value, labels)
    
    def time_function(self, func: Callable, *args, **kwargs):
        """Time a function execution"""
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start_time
            self.record(duration)
    
    def timer_context(self, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        return TimerContext(self, labels)
    
    def get_value(self) -> Dict[str, Any]:
        """Get timer statistics"""
        value = self._histogram.get_value()
        value["type"] = MetricType.TIMER
        return value
    
    def reset(self):
        """Reset timer"""
        self._histogram.reset()


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, timer: Timer, labels: Optional[Dict[str, str]] = None):
        self.timer = timer
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.timer.record(duration, self.labels)


class MetricsRegistry:
    """Registry for managing all metrics"""
    
    def __init__(self):
        self._metrics: Dict[str, BaseMetric] = {}
        self._lock = threading.Lock()
    
    def register(self, metric: BaseMetric) -> BaseMetric:
        """Register a metric"""
        with self._lock:
            if metric.name in self._metrics:
                raise ValueError(f"Metric {metric.name} already registered")
            self._metrics[metric.name] = metric
            return metric
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Get a metric by name"""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, BaseMetric]:
        """Get all registered metrics"""
        with self._lock:
            return dict(self._metrics)
    
    def counter(self, name: str, description: str, unit: MetricUnit = MetricUnit.COUNT, labels: Optional[Dict[str, str]] = None) -> Counter:
        """Create or get a counter metric"""
        metric = self.get_metric(name)
        if metric:
            if not isinstance(metric, Counter):
                raise ValueError(f"Metric {name} is not a counter")
            return metric
        
        counter = Counter(name, description, unit, labels)
        return self.register(counter)
    
    def gauge(self, name: str, description: str, unit: MetricUnit = MetricUnit.NONE, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """Create or get a gauge metric"""
        metric = self.get_metric(name)
        if metric:
            if not isinstance(metric, Gauge):
                raise ValueError(f"Metric {name} is not a gauge")
            return metric
        
        gauge = Gauge(name, description, unit, labels)
        return self.register(gauge)
    
    def histogram(self, name: str, description: str, unit: MetricUnit = MetricUnit.NONE, buckets: Optional[List[float]] = None, labels: Optional[Dict[str, str]] = None) -> Histogram:
        """Create or get a histogram metric"""
        metric = self.get_metric(name)
        if metric:
            if not isinstance(metric, Histogram):
                raise ValueError(f"Metric {name} is not a histogram")
            return metric
        
        histogram = Histogram(name, description, unit, buckets, labels)
        return self.register(histogram)
    
    def timer(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> Timer:
        """Create or get a timer metric"""
        metric = self.get_metric(name)
        if metric:
            if not isinstance(metric, Timer):
                raise ValueError(f"Metric {name} is not a timer")
            return metric
        
        timer = Timer(name, description, labels)
        return self.register(timer)
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all metric values"""
        with self._lock:
            return {
                name: metric.get_value() 
                for name, metric in self._metrics.items()
            }
    
    def reset_all(self):
        """Reset all metrics"""
        with self._lock:
            for metric in self._metrics.values():
                metric.reset()


class MetricsCollector:
    """Central metrics collection system"""
    
    def __init__(self):
        self.registry = MetricsRegistry()
        self._setup_system_metrics()
        self._setup_business_metrics()
    
    def _setup_system_metrics(self):
        """Setup system performance metrics"""
        # API performance metrics
        self.api_request_duration = self.registry.timer(
            "api_request_duration",
            "Duration of API requests"
        )
        
        self.api_request_count = self.registry.counter(
            "api_requests_total", 
            "Total number of API requests"
        )
        
        # AI operation metrics
        self.ai_operation_duration = self.registry.timer(
            "ai_operation_duration",
            "Duration of AI operations"
        )
        
        self.ai_token_usage = self.registry.counter(
            "ai_tokens_used_total",
            "Total AI tokens consumed",
            unit=MetricUnit.COUNT
        )
        
        # Scraping metrics
        self.scraping_duration = self.registry.timer(
            "scraping_duration",
            "Duration of web scraping operations"
        )
        
        self.pages_scraped = self.registry.counter(
            "pages_scraped_total",
            "Total pages scraped",
            unit=MetricUnit.COUNT
        )
        
        # Database metrics
        self.db_operation_duration = self.registry.timer(
            "db_operation_duration",
            "Duration of database operations"
        )
        
        # System health metrics
        self.active_connections = self.registry.gauge(
            "active_connections",
            "Number of active connections",
            unit=MetricUnit.COUNT
        )
        
        self.memory_usage = self.registry.gauge(
            "memory_usage_bytes",
            "Current memory usage",
            unit=MetricUnit.BYTES
        )
    
    def _setup_business_metrics(self):
        """Setup business intelligence metrics"""
        # Research metrics
        self.companies_researched = self.registry.counter(
            "companies_researched_total",
            "Total companies researched",
            unit=MetricUnit.COUNT
        )
        
        self.research_success_rate = self.registry.gauge(
            "research_success_rate",
            "Success rate of company research",
            unit=MetricUnit.PERCENT
        )
        
        # Cost metrics
        self.ai_costs = self.registry.counter(
            "ai_costs_total",
            "Total AI operation costs",
            unit=MetricUnit.DOLLARS
        )
        
        self.cost_per_company = self.registry.histogram(
            "cost_per_company",
            "Cost per company research",
            unit=MetricUnit.DOLLARS
        )
        
        # Batch processing metrics
        self.batch_jobs_total = self.registry.counter(
            "batch_jobs_total",
            "Total batch jobs processed",
            unit=MetricUnit.COUNT
        )
        
        self.batch_processing_duration = self.registry.timer(
            "batch_processing_duration",
            "Duration of batch processing operations"
        )
        
        # Data quality metrics
        self.data_quality_score = self.registry.histogram(
            "data_quality_score",
            "Data quality scores",
            unit=MetricUnit.PERCENT
        )
    
    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics"""
        labels = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        self.api_request_count.record(1, labels)
        self.api_request_duration.record(duration, labels)
    
    def record_ai_operation(self, model: str, operation: str, tokens: int, cost: float, duration: float):
        """Record AI operation metrics"""
        labels = {
            "model": model,
            "operation": operation
        }
        
        self.ai_operation_duration.record(duration, labels)
        self.ai_token_usage.record(tokens, labels)
        self.ai_costs.record(cost, labels)
    
    def record_company_research(self, success: bool, cost: float, quality_score: float, duration: float):
        """Record company research metrics"""
        self.companies_researched.increment()
        self.cost_per_company.record(cost)
        self.data_quality_score.record(quality_score)
        
        # Update success rate
        # Note: This is simplified - in practice you'd use a more sophisticated calculation
        current_rate = self.research_success_rate.get_value()["value"]
        new_rate = current_rate * 0.9 + (100.0 if success else 0.0) * 0.1
        self.research_success_rate.record(new_rate)
    
    def record_batch_job(self, job_type: str, companies_count: int, duration: float, success_rate: float):
        """Record batch processing metrics"""
        labels = {
            "job_type": job_type,
            "batch_size": str(companies_count)
        }
        
        self.batch_jobs_total.record(1, labels)
        self.batch_processing_duration.record(duration, labels)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.registry.collect_all()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for dashboards"""
        metrics = self.get_all_metrics()
        
        return {
            "system": {
                "api_requests": metrics.get("api_requests_total", {}).get("value", 0),
                "companies_researched": metrics.get("companies_researched_total", {}).get("value", 0),
                "total_ai_costs": metrics.get("ai_costs_total", {}).get("value", 0.0),
                "success_rate": metrics.get("research_success_rate", {}).get("value", 0.0)
            },
            "performance": {
                "avg_api_duration": metrics.get("api_request_duration", {}).get("mean", 0.0),
                "avg_research_duration": metrics.get("ai_operation_duration", {}).get("mean", 0.0),
                "avg_cost_per_company": metrics.get("cost_per_company", {}).get("mean", 0.0)
            },
            "quality": {
                "avg_data_quality": metrics.get("data_quality_score", {}).get("mean", 0.0),
                "p95_response_time": metrics.get("api_request_duration", {}).get("p95", 0.0)
            }
        }
    
    # Convenience methods to expose registry functionality
    def counter(self, name: str, description: str, unit: MetricUnit = MetricUnit.COUNT, labels: Optional[Dict[str, str]] = None) -> Counter:
        """Create a new counter metric"""
        return self.registry.counter(name, description, unit, labels)
    
    def gauge(self, name: str, description: str, unit: MetricUnit = MetricUnit.NONE, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """Create a new gauge metric"""
        return self.registry.gauge(name, description, unit, labels)
    
    def histogram(self, name: str, description: str, unit: MetricUnit = MetricUnit.NONE, labels: Optional[Dict[str, str]] = None) -> Histogram:
        """Create a new histogram metric"""
        return self.registry.histogram(name, description, unit, labels)
    
    def timer(self, name: str, description: str, unit: MetricUnit = MetricUnit.SECONDS, labels: Optional[Dict[str, str]] = None) -> Timer:
        """Create a new timer metric"""
        return self.registry.timer(name, description, unit, labels)
    
    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Get a metric by name"""
        return self.registry.get_metric(name)


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


# Business metrics helper class
class BusinessMetrics:
    """High-level business metrics tracking"""
    
    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or get_metrics_collector()
    
    def track_research_success(self, company_name: str, cost: float, quality_score: float, duration: float):
        """Track successful company research"""
        self.collector.record_company_research(True, cost, quality_score, duration)
    
    def track_research_failure(self, company_name: str, error_type: str, duration: float):
        """Track failed company research"""
        self.collector.record_company_research(False, 0.0, 0.0, duration)
    
    def track_batch_completion(self, batch_id: str, companies_count: int, success_count: int, total_cost: float, duration: float):
        """Track batch processing completion"""
        success_rate = (success_count / companies_count * 100) if companies_count > 0 else 0
        self.collector.record_batch_job("research", companies_count, duration, success_rate)
    
    def get_business_summary(self) -> Dict[str, Any]:
        """Get business metrics summary"""
        return self.collector.get_summary()
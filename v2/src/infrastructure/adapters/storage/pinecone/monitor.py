"""
Pinecone monitoring and performance tracking.

This module provides comprehensive monitoring capabilities for
Pinecone operations including metrics collection and analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import time
from collections import defaultdict, deque
import threading

from .config import PineconeConfig


logger = logging.getLogger(__name__)


@dataclass
class OperationMetric:
    """Metric for a single operation."""
    
    operation_type: str
    timestamp: datetime
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceWindow:
    """Performance metrics for a time window."""
    
    start_time: datetime
    end_time: datetime
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    @property
    def average_duration_ms(self) -> float:
        """Calculate average operation duration."""
        if self.total_operations == 0:
            return 0.0
        return self.total_duration_ms / self.total_operations
    
    def add_operation(self, duration_ms: float, success: bool):
        """Add operation to performance window."""
        self.total_operations += 1
        self.total_duration_ms += duration_ms
        
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)


class PineconeMonitor:
    """Comprehensive monitoring for Pinecone operations."""
    
    def __init__(self, config: PineconeConfig):
        self.config = config
        self.enabled = config.enable_monitoring
        
        # Metrics storage
        self._metrics: deque = deque(maxlen=10000)  # Keep last 10k operations
        self._operation_counters: Dict[str, int] = defaultdict(int)
        self._error_counters: Dict[str, int] = defaultdict(int)
        
        # Performance windows
        self._windows: Dict[str, PerformanceWindow] = {}
        self._window_duration = timedelta(minutes=5)  # 5-minute windows
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        if self.enabled:
            logger.info("Pinecone monitoring enabled")
            # Background tasks are started on demand
    
    def record_operation(
        self,
        operation_type: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a completed operation."""
        if not self.enabled:
            return
        
        timestamp = datetime.utcnow()
        
        # Use 0 duration if not provided
        if duration_ms is None:
            duration_ms = 0.0
        
        with self._lock:
            # Create metric
            metric = OperationMetric(
                operation_type=operation_type,
                timestamp=timestamp,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Store metric
            self._metrics.append(metric)
            
            # Update counters
            self._operation_counters[operation_type] += 1
            if not success:
                self._error_counters[operation_type] += 1
            
            # Update performance window
            self._update_performance_window(timestamp, duration_ms, success)
    
    def get_operation_metrics(
        self,
        operation_type: Optional[str] = None,
        time_window: Optional[timedelta] = None
    ) -> List[OperationMetric]:
        """Get operation metrics with optional filtering."""
        if not self.enabled:
            return []
        
        with self._lock:
            metrics = list(self._metrics)
        
        # Filter by operation type
        if operation_type:
            metrics = [m for m in metrics if m.operation_type == operation_type]
        
        # Filter by time window
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        return metrics
    
    def get_performance_summary(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.enabled:
            return {'monitoring_enabled': False}
        
        time_window = time_window or timedelta(hours=1)
        metrics = self.get_operation_metrics(time_window=time_window)
        
        if not metrics:
            return {
                'monitoring_enabled': True,
                'time_window_hours': time_window.total_seconds() / 3600,
                'total_operations': 0,
                'message': 'No operations in time window'
            }
        
        # Calculate overall statistics
        total_ops = len(metrics)
        successful_ops = sum(1 for m in metrics if m.success)
        failed_ops = total_ops - successful_ops
        
        durations = [m.duration_ms for m in metrics if m.duration_ms > 0]
        
        # Operation type breakdown
        op_breakdown = defaultdict(lambda: {'count': 0, 'success': 0, 'failure': 0})
        for metric in metrics:
            op_breakdown[metric.operation_type]['count'] += 1
            if metric.success:
                op_breakdown[metric.operation_type]['success'] += 1
            else:
                op_breakdown[metric.operation_type]['failure'] += 1
        
        # Error analysis
        error_summary = defaultdict(int)
        for metric in metrics:
            if not metric.success and metric.error_message:
                error_summary[metric.error_message] += 1
        
        return {
            'monitoring_enabled': True,
            'time_window_hours': time_window.total_seconds() / 3600,
            'summary': {
                'total_operations': total_ops,
                'successful_operations': successful_ops,
                'failed_operations': failed_ops,
                'success_rate_percent': (successful_ops / total_ops * 100) if total_ops > 0 else 0
            },
            'performance': {
                'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                'min_duration_ms': min(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'total_duration_ms': sum(durations)
            },
            'operations_breakdown': dict(op_breakdown),
            'top_errors': dict(sorted(error_summary.items(), key=lambda x: x[1], reverse=True)[:10]),
            'metrics_collected': len(self._metrics),
            'collection_period': {
                'start': min(m.timestamp for m in metrics).isoformat(),
                'end': max(m.timestamp for m in metrics).isoformat()
            }
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics."""
        if not self.enabled:
            return {'monitoring_enabled': False}
        
        # Get current window
        current_window = self._get_current_window()
        
        # Recent operations (last 60 seconds)
        recent_metrics = self.get_operation_metrics(time_window=timedelta(seconds=60))
        
        # Operations per minute
        ops_per_minute = len(recent_metrics)
        
        # Current error rate
        recent_errors = sum(1 for m in recent_metrics if not m.success)
        error_rate = (recent_errors / len(recent_metrics) * 100) if recent_metrics else 0
        
        return {
            'monitoring_enabled': True,
            'timestamp': datetime.utcnow().isoformat(),
            'current_window': {
                'operations_count': current_window.total_operations,
                'success_rate_percent': current_window.success_rate,
                'avg_duration_ms': current_window.average_duration_ms
            },
            'last_minute': {
                'operations_per_minute': ops_per_minute,
                'error_rate_percent': error_rate,
                'active_operations': len(recent_metrics)
            },
            'lifetime_totals': {
                'total_operations': sum(self._operation_counters.values()),
                'total_errors': sum(self._error_counters.values()),
                'metrics_collected': len(self._metrics)
            }
        }
    
    def get_operation_trends(
        self,
        operation_type: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get trend analysis for specific operation type."""
        if not self.enabled:
            return {'monitoring_enabled': False}
        
        time_window = time_window or timedelta(hours=6)
        metrics = self.get_operation_metrics(
            operation_type=operation_type,
            time_window=time_window
        )
        
        if not metrics:
            return {
                'operation_type': operation_type,
                'message': 'No data available for operation'
            }
        
        # Group by hour for trend analysis
        hourly_data = defaultdict(lambda: {'count': 0, 'success': 0, 'total_duration': 0.0})
        
        for metric in metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_data[hour_key]['count'] += 1
            if metric.success:
                hourly_data[hour_key]['success'] += 1
            hourly_data[hour_key]['total_duration'] += metric.duration_ms
        
        # Calculate trends
        trend_data = []
        for hour, data in sorted(hourly_data.items()):
            success_rate = (data['success'] / data['count'] * 100) if data['count'] > 0 else 0
            avg_duration = data['total_duration'] / data['count'] if data['count'] > 0 else 0
            
            trend_data.append({
                'timestamp': hour.isoformat(),
                'operations_count': data['count'],
                'success_rate_percent': success_rate,
                'avg_duration_ms': avg_duration
            })
        
        return {
            'operation_type': operation_type,
            'time_window_hours': time_window.total_seconds() / 3600,
            'trend_data': trend_data,
            'summary': {
                'total_operations': len(metrics),
                'overall_success_rate': sum(1 for m in metrics if m.success) / len(metrics) * 100,
                'avg_operations_per_hour': len(metrics) / (time_window.total_seconds() / 3600)
            }
        }
    
    def export_metrics(
        self,
        format_type: str = "json",
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Export metrics data for external analysis."""
        if not self.enabled:
            return {'error': 'Monitoring not enabled'}
        
        metrics = self.get_operation_metrics(time_window=time_window)
        
        if format_type == "json":
            return {
                'export_timestamp': datetime.utcnow().isoformat(),
                'metrics_count': len(metrics),
                'time_window': time_window.total_seconds() if time_window else None,
                'metrics': [
                    {
                        'operation_type': m.operation_type,
                        'timestamp': m.timestamp.isoformat(),
                        'duration_ms': m.duration_ms,
                        'success': m.success,
                        'error_message': m.error_message,
                        'metadata': m.metadata
                    }
                    for m in metrics
                ]
            }
        
        # Add other export formats as needed
        return {'error': f'Unsupported format: {format_type}'}
    
    def _update_performance_window(self, timestamp: datetime, duration_ms: float, success: bool) -> None:
        """Update current performance window."""
        window_start = timestamp.replace(second=0, microsecond=0)
        window_key = window_start.isoformat()
        
        if window_key not in self._windows:
            self._windows[window_key] = PerformanceWindow(
                start_time=window_start,
                end_time=window_start + self._window_duration
            )
        
        self._windows[window_key].add_operation(duration_ms, success)
    
    def _get_current_window(self) -> PerformanceWindow:
        """Get current performance window."""
        now = datetime.utcnow()
        window_start = now.replace(second=0, microsecond=0)
        window_key = window_start.isoformat()
        
        with self._lock:
            if window_key not in self._windows:
                self._windows[window_key] = PerformanceWindow(
                    start_time=window_start,
                    end_time=window_start + self._window_duration
                )
            
            return self._windows[window_key]
    
    async def start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        if not self.enabled or self._cleanup_task is not None:
            return
        
        # Start cleanup task to remove old metrics
        self._cleanup_task = asyncio.create_task(self._cleanup_old_data())
        
        # Start metrics collection task
        self._metrics_task = asyncio.create_task(self._collect_system_metrics())
    
    async def _cleanup_old_data(self) -> None:
        """Background task to cleanup old metrics and windows."""
        while self.enabled:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                with self._lock:
                    # Clean old windows (keep last 24 hours)
                    cutoff_time = datetime.utcnow() - timedelta(hours=24)
                    old_windows = [
                        key for key, window in self._windows.items()
                        if window.end_time < cutoff_time
                    ]
                    for key in old_windows:
                        del self._windows[key]
                
                logger.debug(f"Cleaned up {len(old_windows)} old performance windows")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _collect_system_metrics(self) -> None:
        """Background task to collect system-level metrics."""
        while self.enabled:
            try:
                await asyncio.sleep(self.config.metrics_collection_interval)
                
                # Collect memory usage, connection stats, etc.
                # This is a placeholder for system metrics collection
                
            except Exception as e:
                logger.error(f"Error in metrics collection task: {e}")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring and cleanup background tasks."""
        self.enabled = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Pinecone monitoring stopped")
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        if not self.enabled:
            return
        
        with self._lock:
            self._metrics.clear()
            self._operation_counters.clear()
            self._error_counters.clear()
            self._windows.clear()
        
        logger.info("Pinecone metrics reset")
    
    def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score based on recent performance."""
        if not self.enabled:
            return {'health_score': 'unknown', 'monitoring_enabled': False}
        
        # Get recent metrics (last hour)
        recent_metrics = self.get_operation_metrics(time_window=timedelta(hours=1))
        
        if not recent_metrics:
            return {
                'health_score': 'unknown',
                'message': 'No recent operations to analyze'
            }
        
        # Calculate health factors
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100
        
        durations = [m.duration_ms for m in recent_metrics if m.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Health scoring
        health_score = 100
        
        # Penalize low success rate
        if success_rate < 95:
            health_score -= (95 - success_rate) * 2
        
        # Penalize high latency (>1000ms is concerning)
        if avg_duration > 1000:
            health_score -= min(30, (avg_duration - 1000) / 100)
        
        # Determine health status
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 50:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'health_score': max(0, int(health_score)),
            'health_status': status,
            'factors': {
                'success_rate_percent': success_rate,
                'avg_duration_ms': avg_duration,
                'recent_operations': len(recent_metrics)
            },
            'monitoring_enabled': True
        }
#!/usr/bin/env python3
"""
Google Gemini Token Management System
====================================

Advanced token tracking and optimization for Google Gemini API:
- Real-time token usage monitoring
- Cost tracking and budget management
- Token optimization strategies
- Usage analytics and reporting
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .config import GeminiConfig, calculate_gemini_cost, GEMINI_MODEL_CAPABILITIES


logger = logging.getLogger(__name__)


@dataclass
class TokenUsageEntry:
    """Individual token usage record."""
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    request_type: str = "analysis"
    context_size: Optional[int] = None


@dataclass
class UsageStats:
    """Aggregated usage statistics."""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    average_cost_per_request: float = 0.0
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    daily_costs: Dict[str, float] = field(default_factory=dict)
    peak_tokens_per_minute: int = 0


class GeminiTokenManager:
    """
    Advanced token tracking and management for Gemini API.
    
    Provides comprehensive token usage monitoring, cost optimization,
    and budget management capabilities for production environments.
    """
    
    def __init__(self, config: GeminiConfig):
        """Initialize token manager."""
        self.config = config
        self._usage_history: List[TokenUsageEntry] = []
        self._daily_usage: Dict[str, List[TokenUsageEntry]] = {}
        self._minute_buckets: Dict[int, int] = {}  # Token usage per minute
        self._lock = asyncio.Lock()
        
        # Cost thresholds
        self.daily_cost_limit = config.daily_cost_limit
        self.request_cost_limit = config.max_cost_per_request
        
        # Token rate limiting
        self.tokens_per_minute_limit = config.tokens_per_minute
        
        logger.info(f"📊 Token manager initialized with ${config.daily_cost_limit:.2f} daily limit")
    
    async def track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = None,
        request_type: str = "analysis",
        context_size: Optional[int] = None
    ) -> TokenUsageEntry:
        """
        Track token usage for a request.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            model: Model used for the request
            request_type: Type of request (analysis, embedding, etc.)
            context_size: Size of context window used
            
        Returns:
            TokenUsageEntry with tracked information
        """
        model = model or self.config.model
        timestamp = datetime.now()
        cost = calculate_gemini_cost(input_tokens, output_tokens, model)
        
        entry = TokenUsageEntry(
            timestamp=timestamp,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            request_type=request_type,
            context_size=context_size
        )
        
        async with self._lock:
            # Add to history
            self._usage_history.append(entry)
            
            # Track daily usage
            date_key = timestamp.strftime('%Y-%m-%d')
            if date_key not in self._daily_usage:
                self._daily_usage[date_key] = []
            self._daily_usage[date_key].append(entry)
            
            # Track minute-level token usage for rate limiting
            minute_key = int(timestamp.timestamp() // 60)
            total_tokens = input_tokens + output_tokens
            self._minute_buckets[minute_key] = self._minute_buckets.get(minute_key, 0) + total_tokens
            
            # Clean old minute buckets (keep only last hour)
            current_minute = int(time.time() // 60)
            old_minutes = [k for k in self._minute_buckets.keys() if k < current_minute - 60]
            for old_minute in old_minutes:
                del self._minute_buckets[old_minute]
        
        logger.debug(f"📊 Tracked usage: {total_tokens} tokens, ${cost:.4f} for {model}")
        
        return entry
    
    async def check_rate_limits(self) -> Tuple[bool, str]:
        """
        Check if current usage is within rate limits.
        
        Returns:
            Tuple of (is_within_limits, reason_if_not)
        """
        async with self._lock:
            current_minute = int(time.time() // 60)
            
            # Check tokens per minute
            recent_tokens = sum(
                tokens for minute, tokens in self._minute_buckets.items()
                if minute >= current_minute - 1  # Last minute
            )
            
            if recent_tokens > self.tokens_per_minute_limit:
                return False, f"Token rate limit exceeded: {recent_tokens}/{self.tokens_per_minute_limit} tokens/minute"
            
            # Check daily cost limit
            today = datetime.now().strftime('%Y-%m-%d')
            daily_cost = sum(entry.cost for entry in self._daily_usage.get(today, []))
            
            if daily_cost > self.daily_cost_limit:
                return False, f"Daily cost limit exceeded: ${daily_cost:.2f}/${self.daily_cost_limit:.2f}"
            
            return True, ""
    
    async def estimate_request_cost(
        self,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        model: str = None
    ) -> Tuple[float, bool]:
        """
        Estimate cost for a potential request.
        
        Args:
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            model: Model to use for estimation
            
        Returns:
            Tuple of (estimated_cost, is_within_budget)
        """
        model = model or self.config.model
        estimated_cost = calculate_gemini_cost(estimated_input_tokens, estimated_output_tokens, model)
        
        # Check against per-request limit
        within_request_limit = estimated_cost <= self.request_cost_limit
        
        # Check against daily limit
        today = datetime.now().strftime('%Y-%m-%d')
        daily_cost = sum(entry.cost for entry in self._daily_usage.get(today, []))
        within_daily_limit = (daily_cost + estimated_cost) <= self.daily_cost_limit
        
        is_within_budget = within_request_limit and within_daily_limit
        
        return estimated_cost, is_within_budget
    
    async def get_daily_stats(self, date: Optional[datetime] = None) -> UsageStats:
        """
        Get usage statistics for a specific day.
        
        Args:
            date: Date to get stats for (defaults to today)
            
        Returns:
            UsageStats for the specified day
        """
        if date is None:
            date = datetime.now()
        
        date_key = date.strftime('%Y-%m-%d')
        daily_entries = self._daily_usage.get(date_key, [])
        
        if not daily_entries:
            return UsageStats()
        
        # Calculate aggregated stats
        total_requests = len(daily_entries)
        total_input_tokens = sum(entry.input_tokens for entry in daily_entries)
        total_output_tokens = sum(entry.output_tokens for entry in daily_entries)
        total_cost = sum(entry.cost for entry in daily_entries)
        
        # Group by model
        requests_by_model = {}
        cost_by_model = {}
        
        for entry in daily_entries:
            requests_by_model[entry.model] = requests_by_model.get(entry.model, 0) + 1
            cost_by_model[entry.model] = cost_by_model.get(entry.model, 0.0) + entry.cost
        
        return UsageStats(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost=total_cost,
            average_cost_per_request=total_cost / total_requests if total_requests > 0 else 0.0,
            requests_by_model=requests_by_model,
            cost_by_model=cost_by_model,
            daily_costs={date_key: total_cost}
        )
    
    async def get_usage_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get usage trends over the specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_stats = []
        total_cost = 0.0
        total_requests = 0
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            stats = await self.get_daily_stats(date)
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'cost': stats.total_cost,
                'requests': stats.total_requests,
                'tokens': stats.total_input_tokens + stats.total_output_tokens
            })
            total_cost += stats.total_cost
            total_requests += stats.total_requests
        
        # Calculate trends
        recent_half = daily_stats[-days//2:]
        earlier_half = daily_stats[:days//2] if days > 2 else daily_stats[:1]
        
        recent_avg_cost = sum(d['cost'] for d in recent_half) / len(recent_half) if recent_half else 0
        earlier_avg_cost = sum(d['cost'] for d in earlier_half) / len(earlier_half) if earlier_half else 0
        
        cost_trend = "increasing" if recent_avg_cost > earlier_avg_cost * 1.1 else \
                    "decreasing" if recent_avg_cost < earlier_avg_cost * 0.9 else "stable"
        
        return {
            'period_days': days,
            'daily_stats': daily_stats,
            'total_cost': total_cost,
            'total_requests': total_requests,
            'average_daily_cost': total_cost / days,
            'average_daily_requests': total_requests / days,
            'cost_trend': cost_trend,
            'trend_percentage': ((recent_avg_cost - earlier_avg_cost) / earlier_avg_cost * 100) if earlier_avg_cost > 0 else 0
        }
    
    async def optimize_model_selection(self, estimated_tokens: int, task_complexity: str = "medium") -> str:
        """
        Recommend optimal model based on usage patterns and requirements.
        
        Args:
            estimated_tokens: Estimated token count for the task
            task_complexity: Complexity level (simple, medium, complex)
            
        Returns:
            Recommended model name
        """
        # Check budget remaining
        today = datetime.now().strftime('%Y-%m-%d')
        daily_cost = sum(entry.cost for entry in self._daily_usage.get(today, []))
        budget_remaining = self.daily_cost_limit - daily_cost
        
        # Get model capabilities
        model_options = []
        
        for model, caps in GEMINI_MODEL_CAPABILITIES.items():
            if estimated_tokens <= caps['max_context']:
                # Estimate cost for this model
                estimated_cost = calculate_gemini_cost(estimated_tokens, estimated_tokens // 4, model)
                
                if estimated_cost <= budget_remaining:
                    model_options.append({
                        'model': model,
                        'cost': estimated_cost,
                        'relative_cost': caps['relative_cost'],
                        'relative_speed': caps['relative_speed'],
                        'suitable_for': caps['best_for']
                    })
        
        if not model_options:
            # No models within budget
            logger.warning("⚠️ No models within current budget")
            return self.config.model  # Fallback to default
        
        # Select based on task complexity and cost
        if task_complexity == "simple":
            # Choose cheapest option
            best_model = min(model_options, key=lambda x: x['cost'])
        elif task_complexity == "complex":
            # Choose best quality within budget
            complex_models = [m for m in model_options if 'complex_analysis' in m['suitable_for'] or 'large_context' in m['suitable_for']]
            best_model = complex_models[0] if complex_models else min(model_options, key=lambda x: x['cost'])
        else:
            # Balanced choice
            balanced_models = [m for m in model_options if 'general_analysis' in m['suitable_for'] or 'balanced_performance' in m['suitable_for']]
            best_model = balanced_models[0] if balanced_models else min(model_options, key=lambda x: x['cost'])
        
        logger.info(f"🎯 Recommended model: {best_model['model']} (${best_model['cost']:.4f})")
        
        return best_model['model']
    
    async def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current usage status.
        
        Returns:
            Dictionary with current usage information
        """
        today = datetime.now().strftime('%Y-%m-%d')
        daily_entries = self._daily_usage.get(today, [])
        
        daily_cost = sum(entry.cost for entry in daily_entries)
        daily_requests = len(daily_entries)
        daily_tokens = sum(entry.input_tokens + entry.output_tokens for entry in daily_entries)
        
        # Current minute token usage
        current_minute = int(time.time() // 60)
        current_minute_tokens = self._minute_buckets.get(current_minute, 0)
        
        return {
            'daily_cost': daily_cost,
            'daily_cost_limit': self.daily_cost_limit,
            'cost_utilization_percent': (daily_cost / self.daily_cost_limit) * 100 if self.daily_cost_limit > 0 else 0,
            'daily_requests': daily_requests,
            'daily_tokens': daily_tokens,
            'current_minute_tokens': current_minute_tokens,
            'minute_token_limit': self.tokens_per_minute_limit,
            'minute_utilization_percent': (current_minute_tokens / self.tokens_per_minute_limit) * 100 if self.tokens_per_minute_limit > 0 else 0,
            'budget_remaining': max(0, self.daily_cost_limit - daily_cost),
            'within_limits': daily_cost < self.daily_cost_limit and current_minute_tokens < self.tokens_per_minute_limit
        }
    
    def clear_old_data(self, days_to_keep: int = 30) -> None:
        """
        Clear usage data older than specified days.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_key = cutoff_date.strftime('%Y-%m-%d')
        
        # Clean daily usage
        old_dates = [date for date in self._daily_usage.keys() if date < cutoff_key]
        for old_date in old_dates:
            del self._daily_usage[old_date]
        
        # Clean usage history
        self._usage_history = [
            entry for entry in self._usage_history
            if entry.timestamp >= cutoff_date
        ]
        
        logger.info(f"🧹 Cleaned usage data older than {days_to_keep} days")
    
    async def export_usage_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export usage data for analysis.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported usage data
        """
        async with self._lock:
            if format == "json":
                return {
                    'usage_history': [
                        {
                            'timestamp': entry.timestamp.isoformat(),
                            'model': entry.model,
                            'input_tokens': entry.input_tokens,
                            'output_tokens': entry.output_tokens,
                            'cost': entry.cost,
                            'request_type': entry.request_type,
                            'context_size': entry.context_size
                        }
                        for entry in self._usage_history
                    ],
                    'daily_summaries': {
                        date: {
                            'total_cost': sum(e.cost for e in entries),
                            'total_requests': len(entries),
                            'total_tokens': sum(e.input_tokens + e.output_tokens for e in entries)
                        }
                        for date, entries in self._daily_usage.items()
                    },
                    'export_timestamp': datetime.now().isoformat()
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")
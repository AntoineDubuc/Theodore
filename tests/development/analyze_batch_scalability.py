#!/usr/bin/env python3
"""
Analyze Theodore's batch processing scalability and identify optimal concurrency levels
"""

import os
import time
import psutil
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import json

# Simulated resource monitoring
class ResourceMonitor:
    """Monitor system resources during batch processing"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.cpu_samples = []
        self.monitoring = False
        
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.initial_memory
        self.cpu_samples = []
        
    def sample_resources(self):
        """Sample current resource usage"""
        if not self.monitoring:
            return
            
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent()
        
        self.peak_memory = max(self.peak_memory, memory_mb)
        self.cpu_samples.append(cpu_percent)
        
    def get_summary(self) -> Dict[str, float]:
        """Get resource usage summary"""
        return {
            'initial_memory_mb': self.initial_memory,
            'peak_memory_mb': self.peak_memory,
            'memory_increase_mb': self.peak_memory - self.initial_memory,
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            'max_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0
        }

def analyze_processing_bottlenecks():
    """Analyze Theodore's processing pipeline bottlenecks"""
    
    print("🔍 ANALYZING THEODORE BATCH PROCESSING SCALABILITY")
    print("=" * 70)
    
    # Current Theodore architecture analysis
    bottlenecks = {
        "sequential_company_processing": {
            "description": "Companies processed one at a time in main pipeline",
            "impact": "HIGH",
            "current_limitation": "1 company at a time",
            "resource_usage": "Single-threaded company processing"
        },
        "crawl4ai_browser_instances": {
            "description": "FIXED - Now uses single browser per company (3x improvement)",
            "impact": "RESOLVED",
            "current_limitation": "Single browser per company (optimized)",
            "resource_usage": "Minimal browser overhead"
        },
        "llm_api_calls": {
            "description": "Rate limits on Gemini/Bedrock API calls",
            "impact": "MEDIUM",
            "current_limitation": "API rate limits and token quotas",
            "resource_usage": "Network I/O bound"
        },
        "vector_database_operations": {
            "description": "Pinecone upsert operations",
            "impact": "LOW",
            "current_limitation": "Network latency to Pinecone",
            "resource_usage": "Network I/O bound"
        },
        "memory_per_company": {
            "description": "Memory usage per company during processing",
            "impact": "MEDIUM",
            "current_limitation": "Page content + embeddings in memory",
            "resource_usage": "~50-100MB per company"
        },
        "progress_logging": {
            "description": "Thread-safe progress logging system",
            "impact": "LOW",
            "current_limitation": "Thread synchronization overhead",
            "resource_usage": "Minimal"
        }
    }
    
    print("📊 CURRENT BOTTLENECK ANALYSIS:")
    print("-" * 50)
    
    for bottleneck, details in bottlenecks.items():
        status = "🚨" if details["impact"] == "HIGH" else "⚠️" if details["impact"] == "MEDIUM" else "✅"
        print(f"\n{status} {bottleneck.upper().replace('_', ' ')}")
        print(f"   Description: {details['description']}")
        print(f"   Impact: {details['impact']}")
        print(f"   Limitation: {details['current_limitation']}")
        print(f"   Resource: {details['resource_usage']}")
    
    # Estimate optimal concurrency based on resource constraints
    print(f"\n🎯 OPTIMAL CONCURRENCY ANALYSIS:")
    print("-" * 50)
    
    # System resources
    cpu_cores = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"💻 System Resources:")
    print(f"   CPU Cores: {cpu_cores}")
    print(f"   Memory: {memory_gb:.1f} GB")
    
    # Resource-based concurrency calculations
    calculations = {
        "memory_based": {
            "assumption": "100MB per company + 2GB system overhead",
            "formula": f"({memory_gb:.1f}GB - 2GB) / 0.1GB",
            "max_concurrent": int((memory_gb - 2) / 0.1),
            "practical_limit": min(int((memory_gb - 2) / 0.1), 20)  # Cap at 20 for safety
        },
        "cpu_based": {
            "assumption": "Each company uses 1 core for I/O + LLM processing",
            "formula": f"{cpu_cores} cores * 2 (I/O bound factor)",
            "max_concurrent": cpu_cores * 2,
            "practical_limit": min(cpu_cores * 2, 15)  # Cap at 15 for API limits
        },
        "api_rate_limit_based": {
            "assumption": "Gemini: 60 requests/minute, Bedrock: 100 requests/minute",
            "formula": "Rate limits / (4 requests per company * safety factor)",
            "max_concurrent": 60 // (4 * 2),  # Conservative estimate
            "practical_limit": 7  # Be conservative with API limits
        },
        "network_io_based": {
            "assumption": "Network I/O bound (Crawl4AI + APIs)",
            "formula": "Optimized for concurrent network operations",
            "max_concurrent": 10,
            "practical_limit": 10
        }
    }
    
    print(f"\n📊 CONCURRENCY CALCULATIONS:")
    for calc_type, calc in calculations.items():
        print(f"\n   {calc_type.upper().replace('_', ' ')}:")
        print(f"     Assumption: {calc['assumption']}")
        print(f"     Formula: {calc['formula']}")
        print(f"     Max Theoretical: {calc['max_concurrent']}")
        print(f"     Practical Limit: {calc['practical_limit']}")
    
    # Determine optimal range
    practical_limits = [calc['practical_limit'] for calc in calculations.values()]
    recommended_min = min(practical_limits)
    recommended_max = max(3, int(sum(practical_limits) / len(practical_limits)))
    
    print(f"\n🎯 RECOMMENDED CONCURRENCY RANGE:")
    print(f"   Conservative (safe): 2-3 companies")
    print(f"   Optimal (balanced): {recommended_min}-{recommended_max} companies") 
    print(f"   Aggressive (max): {max(practical_limits)} companies")
    
    # Performance projections
    print(f"\n⏱️ PERFORMANCE PROJECTIONS:")
    print("-" * 50)
    
    # Current performance: ~30-45 seconds per company
    time_per_company = 35  # Average seconds
    
    scenarios = [
        {"name": "Current (Sequential)", "concurrent": 1, "time_per": time_per_company},
        {"name": "Conservative Parallel", "concurrent": 3, "time_per": time_per_company + 5},  # Small overhead
        {"name": "Optimal Parallel", "concurrent": recommended_max, "time_per": time_per_company + 10},  # Medium overhead
        {"name": "Aggressive Parallel", "concurrent": max(practical_limits), "time_per": time_per_company + 15}  # Higher overhead
    ]
    
    companies_to_process = [10, 50, 100, 400]  # David's survey sizes
    
    print(f"\n📈 Processing Time Estimates (minutes):")
    print(f"{'Scenario':<20} {'10 companies':<12} {'50 companies':<12} {'100 companies':<13} {'400 companies':<13}")
    print("-" * 80)
    
    for scenario in scenarios:
        times = []
        for company_count in companies_to_process:
            total_time = (company_count * scenario["time_per"]) / scenario["concurrent"] / 60  # Convert to minutes
            times.append(f"{total_time:.1f}m")
        
        print(f"{scenario['name']:<20} {times[0]:<12} {times[1]:<12} {times[2]:<13} {times[3]:<13}")
    
    # Resource usage warnings
    print(f"\n⚠️ RESOURCE USAGE WARNINGS:")
    print("-" * 50)
    
    warnings = [
        "Memory: Each company consumes ~100MB during processing",
        "Network: High bandwidth usage for page crawling",
        "API Limits: Gemini/Bedrock rate limits may throttle processing",
        "Pinecone: Vector database operations scale well",
        "Browser Memory: Crawl4AI optimized but still memory-intensive"
    ]
    
    for warning in warnings:
        print(f"   ⚠️ {warning}")
    
    # Recommendations
    print(f"\n💡 SCALABILITY RECOMMENDATIONS:")
    print("-" * 50)
    
    recommendations = [
        f"Start with 3-5 concurrent companies to test system limits",
        f"Monitor memory usage - should not exceed {memory_gb * 0.8:.1f}GB",
        f"Watch API rate limits - implement backoff if needed",
        f"Consider processing in batches of 50-100 companies",
        f"Use progress monitoring to detect bottlenecks",
        f"Scale up gradually: 3 → 5 → 7 → 10 concurrent companies"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    return {
        "recommended_min": recommended_min,
        "recommended_max": recommended_max,
        "bottlenecks": bottlenecks,
        "system_specs": {
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb
        }
    }

def estimate_processing_capacity():
    """Estimate how many companies can be processed before slowdown"""
    
    print(f"\n🚀 PROCESSING CAPACITY ANALYSIS:")
    print("-" * 50)
    
    # Current system performance baseline
    baseline = {
        "time_per_company_seconds": 35,
        "memory_per_company_mb": 100,
        "api_calls_per_company": 4,  # LLM analysis + page selection + content aggregation + embedding
        "pages_per_company": 15  # Average pages crawled
    }
    
    # System limits
    limits = {
        "available_memory_gb": psutil.virtual_memory().available / (1024**3),
        "api_rate_limit_per_minute": 60,  # Conservative Gemini estimate
        "max_browser_instances": 5,  # Practical limit for Crawl4AI
        "network_bandwidth_factor": 1.0  # No specific limit assumed
    }
    
    print(f"📊 BASELINE PERFORMANCE:")
    for key, value in baseline.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🔒 SYSTEM LIMITS:")
    for key, value in limits.items():
        unit = "GB" if "gb" in key else "per minute" if "minute" in key else "instances" if "instances" in key else ""
        print(f"   {key.replace('_', ' ').title()}: {value} {unit}")
    
    # Calculate capacity limits
    capacity_limits = {
        "memory_limit": int(limits["available_memory_gb"] * 1024 / baseline["memory_per_company_mb"]),
        "api_rate_limit": int(limits["api_rate_limit_per_minute"] / baseline["api_calls_per_company"]),
        "browser_limit": limits["max_browser_instances"]
    }
    
    print(f"\n📈 CAPACITY CALCULATIONS:")
    for limit_type, capacity in capacity_limits.items():
        print(f"   {limit_type.replace('_', ' ').title()}: {capacity} concurrent companies")
    
    # Practical recommendations
    conservative_limit = min(capacity_limits.values())
    optimal_limit = min(conservative_limit * 1.5, 10)  # 50% buffer, max 10
    
    print(f"\n🎯 PRACTICAL CAPACITY RECOMMENDATIONS:")
    print(f"   Conservative Limit: {conservative_limit} companies")
    print(f"   Optimal Target: {int(optimal_limit)} companies")
    print(f"   Warning Threshold: {conservative_limit * 2} companies (expect slowdown)")
    
    # Slowdown indicators
    print(f"\n⚠️ SLOWDOWN INDICATORS:")
    slowdown_thresholds = [
        f"Memory usage > {limits['available_memory_gb'] * 0.8:.1f}GB",
        f"API response times > 10 seconds",
        f"Browser initialization time > 5 seconds",
        f"Processing time per company > {baseline['time_per_company_seconds'] * 1.5:.0f} seconds"
    ]
    
    for threshold in slowdown_thresholds:
        print(f"   🚨 {threshold}")
    
    return {
        "conservative_limit": conservative_limit,
        "optimal_limit": int(optimal_limit),
        "warning_threshold": conservative_limit * 2,
        "baseline_performance": baseline,
        "system_limits": limits
    }

if __name__ == "__main__":
    # Run analysis
    scalability_analysis = analyze_processing_bottlenecks()
    capacity_analysis = estimate_processing_capacity()
    
    print(f"\n" + "=" * 70)
    print(f"📋 FINAL RECOMMENDATIONS")
    print(f"=" * 70)
    
    print(f"\n🎯 OPTIMAL BATCH PROCESSING CONFIGURATION:")
    print(f"   Start with: 3 concurrent companies")
    print(f"   Scale to: {capacity_analysis['optimal_limit']} concurrent companies")
    print(f"   Monitor at: {capacity_analysis['warning_threshold']} companies (slowdown expected)")
    
    print(f"\n⏱️ EXPECTED PERFORMANCE:")
    optimal_concurrent = capacity_analysis['optimal_limit']
    time_per_company = 40  # With concurrency overhead
    
    for company_count in [10, 50, 100]:
        total_minutes = (company_count * time_per_company) / optimal_concurrent / 60
        print(f"   {company_count} companies: ~{total_minutes:.1f} minutes")
    
    print(f"\n✅ IMPLEMENTATION STEPS:")
    steps = [
        "Update BatchProcessorService concurrency from 2 to 3-5",
        "Add resource monitoring to detect bottlenecks",
        "Implement adaptive concurrency based on performance",
        "Test with 10 companies before scaling up",
        "Monitor memory usage and API response times"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
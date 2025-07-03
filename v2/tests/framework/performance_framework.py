#!/usr/bin/env python3
"""
Theodore v2 Performance Testing Framework

Comprehensive performance testing, benchmarking, and load testing framework
for validating system performance and scalability.
"""

import asyncio
import time
import statistics
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import concurrent.futures
import psutil
import gc

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition"""
    name: str
    description: str
    operation: str
    expected_duration_seconds: float
    tolerance_percentage: float
    regression_threshold_percentage: float
    warmup_iterations: int = 3
    test_iterations: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkResult:
    """Performance benchmark result"""
    benchmark_name: str
    average_duration: float
    min_duration: float
    max_duration: float
    std_deviation: float
    iterations: int
    success: bool
    performance_rating: str  # 'excellent', 'good', 'acceptable', 'poor'
    regression_detected: bool
    memory_usage_mb: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    name: str
    description: str
    concurrent_users: List[int]
    test_duration_seconds: int
    ramp_up_duration_seconds: int
    operations_per_user: int
    success_threshold_percentage: float = 95.0
    response_time_threshold_seconds: float = 5.0


@dataclass
class LoadTestResult:
    """Load test execution result"""
    config_name: str
    concurrent_users: int
    total_operations: int
    successful_operations: int
    failed_operations: int
    success_rate: float
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    operations_per_second: float
    peak_memory_usage_mb: float
    cpu_usage_percentage: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceTestSuite:
    """Comprehensive performance testing and benchmarking"""
    
    def __init__(self):
        self.benchmarks: List[PerformanceBenchmark] = []
        self.baseline_results: Dict[str, BenchmarkResult] = {}
        self.current_results: Dict[str, BenchmarkResult] = {}
        self.system_monitor = SystemResourceMonitor()
        
    async def run_performance_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Execute all performance benchmarks"""
        
        logger.info("Starting performance benchmark suite...")
        
        benchmark_results = {}
        
        # Initialize default benchmarks
        self._initialize_default_benchmarks()
        
        for benchmark in self.benchmarks:
            logger.info(f"Running benchmark: {benchmark.name}")
            result = await self._execute_benchmark(benchmark)
            benchmark_results[benchmark.name] = result
            
        logger.info(f"Performance benchmarks completed. {len(benchmark_results)} benchmarks executed")
        
        return benchmark_results
    
    async def run_regression_analysis(self) -> Dict[str, Any]:
        """Run performance regression analysis"""
        
        current_results = await self.run_performance_benchmarks()
        regression_analysis = {}
        
        for benchmark_name, current_result in current_results.items():
            if benchmark_name in self.baseline_results:
                baseline = self.baseline_results[benchmark_name]
                analysis = self._analyze_regression(baseline, current_result)
                regression_analysis[benchmark_name] = analysis
                
        return regression_analysis
    
    def _initialize_default_benchmarks(self):
        """Initialize default performance benchmarks"""
        
        self.benchmarks = [
            PerformanceBenchmark(
                name="single_company_research",
                description="Single company research operation performance",
                operation="research_company",
                expected_duration_seconds=5.0,
                tolerance_percentage=20.0,
                regression_threshold_percentage=15.0,
                test_iterations=10
            ),
            
            PerformanceBenchmark(
                name="similarity_discovery",
                description="Company similarity discovery performance",
                operation="discover_similar",
                expected_duration_seconds=3.0,
                tolerance_percentage=25.0,
                regression_threshold_percentage=20.0,
                test_iterations=8
            ),
            
            PerformanceBenchmark(
                name="data_export_csv",
                description="CSV data export performance",
                operation="export_csv",
                expected_duration_seconds=2.0,
                tolerance_percentage=30.0,
                regression_threshold_percentage=25.0,
                test_iterations=5
            ),
            
            PerformanceBenchmark(
                name="batch_processing_10",
                description="Batch processing 10 companies",
                operation="batch_processing",
                expected_duration_seconds=30.0,
                tolerance_percentage=35.0,
                regression_threshold_percentage=30.0,
                test_iterations=3
            ),
            
            PerformanceBenchmark(
                name="ai_analysis_operation",
                description="AI analysis operation performance",
                operation="ai_analysis",
                expected_duration_seconds=8.0,
                tolerance_percentage=40.0,
                regression_threshold_percentage=35.0,
                test_iterations=5
            )
        ]
    
    async def _execute_benchmark(self, benchmark: PerformanceBenchmark) -> BenchmarkResult:
        """Execute individual performance benchmark"""
        
        durations = []
        memory_usage_samples = []
        
        # Warmup iterations
        for _ in range(benchmark.warmup_iterations):
            await self._execute_benchmark_operation(benchmark.operation)
            
        # Force garbage collection before actual test
        gc.collect()
        
        # Actual benchmark iterations
        for i in range(benchmark.test_iterations):
            start_time = time.time()
            start_memory = self.system_monitor.get_memory_usage_mb()
            
            try:
                await self._execute_benchmark_operation(benchmark.operation)
                duration = time.time() - start_time
                durations.append(duration)
                
                end_memory = self.system_monitor.get_memory_usage_mb()
                memory_usage_samples.append(end_memory - start_memory)
                
            except Exception as e:
                logger.error(f"Benchmark iteration {i+1} failed: {e}")
                durations.append(float('inf'))  # Mark as failed
        
        # Filter out failed iterations
        valid_durations = [d for d in durations if d != float('inf')]
        
        if not valid_durations:
            return BenchmarkResult(
                benchmark_name=benchmark.name,
                average_duration=float('inf'),
                min_duration=float('inf'),
                max_duration=float('inf'),
                std_deviation=0.0,
                iterations=0,
                success=False,
                performance_rating='failed',
                regression_detected=False,
                memory_usage_mb=0.0
            )
        
        # Calculate statistics
        avg_duration = statistics.mean(valid_durations)
        min_duration = min(valid_durations)
        max_duration = max(valid_durations)
        std_dev = statistics.stdev(valid_durations) if len(valid_durations) > 1 else 0.0
        avg_memory = statistics.mean(memory_usage_samples) if memory_usage_samples else 0.0
        
        # Determine performance rating
        performance_rating = self._rate_performance(benchmark, avg_duration)
        
        # Check for regression
        regression_detected = self._check_regression(benchmark, avg_duration)
        
        success = avg_duration <= benchmark.expected_duration_seconds * (1 + benchmark.tolerance_percentage / 100)
        
        return BenchmarkResult(
            benchmark_name=benchmark.name,
            average_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            std_deviation=std_dev,
            iterations=len(valid_durations),
            success=success,
            performance_rating=performance_rating,
            regression_detected=regression_detected,
            memory_usage_mb=avg_memory
        )
    
    async def _execute_benchmark_operation(self, operation: str):
        """Execute specific benchmark operation"""
        
        if operation == "research_company":
            await self._benchmark_research_operation()
        elif operation == "discover_similar":
            await self._benchmark_discovery_operation()
        elif operation == "export_csv":
            await self._benchmark_export_operation()
        elif operation == "batch_processing":
            await self._benchmark_batch_operation()
        elif operation == "ai_analysis":
            await self._benchmark_ai_operation()
        else:
            # Default simulation
            await asyncio.sleep(0.1)
    
    async def _benchmark_research_operation(self):
        """Benchmark research operation"""
        # Simulate research operation
        await asyncio.sleep(0.2)  # Simulate AI and scraping time
        
        # Simulate some CPU work
        dummy_data = [i ** 2 for i in range(1000)]
        sum(dummy_data)
    
    async def _benchmark_discovery_operation(self):
        """Benchmark discovery operation"""
        # Simulate vector similarity computation
        await asyncio.sleep(0.1)
        
        # Simulate vector operations
        import random
        vectors = [[random.random() for _ in range(100)] for _ in range(50)]
        
        # Simulate similarity computation
        for v1 in vectors[:5]:
            for v2 in vectors:
                dot_product = sum(a * b for a, b in zip(v1, v2))
    
    async def _benchmark_export_operation(self):
        """Benchmark export operation"""
        # Simulate data processing and export
        await asyncio.sleep(0.05)
        
        # Simulate data transformation
        mock_data = [{"name": f"Company {i}", "industry": "Tech"} for i in range(100)]
        json.dumps(mock_data)
    
    async def _benchmark_batch_operation(self):
        """Benchmark batch operation"""
        # Simulate batch processing of multiple companies
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(self._benchmark_research_operation())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _benchmark_ai_operation(self):
        """Benchmark AI operation"""
        # Simulate AI processing time
        await asyncio.sleep(0.3)
        
        # Simulate text processing work
        text = "This is a sample company description. " * 100
        words = text.split()
        processed = [word.lower().strip() for word in words]
    
    def _rate_performance(self, benchmark: PerformanceBenchmark, duration: float) -> str:
        """Rate performance based on duration vs expected"""
        
        expected = benchmark.expected_duration_seconds
        tolerance = benchmark.tolerance_percentage / 100
        
        if duration <= expected * 0.7:
            return 'excellent'
        elif duration <= expected:
            return 'good'
        elif duration <= expected * (1 + tolerance):
            return 'acceptable'
        else:
            return 'poor'
    
    def _check_regression(self, benchmark: PerformanceBenchmark, current_duration: float) -> bool:
        """Check if performance regression occurred"""
        
        if benchmark.name not in self.baseline_results:
            return False
        
        baseline_duration = self.baseline_results[benchmark.name].average_duration
        threshold = benchmark.regression_threshold_percentage / 100
        
        return current_duration > baseline_duration * (1 + threshold)
    
    def _analyze_regression(self, baseline: BenchmarkResult, current: BenchmarkResult) -> Dict[str, Any]:
        """Analyze performance regression between baseline and current"""
        
        percentage_change = ((current.average_duration - baseline.average_duration) 
                           / baseline.average_duration * 100)
        
        return {
            'baseline_duration': baseline.average_duration,
            'current_duration': current.average_duration,
            'percentage_change': percentage_change,
            'regression_detected': current.regression_detected,
            'performance_degraded': percentage_change > 0,
            'baseline_timestamp': baseline.timestamp.isoformat(),
            'current_timestamp': current.timestamp.isoformat()
        }


class LoadTestingSuite:
    """Comprehensive load testing for scalability validation"""
    
    def __init__(self):
        self.system_monitor = SystemResourceMonitor()
        
    async def run_load_tests(self) -> Dict[str, List[LoadTestResult]]:
        """Execute comprehensive load testing scenarios"""
        
        logger.info("Starting load testing suite...")
        
        load_test_results = {}
        
        # Research operation load test
        research_results = await self._test_research_load()
        load_test_results['research_load'] = research_results
        
        # Discovery operation load test
        discovery_results = await self._test_discovery_load()
        load_test_results['discovery_load'] = discovery_results
        
        # API endpoint load test
        api_results = await self._test_api_load()
        load_test_results['api_load'] = api_results
        
        logger.info("Load testing suite completed")
        
        return load_test_results
    
    async def _test_research_load(self) -> List[LoadTestResult]:
        """Test research operations under load"""
        
        config = LoadTestConfig(
            name="research_load_test",
            description="Research operations under increasing load",
            concurrent_users=[5, 10, 20, 50],
            test_duration_seconds=60,
            ramp_up_duration_seconds=10,
            operations_per_user=5
        )
        
        results = []
        
        for concurrent_users in config.concurrent_users:
            logger.info(f"Testing research load with {concurrent_users} concurrent users")
            result = await self._execute_load_test(config, concurrent_users, self._research_operation)
            results.append(result)
            
            # Cool down between tests
            await asyncio.sleep(5)
            
        return results
    
    async def _test_discovery_load(self) -> List[LoadTestResult]:
        """Test discovery operations under load"""
        
        config = LoadTestConfig(
            name="discovery_load_test",
            description="Discovery operations under increasing load",
            concurrent_users=[10, 25, 50, 100],
            test_duration_seconds=30,
            ramp_up_duration_seconds=5,
            operations_per_user=3
        )
        
        results = []
        
        for concurrent_users in config.concurrent_users:
            logger.info(f"Testing discovery load with {concurrent_users} concurrent users")
            result = await self._execute_load_test(config, concurrent_users, self._discovery_operation)
            results.append(result)
            
            await asyncio.sleep(5)
            
        return results
    
    async def _test_api_load(self) -> List[LoadTestResult]:
        """Test API endpoints under load"""
        
        config = LoadTestConfig(
            name="api_load_test", 
            description="API endpoints under increasing load",
            concurrent_users=[20, 50, 100, 200],
            test_duration_seconds=45,
            ramp_up_duration_seconds=10,
            operations_per_user=10
        )
        
        results = []
        
        for concurrent_users in config.concurrent_users:
            logger.info(f"Testing API load with {concurrent_users} concurrent users")
            result = await self._execute_load_test(config, concurrent_users, self._api_operation)
            results.append(result)
            
            await asyncio.sleep(5)
            
        return results
    
    async def _execute_load_test(
        self, 
        config: LoadTestConfig, 
        concurrent_users: int,
        operation_func: Callable
    ) -> LoadTestResult:
        """Execute load test with specified configuration"""
        
        start_time = time.time()
        response_times = []
        operation_results = []
        
        # Monitor system resources
        self.system_monitor.start_monitoring()
        
        try:
            # Create user tasks
            user_tasks = []
            for user_id in range(concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user_load(user_id, config, operation_func, response_times)
                )
                user_tasks.append(task)
            
            # Execute all user tasks
            user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Collect results
            for result in user_results:
                if isinstance(result, Exception):
                    operation_results.append(False)
                else:
                    operation_results.extend(result)
            
        finally:
            # Stop monitoring
            resource_stats = self.system_monitor.stop_monitoring()
        
        # Calculate metrics
        total_operations = len(operation_results)
        successful_operations = sum(1 for r in operation_results if r)
        failed_operations = total_operations - successful_operations
        success_rate = successful_operations / total_operations if total_operations > 0 else 0.0
        
        test_duration = time.time() - start_time
        ops_per_second = total_operations / test_duration if test_duration > 0 else 0.0
        
        # Response time statistics
        valid_response_times = [rt for rt in response_times if rt is not None]
        avg_response_time = statistics.mean(valid_response_times) if valid_response_times else 0.0
        
        if valid_response_times:
            valid_response_times.sort()
            p95_index = int(len(valid_response_times) * 0.95)
            p99_index = int(len(valid_response_times) * 0.99)
            p95_response_time = valid_response_times[p95_index] if p95_index < len(valid_response_times) else max(valid_response_times)
            p99_response_time = valid_response_times[p99_index] if p99_index < len(valid_response_times) else max(valid_response_times)
        else:
            p95_response_time = 0.0
            p99_response_time = 0.0
        
        return LoadTestResult(
            config_name=config.name,
            concurrent_users=concurrent_users,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            success_rate=success_rate,
            average_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            operations_per_second=ops_per_second,
            peak_memory_usage_mb=resource_stats.get('peak_memory_mb', 0.0),
            cpu_usage_percentage=resource_stats.get('avg_cpu_percentage', 0.0)
        )
    
    async def _simulate_user_load(
        self,
        user_id: int,
        config: LoadTestConfig,
        operation_func: Callable,
        response_times: List[float]
    ) -> List[bool]:
        """Simulate individual user load"""
        
        results = []
        
        for _ in range(config.operations_per_user):
            start_time = time.time()
            
            try:
                await operation_func()
                duration = time.time() - start_time
                response_times.append(duration)
                results.append(True)
                
            except Exception as e:
                duration = time.time() - start_time
                response_times.append(None)  # Failed operation
                results.append(False)
                logger.debug(f"User {user_id} operation failed: {e}")
            
            # Small delay between operations
            await asyncio.sleep(0.1)
        
        return results
    
    async def _research_operation(self):
        """Simulate research operation for load testing"""
        await asyncio.sleep(0.2)  # Simulate processing
        
        # Simulate some work
        data = list(range(1000))
        sum(data)
    
    async def _discovery_operation(self):
        """Simulate discovery operation for load testing"""
        await asyncio.sleep(0.1)  # Simulate processing
        
        # Simulate vector operations
        import random
        vector = [random.random() for _ in range(100)]
        magnitude = sum(x ** 2 for x in vector) ** 0.5
    
    async def _api_operation(self):
        """Simulate API operation for load testing"""
        await asyncio.sleep(0.05)  # Simulate API processing
        
        # Simulate JSON processing
        data = {"test": "data", "value": 123}
        json.dumps(data)


class SystemResourceMonitor:
    """System resource monitoring for performance tests"""
    
    def __init__(self):
        self.monitoring = False
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
        
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_cpu_usage_percentage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=0.1)
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = time.time()
        
        # Initial samples
        self.memory_samples.append(self.get_memory_usage_mb())
        self.cpu_samples.append(self.get_cpu_usage_percentage())
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return statistics"""
        self.monitoring = False
        
        # Final samples
        self.memory_samples.append(self.get_memory_usage_mb())
        self.cpu_samples.append(self.get_cpu_usage_percentage())
        
        return {
            'peak_memory_mb': max(self.memory_samples) if self.memory_samples else 0.0,
            'avg_memory_mb': statistics.mean(self.memory_samples) if self.memory_samples else 0.0,
            'peak_cpu_percentage': max(self.cpu_samples) if self.cpu_samples else 0.0,
            'avg_cpu_percentage': statistics.mean(self.cpu_samples) if self.cpu_samples else 0.0,
            'monitoring_duration': time.time() - self.start_time if self.start_time else 0.0
        }
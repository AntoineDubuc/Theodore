#!/usr/bin/env python3
"""
Theodore v2 Chaos Engineering Framework

Comprehensive chaos engineering framework for testing system resilience,
fault tolerance, and recovery capabilities under adverse conditions.
"""

import asyncio
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
import statistics

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


class ChaosExperimentType(Enum):
    """Types of chaos engineering experiments"""
    NETWORK_LATENCY = "network_latency"
    SERVICE_FAILURE = "service_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATA_CORRUPTION = "data_corruption"
    DEPENDENCY_FAILURE = "dependency_failure"
    TIMEOUT_INJECTION = "timeout_injection"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_STRESS = "cpu_stress"


@dataclass
class ChaosExperiment:
    """Chaos experiment definition"""
    name: str
    experiment_type: ChaosExperimentType
    duration_seconds: int
    intensity: float  # 0.0 to 1.0
    target_components: List[str]
    expected_recovery_time_seconds: float
    safety_checks_enabled: bool = True
    abort_on_critical_failure: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChaosExperimentResult:
    """Chaos experiment execution result"""
    experiment_name: str
    experiment_type: ChaosExperimentType
    duration_seconds: float
    actual_recovery_time_seconds: float
    expected_recovery_time_seconds: float
    recovery_success: bool
    system_stability_maintained: bool
    baseline_metrics: Dict[str, float]
    failure_impact_metrics: Dict[str, float]
    recovery_metrics: Dict[str, float]
    errors_during_experiment: List[str]
    warnings: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResilienceTestSummary:
    """Overall resilience testing summary"""
    total_experiments: int
    successful_recoveries: int
    failed_recoveries: int
    average_recovery_time: float
    system_stability_score: float
    critical_failures: int
    recommendations: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ChaosEngineeringFramework:
    """Comprehensive chaos engineering framework for resilience testing"""
    
    def __init__(self, safety_enabled: bool = True):
        self.safety_enabled = safety_enabled
        self.active_experiments: List[ChaosExperiment] = []
        self.experiment_results: List[ChaosExperimentResult] = []
        self.system_metrics_collector = SystemMetricsCollector()
        self.failure_injectors = self._initialize_failure_injectors()
        
    async def run_chaos_experiments(self) -> ResilienceTestSummary:
        """Execute comprehensive chaos engineering experiments"""
        
        logger.info("Starting chaos engineering experiment suite...")
        
        # Initialize default experiments
        experiments = self._create_default_experiments()
        
        results = []
        
        for experiment in experiments:
            if self.safety_enabled and not await self._safety_check_passed(experiment):
                logger.warning(f"Safety check failed for experiment {experiment.name}, skipping")
                continue
                
            logger.info(f"Executing chaos experiment: {experiment.name}")
            result = await self._execute_chaos_experiment(experiment)
            results.append(result)
            
            # Cool down period between experiments
            await asyncio.sleep(5)
        
        # Generate summary
        summary = self._generate_resilience_summary(results)
        
        logger.info(f"Chaos engineering suite completed. System stability score: {summary.system_stability_score:.2f}")
        
        return summary
    
    async def run_network_resilience_tests(self) -> List[ChaosExperimentResult]:
        """Test system resilience to network failures"""
        
        network_experiments = [
            ChaosExperiment(
                name="high_latency_injection",
                experiment_type=ChaosExperimentType.NETWORK_LATENCY,
                duration_seconds=60,
                intensity=0.5,
                target_components=["ai_services", "storage", "external_apis"],
                expected_recovery_time_seconds=10.0
            ),
            
            ChaosExperiment(
                name="intermittent_network_failure",
                experiment_type=ChaosExperimentType.SERVICE_FAILURE,
                duration_seconds=30,
                intensity=0.3,
                target_components=["external_apis"],
                expected_recovery_time_seconds=15.0
            ),
            
            ChaosExperiment(
                name="timeout_injection",
                experiment_type=ChaosExperimentType.TIMEOUT_INJECTION,
                duration_seconds=45,
                intensity=0.4,
                target_components=["ai_services"],
                expected_recovery_time_seconds=20.0
            )
        ]
        
        results = []
        for experiment in network_experiments:
            result = await self._execute_chaos_experiment(experiment)
            results.append(result)
            
        return results
    
    async def run_resource_exhaustion_tests(self) -> List[ChaosExperimentResult]:
        """Test system resilience to resource exhaustion"""
        
        resource_experiments = [
            ChaosExperiment(
                name="memory_pressure_injection",
                experiment_type=ChaosExperimentType.MEMORY_PRESSURE,
                duration_seconds=30,
                intensity=0.6,
                target_components=["application"],
                expected_recovery_time_seconds=5.0
            ),
            
            ChaosExperiment(
                name="cpu_stress_injection",
                experiment_type=ChaosExperimentType.CPU_STRESS,
                duration_seconds=45,
                intensity=0.7,
                target_components=["application"],
                expected_recovery_time_seconds=8.0
            )
        ]
        
        results = []
        for experiment in resource_experiments:
            result = await self._execute_chaos_experiment(experiment)
            results.append(result)
            
        return results
    
    async def run_dependency_failure_tests(self) -> List[ChaosExperimentResult]:
        """Test system resilience to dependency failures"""
        
        dependency_experiments = [
            ChaosExperiment(
                name="ai_service_failure",
                experiment_type=ChaosExperimentType.DEPENDENCY_FAILURE,
                duration_seconds=60,
                intensity=0.8,
                target_components=["ai_providers"],
                expected_recovery_time_seconds=25.0
            ),
            
            ChaosExperiment(
                name="database_failure_simulation",
                experiment_type=ChaosExperimentType.DEPENDENCY_FAILURE,
                duration_seconds=40,
                intensity=0.6,
                target_components=["vector_database"],
                expected_recovery_time_seconds=30.0
            )
        ]
        
        results = []
        for experiment in dependency_experiments:
            result = await self._execute_chaos_experiment(experiment)
            results.append(result)
            
        return results
    
    def _create_default_experiments(self) -> List[ChaosExperiment]:
        """Create default chaos experiments"""
        
        return [
            # Network resilience
            ChaosExperiment(
                name="network_latency_basic",
                experiment_type=ChaosExperimentType.NETWORK_LATENCY,
                duration_seconds=30,
                intensity=0.3,
                target_components=["external_apis"],
                expected_recovery_time_seconds=10.0
            ),
            
            # Service failure
            ChaosExperiment(
                name="ai_service_intermittent_failure",
                experiment_type=ChaosExperimentType.SERVICE_FAILURE,
                duration_seconds=45,
                intensity=0.4,
                target_components=["ai_services"],
                expected_recovery_time_seconds=15.0
            ),
            
            # Resource pressure
            ChaosExperiment(
                name="memory_pressure_light",
                experiment_type=ChaosExperimentType.MEMORY_PRESSURE,
                duration_seconds=20,
                intensity=0.4,
                target_components=["application"],
                expected_recovery_time_seconds=5.0
            ),
            
            # Timeout injection
            ChaosExperiment(
                name="request_timeout_injection",
                experiment_type=ChaosExperimentType.TIMEOUT_INJECTION,
                duration_seconds=30,
                intensity=0.5,
                target_components=["api_endpoints"],
                expected_recovery_time_seconds=12.0
            )
        ]
    
    async def _execute_chaos_experiment(self, experiment: ChaosExperiment) -> ChaosExperimentResult:
        """Execute individual chaos experiment"""
        
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Collect baseline metrics
            logger.debug(f"Collecting baseline metrics for {experiment.name}")
            baseline_metrics = await self.system_metrics_collector.collect_metrics()
            
            # Execute failure injection
            logger.debug(f"Injecting failure for {experiment.name}")
            async with self._inject_failure(experiment) as failure_context:
                
                # Monitor system during failure
                failure_metrics = await self._monitor_during_failure(
                    experiment, failure_context
                )
                
            # Monitor recovery
            logger.debug(f"Monitoring recovery for {experiment.name}")
            recovery_start = time.time()
            recovery_metrics = await self._monitor_recovery(
                experiment, baseline_metrics
            )
            
            actual_recovery_time = time.time() - recovery_start
            total_duration = time.time() - start_time
            
            # Analyze results
            recovery_success = actual_recovery_time <= experiment.expected_recovery_time_seconds
            stability_maintained = self._assess_system_stability(
                baseline_metrics, failure_metrics, recovery_metrics
            )
            
            return ChaosExperimentResult(
                experiment_name=experiment.name,
                experiment_type=experiment.experiment_type,
                duration_seconds=total_duration,
                actual_recovery_time_seconds=actual_recovery_time,
                expected_recovery_time_seconds=experiment.expected_recovery_time_seconds,
                recovery_success=recovery_success,
                system_stability_maintained=stability_maintained,
                baseline_metrics=baseline_metrics,
                failure_impact_metrics=failure_metrics,
                recovery_metrics=recovery_metrics,
                errors_during_experiment=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Chaos experiment failed: {str(e)}")
            logger.error(f"Chaos experiment {experiment.name} failed: {e}")
            
            return ChaosExperimentResult(
                experiment_name=experiment.name,
                experiment_type=experiment.experiment_type,
                duration_seconds=time.time() - start_time,
                actual_recovery_time_seconds=float('inf'),
                expected_recovery_time_seconds=experiment.expected_recovery_time_seconds,
                recovery_success=False,
                system_stability_maintained=False,
                baseline_metrics={},
                failure_impact_metrics={},
                recovery_metrics={},
                errors_during_experiment=errors,
                warnings=warnings
            )
    
    @asynccontextmanager
    async def _inject_failure(self, experiment: ChaosExperiment):
        """Inject failure based on experiment type"""
        
        injector = self.failure_injectors.get(experiment.experiment_type)
        if not injector:
            raise ValueError(f"No failure injector for {experiment.experiment_type}")
        
        failure_context = await injector.start_injection(experiment)
        
        try:
            yield failure_context
        finally:
            await injector.stop_injection(failure_context)
    
    async def _monitor_during_failure(
        self, 
        experiment: ChaosExperiment, 
        failure_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Monitor system metrics during failure injection"""
        
        metrics_samples = []
        
        # Monitor for the duration of the experiment
        monitor_duration = experiment.duration_seconds
        sample_interval = 2  # seconds
        samples_count = max(1, monitor_duration // sample_interval)
        
        for i in range(samples_count):
            await asyncio.sleep(sample_interval)
            metrics = await self.system_metrics_collector.collect_metrics()
            metrics_samples.append(metrics)
        
        # Calculate average metrics during failure
        if metrics_samples:
            failure_metrics = {}
            for key in metrics_samples[0]:
                values = [sample[key] for sample in metrics_samples if key in sample]
                failure_metrics[key] = statistics.mean(values) if values else 0.0
        else:
            failure_metrics = {}
        
        return failure_metrics
    
    async def _monitor_recovery(
        self, 
        experiment: ChaosExperiment, 
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Monitor system recovery after failure injection"""
        
        max_recovery_time = experiment.expected_recovery_time_seconds * 2
        sample_interval = 1  # second
        recovery_start = time.time()
        
        while time.time() - recovery_start < max_recovery_time:
            await asyncio.sleep(sample_interval)
            
            current_metrics = await self.system_metrics_collector.collect_metrics()
            
            # Check if system has recovered to baseline
            if self._has_system_recovered(baseline_metrics, current_metrics):
                break
        
        # Return final recovery metrics
        return await self.system_metrics_collector.collect_metrics()
    
    def _has_system_recovered(
        self, 
        baseline: Dict[str, float], 
        current: Dict[str, float]
    ) -> bool:
        """Check if system has recovered to baseline performance"""
        
        recovery_threshold = 0.9  # 90% of baseline performance
        
        for key, baseline_value in baseline.items():
            if key in current:
                current_value = current[key]
                if key in ['response_time', 'error_rate']:
                    # Lower is better for these metrics
                    if current_value > baseline_value * (2 - recovery_threshold):
                        return False
                else:
                    # Higher is better for these metrics (throughput, success_rate)
                    if current_value < baseline_value * recovery_threshold:
                        return False
        
        return True
    
    def _assess_system_stability(
        self,
        baseline: Dict[str, float],
        failure: Dict[str, float],
        recovery: Dict[str, float]
    ) -> bool:
        """Assess overall system stability during experiment"""
        
        # Check if system maintained minimum operational levels
        min_operational_threshold = 0.5  # 50% minimum operational level
        
        for key, baseline_value in baseline.items():
            if key in failure:
                failure_value = failure[key]
                if key in ['success_rate', 'throughput']:
                    # System should maintain minimum operational level
                    if failure_value < baseline_value * min_operational_threshold:
                        return False
                elif key == 'error_rate':
                    # Error rate shouldn't exceed 50%
                    if failure_value > 0.5:
                        return False
        
        return True
    
    def _generate_resilience_summary(
        self, 
        results: List[ChaosExperimentResult]
    ) -> ResilienceTestSummary:
        """Generate overall resilience testing summary"""
        
        total_experiments = len(results)
        successful_recoveries = sum(1 for r in results if r.recovery_success)
        failed_recoveries = total_experiments - successful_recoveries
        
        # Calculate average recovery time (excluding failed recoveries)
        valid_recovery_times = [
            r.actual_recovery_time_seconds for r in results 
            if r.recovery_success and r.actual_recovery_time_seconds != float('inf')
        ]
        avg_recovery_time = statistics.mean(valid_recovery_times) if valid_recovery_times else 0.0
        
        # Calculate system stability score
        stability_scores = [1.0 if r.system_stability_maintained else 0.0 for r in results]
        system_stability_score = statistics.mean(stability_scores) if stability_scores else 0.0
        
        # Count critical failures
        critical_failures = sum(1 for r in results if r.errors_during_experiment)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results)
        
        return ResilienceTestSummary(
            total_experiments=total_experiments,
            successful_recoveries=successful_recoveries,
            failed_recoveries=failed_recoveries,
            average_recovery_time=avg_recovery_time,
            system_stability_score=system_stability_score,
            critical_failures=critical_failures,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: List[ChaosExperimentResult]) -> List[str]:
        """Generate recommendations based on experiment results"""
        
        recommendations = []
        
        # Analyze recovery times
        slow_recoveries = [r for r in results if not r.recovery_success]
        if slow_recoveries:
            recommendations.append(
                f"Improve recovery time for {len(slow_recoveries)} experiment(s) "
                f"that exceeded expected recovery time"
            )
        
        # Analyze stability
        unstable_experiments = [r for r in results if not r.system_stability_maintained]
        if unstable_experiments:
            recommendations.append(
                f"Enhance system stability during {len(unstable_experiments)} "
                f"experiment(s) that showed instability"
            )
        
        # Analyze critical failures
        critical_failures = [r for r in results if r.errors_during_experiment]
        if critical_failures:
            recommendations.append(
                f"Address critical failures in {len(critical_failures)} experiment(s)"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("System resilience appears good, continue monitoring")
        
        return recommendations
    
    async def _safety_check_passed(self, experiment: ChaosExperiment) -> bool:
        """Perform safety checks before running experiment"""
        
        # Check system health
        system_health = await self.system_metrics_collector.check_system_health()
        if not system_health:
            return False
        
        # Check experiment intensity
        if experiment.intensity > 0.8 and not experiment.safety_checks_enabled:
            return False
        
        return True
    
    def _initialize_failure_injectors(self) -> Dict[ChaosExperimentType, 'FailureInjector']:
        """Initialize failure injectors for different experiment types"""
        
        return {
            ChaosExperimentType.NETWORK_LATENCY: NetworkLatencyInjector(),
            ChaosExperimentType.SERVICE_FAILURE: ServiceFailureInjector(),
            ChaosExperimentType.RESOURCE_EXHAUSTION: ResourceExhaustionInjector(),
            ChaosExperimentType.TIMEOUT_INJECTION: TimeoutInjector(),
            ChaosExperimentType.MEMORY_PRESSURE: MemoryPressureInjector(),
            ChaosExperimentType.CPU_STRESS: CPUStressInjector(),
            ChaosExperimentType.DEPENDENCY_FAILURE: DependencyFailureInjector()
        }


class FailureInjector:
    """Base class for failure injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Start failure injection and return context"""
        return {}
    
    async def stop_injection(self, context: Dict[str, Any]):
        """Stop failure injection"""
        pass


class NetworkLatencyInjector(FailureInjector):
    """Network latency injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting network latency with intensity {experiment.intensity}")
        # Simulate network latency injection
        delay = experiment.intensity * 2.0  # Up to 2 seconds delay
        return {'latency_delay': delay}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping network latency injection")
        # Restore normal network conditions


class ServiceFailureInjector(FailureInjector):
    """Service failure injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting service failures with intensity {experiment.intensity}")
        failure_rate = experiment.intensity
        return {'failure_rate': failure_rate}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping service failure injection")


class ResourceExhaustionInjector(FailureInjector):
    """Resource exhaustion injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting resource exhaustion with intensity {experiment.intensity}")
        return {'resource_consumption': experiment.intensity}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping resource exhaustion injection")


class TimeoutInjector(FailureInjector):
    """Timeout injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting timeouts with intensity {experiment.intensity}")
        timeout_multiplier = 1 + experiment.intensity * 5  # Up to 6x normal timeout
        return {'timeout_multiplier': timeout_multiplier}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping timeout injection")


class MemoryPressureInjector(FailureInjector):
    """Memory pressure injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting memory pressure with intensity {experiment.intensity}")
        # Simulate memory allocation
        memory_data = []
        allocation_size = int(experiment.intensity * 100000)  # Allocate some memory
        for _ in range(allocation_size):
            memory_data.append(random.random())
        return {'allocated_memory': memory_data}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping memory pressure injection")
        # Release allocated memory
        if 'allocated_memory' in context:
            del context['allocated_memory']


class CPUStressInjector(FailureInjector):
    """CPU stress injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting CPU stress with intensity {experiment.intensity}")
        # Start CPU stress task
        stress_task = asyncio.create_task(self._cpu_stress_task(experiment.intensity))
        return {'stress_task': stress_task}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping CPU stress injection")
        if 'stress_task' in context:
            context['stress_task'].cancel()
            try:
                await context['stress_task']
            except asyncio.CancelledError:
                pass
    
    async def _cpu_stress_task(self, intensity: float):
        """CPU stress task"""
        while True:
            # Perform CPU-intensive work
            work_duration = intensity * 0.1  # Up to 100ms of work
            start = time.time()
            while time.time() - start < work_duration:
                # CPU-intensive computation
                sum(i ** 2 for i in range(1000))
            
            # Brief pause
            await asyncio.sleep(0.01)


class DependencyFailureInjector(FailureInjector):
    """Dependency failure injection"""
    
    async def start_injection(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        logger.debug(f"Injecting dependency failures with intensity {experiment.intensity}")
        return {'dependency_failure_rate': experiment.intensity}
    
    async def stop_injection(self, context: Dict[str, Any]):
        logger.debug("Stopping dependency failure injection")


class SystemMetricsCollector:
    """System metrics collection for chaos experiments"""
    
    async def collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        
        # Simulate metric collection
        # In real implementation, would collect actual system metrics
        return {
            'response_time': random.uniform(0.1, 0.5),
            'throughput': random.uniform(50, 100),
            'error_rate': random.uniform(0.0, 0.05),
            'success_rate': random.uniform(0.95, 1.0),
            'memory_usage': random.uniform(30, 70),
            'cpu_usage': random.uniform(20, 80)
        }
    
    async def check_system_health(self) -> bool:
        """Check if system is healthy for chaos testing"""
        
        metrics = await self.collect_metrics()
        
        # Basic health checks
        if metrics['error_rate'] > 0.1:  # More than 10% errors
            return False
        if metrics['success_rate'] < 0.9:  # Less than 90% success
            return False
        if metrics['response_time'] > 2.0:  # Response time > 2 seconds
            return False
        
        return True
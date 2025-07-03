#!/usr/bin/env python3
"""
Theodore v2 Comprehensive Test Runner

Main test runner that orchestrates all enterprise testing frameworks including
end-to-end integration tests, performance benchmarks, chaos engineering,
security testing, and production validation.
"""

import asyncio
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import sys

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.framework import (
    E2ETestFramework,
    PerformanceTestSuite,
    LoadTestingSuite,
    ChaosEngineeringFramework,
    SecurityTestingSuite,
    TestDataManager
)
from src.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TestSuiteConfig:
    """Test suite configuration"""
    name: str
    enabled: bool
    timeout_seconds: float
    retry_count: int
    parallel_execution: bool
    config: Dict[str, Any]


@dataclass
class ComprehensiveTestResult:
    """Comprehensive test execution result"""
    suite_name: str
    success: bool
    duration_seconds: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    warnings: List[str]
    detailed_results: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestExecutionSummary:
    """Overall test execution summary"""
    total_duration_seconds: float
    total_suites: int
    successful_suites: int
    failed_suites: int
    overall_success_rate: float
    quality_score: float
    performance_score: float
    security_score: float
    reliability_score: float
    recommendations: List[str]
    suite_results: List[ComprehensiveTestResult]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComprehensiveTestRunner:
    """Main comprehensive test runner for Theodore v2"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.test_data_manager = TestDataManager()
        
        # Initialize test frameworks
        self.e2e_framework = E2ETestFramework(config=self.config.get('e2e', {}))
        self.performance_suite = PerformanceTestSuite()
        self.load_testing_suite = LoadTestingSuite()
        self.chaos_framework = ChaosEngineeringFramework(safety_enabled=True)
        self.security_suite = SecurityTestingSuite(config=self.config.get('security', {}))
        
        self.execution_results: List[ComprehensiveTestResult] = []
    
    async def run_comprehensive_tests(self, suites: List[str] = None) -> TestExecutionSummary:
        """Run comprehensive test suite with all frameworks"""
        
        logger.info("🚀 Starting Theodore v2 Comprehensive Test Suite")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Initialize test environment
        session_id = f"comprehensive_test_{int(time.time())}"
        await self.test_data_manager.initialize_test_session(session_id)
        
        try:
            # Define test suites to run
            test_suites = self._get_enabled_test_suites(suites)
            
            results = []
            
            # Execute test suites
            for suite_config in test_suites:
                logger.info(f"📋 Executing test suite: {suite_config.name}")
                
                result = await self._execute_test_suite(suite_config)
                results.append(result)
                
                # Log suite result
                status = "✅ PASSED" if result.success else "❌ FAILED"
                logger.info(f"{status} {suite_config.name}: {result.passed_tests}/{result.total_tests} tests passed in {result.duration_seconds:.1f}s")
                
                if not result.success:
                    logger.warning(f"❗ Suite {suite_config.name} failed with {len(result.warnings)} warnings")
                
                logger.info("-" * 60)
            
            # Generate comprehensive summary
            summary = self._generate_comprehensive_summary(results, time.time() - start_time)
            
            # Log final results
            self._log_final_results(summary)
            
            return summary
            
        finally:
            # Cleanup test data
            await self.test_data_manager.cleanup_session(session_id)
    
    async def run_quick_validation(self) -> TestExecutionSummary:
        """Run quick validation test suite for CI/CD"""
        
        logger.info("⚡ Running Quick Validation Test Suite")
        
        quick_suites = [
            "e2e_critical_flows",
            "performance_benchmarks", 
            "security_essential"
        ]
        
        return await self.run_comprehensive_tests(quick_suites)
    
    async def run_production_readiness_check(self) -> TestExecutionSummary:
        """Run production readiness validation"""
        
        logger.info("🏭 Running Production Readiness Check")
        
        production_suites = [
            "e2e_complete",
            "performance_full",
            "load_testing",
            "chaos_engineering",
            "security_comprehensive"
        ]
        
        return await self.run_comprehensive_tests(production_suites)
    
    async def _execute_test_suite(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Execute individual test suite"""
        
        start_time = time.time()
        
        try:
            # Route to appropriate test framework
            if suite_config.name.startswith("e2e"):
                result = await self._run_e2e_tests(suite_config)
            elif suite_config.name.startswith("performance"):
                result = await self._run_performance_tests(suite_config)
            elif suite_config.name.startswith("load"):
                result = await self._run_load_tests(suite_config)
            elif suite_config.name.startswith("chaos"):
                result = await self._run_chaos_tests(suite_config)
            elif suite_config.name.startswith("security"):
                result = await self._run_security_tests(suite_config)
            else:
                raise ValueError(f"Unknown test suite: {suite_config.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Test suite {suite_config.name} failed with error: {e}")
            
            return ComprehensiveTestResult(
                suite_name=suite_config.name,
                success=False,
                duration_seconds=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                warnings=[f"Suite execution failed: {str(e)}"],
                detailed_results={"error": str(e)}
            )
    
    async def _run_e2e_tests(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Run end-to-end tests"""
        
        start_time = time.time()
        
        if suite_config.name == "e2e_critical_flows":
            # Run critical workflow tests only
            results = await self.e2e_framework.run_complete_research_flow_tests()
        else:
            # Run complete E2E test suite
            summary = await self.e2e_framework.run_all_tests()
            
            return ComprehensiveTestResult(
                suite_name=suite_config.name,
                success=summary.overall_success_rate >= 0.9,
                duration_seconds=time.time() - start_time,
                total_tests=summary.total_scenarios,
                passed_tests=summary.successful_scenarios,
                failed_tests=summary.failed_scenarios,
                warnings=[],
                detailed_results=summary.to_dict()
            )
        
        # Process individual test results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        return ComprehensiveTestResult(
            suite_name=suite_config.name,
            success=failed_tests == 0,
            duration_seconds=time.time() - start_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=[],
            detailed_results={"test_results": [r.to_dict() for r in results]}
        )
    
    async def _run_performance_tests(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Run performance tests"""
        
        start_time = time.time()
        
        if suite_config.name == "performance_benchmarks":
            # Run basic performance benchmarks
            results = await self.performance_suite.run_performance_benchmarks()
        else:
            # Run full performance suite including regression analysis
            results = await self.performance_suite.run_performance_benchmarks()
            regression_results = await self.performance_suite.run_regression_analysis()
        
        # Analyze results
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.success)
        failed_tests = total_tests - passed_tests
        
        return ComprehensiveTestResult(
            suite_name=suite_config.name,
            success=failed_tests == 0,
            duration_seconds=time.time() - start_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=[],
            detailed_results={"benchmark_results": {k: v.to_dict() for k, v in results.items()}}
        )
    
    async def _run_load_tests(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Run load tests"""
        
        start_time = time.time()
        
        # Execute load testing suite
        load_results = await self.load_testing_suite.run_load_tests()
        
        # Analyze results across all load test types
        total_tests = sum(len(results) for results in load_results.values())
        passed_tests = sum(
            sum(1 for r in results if r.success_rate >= 0.95) 
            for results in load_results.values()
        )
        failed_tests = total_tests - passed_tests
        
        return ComprehensiveTestResult(
            suite_name=suite_config.name,
            success=failed_tests == 0,
            duration_seconds=time.time() - start_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=[],
            detailed_results={"load_test_results": {k: [r.to_dict() for r in v] for k, v in load_results.items()}}
        )
    
    async def _run_chaos_tests(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Run chaos engineering tests"""
        
        start_time = time.time()
        
        # Execute chaos engineering suite
        chaos_summary = await self.chaos_framework.run_chaos_experiments()
        
        return ComprehensiveTestResult(
            suite_name=suite_config.name,
            success=chaos_summary.system_stability_score >= 0.8,
            duration_seconds=time.time() - start_time,
            total_tests=chaos_summary.total_experiments,
            passed_tests=chaos_summary.successful_recoveries,
            failed_tests=chaos_summary.failed_recoveries,
            warnings=[],
            detailed_results=chaos_summary.to_dict()
        )
    
    async def _run_security_tests(self, suite_config: TestSuiteConfig) -> ComprehensiveTestResult:
        """Run security tests"""
        
        start_time = time.time()
        
        if suite_config.name == "security_essential":
            # Run essential security tests
            vuln_results = await self.security_suite.run_vulnerability_scanning()
            auth_results = await self.security_suite.run_compliance_validation()
            all_results = vuln_results + auth_results
        else:
            # Run comprehensive security assessment
            security_summary = await self.security_suite.run_comprehensive_security_assessment()
            
            return ComprehensiveTestResult(
                suite_name=suite_config.name,
                success=security_summary.overall_risk_score <= 3.0,
                duration_seconds=time.time() - start_time,
                total_tests=security_summary.total_tests,
                passed_tests=security_summary.passed_tests,
                failed_tests=security_summary.failed_tests,
                warnings=[],
                detailed_results=security_summary.to_dict()
            )
        
        # Process individual security test results
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.success)
        failed_tests = total_tests - passed_tests
        
        return ComprehensiveTestResult(
            suite_name=suite_config.name,
            success=failed_tests == 0,
            duration_seconds=time.time() - start_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=[],
            detailed_results={"security_results": [r.to_dict() for r in all_results]}
        )
    
    def _get_enabled_test_suites(self, requested_suites: List[str] = None) -> List[TestSuiteConfig]:
        """Get enabled test suites based on configuration and request"""
        
        all_suites = {
            "e2e_critical_flows": TestSuiteConfig(
                name="e2e_critical_flows",
                enabled=True,
                timeout_seconds=300,
                retry_count=1,
                parallel_execution=False,
                config={}
            ),
            "e2e_complete": TestSuiteConfig(
                name="e2e_complete",
                enabled=True,
                timeout_seconds=600,
                retry_count=1,
                parallel_execution=False,
                config={}
            ),
            "performance_benchmarks": TestSuiteConfig(
                name="performance_benchmarks",
                enabled=True,
                timeout_seconds=300,
                retry_count=1,
                parallel_execution=True,
                config={}
            ),
            "performance_full": TestSuiteConfig(
                name="performance_full",
                enabled=True,
                timeout_seconds=600,
                retry_count=1,
                parallel_execution=True,
                config={}
            ),
            "load_testing": TestSuiteConfig(
                name="load_testing",
                enabled=True,
                timeout_seconds=900,
                retry_count=1,
                parallel_execution=False,
                config={}
            ),
            "chaos_engineering": TestSuiteConfig(
                name="chaos_engineering",
                enabled=True,
                timeout_seconds=600,
                retry_count=1,
                parallel_execution=False,
                config={}
            ),
            "security_essential": TestSuiteConfig(
                name="security_essential",
                enabled=True,
                timeout_seconds=300,
                retry_count=1,
                parallel_execution=True,
                config={}
            ),
            "security_comprehensive": TestSuiteConfig(
                name="security_comprehensive",
                enabled=True,
                timeout_seconds=900,
                retry_count=1,
                parallel_execution=True,
                config={}
            )
        }
        
        if requested_suites:
            return [all_suites[suite] for suite in requested_suites if suite in all_suites]
        else:
            return [suite for suite in all_suites.values() if suite.enabled]
    
    def _generate_comprehensive_summary(self, results: List[ComprehensiveTestResult], total_duration: float) -> TestExecutionSummary:
        """Generate comprehensive test execution summary"""
        
        total_suites = len(results)
        successful_suites = sum(1 for r in results if r.success)
        failed_suites = total_suites - successful_suites
        
        overall_success_rate = successful_suites / total_suites if total_suites > 0 else 0.0
        
        # Calculate quality scores
        quality_score = self._calculate_quality_score(results)
        performance_score = self._calculate_performance_score(results)
        security_score = self._calculate_security_score(results)
        reliability_score = self._calculate_reliability_score(results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results)
        
        return TestExecutionSummary(
            total_duration_seconds=total_duration,
            total_suites=total_suites,
            successful_suites=successful_suites,
            failed_suites=failed_suites,
            overall_success_rate=overall_success_rate,
            quality_score=quality_score,
            performance_score=performance_score,
            security_score=security_score,
            reliability_score=reliability_score,
            recommendations=recommendations,
            suite_results=results
        )
    
    def _calculate_quality_score(self, results: List[ComprehensiveTestResult]) -> float:
        """Calculate overall quality score"""
        
        if not results:
            return 0.0
        
        # Weight different test types
        weights = {
            "e2e": 0.4,
            "performance": 0.2,
            "security": 0.2,
            "chaos": 0.1,
            "load": 0.1
        }
        
        weighted_scores = []
        for result in results:
            suite_type = result.suite_name.split("_")[0]
            weight = weights.get(suite_type, 0.1)
            
            success_rate = result.passed_tests / result.total_tests if result.total_tests > 0 else 0.0
            weighted_scores.append(success_rate * weight)
        
        return sum(weighted_scores) / sum(weights.values()) if weighted_scores else 0.0
    
    def _calculate_performance_score(self, results: List[ComprehensiveTestResult]) -> float:
        """Calculate performance score from performance test results"""
        
        performance_results = [r for r in results if "performance" in r.suite_name or "load" in r.suite_name]
        
        if not performance_results:
            return 1.0  # No performance issues if no tests run
        
        scores = []
        for result in performance_results:
            success_rate = result.passed_tests / result.total_tests if result.total_tests > 0 else 0.0
            scores.append(success_rate)
        
        return sum(scores) / len(scores) if scores else 1.0
    
    def _calculate_security_score(self, results: List[ComprehensiveTestResult]) -> float:
        """Calculate security score from security test results"""
        
        security_results = [r for r in results if "security" in r.suite_name]
        
        if not security_results:
            return 0.5  # Unknown security posture
        
        scores = []
        for result in security_results:
            success_rate = result.passed_tests / result.total_tests if result.total_tests > 0 else 0.0
            scores.append(success_rate)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_reliability_score(self, results: List[ComprehensiveTestResult]) -> float:
        """Calculate reliability score from chaos engineering results"""
        
        chaos_results = [r for r in results if "chaos" in r.suite_name]
        
        if not chaos_results:
            return 0.8  # Default reliability assumption
        
        scores = []
        for result in chaos_results:
            # For chaos tests, look at detailed results for stability score
            detailed = result.detailed_results
            if isinstance(detailed, dict) and "system_stability_score" in detailed:
                scores.append(detailed["system_stability_score"])
            else:
                success_rate = result.passed_tests / result.total_tests if result.total_tests > 0 else 0.0
                scores.append(success_rate)
        
        return sum(scores) / len(scores) if scores else 0.8
    
    def _generate_recommendations(self, results: List[ComprehensiveTestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        # Check for failed suites
        failed_suites = [r for r in results if not r.success]
        if failed_suites:
            recommendations.append(f"Address failures in {len(failed_suites)} test suite(s): {', '.join(r.suite_name for r in failed_suites)}")
        
        # Check performance
        performance_results = [r for r in results if "performance" in r.suite_name]
        if performance_results and any(not r.success for r in performance_results):
            recommendations.append("Investigate performance issues and optimize bottlenecks")
        
        # Check security
        security_results = [r for r in results if "security" in r.suite_name]
        if security_results and any(not r.success for r in security_results):
            recommendations.append("Address security findings before production deployment")
        
        # Check reliability
        chaos_results = [r for r in results if "chaos" in r.suite_name]
        if chaos_results and any(not r.success for r in chaos_results):
            recommendations.append("Improve system resilience and fault tolerance")
        
        # General recommendations
        if not failed_suites:
            recommendations.append("All test suites passed - system is ready for production")
            recommendations.append("Continue regular testing and monitoring")
        
        return recommendations
    
    def _log_final_results(self, summary: TestExecutionSummary):
        """Log final test execution results"""
        
        logger.info("=" * 80)
        logger.info("🏁 Theodore v2 Comprehensive Test Results")
        logger.info("=" * 80)
        
        # Overall summary
        status_emoji = "✅" if summary.overall_success_rate >= 0.9 else "⚠️" if summary.overall_success_rate >= 0.7 else "❌"
        logger.info(f"{status_emoji} Overall Success Rate: {summary.overall_success_rate:.1%}")
        logger.info(f"⏱️  Total Duration: {summary.total_duration_seconds:.1f} seconds")
        logger.info(f"📊 Test Suites: {summary.successful_suites}/{summary.total_suites} passed")
        
        # Quality scores
        logger.info("📈 Quality Metrics:")
        logger.info(f"   🎯 Quality Score: {summary.quality_score:.1%}")
        logger.info(f"   ⚡ Performance Score: {summary.performance_score:.1%}")
        logger.info(f"   🔒 Security Score: {summary.security_score:.1%}")
        logger.info(f"   🛡️  Reliability Score: {summary.reliability_score:.1%}")
        
        # Suite breakdown
        logger.info("📋 Suite Results:")
        for result in summary.suite_results:
            status_emoji = "✅" if result.success else "❌"
            logger.info(f"   {status_emoji} {result.suite_name}: {result.passed_tests}/{result.total_tests} ({result.duration_seconds:.1f}s)")
        
        # Recommendations
        if summary.recommendations:
            logger.info("💡 Recommendations:")
            for i, rec in enumerate(summary.recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info("=" * 80)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        
        return {
            "e2e": {
                "timeout_seconds": 300,
                "parallel_execution": False
            },
            "performance": {
                "benchmark_iterations": 10,
                "regression_threshold": 0.15
            },
            "security": {
                "vulnerability_scanning": True,
                "compliance_checking": True,
                "penetration_testing": False  # Disabled by default for safety
            },
            "chaos": {
                "safety_enabled": True,
                "experiment_duration": 60
            },
            "load": {
                "max_concurrent_users": 100,
                "test_duration_seconds": 300
            }
        }


async def main():
    """Main entry point for comprehensive test runner"""
    
    parser = argparse.ArgumentParser(description="Theodore v2 Comprehensive Test Runner")
    parser.add_argument("--suites", nargs="+", help="Specific test suites to run")
    parser.add_argument("--quick", action="store_true", help="Run quick validation suite")
    parser.add_argument("--production", action="store_true", help="Run production readiness check")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize test runner
    runner = ComprehensiveTestRunner()
    
    try:
        # Execute tests based on arguments
        if args.quick:
            summary = await runner.run_quick_validation()
        elif args.production:
            summary = await runner.run_production_readiness_check()
        else:
            summary = await runner.run_comprehensive_tests(args.suites)
        
        # Save results if output file specified
        if args.output:
            output_path = Path(args.output)
            with output_path.open('w') as f:
                json.dump(summary.to_dict(), f, indent=2, default=str)
            logger.info(f"Test results saved to: {output_path}")
        
        # Exit with appropriate code
        exit_code = 0 if summary.overall_success_rate >= 0.9 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Theodore v2 Testing CLI Commands

Command-line interface for running various testing frameworks and scenarios.
"""

import asyncio
import click
import json
from pathlib import Path
from typing import List, Optional

from ..integration.comprehensive_test_runner import ComprehensiveTestRunner
from ..framework import (
    E2ETestFramework,
    PerformanceTestSuite,
    ChaosEngineeringFramework,
    SecurityTestingSuite,
    TestDataManager
)


@click.group()
def test():
    """Theodore v2 Testing Commands"""
    pass


@test.command()
@click.option("--suites", multiple=True, help="Specific test suites to run")
@click.option("--output", type=click.Path(), help="Output file for results (JSON)")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def comprehensive(suites: List[str], output: Optional[str], verbose: bool):
    """Run comprehensive test suite"""
    
    async def run_tests():
        runner = ComprehensiveTestRunner()
        
        # Convert tuple to list
        suite_list = list(suites) if suites else None
        
        summary = await runner.run_comprehensive_tests(suite_list)
        
        if output:
            output_path = Path(output)
            with output_path.open('w') as f:
                json.dump(summary.to_dict(), f, indent=2, default=str)
            click.echo(f"Results saved to: {output_path}")
        
        # Display summary
        status = "PASSED" if summary.overall_success_rate >= 0.9 else "FAILED"
        click.echo(f"\n{status}: {summary.successful_suites}/{summary.total_suites} suites passed")
        click.echo(f"Quality Score: {summary.quality_score:.1%}")
        
        return summary.overall_success_rate >= 0.9
    
    success = asyncio.run(run_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--output", type=click.Path(), help="Output file for results")
def quick(output: Optional[str]):
    """Run quick validation test suite"""
    
    async def run_quick_tests():
        runner = ComprehensiveTestRunner()
        summary = await runner.run_quick_validation()
        
        if output:
            output_path = Path(output)
            with output_path.open('w') as f:
                json.dump(summary.to_dict(), f, indent=2, default=str)
        
        status = "PASSED" if summary.overall_success_rate >= 0.9 else "FAILED"
        click.echo(f"{status}: Quick validation completed in {summary.total_duration_seconds:.1f}s")
        
        return summary.overall_success_rate >= 0.9
    
    success = asyncio.run(run_quick_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--output", type=click.Path(), help="Output file for results")
def production(output: Optional[str]):
    """Run production readiness check"""
    
    async def run_production_tests():
        runner = ComprehensiveTestRunner()
        summary = await runner.run_production_readiness_check()
        
        if output:
            output_path = Path(output)
            with output_path.open('w') as f:
                json.dump(summary.to_dict(), f, indent=2, default=str)
        
        status = "READY" if summary.overall_success_rate >= 0.95 else "NOT READY"
        click.echo(f"Production Readiness: {status}")
        click.echo(f"Overall Score: {summary.quality_score:.1%}")
        
        if summary.recommendations:
            click.echo("\nRecommendations:")
            for rec in summary.recommendations:
                click.echo(f"  • {rec}")
        
        return summary.overall_success_rate >= 0.95
    
    success = asyncio.run(run_production_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--timeout", type=int, default=300, help="Test timeout in seconds")
def e2e(timeout: int):
    """Run end-to-end integration tests"""
    
    async def run_e2e_tests():
        framework = E2ETestFramework()
        await framework.initialize_test_environment()
        
        summary = await framework.run_all_tests()
        
        click.echo(f"E2E Tests: {summary.successful_scenarios}/{summary.total_scenarios} passed")
        click.echo(f"Success Rate: {summary.overall_success_rate:.1%}")
        click.echo(f"Data Quality: {summary.average_data_quality:.1%}")
        
        return summary.overall_success_rate >= 0.9
    
    success = asyncio.run(run_e2e_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--iterations", type=int, default=10, help="Number of benchmark iterations")
def performance(iterations: int):
    """Run performance benchmarks"""
    
    async def run_performance_tests():
        suite = PerformanceTestSuite()
        
        # Override default iterations
        for benchmark in suite.benchmarks:
            benchmark.test_iterations = iterations
        
        results = await suite.run_performance_benchmarks()
        
        passed = sum(1 for r in results.values() if r.success)
        total = len(results)
        
        click.echo(f"Performance Tests: {passed}/{total} benchmarks passed")
        
        for name, result in results.items():
            status = "✅" if result.success else "❌"
            click.echo(f"  {status} {name}: {result.average_duration:.3f}s (rating: {result.performance_rating})")
        
        return passed == total
    
    success = asyncio.run(run_performance_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--safety/--no-safety", default=True, help="Enable safety checks")
def chaos(safety: bool):
    """Run chaos engineering tests"""
    
    async def run_chaos_tests():
        framework = ChaosEngineeringFramework(safety_enabled=safety)
        
        summary = await framework.run_chaos_experiments()
        
        click.echo(f"Chaos Tests: {summary.successful_recoveries}/{summary.total_experiments} experiments passed")
        click.echo(f"System Stability: {summary.system_stability_score:.1%}")
        click.echo(f"Avg Recovery Time: {summary.average_recovery_time:.1f}s")
        
        if summary.recommendations:
            click.echo("\nRecommendations:")
            for rec in summary.recommendations:
                click.echo(f"  • {rec}")
        
        return summary.system_stability_score >= 0.8
    
    success = asyncio.run(run_chaos_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--include-pentest", is_flag=True, help="Include penetration testing")
def security(include_pentest: bool):
    """Run security tests"""
    
    async def run_security_tests():
        config = {}
        if include_pentest:
            config["penetration_testing"] = True
        
        suite = SecurityTestingSuite(config=config)
        
        summary = await suite.run_comprehensive_security_assessment()
        
        click.echo(f"Security Tests: {summary.passed_tests}/{summary.total_tests} tests passed")
        click.echo(f"Risk Score: {summary.overall_risk_score:.1f}/10")
        click.echo(f"Security Posture: {summary.security_posture}")
        
        if summary.critical_findings > 0:
            click.echo(f"⚠️  Critical Findings: {summary.critical_findings}")
        
        if summary.recommendations:
            click.echo("\nRecommendations:")
            for rec in summary.recommendations:
                click.echo(f"  • {rec}")
        
        return summary.overall_risk_score <= 3.0 and summary.critical_findings == 0
    
    success = asyncio.run(run_security_tests())
    exit(0 if success else 1)


@test.command()
@click.option("--session-id", help="Specific session ID to cleanup")
def cleanup(session_id: Optional[str]):
    """Cleanup test data and resources"""
    
    async def run_cleanup():
        manager = TestDataManager()
        
        if session_id:
            await manager.cleanup_session(session_id)
            click.echo(f"Cleaned up session: {session_id}")
        else:
            await manager.cleanup_all()
            click.echo("Cleaned up all test data and resources")
    
    asyncio.run(run_cleanup())


@test.command()
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_suites(format: str):
    """List available test suites"""
    
    suites = [
        {"name": "e2e_critical_flows", "description": "Critical workflow tests", "duration": "~5min"},
        {"name": "e2e_complete", "description": "Complete E2E test suite", "duration": "~10min"},
        {"name": "performance_benchmarks", "description": "Performance benchmarks", "duration": "~5min"},
        {"name": "performance_full", "description": "Full performance suite", "duration": "~10min"},
        {"name": "load_testing", "description": "Load and stress testing", "duration": "~15min"},
        {"name": "chaos_engineering", "description": "Chaos engineering tests", "duration": "~10min"},
        {"name": "security_essential", "description": "Essential security tests", "duration": "~5min"},
        {"name": "security_comprehensive", "description": "Full security assessment", "duration": "~15min"}
    ]
    
    if format == "json":
        click.echo(json.dumps(suites, indent=2))
    else:
        click.echo("Available Test Suites:")
        click.echo("-" * 60)
        for suite in suites:
            click.echo(f"{suite['name']:<25} {suite['description']:<30} {suite['duration']}")


if __name__ == "__main__":
    test()
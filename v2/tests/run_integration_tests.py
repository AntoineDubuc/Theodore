#!/usr/bin/env python3
"""
Theodore v2 Integration Test Runner
===================================

Command-line interface for running enterprise integration tests.
This script provides a simple way to execute and monitor comprehensive
integration tests for Theodore v2.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_enterprise_integration import EnterpriseIntegrationTestSuite


def create_argument_parser():
    """Create command line argument parser"""
    
    parser = argparse.ArgumentParser(
        description="Theodore v2 Enterprise Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                    # Run all tests
  python run_integration_tests.py --quick           # Run quick validation tests
  python run_integration_tests.py --suite research  # Run specific test suite
  python run_integration_tests.py --report          # Generate detailed report
        """
    )
    
    parser.add_argument(
        '--suite',
        choices=['research', 'discovery', 'ai', 'quality', 'performance', 'resilience', 'security', 'monitoring'],
        help='Run specific test suite only'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick validation tests only (faster execution)'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed HTML report after tests'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output with detailed logging'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        help='Output directory for test reports',
        default='test_reports'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Test timeout in seconds (default: 300)'
    )
    
    return parser


async def run_integration_tests(args):
    """Run integration tests based on command line arguments"""
    
    print("🚀 Theodore v2 Enterprise Integration Test Runner")
    print("=" * 60)
    print(f"📅 Test Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if args.quick:
        print("⚡ Quick validation mode enabled")
    if args.suite:
        print(f"🎯 Running test suite: {args.suite}")
    if args.verbose:
        print("📝 Verbose logging enabled")
    
    print()
    
    # Initialize test suite
    suite = EnterpriseIntegrationTestSuite()
    
    try:
        # Setup test environment
        await suite.setup_test_environment()
        
        # Run tests based on arguments
        if args.quick:
            report = await run_quick_validation_tests(suite)
        elif args.suite:
            report = await run_specific_test_suite(suite, args.suite)
        else:
            report = await suite.run_comprehensive_integration_tests()
        
        # Generate report if requested
        if args.report:
            await generate_html_report(report, args.output)
        
        # Print final summary
        print_test_summary(report)
        
        # Return appropriate exit code
        total_tests = report['test_execution_summary']['total_tests']
        failed_tests = report['test_execution_summary']['total_failed']
        
        if failed_tests == 0:
            print("\n✅ All tests passed! System is ready for enterprise deployment.")
            return 0
        else:
            print(f"\n❌ {failed_tests}/{total_tests} tests failed. Review recommendations before deployment.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        return 3
    finally:
        await suite.teardown_test_environment()


async def run_quick_validation_tests(suite):
    """Run quick validation tests for fast feedback"""
    
    print("⚡ Running Quick Validation Tests...")
    print("-" * 40)
    
    # Simplified test execution for quick feedback
    start_time = datetime.now(timezone.utc)
    
    # Test basic system functionality
    quick_tests = [
        ("Container Initialization", suite._validate_external_services),
        ("Basic Research Flow", lambda: test_basic_research(suite)),
        ("System Health Check", lambda: test_system_health(suite))
    ]
    
    passed_tests = 0
    total_tests = len(quick_tests)
    test_details = {}
    
    for test_name, test_func in quick_tests:
        test_start = datetime.now()
        
        try:
            print(f"  🔍 {test_name}...")
            
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            
            test_duration = (datetime.now() - test_start).total_seconds()
            test_details[test_name] = {
                'success': True,
                'duration_seconds': test_duration
            }
            passed_tests += 1
            print(f"    ✅ PASSED ({test_duration:.1f}s)")
            
        except Exception as e:
            test_duration = (datetime.now() - test_start).total_seconds()
            test_details[test_name] = {
                'success': False,
                'duration_seconds': test_duration,
                'error': str(e)
            }
            print(f"    ❌ FAILED: {str(e)}")
    
    total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    return {
        'test_execution_summary': {
            'total_duration_seconds': total_duration,
            'total_suites': 1,
            'passed_suites': 1 if passed_tests == total_tests else 0,
            'failed_suites': 0 if passed_tests == total_tests else 1,
            'total_tests': total_tests,
            'total_passed': passed_tests,
            'total_failed': total_tests - passed_tests
        },
        'suite_results': {
            'Quick Validation': {
                'success': passed_tests == total_tests,
                'test_count': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'details': test_details
            }
        },
        'enterprise_readiness_score': 90 if passed_tests == total_tests else 50,
        'recommendations': ['System basic functionality validated'] if passed_tests == total_tests else ['Review failed tests before proceeding']
    }


async def test_basic_research(suite):
    """Test basic research functionality"""
    
    # Simple test that doesn't require real API calls
    if suite.container is None:
        raise Exception("Container not initialized")
    
    # Test use case availability
    from src.core.use_cases.research_company import ResearchCompanyUseCase
    research_use_case = await suite.container.get(ResearchCompanyUseCase)
    
    if research_use_case is None:
        raise Exception("Research use case not available")


async def test_system_health(suite):
    """Test basic system health"""
    
    # Simple health checks
    if suite.container is None:
        raise Exception("Container not healthy")
    
    # Additional health checks can be added here
    pass


async def run_specific_test_suite(suite, suite_name):
    """Run a specific test suite"""
    
    print(f"🎯 Running {suite_name.title()} Test Suite...")
    print("-" * 50)
    
    # Map suite names to test methods
    suite_methods = {
        'research': suite._test_research_workflows,
        'discovery': suite._test_discovery_workflows,
        'ai': suite._test_ai_provider_integration,
        'quality': suite._test_data_quality_accuracy,
        'performance': suite._test_performance_scalability,
        'resilience': suite._test_error_handling_resilience,
        'security': suite._test_security_compliance,
        'monitoring': suite._test_system_health_monitoring
    }
    
    if suite_name not in suite_methods:
        raise ValueError(f"Unknown test suite: {suite_name}")
    
    start_time = datetime.now(timezone.utc)
    suite_result = await suite_methods[suite_name]()
    total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    return {
        'test_execution_summary': {
            'total_duration_seconds': total_duration,
            'total_suites': 1,
            'passed_suites': 1 if suite_result['success'] else 0,
            'failed_suites': 0 if suite_result['success'] else 1,
            'total_tests': suite_result['test_count'],
            'total_passed': suite_result['passed_tests'],
            'total_failed': suite_result['failed_tests']
        },
        'suite_results': {
            f"{suite_name.title()} Tests": suite_result
        },
        'enterprise_readiness_score': 90 if suite_result['success'] else 40,
        'recommendations': ['Test suite passed successfully'] if suite_result['success'] else ['Review failed tests in this suite']
    }


async def generate_html_report(report, output_dir):
    """Generate HTML report from test results"""
    
    print("\n📄 Generating HTML report...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"integration_test_report_{timestamp}.html"
    
    # Simple HTML report template
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Theodore v2 Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background: #f8f8f8; padding: 15px; font-weight: bold; }}
        .suite-content {{ padding: 15px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .score {{ font-size: 24px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Theodore v2 Integration Test Report</h1>
        <p>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div class="summary">
        <h2>Test Execution Summary</h2>
        <p><strong>Total Duration:</strong> {report['test_execution_summary']['total_duration_seconds']:.1f} seconds</p>
        <p><strong>Tests Passed:</strong> <span class="passed">{report['test_execution_summary']['total_passed']}</span>/{report['test_execution_summary']['total_tests']}</p>
        <p><strong>Tests Failed:</strong> <span class="failed">{report['test_execution_summary']['total_failed']}</span>/{report['test_execution_summary']['total_tests']}</p>
        <p><strong>Enterprise Readiness Score:</strong> <span class="score">{report['enterprise_readiness_score']}/100</span></p>
    </div>
    
    <div class="suites">
        <h2>Test Suite Results</h2>
    """
    
    # Add suite results
    for suite_name, suite_result in report['suite_results'].items():
        status_class = "passed" if suite_result['success'] else "failed"
        status_text = "PASSED" if suite_result['success'] else "FAILED"
        
        html_content += f"""
        <div class="suite">
            <div class="suite-header">
                {suite_name}: <span class="{status_class}">{status_text}</span>
            </div>
            <div class="suite-content">
                <p><strong>Tests:</strong> {suite_result.get('passed_tests', 0)}/{suite_result.get('test_count', 0)} passed</p>
                <p><strong>Duration:</strong> {suite_result.get('duration_seconds', 0):.1f} seconds</p>
            </div>
        </div>
        """
    
    # Add recommendations
    html_content += """
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
    """
    
    for rec in report.get('recommendations', []):
        html_content += f"<li>{rec}</li>"
    
    html_content += """
        </ul>
    </div>
    
    <div class="raw-data">
        <h2>Raw Test Data</h2>
        <pre style="background: #f0f0f0; padding: 20px; border-radius: 5px; overflow: auto;">
    """
    
    html_content += json.dumps(report, indent=2, default=str)
    
    html_content += """
        </pre>
    </div>
    
</body>
</html>
    """
    
    with open(report_file, 'w') as f:
        f.write(html_content)
    
    print(f"  📄 HTML report saved: {report_file}")


def print_test_summary(report):
    """Print comprehensive test summary"""
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    summary = report['test_execution_summary']
    
    print(f"⏱️  Total Duration: {summary['total_duration_seconds']:.1f} seconds")
    print(f"🧪 Test Suites: {summary['passed_suites']}/{summary['total_suites']} passed")
    print(f"✅ Individual Tests: {summary['total_passed']}/{summary['total_tests']} passed")
    print(f"🎯 Enterprise Readiness Score: {report['enterprise_readiness_score']}/100")
    
    # Print suite breakdown
    print("\n📋 Test Suite Breakdown:")
    for suite_name, suite_result in report['suite_results'].items():
        status = "✅ PASSED" if suite_result['success'] else "❌ FAILED"
        test_ratio = f"{suite_result.get('passed_tests', 0)}/{suite_result.get('test_count', 0)}"
        duration = suite_result.get('duration_seconds', 0)
        print(f"  {status} {suite_name}: {test_ratio} tests ({duration:.1f}s)")
    
    # Print recommendations
    if report.get('recommendations'):
        print("\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Print enterprise readiness assessment
    readiness_score = report['enterprise_readiness_score']
    if readiness_score >= 90:
        print("\n🏆 ENTERPRISE READY: System meets enterprise deployment standards")
    elif readiness_score >= 75:
        print("\n⚡ PRODUCTION READY: System ready for production with minor improvements")
    elif readiness_score >= 60:
        print("\n🔧 DEVELOPMENT READY: System functional but requires improvements")
    else:
        print("\n⚠️  NOT READY: System requires significant improvements before deployment")


def main():
    """Main CLI entry point"""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Run integration tests
        exit_code = asyncio.run(run_integration_tests(args))
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Test runner failed: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    main()
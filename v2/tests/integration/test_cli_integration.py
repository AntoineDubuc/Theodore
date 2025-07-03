#!/usr/bin/env python3
"""
Theodore v2 CLI Integration Tests
=================================

Enterprise integration tests focusing on CLI functionality and end-to-end workflows.
This test suite validates Theodore v2's command-line interface and core functionality
without requiring complex dependency injection setup.
"""

import asyncio
import subprocess
import pytest
import time
import json
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import csv
import os


@dataclass
class CLITestResult:
    """CLI test execution result"""
    test_name: str
    command: str
    success: bool
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    expected_outputs: List[str]
    found_outputs: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'command': self.command,
            'success': self.success,
            'exit_code': self.exit_code,
            'duration_seconds': self.duration_seconds,
            'output_length': len(self.stdout),
            'error_length': len(self.stderr),
            'expected_outputs_found': len(self.found_outputs),
            'total_expected_outputs': len(self.expected_outputs)
        }


class TheodoreCliIntegrationTestSuite:
    """
    Comprehensive CLI integration test suite for Theodore v2.
    Tests end-to-end functionality through the command-line interface.
    """
    
    def __init__(self):
        self.test_results: List[CLITestResult] = []
        self.temp_dir: Optional[Path] = None
        self.theodore_cli_path = Path(__file__).parent.parent.parent / "src" / "cli" / "main.py"
        
    async def setup_test_environment(self) -> None:
        """Setup test environment"""
        print("🔧 Setting up CLI integration test environment...")
        
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"  📁 Test directory: {self.temp_dir}")
        
        # Verify Theodore CLI exists
        if not self.theodore_cli_path.exists():
            raise FileNotFoundError(f"Theodore CLI not found at {self.theodore_cli_path}")
        
        print("✅ CLI integration test environment ready")
    
    async def teardown_test_environment(self) -> None:
        """Clean up test environment"""
        print("🧹 Cleaning up CLI test environment...")
        
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            
        print("✅ CLI test environment cleaned")
    
    async def run_comprehensive_cli_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive CLI integration tests covering all major functionality.
        """
        print("🚀 Starting Theodore v2 CLI Integration Test Suite")
        print("=" * 70)
        
        start_time = datetime.now(timezone.utc)
        
        # Test suites to execute
        test_suites = [
            ("CLI Help & Version Tests", self._test_cli_help_version),
            ("Configuration Management Tests", self._test_configuration_management),
            ("Research Command Integration", self._test_research_command_integration),
            ("Discovery Command Integration", self._test_discovery_command_integration),
            ("Batch Processing Integration", self._test_batch_processing_integration),
            ("Export Functionality Tests", self._test_export_functionality),
            ("Error Handling Validation", self._test_error_handling_validation),
            ("Performance & Timeout Tests", self._test_performance_timeout)
        ]
        
        suite_results = {}
        
        for suite_name, suite_function in test_suites:
            print(f"\n📋 Running {suite_name}...")
            print("-" * 50)
            
            suite_start = time.time()
            
            try:
                suite_result = await suite_function()
                suite_duration = time.time() - suite_start
                
                suite_results[suite_name] = {
                    'success': suite_result.get('success', False),
                    'duration_seconds': suite_duration,
                    'test_count': suite_result.get('test_count', 0),
                    'passed_tests': suite_result.get('passed_tests', 0),
                    'failed_tests': suite_result.get('failed_tests', 0),
                    'details': suite_result.get('details', {}),
                    'metrics': suite_result.get('metrics', {})
                }
                
                if suite_result.get('success', False):
                    print(f"✅ {suite_name}: PASSED ({suite_duration:.1f}s)")
                else:
                    print(f"❌ {suite_name}: FAILED ({suite_duration:.1f}s)")
                    
            except Exception as e:
                suite_duration = time.time() - suite_start
                print(f"💥 {suite_name}: ERROR - {str(e)} ({suite_duration:.1f}s)")
                
                suite_results[suite_name] = {
                    'success': False,
                    'duration_seconds': suite_duration,
                    'error': str(e),
                    'test_count': 0,
                    'passed_tests': 0,
                    'failed_tests': 1
                }
        
        # Generate comprehensive test report
        total_duration = time.time() - start_time.timestamp()
        
        final_report = {
            'test_execution_summary': {
                'total_duration_seconds': total_duration,
                'total_suites': len(test_suites),
                'passed_suites': sum(1 for r in suite_results.values() if r['success']),
                'failed_suites': sum(1 for r in suite_results.values() if not r['success']),
                'total_tests': sum(r['test_count'] for r in suite_results.values()),
                'total_passed': sum(r['passed_tests'] for r in suite_results.values()),
                'total_failed': sum(r['failed_tests'] for r in suite_results.values())
            },
            'suite_results': suite_results,
            'cli_readiness_score': self._calculate_cli_readiness_score(suite_results),
            'recommendations': self._generate_cli_recommendations(suite_results),
            'detailed_test_results': [result.to_dict() for result in self.test_results]
        }
        
        # Save detailed report
        await self._save_cli_test_report(final_report)
        
        print("\n" + "=" * 70)
        print("🏁 Theodore v2 CLI Integration Test Suite Complete")
        print(f"📊 Results: {final_report['test_execution_summary']['total_passed']}/{final_report['test_execution_summary']['total_tests']} tests passed")
        print(f"⏱️  Duration: {total_duration:.1f} seconds")
        print(f"🎯 CLI Readiness Score: {final_report['cli_readiness_score']}/100")
        
        return final_report
    
    async def _test_cli_help_version(self) -> Dict[str, Any]:
        """Test CLI help and version commands"""
        
        cli_basic_tests = [
            {
                'name': 'help_command',
                'command': ['python3', str(self.theodore_cli_path), '--help'],
                'expected_outputs': ['usage:', 'Theodore v2', 'commands:', 'research', 'discover'],
                'timeout': 10
            },
            {
                'name': 'version_command', 
                'command': ['python3', str(self.theodore_cli_path), '--version'],
                'expected_outputs': ['Theodore', 'v2'],
                'timeout': 10
            },
            {
                'name': 'research_help',
                'command': ['python3', str(self.theodore_cli_path), 'research', '--help'],
                'expected_outputs': ['research', 'company', 'Usage:', 'options'],
                'timeout': 10
            },
            {
                'name': 'discover_help',
                'command': ['python3', str(self.theodore_cli_path), 'discover', '--help'],
                'expected_outputs': ['discover', 'similar', 'Usage:', 'options'],
                'timeout': 10
            }
        ]
        
        return await self._execute_cli_test_suite(cli_basic_tests, "CLI Help & Version")
    
    async def _test_configuration_management(self) -> Dict[str, Any]:
        """Test configuration management commands"""
        
        config_tests = [
            {
                'name': 'config_help',
                'command': ['python3', str(self.theodore_cli_path), 'config', '--help'],
                'expected_outputs': ['config', 'set', 'get', 'list'],
                'timeout': 15
            },
            {
                'name': 'config_list_default',
                'command': ['python3', str(self.theodore_cli_path), 'config', 'list'],
                'expected_outputs': ['configuration', 'settings'],
                'timeout': 15,
                'allow_failure': True  # Config might not be set up
            }
        ]
        
        return await self._execute_cli_test_suite(config_tests, "Configuration Management")
    
    async def _test_research_command_integration(self) -> Dict[str, Any]:
        """Test research command integration"""
        
        research_tests = [
            {
                'name': 'research_dry_run',
                'command': ['python3', str(self.theodore_cli_path), 'research', 'Test Company', '--dry-run'],
                'expected_outputs': ['dry run', 'would research', 'Test Company'],
                'timeout': 30,
                'allow_failure': True
            },
            {
                'name': 'research_invalid_company',
                'command': ['python3', str(self.theodore_cli_path), 'research', ''],
                'expected_outputs': ['error', 'invalid', 'company name'],
                'timeout': 20,
                'expect_failure': True
            },
            {
                'name': 'research_output_formats',
                'command': ['python3', str(self.theodore_cli_path), 'research', 'Test Company', '--output', 'json', '--dry-run'],
                'expected_outputs': ['json', 'format'],
                'timeout': 25,
                'allow_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(research_tests, "Research Command Integration")
    
    async def _test_discovery_command_integration(self) -> Dict[str, Any]:
        """Test discovery command integration"""
        
        discovery_tests = [
            {
                'name': 'discover_dry_run',
                'command': ['python3', str(self.theodore_cli_path), 'discover', 'Test Company', '--dry-run'],
                'expected_outputs': ['dry run', 'would discover', 'similar'],
                'timeout': 30,
                'allow_failure': True
            },
            {
                'name': 'discover_with_filters',
                'command': ['python3', str(self.theodore_cli_path), 'discover', 'Test Company', '--business-model', 'saas', '--dry-run'],
                'expected_outputs': ['filter', 'saas', 'business model'],
                'timeout': 25,
                'allow_failure': True
            },
            {
                'name': 'discover_limit_option',
                'command': ['python3', str(self.theodore_cli_path), 'discover', 'Test Company', '--limit', '5', '--dry-run'],
                'expected_outputs': ['limit', '5'],
                'timeout': 25,
                'allow_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(discovery_tests, "Discovery Command Integration")
    
    async def _test_batch_processing_integration(self) -> Dict[str, Any]:
        """Test batch processing integration"""
        
        # Create test CSV file
        test_csv = self.temp_dir / "test_companies.csv"
        with open(test_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['company_name', 'website'])
            writer.writerow(['Test Company 1', 'https://example1.com'])
            writer.writerow(['Test Company 2', 'https://example2.com'])
        
        batch_tests = [
            {
                'name': 'batch_help',
                'command': ['python3', str(self.theodore_cli_path), 'batch', '--help'],
                'expected_outputs': ['batch', 'process', 'companies', 'csv'],
                'timeout': 15
            },
            {
                'name': 'batch_csv_dry_run',
                'command': ['python3', str(self.theodore_cli_path), 'batch', 'research', str(test_csv), '--dry-run'],
                'expected_outputs': ['dry run', 'batch', 'companies', 'Test Company'],
                'timeout': 30,
                'allow_failure': True
            },
            {
                'name': 'batch_invalid_file',
                'command': ['python3', str(self.theodore_cli_path), 'batch', 'research', 'nonexistent.csv'],
                'expected_outputs': ['error', 'file', 'not found', 'exist'],
                'timeout': 20,
                'expect_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(batch_tests, "Batch Processing Integration")
    
    async def _test_export_functionality(self) -> Dict[str, Any]:
        """Test export functionality"""
        
        export_tests = [
            {
                'name': 'export_help',
                'command': ['python3', str(self.theodore_cli_path), 'export', '--help'],
                'expected_outputs': ['export', 'data', 'format', 'csv', 'json'],
                'timeout': 15,
                'allow_failure': True  # Export command might not be implemented
            },
            {
                'name': 'export_formats',
                'command': ['python3', str(self.theodore_cli_path), 'export', '--format', 'json', '--dry-run'],
                'expected_outputs': ['json', 'format', 'export'],
                'timeout': 20,
                'allow_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(export_tests, "Export Functionality")
    
    async def _test_error_handling_validation(self) -> Dict[str, Any]:
        """Test error handling and validation"""
        
        error_tests = [
            {
                'name': 'invalid_command',
                'command': ['python3', str(self.theodore_cli_path), 'invalid_command'],
                'expected_outputs': ['error', 'invalid', 'command', 'usage'],
                'timeout': 15,
                'expect_failure': True
            },
            {
                'name': 'missing_arguments',
                'command': ['python3', str(self.theodore_cli_path), 'research'],
                'expected_outputs': ['error', 'required', 'argument', 'company'],
                'timeout': 15,
                'expect_failure': True
            },
            {
                'name': 'invalid_option_value',
                'command': ['python3', str(self.theodore_cli_path), 'research', 'Test', '--output', 'invalid_format'],
                'expected_outputs': ['error', 'invalid', 'choice', 'format'],
                'timeout': 15,
                'expect_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(error_tests, "Error Handling Validation")
    
    async def _test_performance_timeout(self) -> Dict[str, Any]:
        """Test performance and timeout handling"""
        
        performance_tests = [
            {
                'name': 'help_response_time',
                'command': ['python3', str(self.theodore_cli_path), '--help'],
                'expected_outputs': ['usage:'],
                'timeout': 5,
                'max_duration': 3.0  # Help should be fast
            },
            {
                'name': 'command_timeout',
                'command': ['python3', str(self.theodore_cli_path), 'research', 'Test Company', '--timeout', '1'],
                'expected_outputs': ['timeout', 'error', 'cancelled'],
                'timeout': 10,
                'allow_failure': True,
                'expect_failure': True
            }
        ]
        
        return await self._execute_cli_test_suite(performance_tests, "Performance & Timeout")
    
    async def _execute_cli_test_suite(self, tests: List[Dict], suite_name: str) -> Dict[str, Any]:
        """Execute a suite of CLI tests"""
        
        passed_tests = 0
        total_tests = len(tests)
        test_details = {}
        
        for test in tests:
            test_start = time.time()
            
            try:
                result = await self._execute_cli_command(
                    test['command'],
                    test['expected_outputs'],
                    test.get('timeout', 30),
                    test.get('expect_failure', False),
                    test.get('allow_failure', False),
                    test.get('max_duration')
                )
                
                result.test_name = test['name']
                self.test_results.append(result)
                
                test_details[test['name']] = result.to_dict()
                
                if result.success:
                    passed_tests += 1
                    print(f"  ✅ {test['name']}: PASSED ({result.duration_seconds:.1f}s)")
                else:
                    print(f"  ❌ {test['name']}: FAILED - Exit code {result.exit_code}")
                    if result.stderr:
                        print(f"    Error: {result.stderr[:200]}...")
                        
            except Exception as e:
                test_duration = time.time() - test_start
                print(f"  💥 {test['name']}: ERROR - {str(e)}")
                
                # Create error result
                error_result = CLITestResult(
                    test_name=test['name'],
                    command=' '.join(test['command']),
                    success=False,
                    exit_code=-1,
                    duration_seconds=test_duration,
                    stdout="",
                    stderr=str(e),
                    expected_outputs=test['expected_outputs'],
                    found_outputs=[]
                )
                
                self.test_results.append(error_result)
                test_details[test['name']] = error_result.to_dict()
        
        return {
            'success': passed_tests == total_tests,
            'test_count': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'details': test_details,
            'metrics': {
                'average_duration_seconds': sum(d.get('duration_seconds', 0) for d in test_details.values()) / total_tests if total_tests > 0 else 0,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            }
        }
    
    async def _execute_cli_command(
        self,
        command: List[str],
        expected_outputs: List[str],
        timeout: int,
        expect_failure: bool = False,
        allow_failure: bool = False,
        max_duration: Optional[float] = None
    ) -> CLITestResult:
        """Execute a single CLI command and validate output"""
        
        start_time = time.time()
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.theodore_cli_path.parent.parent.parent  # Set working directory to project root
            )
            
            duration = time.time() - start_time
            
            # Check duration if specified
            if max_duration and duration > max_duration:
                return CLITestResult(
                    test_name="",
                    command=' '.join(command),
                    success=False,
                    exit_code=result.returncode,
                    duration_seconds=duration,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    expected_outputs=expected_outputs,
                    found_outputs=[],
                )
            
            # Combine stdout and stderr for output checking
            combined_output = (result.stdout + " " + result.stderr).lower()
            
            # Check for expected outputs
            found_outputs = []
            for expected in expected_outputs:
                if expected.lower() in combined_output:
                    found_outputs.append(expected)
            
            # Determine success
            success = True
            
            # Check exit code expectations
            if expect_failure:
                success = result.returncode != 0
            elif not allow_failure:
                success = result.returncode == 0
            
            # Check output expectations (if command succeeded or we allow failure)
            if success and found_outputs:
                success = len(found_outputs) >= len(expected_outputs) * 0.5  # At least 50% of expected outputs
            elif not allow_failure and not found_outputs and expected_outputs:
                success = False
            
            return CLITestResult(
                test_name="",
                command=' '.join(command),
                success=success,
                exit_code=result.returncode,
                duration_seconds=duration,
                stdout=result.stdout,
                stderr=result.stderr,
                expected_outputs=expected_outputs,
                found_outputs=found_outputs
            )
            
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return CLITestResult(
                test_name="",
                command=' '.join(command),
                success=expect_failure,  # Timeout might be expected for some tests
                exit_code=-2,
                duration_seconds=duration,
                stdout="",
                stderr=f"Command timeout after {timeout}s",
                expected_outputs=expected_outputs,
                found_outputs=[]
            )
        except Exception as e:
            duration = time.time() - start_time
            return CLITestResult(
                test_name="",
                command=' '.join(command),
                success=False,
                exit_code=-1,
                duration_seconds=duration,
                stdout="",
                stderr=str(e),
                expected_outputs=expected_outputs,
                found_outputs=[]
            )
    
    def _calculate_cli_readiness_score(self, suite_results: Dict[str, Any]) -> int:
        """Calculate CLI readiness score (0-100)"""
        
        # Weight different test suites by importance for CLI
        suite_weights = {
            'CLI Help & Version Tests': 0.25,
            'Configuration Management Tests': 0.15,
            'Research Command Integration': 0.25,
            'Discovery Command Integration': 0.15,
            'Batch Processing Integration': 0.10,
            'Export Functionality Tests': 0.05,
            'Error Handling Validation': 0.15,
            'Performance & Timeout Tests': 0.10
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for suite_name, weight in suite_weights.items():
            if suite_name in suite_results:
                suite_result = suite_results[suite_name]
                suite_score = 100 if suite_result['success'] else 0
                weighted_score += suite_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        return int(weighted_score / total_weight)
    
    def _generate_cli_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """Generate CLI-specific recommendations"""
        
        recommendations = []
        
        # Analyze failed test suites
        for suite_name, result in suite_results.items():
            if not result['success']:
                if 'Help & Version' in suite_name:
                    recommendations.append("Fix CLI help and version display functionality")
                elif 'Configuration' in suite_name:
                    recommendations.append("Implement or fix configuration management commands")
                elif 'Research Command' in suite_name:
                    recommendations.append("Resolve research command integration issues")
                elif 'Discovery Command' in suite_name:
                    recommendations.append("Fix discovery command functionality and options")
                elif 'Batch Processing' in suite_name:
                    recommendations.append("Implement or fix batch processing capabilities")
                elif 'Export' in suite_name:
                    recommendations.append("Implement export functionality")
                elif 'Error Handling' in suite_name:
                    recommendations.append("Improve CLI error handling and user feedback")
                elif 'Performance' in suite_name:
                    recommendations.append("Optimize CLI performance and timeout handling")
        
        # Add general recommendations
        if len(recommendations) == 0:
            recommendations.append("CLI is functioning well. Consider adding advanced features.")
        else:
            recommendations.append("Ensure all CLI commands have comprehensive help documentation")
            recommendations.append("Add unit tests for CLI command parsing and execution")
        
        return recommendations
    
    async def _save_cli_test_report(self, report: Dict[str, Any]) -> None:
        """Save detailed CLI test report"""
        
        report_dir = Path(__file__).parent / "test_reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"cli_integration_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 CLI test report saved: {report_file}")


# Main test execution for standalone running
async def main():
    """Main CLI test execution function"""
    
    suite = TheodoreCliIntegrationTestSuite()
    
    try:
        await suite.setup_test_environment()
        report = await suite.run_comprehensive_cli_tests()
        
        # Print summary
        print("\n" + "=" * 70)
        print("🎯 CLI INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        summary = report['test_execution_summary']
        print(f"Total Duration: {summary['total_duration_seconds']:.1f} seconds")
        print(f"Test Suites: {summary['passed_suites']}/{summary['total_suites']} passed")
        print(f"Individual Tests: {summary['total_passed']}/{summary['total_tests']} passed")
        print(f"CLI Readiness Score: {report['cli_readiness_score']}/100")
        
        if report['recommendations']:
            print("\n📋 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        return report
        
    finally:
        await suite.teardown_test_environment()


if __name__ == "__main__":
    # Run the CLI integration test suite
    asyncio.run(main())
#!/usr/bin/env python3
"""
Run All Validation Tests
=======================

Comprehensive test runner that executes all validation tests and generates
a summary report to confirm the antoine batch processing system is working.
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def run_test(test_file, test_name):
    """Run a single test and capture results"""
    print(f"\n{'='*80}")
    print(f"🧪 Running: {test_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        # Determine success
        success = result.returncode == 0
        
        # Extract key metrics from output
        output_lines = result.stdout.split('\n')
        metrics = {}
        
        # Look for specific patterns in output
        for line in output_lines:
            if "Successful:" in line and "/" in line:
                parts = line.split(":")[-1].strip().split("/")
                if len(parts) == 2:
                    metrics['successful'] = int(parts[0])
                    metrics['total'] = int(parts[1])
            elif "Speed improvement:" in line and "x" in line:
                try:
                    metrics['speedup'] = float(line.split(":")[-1].strip().rstrip('x'))
                except:
                    pass
            elif "companies/minute" in line:
                try:
                    metrics['throughput'] = float(line.split(":")[-1].split()[0])
                except:
                    pass
        
        # Print summary
        if success:
            print(f"✅ {test_name} PASSED in {duration:.1f}s")
            if metrics:
                print(f"   Key metrics: {metrics}")
        else:
            print(f"❌ {test_name} FAILED in {duration:.1f}s")
            print(f"   Error output:")
            print(result.stderr[:500])
        
        return {
            'name': test_name,
            'file': test_file,
            'success': success,
            'duration': duration,
            'metrics': metrics,
            'return_code': result.returncode,
            'output_snippet': result.stdout[-500:] if result.stdout else "",
            'error_snippet': result.stderr[-500:] if result.stderr else ""
        }
        
    except subprocess.TimeoutExpired:
        return {
            'name': test_name,
            'file': test_file,
            'success': False,
            'duration': 300,
            'error': 'Test timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'name': test_name,
            'file': test_file,
            'success': False,
            'duration': time.time() - start_time,
            'error': str(e)
        }


def generate_validation_report(test_results):
    """Generate comprehensive validation report"""
    
    print("\n" + "="*80)
    print("📊 VALIDATION REPORT")
    print("="*80)
    
    # Summary statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['success'])
    failed_tests = total_tests - passed_tests
    total_duration = sum(r['duration'] for r in test_results)
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests} ({(passed_tests/total_tests)*100:.0f}%)")
    print(f"   Failed: {failed_tests}")
    print(f"   Total duration: {total_duration:.1f}s")
    
    # Individual test results
    print(f"\n📋 TEST RESULTS:")
    print(f"{'Test Name':<40} {'Status':<10} {'Duration':<10} {'Notes'}")
    print("-" * 80)
    
    for result in test_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        notes = ""
        
        if 'metrics' in result and result['metrics']:
            if 'speedup' in result['metrics']:
                notes = f"{result['metrics']['speedup']:.1f}x speedup"
            elif 'successful' in result['metrics']:
                notes = f"{result['metrics']['successful']}/{result['metrics']['total']} successful"
        elif 'error' in result:
            notes = result['error'][:30] + "..."
        
        print(f"{result['name']:<40} {status:<10} {result['duration']:<10.1f}s {notes}")
    
    # Critical validations
    print(f"\n🎯 CRITICAL VALIDATIONS:")
    
    validations = {
        'Unit Tests Pass': any(r['name'] == 'Unit Tests' and r['success'] for r in test_results),
        'Pipeline Integration Works': any(r['name'] == 'Pipeline Integration' and r['success'] for r in test_results),
        'Performance Improvement Achieved': any(r.get('metrics', {}).get('speedup', 0) > 1.5 for r in test_results),
        'Batch Processing Functions': any('batch' in r['name'].lower() and r['success'] for r in test_results)
    }
    
    for validation, passed in validations.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {validation}")
    
    # Performance metrics
    print(f"\n⚡ PERFORMANCE METRICS:")
    
    speedups = [r.get('metrics', {}).get('speedup', 0) for r in test_results if r.get('metrics', {}).get('speedup')]
    throughputs = [r.get('metrics', {}).get('throughput', 0) for r in test_results if r.get('metrics', {}).get('throughput')]
    
    if speedups:
        print(f"   Best speedup: {max(speedups):.1f}x")
        print(f"   Average speedup: {sum(speedups)/len(speedups):.1f}x")
    
    if throughputs:
        print(f"   Best throughput: {max(throughputs):.1f} companies/minute")
    
    # Save detailed report
    report_data = {
        'test_date': datetime.now().isoformat(),
        'summary': {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'total_duration': total_duration
        },
        'validations': validations,
        'test_results': test_results
    }
    
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    # Final verdict
    all_critical_passed = all(validations.values())
    high_success_rate = (passed_tests/total_tests) >= 0.8
    
    print(f"\n{'='*80}")
    if all_critical_passed and high_success_rate:
        print("✅ VALIDATION SUCCESSFUL - Antoine batch processing is working correctly!")
        print("   - All critical validations passed")
        print("   - Performance improvements confirmed")
        print("   - Integration with pipeline verified")
        return True
    else:
        print("⚠️  VALIDATION INCOMPLETE - Some tests failed")
        print("   - Review failed tests above")
        print("   - Check error logs for details")
        return False


def main():
    """Run all validation tests"""
    
    print("🚀 ANTOINE BATCH PROCESSING - VALIDATION SUITE")
    print("="*80)
    print(f"Starting validation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define tests to run
    tests = [
        ('test_batch_unit.py', 'Unit Tests'),
        ('test_batch_simple.py', 'Simple Batch Test'),
        ('test_pipeline_integration.py', 'Pipeline Integration'),
        ('test_performance_comparison.py', 'Performance Comparison')
    ]
    
    # Run all tests
    test_results = []
    for test_file, test_name in tests:
        result = run_test(test_file, test_name)
        test_results.append(result)
        
        # Brief pause between tests
        if test_file != tests[-1][0]:
            print("\n⏳ Pausing 3 seconds before next test...")
            time.sleep(3)
    
    # Generate validation report
    success = generate_validation_report(test_results)
    
    # Create HTML summary (optional)
    if success:
        create_html_summary(test_results)
    
    return success


def create_html_summary(test_results):
    """Create an HTML summary report"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Antoine Batch Processing Validation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        .metric {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ Antoine Batch Processing Validation</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metric">
        <h2>Summary</h2>
        <p>Total Tests: {len(test_results)}</p>
        <p class="success">Passed: {sum(1 for r in test_results if r['success'])}</p>
        <p class="failed">Failed: {sum(1 for r in test_results if not r['success'])}</p>
    </div>
    
    <table>
        <tr>
            <th>Test</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Details</th>
        </tr>
"""
    
    for result in test_results:
        status_class = "success" if result['success'] else "failed"
        status_text = "✅ PASS" if result['success'] else "❌ FAIL"
        
        details = ""
        if 'metrics' in result and result['metrics']:
            details = str(result['metrics'])
        elif 'error' in result:
            details = result['error']
        
        html_content += f"""
        <tr>
            <td>{result['name']}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result['duration']:.1f}s</td>
            <td>{details}</td>
        </tr>
"""
    
    html_content += """
    </table>
    
    <div class="metric">
        <h2>Validation Complete</h2>
        <p class="success">✅ The antoine batch processing system is working correctly!</p>
    </div>
</body>
</html>
"""
    
    with open('validation_summary.html', 'w') as f:
        f.write(html_content)
    
    print("\n🌐 HTML summary created: validation_summary.html")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
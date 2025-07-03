#!/usr/bin/env python3
"""
Theodore v2 Test Runner

Simple script to run the comprehensive testing framework.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.integration.comprehensive_test_runner import ComprehensiveTestRunner


async def main():
    """Main test runner"""
    
    print("🚀 Starting Theodore v2 Comprehensive Testing Framework")
    print("=" * 80)
    
    # Initialize test runner
    runner = ComprehensiveTestRunner()
    
    try:
        # Run quick validation by default
        summary = await runner.run_quick_validation()
        
        # Display results
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        status_emoji = "✅" if summary.overall_success_rate >= 0.9 else "⚠️" if summary.overall_success_rate >= 0.7 else "❌"
        print(f"{status_emoji} Overall Success Rate: {summary.overall_success_rate:.1%}")
        print(f"⏱️  Total Duration: {summary.total_duration_seconds:.1f} seconds")
        print(f"📈 Quality Score: {summary.quality_score:.1%}")
        print(f"⚡ Performance Score: {summary.performance_score:.1%}")
        print(f"🔒 Security Score: {summary.security_score:.1%}")
        print(f"🛡️  Reliability Score: {summary.reliability_score:.1%}")
        
        if summary.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(summary.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "=" * 80)
        
        # Exit with appropriate code
        exit_code = 0 if summary.overall_success_rate >= 0.9 else 1
        if exit_code == 0:
            print("🎉 All tests passed! Theodore v2 is ready.")
        else:
            print("⚠️  Some tests failed. Please review the results above.")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Simple CLI Integration Test for Theodore v2
===========================================

Simplified CLI integration tests to validate CLI functionality
without complex dependencies.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any


class SimpleCLITest:
    """Simple CLI test runner"""
    
    def __init__(self):
        self.results = []
        self.project_root = Path(__file__).parent.parent
        
    def run_cli_tests(self) -> Dict[str, Any]:
        """Run CLI integration tests"""
        
        print("🖥️  Theodore v2 CLI Integration Tests")
        print("=" * 45)
        print(f"📅 Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        start_time = time.time()
        
        # Test CLI commands
        self._test_cli_help()
        self._test_cli_version()
        self._test_cli_test_command()
        self._test_cli_verbose_mode()
        self._test_cli_invalid_command()
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = self._generate_summary(total_duration)
        
        print("\n" + "=" * 45)
        print("📊 CLI TEST SUMMARY")
        print("=" * 45)
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"🏆 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL CLI TESTS PASSED!")
        else:
            print("\n⚠️  Some CLI tests failed.")
            
        return summary
    
    def _run_cli_command(self, args: List[str], timeout: int = 10) -> Dict[str, Any]:
        """Run CLI command and return results"""
        
        command = [sys.executable, "src/cli/entry_point.py"] + args
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            duration = time.time() - start_time
            
            return {
                "command": " ".join(command),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "command": " ".join(command),
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "duration": timeout,
                "success": False
            }
        except Exception as e:
            return {
                "command": " ".join(command),
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": 0,
                "success": False
            }
    
    def _test_cli_help(self):
        """Test CLI help command"""
        print("🔍 Testing CLI help command...")
        
        result = self._run_cli_command(["--help"])
        
        expected_texts = [
            "Theodore AI Company Intelligence System",
            "Options:",
            "Commands:",
            "test"
        ]
        
        found_texts = []
        for text in expected_texts:
            if text in result["stdout"]:
                found_texts.append(text)
        
        success = result["success"] and len(found_texts) == len(expected_texts)
        
        test_result = {
            "test_name": "CLI Help Command",
            "success": success,
            "expected_texts": len(expected_texts),
            "found_texts": len(found_texts),
            "duration": result["duration"],
            "exit_code": result["exit_code"]
        }
        
        if success:
            print("  ✅ CLI help test PASSED")
        else:
            print(f"  ❌ CLI help test FAILED - Found {len(found_texts)}/{len(expected_texts)} expected texts")
            
        self.results.append(test_result)
    
    def _test_cli_version(self):
        """Test CLI version command"""
        print("\n🔢 Testing CLI version command...")
        
        result = self._run_cli_command(["--version"])
        
        success = result["success"] and "2.0.0" in result["stdout"]
        
        test_result = {
            "test_name": "CLI Version Command",
            "success": success,
            "duration": result["duration"],
            "exit_code": result["exit_code"],
            "version_found": "2.0.0" in result["stdout"]
        }
        
        if success:
            print("  ✅ CLI version test PASSED")
        else:
            print("  ❌ CLI version test FAILED")
            
        self.results.append(test_result)
    
    def _test_cli_test_command(self):
        """Test CLI test command"""
        print("\n🧪 Testing CLI test command...")
        
        result = self._run_cli_command(["test"])
        
        expected_texts = [
            "Theodore v2 CLI is working",
            "Full commands temporarily disabled"
        ]
        
        found_texts = []
        for text in expected_texts:
            if text in result["stdout"]:
                found_texts.append(text)
        
        success = result["success"] and len(found_texts) == len(expected_texts)
        
        test_result = {
            "test_name": "CLI Test Command",
            "success": success,
            "expected_texts": len(expected_texts),
            "found_texts": len(found_texts),
            "duration": result["duration"],
            "exit_code": result["exit_code"]
        }
        
        if success:
            print("  ✅ CLI test command PASSED")
        else:
            print(f"  ❌ CLI test command FAILED - Found {len(found_texts)}/{len(expected_texts)} expected texts")
            
        self.results.append(test_result)
    
    def _test_cli_verbose_mode(self):
        """Test CLI verbose mode"""
        print("\n📢 Testing CLI verbose mode...")
        
        result = self._run_cli_command(["--verbose", "test"])
        
        success = result["success"] and "Verbose mode enabled" in result["stdout"]
        
        test_result = {
            "test_name": "CLI Verbose Mode",
            "success": success,
            "duration": result["duration"],
            "exit_code": result["exit_code"],
            "verbose_found": "Verbose mode enabled" in result["stdout"]
        }
        
        if success:
            print("  ✅ CLI verbose mode test PASSED")
        else:
            print("  ❌ CLI verbose mode test FAILED")
            
        self.results.append(test_result)
    
    def _test_cli_invalid_command(self):
        """Test CLI invalid command handling"""
        print("\n❌ Testing CLI invalid command handling...")
        
        result = self._run_cli_command(["invalid-command"])
        
        # Invalid command should fail (non-zero exit code)
        success = not result["success"] and result["exit_code"] != 0
        
        test_result = {
            "test_name": "CLI Invalid Command",
            "success": success,
            "duration": result["duration"],
            "exit_code": result["exit_code"],
            "properly_failed": not result["success"]
        }
        
        if success:
            print("  ✅ CLI invalid command handling test PASSED")
        else:
            print("  ❌ CLI invalid command handling test FAILED")
            
        self.results.append(test_result)
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate test summary"""
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        return {
            "test_type": "CLI_Integration",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed/total)*100 if total > 0 else 0,
            "total_duration_seconds": total_duration,
            "test_results": self.results,
            "cli_functionality_score": self._calculate_cli_score()
        }
    
    def _calculate_cli_score(self) -> Dict[str, Any]:
        """Calculate CLI functionality score"""
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        score = (passed/total)*100 if total > 0 else 0
        
        if score >= 95:
            level = "EXCELLENT"
        elif score >= 80:
            level = "GOOD"
        elif score >= 60:
            level = "ADEQUATE"
        else:
            level = "NEEDS_IMPROVEMENT"
        
        return {
            "score": score,
            "level": level,
            "tests_passed": passed,
            "tests_total": total
        }


def main():
    """Main CLI test function"""
    
    cli_test = SimpleCLITest()
    summary = cli_test.run_cli_tests()
    
    # Save results
    output_file = Path("cli_test_results.json")
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 CLI test results saved to: {output_file}")
    
    # Return exit code based on success
    if summary["failed_tests"] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Simple Theodore v2 Test Runner for TICKET-027 Validation
=========================================================

Simplified test runner to validate the testing framework itself
without complex dependencies.
"""

import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SimpleTestResult:
    """Simple test result tracking"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.duration = 0.0
        self.errors = []
        self.warnings = []
        self.start_time = None
    
    def start(self):
        self.start_time = time.time()
        
    def finish(self, success: bool = True, error: str = None):
        self.duration = time.time() - self.start_time if self.start_time else 0.0
        self.success = success
        if error:
            self.errors.append(error)
    
    def to_dict(self):
        return {
            "test_name": self.test_name,
            "success": self.success,
            "duration_seconds": self.duration,
            "errors": self.errors,
            "warnings": self.warnings
        }


class SimpleTestSuite:
    """Simple test suite for validating Theodore v2 infrastructure"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all infrastructure tests"""
        
        print("🚀 Theodore v2 Simple Test Suite")
        print("=" * 50)
        print(f"📅 Started: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        self.start_time = time.time()
        
        # Test 1: Basic Import Tests
        self._test_basic_imports()
        
        # Test 2: Container Creation
        self._test_container_creation()
        
        # Test 3: CLI Functionality
        self._test_cli_functionality()
        
        # Test 4: File Structure Validation
        self._test_file_structure()
        
        # Test 5: Configuration Loading
        self._test_configuration()
        
        total_duration = time.time() - self.start_time
        
        # Generate summary
        summary = self._generate_summary(total_duration)
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.results if r.success])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"🏆 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Theodore v2 infrastructure is working!")
        else:
            print("\n⚠️  Some tests failed. See details above.")
            
        return summary
    
    def _test_basic_imports(self):
        """Test basic module imports"""
        test = SimpleTestResult("Basic Module Imports")
        test.start()
        
        try:
            print("🔍 Testing basic imports...")
            
            # Test core imports
            from src.infrastructure.container.application import ApplicationContainer
            print("  ✅ ApplicationContainer import successful")
            
            # Test CLI imports
            from src.cli.main import cli
            print("  ✅ CLI import successful")
            
            # Test domain imports
            from src.core.domain.entities.company import Company
            print("  ✅ Company entity import successful")
            
            test.finish(True)
            print("  🎉 Basic imports test PASSED")
            
        except Exception as e:
            test.finish(False, str(e))
            print(f"  ❌ Basic imports test FAILED: {e}")
            
        self.results.append(test)
    
    def _test_container_creation(self):
        """Test container creation"""
        test = SimpleTestResult("Container Creation")
        test.start()
        
        try:
            print("\n🏗️  Testing container creation...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            # Create container
            container = ApplicationContainer()
            print("  ✅ Container instantiation successful")
            
            # Test basic container properties
            assert hasattr(container, 'config'), "Container should have config"
            assert hasattr(container, 'storage'), "Container should have storage"
            print("  ✅ Container structure validation successful")
            
            test.finish(True)
            print("  🎉 Container creation test PASSED")
            
        except Exception as e:
            test.finish(False, str(e))
            print(f"  ❌ Container creation test FAILED: {e}")
            
        self.results.append(test)
    
    def _test_cli_functionality(self):
        """Test CLI functionality"""
        test = SimpleTestResult("CLI Functionality")
        test.start()
        
        try:
            print("\n🖥️  Testing CLI functionality...")
            
            import subprocess
            import sys
            
            # Test CLI help command
            result = subprocess.run([
                sys.executable, 'src/cli/entry_point.py', '--help'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("  ✅ CLI help command successful")
            else:
                raise Exception(f"CLI help failed with code {result.returncode}")
            
            # Test CLI test command
            result = subprocess.run([
                sys.executable, 'src/cli/entry_point.py', 'test'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Theodore v2 CLI is working" in result.stdout:
                print("  ✅ CLI test command successful")
            else:
                raise Exception(f"CLI test command failed")
            
            test.finish(True)
            print("  🎉 CLI functionality test PASSED")
            
        except Exception as e:
            test.finish(False, str(e))
            print(f"  ❌ CLI functionality test FAILED: {e}")
            
        self.results.append(test)
    
    def _test_file_structure(self):
        """Test file structure"""
        test = SimpleTestResult("File Structure Validation")
        test.start()
        
        try:
            print("\n📁 Testing file structure...")
            
            required_files = [
                "src/cli/main.py",
                "src/cli/entry_point.py", 
                "src/infrastructure/container/application.py",
                "src/core/domain/entities/company.py",
                "tests/run_integration_tests.py",
                "tests/simple_test_runner.py",
                "setup.py"
            ]
            
            for file_path in required_files:
                if not Path(file_path).exists():
                    raise Exception(f"Required file missing: {file_path}")
                    
            print(f"  ✅ All {len(required_files)} required files present")
            
            test.finish(True)
            print("  🎉 File structure test PASSED")
            
        except Exception as e:
            test.finish(False, str(e))
            print(f"  ❌ File structure test FAILED: {e}")
            
        self.results.append(test)
    
    def _test_configuration(self):
        """Test configuration loading"""
        test = SimpleTestResult("Configuration Loading")
        test.start()
        
        try:
            print("\n⚙️  Testing configuration...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            container = ApplicationContainer()
            
            # Test configuration provider exists
            assert hasattr(container, 'config'), "Container should have config provider"
            print("  ✅ Configuration provider exists")
            
            # Test basic configuration operations
            config = container.config
            assert config is not None, "Config should not be None"
            print("  ✅ Configuration accessible")
            
            test.finish(True)
            print("  🎉 Configuration test PASSED")
            
        except Exception as e:
            test.finish(False, str(e))
            print(f"  ❌ Configuration test FAILED: {e}")
            
        self.results.append(test)
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate test summary"""
        
        passed = len([r for r in self.results if r.success])
        total = len(self.results)
        
        return {
            "test_run_id": str(time.time()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed/total)*100 if total > 0 else 0,
            "total_duration_seconds": total_duration,
            "test_results": [r.to_dict() for r in self.results],
            "enterprise_readiness": self._calculate_enterprise_readiness()
        }
    
    def _calculate_enterprise_readiness(self) -> Dict[str, Any]:
        """Calculate enterprise readiness score"""
        
        passed = len([r for r in self.results if r.success])
        total = len(self.results)
        
        base_score = (passed/total)*100 if total > 0 else 0
        
        # Enterprise readiness criteria
        readiness_factors = {
            "infrastructure_stability": base_score,
            "cli_functionality": 100 if any(r.test_name == "CLI Functionality" and r.success for r in self.results) else 0,
            "container_architecture": 100 if any(r.test_name == "Container Creation" and r.success for r in self.results) else 0,
            "file_organization": 100 if any(r.test_name == "File Structure Validation" and r.success for r in self.results) else 0
        }
        
        overall_score = sum(readiness_factors.values()) / len(readiness_factors)
        
        if overall_score >= 95:
            readiness_level = "PRODUCTION_READY"
        elif overall_score >= 80:
            readiness_level = "ENTERPRISE_READY"
        elif overall_score >= 60:
            readiness_level = "DEVELOPMENT_READY"
        else:
            readiness_level = "NEEDS_WORK"
        
        return {
            "overall_score": overall_score,
            "readiness_level": readiness_level,
            "factors": readiness_factors
        }


def main():
    """Main test runner function"""
    
    suite = SimpleTestSuite()
    summary = suite.run_all_tests()
    
    # Save test results
    output_file = Path("test_results.json")
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Test results saved to: {output_file}")
    
    # Return exit code based on success
    if summary["failed_tests"] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
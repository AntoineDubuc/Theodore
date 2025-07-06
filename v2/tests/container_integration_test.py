#!/usr/bin/env python3
"""
Container Integration Test for Theodore v2
==========================================

Tests the container infrastructure with simplified setup
to validate the dependency injection framework.
"""

import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ContainerIntegrationTest:
    """Container integration test suite"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def run_container_tests(self) -> Dict[str, Any]:
        """Run container integration tests"""
        
        print("🏗️  Theodore v2 Container Integration Tests")
        print("=" * 50)
        print(f"📅 Started: {datetime.now(timezone.utc).isoformat()}")
        print()
        
        self.start_time = time.time()
        
        # Test container creation and basic functionality
        self._test_container_instantiation()
        self._test_provider_setup()
        self._test_configuration_system()
        self._test_container_factory()
        self._test_lifecycle_management()
        
        total_duration = time.time() - self.start_time
        
        # Generate summary
        summary = self._generate_summary(total_duration)
        
        print("\n" + "=" * 50)
        print("📊 CONTAINER TEST SUMMARY")
        print("=" * 50)
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"🏆 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL CONTAINER TESTS PASSED!")
        else:
            print("\n⚠️  Some container tests failed.")
            
        return summary
    
    def _test_container_instantiation(self):
        """Test basic container instantiation"""
        test_result = {"test_name": "Container Instantiation", "success": False, "duration": 0, "details": {}}
        start_time = time.time()
        
        try:
            print("🔧 Testing container instantiation...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            # Create container
            container = ApplicationContainer()
            print("  ✅ Container created successfully")
            
            # Test container metadata
            assert hasattr(container, '__version__'), "Container should have version"
            assert hasattr(container, '__name__'), "Container should have name"
            print("  ✅ Container metadata present")
            
            # Test container structure
            assert hasattr(container, 'config'), "Container should have config"
            assert hasattr(container, 'storage'), "Container should have storage"
            assert hasattr(container, 'ai_services'), "Container should have AI services"
            print("  ✅ Container structure validated")
            
            test_result["success"] = True
            test_result["details"]["version"] = getattr(container, '__version__', 'unknown')
            test_result["details"]["name"] = getattr(container, '__name__', 'unknown')
            print("  🎉 Container instantiation test PASSED")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"  ❌ Container instantiation test FAILED: {e}")
        
        test_result["duration"] = time.time() - start_time
        self.results.append(test_result)
    
    def _test_provider_setup(self):
        """Test provider setup and configuration"""
        test_result = {"test_name": "Provider Setup", "success": False, "duration": 0, "details": {}}
        start_time = time.time()
        
        try:
            print("\n⚙️  Testing provider setup...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            container = ApplicationContainer()
            
            # Test provider access
            providers = ["config", "storage", "ai_services", "mcp_search", "use_cases", "external_services"]
            available_providers = []
            
            for provider_name in providers:
                if hasattr(container, provider_name):
                    available_providers.append(provider_name)
                    print(f"  ✅ {provider_name} provider available")
                else:
                    print(f"  ⚠️  {provider_name} provider missing")
            
            # Test configuration provider
            config = container.config
            assert config is not None, "Config provider should not be None"
            print("  ✅ Configuration provider accessible")
            
            test_result["success"] = len(available_providers) >= 4  # At least 4 providers should be available
            test_result["details"]["available_providers"] = available_providers
            test_result["details"]["total_providers"] = len(providers)
            
            if test_result["success"]:
                print("  🎉 Provider setup test PASSED")
            else:
                print(f"  ❌ Provider setup test FAILED - Only {len(available_providers)}/{len(providers)} providers available")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"  ❌ Provider setup test FAILED: {e}")
        
        test_result["duration"] = time.time() - start_time
        self.results.append(test_result)
    
    def _test_configuration_system(self):
        """Test configuration system"""
        test_result = {"test_name": "Configuration System", "success": False, "duration": 0, "details": {}}
        start_time = time.time()
        
        try:
            print("\n📝 Testing configuration system...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            container = ApplicationContainer()
            
            # Test configuration provider
            config = container.config
            assert config is not None, "Configuration should be accessible"
            print("  ✅ Configuration provider accessible")
            
            # Test configuration type
            from dependency_injector.providers import Configuration
            assert isinstance(config, Configuration), "Config should be Configuration provider"
            print("  ✅ Configuration type validated")
            
            # Test basic configuration operations
            test_config = {"test_key": "test_value"}
            config.from_dict(test_config)
            print("  ✅ Configuration loading works")
            
            test_result["success"] = True
            test_result["details"]["config_type"] = str(type(config))
            print("  🎉 Configuration system test PASSED")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"  ❌ Configuration system test FAILED: {e}")
        
        test_result["duration"] = time.time() - start_time
        self.results.append(test_result)
    
    def _test_container_factory(self):
        """Test container factory functionality"""
        test_result = {"test_name": "Container Factory", "success": False, "duration": 0, "details": {}}
        start_time = time.time()
        
        try:
            print("\n🏭 Testing container factory...")
            
            from src.infrastructure.container import ContainerFactory, ContainerEnvironment, ContainerContext
            
            # Test factory import
            assert ContainerFactory is not None, "ContainerFactory should be importable"
            print("  ✅ ContainerFactory imported successfully")
            
            # Test environment and context enums
            assert ContainerEnvironment.CLI is not None, "CLI environment should exist"
            assert ContainerContext.CLI_APPLICATION is not None, "CLI context should exist"
            print("  ✅ Environment and context enums available")
            
            # Test basic factory methods exist
            assert hasattr(ContainerFactory, 'create_cli_container'), "Should have create_cli_container method"
            assert hasattr(ContainerFactory, 'create_container'), "Should have create_container method"
            print("  ✅ Factory methods available")
            
            test_result["success"] = True
            test_result["details"]["factory_available"] = True
            print("  🎉 Container factory test PASSED")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"  ❌ Container factory test FAILED: {e}")
        
        test_result["duration"] = time.time() - start_time
        self.results.append(test_result)
    
    def _test_lifecycle_management(self):
        """Test lifecycle management"""
        test_result = {"test_name": "Lifecycle Management", "success": False, "duration": 0, "details": {}}
        start_time = time.time()
        
        try:
            print("\n🔄 Testing lifecycle management...")
            
            from src.infrastructure.container.application import ApplicationContainer
            
            container = ApplicationContainer()
            
            # Test initialization
            container.init_resources()
            print("  ✅ Container initialization successful")
            
            # Test health check
            health_result = container.health_check()
            if hasattr(health_result, '__call__'):
                # It's a coroutine, we need to await it
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                health_data = loop.run_until_complete(health_result)
            else:
                health_data = health_result
            
            assert health_data is not None, "Health check should return data"
            print("  ✅ Health check functional")
            
            # Test shutdown
            shutdown_result = container.shutdown()
            if hasattr(shutdown_result, '__call__'):
                # It's a coroutine
                loop.run_until_complete(shutdown_result)
            print("  ✅ Container shutdown successful")
            
            test_result["success"] = True
            test_result["details"]["lifecycle_methods"] = ["init_resources", "health_check", "shutdown"]
            print("  🎉 Lifecycle management test PASSED")
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            print(f"  ❌ Lifecycle management test FAILED: {e}")
        
        test_result["duration"] = time.time() - start_time
        self.results.append(test_result)
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate test summary"""
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        return {
            "test_type": "Container_Integration",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed/total)*100 if total > 0 else 0,
            "total_duration_seconds": total_duration,
            "test_results": self.results,
            "container_architecture_score": self._calculate_architecture_score()
        }
    
    def _calculate_architecture_score(self) -> Dict[str, Any]:
        """Calculate container architecture score"""
        
        passed = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        score = (passed/total)*100 if total > 0 else 0
        
        if score >= 95:
            level = "PRODUCTION_READY"
        elif score >= 80:
            level = "ENTERPRISE_READY"
        elif score >= 60:
            level = "DEVELOPMENT_READY"
        else:
            level = "NEEDS_WORK"
        
        return {
            "score": score,
            "level": level,
            "tests_passed": passed,
            "tests_total": total,
            "architecture_quality": level
        }


def main():
    """Main container test function"""
    
    container_test = ContainerIntegrationTest()
    summary = container_test.run_container_tests()
    
    # Save results
    output_file = Path("container_test_results.json")
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Container test results saved to: {output_file}")
    
    # Return exit code based on success
    if summary["failed_tests"] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
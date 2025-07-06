#!/usr/bin/env python3
"""
Quick Theodore API Test - Skip Research Endpoint
Tests all endpoints except the long-running research endpoint
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TestStatus(Enum):
    SUCCESS = "✅ SUCCESS"
    FAILED = "❌ FAILED"
    TIMEOUT = "⏰ TIMEOUT"
    ERROR = "🔥 ERROR"
    SKIP = "⏭️ SKIPPED"

@dataclass
class TestResult:
    endpoint: str
    method: str
    status: TestStatus
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    human_readable: Optional[str] = None

class QuickEndpointTester:
    def __init__(self, base_url: str = "http://localhost:5002", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Theodore-Quick-Test/1.0'
        })
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None, description: str = "") -> TestResult:
        start_time = time.time()
        full_url = f"{self.base_url}{endpoint}"
        
        self.log(f"Testing {method} {endpoint} - {description}")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(full_url, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(full_url, json=data, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_text": response.text}
                
            status = TestStatus.SUCCESS if response.status_code < 400 else TestStatus.FAILED
            
            human_readable = f"✅ Success - {response.status_code}" if status == TestStatus.SUCCESS else f"❌ Failed - {response.status_code}"
            
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=status,
                response_time=response_time,
                status_code=response.status_code,
                human_readable=human_readable
            )
            
        except requests.exceptions.Timeout:
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=TestStatus.TIMEOUT,
                response_time=self.timeout,
                error_message="Request timed out"
            )
        except Exception as e:
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=TestStatus.ERROR,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def run_quick_tests(self):
        """Run quick tests excluding research endpoint"""
        self.log("🚀 Starting Quick Theodore API Testing (excluding research)")
        
        # System Health Tests
        tests = [
            ("GET", "/", None, None, "API Root"),
            ("GET", "/api/health", None, None, "Health Check"),
            ("GET", "/api/diagnostic", None, None, "System Diagnostic"),
            ("GET", "/ping", None, None, "Ping Test"),
            
            # Research Progress (not the main research endpoint)
            ("GET", "/api/research/progress", None, None, "Research Progress"),
            ("GET", "/api/research/prompts/available", None, None, "Available Prompts"),
            ("POST", "/api/research/prompts/estimate", {"selected_prompts": ["industry_analysis"]}, None, "Estimate Cost"),
            ("GET", "/api/research/structured/sessions", None, None, "Research Sessions"),
            
            # Discovery Tests
            ("POST", "/api/discover", {"company_name": "Salesforce", "limit": 3}, None, "Company Discovery"),
            ("POST", "/api/test-discovery", {"company_name": "Salesforce"}, None, "Test Discovery"),
            ("GET", "/api/search", None, {"q": "apple"}, "Company Search"),
            
            # Database Tests
            ("GET", "/api/database", None, None, "Browse Database"),
            ("GET", "/api/companies", None, None, "List Companies"),
            ("GET", "/api/companies/details", None, {"company_id": "1"}, "Company Details"),
            ("POST", "/api/database/add-sample", {}, None, "Add Sample Companies"),
            
            # Progress Tests (quick ones)
            ("GET", "/api/progress/current", None, None, "Current Progress"),
            ("GET", "/api/progress/all", None, None, "All Progress"),
            
            # Classification Tests
            ("GET", "/api/classification/stats", None, None, "Classification Stats"),
            ("GET", "/api/classification/categories", None, None, "Classification Categories"),
            ("GET", "/api/classification/unclassified", None, None, "Unclassified Companies"),
            
            # Settings Tests
            ("GET", "/api/settings", None, None, "Get Settings"),
            ("POST", "/api/settings/health-check", {}, None, "Settings Health Check"),
            ("POST", "/api/settings/test-models", {}, None, "Test AI Models"),
            
            # Field Metrics Tests
            ("GET", "/api/field-metrics/summary", None, None, "Field Metrics Summary"),
            ("GET", "/api/field-metrics/export", None, None, "Export Field Metrics"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
        
        self.log("✅ Quick tests completed!")
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.status == TestStatus.SUCCESS])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR])
        timeout_tests = len([r for r in self.results if r.status == TestStatus.TIMEOUT])
        
        print("\n" + "="*60)
        print("🎉 Quick API Test Results Summary")
        print("="*60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"⏰ Timeouts: {timeout_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0 or error_tests > 0 or timeout_tests > 0:
            print("\n❌ Issues Found:")
            for result in self.results:
                if result.status != TestStatus.SUCCESS:
                    print(f"  • {result.endpoint} ({result.method}): {result.status.value}")
                    if result.error_message:
                        print(f"    └─ {result.error_message}")
        
        print("\n✅ All originally failing endpoints from previous report:")
        key_endpoints = ["/ping", "/api/research/progress", "/api/research/prompts/available", 
                        "/api/research/prompts/estimate", "/api/research/structured/sessions", "/api/test-discovery"]
        
        for endpoint in key_endpoints:
            result = next((r for r in self.results if r.endpoint == endpoint), None)
            if result:
                print(f"  • {endpoint}: {result.status.value}")
            else:
                print(f"  • {endpoint}: Not tested")

def main():
    print("🚀 Theodore Quick API Test Suite")
    print("=" * 50)
    
    # Check if Theodore is running
    try:
        response = requests.get("http://localhost:5002/ping", timeout=5)
        print("✅ Theodore API is running")
    except:
        print("❌ Theodore API is not running")
        return
    
    # Run tests
    tester = QuickEndpointTester()
    tester.run_quick_tests()
    tester.generate_summary()

if __name__ == "__main__":
    main()
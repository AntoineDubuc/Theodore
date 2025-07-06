#!/usr/bin/env python3
"""
Comprehensive Theodore API Endpoint Testing Script

This script tests all available Theodore API endpoints and generates a detailed
markdown report with results, response times, and human-readable summaries.
"""

import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os
from pathlib import Path

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
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    human_readable: Optional[str] = None
    raw_response: Optional[str] = None
    request_command: Optional[str] = None
    request_data: Optional[Dict] = None
    request_params: Optional[Dict] = None
    full_url: Optional[str] = None

class TheodoreEndpointTester:
    """Comprehensive endpoint testing class"""
    
    def __init__(self, base_url: str = "http://localhost:5002", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Theodore-Test-Suite/1.0'
        })
        self.results: List[TestResult] = []
        self.test_companies = [
            "Apple Inc",
            "Salesforce",
            "Microsoft",
            "Google",
            "Amazon"
        ]
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None, description: str = "", custom_timeout: Optional[int] = None) -> TestResult:
        """Test a single endpoint"""
        start_time = time.time()
        full_url = f"{self.base_url}{endpoint}"
        
        # Determine timeout for this endpoint
        endpoint_timeout = custom_timeout if custom_timeout else self.timeout
        
        # Use extended timeout for research and long-running endpoints
        if any(pattern in endpoint for pattern in ['/api/research', '/api/progress', '/api/cancel-current-job']):
            endpoint_timeout = 300  # 5 minutes for research operations
        
        # Generate curl command for documentation
        curl_command = self._generate_curl_command(method, full_url, data, params)
        
        self.log(f"Testing {method} {endpoint} - {description} (timeout: {endpoint_timeout}s)")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(full_url, params=params, timeout=endpoint_timeout)
            elif method.upper() == "POST":
                response = self.session.post(full_url, json=data, params=params, timeout=endpoint_timeout)
            elif method.upper() == "PUT":
                response = self.session.put(full_url, json=data, params=params, timeout=endpoint_timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(full_url, params=params, timeout=endpoint_timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response_time = time.time() - start_time
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_text": response.text}
                
            # Generate human-readable summary
            human_readable = self._generate_human_readable(endpoint, response_data, response.status_code)
            
            status = TestStatus.SUCCESS if response.status_code < 400 else TestStatus.FAILED
            
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=status,
                response_time=response_time,
                status_code=response.status_code,
                response_data=response_data,
                human_readable=human_readable,
                raw_response=response.text[:2000] if response.text else None,
                request_command=curl_command,
                request_data=data,
                request_params=params,
                full_url=full_url
            )
            
        except requests.exceptions.Timeout:
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=TestStatus.TIMEOUT,
                response_time=endpoint_timeout,
                error_message=f"Request timed out after {endpoint_timeout}s",
                request_command=curl_command,
                request_data=data,
                request_params=params,
                full_url=full_url
            )
        except Exception as e:
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=TestStatus.ERROR,
                response_time=time.time() - start_time,
                error_message=str(e),
                request_command=curl_command,
                request_data=data,
                request_params=params,
                full_url=full_url
            )
    
    def _generate_human_readable(self, endpoint: str, response_data: Dict, status_code: int) -> str:
        """Generate human-readable summary of the response"""
        if status_code >= 400:
            return f"❌ Failed with status {status_code}: {response_data.get('error', 'Unknown error')}"
        
        if endpoint == "/" or endpoint == "/api/health":
            return f"✅ System is healthy and responding"
        elif "/research" in endpoint:
            if "company_name" in str(response_data):
                return f"✅ Research initiated or completed for company"
            elif "prompts" in str(response_data):
                return f"✅ Research prompts available: {len(response_data.get('prompts', []))}"
            else:
                return f"✅ Research endpoint responded successfully"
        elif "/discover" in endpoint:
            similar_count = len(response_data.get('similar_companies', []))
            return f"✅ Discovery found {similar_count} similar companies"
        elif "/database" in endpoint:
            total_companies = response_data.get('total', 0)
            return f"✅ Database contains {total_companies} companies"
        elif "/search" in endpoint:
            suggestions = len(response_data.get('suggestions', []))
            return f"✅ Search returned {suggestions} suggestions"
        elif "/progress" in endpoint:
            if response_data.get('status'):
                return f"✅ Progress status: {response_data.get('status')}"
            else:
                return f"✅ Progress tracking is active"
        elif "/settings" in endpoint:
            return f"✅ Settings endpoint accessible"
        elif "/classification" in endpoint:
            return f"✅ Classification system operational"
        else:
            return f"✅ Endpoint responded successfully"
    
    def _generate_curl_command(self, method: str, url: str, data: Optional[Dict] = None, 
                              params: Optional[Dict] = None) -> str:
        """Generate curl command equivalent for the request"""
        cmd_parts = ["curl", "-X", method.upper()]
        
        # Add headers
        cmd_parts.extend(["-H", "'Content-Type: application/json'"])
        cmd_parts.extend(["-H", "'User-Agent: Theodore-Test-Suite/1.0'"])
        
        # Add data for POST/PUT requests
        if data and method.upper() in ["POST", "PUT"]:
            data_str = json.dumps(data, separators=(',', ':'))
            cmd_parts.extend(["-d", f"'{data_str}'"])
        
        # Add URL (with params if any)
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{param_str}"
        
        cmd_parts.append(f"'{url}'")
        
        return " ".join(cmd_parts)
    
    def run_system_health_tests(self):
        """Test system health endpoints"""
        self.log("🔍 Testing System Health Endpoints", "INFO")
        
        tests = [
            ("GET", "/", None, None, "API Root"),
            ("GET", "/api/health", None, None, "Health Check"),
            ("GET", "/api/diagnostic", None, None, "System Diagnostic"),
            ("GET", "/ping", None, None, "Ping Test"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_research_tests(self):
        """Test research endpoints"""
        self.log("🔬 Testing Research Endpoints", "INFO")
        
        # Test basic research with real website
        research_data = {
            "company": {
                "name": "ApniMed",
                "website": "https://www.apnimed.com"
            }
        }
        
        tests = [
            ("POST", "/api/research", research_data, None, "Start Company Research"),
            ("GET", "/api/research/progress", None, None, "Get Research Progress"),
            ("GET", "/api/research/prompts/available", None, None, "Get Available Prompts"),
            ("POST", "/api/research/prompts/estimate", 
             {"selected_prompts": ["industry_analysis"]}, None, "Estimate Research Cost"),
            ("GET", "/api/research/structured/sessions", None, None, "List Research Sessions"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_discovery_tests(self):
        """Test discovery endpoints"""
        self.log("🔍 Testing Discovery Endpoints", "INFO")
        
        test_company = self.test_companies[1]
        discovery_data = {"company_name": test_company, "limit": 5}
        
        tests = [
            ("POST", "/api/discover", discovery_data, None, "Company Discovery"),
            ("POST", "/api/test-discovery", {"company_name": test_company}, None, "Test Discovery"),
            ("GET", "/api/search", None, {"q": "apple"}, "Company Search"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_database_tests(self):
        """Test database endpoints"""
        self.log("🗄️ Testing Database Endpoints", "INFO")
        
        tests = [
            ("GET", "/api/database", None, None, "Browse Database"),
            ("GET", "/api/companies", None, None, "List Companies"),
            ("GET", "/api/companies/details", None, {"company_id": "1"}, "Get Company Details"),
            ("POST", "/api/database/add-sample", {}, None, "Add Sample Companies"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_progress_tests(self):
        """Test progress tracking endpoints"""
        self.log("📊 Testing Progress Endpoints", "INFO")
        
        tests = [
            ("GET", "/api/progress/current", None, None, "Current Progress"),
            ("GET", "/api/progress/all", None, None, "All Progress Data"),
            ("POST", "/api/cancel-current-job", {}, None, "Cancel Current Job"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_classification_tests(self):
        """Test classification endpoints"""
        self.log("🏷️ Testing Classification Endpoints", "INFO")
        
        tests = [
            ("GET", "/api/classification/stats", None, None, "Classification Stats"),
            ("GET", "/api/classification/categories", None, None, "Classification Categories"),
            ("GET", "/api/classification/unclassified", None, None, "Unclassified Companies"),
            ("POST", "/api/classify-unknown-industries", {}, None, "Classify Unknown Industries"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_settings_tests(self):
        """Test settings endpoints"""
        self.log("⚙️ Testing Settings Endpoints", "INFO")
        
        tests = [
            ("GET", "/api/settings", None, None, "Get Settings"),
            ("POST", "/api/settings/health-check", {}, None, "Settings Health Check"),
            ("POST", "/api/settings/test-models", {}, None, "Test AI Models"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_field_metrics_tests(self):
        """Test field metrics endpoints"""
        self.log("📈 Testing Field Metrics Endpoints", "INFO")
        
        tests = [
            ("GET", "/api/field-metrics/summary", None, None, "Field Metrics Summary"),
            ("GET", "/api/field-metrics/export", None, None, "Export Field Metrics"),
        ]
        
        for method, endpoint, data, params, desc in tests:
            result = self.test_endpoint(method, endpoint, data, params, desc)
            self.results.append(result)
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        self.log("🚀 Starting Comprehensive Theodore API Testing", "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log(f"Timeout: {self.timeout}s", "INFO")
        
        # Run test suites
        self.run_system_health_tests()
        self.run_research_tests()
        self.run_discovery_tests()
        self.run_database_tests()
        self.run_progress_tests()
        self.run_classification_tests()
        self.run_settings_tests()
        self.run_field_metrics_tests()
        
        self.log("✅ All tests completed!", "INFO")
    
    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.status == TestStatus.SUCCESS])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR])
        timeout_tests = len([r for r in self.results if r.status == TestStatus.TIMEOUT])
        
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results) if self.results else 0
        
        report = f"""# Theodore API Comprehensive Test Report

## 📊 Executive Summary

**Test Run Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Tests:** {total_tests}  
**Success Rate:** {(successful_tests/total_tests)*100:.1f}%  
**Average Response Time:** {avg_response_time:.2f}s  

### Test Results Overview

- ✅ **Successful:** {successful_tests} tests
- ❌ **Failed:** {failed_tests} tests  
- 🔥 **Errors:** {error_tests} tests
- ⏰ **Timeouts:** {timeout_tests} tests

### Performance Metrics

- **Fastest Response:** {min(r.response_time for r in self.results):.3f}s
- **Slowest Response:** {max(r.response_time for r in self.results):.3f}s
- **Total Test Duration:** {(datetime.now() - self.start_time).total_seconds():.1f}s

---

## 🔍 Detailed Test Results

"""
        
        # Group results by category
        categories = {
            "System Health": ["/", "/api/health", "/api/diagnostic", "/ping"],
            "Research": ["/api/research", "/api/research/progress", "/api/research/prompts", "/api/research/structured"],
            "Discovery": ["/api/discover", "/api/test-discovery", "/api/search"],
            "Database": ["/api/database", "/api/companies"],
            "Progress": ["/api/progress"],
            "Classification": ["/api/classification"],
            "Settings": ["/api/settings"],
            "Field Metrics": ["/api/field-metrics"]
        }
        
        for category, endpoints in categories.items():
            report += f"### {category}\n\n"
            
            category_results = []
            for result in self.results:
                if any(ep in result.endpoint for ep in endpoints):
                    category_results.append(result)
            
            if category_results:
                # Summary table
                report += "| Endpoint | Method | Status | Response Time | Human Readable |\n"
                report += "|----------|--------|--------|---------------|----------------|\n"
                
                for result in category_results:
                    report += f"| `{result.endpoint}` | {result.method} | {result.status.value} | {result.response_time:.3f}s | {result.human_readable or 'N/A'} |\n"
                
                report += "\n"
                
                # Detailed results
                for result in category_results:
                    report += f"#### {result.method} {result.endpoint}\n\n"
                    report += f"**Status:** {result.status.value}  \n"
                    report += f"**Response Time:** {result.response_time:.3f}s  \n"
                    
                    if result.status_code:
                        report += f"**HTTP Status Code:** {result.status_code}  \n"
                    
                    if result.human_readable:
                        report += f"**Summary:** {result.human_readable}  \n"
                    
                    if result.error_message:
                        report += f"**Error:** {result.error_message}  \n"
                    
                    # Add command information
                    report += "\n**Request Details:**\n"
                    if result.request_command:
                        report += f"**Curl Command:**\n```bash\n{result.request_command}\n```\n\n"
                    
                    if result.full_url:
                        report += f"**Full URL:** `{result.full_url}`  \n"
                    
                    if result.request_data:
                        report += f"**Request Data:**\n```json\n{json.dumps(result.request_data, indent=2)}\n```\n\n"
                    
                    if result.request_params:
                        report += f"**Request Parameters:**\n```json\n{json.dumps(result.request_params, indent=2)}\n```\n\n"
                    
                    report += "**Raw Response:**\n"
                    report += "```json\n"
                    if result.response_data:
                        report += json.dumps(result.response_data, indent=2)
                    elif result.raw_response:
                        report += result.raw_response
                    else:
                        report += "No response data"
                    report += "\n```\n\n"
                    
                    report += "---\n\n"
            else:
                report += "*No test results found for this category.*\n\n"
        
        # Add recommendations
        report += """## 🎯 Recommendations

### System Performance
"""
        
        if avg_response_time > 5.0:
            report += "- ⚠️ **High Response Times:** Average response time is above 5 seconds. Consider performance optimization.\n"
        else:
            report += "- ✅ **Good Performance:** Response times are within acceptable limits.\n"
        
        if failed_tests > 0:
            report += f"- ⚠️ **Failed Tests:** {failed_tests} tests failed. Review error messages and fix issues.\n"
        else:
            report += "- ✅ **All Tests Passing:** No failed tests detected.\n"
        
        if error_tests > 0:
            report += f"- 🔥 **Error Tests:** {error_tests} tests encountered errors. Check system logs.\n"
        
        if timeout_tests > 0:
            report += f"- ⏰ **Timeout Issues:** {timeout_tests} tests timed out. Consider increasing timeout or optimizing endpoints.\n"
        
        report += """
### Next Steps

1. **Review Failed Tests:** Address any failing endpoints
2. **Performance Optimization:** Focus on slow-responding endpoints
3. **Error Handling:** Improve error responses and logging
4. **Documentation:** Update API documentation based on test results
5. **Monitoring:** Set up continuous monitoring for critical endpoints

---

*Report generated by Theodore API Test Suite*  
*For questions or issues, check the system logs and API documentation*
"""
        
        return report
    
    def save_report(self, filename: str = None):
        """Save the markdown report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"theodore_api_test_report_{timestamp}.md"
        
        report = self.generate_markdown_report()
        
        with open(filename, 'w') as f:
            f.write(report)
        
        self.log(f"📄 Report saved to: {filename}", "INFO")
        return filename

def main():
    """Main test runner"""
    print("🚀 Theodore API Comprehensive Testing Suite")
    print("=" * 50)
    
    # Check if Theodore is running
    try:
        response = requests.get("http://localhost:5002/ping", timeout=5)
        print("✅ Theodore API is running")
    except:
        print("❌ Theodore API is not running. Please start it first:")
        print("   cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore")
        print("   python3 app.py")
        return
    
    # Run tests
    tester = TheodoreEndpointTester()
    tester.run_all_tests()
    
    # Generate and save report
    filename = tester.save_report()
    
    print("\n" + "=" * 50)
    print("🎉 Testing Complete!")
    print(f"📊 Total Tests: {len(tester.results)}")
    print(f"✅ Successful: {len([r for r in tester.results if r.status == TestStatus.SUCCESS])}")
    print(f"❌ Failed: {len([r for r in tester.results if r.status == TestStatus.FAILED])}")
    print(f"📄 Report: {filename}")

if __name__ == "__main__":
    main()
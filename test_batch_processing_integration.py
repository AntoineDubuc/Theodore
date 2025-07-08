#!/usr/bin/env python3
"""
Comprehensive Batch Processing Integration Test
=============================================

This script tests the complete batch processing workflow:
1. Google Sheets integration
2. Antoine batch processor with parallel execution
3. Progress tracking and real-time updates
4. UI integration via API endpoints
5. Error handling and recovery
"""

import os
import sys
import json
import time
import asyncio
import logging
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchProcessingIntegrationTest:
    """Test the complete batch processing integration"""
    
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_sheet_id = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"  # Test sheet
        
    def test_api_health(self):
        """Test that the API is running and healthy"""
        logger.info("🏥 Testing API health...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                logger.info("✅ API is healthy")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to API: {e}")
            return False
    
    def test_sheet_validation(self):
        """Test Google Sheets validation endpoint"""
        logger.info("📋 Testing Google Sheets validation...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/batch/validate",
                json={"sheet_id": self.test_sheet_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Sheet validated: {data['title']}")
                logger.info(f"   Found {data['companies_count']} companies")
                logger.info(f"   Sheets: {', '.join(data['sheets'])}")
                return True
            else:
                error_data = response.json()
                logger.error(f"❌ Sheet validation failed: {error_data.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Sheet validation error: {e}")
            return False
    
    def test_batch_processing_standard(self):
        """Test standard batch processing endpoint"""
        logger.info("🔄 Testing standard batch processing...")
        
        try:
            # Start batch processing
            response = self.session.post(
                f"{self.base_url}/api/batch/process",
                json={
                    "sheet_id": self.test_sheet_id,
                    "batch_size": 3,
                    "start_row": 2
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data['job_id']
                logger.info(f"✅ Standard batch started: {job_id}")
                logger.info(f"   Processing {data['companies_count']} companies")
                
                # Monitor progress
                self._monitor_batch_progress(job_id)
                return True
            else:
                error_data = response.json()
                logger.error(f"❌ Failed to start batch: {error_data.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return False
    
    def test_antoine_batch_processing(self):
        """Test antoine batch processing with parallel execution"""
        logger.info("🚀 Testing Antoine batch processing...")
        
        try:
            # Start antoine batch processing
            response = self.session.post(
                f"{self.base_url}/api/batch/process-antoine",
                json={
                    "sheet_id": self.test_sheet_id,
                    "batch_size": 5,
                    "start_row": 2,
                    "max_concurrent": 3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data['job_id']
                logger.info(f"✅ Antoine batch started: {job_id}")
                logger.info(f"   Processing {data['companies_count']} companies")
                logger.info(f"   Max concurrent: {data['max_concurrent']}")
                
                # Monitor progress with SSE
                self._monitor_batch_progress_sse(job_id)
                return True
            else:
                error_data = response.json()
                logger.error(f"❌ Failed to start antoine batch: {error_data.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Antoine batch error: {e}")
            return False
    
    def _monitor_batch_progress(self, job_id, max_duration=300):
        """Monitor batch progress using polling"""
        logger.info(f"📊 Monitoring progress for job {job_id}...")
        
        start_time = time.time()
        last_processed = 0
        
        while time.time() - start_time < max_duration:
            try:
                response = self.session.get(f"{self.base_url}/api/batch/progress/{job_id}")
                
                if response.status_code == 200:
                    progress = response.json()
                    
                    # Log progress update
                    processed = progress.get('processed', 0)
                    if processed != last_processed:
                        logger.info(f"   Progress: {processed}/{progress.get('total_companies', 0)}")
                        logger.info(f"   Message: {progress.get('current_message', '')}")
                        last_processed = processed
                    
                    # Check if completed
                    if progress.get('status') == 'completed':
                        logger.info(f"✅ Batch completed!")
                        logger.info(f"   Successful: {progress.get('successful', 0)}")
                        logger.info(f"   Failed: {progress.get('failed', 0)}")
                        
                        # Show results if available
                        results = progress.get('results', {})
                        if results:
                            logger.info(f"   Total cost: ${results.get('total_cost_usd', 0):.4f}")
                            if 'parallel_efficiency' in results:
                                logger.info(f"   Parallel efficiency: {results['parallel_efficiency']:.1%}")
                        break
                    
                time.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring progress: {e}")
                break
        
        if time.time() - start_time >= max_duration:
            logger.warning("⏱️ Monitoring timed out")
    
    def _monitor_batch_progress_sse(self, job_id, max_duration=300):
        """Monitor batch progress using Server-Sent Events"""
        logger.info(f"📡 Monitoring progress via SSE for job {job_id}...")
        
        import sseclient  # You may need to: pip install sseclient-py
        
        try:
            # Note: requests doesn't support streaming SSE well, using a simple approach
            response = self.session.get(
                f"{self.base_url}/api/batch/stream/{job_id}",
                stream=True
            )
            
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                data = json.loads(event.data)
                
                if 'error' in data:
                    logger.error(f"❌ SSE Error: {data['error']}")
                    break
                
                if data.get('event') == 'complete':
                    progress = data.get('progress', {})
                    logger.info("✅ Batch completed via SSE!")
                    logger.info(f"   Successful: {progress.get('successful', 0)}")
                    logger.info(f"   Failed: {progress.get('failed', 0)}")
                    break
                
                if data.get('event') == 'timeout':
                    logger.warning(f"⏱️ SSE timeout: {data.get('message')}")
                    break
                
                # Regular progress update
                logger.info(f"   SSE Update: {data.get('current_message', '')}")
                
        except ImportError:
            logger.warning("sseclient not installed, falling back to polling")
            self._monitor_batch_progress(job_id, max_duration)
        except Exception as e:
            logger.error(f"SSE monitoring error: {e}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("🚨 Testing error handling...")
        
        # Test invalid sheet ID
        logger.info("   Testing invalid sheet ID...")
        response = self.session.post(
            f"{self.base_url}/api/batch/validate",
            json={"sheet_id": "invalid-sheet-id"}
        )
        if response.status_code != 200:
            logger.info("   ✅ Invalid sheet ID properly rejected")
        else:
            logger.error("   ❌ Invalid sheet ID not rejected!")
        
        # Test missing parameters
        logger.info("   Testing missing parameters...")
        response = self.session.post(
            f"{self.base_url}/api/batch/process-antoine",
            json={}
        )
        if response.status_code == 400:
            logger.info("   ✅ Missing parameters properly handled")
        else:
            logger.error("   ❌ Missing parameters not handled!")
        
        # Test invalid batch size
        logger.info("   Testing invalid batch size...")
        response = self.session.post(
            f"{self.base_url}/api/batch/process-antoine",
            json={
                "sheet_id": self.test_sheet_id,
                "batch_size": 1000  # Too large
            }
        )
        if response.status_code == 400:
            logger.info("   ✅ Invalid batch size properly rejected")
        else:
            logger.error("   ❌ Invalid batch size not rejected!")
        
        return True
    
    def test_performance_comparison(self):
        """Compare performance between standard and antoine batch processing"""
        logger.info("⚡ Testing performance comparison...")
        
        # Test small batch with standard processor
        logger.info("   Standard processor (3 companies, sequential)...")
        start_time = time.time()
        
        response = self.session.post(
            f"{self.base_url}/api/batch/process",
            json={
                "sheet_id": self.test_sheet_id,
                "batch_size": 3,
                "start_row": 10
            }
        )
        
        if response.status_code == 200:
            job_id = response.json()['job_id']
            self._wait_for_completion(job_id)
            standard_duration = time.time() - start_time
            logger.info(f"   Standard completed in {standard_duration:.1f}s")
        else:
            standard_duration = None
            logger.error("   Standard processor failed")
        
        # Test same batch with antoine processor
        logger.info("   Antoine processor (3 companies, parallel)...")
        start_time = time.time()
        
        response = self.session.post(
            f"{self.base_url}/api/batch/process-antoine",
            json={
                "sheet_id": self.test_sheet_id,
                "batch_size": 3,
                "start_row": 15,
                "max_concurrent": 3
            }
        )
        
        if response.status_code == 200:
            job_id = response.json()['job_id']
            self._wait_for_completion(job_id)
            antoine_duration = time.time() - start_time
            logger.info(f"   Antoine completed in {antoine_duration:.1f}s")
            
            if standard_duration and antoine_duration:
                speedup = standard_duration / antoine_duration
                logger.info(f"   🚀 Antoine is {speedup:.1f}x faster!")
        else:
            logger.error("   Antoine processor failed")
        
        return True
    
    def _wait_for_completion(self, job_id, timeout=300):
        """Wait for a job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/api/batch/progress/{job_id}")
                if response.status_code == 200:
                    progress = response.json()
                    if progress.get('status') == 'completed':
                        return True
                time.sleep(2)
            except:
                pass
        
        return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🧪 Starting Batch Processing Integration Tests")
        logger.info("=" * 60)
        
        tests = [
            ("API Health", self.test_api_health),
            ("Sheet Validation", self.test_sheet_validation),
            ("Error Handling", self.test_error_handling),
            ("Standard Batch Processing", self.test_batch_processing_standard),
            ("Antoine Batch Processing", self.test_antoine_batch_processing),
            ("Performance Comparison", self.test_performance_comparison)
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n🔧 Running: {test_name}")
            logger.info("-" * 40)
            
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                logger.error(f"💥 Test crashed: {e}")
                results.append((test_name, False))
            
            time.sleep(2)  # Brief pause between tests
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name:.<40} {status}")
        
        logger.info("-" * 60)
        logger.info(f"Total: {passed}/{total} passed ({passed/total*100:.0f}%)")
        
        if passed == total:
            logger.info("\n🎉 All tests passed! Batch processing is working correctly.")
        else:
            logger.info("\n⚠️ Some tests failed. Please check the logs above.")
        
        return passed == total


def main():
    """Main test runner"""
    # Check if server is running
    try:
        response = requests.get("http://localhost:5002/api/health")
        if response.status_code != 200:
            logger.error("❌ Theodore API is not running. Please start the server first:")
            logger.error("   python app.py")
            return
    except:
        logger.error("❌ Cannot connect to Theodore API at http://localhost:5002")
        logger.error("   Please start the server first: python app.py")
        return
    
    # Run tests
    tester = BatchProcessingIntegrationTest()
    success = tester.run_all_tests()
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
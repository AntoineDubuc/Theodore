#!/usr/bin/env python3
"""
Test Antoine Web Integration
============================

Test suite to verify if fixing AntoineScraperAdapter phase names and progress tracking
can resolve web application integration issues without breaking the working antoine pipeline.

This test validates Option 1: Fix AntoineScraperAdapter for web compatibility.
"""

import sys
import os
import time
import threading
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

from src.models import CompanyData, CompanyIntelligenceConfig
from src.progress_logger import start_company_processing, progress_logger, log_processing_phase


class TestAntoineWebIntegration:
    """Test suite for antoine web application integration"""
    
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
        self.progress_updates = []
        self.phase_counts = {}
        
    def capture_progress_updates(self, job_id: str):
        """Capture progress updates for analysis"""
        for i in range(20):  # Monitor for 20 cycles (40 seconds)
            try:
                progress = progress_logger.get_progress(job_id)
                if progress and 'phases' in progress:
                    for phase in progress['phases']:
                        phase_key = f"{phase['name']}_{phase['status']}"
                        self.phase_counts[phase_key] = self.phase_counts.get(phase_key, 0) + 1
                        self.progress_updates.append({
                            'timestamp': time.time(),
                            'phase': phase['name'],
                            'status': phase['status'],
                            'cycle': i
                        })
                time.sleep(2)  # Match UI polling interval
            except Exception as e:
                print(f"⚠️ Progress monitoring error: {e}")
                break
    
    def test_corrected_phase_names(self):
        """Test AntoineScraperAdapter with corrected phase names"""
        print("\n" + "="*80)
        print("TEST 1: CORRECTED PHASE NAMES")
        print("="*80)
        
        # Expected phase names that match UI
        expected_phases = [
            "Link Discovery",
            "LLM Page Selection", 
            "Content Extraction",
            "Social Media Research",
            "Sales Intelligence Generation"
        ]
        
        print(f"🎯 Expected phases: {expected_phases}")
        
        # Create test company
        company = CompanyData(name="Stripe Test", website="https://stripe.com")
        
        # Start job with progress tracking (like web app does)
        job_id = start_company_processing(company.name)
        print(f"📋 Started job: {job_id}")
        
        # Start progress monitoring in background
        monitor_thread = threading.Thread(
            target=self.capture_progress_updates, 
            args=(job_id,),
            daemon=True
        )
        monitor_thread.start()
        
        try:
            # Import the actual antoine adapter
            from src.antoine_scraper_adapter import AntoineScraperAdapter
            
            # Create adapter instance (like main_pipeline does)
            adapter = AntoineScraperAdapter(self.config)
            
            print(f"🚀 Starting scraping with progress tracking...")
            start_time = time.time()
            
            # Call with job_id (like web app does)
            result = adapter.scrape_company(company, job_id=job_id)
            
            elapsed = time.time() - start_time
            print(f"⏱️ Completed in {elapsed:.1f}s")
            print(f"📊 Status: {result.scrape_status}")
            
            # Wait for monitoring to capture a few cycles
            time.sleep(8)
            
            # Analyze results
            print(f"\n📈 PROGRESS ANALYSIS:")
            print(f"   Total updates captured: {len(self.progress_updates)}")
            print(f"   Phase occurrence counts: {self.phase_counts}")
            
            # Check for repetitive logging (the main issue)
            repetitive_issues = []
            for phase_status, count in self.phase_counts.items():
                if count > 3:  # More than 3 occurrences suggests repetition
                    repetitive_issues.append(f"{phase_status}: {count} times")
            
            if repetitive_issues:
                print(f"❌ REPETITIVE LOGGING DETECTED:")
                for issue in repetitive_issues:
                    print(f"   - {issue}")
                return False
            else:
                print(f"✅ No repetitive logging detected")
            
            # Check if expected phases were used
            actual_phases = set()
            for update in self.progress_updates:
                actual_phases.add(update['phase'])
            
            print(f"📋 Actual phases used: {sorted(actual_phases)}")
            
            missing_phases = set(expected_phases) - actual_phases
            extra_phases = actual_phases - set(expected_phases)
            
            if missing_phases:
                print(f"❌ Missing expected phases: {missing_phases}")
                return False
            
            if extra_phases:
                print(f"⚠️ Unexpected phases: {extra_phases}")
            
            print(f"✅ Phase names test passed")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_social_media_integration(self):
        """Test that social media extraction is included"""
        print("\n" + "="*80)
        print("TEST 2: SOCIAL MEDIA INTEGRATION")
        print("="*80)
        
        try:
            from src.antoine_scraper_adapter import AntoineScraperAdapter
            
            # Test with a company known to have social media links
            company = CompanyData(name="Stripe Social Test", website="https://stripe.com")
            adapter = AntoineScraperAdapter(self.config)
            
            print(f"🔍 Testing social media extraction for {company.name}")
            
            # Run without job_id to avoid progress tracking noise
            result = adapter.scrape_company(company)
            
            print(f"📊 Scrape status: {result.scrape_status}")
            
            # Check if social media was extracted
            if hasattr(result, 'social_media') and result.social_media:
                print(f"✅ Social media extracted: {result.social_media}")
                return True
            else:
                print(f"⚠️ No social media data found")
                print(f"   Available fields: {[attr for attr in dir(result) if not attr.startswith('_')]}")
                return False
                
        except Exception as e:
            print(f"❌ Social media test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_progress_tracking_stability(self):
        """Test that progress tracking doesn't cause instability"""
        print("\n" + "="*80)
        print("TEST 3: PROGRESS TRACKING STABILITY")
        print("="*80)
        
        try:
            from src.antoine_scraper_adapter import AntoineScraperAdapter
            
            # Test with a simpler site for faster execution
            company = CompanyData(name="Linear Stability Test", website="https://linear.app")
            job_id = start_company_processing(company.name)
            
            adapter = AntoineScraperAdapter(self.config)
            
            print(f"🔬 Testing progress stability...")
            
            # Clear previous test data
            self.progress_updates = []
            self.phase_counts = {}
            
            # Start monitoring
            monitor_thread = threading.Thread(
                target=self.capture_progress_updates,
                args=(job_id,),
                daemon=True
            )
            monitor_thread.start()
            
            # Execute
            start_time = time.time()
            result = adapter.scrape_company(company, job_id=job_id)
            elapsed = time.time() - start_time
            
            # Let monitoring continue for a bit
            time.sleep(6)
            
            print(f"⏱️ Execution time: {elapsed:.1f}s")
            print(f"📊 Final status: {result.scrape_status}")
            
            # Check for stability issues
            if len(self.progress_updates) > 50:  # Too many updates suggests instability
                print(f"❌ Too many progress updates: {len(self.progress_updates)}")
                return False
            
            # Check for error patterns
            error_updates = [u for u in self.progress_updates if 'error' in u.get('status', '').lower()]
            if error_updates:
                print(f"❌ Error updates detected: {error_updates}")
                return False
            
            print(f"✅ Progress tracking stability test passed")
            return True
            
        except Exception as e:
            print(f"❌ Stability test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_compatibility_with_working_code(self):
        """Test that changes don't break working antoine functionality"""
        print("\n" + "="*80)
        print("TEST 4: COMPATIBILITY WITH WORKING CODE")
        print("="*80)
        
        try:
            from src.antoine_scraper_adapter import AntoineScraperAdapter
            
            # Test the exact same way working tests do (no job_id)
            company = CompanyData(name="Notion Compatibility Test", website="https://www.notion.so")
            adapter = AntoineScraperAdapter(self.config)
            
            print(f"🔄 Testing compatibility (no job_id like working tests)...")
            
            start_time = time.time()
            result = adapter.scrape_company(company)  # No job_id like working tests
            elapsed = time.time() - start_time
            
            print(f"⏱️ Execution time: {elapsed:.1f}s")
            print(f"📊 Status: {result.scrape_status}")
            
            if result.scrape_status == "success":
                print(f"✅ Compatibility test passed - working code pattern still works")
                
                # Show some extracted data
                if hasattr(result, 'company_description') and result.company_description:
                    print(f"📝 Description preview: {result.company_description[:100]}...")
                
                return True
            else:
                print(f"❌ Compatibility test failed - status: {result.scrape_status}")
                if hasattr(result, 'scrape_error'):
                    print(f"   Error: {result.scrape_error}")
                return False
                
        except Exception as e:
            print(f"❌ Compatibility test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("\n" + "🧪"*40)
        print("ANTOINE WEB INTEGRATION TEST SUITE")
        print("🧪"*40)
        
        tests = [
            ("Phase Names", self.test_corrected_phase_names),
            ("Social Media Integration", self.test_social_media_integration),
            ("Progress Stability", self.test_progress_tracking_stability),
            ("Working Code Compatibility", self.test_compatibility_with_working_code)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n🎯 Starting: {test_name}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = 0
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status:<10} {test_name}")
            if success:
                passed += 1
        
        print(f"\n📊 Overall: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("\n🎉 ALL TESTS PASSED - Option 1 is viable!")
            print("✅ AntoineScraperAdapter can be fixed for web integration")
        else:
            print("\n⚠️ SOME TESTS FAILED - Option 1 needs more work")
            print("💡 Consider falling back to Option 2 (disable progress tracking)")
        
        return passed == len(tests)


def main():
    """Run the test suite"""
    tester = TestAntoineWebIntegration()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Ready to implement Option 1 fixes!")
    else:
        print("\n🔄 Consider implementing Option 2 instead")
    
    return success


if __name__ == "__main__":
    main()
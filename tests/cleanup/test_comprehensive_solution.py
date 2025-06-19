#!/usr/bin/env python3
"""
Test the comprehensive AsyncExecutionManager solution
Validates that the 184-character issue is fixed
"""

import sys
import os
import time
import asyncio
sys.path.append('src')

def test_comprehensive_solution():
    """Test the new AsyncExecutionManager approach vs old subprocess approach"""
    
    print("🧪 TESTING COMPREHENSIVE ASYNCEXECUTIONMANAGER SOLUTION")
    print("=" * 70)
    
    try:
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.async_execution_manager import IntelligentCompanyScraperAsync
        from src.intelligent_company_scraper import IntelligentCompanyScraperSync
        
        config = CompanyIntelligenceConfig()
        
        # Test data - the problematic FreeConvert case
        company_data = CompanyData(
            name='FreeConvert-Solution-Test',
            website='https://www.freeconvert.com'
        )
        
        print(f"🎯 Testing with: {company_data.website}")
        print(f"📋 Expected: >1000 characters (vs broken 148 chars)")
        print()
        
        # Test 1: New AsyncExecutionManager approach
        print("🚀 TEST 1: New AsyncExecutionManager Solution")
        print("-" * 50)
        
        async_scraper = IntelligentCompanyScraperAsync(config)
        
        start_time = time.time()
        async_result = async_scraper.scrape_company(
            CompanyData(name='AsyncTest', website=company_data.website),
            job_id="async_solution_test",
            timeout=60
        )
        async_time = time.time() - start_time
        
        async_chars = len(async_result.company_description or '')
        async_pages = len(getattr(async_result, 'pages_crawled', []))
        
        print(f"✅ AsyncExecutionManager Results:")
        print(f"   Status: {async_result.scrape_status}")
        print(f"   Execution Time: {async_time:.1f}s")
        print(f"   Description Length: {async_chars} characters")
        print(f"   Pages Crawled: {async_pages}")
        print(f"   About Page Found: {'about' in str(getattr(async_result, 'pages_crawled', [])).lower()}")
        
        # Test 2: Old subprocess approach for comparison
        print(f"\n🔧 TEST 2: Old Subprocess Approach (for comparison)")
        print("-" * 50)
        
        sync_scraper = IntelligentCompanyScraperSync(config)
        
        start_time = time.time()
        sync_result = sync_scraper.scrape_company(
            CompanyData(name='SubprocessTest', website=company_data.website),
            job_id="subprocess_comparison_test",
            timeout=60
        )
        sync_time = time.time() - start_time
        
        sync_chars = len(sync_result.company_description or '')
        sync_pages = len(getattr(sync_result, 'pages_crawled', []))
        
        print(f"⚠️ Subprocess Results:")
        print(f"   Status: {sync_result.scrape_status}")
        print(f"   Execution Time: {sync_time:.1f}s")
        print(f"   Description Length: {sync_chars} characters")
        print(f"   Pages Crawled: {sync_pages}")
        print(f"   About Page Found: {'about' in str(getattr(sync_result, 'pages_crawled', [])).lower()}")
        
        # Analysis
        print(f"\n📊 COMPREHENSIVE ANALYSIS:")
        print("=" * 50)
        
        improvement_chars = async_chars - sync_chars
        improvement_percent = ((async_chars - sync_chars) / max(sync_chars, 1)) * 100
        
        print(f"📈 Character Count Improvement:")
        print(f"   Subprocess: {sync_chars} chars")
        print(f"   AsyncManager: {async_chars} chars")
        print(f"   Improvement: +{improvement_chars} chars ({improvement_percent:.1f}%)")
        
        print(f"\n📄 Page Crawling Improvement:")
        print(f"   Subprocess: {sync_pages} pages")
        print(f"   AsyncManager: {async_pages} pages")
        print(f"   Improvement: +{async_pages - sync_pages} pages")
        
        print(f"\n⏱️ Performance Comparison:")
        print(f"   Subprocess: {sync_time:.1f}s")
        print(f"   AsyncManager: {async_time:.1f}s")
        time_diff = async_time - sync_time
        print(f"   Time Difference: {'+' if time_diff > 0 else ''}{time_diff:.1f}s")
        
        # Success criteria
        print(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        print("-" * 40)
        
        criteria_met = 0
        total_criteria = 4
        
        # Criterion 1: Character count significantly improved
        if async_chars > sync_chars * 2:
            print(f"✅ Character Count: EXCELLENT ({async_chars} > {sync_chars * 2})")
            criteria_met += 1
        elif async_chars > sync_chars:
            print(f"✅ Character Count: GOOD ({async_chars} > {sync_chars})")
            criteria_met += 1
        else:
            print(f"❌ Character Count: POOR ({async_chars} ≤ {sync_chars})")
        
        # Criterion 2: Page crawling improved
        if async_pages > sync_pages:
            print(f"✅ Page Crawling: IMPROVED ({async_pages} > {sync_pages})")
            criteria_met += 1
        else:
            print(f"❌ Page Crawling: NO IMPROVEMENT ({async_pages} ≤ {sync_pages})")
        
        # Criterion 3: Execution completed successfully
        if async_result.scrape_status == "success":
            print(f"✅ Execution Status: SUCCESS")
            criteria_met += 1
        else:
            print(f"❌ Execution Status: FAILED ({async_result.scrape_status})")
        
        # Criterion 4: Minimum quality threshold
        if async_chars >= 1000:
            print(f"✅ Quality Threshold: MET ({async_chars} ≥ 1000 chars)")
            criteria_met += 1
        else:
            print(f"❌ Quality Threshold: NOT MET ({async_chars} < 1000 chars)")
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        print("=" * 30)
        
        success_rate = (criteria_met / total_criteria) * 100
        
        if criteria_met == total_criteria:
            print(f"🎉 EXCELLENT: All criteria met ({success_rate:.0f}%)")
            print(f"✅ The AsyncExecutionManager solution FULLY FIXES the 184-character issue!")
        elif criteria_met >= 3:
            print(f"👍 GOOD: Most criteria met ({success_rate:.0f}%)")
            print(f"✅ The AsyncExecutionManager solution SIGNIFICANTLY IMPROVES the issue!")
        elif criteria_met >= 2:
            print(f"⚠️ PARTIAL: Some improvement ({success_rate:.0f}%)")
            print(f"🔄 The AsyncExecutionManager solution shows promise but needs refinement.")
        else:
            print(f"❌ FAILED: Major issues remain ({success_rate:.0f}%)")
            print(f"🚨 The AsyncExecutionManager solution did not fix the core problem.")
        
        return criteria_met >= 3
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 COMPREHENSIVE SOLUTION VALIDATION")
    print("Designed to fix the 184-character FreeConvert.com issue")
    print("by replacing broken subprocess with AsyncExecutionManager")
    print()
    
    success = test_comprehensive_solution()
    
    print(f"\n{'='*50}")
    if success:
        print("🎯 SOLUTION VALIDATION: SUCCESS")
        print("The comprehensive AsyncExecutionManager approach works!")
    else:
        print("⚠️ SOLUTION VALIDATION: NEEDS REFINEMENT")
        print("Additional improvements may be needed.")
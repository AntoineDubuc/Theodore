#!/usr/bin/env python3
"""
Fix Strategy 1: Replace subprocess with direct async execution
"""

import asyncio
import sys
import os
sys.path.append('src')

def create_fixed_sync_wrapper():
    """
    Create a new sync wrapper that uses direct execution instead of subprocess
    """
    
    fixed_code = '''
class IntelligentCompanyScraperSyncFixed:
    """Fixed synchronous wrapper using direct async execution instead of subprocess"""
    
    def __init__(self, config: CompanyIntelligenceConfig, bedrock_client=None):
        self.config = config
        self.scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    def scrape_company(self, company_data: CompanyData, job_id: str = None, timeout: int = None) -> CompanyData:
        """Direct async execution - no subprocess"""
        
        if timeout is None:
            timeout = getattr(self.config, 'scraper_timeout', 120)
            
        print(f"🔬 SCRAPER: Starting DIRECT scrape for company '{company_data.name}'")
        print(f"🔬 SCRAPER: Job ID: {job_id}")
        
        try:
            # Direct async execution using asyncio.run()
            result = asyncio.run(
                self.scraper.scrape_company_intelligent(company_data, job_id)
            )
            
            print(f"🔬 SCRAPER: Direct execution completed successfully")
            print(f"🔬 SCRAPER: Description length: {len(result.company_description or '')}")
            print(f"🔬 SCRAPER: Pages crawled: {len(result.pages_crawled or [])}")
            
            return result
            
        except Exception as e:
            print(f"❌ SCRAPER: Direct execution failed: {e}")
            company_data.scrape_status = "failed"
            company_data.scrape_error = str(e)
            return company_data
    '''
    
    return fixed_code

def test_direct_vs_subprocess():
    """
    Test both approaches to prove direct execution works better
    """
    print("🧪 TESTING DIRECT VS SUBPROCESS EXECUTION")
    print("="*60)
    
    try:
        from intelligent_company_scraper import IntelligentCompanyScraper, IntelligentCompanyScraperSync
        from models import CompanyData, CompanyIntelligenceConfig
        import asyncio
        
        config = CompanyIntelligenceConfig()
        company_data = CompanyData(
            name='Test-FreeConvert', 
            website='https://www.freeconvert.com'
        )
        
        # Test 1: Current broken subprocess
        print("🔧 TEST 1: Current Subprocess (broken)")
        sync_scraper = IntelligentCompanyScraperSync(config)
        subprocess_result = sync_scraper.scrape_company(company_data, "subprocess_test", timeout=30)
        
        print(f"  Subprocess Result:")
        print(f"    Status: {subprocess_result.scrape_status}")
        print(f"    Description Length: {len(subprocess_result.company_description or '')}")
        print(f"    Pages: {len(subprocess_result.pages_crawled or [])}")
        
        # Test 2: Direct async execution
        print(f"\n✅ TEST 2: Direct Async (working)")
        async_scraper = IntelligentCompanyScraper(config)
        
        async def test_direct():
            return await async_scraper.scrape_company_intelligent(
                CompanyData(name='Test-FreeConvert-Direct', website='https://www.freeconvert.com'),
                "direct_test"
            )
        
        direct_result = asyncio.run(test_direct())
        
        print(f"  Direct Result:")
        print(f"    Status: {direct_result.scrape_status}")
        print(f"    Description Length: {len(direct_result.company_description or '')}")
        print(f"    Pages: {len(direct_result.pages_crawled or [])}")
        
        # Compare results
        print(f"\n📊 COMPARISON:")
        subprocess_chars = len(subprocess_result.company_description or '')
        direct_chars = len(direct_result.company_description or '')
        
        print(f"  Subprocess: {subprocess_chars} chars")
        print(f"  Direct: {direct_chars} chars")
        print(f"  Improvement: {((direct_chars - subprocess_chars) / max(subprocess_chars, 1)) * 100:.1f}%")
        
        if direct_chars > subprocess_chars * 5:
            print(f"  ✅ Direct execution is SIGNIFICANTLY better!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 FIX STRATEGY 1: DIRECT ASYNC EXECUTION")
    print("="*50)
    
    print("Fixed wrapper code:")
    print(create_fixed_sync_wrapper())
    
    print("\nTesting comparison...")
    test_direct_vs_subprocess()
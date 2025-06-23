#!/usr/bin/env python3
"""
Test Method Fix
Verify that the concurrent scraper has the correct method name
"""

import sys
sys.path.insert(0, 'src')

def test_method_fix():
    """Test if the concurrent scraper has the correct methods"""
    
    print("🧪 TESTING METHOD FIX")
    print("=" * 60)
    
    try:
        from models import CompanyIntelligenceConfig, CompanyData
        from concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
        
        # Initialize scraper
        config = CompanyIntelligenceConfig()
        scraper = ConcurrentIntelligentScraperSync(config)
        
        # Check if scrape_company method exists
        if hasattr(scraper, 'scrape_company'):
            print("✅ scrape_company method exists")
        else:
            print("❌ scrape_company method missing")
            return False
        
        # Check if scrape_company_intelligent method exists
        if hasattr(scraper, 'scrape_company_intelligent'):
            print("✅ scrape_company_intelligent method exists")
        else:
            print("❌ scrape_company_intelligent method missing")
            return False
        
        # Test method signature
        import inspect
        sig = inspect.signature(scraper.scrape_company)
        params = list(sig.parameters.keys())
        
        if 'company_data' in params and 'job_id' in params:
            print("✅ Method signature is correct")
        else:
            print(f"❌ Method signature incorrect: {params}")
            return False
        
        print("✅ All method checks passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test execution"""
    
    success = test_method_fix()
    
    print("\\n" + "=" * 60)
    if success:
        print("🎉 METHOD FIX TEST: ✅ WORKING")
        print("✅ Concurrent scraper has correct method names")
        print("✅ Should resolve the AttributeError")
    else:
        print("❌ METHOD FIX TEST: ❌ FAILED")
        print("⚠️ Method signature issues remain")
    
    print("\\n📋 Next Steps:")
    print("1. If working: Restart Theodore to test the fix")
    print("2. Try processing a company again")
    print("3. Monitor for detailed URL logging")

if __name__ == "__main__":
    main()
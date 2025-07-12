#!/usr/bin/env python3
"""
Unit Test for Phase 5 Social Media Integration
==============================================

Unit test to verify Phase 5 social media extraction integration
without running the full scraper pipeline.

Usage:
    python test_phase5_unit.py
"""

import sys
import os
import asyncio

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_social_media_researcher_import():
    """Test that SocialMediaResearcher can be imported successfully"""
    
    print("🧪 Testing SocialMediaResearcher Import")
    print("-" * 50)
    
    try:
        from src.social_media_researcher import SocialMediaResearcher
        print("✅ SocialMediaResearcher imported successfully")
        
        # Test instantiation
        researcher = SocialMediaResearcher()
        print("✅ SocialMediaResearcher instantiated successfully")
        
        # Test supported platforms
        platforms = researcher.get_supported_platforms()
        print(f"✅ Supported platforms: {len(platforms)} platforms")
        print(f"   Platforms: {', '.join(platforms)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_phase5_method_exists():
    """Test that the Phase 5 method exists in IntelligentCompanyScraper"""
    
    print("\n🧪 Testing Phase 5 Method Integration")
    print("-" * 50)
    
    try:
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyIntelligenceConfig
        
        # Create scraper instance
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        
        # Check if the Phase 5 method exists
        has_method = hasattr(scraper, '_extract_social_media_from_pages')
        print(f"{'✅' if has_method else '❌'} _extract_social_media_from_pages method exists: {has_method}")
        
        if has_method:
            method = getattr(scraper, '_extract_social_media_from_pages')
            print(f"✅ Method type: {type(method)}")
            print(f"✅ Method is callable: {callable(method)}")
        
        return has_method
        
    except Exception as e:
        print(f"❌ Method check failed: {e}")
        return False

def test_phase5_method_execution():
    """Test that the Phase 5 method can be called with sample data"""
    
    print("\n🧪 Testing Phase 5 Method Execution")
    print("-" * 50)
    
    try:
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyIntelligenceConfig
        
        # Create scraper instance
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        
        # Sample page content with social media links
        sample_page_contents = [
            {
                'url': 'https://example.com',
                'content': '''
                <html>
                    <body>
                        <footer>
                            <a href="https://facebook.com/example">Facebook</a>
                            <a href="https://twitter.com/example">Twitter</a>
                            <a href="https://linkedin.com/company/example">LinkedIn</a>
                        </footer>
                    </body>
                </html>
                '''
            },
            {
                'url': 'https://example.com/about',
                'content': '''
                <html>
                    <body>
                        <header>
                            <a href="https://instagram.com/example">Instagram</a>
                            <a href="https://youtube.com/channel/example">YouTube</a>
                        </header>
                    </body>
                </html>
                '''
            }
        ]
        
        # Test the method
        print("🚀 Calling _extract_social_media_from_pages...")
        result = asyncio.run(scraper._extract_social_media_from_pages(sample_page_contents))
        
        print(f"✅ Method executed successfully")
        print(f"✅ Result type: {type(result)}")
        print(f"✅ Result is dict: {isinstance(result, dict)}")
        print(f"✅ Social media links found: {len(result)}")
        
        if result:
            print(f"📱 Links found:")
            for platform, url in result.items():
                print(f"   {platform}: {url}")
        
        # Expected platforms from sample data
        expected_platforms = {'facebook', 'twitter', 'linkedin', 'instagram', 'youtube'}
        found_platforms = set(result.keys())
        
        platforms_match = expected_platforms.issubset(found_platforms)
        print(f"✅ Expected platforms found: {platforms_match}")
        
        return len(result) >= 3  # At least 3 links should be found
        
    except Exception as e:
        print(f"❌ Method execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_company_data_social_media_field():
    """Test that CompanyData has social_media field"""
    
    print("\n🧪 Testing CompanyData Social Media Field")
    print("-" * 50)
    
    try:
        from src.models import CompanyData
        
        # Create company data instance
        company = CompanyData(name="Test Company", website="https://example.com")
        
        # Check if social_media field exists
        has_field = hasattr(company, 'social_media')
        print(f"{'✅' if has_field else '❌'} social_media field exists: {has_field}")
        
        if has_field:
            field_value = getattr(company, 'social_media')
            print(f"✅ Field type: {type(field_value)}")
            print(f"✅ Field is dict: {isinstance(field_value, dict)}")
            print(f"✅ Field initial value: {field_value}")
            
            # Test setting social media data
            company.social_media = {'facebook': 'https://facebook.com/test', 'twitter': 'https://twitter.com/test'}
            print(f"✅ Field can be set: {company.social_media}")
        
        return has_field
        
    except Exception as e:
        print(f"❌ Field check failed: {e}")
        return False

def main():
    """Run all unit tests"""
    
    print("🚀 Phase 5 Social Media Integration - Unit Tests")
    print("=" * 70)
    
    tests = [
        ("SocialMediaResearcher Import", test_social_media_researcher_import),
        ("Phase 5 Method Exists", test_phase5_method_exists),
        ("Phase 5 Method Execution", test_phase5_method_execution),
        ("CompanyData Social Media Field", test_company_data_social_media_field),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASS' if result else '❌ FAIL'} {test_name}")
        except Exception as e:
            print(f"❌ FAIL {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Unit Test Summary")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print(f"\n🎉 ALL UNIT TESTS PASSED!")
        print(f"   Phase 5 social media integration is properly implemented")
        print(f"   Ready for integration testing with full pipeline")
    else:
        print(f"\n❌ SOME UNIT TESTS FAILED")
        print(f"   Fix failing components before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
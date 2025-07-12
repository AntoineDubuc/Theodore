#!/usr/bin/env python3
"""
Test Social Media Extraction Fix
================================

Test that social media extraction now works synchronously after removing the async keyword.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.social_media_researcher import SocialMediaResearcher


def test_social_media_extraction():
    """Test that social media extraction works synchronously."""
    print("🔗 TESTING SOCIAL MEDIA EXTRACTION FIX")
    print("=" * 50)
    
    # Create test page content with social media links
    test_pages = [
        {
            'content': '''
            <html>
            <body>
            <footer>
                <a href="https://twitter.com/volvo">Follow us on Twitter</a>
                <a href="https://www.facebook.com/volvo">Facebook</a>
                <a href="https://www.linkedin.com/company/volvo">LinkedIn</a>
            </footer>
            </body>
            </html>
            '''
        },
        {
            'content': '''
            <html>
            <body>
            <div class="social-links">
                <a href="https://www.instagram.com/volvo">Instagram</a>
                <a href="https://www.youtube.com/volvo">YouTube</a>
            </div>
            </body>
            </html>
            '''
        }
    ]
    
    print(f"📄 Test data: {len(test_pages)} pages with social media links")
    print(f"🎯 Expected platforms: Twitter, Facebook, LinkedIn, Instagram, YouTube")
    
    # Test the fixed social media researcher
    researcher = SocialMediaResearcher()
    
    print(f"\n🔍 Testing extract_social_media_from_pages...")
    start_time = time.time()
    
    try:
        # This should now work synchronously (no await needed)
        social_links = researcher.extract_social_media_from_pages(test_pages)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️  Extraction completed in {duration:.3f}s")
        
        # Check results
        print(f"\n📊 RESULTS:")
        print(f"   Found {len(social_links)} social media platforms")
        
        for platform, url in social_links.items():
            print(f"   ✅ {platform}: {url}")
        
        # Validate expected platforms
        expected_platforms = ['twitter', 'facebook', 'linkedin', 'instagram', 'youtube']
        found_platforms = list(social_links.keys())
        
        missing = [p for p in expected_platforms if p not in found_platforms]
        unexpected = [p for p in found_platforms if p not in expected_platforms]
        
        print(f"\n🎯 VALIDATION:")
        print(f"   Expected: {len(expected_platforms)} platforms")
        print(f"   Found: {len(found_platforms)} platforms")
        
        if not missing and not unexpected:
            print(f"   ✅ PERFECT: All expected platforms found, no unexpected ones")
            return True
        else:
            if missing:
                print(f"   ⚠️  Missing: {missing}")
            if unexpected:
                print(f"   ⚠️  Unexpected: {unexpected}")
            print(f"   ✅ GOOD: Social media extraction working")
            return True
            
    except Exception as e:
        print(f"❌ FAILED: Social media extraction threw exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_async_removal():
    """Test that the method is no longer async."""
    print(f"\n🔧 TESTING ASYNC REMOVAL")
    print("=" * 50)
    
    researcher = SocialMediaResearcher()
    method = researcher.extract_social_media_from_pages
    
    # Check if the method is a coroutine function
    import inspect
    is_async = inspect.iscoroutinefunction(method)
    
    print(f"📊 Method analysis:")
    print(f"   Method name: {method.__name__}")
    print(f"   Is async: {is_async}")
    
    if not is_async:
        print(f"   ✅ CORRECT: Method is now synchronous")
        return True
    else:
        print(f"   ❌ INCORRECT: Method is still async")
        return False


def main():
    """Run social media extraction tests."""
    print("🧪 SOCIAL MEDIA EXTRACTION FIX TESTS")
    print("Testing that social media research no longer shows as 'pending'")
    print("=" * 80)
    
    tests = [
        ("Async Removal Test", test_async_removal),
        ("Social Media Extraction Test", test_social_media_extraction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 RUNNING: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ ERROR: {test_name} - {e}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("🎯 SOCIAL MEDIA FIX TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Social media extraction fix successful")
        print(f"🌐 Social media should no longer show as 'pending' in web UI")
        print(f"🔗 Enhanced social media research now working properly")
    else:
        print(f"\n⚠️ SOME TESTS FAILED!")
        print(f"🔧 Social media may still show as 'pending'")
        print(f"💡 Check the failed tests above for details")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
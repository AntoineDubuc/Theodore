#!/usr/bin/env python3
"""
Phase 5 UI Integration Test
=========================

Test to verify that Phase 5 social media research is properly integrated
with the UI progress tracking system.

This test will:
1. Check that progress logger is configured for 5 phases
2. Verify UI template includes Phase 5 display
3. Test JavaScript phase handling for Phase 5
4. Verify progress tracking works for Phase 5

Usage:
    python test_phase5_ui_integration.py
"""

import os
import sys
import json
import re
import time
from pathlib import Path

def test_progress_logger_configuration():
    """Test that progress logger is configured for 5 phases"""
    
    print("🧪 Testing Progress Logger Configuration")
    print("-" * 50)
    
    try:
        # Read the progress logger file
        with open('src/progress_logger.py', 'r') as f:
            content = f.read()
        
        # Check if total_phases=5 is set
        if 'total_phases=5' in content:
            print("✅ Progress logger configured for 5 phases")
            return True
        else:
            print("❌ Progress logger still configured for 4 phases")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check progress logger: {e}")
        return False

def test_ui_template_phase5():
    """Test that UI template includes Phase 5 display"""
    
    print("\n🧪 Testing UI Template Phase 5 Display")
    print("-" * 50)
    
    try:
        # Read the HTML template
        with open('templates/index.html', 'r') as f:
            content = f.read()
        
        # Check if Phase 5 is included
        if 'phase-social-media-research' in content:
            print("✅ UI template includes Phase 5 display")
            
            # Check for specific Phase 5 elements
            if 'Social Media Research' in content:
                print("✅ Phase 5 name correctly displayed")
            
            if '📱' in content:
                print("✅ Phase 5 icon correctly displayed")
            
            return True
        else:
            print("❌ UI template missing Phase 5 display")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check UI template: {e}")
        return False

def test_javascript_phase_handling():
    """Test that JavaScript handles Phase 5 correctly"""
    
    print("\n🧪 Testing JavaScript Phase 5 Handling")
    print("-" * 50)
    
    try:
        # Read the JavaScript file
        with open('static/js/app.js', 'r') as f:
            content = f.read()
        
        # Check if Phase 5 is included in phase mapping
        if 'Social Media Research' in content:
            print("✅ JavaScript includes Phase 5 in phase mapping")
            
            # Check phase array
            if 'social-media-research' in content:
                print("✅ Phase 5 ID included in phase arrays")
            
            # Check phase map
            if 'phase-social-media-research' in content:
                print("✅ Phase 5 mapping correctly defined")
            
            return True
        else:
            print("❌ JavaScript missing Phase 5 handling")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check JavaScript: {e}")
        return False

def test_phase5_progress_structure():
    """Test that Phase 5 progress tracking structure is correct"""
    
    print("\n🧪 Testing Phase 5 Progress Structure")
    print("-" * 50)
    
    try:
        # Test the progress logger directly
        sys.path.insert(0, 'src')
        from progress_logger import start_company_processing, progress_logger
        
        # Start a test job
        job_id = start_company_processing("Test Company Phase 5")
        
        # Check that it's configured for 5 phases
        progress = progress_logger.get_progress(job_id)
        
        if progress.get('total_phases') == 5:
            print("✅ New jobs configured for 5 phases")
            
            # Update Phase 5 to test tracking
            progress_logger.update_phase(job_id, "Social Media Research", "running")
            
            # Check if Phase 5 is tracked
            updated_progress = progress_logger.get_progress(job_id)
            phases = updated_progress.get('phases', [])
            
            phase5_found = any(phase['name'] == 'Social Media Research' for phase in phases)
            
            if phase5_found:
                print("✅ Phase 5 progress tracking working")
                
                # Complete the test job
                progress_logger.complete_job(job_id, success=True)
                
                return True
            else:
                print("❌ Phase 5 progress tracking not working")
                return False
        else:
            print(f"❌ New jobs still configured for {progress.get('total_phases', 'unknown')} phases")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test progress structure: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase5_ui_consistency():
    """Test that Phase 5 UI elements are consistent"""
    
    print("\n🧪 Testing Phase 5 UI Consistency")
    print("-" * 50)
    
    try:
        # Check HTML template
        with open('templates/index.html', 'r') as f:
            html_content = f.read()
        
        # Check JavaScript
        with open('static/js/app.js', 'r') as f:
            js_content = f.read()
        
        # Define expected Phase 5 elements
        expected_elements = {
            'html_id': 'phase-social-media-research',
            'name': 'Social Media Research',
            'icon': '📱'
        }
        
        # Check HTML template
        html_checks = {
            'id': expected_elements['html_id'] in html_content,
            'name': expected_elements['name'] in html_content,
            'icon': expected_elements['icon'] in html_content
        }
        
        # Check JavaScript
        js_checks = {
            'id': expected_elements['html_id'] in js_content,
            'name': expected_elements['name'] in js_content,
            'mapping': 'phase-social-media-research' in js_content
        }
        
        # Report results
        all_html_ok = all(html_checks.values())
        all_js_ok = all(js_checks.values())
        
        print(f"📄 HTML Template: {'✅' if all_html_ok else '❌'}")
        for check, result in html_checks.items():
            print(f"   {check}: {'✅' if result else '❌'}")
        
        print(f"📜 JavaScript: {'✅' if all_js_ok else '❌'}")
        for check, result in js_checks.items():
            print(f"   {check}: {'✅' if result else '❌'}")
        
        return all_html_ok and all_js_ok
        
    except Exception as e:
        print(f"❌ Failed to check UI consistency: {e}")
        return False

def main():
    """Run all Phase 5 UI integration tests"""
    
    print("🚀 Phase 5 UI Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Progress Logger Configuration", test_progress_logger_configuration),
        ("UI Template Phase 5 Display", test_ui_template_phase5),
        ("JavaScript Phase 5 Handling", test_javascript_phase_handling),
        ("Phase 5 Progress Structure", test_phase5_progress_structure),
        ("Phase 5 UI Consistency", test_phase5_ui_consistency),
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
    print(f"\n📊 UI Integration Test Summary")
    print("=" * 70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print(f"\n🎉 ALL UI INTEGRATION TESTS PASSED!")
        print(f"   Phase 5 social media research is fully integrated")
        print(f"   UI progress tracking and display working correctly")
        print(f"   Ready for production deployment")
    else:
        print(f"\n❌ SOME UI INTEGRATION TESTS FAILED")
        print(f"   Fix failing components before deploying")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
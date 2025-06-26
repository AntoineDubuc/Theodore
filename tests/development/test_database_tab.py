#!/usr/bin/env python3
"""
Test script to verify database tab functionality
"""

import requests
import json

def test_database_api():
    """Test that the database API endpoint is working"""
    print("🧪 TESTING DATABASE TAB FUNCTIONALITY")
    print("=" * 50)
    
    base_url = "http://localhost:5002"
    
    # Test 1: Check main app is running
    print("\n1️⃣ Testing main app accessibility:")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Main app accessible")
        else:
            print(f"   ❌ Main app returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot reach main app: {e}")
        return False
    
    # Test 2: Check companies API endpoint
    print("\n2️⃣ Testing companies API endpoint:")
    try:
        response = requests.get(f"{base_url}/api/companies?page=1&page_size=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                companies_count = len(data.get('companies', []))
                total_count = data.get('total', 0)
                print(f"   ✅ API working: {companies_count} companies returned, {total_count} total")
                
                # Show sample company data
                if companies_count > 0:
                    sample = data['companies'][0]
                    print(f"   📊 Sample company: {sample.get('name', 'Unknown')} ({sample.get('industry', 'Unknown industry')})")
                
                return True
            else:
                print(f"   ❌ API returned success=false: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return False

def test_company_details():
    """Test that we can fetch individual company details"""
    print("\n3️⃣ Testing company details endpoint:")
    try:
        # First get a list of companies
        response = requests.get("http://localhost:5002/api/companies?page=1&page_size=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('companies'):
                company_id = data['companies'][0]['id']
                company_name = data['companies'][0]['name']
                
                # Test fetching details for this company
                details_response = requests.get(f"http://localhost:5002/api/company/{company_id}", timeout=10)
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    if details_data.get('success'):
                        print(f"   ✅ Company details working: {company_name}")
                        return True
                    else:
                        print(f"   ❌ Company details failed: {details_data.get('error')}")
                        return False
                else:
                    print(f"   ❌ Company details returned {details_response.status_code}")
                    return False
            else:
                print("   ❌ No companies available for testing")
                return False
        else:
            print(f"   ❌ Cannot get companies list for testing")
            return False
    except Exception as e:
        print(f"   ❌ Company details test error: {e}")
        return False

def main():
    print("🚀 DATABASE TAB DIAGNOSTIC")
    print("=" * 60)
    
    api_ok = test_database_api()
    details_ok = test_company_details()
    
    print(f"\n🎯 DIAGNOSTIC RESULTS:")
    print("=" * 60)
    
    if api_ok and details_ok:
        print("✅ ALL BACKEND SYSTEMS WORKING")
        print("\nIf database tab still doesn't work, the issue is in frontend JavaScript:")
        print("   • Check browser console for JavaScript errors")
        print("   • Verify tab clicking triggers loadDatabaseBrowser()")
        print("   • Check if DOM elements exist when function runs")
        print("   • Verify CSS is not hiding the content")
        
        print("\n🔧 FRONTEND DEBUGGING STEPS:")
        print("1. Open browser developer tools (F12)")
        print("2. Go to Console tab")
        print("3. Click database tab")
        print("4. Check for any error messages")
        print("5. Try running: window.theodoreUI.loadDatabaseBrowser()")
        
    else:
        print("❌ BACKEND ISSUES DETECTED")
        if not api_ok:
            print("   • Companies API endpoint not working")
        if not details_ok:
            print("   • Company details endpoint not working")
        print("\nResolve backend issues before investigating frontend")

if __name__ == "__main__":
    main()
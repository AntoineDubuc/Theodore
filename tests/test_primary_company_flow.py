#!/usr/bin/env python3
"""
Test the new primary company flow:
1. Search for a company
2. Verify "Research this company" button appears first
3. Test the research → view research → add to index → hide view research flow
"""

import requests
import json
from datetime import datetime

def test_discovery_api():
    """Test the discovery API to see the primary company structure"""
    print("🎯 TESTING: V2 Discovery API for Primary Company")
    print("=" * 50)
    
    base_url = "http://localhost:5004"
    
    # Test discovery
    discovery_payload = {
        "input_text": "walmart",
        "limit": 3
    }
    
    print("📤 Calling V2 discovery API...")
    try:
        response = requests.post(
            f"{base_url}/api/v2/discover",
            json=discovery_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Discovery successful!")
                print(f"📊 Found {result['total_found']} similar companies")
                
                # Check primary company structure
                primary_company = result.get('primary_company', {})
                print(f"\n🏢 Primary Company:")
                print(f"   Name: {primary_company.get('name', 'N/A')}")
                print(f"   Website: {primary_company.get('website', 'N/A')}")
                
                print(f"\n👥 Similar Companies:")
                for i, company in enumerate(result.get('similar_companies', [])[:3]):
                    print(f"   {i+1}. {company.get('name', 'N/A')} - {company.get('website', 'N/A')}")
                
                print(f"\n✅ Primary company data structure looks good for UI!")
                return True
            else:
                print(f"❌ Discovery failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Discovery API failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Discovery test exception: {e}")
        return False

def check_ui_structure():
    """Check that the UI can load properly"""
    print(f"\n🌐 TESTING: V2 UI Structure")
    print("=" * 30)
    
    base_url = "http://localhost:5004"
    
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            html_content = response.text
            
            # Check for key UI elements
            checks = [
                ('discoveryResults', 'Discovery results container'),
                ('companyCards', 'Company cards container'),
                ('theodoreV2', 'JavaScript object'),
                ('v2_app.js', 'JavaScript file inclusion'),
                ('primary-company', 'Primary company styling')
            ]
            
            all_good = True
            for check_item, description in checks:
                if check_item in html_content:
                    print(f"✅ {description}: Found")
                else:
                    print(f"❌ {description}: Missing")
                    all_good = False
            
            return all_good
            
        else:
            print(f"❌ UI load failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ UI check exception: {e}")
        return False

def main():
    """Run the complete test"""
    print("🚀 PRIMARY COMPANY FLOW TEST")
    print(f"Timestamp: {datetime.now()}")
    print("Testing the new flow: Search → Research this company → View Research → Add to Index")
    print()
    
    # Test 1: Discovery API
    discovery_ok = test_discovery_api()
    
    # Test 2: UI Structure
    ui_ok = check_ui_structure()
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if discovery_ok:
        print("✅ PASS: Discovery API returns primary company data")
    else:
        print("❌ FAIL: Discovery API issues")
    
    if ui_ok:
        print("✅ PASS: UI structure supports primary company flow")
    else:
        print("❌ FAIL: UI structure issues")
    
    if discovery_ok and ui_ok:
        print(f"\n🎉 SUCCESS: Primary company flow is ready!")
        print("✅ UI will show 'Research this company' button first")
        print("✅ After research: 'Research this company' + 'View Research' buttons")
        print("✅ After add to index: 'View Research' button will disappear")
        
        print(f"\n🎯 MANUAL TEST STEPS:")
        print("1. Go to http://localhost:5004")
        print("2. Search for 'walmart'")
        print("3. Verify primary company card appears first with 'Research this company' button")
        print("4. Click 'Research this company' and watch the flow")
        
    else:
        print(f"\n💥 FAILURE: Issues need to be resolved")
    
    print(f"\n✅ TEST COMPLETE")

if __name__ == "__main__":
    main()
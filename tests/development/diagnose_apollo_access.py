#!/usr/bin/env python3
"""
Apollo.io API Access Diagnostic
Test different endpoints to see what's available with current API plan
"""

import os
import requests
import json
from pathlib import Path

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

def test_apollo_endpoints():
    """Test various Apollo.io endpoints to determine access level"""
    
    print("🔍 APOLLO.IO API ACCESS DIAGNOSTIC")
    print("="*50)
    
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    print(f"🔑 Testing API key: {api_key[:8]}...")
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    # Test different endpoints
    endpoints_to_test = [
        {
            "name": "Mixed Companies Search (v1)",
            "method": "POST",
            "url": "https://api.apollo.io/api/v1/mixed_companies/search",
            "payload": {"q_organization_name": "Apollo", "page": 1, "per_page": 1}
        },
        {
            "name": "Organizations Search (v1)", 
            "method": "POST",
            "url": "https://api.apollo.io/api/v1/organizations/search",
            "payload": {"q_organization_name": "Apollo", "page": 1, "per_page": 1}
        },
        {
            "name": "People Search (v1)",
            "method": "POST", 
            "url": "https://api.apollo.io/api/v1/mixed_people/search",
            "payload": {"q_organization_name": "Apollo", "page": 1, "per_page": 1}
        },
        {
            "name": "Account Info",
            "method": "GET",
            "url": "https://api.apollo.io/api/v1/auth/health",
            "payload": None
        },
        {
            "name": "Credits Info",
            "method": "GET", 
            "url": "https://api.apollo.io/api/v1/users/me",
            "payload": None
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"   Method: {endpoint['method']}")
        print(f"   URL: {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    headers=headers,
                    json=endpoint['payload'],
                    timeout=10
                )
            else:
                response = requests.get(
                    endpoint['url'],
                    headers=headers,
                    timeout=10
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Endpoint accessible")
                try:
                    data = response.json()
                    if 'pagination' in data:
                        total = data.get('pagination', {}).get('total_entries', 0)
                        print(f"   📊 Total entries available: {total}")
                    if 'user' in data:
                        print(f"   👤 User info available")
                    if 'credits' in data:
                        print(f"   💳 Credits info available")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
                    
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED - Invalid API key")
            elif response.status_code == 403:
                print(f"   🚫 FORBIDDEN - Endpoint not accessible with current plan")
                try:
                    error_data = response.json()
                    print(f"   💡 Error: {error_data.get('error', 'Unknown')}")
                    print(f"   💡 Code: {error_data.get('error_code', 'Unknown')}")
                except:
                    pass
            elif response.status_code == 429:
                print(f"   ⚠️  RATE LIMITED - Too many requests")
            else:
                print(f"   ❓ UNKNOWN STATUS - {response.text[:100]}...")
                
            results.append({
                "endpoint": endpoint['name'],
                "status": response.status_code,
                "accessible": response.status_code == 200
            })
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST FAILED - {e}")
            results.append({
                "endpoint": endpoint['name'],
                "status": "ERROR",
                "accessible": False
            })
    
    # Summary
    print(f"\n" + "="*50)
    print("📊 ACCESS SUMMARY")
    print("="*50)
    
    accessible_endpoints = [r for r in results if r['accessible']]
    
    print(f"✅ Accessible endpoints: {len(accessible_endpoints)}/{len(results)}")
    
    if accessible_endpoints:
        print(f"\n🎯 Available endpoints:")
        for result in accessible_endpoints:
            print(f"   • {result['endpoint']}")
            
        print(f"\n💡 RECOMMENDATION:")
        if any("Organizations Search" in r['endpoint'] for r in accessible_endpoints):
            print("   ✅ Use Organizations Search endpoint for company data")
        elif any("People Search" in r['endpoint'] for r in accessible_endpoints):
            print("   🟡 Only People Search available - limited company data")
        elif any("Account Info" in r['endpoint'] for r in accessible_endpoints):
            print("   🔴 Only basic account access - no search capabilities")
        else:
            print("   ❌ No search endpoints available")
            
    else:
        print(f"\n🔴 No endpoints accessible")
        print(f"💡 Possible issues:")
        print(f"   • Free plan with no API access")
        print(f"   • Trial plan expired")
        print(f"   • Need to upgrade to paid plan")
        print(f"   • API key configuration issue")
    
    return results

if __name__ == "__main__":
    try:
        results = test_apollo_endpoints()
        print(f"\n🎉 Diagnostic completed!")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
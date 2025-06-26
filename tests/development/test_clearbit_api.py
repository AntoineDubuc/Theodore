#!/usr/bin/env python3
"""
Clearbit API Test
Test Clearbit's company enrichment and discovery APIs
"""

import os
import requests
import json
from datetime import datetime
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

def test_clearbit_access():
    """Test Clearbit API access and capabilities"""
    
    print("🔍 CLEARBIT API ACCESS TEST")
    print("="*50)
    
    # Check for API key (would need to be added to .env)
    api_key = os.getenv('CLEARBIT_API_KEY')
    
    if not api_key:
        print("❌ CLEARBIT_API_KEY not found in environment")
        print("📝 To test Clearbit, add to your .env file:")
        print("CLEARBIT_API_KEY=your_clearbit_api_key")
        print("\n💡 Get a free API key from: https://clearbit.com/")
        return False
    
    print(f"🔑 Testing API key: {api_key[:8]}...")
    
    # Test endpoints
    test_companies = ["procurify.com", "stripe.com", "shopify.com"]
    
    for domain in test_companies:
        print(f"\n🏢 Testing: {domain}")
        
        # Test Company API
        try:
            response = requests.get(
                f"https://company.clearbit.com/v2/companies/find",
                params={"domain": domain},
                auth=(api_key, ""),  # Clearbit uses basic auth
                timeout=10
            )
            
            print(f"   Company API Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Company found")
                print(f"   📊 Name: {data.get('name', 'Unknown')}")
                print(f"   🏢 Industry: {data.get('category', {}).get('industry', 'Unknown')}")
                print(f"   👥 Employees: {data.get('metrics', {}).get('employees', 'Unknown')}")
                print(f"   📍 Location: {data.get('geo', {}).get('city', 'Unknown')}")
                
            elif response.status_code == 202:
                print(f"   ⏳ PENDING - Data being enriched")
            elif response.status_code == 404:
                print(f"   ❌ NOT FOUND - Company not in database")
            elif response.status_code == 401:
                print(f"   🔑 UNAUTHORIZED - Invalid API key")
            elif response.status_code == 422:
                print(f"   ❓ UNPROCESSABLE - Invalid domain format")
            else:
                print(f"   ❓ UNKNOWN STATUS: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST FAILED: {e}")
        
        # Small delay between requests
        import time
        time.sleep(1)
    
    return True

def test_clearbit_discovery():
    """Test Clearbit Discovery API for company search"""
    
    print(f"\n" + "="*50)
    print("CLEARBIT DISCOVERY API TEST")
    print("="*50)
    
    api_key = os.getenv('CLEARBIT_API_KEY')
    if not api_key:
        print("❌ No API key available for Discovery test")
        return
    
    # Test discovery search
    try:
        search_params = {
            "query": "procurement software",
            "limit": 5
        }
        
        response = requests.get(
            "https://discovery.clearbit.com/v1/companies/search",
            params=search_params,
            auth=(api_key, ""),
            timeout=10
        )
        
        print(f"Discovery API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            companies = data.get('results', [])
            print(f"✅ Found {len(companies)} companies")
            
            for i, company in enumerate(companies[:3], 1):
                print(f"   {i}. {company.get('name', 'Unknown')}")
                print(f"      Domain: {company.get('domain', 'Unknown')}")
                print(f"      Industry: {company.get('category', {}).get('industry', 'Unknown')}")
                
        elif response.status_code == 401:
            print("🔑 UNAUTHORIZED - Discovery API requires paid plan")
        elif response.status_code == 403:
            print("🚫 FORBIDDEN - Discovery API not accessible")
        else:
            print(f"❓ STATUS {response.status_code}: {response.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Discovery test failed: {e}")

def show_clearbit_integration_potential():
    """Show how Clearbit could integrate with Theodore"""
    
    print(f"\n" + "="*50)
    print("CLEARBIT + THEODORE INTEGRATION POTENTIAL")
    print("="*50)
    
    integration_benefits = {
        "Real-time Enrichment": "Add company data during Theodore research",
        "Technology Detection": "Identify tech stack and tools used",
        "Employee Count": "Get accurate headcount data",
        "Social Profiles": "LinkedIn, Twitter, Facebook links",
        "Funding Information": "Investment rounds and valuations",
        "Contact Discovery": "Find key decision makers"
    }
    
    for benefit, description in integration_benefits.items():
        print(f"✅ {benefit}: {description}")
    
    print(f"\n🎯 CLEARBIT INTEGRATION WORKFLOW:")
    print(f"   1. Theodore scrapes company website")
    print(f"   2. Clearbit enriches with additional data")
    print(f"   3. Combined intelligence in Theodore results")
    print(f"   4. Enhanced company profiles for users")

if __name__ == "__main__":
    try:
        has_api_key = test_clearbit_access()
        
        if has_api_key:
            test_clearbit_discovery()
        
        show_clearbit_integration_potential()
        
        print(f"\n🎉 Clearbit API test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
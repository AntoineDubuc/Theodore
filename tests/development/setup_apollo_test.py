#!/usr/bin/env python3
"""
Apollo.io API Test Setup
Simple script to validate API key and basic connectivity
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
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value

# Load .env file
load_env()

def validate_apollo_api_key():
    """Validate Apollo.io API key with a simple test request"""
    
    print("🔧 APOLLO.IO API SETUP VALIDATION")
    print("="*50)
    
    # Check for API key
    api_key = os.getenv('APOLLO_API_KEY')
    
    if not api_key:
        print("❌ APOLLO_API_KEY environment variable not found")
        print("\n📝 To set your API key:")
        print("export APOLLO_API_KEY='your_apollo_api_key_here'")
        print("\nOr add it to your .env file:")
        print("APOLLO_API_KEY=your_apollo_api_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    
    # Test basic API connectivity
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json", 
        "X-Api-Key": api_key
    }
    
    print("\n🔍 Testing API connectivity...")
    
    try:
        # Simple test - search for a well-known company
        test_payload = {
            "q_organization_name": "Apollo",
            "page": 1,
            "per_page": 1
        }
        
        response = requests.post(
            "https://api.apollo.io/api/v1/mixed_companies/search",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total_entries = data.get("pagination", {}).get("total_entries", 0)
            print(f"✅ API working! Found {total_entries} organizations matching 'Apollo'")
            print("🚀 Ready to run full API test!")
            return True
            
        elif response.status_code == 401:
            print("❌ API key is invalid or expired")
            print("Please check your Apollo.io API key")
            return False
            
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded")
            print("Wait a moment and try again")
            return False
            
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        print("Check your internet connection and try again")
        return False

def show_test_instructions():
    """Show instructions for running the full test"""
    
    print(f"\n" + "="*50)
    print("📋 NEXT STEPS")
    print("="*50)
    print("1. Run the full Apollo.io API test:")
    print("   python tests/development/test_apollo_api.py")
    print()
    print("2. The test will:")
    print("   • Search for 5 sample companies")
    print("   • Test organization data retrieval")
    print("   • Test job postings data")
    print("   • Generate integration recommendations")
    print()
    print("3. Results will be saved as JSON for analysis")
    print()
    print("🎯 This will help determine if Apollo.io is worth")
    print("   integrating into Theodore's data pipeline")

if __name__ == "__main__":
    success = validate_apollo_api_key()
    
    if success:
        show_test_instructions()
    else:
        print(f"\n🔧 Fix the API key issue and run this script again")
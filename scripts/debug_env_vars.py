#!/usr/bin/env python3
"""
Debug environment variable loading
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_env_vars():
    """Check what environment variables are loaded"""
    print("🔍 Debugging environment variables...")
    
    # Check Google API configuration
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cx = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    print(f"\n📋 Google API Configuration:")
    print(f"   GOOGLE_API_KEY: {'✅ Set' if google_api_key else '❌ Not found'}")
    if google_api_key:
        print(f"   Value: {google_api_key[:10]}...{google_api_key[-5:] if len(google_api_key) > 15 else google_api_key}")
    
    print(f"   GOOGLE_SEARCH_ENGINE_ID: {'✅ Set' if google_cx else '❌ Not found'}")
    if google_cx:
        print(f"   Value: {google_cx[:10]}...{google_cx[-5:] if len(google_cx) > 15 else google_cx}")
    
    print(f"   SERPAPI_KEY: {'✅ Set' if serpapi_key else '❌ Not found'}")
    if serpapi_key:
        print(f"   Value: {serpapi_key[:10]}...{serpapi_key[-5:] if len(serpapi_key) > 15 else serpapi_key}")
    
    print(f"\n📝 Next Steps:")
    if google_api_key and not google_cx:
        print(f"   ✅ Google API key found!")
        print(f"   ❌ Need to add GOOGLE_SEARCH_ENGINE_ID to .env file")
        print(f"   📋 Instructions:")
        print(f"      1. Go to: https://cse.google.com/cse/")
        print(f"      2. Create new search engine (search entire web)")
        print(f"      3. Get the Search Engine ID")
        print(f"      4. Add to .env: GOOGLE_SEARCH_ENGINE_ID=your_id_here")
    elif not google_api_key:
        print(f"   ❌ Google API key not found in environment")
        print(f"   📋 Check that .env file has: GOOGLE_API_KEY=your_key_here")
    else:
        print(f"   ✅ Both Google API key and Search Engine ID found!")

if __name__ == "__main__":
    debug_env_vars()
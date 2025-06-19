#!/usr/bin/env python3
"""
Test Gemini API directly
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini():
    """Test if Gemini API is working"""
    
    print("🧪 Testing Gemini API...")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GEMINI_API_KEY found")
        return
        
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        
        print("📤 Sending test prompt...")
        response = model.generate_content("Say 'Hello, Gemini is working!' in exactly 5 words")
        
        print(f"✅ Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_gemini()
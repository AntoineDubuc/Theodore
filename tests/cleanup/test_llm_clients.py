#!/usr/bin/env python3
"""
Test Bedrock and Gemini clients directly to prove if they work
"""

import sys
import os
sys.path.append('src')

def test_bedrock_client():
    print("🧪 TESTING BEDROCK CLIENT")
    print("="*50)
    
    try:
        from bedrock_client import BedrockClient
        from models import CompanyIntelligenceConfig
        
        # Test 1: Import and initialize
        print("✅ Successfully imported BedrockClient")
        
        # Test 2: Check configuration
        config = CompanyIntelligenceConfig()
        print(f"✅ Config created: {type(config)}")
        
        # Test 3: Initialize client
        try:
            bedrock_client = BedrockClient(config)
            print("✅ BedrockClient initialized successfully")
        except Exception as e:
            print(f"❌ BedrockClient initialization failed: {e}")
            return False
        
        # Test 4: Check environment variables
        aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        print(f"AWS_ACCESS_KEY_ID: {'✅ Present' if aws_key else '❌ Missing'}")
        print(f"AWS_SECRET_ACCESS_KEY: {'✅ Present' if aws_secret else '❌ Missing'}")
        
        # Test 5: Simple API call
        try:
            test_prompt = "What is 2+2? Answer in one word."
            print(f"🧠 Testing with prompt: '{test_prompt}'")
            response = bedrock_client.analyze_content(test_prompt)
            print(f"✅ Bedrock response: '{response}'")
            print(f"✅ Response length: {len(response)} characters")
            return True
        except Exception as e:
            print(f"❌ Bedrock API call failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Bedrock test completely failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_client():
    print("\n🧪 TESTING GEMINI CLIENT")
    print("="*50)
    
    try:
        # Test 1: Check environment variable
        gemini_key = os.getenv('GEMINI_API_KEY')
        print(f"GEMINI_API_KEY: {'✅ Present' if gemini_key else '❌ Missing'}")
        
        if not gemini_key:
            print("❌ Cannot test Gemini without API key")
            return False
            
        # Test 2: Import Gemini
        try:
            import google.generativeai as genai
            print("✅ Successfully imported google.generativeai")
        except ImportError as e:
            print(f"❌ Failed to import google.generativeai: {e}")
            return False
        
        # Test 3: Configure Gemini
        try:
            genai.configure(api_key=gemini_key)
            print("✅ Gemini configured successfully")
        except Exception as e:
            print(f"❌ Gemini configuration failed: {e}")
            return False
        
        # Test 4: Initialize model
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
            print("✅ Gemini model initialized successfully")
        except Exception as e:
            print(f"❌ Gemini model initialization failed: {e}")
            return False
        
        # Test 5: Simple API call
        try:
            test_prompt = "What is 2+2? Answer in one word."
            print(f"🧠 Testing with prompt: '{test_prompt}'")
            response = model.generate_content(test_prompt)
            print(f"✅ Gemini response: '{response.text}'")
            print(f"✅ Response length: {len(response.text)} characters")
            return True
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Gemini test completely failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_scraper_llm():
    print("\n🧪 TESTING INTELLIGENT SCRAPER LLM INTEGRATION")
    print("="*60)
    
    try:
        from intelligent_company_scraper import IntelligentCompanyScraper
        from models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        
        print(f"Bedrock client available: {'✅ YES' if scraper.bedrock_client else '❌ NO'}")
        print(f"Gemini client available: {'✅ YES' if scraper.gemini_client else '❌ NO'}")
        
        # Test the actual LLM call method
        import asyncio
        
        async def test_llm_call():
            try:
                test_prompt = "What is 2+2? Answer in one word."
                print(f"🧠 Testing _call_llm_async with: '{test_prompt}'")
                response = await scraper._call_llm_async(test_prompt)
                print(f"✅ LLM call successful: '{response}'")
                print(f"✅ Response length: {len(response)} characters")
                return True
            except Exception as e:
                print(f"❌ LLM call failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        return asyncio.run(test_llm_call())
        
    except Exception as e:
        print(f"❌ Scraper LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 COMPREHENSIVE LLM CLIENT TESTING")
    print("="*60)
    
    bedrock_works = test_bedrock_client()
    gemini_works = test_gemini_client()
    scraper_works = test_intelligent_scraper_llm()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Bedrock Client: {'✅ WORKING' if bedrock_works else '❌ FAILED'}")
    print(f"Gemini Client: {'✅ WORKING' if gemini_works else '❌ FAILED'}")
    print(f"Scraper LLM Integration: {'✅ WORKING' if scraper_works else '❌ FAILED'}")
    
    if bedrock_works or gemini_works:
        print(f"\n✅ At least one LLM client is working!")
    else:
        print(f"\n❌ NO LLM clients are working!")
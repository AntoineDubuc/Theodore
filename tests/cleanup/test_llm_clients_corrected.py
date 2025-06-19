#!/usr/bin/env python3
"""
Corrected test for Bedrock and Gemini clients with proper .env loading
"""

import sys
import os
sys.path.append('src')

# CRITICAL: Load .env file first!
from dotenv import load_dotenv
load_dotenv()

def test_bedrock_client():
    print("🧪 TESTING BEDROCK CLIENT (with .env loaded)")
    print("="*50)
    
    try:
        from bedrock_client import BedrockClient
        from models import CompanyIntelligenceConfig
        
        # Check environment variables after loading .env
        aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION')
        
        print(f"AWS_ACCESS_KEY_ID: {'✅ Present (' + aws_key[:8] + '...)' if aws_key else '❌ Missing'}")
        print(f"AWS_SECRET_ACCESS_KEY: {'✅ Present' if aws_secret else '❌ Missing'}")
        print(f"AWS_REGION: {'✅ Present (' + aws_region + ')' if aws_region else '❌ Missing'}")
        
        if not aws_key or not aws_secret:
            print("❌ Cannot test Bedrock without AWS credentials")
            return False
        
        # Initialize client
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        print("✅ BedrockClient initialized successfully")
        
        # Test API call
        test_prompt = "What is 2+2? Answer in one word."
        print(f"🧠 Testing with prompt: '{test_prompt}'")
        response = bedrock_client.analyze_content(test_prompt)
        
        if response and len(response.strip()) > 0:
            print(f"✅ Bedrock response: '{response}'")
            print(f"✅ Response length: {len(response)} characters")
            return True
        else:
            print(f"❌ Bedrock returned empty response: '{response}'")
            return False
            
    except Exception as e:
        print(f"❌ Bedrock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_client():
    print("\n🧪 TESTING GEMINI CLIENT (with .env loaded)")
    print("="*50)
    
    try:
        # Check environment variable after loading .env
        gemini_key = os.getenv('GEMINI_API_KEY')
        print(f"GEMINI_API_KEY: {'✅ Present (' + gemini_key[:8] + '...)' if gemini_key else '❌ Missing'}")
        
        if not gemini_key:
            print("❌ Cannot test Gemini without API key")
            return False
            
        # Import and configure Gemini
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        print("✅ Gemini configured successfully")
        
        # Initialize model
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        print("✅ Gemini model initialized successfully")
        
        # Test API call
        test_prompt = "What is 2+2? Answer in one word."
        print(f"🧠 Testing with prompt: '{test_prompt}'")
        response = model.generate_content(test_prompt)
        
        if response and response.text and len(response.text.strip()) > 0:
            print(f"✅ Gemini response: '{response.text}'")
            print(f"✅ Response length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ Gemini returned empty response: '{response}'")
            return False
            
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_page_selection():
    print("\n🧪 TESTING LLM PAGE SELECTION")
    print("="*50)
    
    try:
        from intelligent_company_scraper import IntelligentCompanyScraper
        from models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        
        print(f"Bedrock client available: {'✅ YES' if scraper.bedrock_client else '❌ NO'}")
        print(f"Gemini client available: {'✅ YES' if scraper.gemini_client else '❌ NO'}")
        
        # Test with sample links including about page
        test_links = [
            "https://www.freeconvert.com",
            "https://www.freeconvert.com/about",  # This should be prioritized!
            "https://www.freeconvert.com/pricing",
            "https://www.freeconvert.com/mp4-to-mp3",
            "https://www.freeconvert.com/pdf-converter",
        ]
        
        import asyncio
        
        async def test_selection():
            print(f"🤖 Testing page selection with {len(test_links)} links...")
            selected = await scraper._llm_select_promising_pages(
                test_links, "FreeConvert", "https://www.freeconvert.com"
            )
            
            print(f"✅ Selected {len(selected)} pages:")
            for i, url in enumerate(selected, 1):
                print(f"  {i}. {url}")
            
            about_selected = any("/about" in url for url in selected)
            print(f"🎯 About page selected: {'✅ YES' if about_selected else '❌ NO'}")
            
            return len(selected) > 0
        
        return asyncio.run(test_selection())
        
    except Exception as e:
        print(f"❌ Page selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 CORRECTED LLM CLIENT TESTING (with proper .env loading)")
    print("="*60)
    
    bedrock_works = test_bedrock_client()
    gemini_works = test_gemini_client()
    selection_works = test_page_selection()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Bedrock Client: {'✅ WORKING' if bedrock_works else '❌ FAILED'}")
    print(f"Gemini Client: {'✅ WORKING' if gemini_works else '❌ FAILED'}")
    print(f"Page Selection: {'✅ WORKING' if selection_works else '❌ FAILED'}")
    
    if bedrock_works or gemini_works:
        print(f"\n✅ At least one LLM client is working!")
        if selection_works:
            print(f"✅ LLM page selection should work properly!")
        else:
            print(f"❌ Page selection still failing despite working LLM clients")
    else:
        print(f"\n❌ NO LLM clients are working!")
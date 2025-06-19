#!/usr/bin/env python3
"""
Test Gemini API with timeout
"""

import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types as genai_types

load_dotenv()

async def test_gemini_with_timeout():
    """Test Gemini with async timeout"""
    
    print("🧪 Testing Gemini API with timeout...")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GEMINI_API_KEY found")
        return
        
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test prompt
        prompt = "Return only a JSON array of 3 URLs: ['url1', 'url2', 'url3']"
        
        print("📤 Sending test prompt with generation config...")
        
        generation_config = genai_types.GenerationConfig(
            max_output_tokens=1000,
            temperature=0.7,
            candidate_count=1,
        )
        
        # Try with timeout
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            ),
            timeout=10
        )
        
        print(f"✅ Response: {response.text}")
        
    except asyncio.TimeoutError:
        print("❌ Timeout after 10 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_gemini_with_timeout())
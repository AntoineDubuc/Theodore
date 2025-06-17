#!/usr/bin/env python3
"""
Test what the Google fallback actually returned for MSI
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

from openai_client import SimpleOpenAIClient

def test_msi_google_knowledge():
    """Test what the LLM knows about MSI careers when asked directly"""
    print("🧪 Testing what LLM knows about MSI careers...")
    
    try:
        # Initialize OpenAI client
        openai_client = SimpleOpenAIClient()
        
        # Test the exact prompt used in Google fallback
        prompt = f"""I couldn't find job listings directly on MSI's website. Please provide helpful guidance for finding their job openings.

Based on your knowledge of MSI:

1. Are they actively hiring? (true/false)
2. What types of roles do they typically hire for?
3. What are the best places to find their job postings?
4. Any specific advice for job seekers interested in MSI?

Respond in JSON format:
{{
    "likely_hiring": true/false,
    "typical_roles": ["Software Engineer", "Product Manager", "Sales"],
    "best_job_sites": ["LinkedIn", "their careers page", "AngelList"],
    "career_page_url": "direct URL if you know it",
    "search_tips": "specific search tips",
    "company_info": "brief hiring info"
}}

Response:"""
        
        print("🤖 Asking LLM about MSI careers...")
        response = openai_client.analyze_content(prompt)
        
        print(f"\n📥 Raw LLM Response:")
        print(response)
        
        # Try to parse JSON
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                print(f"\n✅ Parsed JSON:")
                print(json.dumps(data, indent=2))
                
                career_url = data.get('career_page_url', '')
                if career_url:
                    print(f"\n🔍 LLM provided career URL: {career_url}")
                    if 'ca.msi.com/about/careers' in career_url:
                        print(f"✅ LLM knew about the Canadian MSI careers page!")
                    else:
                        print(f"❓ LLM provided different URL than ca.msi.com/about/careers")
                else:
                    print(f"\n❌ LLM did not provide a specific career URL")
                    
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            
        # Test if we should implement real Google search
        print(f"\n🤔 Analysis:")
        print(f"The current 'Google search fallback' is actually just LLM knowledge.")
        print(f"If we want to find https://ca.msi.com/about/careers, we need:")
        print(f"1. Real Google search API integration, OR")
        print(f"2. Better LLM prompt that finds specific career URLs, OR") 
        print(f"3. Try common career URL patterns (company.com/careers, etc.)")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_msi_google_knowledge()
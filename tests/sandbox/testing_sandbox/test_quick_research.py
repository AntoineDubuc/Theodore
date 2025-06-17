#!/usr/bin/env python3
"""
Quick test of Theodore structured research system
"""

import requests
import json
import time

BASE_URL = "http://localhost:5002"

def test_structured_research():
    """Test structured research with a real company"""
    print("🔬 Testing Theodore Structured Research")
    print("=" * 50)
    
    # Test company
    company_name = "Stripe"
    website = "https://stripe.com"
    
    # Get available prompts
    print("1. Getting available research prompts...")
    response = requests.get(f"{BASE_URL}/api/research/prompts/available")
    if response.status_code != 200:
        print("❌ Failed to get prompts")
        return False
        
    prompts_data = response.json()
    
    # Get list of all prompts
    all_prompts = []
    for category in prompts_data['prompts']['categories'].values():
        all_prompts.extend(category['prompts'])
    
    # Select first 2 prompts
    selected_prompts = [p['id'] for p in all_prompts[:2]]
    print(f"✅ Selected prompts: {[p['name'] for p in all_prompts[:2]]}")
    
    # Get cost estimate
    print("2. Getting cost estimate...")
    cost_response = requests.post(
        f"{BASE_URL}/api/research/prompts/estimate",
        json={"selected_prompts": selected_prompts}
    )
    
    if cost_response.status_code == 200:
        cost_data = cost_response.json()
        estimate = cost_data.get('cost_estimate', {})
        print(f"✅ Estimated cost: ${estimate.get('total_cost', 0):.4f}")
        print(f"✅ Estimated tokens: {estimate.get('total_tokens', 0)}")
    
    # Start research
    print(f"3. Starting research for {company_name}...")
    research_payload = {
        "company_name": company_name,
        "website": website,
        "selected_prompts": selected_prompts,
        "include_base_research": True
    }
    
    research_response = requests.post(
        f"{BASE_URL}/api/research/structured/start",
        json=research_payload,
        timeout=120
    )
    
    if research_response.status_code == 200:
        research_data = research_response.json()
        if research_data.get('success'):
            session_id = research_data.get('session_id')
            print(f"✅ Research started - Session ID: {session_id}")
            
            # Wait and check results
            print("4. Waiting for research to complete...")
            time.sleep(15)  # Give it time to process
            
            session_response = requests.get(
                f"{BASE_URL}/api/research/structured/session/{session_id}"
            )
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                if session_data.get('success'):
                    session = session_data.get('session', {})
                    print(f"✅ Research completed!")
                    print(f"   Total cost: ${session.get('total_cost', 0):.4f}")
                    print(f"   Success rate: {session.get('success_rate', 0):.1%}")
                    
                    results = session.get('results', [])
                    for result in results:
                        status = "✅" if result.get('success') else "❌"
                        print(f"   {status} {result.get('prompt_name', 'Unknown')}")
                        if result.get('success') and result.get('result_data'):
                            # Show snippet of result
                            data = result.get('result_data', '')
                            snippet = data[:100] + "..." if len(data) > 100 else data
                            print(f"       Preview: {snippet}")
                    
                    return True
                else:
                    print(f"❌ Session error: {session_data.get('error')}")
            else:
                print(f"❌ Session fetch failed: {session_response.status_code}")
        else:
            print(f"❌ Research failed: {research_data.get('error')}")
    else:
        print(f"❌ Research API failed: {research_response.status_code}")
        print(f"   Response: {research_response.text[:200]}")
    
    return False

if __name__ == "__main__":
    success = test_structured_research()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 STRUCTURED RESEARCH TEST PASSED!")
        print("   Theodore system is working correctly with real companies")
    else:
        print("❌ Test failed - check server logs")
    
    print("\n💡 You can also test manually at: http://localhost:5002")
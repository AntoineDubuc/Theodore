#!/usr/bin/env python3
"""
Test the size of the LLM prompt that's causing the hang
"""
import sys
import os
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

def test_prompt_size():
    """Test how big the LLM prompt gets with real link data"""
    
    # Simulate 713 links (as found in our test)
    sample_links = []
    for i in range(713):
        sample_links.append(f"https://openai.com/page-{i}")
    
    # Prepare links for LLM analysis (same as scraper does)
    links_text = "\n".join([f"- {link}" for link in sample_links[:500]])  # Limit for token management
    
    company_name = "OpenAI"
    base_url = "https://openai.com"
    
    prompt = f"""You are a sales intelligence analyst. Your goal is to help a salesperson understand everything they need to know about {company_name} to have an effective sales conversation.

Given these discovered links for {company_name} (base URL: {base_url}):

{links_text}

Select up to 100 URLs that would provide the most valuable sales intelligence, focusing on:

1. **Business Model & Value Proposition**: How they make money, what problems they solve
2. **Target Customers**: Who they serve, customer segments, use cases
3. **Product/Service Offerings**: What they sell, pricing models, features
4. **Company Maturity**: Size indicators, funding, growth stage, team
5. **Competitive Position**: Differentiators, market position, partnerships
6. **Sales Process**: How they sell, pricing transparency, contact methods

Prioritize pages that typically contain this information:
- Homepage, About, Products/Services, Pricing, Customers, Case Studies
- Team/Leadership, Careers, Press/News, Partnerships, Solutions
- Industry-specific pages, Use Cases, Documentation

Return ONLY a JSON array of the selected URLs (no explanations):
["url1", "url2", "url3", ...]

Focus on quality over quantity. Better to select 50 highly relevant pages than 100 mediocre ones."""

    print(f"🔍 PROMPT SIZE ANALYSIS")
    print(f"=" * 50)
    print(f"Total links discovered: {len(sample_links)}")
    print(f"Links included in prompt: {min(len(sample_links), 500)}")
    print(f"Links text length: {len(links_text):,} characters")
    print(f"Full prompt length: {len(prompt):,} characters")
    print(f"Estimated tokens (rough): {len(prompt) // 4:,} tokens")
    print()
    
    print(f"📋 Prompt preview (first 500 chars):")
    print(prompt[:500] + "...")
    print()
    
    print(f"📋 Links section preview (first 10 links):")
    links_preview = "\n".join([f"- {link}" for link in sample_links[:10]])
    print(links_preview)
    print("...")
    
    # Test with BedrockClient to see if large prompt causes hang
    print(f"\n🧪 Testing BedrockClient with large prompt...")
    
    try:
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        import time
        start_time = time.time()
        
        print(f"🚀 Sending {len(prompt):,} character prompt to Bedrock...")
        response = bedrock_client.analyze_content(prompt)
        
        duration = time.time() - start_time
        
        print(f"✅ Bedrock responded in {duration:.2f} seconds")
        print(f"📤 Response length: {len(response):,} characters")
        print(f"📋 Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock failed with large prompt: {e}")
        return False

if __name__ == "__main__":
    test_prompt_size()
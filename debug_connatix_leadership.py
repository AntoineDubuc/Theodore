#!/usr/bin/env python3
"""
Debug why we didn't capture leadership data from Connatix leadership page.
"""

import os
import sys
from typing import Dict, Any

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def debug_connatix_leadership():
    """Debug Connatix leadership extraction"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get Connatix data
    connatix = pipeline.pinecone_client.find_company_by_name("connatix.com")
    
    if not connatix:
        print("❌ Connatix not found in database")
        return
    
    metadata = connatix.__dict__ if hasattr(connatix, '__dict__') else {}
    
    print("=" * 80)
    print("CONNATIX LEADERSHIP EXTRACTION DEBUG")
    print("=" * 80)
    print(f"Company: {metadata.get('company_name', 'connatix.com')}")
    print(f"Website: {metadata.get('website', 'N/A')}")
    print()
    
    # Check what pages were crawled
    pages_crawled = metadata.get('pages_crawled', [])
    raw_content = metadata.get('raw_content', '')
    company_description = metadata.get('company_description', '')
    leadership_team = metadata.get('leadership_team', '')
    
    print("📄 PAGES CRAWLED:")
    if pages_crawled:
        for i, page in enumerate(pages_crawled, 1):
            print(f"  {i}. {page}")
    else:
        print("  ❌ No pages_crawled data found")
    
    print(f"\n🔍 LEADERSHIP PAGE CHECK:")
    leadership_page = "https://connatix.com/leadership"
    if leadership_page in pages_crawled:
        print(f"  ✅ Leadership page WAS crawled: {leadership_page}")
    else:
        print(f"  ❌ Leadership page NOT crawled: {leadership_page}")
        
        # Check for similar leadership URLs
        leadership_variants = [url for url in pages_crawled if 'leadership' in url.lower() or 'team' in url.lower() or 'about' in url.lower()]
        if leadership_variants:
            print(f"  🔍 Related pages found:")
            for url in leadership_variants:
                print(f"    - {url}")
        else:
            print(f"  ❌ No leadership-related pages found in crawled URLs")
    
    print(f"\n📊 EXTRACTED LEADERSHIP DATA:")
    if leadership_team and leadership_team.strip():
        print(f"  ✅ Leadership data found: {leadership_team[:200]}...")
    else:
        print(f"  ❌ No leadership data extracted")
    
    print(f"\n📝 RAW CONTENT ANALYSIS:")
    if raw_content and 'leadership' in raw_content.lower():
        print(f"  ✅ Leadership mentions found in raw content")
        # Extract leadership-related snippets
        content_lines = raw_content.split('\n')
        leadership_lines = [line for line in content_lines if 'leadership' in line.lower() or 'CEO' in line or 'CTO' in line or 'founder' in line.lower()]
        
        if leadership_lines:
            print(f"  📋 Leadership-related content:")
            for line in leadership_lines[:5]:  # Show first 5 matches
                print(f"    - {line.strip()[:100]}...")
    else:
        print(f"  ❌ No leadership mentions in raw content")
    
    print(f"\n🧠 COMPANY DESCRIPTION ANALYSIS:")
    if company_description and ('leadership' in company_description.lower() or 'CEO' in company_description or 'founder' in company_description.lower()):
        print(f"  ✅ Leadership mentions in description")
        # Look for executive names or titles
        import re
        ceo_pattern = r'CEO[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)'
        founder_pattern = r'[Ff]ounder[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)'
        
        ceo_matches = re.findall(ceo_pattern, company_description)
        founder_matches = re.findall(founder_pattern, company_description)
        
        if ceo_matches:
            print(f"    📋 CEO found: {', '.join(ceo_matches)}")
        if founder_matches:
            print(f"    📋 Founders found: {', '.join(founder_matches)}")
            
        if not ceo_matches and not founder_matches:
            print(f"    ❓ Leadership mentioned but no names extracted")
    else:
        print(f"  ❌ No leadership mentions in company description")
    
    # Check all metadata for any leadership-related fields
    print(f"\n🔍 ALL LEADERSHIP-RELATED FIELDS:")
    leadership_fields = ['leadership_team', 'key_decision_makers', 'founders', 'executives', 'management_team']
    found_any = False
    
    for field in leadership_fields:
        value = metadata.get(field)
        if value and str(value).strip() and str(value).lower() not in ['unknown', 'not specified', 'n/a', 'none']:
            print(f"  ✅ {field}: {str(value)[:100]}...")
            found_any = True
        else:
            print(f"  ❌ {field}: Empty")
    
    if not found_any:
        print(f"  ❌ No leadership data found in any field")
    
    print(f"\n🎯 DEBUGGING CONCLUSIONS:")
    
    if leadership_page not in pages_crawled:
        print(f"  🔴 ROOT CAUSE: Leadership page not selected by LLM page selection")
        print(f"     - The LLM page selector did not choose the /leadership page")
        print(f"     - This could be due to:")
        print(f"       • Page selection prompt not prioritizing leadership pages enough")
        print(f"       • LLM response parsing issues")
        print(f"       • Fallback to heuristic selection missing leadership patterns")
    elif leadership_page in pages_crawled and not leadership_team:
        print(f"  🟡 CONTENT EXTRACTION ISSUE: Page crawled but data not extracted")
        print(f"     - Leadership page was crawled but no leadership data extracted")
        print(f"     - This could be due to:")
        print(f"       • LLM aggregation prompt not focusing on leadership extraction")
        print(f"       • Content parsing issues (JavaScript, complex layout)")
        print(f"       • Leadership data in non-text format (images, complex HTML)")
    else:
        print(f"  🟢 Need to investigate further - check logs for extraction details")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    debug_connatix_leadership()
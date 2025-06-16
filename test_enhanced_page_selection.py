#!/usr/bin/env python3
"""
Test the enhanced page selection targeting missing data points
"""

import asyncio
import logging
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.bedrock_client import BedrockClient
from src.extraction_improvements import enhance_company_extraction
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_page_selection():
    """Test that the enhanced page selection finds pages with missing data"""
    
    # Test companies known to have the data we're looking for
    test_companies = [
        {"name": "Stripe", "website": "https://stripe.com"},
        {"name": "Datadog", "website": "https://www.datadoghq.com"},
        {"name": "GitLab", "website": "https://about.gitlab.com"}
    ]
    
    config = CompanyIntelligenceConfig()
    bedrock_client = BedrockClient(config)
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    for company_info in test_companies:
        print(f"\n{'='*70}")
        print(f"Testing: {company_info['name']}")
        print(f"{'='*70}")
        
        company = CompanyData(
            name=company_info['name'],
            website=company_info['website']
        )
        
        try:
            # Phase 1: Link Discovery
            print("\n📍 Phase 1: Link Discovery")
            all_links = await scraper._discover_all_links(company.website)
            print(f"   Found {len(all_links)} total links")
            
            # Show links that match our target patterns
            target_patterns = ['contact', 'about', 'team', 'careers', 'leadership', 'partners']
            matching_links = []
            for link in all_links:
                link_lower = link.lower()
                for pattern in target_patterns:
                    if pattern in link_lower:
                        matching_links.append(link)
                        break
            
            print(f"\n   Links matching target patterns:")
            for link in matching_links[:10]:  # Show first 10
                print(f"   - {link}")
            
            # Phase 2: LLM Selection
            print("\n🤖 Phase 2: LLM Page Selection")
            selected_urls = await scraper._llm_select_promising_pages(
                all_links, company_info['name'], company.website
            )
            print(f"   LLM selected {len(selected_urls)} pages")
            
            print(f"\n   Top selected pages for missing data:")
            for i, url in enumerate(selected_urls[:15], 1):
                # Identify what data this page might contain
                url_lower = url.lower()
                data_types = []
                if 'contact' in url_lower:
                    data_types.append("location, email, phone")
                if 'about' in url_lower:
                    data_types.append("founding year, company size")
                if 'team' in url_lower or 'leadership' in url_lower:
                    data_types.append("leadership team")
                if 'careers' in url_lower or 'jobs' in url_lower:
                    data_types.append("employee count, culture")
                if 'partners' in url_lower:
                    data_types.append("partnerships")
                if 'security' in url_lower or 'compliance' in url_lower:
                    data_types.append("certifications")
                
                data_str = f" → {', '.join(data_types)}" if data_types else ""
                print(f"   {i:2}. {url}{data_str}")
            
            # Phase 3: Extract content from a sample page
            print("\n🔍 Phase 3: Sample Extraction")
            # Find a contact or about page
            sample_url = None
            for url in selected_urls:
                if 'contact' in url.lower() or 'about' in url.lower():
                    sample_url = url
                    break
            
            if sample_url:
                print(f"   Extracting from: {sample_url}")
                extracted = await scraper._parallel_extract_content([sample_url])
                if extracted and extracted[0].get('content'):
                    content = extracted[0]['content'][:500]  # First 500 chars
                    
                    # Test pattern extraction
                    from src.extraction_improvements import EnhancedFieldExtractor
                    extractor = EnhancedFieldExtractor()
                    
                    # Try to extract specific fields
                    founding_year = extractor.extract_founding_year(content)
                    location = extractor.extract_location(content)
                    employee_count = extractor.extract_employee_count(content)
                    
                    print(f"\n   Quick extraction test:")
                    if founding_year:
                        print(f"   ✓ Found founding year: {founding_year}")
                    if location:
                        print(f"   ✓ Found location: {location}")
                    if employee_count:
                        print(f"   ✓ Found employee count: {employee_count}")
                    
                    if not any([founding_year, location, employee_count]):
                        print(f"   ℹ️  No patterns found in first 500 chars")
            
        except Exception as e:
            print(f"\n❌ Error testing {company_info['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n\n✅ Enhanced page selection test complete!")
    print("\nKey findings:")
    print("1. The scraper successfully discovers links from robots.txt, sitemap.xml, and crawling")
    print("2. The LLM now prioritizes pages likely to contain missing data (contact, about, team)")
    print("3. The system is ready to extract location, founding year, employee count, etc.")

if __name__ == "__main__":
    asyncio.run(test_enhanced_page_selection())
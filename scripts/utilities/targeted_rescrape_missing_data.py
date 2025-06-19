#!/usr/bin/env python3
"""
Phase 3: Targeted Re-scraping for Missing Data
Re-scrapes companies that lack both critical fields AND raw content
"""

import os
import sys
from datetime import datetime
import asyncio

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🎯 Targeted Re-scraping for Missing Data")
    print("=" * 60)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Theodore components
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        
        # Initialize components
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        print("✅ Theodore pipeline initialized")
        
        # Fetch companies with missing data
        print("\n📊 Identifying companies needing re-scraping...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Identify re-scraping candidates
        rescraping_candidates = []
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            website = metadata.get('website', '')
            raw_content = metadata.get('raw_content', '')
            
            # Check for missing critical fields
            missing_fields = []
            if not metadata.get('founding_year'):
                missing_fields.append('founding_year')
            if not metadata.get('location'):
                missing_fields.append('location')  
            if not metadata.get('leadership_team'):
                missing_fields.append('leadership_team')
            if not metadata.get('contact_info') or metadata.get('contact_info') == '':
                missing_fields.append('contact_info')
            if not metadata.get('employee_count_range'):
                missing_fields.append('employee_count_range')
            
            # Priority: Companies with missing fields AND little/no raw content
            if missing_fields and (not raw_content or len(raw_content) < 500) and website:
                rescraping_candidates.append({
                    'id': match.id,
                    'name': company_name,
                    'website': website,
                    'metadata': metadata,
                    'missing_fields': missing_fields,
                    'content_length': len(raw_content),
                    'priority': len(missing_fields) + (1 if not raw_content else 0)
                })
        
        # Sort by priority (most missing fields + no content = highest priority)
        rescraping_candidates.sort(key=lambda x: x['priority'], reverse=True)
        
        print(f"📈 Re-scraping Analysis:")
        print(f"   Total companies: {len(query_result.matches)}")
        print(f"   Companies needing re-scraping: {len(rescraping_candidates)}")
        print(f"   Companies with no raw content: {sum(1 for c in rescraping_candidates if not c['metadata'].get('raw_content'))}")
        
        if not rescraping_candidates:
            print("✅ All companies have sufficient data!")
            return
        
        # Process a batch of high-priority candidates
        batch_size = min(2, len(rescraping_candidates))  # Start with 2 companies for faster testing
        companies_to_rescrape = rescraping_candidates[:batch_size]
        
        print(f"\n🔄 Re-scraping {len(companies_to_rescrape)} highest priority companies...")
        print(f"   (Companies with {companies_to_rescrape[0]['priority']}+ missing fields/content issues)")
        
        successful_rescrapings = 0
        
        for i, company_info in enumerate(companies_to_rescrape):
            company_name = company_info['name']
            website = company_info['website']
            missing_fields = company_info['missing_fields']
            
            print(f"\n[{i+1}/{len(companies_to_rescrape)}] 🌐 Re-scraping: {company_name}")
            print(f"   Website: {website}")
            print(f"   Missing: {', '.join(missing_fields)}")
            print(f"   Current content: {company_info['content_length']} chars")
            
            try:
                # Perform intelligent re-scraping using main pipeline
                scraped_company = pipeline.process_single_company(company_name, website)
                
                if scraped_company:
                    enhanced_metadata = company_info['metadata'].copy()
                    
                    # Update with newly scraped data
                    if scraped_company.raw_content:
                        enhanced_metadata['raw_content'] = scraped_company.raw_content
                    if scraped_company.ai_summary:
                        enhanced_metadata['ai_summary'] = scraped_company.ai_summary
                    if scraped_company.company_description:
                        enhanced_metadata['company_description'] = scraped_company.company_description
                    
                    # Update structured fields if found
                    fields_updated = []
                    for field in ['founding_year', 'location', 'leadership_team', 'contact_info', 'employee_count_range']:
                        scraped_value = getattr(scraped_company, field, None)
                        if scraped_value and not enhanced_metadata.get(field):
                            enhanced_metadata[field] = scraped_value
                            fields_updated.append(field)
                    
                    # Add re-scraping metadata
                    enhanced_metadata['rescraping_timestamp'] = datetime.now().isoformat()
                    enhanced_metadata['rescraping_reason'] = 'missing_fields_and_content'
                    enhanced_metadata['rescraping_fields_updated'] = fields_updated
                    
                    # Update in Pinecone
                    pipeline.pinecone_client.index.update(
                        id=company_info['id'],
                        set_metadata=enhanced_metadata
                    )
                    
                    successful_rescrapings += 1
                    new_content_length = len(scraped_company.raw_content or '')
                    
                    print(f"   ✅ Re-scraping successful!")
                    print(f"      Content: {company_info['content_length']} → {new_content_length} chars")
                    if fields_updated:
                        print(f"      Fields updated: {', '.join(fields_updated)}")
                    else:
                        print(f"      Enhanced content available for AI extraction")
                        
                else:
                    print(f"   ❌ Re-scraping failed: No data returned")
                    
            except Exception as e:
                print(f"   ❌ Error during re-scraping: {e}")
        
        print(f"\n🎉 Re-scraping Summary:")
        print(f"   Companies processed: {len(companies_to_rescrape)}")
        print(f"   Successful re-scrapings: {successful_rescrapings}")
        print(f"   Success rate: {round(successful_rescrapings/len(companies_to_rescrape)*100, 1)}%")
        
        if successful_rescrapings > 0:
            print(f"\n💡 Next Steps:")
            print(f"   1. Run hybrid field enhancement again on re-scraped companies")
            print(f"   2. Enhanced raw content should improve pattern matching")
            print(f"   3. AI enhancement will have better source material")
            print(f"\n   Command: python3 scripts/utilities/hybrid_field_enhancement.py")
            
        print(f"\n📊 Remaining candidates for future batches: {len(rescraping_candidates) - batch_size}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
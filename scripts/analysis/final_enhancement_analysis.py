#!/usr/bin/env python3
"""
Final analysis of enhancement progress: what we gained vs what's still missing.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def final_enhancement_analysis():
    """Comprehensive analysis of enhancement progress"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 90)
    print("FINAL ENHANCEMENT ANALYSIS: WHAT WE GAINED VS WHAT'S STILL MISSING")
    print("=" * 90)
    
    # Get all companies from database
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    # Define all fields we're tracking
    basic_fields = ['company_name', 'website', 'industry', 'business_model', 'company_size', 'target_market']
    scraping_fields = ['scrape_status', 'pages_crawled', 'raw_content', 'crawl_duration']
    enhanced_fields = [
        'founding_year', 'location', 'employee_count_range', 'company_description',
        'value_proposition', 'leadership_team', 'contact_info', 'social_media',
        'tech_stack', 'key_services', 'products_services_offered', 'competitive_advantages',
        'funding_status', 'partnerships', 'awards', 'recent_news_events', 'company_culture'
    ]
    
    all_fields = basic_fields + scraping_fields + enhanced_fields
    
    print(f"📊 ANALYSIS OF {len(companies)} COMPANIES")
    print(f"🎯 Tracking {len(all_fields)} total fields:")
    print(f"   • Basic fields: {len(basic_fields)}")
    print(f"   • Scraping fields: {len(scraping_fields)}")
    print(f"   • Enhanced fields: {len(enhanced_fields)}")
    print()
    
    # Analyze field success rates
    field_stats = {}
    
    for field in all_fields:
        filled_count = 0
        for company in companies[:10]:  # First 10 companies
            metadata = company.get('metadata', {})
            value = metadata.get(field)
            
            # Check if field has meaningful data
            if value is not None:
                if isinstance(value, str) and value.strip() and value.lower() not in ['unknown', 'not specified', 'n/a']:
                    filled_count += 1
                elif isinstance(value, (list, dict)) and len(value) > 0:
                    filled_count += 1
                elif isinstance(value, (int, float)) and value > 0:
                    filled_count += 1
                elif isinstance(value, bool):
                    filled_count += 1
        
        success_rate = (filled_count / min(10, len(companies))) * 100
        field_stats[field] = {
            'filled': filled_count,
            'total': min(10, len(companies)),
            'success_rate': success_rate
        }
    
    # WHAT WE GAINED
    print("🎉 WHAT WE SUCCESSFULLY GAINED:")
    print("=" * 50)
    
    successful_fields = {k: v for k, v in field_stats.items() if v['success_rate'] >= 50}
    if successful_fields:
        for field, stats in sorted(successful_fields.items(), key=lambda x: x[1]['success_rate'], reverse=True):
            category = "Basic" if field in basic_fields else "Scraping" if field in scraping_fields else "Enhanced"
            print(f"✅ {field:30} {stats['success_rate']:3.0f}% ({stats['filled']}/{stats['total']}) - {category}")
    else:
        print("❌ No fields achieved 50%+ success rate")
    
    print()
    
    # WHAT'S STILL MISSING
    print("❌ WHAT'S STILL MISSING:")
    print("=" * 50)
    
    missing_fields = {k: v for k, v in field_stats.items() if v['success_rate'] < 50}
    for field, stats in sorted(missing_fields.items(), key=lambda x: x[1]['success_rate']):
        category = "Basic" if field in basic_fields else "Scraping" if field in scraping_fields else "Enhanced"
        if stats['success_rate'] == 0:
            print(f"🔴 {field:30} {stats['success_rate']:3.0f}% ({stats['filled']}/{stats['total']}) - {category} - NEVER EXTRACTED")
        else:
            print(f"🟡 {field:30} {stats['success_rate']:3.0f}% ({stats['filled']}/{stats['total']}) - {category} - PARTIALLY EXTRACTED")
    
    print()
    
    # SUMMARY STATISTICS
    print("📈 SUMMARY STATISTICS:")
    print("=" * 50)
    
    basic_success = sum(1 for f in basic_fields if field_stats[f]['success_rate'] >= 50)
    scraping_success = sum(1 for f in scraping_fields if field_stats[f]['success_rate'] >= 50)
    enhanced_success = sum(1 for f in enhanced_fields if field_stats[f]['success_rate'] >= 50)
    
    total_success = len(successful_fields)
    total_fields = len(all_fields)
    overall_success_rate = (total_success / total_fields) * 100
    
    print(f"Basic fields successful:    {basic_success:2d}/{len(basic_fields):2d} ({basic_success/len(basic_fields)*100:.0f}%)")
    print(f"Scraping fields successful: {scraping_success:2d}/{len(scraping_fields):2d} ({scraping_success/len(scraping_fields)*100:.0f}%)")
    print(f"Enhanced fields successful: {enhanced_success:2d}/{len(enhanced_fields):2d} ({enhanced_success/len(enhanced_fields)*100:.0f}%)")
    print(f"Overall success rate:       {total_success:2d}/{total_fields:2d} ({overall_success_rate:.0f}%)")
    
    # CRITICAL ISSUES IDENTIFIED
    print("\n🔍 CRITICAL ISSUES IDENTIFIED:")
    print("=" * 50)
    
    # Check raw content issue
    raw_content_success = field_stats['raw_content']['success_rate']
    if raw_content_success == 0:
        print("🚨 CRITICAL: raw_content is 0% - no content is being stored for analysis")
    
    # Check enhanced fields
    if enhanced_success == 0:
        print("🚨 CRITICAL: Enhanced fields are 0% - enhanced extraction pipeline not working")
    
    # Check pages crawled vs raw content
    pages_success = field_stats['pages_crawled']['success_rate']
    if pages_success > 0 and raw_content_success == 0:
        print("🚨 CRITICAL: Pages crawled but no raw content - data persistence issue")
    
    # SPECIFIC EXAMPLES
    print("\n💎 EXAMPLES FROM ACTUAL DATA:")
    print("=" * 50)
    
    for i, company in enumerate(companies[:3], 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        
        print(f"\n{i}. {company_name}:")
        
        # Show what we have
        has_data = []
        for field in ['scrape_status', 'pages_crawled', 'industry', 'business_model']:
            value = metadata.get(field)
            if value:
                if field == 'pages_crawled':
                    has_data.append(f"{field}: {len(value)} pages")
                else:
                    has_data.append(f"{field}: {value}")
        
        if has_data:
            print(f"   ✅ Has: {' | '.join(has_data)}")
        
        # Show what's missing
        missing_critical = []
        for field in ['raw_content', 'founding_year', 'location', 'leadership_team']:
            value = metadata.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_critical.append(field)
        
        if missing_critical:
            print(f"   ❌ Missing: {', '.join(missing_critical)}")
    
    # NEXT STEPS
    print("\n🚀 RECOMMENDED NEXT STEPS:")
    print("=" * 50)
    print("1. 🔧 Fix raw_content storage - data is scraped but not persisted")
    print("2. 🧠 Fix AI analysis application - bedrock analysis not being stored")
    print("3. 🔄 Re-run enhanced extraction pipeline once storage is fixed")
    print("4. 📊 Focus on leadership_team, founding_year, location as high-value fields")
    print("5. 🎯 Target 80%+ success rate for enhanced fields")
    
    print("\n" + "=" * 90)

if __name__ == "__main__":
    final_enhancement_analysis()
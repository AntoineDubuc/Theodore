#!/usr/bin/env python3
"""
Reprocess the 10 companies in the details spreadsheet and show comprehensive before/after comparison.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def reprocess_ten_companies():
    """Reprocess the 10 companies and show detailed improvements"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 100)
    print("REPROCESSING 10 COMPANIES WITH ENHANCED EXTRACTION")
    print("=" * 100)
    
    # Get companies from database (first 10)
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    first_ten = companies[:10]
    
    print(f"📊 Found {len(companies)} total companies, processing first 10")
    print()
    
    # Enhanced fields to track
    enhanced_fields = [
        'raw_content', 'location', 'founding_year', 'employee_count_range',
        'leadership_team', 'contact_info', 'social_media', 'value_proposition',
        'tech_stack', 'key_services', 'competitive_advantages', 'partnerships',
        'products_services_offered', 'funding_status', 'awards', 'company_culture'
    ]
    
    def get_field_data(metadata, field):
        """Extract and format field data"""
        value = metadata.get(field)
        if not value:
            return None, "Empty"
        
        if field == 'raw_content':
            if isinstance(value, str) and value.strip():
                return len(value), f"{len(value):,} chars"
            return None, "Empty"
        elif field in ['contact_info', 'social_media']:
            if isinstance(value, str) and value.strip():
                try:
                    import json
                    parsed = json.loads(value)
                    if parsed and any(v and str(v).lower() != 'unknown' for v in parsed.values()):
                        return parsed, "Structured data"
                    return None, "Unknown values only"
                except:
                    return value, "String data"
            return None, "Empty"
        elif field in ['leadership_team', 'tech_stack', 'key_services', 'competitive_advantages', 'partnerships', 'products_services_offered', 'awards']:
            if isinstance(value, str) and value.strip():
                items = [item.strip() for item in value.split(',') if item.strip()]
                if items and any(item.lower() != 'unknown' for item in items):
                    return items, f"{len(items)} items"
                return None, "Unknown values only"
            elif isinstance(value, list) and value:
                if any(str(item).lower() != 'unknown' for item in value):
                    return value, f"{len(value)} items"
                return None, "Unknown values only"
            return None, "Empty"
        else:
            if isinstance(value, str) and value.strip() and value.lower() not in ['unknown', 'not specified', 'n/a']:
                return value, str(value)[:50] + ("..." if len(str(value)) > 50 else "")
            elif isinstance(value, (int, float)) and value > 0:
                return value, str(value)
            return None, "Unknown/Empty"
    
    results = []
    
    for i, company in enumerate(first_ten, 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        website = metadata.get('website', 'No website')
        company_id = company.get('id')
        
        print(f"\n{'='*80}")
        print(f"{i:2d}. PROCESSING: {company_name}")
        print(f"{'='*80}")
        print(f"Website: {website}")
        print(f"ID: {company_id}")
        
        # Capture BEFORE state
        before_data = {}
        before_filled = 0
        
        print(f"\n📊 BEFORE STATE:")
        for field in enhanced_fields:
            data, display = get_field_data(metadata, field)
            before_data[field] = data
            if data is not None:
                before_filled += 1
                print(f"   ✅ {field:25}: {display}")
            else:
                print(f"   ❌ {field:25}: {display}")
        
        print(f"\n   BEFORE SUMMARY: {before_filled}/{len(enhanced_fields)} fields filled")
        
        # Reprocess the company
        print(f"\n🔄 Reprocessing {company_name}...")
        try:
            # Determine website URL
            if website and website != 'No website' and not website.startswith('http'):
                website_url = f"https://{website}"
            elif website and website.startswith('http'):
                website_url = website
            else:
                website_url = f"https://{company_name.lower().replace(' ', '').replace('.com', '')}.com"
            
            # Reprocess with enhanced extraction
            updated_company = pipeline.process_single_company(company_name, website_url)
            
            # Get fresh data from database
            fresh_companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=20)
            fresh_company = None
            
            for comp in fresh_companies:
                if comp.get('metadata', {}).get('company_name') == company_name:
                    fresh_company = comp
                    break
            
            if fresh_company:
                fresh_metadata = fresh_company.get('metadata', {})
                
                # Capture AFTER state
                after_data = {}
                after_filled = 0
                improvements = []
                
                print(f"\n📊 AFTER STATE:")
                for field in enhanced_fields:
                    data, display = get_field_data(fresh_metadata, field)
                    after_data[field] = data
                    
                    if data is not None:
                        after_filled += 1
                        if before_data[field] is None:
                            improvements.append(field)
                            print(f"   🆕 {field:25}: {display}")
                        else:
                            print(f"   ✅ {field:25}: {display}")
                    else:
                        print(f"   ❌ {field:25}: {display}")
                
                improvement_count = after_filled - before_filled
                
                print(f"\n   AFTER SUMMARY: {after_filled}/{len(enhanced_fields)} fields filled")
                print(f"   IMPROVEMENT: {improvement_count:+d} fields ({improvement_count/len(enhanced_fields)*100:+.1f}%)")
                
                if improvements:
                    print(f"   🆕 NEW FIELDS: {', '.join(improvements)}")
                    
                    # Show key new data
                    key_improvements = []
                    for field in ['location', 'leadership_team', 'partnerships', 'tech_stack']:
                        if field in improvements and after_data[field]:
                            if field == 'location':
                                key_improvements.append(f"📍 {after_data[field]}")
                            elif field == 'leadership_team':
                                leaders = after_data[field][:2] if isinstance(after_data[field], list) else [str(after_data[field])[:50]]
                                key_improvements.append(f"👥 {', '.join(leaders)}")
                            elif field == 'partnerships':
                                partners = after_data[field][:3] if isinstance(after_data[field], list) else [str(after_data[field])[:50]]
                                key_improvements.append(f"🤝 {', '.join(partners)}")
                            elif field == 'tech_stack':
                                tech = after_data[field][:3] if isinstance(after_data[field], list) else [str(after_data[field])[:50]]
                                key_improvements.append(f"💻 {', '.join(tech)}")
                    
                    if key_improvements:
                        print(f"   💎 KEY DATA: {' | '.join(key_improvements)}")
                else:
                    print(f"   ⚠️  No new fields extracted")
                
                # Store results
                results.append({
                    'rank': i,
                    'company_name': company_name,
                    'website': website_url,
                    'before_filled': before_filled,
                    'after_filled': after_filled,
                    'improvement': improvement_count,
                    'improvement_pct': (improvement_count/len(enhanced_fields)*100),
                    'new_fields': improvements,
                    'key_data': {
                        'location': after_data.get('location'),
                        'leadership_team': after_data.get('leadership_team'),
                        'partnerships': after_data.get('partnerships'),
                        'tech_stack': after_data.get('tech_stack'),
                        'raw_content_length': len(fresh_metadata.get('raw_content', ''))
                    }
                })
                
            else:
                print(f"❌ Could not find fresh data for {company_name}")
                
        except Exception as e:
            print(f"❌ Error processing {company_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate comprehensive summary
    print(f"\n\n{'='*100}")
    print("COMPREHENSIVE ENHANCEMENT RESULTS")
    print(f"{'='*100}")
    
    if results:
        total_improvements = sum(r['improvement'] for r in results)
        companies_improved = len([r for r in results if r['improvement'] > 0])
        avg_before = sum(r['before_filled'] for r in results) / len(results)
        avg_after = sum(r['after_filled'] for r in results) / len(results)
        
        print(f"📊 OVERALL STATISTICS:")
        print(f"   Companies processed: {len(results)}")
        print(f"   Companies improved: {companies_improved}/{len(results)} ({companies_improved/len(results)*100:.0f}%)")
        print(f"   Total new fields: {total_improvements}")
        print(f"   Average completeness: {avg_before:.1f} → {avg_after:.1f} fields ({avg_after-avg_before:+.1f})")
        print(f"   Average improvement: {(avg_after-avg_before)/len(enhanced_fields)*100:+.1f}%")
        
        print(f"\n🏆 TOP PERFORMERS:")
        sorted_results = sorted(results, key=lambda x: x['improvement'], reverse=True)
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"   {i}. {result['company_name']:30} +{result['improvement']:2d} fields ({result['improvement_pct']:+4.1f}%)")
            if result['key_data']['location']:
                print(f"      📍 Location: {result['key_data']['location']}")
            if result['key_data']['leadership_team']:
                leaders = result['key_data']['leadership_team'][:2] if isinstance(result['key_data']['leadership_team'], list) else [str(result['key_data']['leadership_team'])[:50]]
                print(f"      👥 Leadership: {', '.join(leaders)}")
        
        print(f"\n❌ STILL CHALLENGING FIELDS:")
        field_success = {}
        for field in enhanced_fields:
            success_count = sum(1 for r in results if field in r['new_fields'] or any(field in comp['metadata'] for comp in first_ten))
            field_success[field] = success_count
        
        challenging_fields = sorted(field_success.items(), key=lambda x: x[1])[:5]
        for field, count in challenging_fields:
            if count < len(results) * 0.7:  # Less than 70% success
                print(f"   {field:25}: {count}/{len(results)} companies ({count/len(results)*100:.0f}%)")
        
        print(f"\n💎 SAMPLE SUCCESS STORIES:")
        for result in sorted_results[:2]:
            if result['improvement'] > 0:
                print(f"\n   🏢 {result['company_name']}:")
                if result['key_data']['raw_content_length'] > 0:
                    print(f"      📄 Scraped: {result['key_data']['raw_content_length']:,} chars")
                if result['key_data']['location']:
                    print(f"      📍 Location: {result['key_data']['location']}")
                if result['key_data']['partnerships']:
                    partners = result['key_data']['partnerships'][:3] if isinstance(result['key_data']['partnerships'], list) else [str(result['key_data']['partnerships'])]
                    print(f"      🤝 Partners: {', '.join(partners)}")
    
    else:
        print("❌ No results to analyze")
    
    print(f"\n" + "=" * 100)
    print("🎯 CONCLUSION: Enhanced extraction pipeline has been executed.")
    print("   Check the web UI at http://localhost:5002 to see updated company details!")
    print("=" * 100)

if __name__ == "__main__":
    reprocess_ten_companies()
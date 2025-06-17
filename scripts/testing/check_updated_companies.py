#!/usr/bin/env python3
"""
Check the current state of companies after reprocessing to see what we gained.
"""

import os
import sys
import json
from datetime import datetime

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def check_updated_companies():
    """Check current state of companies"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("CURRENT STATE AFTER REPROCESSING")
    print("=" * 80)
    
    # Get all companies
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=25)
    
    # Enhanced fields to check
    enhanced_fields = [
        'raw_content', 'location', 'founding_year', 'leadership_team',
        'contact_info', 'social_media', 'value_proposition', 'tech_stack',
        'key_services', 'competitive_advantages', 'partnerships', 'awards'
    ]
    
    def get_field_value(metadata, field):
        """Get meaningful field value"""
        value = metadata.get(field)
        if not value:
            return None
        
        if field == 'raw_content':
            if isinstance(value, str) and value.strip():
                return len(value)
            return None
        elif field in ['contact_info', 'social_media']:
            if isinstance(value, str) and value.strip():
                try:
                    parsed = json.loads(value)
                    if parsed and any(v and str(v).lower() != 'unknown' for v in parsed.values()):
                        return parsed
                except:
                    pass
            return None
        elif field in ['leadership_team', 'tech_stack', 'key_services', 'competitive_advantages', 'partnerships', 'awards']:
            if isinstance(value, str) and value.strip():
                items = [item.strip() for item in value.split(',') if item.strip()]
                if items and any(item.lower() != 'unknown' for item in items):
                    return items
            elif isinstance(value, list) and value:
                if any(str(item).lower() != 'unknown' for item in value):
                    return value
            return None
        else:
            if isinstance(value, str) and value.strip() and value.lower() not in ['unknown', 'not specified', 'n/a']:
                return value
            elif isinstance(value, (int, float)) and value > 0:
                return value
            return None
    
    # Analyze recently updated companies (last 2 hours)
    recent_cutoff = datetime.now().replace(hour=datetime.now().hour-2)
    recent_companies = []
    
    for company in companies:
        metadata = company.get('metadata', {})
        last_updated = metadata.get('last_updated', '')
        
        if last_updated:
            try:
                update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                if update_time.replace(tzinfo=None) > recent_cutoff:
                    recent_companies.append(company)
            except:
                pass
    
    print(f"📊 Found {len(companies)} total companies, {len(recent_companies)} recently updated")
    print()
    
    # Show overall field success rates
    field_stats = {}
    for field in enhanced_fields:
        success_count = 0
        for company in companies[:10]:  # First 10
            metadata = company.get('metadata', {})
            if get_field_value(metadata, field) is not None:
                success_count += 1
        
        field_stats[field] = {
            'success_count': success_count,
            'success_rate': (success_count / 10) * 100
        }
    
    print("🏆 ENHANCED FIELDS SUCCESS RATES (Top 10 Companies):")
    print("-" * 60)
    
    # Sort by success rate
    sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['success_rate'], reverse=True)
    
    for field, stats in sorted_fields:
        success_rate = stats['success_rate']
        if success_rate >= 50:
            print(f"✅ {field:25} {success_rate:5.0f}% ({stats['success_count']}/10)")
        elif success_rate > 0:
            print(f"🟡 {field:25} {success_rate:5.0f}% ({stats['success_count']}/10)")
        else:
            print(f"❌ {field:25} {success_rate:5.0f}% ({stats['success_count']}/10)")
    
    print("\n💎 COMPANIES WITH BEST DATA:")
    print("-" * 60)
    
    # Find companies with most enhanced fields
    company_scores = []
    for company in companies[:10]:
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', 'Unknown')
        
        filled_count = 0
        filled_fields = []
        for field in enhanced_fields:
            value = get_field_value(metadata, field)
            if value is not None:
                filled_count += 1
                filled_fields.append(field)
        
        company_scores.append({
            'name': company_name,
            'filled_count': filled_count,
            'filled_fields': filled_fields,
            'metadata': metadata
        })
    
    # Sort by filled count
    company_scores.sort(key=lambda x: x['filled_count'], reverse=True)
    
    for i, company in enumerate(company_scores[:5], 1):
        print(f"\n{i}. {company['name']:30} ({company['filled_count']}/{len(enhanced_fields)} fields)")
        
        # Show key data
        metadata = company['metadata']
        raw_content_len = len(metadata.get('raw_content', ''))
        if raw_content_len > 0:
            print(f"   📄 Raw content: {raw_content_len:,} chars")
        
        location = get_field_value(metadata, 'location')
        if location:
            print(f"   📍 Location: {location}")
        
        leadership = get_field_value(metadata, 'leadership_team')
        if leadership:
            leaders = leadership[:2] if isinstance(leadership, list) else [str(leadership)[:50]]
            print(f"   👥 Leadership: {', '.join(leaders)}")
        
        partnerships = get_field_value(metadata, 'partnerships')
        if partnerships:
            partners = partnerships[:3] if isinstance(partnerships, list) else [str(partnerships)[:50]]
            print(f"   🤝 Partners: {', '.join(partners)}")
        
        tech_stack = get_field_value(metadata, 'tech_stack')
        if tech_stack:
            tech = tech_stack[:3] if isinstance(tech_stack, list) else [str(tech_stack)[:50]]
            print(f"   💻 Tech: {', '.join(tech)}")
    
    print(f"\n🎯 KEY ACHIEVEMENTS:")
    print("-" * 60)
    
    # Count specific successes
    companies_with_location = sum(1 for c in companies[:10] if get_field_value(c.get('metadata', {}), 'location'))
    companies_with_leadership = sum(1 for c in companies[:10] if get_field_value(c.get('metadata', {}), 'leadership_team'))
    companies_with_partnerships = sum(1 for c in companies[:10] if get_field_value(c.get('metadata', {}), 'partnerships'))
    companies_with_content = sum(1 for c in companies[:10] if get_field_value(c.get('metadata', {}), 'raw_content'))
    
    print(f"📍 Location data: {companies_with_location}/10 companies ({companies_with_location*10}%)")
    print(f"👥 Leadership data: {companies_with_leadership}/10 companies ({companies_with_leadership*10}%)")
    print(f"🤝 Partnership data: {companies_with_partnerships}/10 companies ({companies_with_partnerships*10}%)")
    print(f"📄 Raw content: {companies_with_content}/10 companies ({companies_with_content*10}%)")
    
    print(f"\n🔄 RECOMMENDATION:")
    print("-" * 60)
    print("Check the web interface at http://localhost:5002")
    print("Click on companies to see enhanced data in the details view!")
    print("The spreadsheet should now show significantly more data.")
    
    print("=" * 80)

if __name__ == "__main__":
    check_updated_companies()
#!/usr/bin/env python3
"""
Analyze specific data improvements - what exactly did we gain.
"""

import os
import sys
from typing import Dict, Any, List

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def analyze_specific_improvements():
    """Show exactly what new data we extracted"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get all companies and analyze their data richness
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=10)
    
    print("=" * 80)
    print("SPECIFIC DATA IMPROVEMENTS ANALYSIS")
    print("=" * 80)
    
    # Define all possible fields we extract
    all_fields = [
        'company_name', 'website', 'industry', 'business_model', 'company_size',
        'company_stage', 'founding_year', 'location', 'employee_count_range',
        'company_description', 'value_proposition', 'target_market', 'company_culture',
        'key_services', 'products_services_offered', 'pain_points', 'competitive_advantages',
        'tech_stack', 'tech_sophistication', 'has_chat_widget', 'has_forms',
        'funding_status', 'funding_stage_detailed', 'has_job_listings', 'job_listings_count',
        'leadership_team', 'key_decision_makers', 'awards', 'certifications', 'partnerships',
        'contact_info', 'social_media', 'recent_news', 'recent_news_events'
    ]
    
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return value > 0
        return bool(value)
    
    # Analyze each company's data richness
    rich_companies = []
    poor_companies = []
    
    for company in companies:
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', 'Unknown')
        
        filled_count = 0
        filled_fields = []
        sample_data = {}
        
        for field in all_fields:
            value = metadata.get(field)
            if is_filled(value):
                filled_count += 1
                filled_fields.append(field)
                # Store sample data for rich fields
                if field in ['company_description', 'value_proposition', 'target_market', 'competitive_advantages', 'tech_stack']:
                    if isinstance(value, str) and len(value) > 20:
                        sample_data[field] = value[:100] + "..." if len(value) > 100 else value
                    else:
                        sample_data[field] = str(value)
        
        completeness = (filled_count / len(all_fields)) * 100
        
        company_data = {
            'name': company_name,
            'filled_count': filled_count,
            'completeness': completeness,
            'filled_fields': filled_fields,
            'sample_data': sample_data
        }
        
        if completeness > 20:  # Companies with meaningful data
            rich_companies.append(company_data)
        else:
            poor_companies.append(company_data)
    
    # Sort by richness
    rich_companies.sort(key=lambda x: x['completeness'], reverse=True)
    poor_companies.sort(key=lambda x: x['completeness'], reverse=True)
    
    print("🎯 COMPANIES WITH ENHANCED DATA EXTRACTION:")
    print("=" * 80)
    
    for i, company in enumerate(rich_companies, 1):
        print(f"\n{i}. {company['name']}")
        print(f"   Data Completeness: {company['completeness']:.1f}% ({company['filled_count']}/{len(all_fields)} fields)")
        
        # Show what specific valuable data we extracted
        if company['sample_data']:
            print("   🔍 EXTRACTED INTELLIGENCE:")
            for field, value in company['sample_data'].items():
                field_display = field.replace('_', ' ').title()
                print(f"   • {field_display}: {value}")
        
        # Show which categories of data we captured
        categories = {
            'Basic Info': ['company_name', 'website', 'industry', 'business_model'],
            'Business Intelligence': ['company_description', 'value_proposition', 'target_market', 'competitive_advantages'],
            'Technical': ['tech_stack', 'tech_sophistication', 'has_chat_widget', 'has_forms'],
            'Corporate': ['company_size', 'company_stage', 'founding_year', 'location', 'employee_count_range'],
            'Contact & Social': ['contact_info', 'social_media', 'leadership_team'],
            'Market Position': ['funding_status', 'awards', 'certifications', 'partnerships']
        }
        
        captured_categories = []
        for category, fields in categories.items():
            if any(field in company['filled_fields'] for field in fields):
                captured_categories.append(category)
        
        if captured_categories:
            print(f"   📊 Data Categories: {', '.join(captured_categories)}")
    
    print(f"\n\n📉 COMPANIES WITH MINIMAL DATA:")
    print("=" * 80)
    
    for company in poor_companies:
        print(f"• {company['name']}: {company['completeness']:.1f}% ({company['filled_count']}/{len(all_fields)} fields)")
    
    # Overall statistics
    if rich_companies:
        avg_rich = sum(c['completeness'] for c in rich_companies) / len(rich_companies)
        print(f"\n📈 ENHANCEMENT SUCCESS METRICS:")
        print(f"• Companies with enhanced data: {len(rich_companies)}")
        print(f"• Average completeness (enhanced): {avg_rich:.1f}%")
        print(f"• Companies needing reprocessing: {len(poor_companies)}")
        
        # Most successfully extracted fields
        field_success = {}
        for company in rich_companies:
            for field in company['filled_fields']:
                field_success[field] = field_success.get(field, 0) + 1
        
        successful_fields = sorted(field_success.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 MOST SUCCESSFULLY EXTRACTED FIELDS:")
        for field, count in successful_fields[:8]:
            field_display = field.replace('_', ' ').title()
            success_rate = (count / len(rich_companies)) * 100
            print(f"• {field_display}: {success_rate:.0f}% success rate ({count}/{len(rich_companies)} companies)")
    
    print("\n" + "=" * 80)
    print("🚀 KEY IMPROVEMENTS ACHIEVED:")
    print("• Enhanced AI extraction vs basic web scraping")
    print("• 34-field comprehensive business intelligence model")
    print("• Smart content analysis for value propositions and competitive advantages")
    print("• Technical sophistication assessment")
    print("• Business model and market positioning analysis")
    print("=" * 80)

if __name__ == "__main__":
    analyze_specific_improvements()
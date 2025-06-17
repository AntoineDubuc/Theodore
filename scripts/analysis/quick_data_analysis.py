#!/usr/bin/env python3
"""
Quick analysis of current data completeness in the database.
Shows what fields are filled vs empty for the companies we have.
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

def analyze_data_completeness():
    """Analyze current data completeness"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Key fields to analyze
    key_fields = [
        'company_name', 'website', 'industry', 'business_model', 'company_size',
        'company_stage', 'founding_year', 'location', 'employee_count_range',
        'company_description', 'value_proposition', 'target_market', 'company_culture',
        'key_services', 'products_services_offered', 'pain_points', 'competitive_advantages',
        'tech_stack', 'tech_sophistication', 'has_chat_widget', 'has_forms',
        'funding_status', 'funding_stage_detailed', 'has_job_listings', 'job_listings_count',
        'leadership_team', 'key_decision_makers', 'awards', 'certifications', 'partnerships',
        'contact_info', 'social_media', 'recent_news', 'recent_news_events'
    ]
    
    def is_field_filled(value: Any) -> bool:
        """Check if a field has meaningful data"""
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
    
    # Get companies
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=25)
    
    print("=" * 80)
    print("CURRENT DATA COMPLETENESS ANALYSIS")
    print("=" * 80)
    print(f"Companies in database: {len(companies)}")
    print(f"Fields analyzed: {len(key_fields)}")
    print()
    
    # Analyze each company
    company_stats = []
    for i, company in enumerate(companies[:10], 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        
        filled_fields = 0
        filled_field_names = []
        empty_field_names = []
        
        for field in key_fields:
            value = metadata.get(field)
            if is_field_filled(value):
                filled_fields += 1
                filled_field_names.append(field)
            else:
                empty_field_names.append(field)
        
        completeness = (filled_fields / len(key_fields)) * 100
        
        company_stats.append({
            'name': company_name,
            'website': metadata.get('website', 'No website'),
            'filled_fields': filled_fields,
            'completeness': completeness,
            'filled_field_names': filled_field_names,
            'empty_field_names': empty_field_names
        })
        
        print(f"{i:2d}. {company_name}")
        print(f"    Completeness: {completeness:.1f}% ({filled_fields}/{len(key_fields)} fields)")
        print(f"    Website: {metadata.get('website', 'No website')}")
        
        # Show key missing fields
        critical_missing = [f for f in empty_field_names if f in [
            'founding_year', 'location', 'employee_count_range', 'company_description',
            'value_proposition', 'tech_stack', 'contact_info'
        ]]
        if critical_missing:
            print(f"    Missing critical: {', '.join(critical_missing[:5])}")
        print()
    
    # Overall statistics
    if company_stats:
        avg_completeness = sum(c['completeness'] for c in company_stats) / len(company_stats)
        avg_filled = sum(c['filled_fields'] for c in company_stats) / len(company_stats)
        
        print("OVERALL STATISTICS:")
        print(f"  Average completeness: {avg_completeness:.1f}%")
        print(f"  Average fields filled: {avg_filled:.1f}/{len(key_fields)}")
        print()
        
        # Field-by-field analysis
        field_fill_rates = {}
        for field in key_fields:
            filled_count = sum(1 for c in company_stats if field in c['filled_field_names'])
            fill_rate = (filled_count / len(company_stats)) * 100
            field_fill_rates[field] = fill_rate
        
        print("FIELD FILL RATES (Top 10 best):")
        sorted_fields = sorted(field_fill_rates.items(), key=lambda x: x[1], reverse=True)
        for field, rate in sorted_fields[:10]:
            print(f"  {field:25} : {rate:5.1f}%")
        
        print()
        print("FIELD FILL RATES (Top 10 worst):")
        for field, rate in sorted_fields[-10:]:
            if rate < 100:
                print(f"  {field:25} : {rate:5.1f}%")
    
    print()
    print("=" * 80)
    print("IMPROVEMENT OPPORTUNITIES:")
    print("- Focus on extracting: founding_year, location, employee_count_range")
    print("- Improve contact_info and social_media extraction")
    print("- Better tech_stack and competitive_advantages analysis")
    print("- Enhanced company_culture and value_proposition extraction")
    print("=" * 80)

if __name__ == "__main__":
    analyze_data_completeness()
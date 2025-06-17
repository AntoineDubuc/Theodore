#!/usr/bin/env python3
"""
Show exactly what data we extracted for enhanced companies.
"""

import os
import sys
import json

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def show_extracted_data():
    """Show exactly what we extracted vs what we had before"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get Dollarama as our best example
    dollarama = pipeline.pinecone_client.find_company_by_name("Dollarama")
    
    if not dollarama:
        print("❌ Dollarama not found")
        return
    
    metadata = dollarama.__dict__ if hasattr(dollarama, '__dict__') else {}
    
    print("=" * 80)
    print("SPECIFIC DATA EXTRACTED: DOLLARAMA EXAMPLE")
    print("=" * 80)
    
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True
        return bool(value)
    
    # Show exactly what we extracted
    extracted_data = {}
    for key, value in metadata.items():
        if is_filled(value) and not key.startswith('_'):
            extracted_data[key] = value
    
    print("🎯 WHAT WE SUCCESSFULLY EXTRACTED:")
    print("=" * 80)
    
    # Group by category
    categories = {
        "BASIC COMPANY INFO": ['company_name', 'website', 'industry', 'business_model'],
        "BUSINESS INTELLIGENCE": ['company_description', 'value_proposition', 'target_market', 'competitive_advantages'],
        "TECHNICAL ASSESSMENT": ['tech_stack', 'tech_sophistication', 'has_chat_widget', 'has_forms'],
        "COMPANY METRICS": ['company_size', 'company_stage', 'employee_count_range', 'funding_status'],
        "CONTACT & SOCIAL": ['contact_info', 'social_media', 'leadership_team'],
        "MARKET POSITION": ['key_services', 'products_services_offered', 'awards', 'partnerships']
    }
    
    for category, fields in categories.items():
        category_data = {k: v for k, v in extracted_data.items() if k in fields}
        
        if category_data:
            print(f"\n📊 {category}:")
            for field, value in category_data.items():
                field_name = field.replace('_', ' ').title()
                
                # Format the value nicely
                if isinstance(value, str) and len(value) > 100:
                    display_value = value[:100] + "..."
                elif isinstance(value, bool):
                    display_value = "✅ Yes" if value else "❌ No"
                elif isinstance(value, (list, dict)):
                    display_value = str(value)
                else:
                    display_value = str(value)
                
                print(f"  • {field_name}: {display_value}")
    
    # Show what we're still missing
    all_possible = [
        'founding_year', 'location', 'employee_count_range', 'company_culture',
        'pain_points', 'funding_stage_detailed', 'has_job_listings', 
        'key_decision_makers', 'certifications', 'recent_news'
    ]
    
    missing = [field for field in all_possible if not is_filled(metadata.get(field))]
    
    if missing:
        print(f"\n❌ STILL MISSING (opportunities for improvement):")
        for field in missing[:8]:
            field_name = field.replace('_', ' ').title()
            print(f"  • {field_name}")
    
    print(f"\n📈 SUMMARY:")
    total_extracted = len(extracted_data)
    total_possible = 34  # Our full data model
    completeness = (total_extracted / total_possible) * 100
    
    print(f"  • Extracted: {total_extracted} fields")
    print(f"  • Completeness: {completeness:.1f}%")
    print(f"  • Data Quality: {'🟢 Good' if completeness > 50 else '🟡 Medium' if completeness > 25 else '🔴 Needs Improvement'}")
    
    print(f"\n🚀 BEFORE vs AFTER:")
    print(f"  BEFORE: Basic web scraping - typically 3-5 basic fields")
    print(f"  AFTER:  AI-powered extraction - {total_extracted} structured fields")
    print(f"  IMPROVEMENT: {total_extracted - 4}+ additional data points per company")
    
    # Show the most valuable extracted data
    valuable_fields = ['company_description', 'value_proposition', 'target_market', 'competitive_advantages']
    valuable_data = {k: v for k, v in extracted_data.items() if k in valuable_fields}
    
    if valuable_data:
        print(f"\n💎 MOST VALUABLE BUSINESS INTELLIGENCE:")
        for field, value in valuable_data.items():
            field_name = field.replace('_', ' ').title()
            if isinstance(value, str):
                # Show more of the valuable content
                display_value = value[:200] + "..." if len(value) > 200 else value
                print(f"  📝 {field_name}:")
                print(f"     {display_value}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    show_extracted_data()
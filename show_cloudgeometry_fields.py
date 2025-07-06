#!/usr/bin/env python3
"""
Show actual CloudGeometry field extraction results from database
"""

from src.pinecone_client import PineconeClient
from src.models import CompanyIntelligenceConfig
import json
import os

def show_field_results():
    """Show what we extracted for each field"""
    config = CompanyIntelligenceConfig()
    client = PineconeClient(
        config=config,
        api_key=os.getenv('PINECONE_API_KEY'),
        environment=os.getenv('PINECONE_ENVIRONMENT', 'gcp-starter'),
        index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Search for CloudGeometry
    result = client.find_company_by_name('CloudGeometry')
    if not result:
        print("No CloudGeometry data found in database")
        return
    
    print("CLOUDGEOMETRY FIELD EXTRACTION RESULTS")
    print("=" * 60)
    
    # Get all fields and their values
    all_fields = [
        'id', 'name', 'website', 'industry', 'business_model', 'company_size',
        'tech_stack', 'has_chat_widget', 'has_forms', 'pain_points', 'key_services',
        'competitive_advantages', 'target_market', 'business_model_framework',
        'company_description', 'value_proposition', 'founding_year', 'location',
        'employee_count_range', 'company_culture', 'funding_status', 'social_media',
        'contact_info', 'leadership_team', 'recent_news', 'certifications',
        'partnerships', 'awards', 'pages_crawled', 'crawl_depth', 'crawl_duration',
        'saas_classification', 'classification_confidence', 'classification_justification',
        'classification_timestamp', 'classification_model_version', 'is_saas',
        'company_stage', 'tech_sophistication', 'geographic_scope', 'business_model_type',
        'decision_maker_type', 'sales_complexity', 'stage_confidence', 'tech_confidence',
        'industry_confidence', 'has_job_listings', 'job_listings_count', 'job_listings',
        'job_listings_details', 'products_services_offered', 'key_decision_makers',
        'funding_stage_detailed', 'sales_marketing_tools', 'recent_news_events',
        'raw_content', 'ai_summary', 'embedding', 'scraped_urls', 'scraped_content_details',
        'llm_prompts_sent', 'page_selection_prompt', 'content_analysis_prompt',
        'total_input_tokens', 'total_output_tokens', 'total_cost_usd', 'llm_calls_breakdown',
        'created_at', 'last_updated', 'scrape_status', 'scrape_error'
    ]
    
    extracted_count = 0
    
    for i, field in enumerate(all_fields, 1):
        value = getattr(result, field, None)
        
        # Check if field has meaningful data
        has_data = False
        display_value = "None"
        
        if value is not None:
            if isinstance(value, str):
                if value and value.strip() and value not in ['unknown', 'Unknown', 'N/A', 'null']:
                    has_data = True
                    if len(value) > 150:
                        display_value = f'"{value[:147]}..."'
                    else:
                        display_value = f'"{value}"'
                else:
                    display_value = f'"{value}" (empty/default)'
            elif isinstance(value, (list, dict)):
                if len(value) > 0:
                    has_data = True
                    if isinstance(value, list):
                        display_value = f"[{len(value)} items]: {str(value[:3])}"
                        if len(value) > 3:
                            display_value += "..."
                    else:
                        display_value = f"{{...}} ({len(value)} keys)"
                else:
                    display_value = f"{type(value).__name__} (empty)"
            elif isinstance(value, (int, float)):
                if value > 0:
                    has_data = True
                display_value = str(value)
            elif isinstance(value, bool):
                has_data = True
                display_value = str(value)
            else:
                has_data = True
                display_value = str(value)
        
        if has_data:
            extracted_count += 1
        
        status = "✅" if has_data else "❌"
        print(f"{i:2d}. {status} {field:30} = {display_value}")
    
    print()
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Total Fields: {len(all_fields)}")
    print(f"   Extracted: {extracted_count}")
    print(f"   Success Rate: {extracted_count/len(all_fields)*100:.1f}%")
    print(f"   Target: 75% ({len(all_fields)*0.75:.0f} fields)")
    print(f"   Status: {'✅ SUCCESS' if extracted_count/len(all_fields) >= 0.75 else '❌ BELOW TARGET'}")

if __name__ == "__main__":
    show_field_results()
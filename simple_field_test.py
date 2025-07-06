#!/usr/bin/env python3
"""
Simple CloudGeometry field test - extract data and show what we got for each field
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig

async def extract_and_report():
    """Extract data from CloudGeometry and report what we got for each field"""
    print("🚀 CLOUDGEOMETRY FIELD EXTRACTION TEST")
    print("=" * 60)
    
    # Create test company
    company = CompanyData(
        name="CloudGeometry",
        website="https://www.cloudgeometry.com"
    )
    
    # Initialize scraper with limited pages for speed
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    scraper.max_pages = 3  # Only 3 pages for speed
    
    print(f"🎯 Extracting data from: {company.website}")
    print(f"📊 Limited to 3 pages for quick results")
    print()
    
    try:
        # Extract data
        result = await scraper.scrape_company_intelligent(company)
        
        print(f"✅ EXTRACTION COMPLETED!")
        print(f"📋 FIELD-BY-FIELD RESULTS:")
        print("=" * 60)
        
        # Get all fields from the model
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
                            display_value = f"[{len(value)} items]: {value[:3]}{'...' if len(value) > 3 else ''}"
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
        
        return True
        
    except Exception as e:
        print(f"❌ EXTRACTION FAILED: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(extract_and_report())
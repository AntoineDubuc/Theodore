#!/usr/bin/env python3
"""
Test reprocessing a few companies to show data improvements.
"""

import os
import sys
from typing import Dict, Any

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def test_sample_improvements():
    """Test reprocessing a few companies to show improvements"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Sample companies to reprocess
    test_companies = [
        {"name": "Dollarama", "website": "https://www.dollarama.com"},
        {"name": "ResMed", "website": "https://www.resmed.com"},
        {"name": "adtheorent.com", "website": "adtheorent.com"}
    ]
    
    key_fields = [
        'founding_year', 'location', 'employee_count_range', 'company_description',
        'value_proposition', 'target_market', 'tech_stack', 'competitive_advantages',
        'contact_info', 'social_media', 'key_services', 'leadership_team'
    ]
    
    def count_filled_fields(metadata, fields):
        """Count how many fields are filled"""
        filled = 0
        for field in fields:
            value = metadata.get(field)
            if value and str(value).strip() and str(value).lower() not in ['unknown', 'not specified', 'n/a']:
                if isinstance(value, (list, dict)) and len(value) > 0:
                    filled += 1
                elif isinstance(value, str) and value.strip():
                    filled += 1
                elif isinstance(value, (int, float)) and value > 0:
                    filled += 1
        return filled
    
    print("=" * 80)
    print("SAMPLE REPROCESSING TEST - BEFORE vs AFTER")
    print("=" * 80)
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n{i}. TESTING: {company['name']}")
        print("-" * 40)
        
        # Get current data
        existing = pipeline.pinecone_client.find_company_by_name(company['name'])
        if existing:
            before_metadata = existing.__dict__ if hasattr(existing, '__dict__') else {}
            before_filled = count_filled_fields(before_metadata, key_fields)
            
            print(f"BEFORE - Filled fields: {before_filled}/{len(key_fields)}")
            desc = before_metadata.get('company_description', 'None')
            desc_preview = desc[:100] if desc and desc != 'None' else 'None'
            print(f"Current description: {desc_preview}...")
            
            # Reprocess
            print(f"Reprocessing {company['name']}...")
            try:
                new_data = pipeline.process_single_company(company['name'], company['website'])
                
                # Get updated data
                updated = pipeline.pinecone_client.find_company_by_name(company['name'])
                if updated:
                    after_metadata = updated.__dict__ if hasattr(updated, '__dict__') else {}
                    after_filled = count_filled_fields(after_metadata, key_fields)
                    
                    improvement = after_filled - before_filled
                    
                    print(f"AFTER  - Filled fields: {after_filled}/{len(key_fields)} ({improvement:+d})")
                    
                    # Show new fields
                    new_fields = []
                    for field in key_fields:
                        before_val = before_metadata.get(field)
                        after_val = after_metadata.get(field)
                        
                        before_filled = bool(before_val and str(before_val).strip() and str(before_val) != 'unknown')
                        after_filled = bool(after_val and str(after_val).strip() and str(after_val) != 'unknown')
                        
                        if not before_filled and after_filled:
                            new_fields.append(field)
                    
                    if new_fields:
                        print(f"NEW FIELDS: {', '.join(new_fields)}")
                    else:
                        print("No new fields added")
                    
                    new_desc = after_metadata.get('company_description', 'None')
                    new_desc_preview = new_desc[:100] if new_desc and new_desc != 'None' else 'None'
                    print(f"New description: {new_desc_preview}...")
                
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Company {company['name']} not found in database")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_sample_improvements()
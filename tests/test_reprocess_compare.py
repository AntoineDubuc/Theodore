#!/usr/bin/env python3
"""
Reprocess the same 10 companies and compare results with enhanced extraction
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig
from src.sheets_integration import GoogleSheetsServiceClient
from config.sheets_field_mapping import COMPLETE_DATA_COLUMNS
from dotenv import load_dotenv

load_dotenv()

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

# Fields we're specifically targeting with improvements
TARGET_FIELDS = [
    'Location', 'Founded Year', 'Employee Count', 'Contact Email', 
    'Contact Phone', 'Social Media Links', 'Products/Services Offered',
    'Leadership Team', 'Partnerships', 'Certifications'
]

def get_existing_data(sheets_client, sheet_id: str) -> Dict[str, Dict]:
    """Get existing data from the Details sheet"""
    print("📊 Reading existing data from Google Sheets...")
    
    details = sheets_client.service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='Details!A:BZ'
    ).execute()
    
    if 'values' not in details or len(details['values']) < 2:
        return {}
    
    headers = details['values'][0]
    data_rows = details['values'][1:]
    
    # Create lookup by company name
    existing_data = {}
    for row in data_rows:
        if len(row) > 0:
            company_name = row[0] if row else ""
            if company_name:
                # Convert row to dict
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                    else:
                        row_dict[header] = ""
                existing_data[company_name] = row_dict
    
    return existing_data

def analyze_field_improvements(before: Dict, after: Dict) -> Dict[str, Tuple[str, str, bool]]:
    """Compare field values before and after reprocessing"""
    improvements = {}
    
    for field in TARGET_FIELDS:
        before_value = before.get(field, "")
        after_value = after.get(field, "")
        
        # Clean up values for comparison
        before_clean = str(before_value).strip()
        after_clean = str(after_value).strip()
        
        # Check if field was empty before but has data now
        was_empty = before_clean in ["", "[]", "{}", "None", "null"]
        has_data_now = after_clean not in ["", "[]", "{}", "None", "null"]
        
        improved = was_empty and has_data_now
        
        improvements[field] = (before_clean, after_clean, improved)
    
    return improvements

def calculate_fill_rates(data: Dict[str, Dict]) -> Dict[str, float]:
    """Calculate fill rates for target fields"""
    fill_rates = {}
    
    if not data:
        return fill_rates
    
    total_companies = len(data)
    
    for field in TARGET_FIELDS:
        filled_count = 0
        for company_name, company_data in data.items():
            value = str(company_data.get(field, "")).strip()
            if value and value not in ["", "[]", "{}", "None", "null"]:
                filled_count += 1
        
        fill_rate = (filled_count / total_companies * 100) if total_companies > 0 else 0
        fill_rates[field] = fill_rate
    
    return fill_rates

def main():
    print("🔄 Reprocessing Companies with Enhanced Extraction")
    print("=" * 70)
    
    try:
        # Initialize sheets client
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Get existing data (before improvements)
        existing_data = get_existing_data(sheets_client, TEST_SHEET_ID)
        
        # Get list of companies to reprocess (first 10)
        company_list = list(existing_data.keys())[:10]
        
        if not company_list:
            print("❌ No companies found in the sheet")
            return
        
        print(f"\n📋 Found {len(company_list)} companies to reprocess:")
        for i, company in enumerate(company_list, 1):
            print(f"   {i}. {company}")
        
        # Calculate before fill rates
        before_fill_rates = calculate_fill_rates(
            {name: existing_data[name] for name in company_list if name in existing_data}
        )
        
        print(f"\n📊 Before Enhancement - Fill Rates:")
        print("-" * 50)
        for field, rate in sorted(before_fill_rates.items()):
            status = "✅" if rate > 50 else "🟡" if rate > 20 else "❌"
            print(f"{status} {field:30} {rate:5.1f}%")
        
        # Initialize pipeline with enhanced extraction
        print(f"\n🚀 Starting reprocessing with enhanced extraction...")
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Reprocess each company
        reprocessed_data = {}
        for i, company_name in enumerate(company_list, 1):
            print(f"\n🔍 Reprocessing {i}/{len(company_list)}: {company_name}")
            
            try:
                # Get website from existing data
                website = existing_data[company_name].get('Website', '')
                if not website:
                    print(f"   ⚠️  No website found, skipping")
                    continue
                
                # Process with enhanced extraction
                result = pipeline.process_single_company(company_name, website)
                
                if result.scrape_status == "success":
                    print(f"   ✅ Successfully reprocessed")
                    
                    # Convert to sheet format
                    from config.sheets_field_mapping import convert_company_to_sheets_row
                    row_data = convert_company_to_sheets_row(result, COMPLETE_DATA_COLUMNS)
                    
                    # Create dict from row data
                    company_dict = {}
                    for j, header in enumerate(COMPLETE_DATA_COLUMNS):
                        if j < len(row_data):
                            company_dict[header] = row_data[j]
                        else:
                            company_dict[header] = ""
                    
                    reprocessed_data[company_name] = company_dict
                    
                    # Show improvements for this company
                    improvements = analyze_field_improvements(
                        existing_data[company_name], 
                        company_dict
                    )
                    
                    improved_fields = [field for field, (before, after, improved) in improvements.items() if improved]
                    if improved_fields:
                        print(f"   🎯 New data extracted for: {', '.join(improved_fields)}")
                else:
                    print(f"   ❌ Reprocessing failed: {result.scrape_error}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        # Calculate after fill rates
        after_fill_rates = calculate_fill_rates(reprocessed_data)
        
        # Compare results
        print(f"\n\n📊 RESULTS COMPARISON")
        print("=" * 70)
        print(f"{'Field':<30} {'Before':<10} {'After':<10} {'Change':<10}")
        print("-" * 70)
        
        total_improvement = 0
        improved_fields = 0
        
        for field in TARGET_FIELDS:
            before_rate = before_fill_rates.get(field, 0)
            after_rate = after_fill_rates.get(field, 0)
            change = after_rate - before_rate
            total_improvement += change
            
            if change > 0:
                improved_fields += 1
                status = "📈"
            elif change < 0:
                status = "📉"
            else:
                status = "➖"
            
            print(f"{field:<30} {before_rate:>6.1f}% {after_rate:>6.1f}% {status} {change:>+6.1f}%")
        
        avg_before = sum(before_fill_rates.values()) / len(before_fill_rates) if before_fill_rates else 0
        avg_after = sum(after_fill_rates.values()) / len(after_fill_rates) if after_fill_rates else 0
        avg_improvement = avg_after - avg_before
        
        print("-" * 70)
        print(f"{'AVERAGE':<30} {avg_before:>6.1f}% {avg_after:>6.1f}% {'📈' if avg_improvement > 0 else '📉'} {avg_improvement:>+6.1f}%")
        
        # Summary
        print(f"\n\n📈 IMPROVEMENT SUMMARY")
        print("=" * 70)
        print(f"✅ Fields improved: {improved_fields}/{len(TARGET_FIELDS)}")
        print(f"📊 Average fill rate: {avg_before:.1f}% → {avg_after:.1f}% ({avg_improvement:+.1f}%)")
        
        # Show specific improvements
        print(f"\n🎯 Specific Improvements Found:")
        for company_name, company_data in reprocessed_data.items():
            if company_name in existing_data:
                improvements = analyze_field_improvements(existing_data[company_name], company_data)
                improved = [(field, after) for field, (before, after, imp) in improvements.items() if imp]
                
                if improved:
                    print(f"\n{company_name}:")
                    for field, value in improved:
                        # Truncate long values
                        display_value = value if len(value) <= 50 else value[:47] + "..."
                        print(f"   • {field}: {display_value}")
        
        # Save detailed comparison
        comparison_file = f"extraction_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        comparison_data = {
            "summary": {
                "companies_processed": len(reprocessed_data),
                "avg_fill_before": avg_before,
                "avg_fill_after": avg_after,
                "improvement": avg_improvement,
                "fields_improved": improved_fields
            },
            "field_comparison": {
                field: {
                    "before": before_fill_rates.get(field, 0),
                    "after": after_fill_rates.get(field, 0),
                    "change": after_fill_rates.get(field, 0) - before_fill_rates.get(field, 0)
                } for field in TARGET_FIELDS
            },
            "company_improvements": {}
        }
        
        for company_name in company_list:
            if company_name in existing_data and company_name in reprocessed_data:
                improvements = analyze_field_improvements(
                    existing_data[company_name], 
                    reprocessed_data[company_name]
                )
                improved_fields = {
                    field: {"before": before, "after": after} 
                    for field, (before, after, improved) in improvements.items() 
                    if improved
                }
                if improved_fields:
                    comparison_data["company_improvements"][company_name] = improved_fields
        
        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"\n💾 Detailed comparison saved to: {comparison_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Analyze the before and after state of the 10 companies
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

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

def analyze_existing_data():
    """Analyze the current state of data in the sheet"""
    print("📊 Analyzing Current Data State (Before Reprocessing)")
    print("=" * 70)
    
    try:
        # Initialize sheets client
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Get data from Details sheet
        print("\n📋 Reading data from Google Sheets...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A:BZ'
        ).execute()
        
        if 'values' not in details or len(details['values']) < 2:
            print("❌ No data found in Details sheet")
            return
        
        headers = details['values'][0]
        data_rows = details['values'][1:]
        
        # Filter to first 10 companies
        companies = []
        for row in data_rows[:10]:
            if len(row) > 0:
                company_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        company_dict[header] = row[i]
                    else:
                        company_dict[header] = ""
                companies.append(company_dict)
        
        print(f"   Found {len(companies)} companies to analyze")
        
        # Analyze each target field
        print(f"\n📊 Target Field Analysis:")
        print("-" * 70)
        print(f"{'Field':<30} {'Fill Rate':<12} {'Examples':<30}")
        print("-" * 70)
        
        field_stats = {}
        
        for field in TARGET_FIELDS:
            if field in headers:
                filled_count = 0
                examples = []
                
                for company in companies:
                    value = str(company.get(field, "")).strip()
                    if value and value not in ["", "[]", "{}", "None", "null"]:
                        filled_count += 1
                        if len(examples) < 2 and len(value) < 50:
                            examples.append(value)
                
                fill_rate = (filled_count / len(companies) * 100) if companies else 0
                field_stats[field] = {
                    'fill_rate': fill_rate,
                    'filled_count': filled_count,
                    'total': len(companies),
                    'examples': examples
                }
                
                status = "✅" if fill_rate > 50 else "🟡" if fill_rate > 20 else "❌"
                example_str = ", ".join(examples[:1]) if examples else "No data"
                if len(example_str) > 30:
                    example_str = example_str[:27] + "..."
                
                print(f"{status} {field:<28} {fill_rate:>5.1f}% ({filled_count}/{len(companies)}) {example_str:<30}")
        
        # Show company-by-company breakdown
        print(f"\n📋 Company-by-Company Breakdown:")
        print("-" * 70)
        
        for i, company in enumerate(companies, 1):
            company_name = company.get('Company Name', 'Unknown')
            website = company.get('Website', 'No website')
            
            # Count filled target fields
            filled_fields = []
            empty_fields = []
            
            for field in TARGET_FIELDS:
                value = str(company.get(field, "")).strip()
                if value and value not in ["", "[]", "{}", "None", "null"]:
                    filled_fields.append(field)
                else:
                    empty_fields.append(field)
            
            fill_percentage = (len(filled_fields) / len(TARGET_FIELDS) * 100) if TARGET_FIELDS else 0
            
            print(f"\n{i}. {company_name} ({website})")
            print(f"   Target fields filled: {len(filled_fields)}/{len(TARGET_FIELDS)} ({fill_percentage:.0f}%)")
            
            if filled_fields:
                print(f"   ✅ Has data for: {', '.join(filled_fields[:3])}")
                if len(filled_fields) > 3:
                    print(f"      and {len(filled_fields) - 3} more fields")
            
            if empty_fields:
                priority_empty = [f for f in ['Location', 'Founded Year', 'Employee Count'] if f in empty_fields]
                if priority_empty:
                    print(f"   ❌ Missing critical: {', '.join(priority_empty)}")
        
        # Overall statistics
        avg_fill_rate = sum(stat['fill_rate'] for stat in field_stats.values()) / len(field_stats) if field_stats else 0
        
        print(f"\n\n📈 OVERALL STATISTICS")
        print("=" * 70)
        print(f"Average fill rate for target fields: {avg_fill_rate:.1f}%")
        print(f"Fields with >50% fill rate: {sum(1 for stat in field_stats.values() if stat['fill_rate'] > 50)}/{len(TARGET_FIELDS)}")
        print(f"Fields with 0% fill rate: {sum(1 for stat in field_stats.values() if stat['fill_rate'] == 0)}/{len(TARGET_FIELDS)}")
        
        # Identify completely missing fields
        missing_fields = [field for field, stat in field_stats.items() if stat['fill_rate'] == 0]
        if missing_fields:
            print(f"\n🔴 Completely missing fields: {', '.join(missing_fields)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS FOR REPROCESSING")
        print("=" * 70)
        print("1. Focus on extracting: Location, Founded Year, Employee Count")
        print("2. These are likely available on /contact, /about, /team pages")
        print("3. The enhanced LLM prompts should specifically target these pages")
        print("4. Pattern-based extraction should help find dates, locations, numbers")
        
        return field_stats, companies
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    field_stats, companies = analyze_existing_data()
    
    if field_stats:
        print(f"\n\n💾 Current state analyzed. To reprocess with improvements:")
        print("   python test_reprocess_compare.py")
        print("\nThis will:")
        print("   1. Reprocess the same 10 companies")
        print("   2. Use enhanced page selection targeting missing data")
        print("   3. Apply pattern-based extraction")
        print("   4. Show before/after comparison")
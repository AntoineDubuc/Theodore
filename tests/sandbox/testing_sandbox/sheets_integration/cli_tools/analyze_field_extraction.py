#!/usr/bin/env python3
"""
Analyze field extraction patterns to identify improvement opportunities
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient
from src.pinecone_client import PineconeClient
from src.models import CompanyIntelligenceConfig
from config.sheets_field_mapping import COMPLETE_DATA_COLUMNS

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def analyze_field_patterns():
    """Analyze which fields are commonly empty and why"""
    print("🔍 Analyzing Field Extraction Patterns")
    print("=" * 60)
    
    try:
        # Initialize clients
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Get data from sheet
        print("\n📊 Reading data from Google Sheets...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A:BZ'
        ).execute()
        
        if 'values' not in details or len(details['values']) < 2:
            print("❌ No data found in Details sheet")
            return
        
        headers = details['values'][0]
        data_rows = [row for row in details['values'][1:] if len(row) > 10]
        
        print(f"   Found {len(data_rows)} companies with data")
        print(f"   Total fields: {len(headers)}")
        
        # Analyze field fill rates
        field_stats = defaultdict(lambda: {'filled': 0, 'empty': 0, 'values': []})
        
        for row in data_rows:
            for col_idx, header in enumerate(headers):
                if col_idx < len(row):
                    value = row[col_idx]
                    if value and str(value).strip() and value not in ['[]', '{}', 'None', 'null']:
                        field_stats[header]['filled'] += 1
                        field_stats[header]['values'].append(value)
                    else:
                        field_stats[header]['empty'] += 1
                else:
                    field_stats[header]['empty'] += 1
        
        # Calculate fill rates
        print("\n📈 Field Fill Rate Analysis:")
        print("-" * 60)
        
        fill_rates = []
        for field, stats in field_stats.items():
            total = stats['filled'] + stats['empty']
            fill_rate = stats['filled'] / total * 100 if total > 0 else 0
            fill_rates.append((field, fill_rate, stats['filled'], total))
        
        # Sort by fill rate
        fill_rates.sort(key=lambda x: x[1], reverse=True)
        
        # Group by fill rate categories
        always_filled = []      # >90%
        usually_filled = []     # 50-90%
        sometimes_filled = []   # 10-50%
        rarely_filled = []      # <10%
        
        for field, rate, filled, total in fill_rates:
            if rate > 90:
                always_filled.append((field, rate, filled, total))
            elif rate > 50:
                usually_filled.append((field, rate, filled, total))
            elif rate > 10:
                sometimes_filled.append((field, rate, filled, total))
            else:
                rarely_filled.append((field, rate, filled, total))
        
        # Display results
        print(f"\n✅ Always Filled (>90%): {len(always_filled)} fields")
        for field, rate, filled, total in always_filled[:10]:
            print(f"   {field:30} {rate:5.1f}% ({filled}/{total})")
        
        print(f"\n🟡 Usually Filled (50-90%): {len(usually_filled)} fields")
        for field, rate, filled, total in usually_filled[:10]:
            print(f"   {field:30} {rate:5.1f}% ({filled}/{total})")
        
        print(f"\n🟠 Sometimes Filled (10-50%): {len(sometimes_filled)} fields")
        for field, rate, filled, total in sometimes_filled[:10]:
            print(f"   {field:30} {rate:5.1f}% ({filled}/{total})")
        
        print(f"\n❌ Rarely Filled (<10%): {len(rarely_filled)} fields")
        for field, rate, filled, total in rarely_filled[:10]:
            print(f"   {field:30} {rate:5.1f}% ({filled}/{total})")
        
        # Analyze array fields specifically
        print("\n📋 Array Field Analysis:")
        print("-" * 60)
        
        array_fields = []
        for col, field_info in COMPLETE_DATA_COLUMNS.items():
            if field_info['type'] in ['list', 'list_dict']:
                display_name = field_info['header']
                field_name = field_info['field']
                if display_name in field_stats:
                    stats = field_stats[display_name]
                    fill_rate = stats['filled'] / (stats['filled'] + stats['empty']) * 100
                    array_fields.append((display_name, field_name, fill_rate, stats['filled']))
        
        array_fields.sort(key=lambda x: x[2], reverse=True)
        
        for display_name, field_name, rate, filled in array_fields:
            status = "✅" if rate > 50 else "🟡" if rate > 10 else "❌"
            print(f"   {status} {display_name:30} {rate:5.1f}% ({filled} companies)")
        
        # Identify improvement opportunities
        print("\n💡 Improvement Recommendations:")
        print("-" * 60)
        
        # Fields that should be extractable but aren't
        improvable_fields = [
            ('location', 'Usually available on About/Contact pages'),
            ('employee_count_range', 'Often in About or Careers sections'),
            ('founding_year', 'Common in About Us or company history'),
            ('social_media', 'Usually in footer or contact page'),
            ('contact_info', 'Should be on Contact page'),
            ('products_services_offered', 'Main offering pages'),
            ('partnerships', 'Often in About or Press sections'),
            ('certifications', 'Usually displayed prominently'),
            ('recent_news', 'Press or News sections')
        ]
        
        for field, hint in improvable_fields:
            if field in field_stats:
                stats = field_stats[field]
                fill_rate = stats['filled'] / (stats['filled'] + stats['empty']) * 100
                if fill_rate < 50:
                    print(f"   • {field} (currently {fill_rate:.1f}% filled)")
                    print(f"     → {hint}")
        
        # Sample some companies to see what's missing
        print("\n🔬 Sample Company Analysis:")
        print("-" * 60)
        
        # Get a few companies from Pinecone for detailed analysis
        sample_companies = pinecone_client.get_all_companies(limit=5)
        
        for company in sample_companies[:3]:
            print(f"\n   Company: {company.name}")
            print(f"   Website: {company.website}")
            print(f"   Pages crawled: {len(company.pages_crawled or [])}")
            
            # Check which important fields are missing
            missing_fields = []
            if not company.location:
                missing_fields.append('location')
            if not company.employee_count_range:
                missing_fields.append('employee_count_range')
            if not company.founding_year:
                missing_fields.append('founding_year')
            if not company.social_media or company.social_media == {}:
                missing_fields.append('social_media')
            if not company.products_services_offered:
                missing_fields.append('products_services_offered')
            
            if missing_fields:
                print(f"   Missing: {', '.join(missing_fields)}")
                
                # Suggest pages to check
                if company.pages_crawled:
                    about_pages = [p for p in company.pages_crawled if 'about' in p.lower()]
                    contact_pages = [p for p in company.pages_crawled if 'contact' in p.lower()]
                    
                    if about_pages:
                        print(f"   → Has About page: {about_pages[0]}")
                    if contact_pages:
                        print(f"   → Has Contact page: {contact_pages[0]}")
        
        # Generate extraction improvement strategies
        print("\n🚀 Extraction Improvement Strategies:")
        print("-" * 60)
        print("1. **Enhanced Page Selection**:")
        print("   • Prioritize About, Contact, Team, and Company pages")
        print("   • Look for footer links to social media")
        print("   • Check careers page for employee count hints")
        
        print("\n2. **Improved Prompt Engineering**:")
        print("   • Add specific extraction prompts for missing fields")
        print("   • Use few-shot examples for better extraction")
        print("   • Chain prompts for detailed extraction")
        
        print("\n3. **Page-Specific Extraction**:")
        print("   • Contact page → location, phone, email, social")
        print("   • About page → founding year, employee count, mission")
        print("   • Team page → leadership, company size indicators")
        print("   • Footer → social media, certifications, awards")
        
        print("\n4. **Pattern Recognition**:")
        print("   • Look for patterns like 'Founded in YYYY'")
        print("   • Employee count patterns: '50-100 employees'")
        print("   • Location patterns: 'Headquartered in X'")
        print("   • Social media icons and links")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_field_patterns()
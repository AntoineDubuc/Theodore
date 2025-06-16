#!/usr/bin/env python3
"""
Analyze missing data points in the current dataset
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient
from config.sheets_field_mapping import COMPLETE_DATA_COLUMNS

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def analyze_missing_data():
    """Analyze which data points are most commonly missing"""
    print("🔍 Analyzing Missing Data Points in Theodore Dataset")
    print("=" * 70)
    
    try:
        # Initialize sheets client
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
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
        
        # Categorize fields by business importance
        field_categories = {
            'Essential Business Info': [
                'Company Name', 'Website', 'Industry', 'Business Model', 
                'Company Size', 'Target Market', 'Value Proposition'
            ],
            'Contact & Location': [
                'Location', 'Contact Email', 'Contact Phone', 'Contact Address',
                'Social Media Links'
            ],
            'Company Details': [
                'Founded Year', 'Employee Count', 'Company Stage', 
                'Geographic Scope', 'Funding Status'
            ],
            'Technology & Products': [
                'Tech Stack', 'Products/Services Offered', 'Key Services',
                'Tech Sophistication', 'Sales/Marketing Tools'
            ],
            'Market Intelligence': [
                'Pain Points', 'Competitive Advantages', 'Partnerships',
                'Key Decision Makers', 'Decision Maker Type'
            ],
            'Credibility Indicators': [
                'Certifications', 'Awards', 'Recent News', 'Leadership Team',
                'Company Culture'
            ],
            'Sales Intelligence': [
                'Sales Complexity', 'Business Model Type', 'Has Job Listings',
                'Job Listings Count', 'Job Listings Details'
            ]
        }
        
        # Analyze missing data by category
        category_stats = {}
        field_details = {}
        
        for category, fields in field_categories.items():
            category_total = 0
            category_filled = 0
            category_fields = []
            
            for field in fields:
                if field in headers:
                    col_idx = headers.index(field)
                    filled_count = 0
                    total_count = len(data_rows)
                    
                    for row in data_rows:
                        if col_idx < len(row):
                            value = row[col_idx]
                            if value and str(value).strip() and value not in ['[]', '{}', 'None', 'null', '']:
                                filled_count += 1
                    
                    fill_rate = filled_count / total_count * 100 if total_count > 0 else 0
                    category_total += 1
                    if fill_rate > 0:
                        category_filled += fill_rate / 100
                    
                    category_fields.append({
                        'field': field,
                        'fill_rate': fill_rate,
                        'filled': filled_count,
                        'total': total_count
                    })
                    
                    field_details[field] = {
                        'category': category,
                        'fill_rate': fill_rate,
                        'filled': filled_count,
                        'total': total_count
                    }
            
            if category_total > 0:
                category_stats[category] = {
                    'average_fill_rate': (category_filled / category_total) * 100,
                    'fields': category_fields
                }
        
        # Display results by category
        print("\n📊 Missing Data Analysis by Category:")
        print("-" * 70)
        
        # Sort categories by completeness
        sorted_categories = sorted(category_stats.items(), 
                                 key=lambda x: x[1]['average_fill_rate'], 
                                 reverse=True)
        
        for category, stats in sorted_categories:
            avg_rate = stats['average_fill_rate']
            status = "✅" if avg_rate > 70 else "🟡" if avg_rate > 30 else "❌"
            
            print(f"\n{status} {category}: {avg_rate:.1f}% average fill rate")
            
            # Show worst fields in this category
            worst_fields = sorted(stats['fields'], key=lambda x: x['fill_rate'])[:5]
            for field_info in worst_fields:
                if field_info['fill_rate'] < 50:
                    print(f"   ❌ {field_info['field']:30} {field_info['fill_rate']:5.1f}% ({field_info['filled']}/{field_info['total']})")
        
        # Identify critical missing data
        print("\n🚨 Critical Missing Data Points (Business Impact):")
        print("-" * 70)
        
        critical_missing = [
            ('Location', 'Essential for territory planning and local outreach'),
            ('Employee Count', 'Indicates company size and buying power'),
            ('Founded Year', 'Shows company maturity and stability'),
            ('Contact Email', 'Direct communication channel'),
            ('Products/Services Offered', 'Understanding what they sell'),
            ('Key Decision Makers', 'Who to contact for sales'),
            ('Funding Status', 'Budget availability indicator'),
            ('Company Stage', 'Sales approach customization'),
            ('Partnerships', 'Integration opportunities'),
            ('Certifications', 'Compliance and credibility')
        ]
        
        for field, impact in critical_missing:
            if field in field_details:
                fill_rate = field_details[field]['fill_rate']
                if fill_rate < 50:
                    status = "🔴" if fill_rate < 10 else "🟠"
                    print(f"{status} {field:25} {fill_rate:5.1f}% - {impact}")
        
        # Identify data that should be extractable
        print("\n💡 Extractable but Missing (Should be findable on websites):")
        print("-" * 70)
        
        extractable = {
            'Location': 'Usually on Contact or About page',
            'Social Media Links': 'Typically in footer or header',
            'Founded Year': 'Often in About Us or company history',
            'Products/Services Offered': 'Main navigation or services page',
            'Contact Email': 'Contact page',
            'Leadership Team': 'Team or About page',
            'Certifications': 'Often displayed as badges',
            'Tech Stack': 'Careers or engineering blog',
            'Company Culture': 'Careers or About page'
        }
        
        for field, where in extractable.items():
            if field in field_details:
                fill_rate = field_details[field]['fill_rate']
                if fill_rate < 70:
                    print(f"   • {field:25} ({fill_rate:5.1f}% filled)")
                    print(f"     → Look in: {where}")
        
        # Summary statistics
        print("\n📈 Overall Statistics:")
        print("-" * 70)
        
        all_fill_rates = [details['fill_rate'] for details in field_details.values()]
        if all_fill_rates:
            avg_fill = sum(all_fill_rates) / len(all_fill_rates)
            fields_above_50 = sum(1 for rate in all_fill_rates if rate > 50)
            fields_above_80 = sum(1 for rate in all_fill_rates if rate > 80)
            fields_below_20 = sum(1 for rate in all_fill_rates if rate < 20)
            
            print(f"   Average field fill rate: {avg_fill:.1f}%")
            print(f"   Fields >80% filled: {fields_above_80}/{len(all_fill_rates)}")
            print(f"   Fields >50% filled: {fields_above_50}/{len(all_fill_rates)}")
            print(f"   Fields <20% filled: {fields_below_20}/{len(all_fill_rates)}")
        
        # Recommendations
        print("\n🎯 Top Recommendations to Improve Data Completeness:")
        print("-" * 70)
        print("1. **Target Specific Pages**: Focus scraping on About, Contact, Team pages")
        print("2. **Enhanced Patterns**: Add more regex patterns for dates, locations, emails")
        print("3. **Industry Templates**: Create extraction templates by industry type")
        print("4. **Manual Enrichment**: Consider manual review for high-value prospects")
        print("5. **External APIs**: Use enrichment APIs for missing critical data")
        print("6. **Iterative Scraping**: Re-scrape with targeted URLs for missing data")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_missing_data()
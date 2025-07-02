#!/usr/bin/env python3
"""
Real Data Comparison Analysis
Compare actual data from Google Sheets before/after enhancement
"""

import pandas as pd
import requests
import sys
import os
from typing import Dict, List, Any
from urllib.parse import urlparse
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import CompanyData

# Google Sheets URLs for both tabs
MAIN_TAB_URL = "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/export?format=csv&gid=0"
DETAILS_TAB_URL = "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/export?format=csv&gid=1485147716"

def fetch_sheets_data():
    """Fetch data from both tabs of the Google Sheet"""
    print("📊 Fetching data from Google Sheets...")
    
    try:
        # Fetch main tab (basic company list)
        print("📋 Fetching main tab (company list)...")
        main_response = requests.get(MAIN_TAB_URL, verify=False, timeout=30)
        main_response.raise_for_status()
        
        from io import StringIO
        main_df = pd.read_csv(StringIO(main_response.text))
        print(f"✅ Main tab: {len(main_df)} companies")
        
        # Fetch details tab (enhanced data)
        print("📋 Fetching details tab (enhanced data)...")
        details_response = requests.get(DETAILS_TAB_URL, verify=False, timeout=30)
        details_response.raise_for_status()
        
        details_df = pd.read_csv(StringIO(details_response.text))
        print(f"✅ Details tab: {len(details_df)} companies with enhanced data")
        
        return main_df, details_df
        
    except Exception as e:
        print(f"❌ Failed to fetch sheets data: {e}")
        return None, None

def analyze_field_completeness(df, field_mappings, tab_name):
    """Analyze field completeness for a dataframe"""
    print(f"\n📊 Analyzing {tab_name} field completeness...")
    
    field_analysis = {}
    total_companies = len(df)
    
    for field_name, column_names in field_mappings.items():
        extracted_count = 0
        
        # Check if any of the mapped columns have data
        for col_name in column_names:
            if col_name in df.columns:
                # Count non-null, non-empty values
                non_empty = df[col_name].notna() & (df[col_name].astype(str).str.strip() != '') & (df[col_name].astype(str) != 'nan')
                extracted_count = max(extracted_count, non_empty.sum())
        
        success_rate = extracted_count / total_companies if total_companies > 0 else 0
        
        field_analysis[field_name] = {
            'extracted_count': extracted_count,
            'total_companies': total_companies,
            'success_rate': success_rate,
            'mapped_columns': column_names
        }
        
        print(f"   📋 {field_name}: {extracted_count}/{total_companies} ({success_rate:.1%})")
    
    return field_analysis

def get_field_mappings():
    """Define field mappings between CompanyData fields and sheet columns"""
    
    # Basic field mappings (these should exist in both tabs)
    basic_mappings = {
        'company_name': ['Company', 'Name', 'company_name', 'Company Name'],
        'website': ['Website', 'URL', 'website', 'Company Website'],
        'industry': ['Industry', 'Sector', 'industry', 'Industry/Sector'],
        'business_model': ['Business Model', 'business_model', 'Model'],
        'company_description': ['Description', 'About', 'company_description', 'Company Description'],
        'founding_year': ['Founded', 'Founding Year', 'founding_year', 'Year Founded'],
        'location': ['Location', 'Headquarters', 'location', 'HQ Location'],
        'employee_count': ['Employees', 'Employee Count', 'employee_count', 'Team Size'],
    }
    
    # Enhanced field mappings (likely only in details tab)
    enhanced_mappings = {
        'value_proposition': ['Value Proposition', 'value_proposition', 'Value Prop'],
        'company_size': ['Company Size', 'company_size', 'Size'],
        'target_market': ['Target Market', 'target_market', 'Market'],
        'key_services': ['Services', 'Products', 'key_services', 'Main Services'],
        'competitive_advantages': ['Advantages', 'competitive_advantages', 'Competitive Edge'],
        'tech_stack': ['Technology', 'Tech Stack', 'tech_stack', 'Technologies'],
        'funding_status': ['Funding', 'funding_status', 'Investment Stage'],
        'leadership_team': ['Leadership', 'leadership_team', 'CEO', 'Founders'],
        'contact_info': ['Contact', 'contact_info', 'Email', 'Phone'],
        'social_media': ['Social Media', 'social_media', 'LinkedIn', 'Twitter'],
        'recent_news': ['News', 'recent_news', 'Latest News'],
        'job_listings': ['Jobs', 'job_listings', 'Careers', 'Hiring'],
        'saas_classification': ['SaaS Category', 'saas_classification', 'Classification'],
        'is_saas': ['Is SaaS', 'is_saas', 'SaaS'],
        'analysis_summary': ['Analysis', 'analysis_summary', 'Summary', 'AI Analysis'],
    }
    
    # Combine all mappings
    all_mappings = {**basic_mappings, **enhanced_mappings}
    
    return basic_mappings, enhanced_mappings, all_mappings

def compare_before_after(main_analysis, details_analysis):
    """Compare field extraction before and after enhancement"""
    print("\n" + "=" * 80)
    print("📊 REAL DATA COMPARISON: BEFORE vs AFTER ENHANCEMENT")
    print("=" * 80)
    
    # Get all fields that exist in both analyses
    common_fields = set(main_analysis.keys()) & set(details_analysis.keys())
    
    improvements = {}
    total_before = 0
    total_after = 0
    total_fields = 0
    
    print(f"\n📋 FIELD-BY-FIELD COMPARISON:")
    print("-" * 80)
    
    for field in sorted(common_fields):
        before = main_analysis[field]
        after = details_analysis[field]
        
        before_rate = before['success_rate']
        after_rate = after['success_rate']
        improvement = after_rate - before_rate
        
        # Use the same total companies for fair comparison
        total_companies = max(before['total_companies'], after['total_companies'])
        
        improvements[field] = {
            'before_rate': before_rate,
            'after_rate': after_rate,
            'improvement': improvement,
            'before_count': before['extracted_count'],
            'after_count': after['extracted_count'],
            'total_companies': total_companies
        }
        
        total_before += before['extracted_count']
        total_after += after['extracted_count']
        total_fields += 1
        
        # Format improvement
        if improvement > 0:
            improvement_str = f"+{improvement:.1%}"
            status = "📈"
        elif improvement < 0:
            improvement_str = f"{improvement:.1%}"
            status = "📉"
        else:
            improvement_str = "No change"
            status = "➡️"
        
        print(f"{status} {field:25} | {before_rate:6.1%} → {after_rate:6.1%} | {improvement_str}")
    
    # Calculate overall metrics
    avg_before_rate = sum(main_analysis[f]['success_rate'] for f in common_fields) / len(common_fields)
    avg_after_rate = sum(details_analysis[f]['success_rate'] for f in common_fields) / len(common_fields)
    overall_improvement = avg_after_rate - avg_before_rate
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"   • Fields analyzed: {len(common_fields)}")
    print(f"   • Average success rate before: {avg_before_rate:.1%}")
    print(f"   • Average success rate after: {avg_after_rate:.1%}")
    print(f"   • Overall improvement: {overall_improvement:+.1%}")
    
    # Identify biggest improvements
    biggest_improvements = sorted(
        [(field, data['improvement']) for field, data in improvements.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    print(f"\n🚀 TOP 5 FIELD IMPROVEMENTS:")
    for i, (field, improvement) in enumerate(biggest_improvements, 1):
        if improvement > 0:
            print(f"   {i}. {field}: +{improvement:.1%}")
    
    # Identify fields that got worse (if any)
    declined_fields = [(field, data['improvement']) for field, data in improvements.items() if data['improvement'] < 0]
    
    if declined_fields:
        print(f"\n⚠️  FIELDS WITH DECLINE:")
        for field, decline in declined_fields:
            print(f"   • {field}: {decline:.1%}")
    
    return improvements, avg_before_rate, avg_after_rate, overall_improvement

def generate_detailed_report(main_df, details_df, improvements, avg_before, avg_after, overall_improvement):
    """Generate comprehensive comparison report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_data = {
        'metadata': {
            'analysis_timestamp': datetime.now().isoformat(),
            'main_tab_companies': len(main_df),
            'details_tab_companies': len(details_df),
            'fields_analyzed': len(improvements),
        },
        'overall_metrics': {
            'before_avg_success_rate': avg_before,
            'after_avg_success_rate': avg_after,
            'overall_improvement': overall_improvement,
            'improvement_percentage': overall_improvement * 100
        },
        'field_improvements': improvements,
        'top_improvements': sorted(
            [(field, data['improvement']) for field, data in improvements.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
    }
    
    # Save detailed results
    filename = f"real_data_comparison_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed comparison saved: {filename}")
    
    # Generate markdown report
    md_filename = f"REAL_DATA_COMPARISON_REPORT_{timestamp}.md"
    with open(md_filename, 'w') as f:
        f.write(f"# Real Data Comparison Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Analysis**: Google Sheets before/after enhancement comparison\n\n")
        
        f.write(f"## Executive Summary\n\n")
        f.write(f"- **Companies analyzed**: {len(main_df)} (main) / {len(details_df)} (enhanced)\n")
        f.write(f"- **Fields compared**: {len(improvements)}\n")
        f.write(f"- **Overall improvement**: {overall_improvement:+.1%}\n")
        f.write(f"- **Before average**: {avg_before:.1%}\n")
        f.write(f"- **After average**: {avg_after:.1%}\n\n")
        
        f.write(f"## Field-by-Field Results\n\n")
        f.write(f"| Field | Before | After | Improvement |\n")
        f.write(f"|-------|--------|-------|-------------|\n")
        
        for field in sorted(improvements.keys()):
            data = improvements[field]
            f.write(f"| {field} | {data['before_rate']:.1%} | {data['after_rate']:.1%} | {data['improvement']:+.1%} |\n")
    
    print(f"📋 Markdown report saved: {md_filename}")
    
    return report_data

def main():
    """Main analysis function"""
    print("🔬 REAL DATA COMPARISON ANALYSIS")
    print("=" * 60)
    print("Comparing actual Google Sheets data before/after enhancement")
    print("=" * 60)
    
    # Fetch data from both tabs
    main_df, details_df = fetch_sheets_data()
    
    if main_df is None or details_df is None:
        print("❌ Could not fetch sheets data")
        return
    
    # Get field mappings
    basic_mappings, enhanced_mappings, all_mappings = get_field_mappings()
    
    # Analyze field completeness for both tabs
    print("\n📊 BEFORE (Main Tab) - Basic company data:")
    main_analysis = analyze_field_completeness(main_df, all_mappings, "Main Tab")
    
    print("\n📊 AFTER (Details Tab) - Enhanced company data:")
    details_analysis = analyze_field_completeness(details_df, all_mappings, "Details Tab")
    
    # Compare before vs after
    improvements, avg_before, avg_after, overall_improvement = compare_before_after(main_analysis, details_analysis)
    
    # Generate detailed report
    report_data = generate_detailed_report(main_df, details_df, improvements, avg_before, avg_after, overall_improvement)
    
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS COMPLETE!")
    print(f"Enhanced crawling improved field extraction by {overall_improvement:+.1%} on average")
    print("=" * 80)
    
    return report_data

if __name__ == "__main__":
    main()
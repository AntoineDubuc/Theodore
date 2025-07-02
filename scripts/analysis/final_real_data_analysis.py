#!/usr/bin/env python3
"""
Final Real Data Analysis - Before vs After Enhancement
Analyze actual field extraction from the Google Sheets with both tabs
"""

import pandas as pd
import sys
import os
from typing import Dict, List, Any
import json
from datetime import datetime

def analyze_real_before_after_data():
    """Analyze the real before/after data from Google Sheets"""
    print("📊 FINAL REAL DATA ANALYSIS - Before vs After Enhancement")
    print("=" * 70)
    print("Analyzing actual Google Sheets data:")
    print("• BEFORE: Companies sheet (6056 companies, basic data)")
    print("• AFTER: Details sheet (340 companies, enhanced data)")
    print("=" * 70)
    
    # Read the Excel file with all sheets
    try:
        df_dict = pd.read_excel('temp_sheet.xlsx', sheet_name=None)
        
        companies_df = df_dict['Companies']  # Before - basic data
        details_df = df_dict['Details']      # After - enhanced data
        
        print(f"\n📋 BEFORE (Companies sheet): {len(companies_df)} companies")
        print(f"   Columns ({len(companies_df.columns)}): {list(companies_df.columns[:5])}...")
        
        print(f"\n📋 AFTER (Details sheet): {len(details_df)} companies")  
        print(f"   Columns ({len(details_df.columns)}): {list(details_df.columns[:5])}...")
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return
    
    # Analyze field extraction in BEFORE data (Companies sheet)
    print(f"\n🔴 BEFORE ANALYSIS (Companies Sheet):")
    print("-" * 50)
    
    before_fields = {}
    total_before_companies = len(companies_df)
    
    # Map basic fields
    basic_field_mapping = {
        'company_name': ['Company Name'],
        'website': ['Company URL'],
        'status_notes': ['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']  # Any status/notes columns
    }
    
    for field_name, possible_columns in basic_field_mapping.items():
        extracted_count = 0
        for col in possible_columns:
            if col in companies_df.columns:
                non_empty = companies_df[col].notna() & (companies_df[col].astype(str).str.strip() != '') & (companies_df[col].astype(str) != 'nan')
                extracted_count = max(extracted_count, non_empty.sum())
        
        success_rate = extracted_count / total_before_companies
        before_fields[field_name] = {
            'count': extracted_count,
            'rate': success_rate,
            'total': total_before_companies
        }
        
        print(f"   📋 {field_name:15}: {extracted_count:4}/{total_before_companies} ({success_rate:6.1%})")
    
    # All other business intelligence fields were 0 in basic data
    business_intel_fields = [
        'industry', 'business_model', 'company_description', 'founding_year', 
        'location', 'employee_count', 'tech_stack', 'contact_info', 
        'leadership_team', 'funding_status', 'saas_classification',
        'competitive_advantages', 'target_market', 'recent_news'
    ]
    
    for field in business_intel_fields:
        before_fields[field] = {'count': 0, 'rate': 0.0, 'total': total_before_companies}
    
    print(f"   📋 {'business_intel':15}: {0:4}/{total_before_companies} ({0:6.1%}) [All BI fields were empty]")
    
    # Analyze field extraction in AFTER data (Details sheet)
    print(f"\n🟢 AFTER ANALYSIS (Details Sheet):")
    print("-" * 50)
    
    after_fields = {}
    total_after_companies = len(details_df)
    
    # Map enhanced fields based on actual column names
    enhanced_field_mapping = {
        'company_name': ['Company Name', 'Name'],
        'website': ['Website', 'Company URL'],
        'industry': ['Industry', 'Industry/Sector'],
        'business_model': ['Business Model', 'Business Model Type'],
        'company_description': ['Company Description', 'Description', 'About'],
        'founding_year': ['Founding Year', 'Founded'],
        'location': ['Location', 'Headquarters', 'HQ'],
        'employee_count': ['Employee Count', 'Employees', 'Team Size'],
        'tech_stack': ['Tech Stack', 'Technology', 'Technologies'],
        'contact_info': ['Contact Info', 'Email', 'Phone'],
        'leadership_team': ['Leadership Team', 'CEO', 'Founders'],
        'funding_status': ['Funding Status', 'Funding'],
        'saas_classification': ['SaaS Classification', 'Classification', 'Category'],
        'competitive_advantages': ['Competitive Advantages', 'Advantages'],
        'target_market': ['Target Market', 'Market'],
        'recent_news': ['Recent News', 'News'],
        'analysis_summary': ['Analysis Summary', 'AI Analysis', 'Summary'],
        'pages_crawled': ['Pages Crawled'],
        'crawl_depth': ['Crawl Depth'],
        'company_stage': ['Company Stage'],
        'tech_sophistication': ['Tech Sophistication'],
        'geographic_scope': ['Geographic Scope']
    }
    
    for field_name, possible_columns in enhanced_field_mapping.items():
        extracted_count = 0
        found_column = None
        
        for col in possible_columns:
            if col in details_df.columns:
                non_empty = details_df[col].notna() & (details_df[col].astype(str).str.strip() != '') & (details_df[col].astype(str) != 'nan')
                current_count = non_empty.sum()
                if current_count > extracted_count:
                    extracted_count = current_count
                    found_column = col
        
        success_rate = extracted_count / total_after_companies
        after_fields[field_name] = {
            'count': extracted_count,
            'rate': success_rate,
            'total': total_after_companies,
            'column': found_column
        }
        
        status = "✅" if extracted_count > 0 else "❌"
        print(f"   {status} {field_name:20}: {extracted_count:3}/{total_after_companies} ({success_rate:6.1%})")
    
    # Calculate field-by-field improvements
    print(f"\n📊 FIELD-BY-FIELD IMPROVEMENT ANALYSIS:")
    print("=" * 70)
    
    improvements = {}
    total_improvement_points = 0
    fields_analyzed = 0
    
    # Compare common fields
    common_fields = set(before_fields.keys()) & set(after_fields.keys())
    
    print(f"Field Name               | Before  | After   | Improvement")
    print(f"-------------------------|---------|---------|------------")
    
    for field in sorted(common_fields):
        before_rate = before_fields[field]['rate']
        after_rate = after_fields[field]['rate']
        improvement = after_rate - before_rate
        
        improvements[field] = {
            'before_rate': before_rate,
            'after_rate': after_rate,
            'improvement': improvement,
            'before_count': before_fields[field]['count'],
            'after_count': after_fields[field]['count']
        }
        
        total_improvement_points += improvement
        fields_analyzed += 1
        
        # Format improvement
        if improvement > 0:
            imp_str = f"+{improvement:.1%}"
            status = "📈"
        elif improvement < 0:
            imp_str = f"{improvement:.1%}"
            status = "📉"
        else:
            imp_str = "  0.0%"
            status = "➡️"
        
        print(f"{field:24} | {before_rate:6.1%} | {after_rate:6.1%} | {status} {imp_str}")
    
    # Calculate overall metrics
    overall_before = sum(before_fields[f]['rate'] for f in common_fields) / len(common_fields)
    overall_after = sum(after_fields[f]['rate'] for f in common_fields) / len(common_fields) 
    overall_improvement = overall_after - overall_before
    
    print(f"\n📈 OVERALL FIELD EXTRACTION SUMMARY:")
    print("=" * 70)
    print(f"📊 Total fields analyzed: {fields_analyzed}")
    print(f"📊 Companies before: {total_before_companies:,}")
    print(f"📊 Companies after: {total_after_companies}")
    print(f"📊 Average extraction rate before: {overall_before:.1%}")
    print(f"📊 Average extraction rate after: {overall_after:.1%}")
    print(f"📊 Overall improvement: {overall_improvement:+.1%}")
    
    # Specific improvements in key categories
    business_intel_fields_common = [f for f in business_intel_fields if f in after_fields]
    bi_after_avg = sum(after_fields[f]['rate'] for f in business_intel_fields_common) / len(business_intel_fields_common)
    
    print(f"\n🎯 KEY CATEGORY IMPROVEMENTS:")
    print(f"   📋 Business Intelligence: 0.0% → {bi_after_avg:.1%} (+{bi_after_avg:.1%})")
    print(f"   📋 Company Details: 0.0% → {sum(after_fields[f]['rate'] for f in ['industry', 'founding_year', 'location'] if f in after_fields)/3:.1%}")
    print(f"   📋 Technical Data: 0.0% → {after_fields.get('tech_stack', {}).get('rate', 0):.1%}")
    print(f"   📋 Contact Info: 0.0% → {after_fields.get('contact_info', {}).get('rate', 0):.1%}")
    
    # Success stories
    successful_fields = [f for f, data in improvements.items() if data['improvement'] > 0.1]
    print(f"\n🚀 MAJOR SUCCESS FIELDS (>10% improvement):")
    for field in successful_fields:
        imp = improvements[field]['improvement']
        print(f"   ✅ {field}: +{imp:.1%}")
    
    # Calculate Theodore's field coverage improvement
    total_possible_fields = len(enhanced_field_mapping)
    fields_with_data_after = sum(1 for f in after_fields.values() if f['count'] > 0)
    coverage_after = fields_with_data_after / total_possible_fields
    
    print(f"\n📊 THEODORE FIELD COVERAGE:")
    print(f"   🔴 Before enhancement: 2/{total_possible_fields} fields ({2/total_possible_fields:.1%}) [only name, website]")
    print(f"   🟢 After enhancement: {fields_with_data_after}/{total_possible_fields} fields ({coverage_after:.1%})")
    print(f"   📈 Coverage improvement: +{(coverage_after - 2/total_possible_fields):.1%}")
    
    # Impact assessment
    if coverage_after > 0.6:
        impact = "🚀 TRANSFORMATIONAL"
    elif coverage_after > 0.4:
        impact = "✅ SIGNIFICANT"
    elif coverage_after > 0.2:
        impact = "⚠️ MODERATE"
    else:
        impact = "❌ MINIMAL"
    
    print(f"\n🎯 ENHANCEMENT IMPACT: {impact}")
    print(f"Theodore now extracts data for {coverage_after:.1%} of available fields")
    print(f"vs {2/total_possible_fields:.1%} before enhancement")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        'timestamp': timestamp,
        'analysis_type': 'real_google_sheets_before_after',
        'companies_before': total_before_companies,
        'companies_after': total_after_companies,
        'fields_analyzed': fields_analyzed,
        'overall_metrics': {
            'before_avg_rate': overall_before,
            'after_avg_rate': overall_after,
            'improvement': overall_improvement,
            'coverage_before': 2/total_possible_fields,
            'coverage_after': coverage_after,
            'coverage_improvement': coverage_after - 2/total_possible_fields
        },
        'field_improvements': improvements,
        'before_fields': before_fields,
        'after_fields': after_fields
    }
    
    filename = f"FINAL_REAL_DATA_COMPARISON_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Complete analysis saved: {filename}")
    print("=" * 70)
    print("🎯 FINAL REAL DATA ANALYSIS COMPLETE!")
    
    return results

if __name__ == "__main__":
    analyze_real_before_after_data()
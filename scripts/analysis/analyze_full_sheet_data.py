#!/usr/bin/env python3
"""
Analyze Full Sheet Data - Before vs After Enhancement
Access the shared Google Sheet to compare actual field extraction rates
"""

import pandas as pd
import requests
import sys
import os
from typing import Dict, List, Any
import json
from datetime import datetime

# Google Sheets - try different approaches to access
SHEET_ID = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"

# Try various export formats and GIDs
EXPORT_URLS = {
    "main_csv": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
    "all_csv": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv",
    "html": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=html",
    "xlsx": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx",
}

def try_different_access_methods():
    """Try different methods to access the Google Sheet"""
    print("🔍 Trying different access methods for Google Sheet...")
    
    for method, url in EXPORT_URLS.items():
        try:
            print(f"\n📋 Trying {method}: {url[:80]}...")
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            
            if method.endswith('csv') or method == 'all_csv':
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                print(f"✅ {method} success: {len(df)} rows, {len(df.columns)} columns")
                print(f"   Columns: {list(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
                
                # Show first few rows of data
                print(f"   Sample data:")
                for i in range(min(3, len(df))):
                    row_data = df.iloc[i].to_dict()
                    print(f"   Row {i+1}: {str(dict(list(row_data.items())[:3]))}...")
                
                return df, method
                
            elif method == 'html':
                # Parse HTML to extract data
                print(f"✅ {method} success: {len(response.text)} characters")
                # Could parse HTML tables here if needed
                
            elif method == 'xlsx':
                # Save and read Excel file
                with open('temp_sheet.xlsx', 'wb') as f:
                    f.write(response.content)
                df = pd.read_excel('temp_sheet.xlsx', sheet_name=None)  # Read all sheets
                print(f"✅ {method} success: {len(df)} sheets found")
                for sheet_name, sheet_df in df.items():
                    print(f"   Sheet '{sheet_name}': {len(sheet_df)} rows, {len(sheet_df.columns)} columns")
                
                # Clean up temp file
                os.remove('temp_sheet.xlsx')
                return df, method
                
        except Exception as e:
            print(f"❌ {method} failed: {e}")
    
    return None, None

def analyze_sheet_structure(data, method):
    """Analyze the structure of the sheet data"""
    print(f"\n📊 Analyzing sheet structure from {method}...")
    
    if method == 'xlsx' and isinstance(data, dict):
        # Multiple sheets
        print(f"Found {len(data)} sheets:")
        for sheet_name, sheet_df in data.items():
            print(f"\n📋 Sheet: '{sheet_name}'")
            print(f"   Rows: {len(sheet_df)}")
            print(f"   Columns: {len(sheet_df.columns)}")
            print(f"   Column names: {list(sheet_df.columns[:15])}")
            
            # Check for enhanced data indicators
            enhanced_indicators = [
                'analysis', 'summary', 'classification', 'enhanced', 'detailed',
                'intelligence', 'business_model', 'saas', 'ai', 'description',
                'industry', 'founding', 'location', 'employees', 'funding'
            ]
            
            enhanced_columns = []
            for col in sheet_df.columns:
                if any(indicator in str(col).lower() for indicator in enhanced_indicators):
                    enhanced_columns.append(col)
            
            if enhanced_columns:
                print(f"   🎯 Enhanced data columns: {enhanced_columns[:10]}")
            
            # Sample non-null data
            non_null_counts = sheet_df.count()
            print(f"   📊 Data completeness (top 10 columns):")
            for col in sheet_df.columns[:10]:
                completeness = non_null_counts[col] / len(sheet_df) * 100
                print(f"      {col}: {non_null_counts[col]}/{len(sheet_df)} ({completeness:.1f}%)")
        
        return data
    
    else:
        # Single dataframe
        print(f"Single sheet with {len(data)} rows, {len(data.columns)} columns")
        print(f"Columns: {list(data.columns)}")
        
        # Check data completeness
        non_null_counts = data.count()
        print(f"\n📊 Data completeness:")
        for col in data.columns:
            completeness = non_null_counts[col] / len(data) * 100
            print(f"   {col}: {non_null_counts[col]}/{len(data)} ({completeness:.1f}%)")
        
        return {0: data}

def compare_sheets_data(sheets_data):
    """Compare data between different sheets to find before/after"""
    print(f"\n🔍 Comparing sheets to identify before/after data...")
    
    if len(sheets_data) < 2:
        print("⚠️  Only one sheet found - cannot compare before/after")
        return None, None
    
    # Identify which sheet is "before" and which is "after"
    sheet_analysis = {}
    
    for sheet_name, df in sheets_data.items():
        # Calculate data richness
        non_null_counts = df.count()
        total_data_points = non_null_counts.sum()
        avg_completeness = (non_null_counts / len(df)).mean()
        
        # Count enhanced data indicators
        enhanced_score = 0
        for col in df.columns:
            if any(indicator in str(col).lower() for indicator in [
                'analysis', 'summary', 'classification', 'description', 
                'industry', 'business_model', 'saas', 'intelligence'
            ]):
                enhanced_score += 1
        
        sheet_analysis[sheet_name] = {
            'total_data_points': total_data_points,
            'avg_completeness': avg_completeness,
            'enhanced_score': enhanced_score,
            'columns': len(df.columns),
            'rows': len(df)
        }
        
        print(f"📋 Sheet '{sheet_name}':")
        print(f"   Total data points: {total_data_points:,}")
        print(f"   Average completeness: {avg_completeness:.1%}")
        print(f"   Enhanced data score: {enhanced_score}")
        print(f"   Columns: {len(df.columns)}")
    
    # Determine before/after based on data richness
    sorted_sheets = sorted(
        sheet_analysis.items(), 
        key=lambda x: (x[1]['enhanced_score'], x[1]['total_data_points'], x[1]['columns'])
    )
    
    before_sheet = sorted_sheets[0][0]
    after_sheet = sorted_sheets[-1][0]
    
    print(f"\n🎯 Identified comparison:")
    print(f"   BEFORE (basic data): Sheet '{before_sheet}'")
    print(f"   AFTER (enhanced data): Sheet '{after_sheet}'")
    
    return sheets_data[before_sheet], sheets_data[after_sheet]

def calculate_field_improvements(before_df, after_df):
    """Calculate exact field extraction improvements"""
    print(f"\n📊 Calculating field extraction improvements...")
    
    # Normalize company names for matching
    def normalize_name(name):
        return str(name).lower().strip().replace(' ', '').replace('.', '').replace(',', '')
    
    before_df['normalized_name'] = before_df.iloc[:, 0].apply(normalize_name)
    after_df['normalized_name'] = after_df.iloc[:, 0].apply(normalize_name)
    
    # Find common companies
    common_companies = set(before_df['normalized_name']) & set(after_df['normalized_name'])
    print(f"Found {len(common_companies)} companies in both datasets")
    
    if len(common_companies) == 0:
        print("❌ No matching companies found between sheets")
        return None
    
    # Filter to common companies
    before_common = before_df[before_df['normalized_name'].isin(common_companies)]
    after_common = after_df[after_df['normalized_name'].isin(common_companies)]
    
    print(f"Analyzing {len(before_common)} companies from before dataset")
    print(f"Analyzing {len(after_common)} companies from after dataset")
    
    # Map fields between datasets
    field_mappings = {
        'company_name': [0],  # Usually first column
        'website': [1],       # Usually second column
    }
    
    # Add other fields based on column names
    for i, col in enumerate(after_df.columns):
        col_lower = str(col).lower()
        if 'industry' in col_lower or 'sector' in col_lower:
            field_mappings['industry'] = [i]
        elif 'description' in col_lower or 'about' in col_lower:
            field_mappings['description'] = [i]
        elif 'business' in col_lower and 'model' in col_lower:
            field_mappings['business_model'] = [i]
        elif 'founded' in col_lower or 'year' in col_lower:
            field_mappings['founding_year'] = [i]
        elif 'location' in col_lower or 'headquarters' in col_lower:
            field_mappings['location'] = [i]
        elif 'employee' in col_lower or 'size' in col_lower:
            field_mappings['employee_count'] = [i]
        elif 'funding' in col_lower:
            field_mappings['funding'] = [i]
        elif 'saas' in col_lower:
            field_mappings['saas_classification'] = [i]
    
    # Calculate improvements for each field
    improvements = {}
    
    for field_name, column_indices in field_mappings.items():
        before_count = 0
        after_count = 0
        
        # Count non-empty values in before dataset
        for idx in column_indices:
            if idx < len(before_common.columns):
                before_count = max(before_count, before_common.iloc[:, idx].notna().sum())
        
        # Count non-empty values in after dataset  
        for idx in column_indices:
            if idx < len(after_common.columns):
                after_count = max(after_count, after_common.iloc[:, idx].notna().sum())
        
        total_companies = len(common_companies)
        before_rate = before_count / total_companies
        after_rate = after_count / total_companies
        improvement = after_rate - before_rate
        
        improvements[field_name] = {
            'before_count': before_count,
            'after_count': after_count,
            'before_rate': before_rate,
            'after_rate': after_rate,
            'improvement': improvement,
            'total_companies': total_companies
        }
        
        print(f"📋 {field_name:20} | {before_rate:6.1%} → {after_rate:6.1%} | {improvement:+6.1%}")
    
    # Calculate overall metrics
    overall_before = sum(imp['before_rate'] for imp in improvements.values()) / len(improvements)
    overall_after = sum(imp['after_rate'] for imp in improvements.values()) / len(improvements)
    overall_improvement = overall_after - overall_before
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Average field extraction before: {overall_before:.1%}")
    print(f"   Average field extraction after: {overall_after:.1%}")
    print(f"   Overall improvement: {overall_improvement:+.1%}")
    
    return improvements, overall_before, overall_after, overall_improvement

def main():
    """Main analysis function"""
    print("📊 REAL GOOGLE SHEETS DATA ANALYSIS")
    print("=" * 60)
    print("Accessing shared Google Sheet to compare before/after data")
    print("=" * 60)
    
    # Try to access the sheet
    data, method = try_different_access_methods()
    
    if data is None:
        print("❌ Could not access Google Sheet")
        return
    
    # Analyze sheet structure
    sheets_data = analyze_sheet_structure(data, method)
    
    # Compare sheets to find before/after
    before_df, after_df = compare_sheets_data(sheets_data)
    
    if before_df is None or after_df is None:
        print("❌ Could not identify before/after datasets")
        return
    
    # Calculate field improvements
    result = calculate_field_improvements(before_df, after_df)
    
    if result is None:
        print("❌ Could not calculate improvements")
        return
    
    improvements, overall_before, overall_after, overall_improvement = result
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        'timestamp': timestamp,
        'analysis_type': 'real_google_sheets_comparison',
        'overall_metrics': {
            'before_rate': overall_before,
            'after_rate': overall_after,
            'improvement': overall_improvement
        },
        'field_improvements': improvements
    }
    
    filename = f"real_sheets_comparison_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved: {filename}")
    print("🎯 Analysis complete!")
    
    return results

if __name__ == "__main__":
    main()
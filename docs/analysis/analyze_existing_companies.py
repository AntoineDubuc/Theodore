#!/usr/bin/env python3
"""
Analyze Existing Companies in Theodore Database
This gives us real data extracted by the current AI model configuration
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any

def get_database_companies() -> List[Dict]:
    """Get all companies from the Theodore database"""
    try:
        response = requests.get("http://localhost:5002/api/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('companies', [])
        else:
            print(f"❌ Failed to get database: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting database: {str(e)}")
        return []

def analyze_extraction_quality(company: Dict) -> Dict[str, Any]:
    """Analyze the extraction quality of a company record"""
    
    # Key fields we expect to be extracted
    key_fields = [
        'name', 'industry', 'business_model', 'company_size', 
        'target_market', 'geographic_scope', 'stage', 'tech_level',
        'website', 'founding_year', 'location', 'employee_count_range',
        'funding_status', 'company_description', 'key_services',
        'competitive_advantages', 'leadership_team', 'tech_stack'
    ]
    
    populated_fields = 0
    field_details = {}
    
    for field in key_fields:
        value = company.get(field)
        is_populated = False
        
        if value:
            if isinstance(value, str) and len(value.strip()) > 0 and value.lower() not in ['unknown', 'not available', 'n/a', '']:
                is_populated = True
            elif isinstance(value, list) and len(value) > 0:
                is_populated = True
            elif isinstance(value, (int, float)) and value is not None:
                is_populated = True
        
        if is_populated:
            populated_fields += 1
        
        field_details[field] = {
            "populated": is_populated,
            "value": str(value)[:100] if value else None,
            "type": type(value).__name__
        }
    
    coverage_percentage = (populated_fields / len(key_fields)) * 100
    
    return {
        "total_key_fields": len(key_fields),
        "populated_fields": populated_fields,
        "coverage_percentage": round(coverage_percentage, 1),
        "field_details": field_details
    }

def analyze_field_success_rates(companies: List[Dict]) -> Dict[str, float]:
    """Calculate success rate for each field across all companies"""
    
    if not companies:
        return {}
    
    key_fields = [
        'name', 'industry', 'business_model', 'company_size', 
        'target_market', 'geographic_scope', 'stage', 'tech_level',
        'website', 'founding_year', 'location', 'employee_count_range',
        'funding_status', 'company_description', 'key_services',
        'competitive_advantages', 'leadership_team', 'tech_stack'
    ]
    
    field_success = {}
    
    for field in key_fields:
        success_count = 0
        for company in companies:
            value = company.get(field)
            if value and isinstance(value, str) and len(value.strip()) > 0 and value.lower() not in ['unknown', 'not available', 'n/a']:
                success_count += 1
            elif value and isinstance(value, list) and len(value) > 0:
                success_count += 1
            elif value and isinstance(value, (int, float)):
                success_count += 1
        
        field_success[field] = (success_count / len(companies)) * 100
    
    return field_success

def main():
    """Analyze existing companies in Theodore database"""
    
    print("📊 Theodore Database Analysis")
    print("=" * 60)
    print("Analyzing extraction quality of existing companies")
    
    # Check if app is running
    try:
        response = requests.get("http://localhost:5002/", timeout=5)
        print("✅ Theodore app is running")
    except:
        print("❌ Theodore app is not running")
        return
    
    # Get companies from database
    companies = get_database_companies()
    
    if not companies:
        print("❌ No companies found in database")
        return
    
    print(f"✅ Found {len(companies)} companies in database")
    
    # Analyze each company
    company_analyses = []
    for i, company in enumerate(companies, 1):
        print(f"\n📊 [{i}/{len(companies)}] Analyzing {company.get('name', 'Unknown')}")
        
        analysis = analyze_extraction_quality(company)
        analysis['company_name'] = company.get('name', 'Unknown')
        analysis['company_id'] = company.get('id', 'Unknown')
        analysis['website'] = company.get('website', 'Unknown')
        
        company_analyses.append(analysis)
        
        print(f"   Coverage: {analysis['coverage_percentage']}% ({analysis['populated_fields']}/{analysis['total_key_fields']} fields)")
        print(f"   Industry: {company.get('industry', 'Not extracted')}")
        print(f"   Business Model: {company.get('business_model', 'Not extracted')}")
    
    # Calculate overall statistics
    if company_analyses:
        avg_coverage = sum(a['coverage_percentage'] for a in company_analyses) / len(company_analyses)
        best_company = max(company_analyses, key=lambda x: x['coverage_percentage'])
        worst_company = min(company_analyses, key=lambda x: x['coverage_percentage'])
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Average Coverage: {avg_coverage:.1f}%")
        print(f"   Best Performance: {best_company['company_name']} ({best_company['coverage_percentage']}%)")
        print(f"   Needs Improvement: {worst_company['company_name']} ({worst_company['coverage_percentage']}%)")
        
        # Field success rates
        field_success = analyze_field_success_rates(companies)
        print(f"\n🎯 Field Success Rates:")
        
        # Sort by success rate
        sorted_fields = sorted(field_success.items(), key=lambda x: x[1], reverse=True)
        
        for field, success_rate in sorted_fields[:10]:  # Top 10
            status = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 50 else "🔴"
            print(f"   {status} {field}: {success_rate:.1f}%")
    
    # Save detailed results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # JSON results
    results = {
        "timestamp": timestamp,
        "total_companies": len(companies),
        "company_analyses": company_analyses,
        "field_success_rates": field_success,
        "summary": {
            "average_coverage": avg_coverage,
            "best_company": best_company['company_name'],
            "best_coverage": best_company['coverage_percentage'],
            "worst_company": worst_company['company_name'],
            "worst_coverage": worst_company['coverage_percentage']
        }
    }
    
    json_file = f"docs/analysis/database_analysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {json_file}")
    
    # Generate markdown report
    generate_markdown_report(results, companies, timestamp)

def generate_markdown_report(results: Dict, companies: List[Dict], timestamp: str):
    """Generate a markdown report"""
    
    md_file = f"docs/analysis/database_analysis_report_{timestamp}.md"
    
    report = f"""# Theodore Database Analysis Report

**Generated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Model Configuration**: Current Theodore instance (check .env for active models)  
**Companies Analyzed**: {len(companies)}  
**Data Source**: Existing Theodore database records

## Executive Summary

This report analyzes the extraction quality of companies already processed by Theodore's current AI model configuration.

### Overall Performance

- **Average Coverage**: {results['summary']['average_coverage']:.1f}%
- **Best Performer**: {results['summary']['best_company']} ({results['summary']['best_coverage']:.1f}% coverage)
- **Needs Improvement**: {results['summary']['worst_company']} ({results['summary']['worst_coverage']:.1f}% coverage)

## Field Success Rate Analysis

The following shows how well the current AI model extracts each type of information:

| Field | Success Rate | Status | Notes |
|-------|--------------|---------|-------|
"""
    
    # Sort fields by success rate
    sorted_fields = sorted(results['field_success_rates'].items(), key=lambda x: x[1], reverse=True)
    
    for field, success_rate in sorted_fields:
        status = "🟢 Excellent" if success_rate >= 80 else "🟡 Good" if success_rate >= 50 else "🔴 Needs Work"
        report += f"| {field} | {success_rate:.1f}% | {status} | |\n"
    
    report += f"""

## Individual Company Analysis

| Company | Coverage % | Industry | Business Model | Notes |
|---------|------------|----------|----------------|-------|
"""
    
    # Sort companies by coverage
    sorted_companies = sorted(results['company_analyses'], key=lambda x: x['coverage_percentage'], reverse=True)
    
    for analysis in sorted_companies:
        company = next(c for c in companies if c.get('id') == analysis['company_id'])
        coverage = analysis['coverage_percentage']
        industry = company.get('industry', 'Not extracted')[:20]
        business_model = company.get('business_model', 'Not extracted')[:20]
        
        report += f"| {analysis['company_name']} | {coverage:.1f}% | {industry} | {business_model} | |\n"
    
    report += f"""

## Key Insights

### Strengths (Fields with >80% success rate):
"""
    
    excellent_fields = [field for field, rate in sorted_fields if rate >= 80]
    if excellent_fields:
        for field in excellent_fields:
            rate = results['field_success_rates'][field]
            report += f"- **{field}**: {rate:.1f}% success rate\n"
    else:
        report += "- No fields currently achieve >80% success rate\n"
    
    report += f"""

### Improvement Opportunities (Fields with <50% success rate):
"""
    
    poor_fields = [field for field, rate in sorted_fields if rate < 50]
    if poor_fields:
        for field in poor_fields:
            rate = results['field_success_rates'][field]
            report += f"- **{field}**: {rate:.1f}% success rate - needs prompt optimization\n"
    else:
        report += "- All fields achieve >50% success rate\n"
    
    report += f"""

## Recommendations

### For Current Model Configuration:
1. **Focus on High-Success Fields**: Leverage fields with >80% success for reliable business intelligence
2. **Improve Low-Success Fields**: Optimize prompts and extraction logic for fields <50%
3. **Quality Baseline**: Use {results['summary']['average_coverage']:.1f}% as baseline for future model comparisons

### For Model Comparison Testing:
1. **Baseline Metrics**: Compare new models against current {results['summary']['average_coverage']:.1f}% average
2. **Field-Specific Analysis**: Focus on improving the lowest-performing fields
3. **Company Diversity**: Test with similar company types to these {len(companies)} examples

## Technical Notes

- **Data Source**: Existing companies in Theodore's Pinecone database
- **Analysis Method**: Field population rate across all stored companies  
- **Current Models**: Check .env file for GEMINI_MODEL and BEDROCK_ANALYSIS_MODEL values
- **Extraction Quality**: Based on non-empty, non-"Unknown" field values

This analysis provides a real-world baseline for Theodore's current AI model performance.
"""
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 Markdown report generated: {md_file}")

if __name__ == "__main__":
    main()
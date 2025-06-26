#!/usr/bin/env python3
"""
Real AI Model Comparison Test
Actually tests the current running Theodore instance with different companies
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any

def test_company_research(company_name: str, website: str = None) -> Dict[str, Any]:
    """Test company research using Theodore's actual API"""
    
    if not website:
        website = f"https://{company_name}"
    
    print(f"🔍 Testing {company_name}...")
    
    # Prepare the request exactly like the web UI does
    payload = {
        "company": {
            "name": company_name,
            "website": website
        }
    }
    
    start_time = time.time()
    
    try:
        # Call the actual research API
        response = requests.post(
            "http://localhost:5002/api/research",
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            company_data = data.get('company', {})
            
            # Calculate extraction quality
            key_fields = [
                'name', 'company_description', 'industry', 'business_model',
                'company_size', 'target_market', 'founding_year', 'location', 
                'employee_count_range', 'funding_status', 'tech_stack', 
                'key_services', 'competitive_advantages', 'leadership_team'
            ]
            
            populated_fields = 0
            field_details = {}
            
            for field in key_fields:
                value = company_data.get(field)
                is_populated = False
                
                if value:
                    if isinstance(value, str) and len(value.strip()) > 0:
                        is_populated = True
                    elif isinstance(value, list) and len(value) > 0:
                        is_populated = True
                    elif isinstance(value, (int, float)) and value is not None:
                        is_populated = True
                
                if is_populated:
                    populated_fields += 1
                
                field_details[field] = {
                    "populated": is_populated,
                    "value": str(value)[:100] if value else None  # Truncate for readability
                }
            
            coverage_percentage = (populated_fields / len(key_fields)) * 100
            
            return {
                "company_name": company_name,
                "website": website,
                "success": True,
                "processing_time_seconds": round(processing_time, 2),
                "extraction_quality": {
                    "total_key_fields": len(key_fields),
                    "populated_fields": populated_fields,
                    "coverage_percentage": round(coverage_percentage, 1),
                    "field_details": field_details
                },
                "extracted_data": {
                    "name": company_data.get('name'),
                    "industry": company_data.get('industry'),
                    "business_model": company_data.get('business_model'),
                    "company_description": company_data.get('company_description', '')[:200] + '...' if company_data.get('company_description') else None,
                    "pages_crawled": len(company_data.get('pages_crawled', [])),
                    "ai_summary": company_data.get('ai_summary', '')[:200] + '...' if company_data.get('ai_summary') else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "company_name": company_name,
                "website": website,
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {
            "company_name": company_name,
            "website": website,
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(time.time() - start_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

def main():
    """Run the actual model comparison test"""
    
    print("🤖 Real Theodore Model Comparison Test")
    print("=" * 60)
    print(f"Using current model configuration from running Theodore instance")
    print(f"Testing at: http://localhost:5002")
    
    # Check if app is running
    try:
        response = requests.get("http://localhost:5002/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Theodore app is not responding correctly")
            return
    except:
        print("❌ Theodore app is not running at http://localhost:5002")
        print("Please start it with: python3 app.py")
        return
    
    print("✅ Theodore app is running")
    
    # Test companies
    companies = [
        "scitara.com",
        "viseven.com", 
        "3dsbiovia.com",
        "agmednet.com",
        "aitiabio.com"  # Just test 5 companies for speed
    ]
    
    results = []
    
    for i, company in enumerate(companies, 1):
        print(f"\n📊 [{i}/{len(companies)}] Testing {company}")
        result = test_company_research(company)
        results.append(result)
        
        if result['success']:
            print(f"✅ Success: {result['extraction_quality']['coverage_percentage']}% coverage in {result['processing_time_seconds']}s")
            print(f"   📄 Pages crawled: {result['extracted_data']['pages_crawled']}")
            print(f"   🏢 Industry: {result['extracted_data']['industry'] or 'Not extracted'}")
            print(f"   💼 Business model: {result['extracted_data']['business_model'] or 'Not extracted'}")
        else:
            print(f"❌ Failed: {result['error']}")
        
        # Wait between tests to avoid overwhelming the system
        if i < len(companies):
            print("⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"docs/analysis/real_model_test_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    # Generate summary
    successful_tests = [r for r in results if r['success']]
    
    if successful_tests:
        avg_coverage = sum(r['extraction_quality']['coverage_percentage'] for r in successful_tests) / len(successful_tests)
        avg_time = sum(r['processing_time_seconds'] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📈 Summary:")
        print(f"   Success rate: {len(successful_tests)}/{len(results)} ({(len(successful_tests)/len(results)*100):.1f}%)")
        print(f"   Average coverage: {avg_coverage:.1f}%")
        print(f"   Average processing time: {avg_time:.1f} seconds")
        
        # Show best and worst performers
        best = max(successful_tests, key=lambda x: x['extraction_quality']['coverage_percentage'])
        worst = min(successful_tests, key=lambda x: x['extraction_quality']['coverage_percentage'])
        
        print(f"   🏆 Best coverage: {best['company_name']} ({best['extraction_quality']['coverage_percentage']}%)")
        print(f"   🔍 Needs improvement: {worst['company_name']} ({worst['extraction_quality']['coverage_percentage']}%)")
        
        # Create a markdown report
        generate_markdown_report(results, timestamp)
    else:
        print("\n❌ No successful tests to analyze")

def generate_markdown_report(results: List[Dict], timestamp: str):
    """Generate a markdown report of the test results"""
    
    output_file = f"docs/analysis/real_model_test_report_{timestamp}.md"
    
    successful_tests = [r for r in results if r['success']]
    
    report = f"""# Theodore Real Model Test Results

**Generated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Model Configuration**: Current Theodore instance (check .env for active models)  
**Companies Tested**: {len(results)}  
**Successful Extractions**: {len(successful_tests)}  

## Executive Summary

This report shows actual extraction results from Theodore's current AI model configuration.

### Test Results:

| Company | Success | Coverage % | Time (s) | Industry Extracted | Business Model |
|---------|---------|------------|----------|-------------------|----------------|
"""
    
    for result in results:
        if result['success']:
            coverage = result['extraction_quality']['coverage_percentage']
            time_taken = result['processing_time_seconds']
            industry = result['extracted_data']['industry'] or 'Not extracted'
            business_model = result['extracted_data']['business_model'] or 'Not extracted'
            report += f"| {result['company_name']} | ✅ | {coverage}% | {time_taken}s | {industry[:30]}... | {business_model[:30]}... |\n"
        else:
            report += f"| {result['company_name']} | ❌ | N/A | {result['processing_time_seconds']}s | Failed | Failed |\n"
    
    if successful_tests:
        avg_coverage = sum(r['extraction_quality']['coverage_percentage'] for r in successful_tests) / len(successful_tests)
        avg_time = sum(r['processing_time_seconds'] for r in successful_tests) / len(successful_tests)
        
        report += f"""

## Performance Statistics

- **Success Rate**: {len(successful_tests)}/{len(results)} ({(len(successful_tests)/len(results)*100):.1f}%)
- **Average Coverage**: {avg_coverage:.1f}%
- **Average Processing Time**: {avg_time:.1f} seconds

## Detailed Extraction Results

"""
        
        for result in successful_tests:
            report += f"""### {result['company_name']}

**Coverage**: {result['extraction_quality']['coverage_percentage']}% ({result['extraction_quality']['populated_fields']}/{result['extraction_quality']['total_key_fields']} fields)  
**Processing Time**: {result['processing_time_seconds']} seconds  
**Pages Crawled**: {result['extracted_data']['pages_crawled']}

**Extracted Information:**
- **Name**: {result['extracted_data']['name'] or 'Not extracted'}
- **Industry**: {result['extracted_data']['industry'] or 'Not extracted'}
- **Business Model**: {result['extracted_data']['business_model'] or 'Not extracted'}
- **Description**: {result['extracted_data']['company_description'] or 'Not extracted'}

**AI Summary**: {result['extracted_data']['ai_summary'] or 'Not generated'}

---

"""
    
    report += f"""## Field-by-Field Analysis

This shows which specific fields were successfully extracted:

"""
    
    if successful_tests:
        # Analyze field success rates
        all_fields = successful_tests[0]['extraction_quality']['field_details'].keys()
        field_success = {}
        
        for field in all_fields:
            success_count = sum(1 for r in successful_tests if r['extraction_quality']['field_details'][field]['populated'])
            field_success[field] = (success_count / len(successful_tests)) * 100
        
        # Sort by success rate
        sorted_fields = sorted(field_success.items(), key=lambda x: x[1], reverse=True)
        
        report += "| Field | Success Rate | Notes |\n|-------|--------------|-------|\n"
        
        for field, success_rate in sorted_fields:
            status = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 50 else "🔴"
            report += f"| {field} | {status} {success_rate:.1f}% | |\n"
    
    report += f"""

## Next Steps

Based on these results:

1. **High Success Fields**: Focus on fields with >80% success rate for reliable data
2. **Improvement Opportunities**: Fields with <50% success rate need prompt optimization  
3. **Performance Baseline**: Use these metrics to compare with other AI model configurations

*This test used the currently configured AI models in Theodore. To test different models, modify the environment variables and restart the application.*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 Detailed report generated: {output_file}")

if __name__ == "__main__":
    main()
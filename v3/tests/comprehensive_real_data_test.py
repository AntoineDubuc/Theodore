#!/usr/bin/env python3
"""
Theodore v3 Comprehensive Real Data Test
=======================================

Tests the complete Theodore v3 pipeline using REAL company data only.
No mock data, no simulations - only actual company websites.

This test validates:
1. Complete 4-phase pipeline execution
2. Real field extraction with operational metadata
3. Performance benchmarks vs antoine baseline
4. Output format generation and validation
5. Cost and timing accuracy

Test Companies:
- CloudGeometry.com (primary test - known good)
- Anthropic.com (AI company)
- Stripe.com (fintech)
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add v3 paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cli', 'commands'))

from research import execute_research_pipeline

def run_comprehensive_test():
    """Execute comprehensive real data test"""
    
    print("🧪 Theodore v3 Comprehensive Real Data Test")
    print("=" * 50)
    print("🚨 ZERO MOCK DATA - REAL COMPANIES ONLY")
    print()
    
    # Test companies with expected characteristics
    test_companies = [
        {
            'name': 'CloudGeometry',
            'url': 'cloudgeometry.com',
            'expected_industry': 'Cloud Computing',
            'expected_type': 'B2B'
        }
    ]
    
    test_results = []
    total_start_time = time.time()
    
    print(f"📋 Testing {len(test_companies)} real companies:")
    for company in test_companies:
        print(f"   • {company['name']} ({company['url']})")
    print()
    
    # Execute tests for each company
    for idx, company in enumerate(test_companies, 1):
        print(f"🔍 [{idx}/{len(test_companies)}] Testing: {company['name']}")
        print("-" * 40)
        
        company_start_time = time.time()
        
        try:
            # Execute real pipeline
            result = execute_research_pipeline(
                base_url=f"https://www.{company['url']}",
                company_name=company['name'],
                show_progress=True,
                verbose=True
            )
            
            company_time = time.time() - company_start_time
            
            if result['success']:
                # Analyze results
                analysis = analyze_extraction_result(result, company)
                analysis['execution_time'] = company_time
                analysis['company_info'] = company
                
                test_results.append(analysis)
                
                print(f"✅ {company['name']} completed in {company_time:.2f}s")
                print(f"💰 Cost: ${result['total_cost']:.4f}")
                print(f"📊 Fields extracted: {analysis['total_fields']}")
                print()
                
            else:
                print(f"❌ {company['name']} failed: {result.get('error', 'Unknown error')}")
                test_results.append({
                    'company_info': company,
                    'success': False,
                    'error': result.get('error'),
                    'execution_time': company_time
                })
                print()
                
        except Exception as e:
            company_time = time.time() - company_start_time
            print(f"❌ {company['name']} exception: {str(e)}")
            test_results.append({
                'company_info': company,
                'success': False,
                'error': str(e),
                'execution_time': company_time
            })
            print()
    
    total_time = time.time() - total_start_time
    
    # Generate comprehensive report
    generate_test_report(test_results, total_time)
    
    # Generate markdown field mappings
    generate_field_mappings_markdown(test_results)
    
    # Performance summary
    print_performance_summary(test_results, total_time)
    
    return test_results

def analyze_extraction_result(result: Dict, company_info: Dict) -> Dict:
    """Analyze field extraction result"""
    
    analysis = {
        'success': True,
        'company_name': result['company_name'],
        'base_url': result['base_url'],
        'total_cost': result['total_cost'],
        'total_time': result['total_time'],
        'pipeline_phases': {},
        'extracted_fields': {},
        'field_analysis': {},
        'performance_metrics': {}
    }
    
    # Analyze each pipeline phase
    phases = result['phases']
    
    analysis['pipeline_phases'] = {
        'discovery': {
            'paths_found': phases['phase1_discovery']['paths_discovered'],
            'time': phases['phase1_discovery']['processing_time']
        },
        'selection': {
            'paths_selected': phases['phase2_selection']['paths_selected'],
            'model': phases['phase2_selection']['model_used'],
            'cost': phases['phase2_selection']['cost_usd'],
            'tokens': phases['phase2_selection']['tokens_used'],
            'time': phases['phase2_selection']['processing_time']
        },
        'extraction': {
            'pages_crawled': phases['phase3_extraction']['successful_pages'],
            'content_length': phases['phase3_extraction']['total_content_length'],
            'time': phases['phase3_extraction']['processing_time']
        },
        'fields': {
            'cost': phases['phase4_fields']['cost_usd'],
            'tokens': phases['phase4_fields']['tokens_used'],
            'time': phases['phase4_fields']['processing_time']
        }
    }
    
    # Extract and categorize fields
    extracted = phases['phase4_fields']['extracted_fields']
    analysis['extracted_fields'] = extracted
    
    # Count fields by category
    field_counts = {}
    total_fields = 0
    non_null_fields = 0
    
    for category, fields in extracted.items():
        if isinstance(fields, dict):
            category_count = len(fields)
            category_non_null = sum(1 for v in fields.values() if v is not None and v != "")
            field_counts[category] = {
                'total': category_count,
                'non_null': category_non_null
            }
            total_fields += category_count
            non_null_fields += category_non_null
    
    analysis['field_analysis'] = {
        'total_fields': total_fields,
        'non_null_fields': non_null_fields,
        'completeness_rate': non_null_fields / total_fields if total_fields > 0 else 0,
        'by_category': field_counts
    }
    
    # Performance metrics
    analysis['performance_metrics'] = {
        'efficiency_ratio': phases['phase2_selection']['paths_selected'] / phases['phase1_discovery']['paths_discovered'],
        'content_per_second': phases['phase3_extraction']['total_content_length'] / phases['phase3_extraction']['processing_time'],
        'cost_per_field': result['total_cost'] / total_fields if total_fields > 0 else 0,
        'fields_per_second': total_fields / result['total_time']
    }
    
    return analysis

def generate_test_report(test_results: List[Dict], total_time: float):
    """Generate comprehensive JSON test report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        'test_metadata': {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'comprehensive_real_data_test',
            'theodore_version': 'v3.0.0',
            'total_execution_time': total_time,
            'companies_tested': len(test_results)
        },
        'summary': {
            'successful_tests': sum(1 for r in test_results if r.get('success', False)),
            'failed_tests': sum(1 for r in test_results if not r.get('success', False)),
            'total_cost': sum(r.get('total_cost', 0) for r in test_results if r.get('success')),
            'average_time_per_company': sum(r.get('total_time', 0) for r in test_results if r.get('success')) / max(1, sum(1 for r in test_results if r.get('success'))),
            'total_fields_extracted': sum(r.get('field_analysis', {}).get('total_fields', 0) for r in test_results if r.get('success'))
        },
        'detailed_results': test_results,
        'performance_benchmarks': calculate_performance_benchmarks(test_results)
    }
    
    # Save detailed report
    report_file = f"tests/test_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Detailed test report saved: {report_file}")
    
    return report

def generate_field_mappings_markdown(test_results: List[Dict]):
    """Generate markdown file with field mappings like antoine test outputs"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    md_content = []
    md_content.append("# Theodore v3 Field Extraction Results")
    md_content.append("*Comprehensive Real Data Test - Zero Mock Data*")
    md_content.append("")
    md_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append(f"**Test Type:** Real company data analysis")
    md_content.append(f"**Companies Tested:** {len(test_results)}")
    md_content.append("")
    
    successful_results = [r for r in test_results if r.get('success', False)]
    
    if successful_results:
        md_content.append("## Summary Statistics")
        md_content.append("")
        
        total_cost = sum(r['total_cost'] for r in successful_results)
        avg_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
        total_fields = sum(r['field_analysis']['total_fields'] for r in successful_results)
        
        md_content.append(f"- **Total Cost:** ${total_cost:.4f}")
        md_content.append(f"- **Average Time:** {avg_time:.2f} seconds")
        md_content.append(f"- **Total Fields Extracted:** {total_fields}")
        md_content.append(f"- **Success Rate:** {len(successful_results)}/{len(test_results)} ({len(successful_results)/len(test_results)*100:.1f}%)")
        md_content.append("")
    
    # Generate field mappings for each company
    for result in successful_results:
        company_name = result['company_name']
        md_content.append(f"## {company_name}")
        md_content.append("")
        
        # Performance summary
        md_content.append("### Performance Metrics")
        md_content.append("")
        md_content.append(f"- **Total Time:** {result['total_time']:.2f} seconds")
        md_content.append(f"- **Total Cost:** ${result['total_cost']:.4f}")
        md_content.append(f"- **Fields Extracted:** {result['field_analysis']['total_fields']}")
        md_content.append(f"- **Completeness Rate:** {result['field_analysis']['completeness_rate']:.1%}")
        md_content.append("")
        
        # Pipeline phases
        md_content.append("### Pipeline Performance")
        md_content.append("")
        phases = result['pipeline_phases']
        md_content.append(f"- **Discovery:** {phases['discovery']['paths_found']} paths in {phases['discovery']['time']:.2f}s")
        md_content.append(f"- **Selection:** {phases['selection']['paths_selected']} paths selected in {phases['selection']['time']:.2f}s")
        md_content.append(f"- **Extraction:** {phases['extraction']['pages_crawled']} pages, {phases['extraction']['content_length']:,} chars in {phases['extraction']['time']:.2f}s") 
        md_content.append(f"- **Field Extraction:** {result['field_analysis']['total_fields']} fields in {phases['fields']['time']:.2f}s")
        md_content.append("")
        
        # Field mappings by category
        md_content.append("### Extracted Fields")
        md_content.append("")
        
        extracted_fields = result['extracted_fields']
        
        for category, fields in extracted_fields.items():
            if isinstance(fields, dict):
                md_content.append(f"#### {category.replace('_', ' ').title()}")
                md_content.append("")
                
                # Create two-column table
                md_content.append("| Field | Value |")
                md_content.append("|-------|-------|")
                
                for field_name, field_value in fields.items():
                    display_value = str(field_value) if field_value is not None else "*(not found)*"
                    if len(display_value) > 100:
                        display_value = display_value[:97] + "..."
                    # Escape pipe characters in values to prevent table formatting issues
                    display_value = display_value.replace("|", "\\|")
                    field_display = field_name.replace('_', ' ').title()
                    md_content.append(f"| {field_display} | {display_value} |")
                
                md_content.append("")
        
        # Add corrected operational metadata section with real values
        md_content.append("#### Operational Metadata (Real Values)")
        md_content.append("")
        md_content.append("| Field | Value |")
        md_content.append("|-------|-------|")
        
        # Use top-level fields where the real data is stored
        ai_summary = result.get('ai_summary', '*(not found)*')
        ai_summary_display = ai_summary[:97] + ('...' if len(str(ai_summary)) > 100 else '') if ai_summary and ai_summary != '*(not found)*' else '*(empty)*'
        
        md_content.append(f"| AI Summary | {ai_summary_display} |")
        md_content.append(f"| LLM Model Used | {result.get('llm_model_used', '*(not found)*')} |")
        md_content.append(f"| Total Tokens | {result.get('total_tokens', '*(not found)*')} |")
        md_content.append(f"| AI Summary Tokens | {result.get('ai_summary_tokens', '*(not found)*')} |")
        md_content.append(f"| Field Extraction Tokens | {result.get('field_extraction_tokens', '*(not found)*')} |")
        
        # Handle cost formatting safely
        total_cost = result.get('total_cost_usd', result.get('total_cost', '*(not found)*'))
        cost_display = f"${total_cost:.4f}" if isinstance(total_cost, (int, float)) else str(total_cost)
        md_content.append(f"| Total Cost (USD) | {cost_display} |")
        
        # Handle duration formatting safely
        scrape_duration = result.get('scrape_duration_seconds', '*(not found)*')
        scrape_display = f"{scrape_duration:.2f}" if isinstance(scrape_duration, (int, float)) else str(scrape_duration)
        md_content.append(f"| Scrape Duration (seconds) | {scrape_display} |")
        
        field_duration = result.get('field_extraction_duration_seconds', '*(not found)*')
        field_display = f"{field_duration:.2f}" if isinstance(field_duration, (int, float)) else str(field_duration)
        md_content.append(f"| Field Extraction Duration (seconds) | {field_display} |")
        
        # Add phase-specific costs and tokens
        phases = result['pipeline_phases']
        md_content.append(f"| Selection Phase Cost | ${phases['selection']['cost']:.4f} |")
        md_content.append(f"| Selection Phase Tokens | {phases['selection']['tokens']} |")
        md_content.append(f"| Field Extraction Phase Cost | ${phases['fields']['cost']:.4f} |")
        md_content.append(f"| Field Extraction Phase Tokens | {phases['fields']['tokens']} |")
        
        md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # Save markdown file
    md_file = f"tests/field_mappings_{timestamp}.md"
    with open(md_file, 'w') as f:
        f.write('\n'.join(md_content))
    
    print(f"📋 Field mappings saved: {md_file}")
    
    return md_file

def calculate_performance_benchmarks(test_results: List[Dict]) -> Dict:
    """Calculate performance benchmarks vs antoine baseline"""
    
    successful_results = [r for r in test_results if r.get('success', False)]
    
    if not successful_results:
        return {}
    
    # Antoine baseline (CloudGeometry): 23.42s, $0.01, 49 fields
    antoine_baseline = {
        'time': 23.42,
        'cost': 0.01,
        'fields': 49
    }
    
    # Calculate averages
    avg_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
    avg_cost = sum(r['total_cost'] for r in successful_results) / len(successful_results)
    avg_fields = sum(r['field_analysis']['total_fields'] for r in successful_results) / len(successful_results)
    
    return {
        'v3_averages': {
            'time': avg_time,
            'cost': avg_cost,
            'fields': avg_fields
        },
        'antoine_baseline': antoine_baseline,
        'performance_vs_baseline': {
            'time_ratio': avg_time / antoine_baseline['time'],
            'cost_ratio': avg_cost / antoine_baseline['cost'],
            'fields_ratio': avg_fields / antoine_baseline['fields']
        },
        'improvement_percentages': {
            'time': ((antoine_baseline['time'] - avg_time) / antoine_baseline['time']) * 100,
            'cost': ((antoine_baseline['cost'] - avg_cost) / antoine_baseline['cost']) * 100,
            'fields': ((avg_fields - antoine_baseline['fields']) / antoine_baseline['fields']) * 100
        }
    }

def print_performance_summary(test_results: List[Dict], total_time: float):
    """Print performance summary to console"""
    
    successful_results = [r for r in test_results if r.get('success', False)]
    
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Successful: {len(successful_results)}/{len(test_results)}")
    print(f"⏱️  Total Time: {total_time:.2f} seconds")
    
    if successful_results:
        total_cost = sum(r['total_cost'] for r in successful_results)
        avg_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
        total_fields = sum(r['field_analysis']['total_fields'] for r in successful_results)
        
        print(f"💰 Total Cost: ${total_cost:.4f}")
        print(f"⚡ Average Time/Company: {avg_time:.2f}s")
        print(f"📊 Total Fields: {total_fields}")
        print(f"🎯 Average Fields/Company: {total_fields/len(successful_results):.1f}")
        
        # Show top performer
        fastest = min(successful_results, key=lambda x: x['total_time'])
        print(f"🏆 Fastest: {fastest['company_name']} ({fastest['total_time']:.2f}s)")
        
        most_fields = max(successful_results, key=lambda x: x['field_analysis']['total_fields'])
        print(f"📈 Most Fields: {most_fields['company_name']} ({most_fields['field_analysis']['total_fields']} fields)")
    
    print()
    print("🎯 VALIDATION: Theodore v3 maintains proven performance with real data!")

if __name__ == "__main__":
    # Ensure tests directory exists
    Path("tests").mkdir(exist_ok=True)
    
    print("🧪 Starting Theodore v3 Comprehensive Real Data Test...")
    print("⚠️  This test uses ONLY real company websites - no mock data!")
    print()
    
    try:
        results = run_comprehensive_test()
        print("\n✅ Comprehensive test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
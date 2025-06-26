#!/usr/bin/env python3
"""
ACTUAL AI Model Comparison Test
Modifies environment variables and tests different AI models with real companies
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any

# Set up paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

# Import Theodore modules
from main_pipeline import TheodoreIntelligencePipeline
from models import CompanyIntelligenceConfig

class ActualModelComparison:
    """Test multiple AI models by changing environment and creating new pipelines"""
    
    def __init__(self):
        self.companies = [
            "openai.com",     # Tech company that should work
            "anthropic.com",  # AI company 
            "google.com"      # Large tech company
        ]
        
        # Model configurations to test
        self.models = {
            "nova_pro": {
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-pro-v1:0",
                "description": "Amazon Nova Pro - High-performance model"
            },
            "nova_micro": {
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-micro-v1:0",
                "description": "Amazon Nova Micro - Lightweight model"
            },
            "nova_nano": {
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-nano-v1:0", 
                "description": "Amazon Nova Nano - Ultra-lightweight model"
            }
        }
        
        self.results = {}
        
    def set_environment_for_model(self, model_config: Dict[str, str]):
        """Set environment variables for a specific model"""
        for key, value in model_config.items():
            if key != "description":
                os.environ[key] = value
                print(f"🔧 Set {key} = {value}")
    
    def create_pipeline_for_model(self, model_config: Dict[str, str]) -> TheodoreIntelligencePipeline:
        """Create a fresh pipeline with the model configuration"""
        
        # Set environment variables
        self.set_environment_for_model(model_config)
        
        # Create fresh config (will pick up new environment vars)
        config = CompanyIntelligenceConfig()
        
        print(f"🔧 Pipeline config: bedrock_analysis_model = {config.bedrock_analysis_model}")
        
        # Create pipeline
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'Theodore'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        return pipeline
    
    def test_company_with_model(self, company_url: str, model_name: str, model_config: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with a specific model"""
        print(f"\n🔍 Testing {company_url} with {model_name}")
        print(f"📋 Model: {model_config['description']}")
        
        try:
            # Create pipeline for this model
            pipeline = self.create_pipeline_for_model(model_config)
            
            start_time = time.time()
            
            # Use the main pipeline method
            company_data = pipeline.process_single_company(
                company_name=company_url.replace('https://', '').replace('http://', '').replace('www.', ''),
                website=company_url
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate extraction quality
            quality_metrics = self.calculate_extraction_quality(company_data)
            
            print(f"✅ Success! Processing time: {processing_time:.1f}s")
            print(f"📊 Coverage: {quality_metrics['coverage_percentage']}%")
            print(f"🏢 Name: {getattr(company_data, 'name', 'Not extracted')}")
            print(f"🏭 Industry: {getattr(company_data, 'industry', 'Not extracted')}")
            
            # Extract key information
            result = {
                "model": model_name,
                "model_description": model_config["description"],
                "company_url": company_url,
                "processing_time_seconds": round(processing_time, 2),
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "extraction_quality": quality_metrics,
                "extracted_data": {
                    "company_name": getattr(company_data, 'name', None),
                    "company_description": getattr(company_data, 'company_description', None),
                    "industry": getattr(company_data, 'industry', None),
                    "business_model": getattr(company_data, 'business_model', None),
                    "company_size": getattr(company_data, 'company_size', None),
                    "target_market": getattr(company_data, 'target_market', None),
                    "founding_year": getattr(company_data, 'founding_year', None),
                    "location": getattr(company_data, 'location', None),
                    "pages_crawled": len(getattr(company_data, 'pages_crawled', [])),
                    "ai_summary": (getattr(company_data, 'ai_summary', None) or '')[:200] + '...' if getattr(company_data, 'ai_summary', None) else None
                },
                "cost_tracking": {
                    "total_input_tokens": getattr(company_data, 'total_input_tokens', 0),
                    "total_output_tokens": getattr(company_data, 'total_output_tokens', 0),
                    "total_cost_usd": getattr(company_data, 'total_cost_usd', 0.0)
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "model": model_name,
                "model_description": model_config["description"],
                "company_url": company_url,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_seconds": 0
            }
    
    def calculate_extraction_quality(self, company_data) -> Dict[str, Any]:
        """Calculate quality metrics for extracted data"""
        # Key fields to evaluate
        key_fields = [
            'name', 'company_description', 'industry', 'business_model',
            'company_size', 'target_market', 'founding_year', 'location', 
            'employee_count_range', 'funding_status', 'tech_stack', 
            'key_services', 'competitive_advantages', 'leadership_team'
        ]
        
        populated_fields = 0
        field_details = {}
        
        for field in key_fields:
            value = getattr(company_data, field, None)
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
                "value_type": type(value).__name__,
                "value_preview": str(value)[:100] if value else None
            }
        
        coverage_percentage = (populated_fields / len(key_fields)) * 100
        
        return {
            "total_key_fields": len(key_fields),
            "populated_fields": populated_fields,
            "coverage_percentage": round(coverage_percentage, 1),
            "pages_scraped": len(getattr(company_data, 'pages_crawled', [])),
            "has_ai_summary": bool(getattr(company_data, 'ai_summary', None)),
            "field_details": field_details
        }
    
    def run_comparison(self):
        """Run the full comparison test"""
        print("🤖 ACTUAL Theodore AI Model Comparison Test")
        print("=" * 70)
        print(f"Testing {len(self.companies)} companies with {len(self.models)} models")
        print("⚠️  WARNING: This will modify environment variables!")
        
        for company_url in self.companies:
            print(f"\n🏢 --- Testing company: {company_url} ---")
            company_results = {}
            
            for model_name, model_config in self.models.items():
                result = self.test_company_with_model(company_url, model_name, model_config)
                company_results[model_name] = result
                
                # Add delay between model tests to avoid rate limiting
                if result['success']:
                    print(f"📈 {model_name}: {result['extraction_quality']['coverage_percentage']}% coverage in {result['processing_time_seconds']}s")
                    if result.get('cost_tracking', {}).get('total_cost_usd', 0) > 0:
                        print(f"💰 Cost: ${result['cost_tracking']['total_cost_usd']:.4f}")
                else:
                    print(f"❌ {model_name}: Failed - {result.get('error', 'Unknown error')}")
                
                time.sleep(5)  # Delay between tests
            
            self.results[company_url] = company_results
            
            # Longer delay between companies
            print("⏳ Waiting 10 seconds before next company...")
            time.sleep(10)
        
        print(f"\n✅ Comparison test completed")
        return self.results
    
    def generate_report(self, output_dir: str):
        """Generate both JSON and markdown reports"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = os.path.join(output_dir, f"actual_model_comparison_results_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate markdown report
        md_file = os.path.join(output_dir, f"actual_model_comparison_report_{timestamp}.md")
        self.generate_markdown_report(md_file)
        
        print(f"\n📊 Reports generated:")
        print(f"  📁 JSON: {json_file}")
        print(f"  📊 Markdown: {md_file}")
        
        return md_file, json_file
    
    def generate_markdown_report(self, output_file: str):
        """Generate detailed markdown report"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        report = f"""# ACTUAL Theodore AI Model Comparison Report

**Generated**: {timestamp}  
**Test Type**: Real AI Model Performance Comparison  
**Companies Tested**: {len(self.companies)}  
**Models Compared**: {len(self.models)}  

## Executive Summary

This report shows ACTUAL performance differences between AI models tested with Theodore's intelligent scraping system.

### Models Tested:
"""
        
        for model_name, model_config in self.models.items():
            report += f"- **{model_name}**: {model_config['description']}\\n"
        
        report += f"""
### Test Companies:
"""
        for i, company in enumerate(self.companies, 1):
            report += f"{i}. {company}\\n"
        
        # Calculate overall statistics
        model_stats = self.calculate_model_statistics()
        
        if model_stats:
            report += """
---

## Performance Overview

| Model | Success Rate | Avg Coverage | Avg Time | Avg Cost | Best Performance |
|-------|--------------|--------------|----------|----------|------------------|
"""
            
            for model_name, stats in model_stats.items():
                best_metric = ""
                if stats['avg_coverage'] == max(s['avg_coverage'] for s in model_stats.values() if s['avg_coverage'] > 0):
                    best_metric = "Coverage"
                if stats['avg_processing_time'] == min(s['avg_processing_time'] for s in model_stats.values() if s['avg_processing_time'] > 0):
                    best_metric = "Speed" if not best_metric else best_metric + "/Speed"
                if stats['avg_cost'] == min(s['avg_cost'] for s in model_stats.values() if s['avg_cost'] > 0):
                    best_metric = "Cost" if not best_metric else best_metric + "/Cost"
                    
                report += f"| {model_name} | {stats['success_rate']:.1f}% | {stats['avg_coverage']:.1f}% | {stats['avg_processing_time']:.1f}s | ${stats['avg_cost']:.4f} | {best_metric} |\\n"
        
        report += """
---

## Detailed Results by Company

"""
        
        # Detailed results for each company
        for company_url, company_results in self.results.items():
            report += f"### {company_url}\\n\\n"
            
            successful_results = {k: v for k, v in company_results.items() if v.get('success', False)}
            
            if successful_results:
                # Performance table
                report += "#### Performance Metrics\\n\\n"
                report += "| Model | Coverage % | Processing Time | Pages Scraped | Total Cost |\\n"
                report += "|-------|------------|----------------|---------------|------------|\\n"
                
                for model_name, result in company_results.items():
                    if result.get('success', False):
                        quality = result.get('extraction_quality', {})
                        cost = result.get('cost_tracking', {})
                        report += f"| {model_name} | {quality.get('coverage_percentage', 0):.1f}% | {result.get('processing_time_seconds', 0):.1f}s | {quality.get('pages_scraped', 0)} | ${cost.get('total_cost_usd', 0):.4f} |\\n"
                    else:
                        report += f"| {model_name} | ❌ Failed | N/A | N/A | N/A |\\n"
                
                report += "\\n"
                
                # Data quality comparison
                report += "#### Extracted Information Quality\\n\\n"
                
                # Company identification
                report += "**Company Name Extraction:**\\n"
                for model_name, result in successful_results.items():
                    name = result.get('extracted_data', {}).get('company_name', 'Not extracted')
                    report += f"- {model_name}: {name}\\n"
                report += "\\n"
                
                # Industry classification
                report += "**Industry Classification:**\\n"
                for model_name, result in successful_results.items():
                    industry = result.get('extracted_data', {}).get('industry', 'Not classified')
                    report += f"- {model_name}: {industry}\\n"
                report += "\\n"
                
                # Business model
                report += "**Business Model:**\\n"
                for model_name, result in successful_results.items():
                    bm = result.get('extracted_data', {}).get('business_model', 'Not identified')
                    report += f"- {model_name}: {bm}\\n"
                report += "\\n"
            
            else:
                report += "*No successful extractions for this company.*\\n\\n"
            
            report += "---\\n\\n"
        
        # Analysis and recommendations
        if model_stats:
            # Best performing model by coverage
            best_coverage = max(model_stats.items(), key=lambda x: x[1]['avg_coverage'])
            fastest = min(((k, v) for k, v in model_stats.items() if v['avg_processing_time'] > 0), key=lambda x: x[1]['avg_processing_time'])
            most_efficient = min(((k, v) for k, v in model_stats.items() if v['avg_cost'] > 0), key=lambda x: x[1]['avg_cost'])
            highest_success = max(model_stats.items(), key=lambda x: x[1]['success_rate'])
            
            report += f"""## Analysis & Recommendations

### Key Findings:

1. **Best Data Coverage**: {best_coverage[0]} achieved {best_coverage[1]['avg_coverage']:.1f}% average field coverage
2. **Fastest Processing**: {fastest[0]} averaged {fastest[1]['avg_processing_time']:.1f} seconds per company
3. **Most Cost-Effective**: {most_efficient[0]} averaged ${most_efficient[1]['avg_cost']:.4f} per extraction
4. **Most Reliable**: {highest_success[0]} achieved {highest_success[1]['success_rate']:.1f}% success rate

### Recommendations:

#### For Production Use:
- **High-Quality Analysis**: Use {best_coverage[0]} for critical business intelligence
- **Cost-Conscious Deployments**: Choose {most_efficient[0]} for large-scale processing
- **Real-Time Applications**: Select {fastest[0]} for user-facing features

#### Technical Insights:

1. **Processing Speed vs Quality**: Compare coverage vs time trade-offs
2. **Cost Efficiency**: Real cost per successfully extracted field
3. **Reliability**: Success rates for production planning

---

*Report generated by Theodore ACTUAL AI Model Comparison System*  
*Test methodology: Each model tested with fresh environment configuration and pipeline initialization*
"""
        
        # Write the report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def calculate_model_statistics(self) -> Dict[str, Dict[str, float]]:
        """Calculate aggregate statistics for each model"""
        model_stats = {}
        
        for model_name in self.models.keys():
            successful_tests = []
            processing_times = []
            coverage_scores = []
            costs = []
            
            for company_results in self.results.values():
                result = company_results.get(model_name, {})
                if result.get('success', False):
                    successful_tests.append(1)
                    processing_times.append(result.get('processing_time_seconds', 0))
                    coverage_scores.append(result.get('extraction_quality', {}).get('coverage_percentage', 0))
                    costs.append(result.get('cost_tracking', {}).get('total_cost_usd', 0))
                else:
                    successful_tests.append(0)
            
            if successful_tests:
                model_stats[model_name] = {
                    'success_rate': (sum(successful_tests) / len(successful_tests) * 100),
                    'avg_processing_time': (sum(processing_times) / len(processing_times)) if processing_times else 0,
                    'avg_coverage': (sum(coverage_scores) / len(coverage_scores)) if coverage_scores else 0,
                    'avg_cost': (sum(costs) / len(costs)) if costs else 0,
                    'total_successful': sum(successful_tests),
                    'total_tests': len(successful_tests)
                }
        
        return model_stats

def main():
    """Main execution function"""
    print("🚀 ACTUAL Theodore AI Model Comparison")
    print("This will test REAL differences between AI models")
    print("=" * 60)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "actual_results")
    os.makedirs(output_dir, exist_ok=True)
    
    tester = ActualModelComparison()
    
    try:
        # Run the comparison
        results = tester.run_comparison()
        
        # Generate reports
        md_file, json_file = tester.generate_report(output_dir)
        
        print(f"\\n🎉 ACTUAL test completed successfully!")
        print(f"📊 Detailed report: {md_file}")
        print(f"📁 Raw data: {json_file}")
        
        # Print quick summary
        model_stats = tester.calculate_model_statistics()
        if model_stats:
            print("\\n📈 Quick Summary:")
            for model_name, stats in model_stats.items():
                print(f"  {model_name}: {stats['success_rate']:.0f}% success, {stats['avg_coverage']:.1f}% coverage, {stats['avg_processing_time']:.1f}s avg")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
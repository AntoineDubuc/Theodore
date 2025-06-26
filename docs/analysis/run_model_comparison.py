#!/usr/bin/env python3
"""
Simplified AI Model Comparison Script
Tests multiple AI models with 10 life sciences companies using Theodore's UI workflow
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Set up paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

# Import Theodore modules
from main_pipeline import TheodoreIntelligencePipeline
from models import CompanyIntelligenceConfig, CompanyData

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleModelComparison:
    """Simple model comparison using Theodore's existing pipeline"""
    
    def __init__(self):
        self.companies = [
            "scitara.com",
            "viseven.com", 
            "3dsbiovia.com",
            "agmednet.com",
            "aitiabio.com",
            "aizon.ai",
            "certara.com",
            "chemify.io",
            "citeline.com",
            "clinicalresearch.io",
            "dotcompliance.com"
        ]
        
        # Model configurations to test
        self.models = {
            "gemini_2_5_flash": {
                "gemini_model": "gemini-2.5-flash",
                "bedrock_analysis_model": "us.amazon.nova-pro-v1:0",  # Keep bedrock for embeddings
                "description": "Gemini 2.5 Flash - Fast, efficient model"
            },
            "gemini_2_5_pro": {
                "gemini_model": "gemini-2.5-pro", 
                "bedrock_analysis_model": "us.amazon.nova-pro-v1:0",
                "description": "Gemini 2.5 Pro - Advanced reasoning model"
            },
            "nova_pro": {
                "gemini_model": "gemini-2.5-flash",  # Keep gemini for page selection
                "bedrock_analysis_model": "us.amazon.nova-pro-v1:0",
                "description": "Amazon Nova Pro - High-performance model"
            },
            "nova_micro": {
                "gemini_model": "gemini-2.5-flash",
                "bedrock_analysis_model": "us.amazon.nova-micro-v1:0",
                "description": "Amazon Nova Micro - Lightweight model"
            },
            "nova_nano": {
                "gemini_model": "gemini-2.5-flash",
                "bedrock_analysis_model": "us.amazon.nova-nano-v1:0", 
                "description": "Amazon Nova Nano - Ultra-lightweight model"
            }
        }
        
        self.results = {}
        
    def create_pipeline_for_model(self, model_config: Dict[str, str]) -> TheodoreIntelligencePipeline:
        """Create Theodore pipeline with specific model configuration"""
        # Create custom config for this model
        config = CompanyIntelligenceConfig()
        
        # Override model settings
        if 'gemini_model' in model_config:
            os.environ['GEMINI_MODEL'] = model_config['gemini_model']
        if 'bedrock_analysis_model' in model_config:
            os.environ['BEDROCK_ANALYSIS_MODEL'] = model_config['bedrock_analysis_model']
        
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
        logger.info(f"Testing {company_url} with {model_name}")
        
        try:
            # Create pipeline for this model
            pipeline = self.create_pipeline_for_model(model_config)
            
            start_time = time.time()
            
            # Use the same workflow as Theodore's UI "Add New Company"
            company_data = pipeline.process_single_company(
                company_name=company_url.replace('https://', '').replace('http://', '').replace('www.', ''),
                website=company_url
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Calculate extraction quality
            quality_metrics = self.calculate_extraction_quality(company_data)
            
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
                    "employee_count_range": getattr(company_data, 'employee_count_range', None),
                    "funding_status": getattr(company_data, 'funding_status', None),
                    "tech_stack": getattr(company_data, 'tech_stack', []),
                    "key_services": getattr(company_data, 'key_services', []),
                    "competitive_advantages": getattr(company_data, 'competitive_advantages', []),
                    "leadership_team": getattr(company_data, 'leadership_team', []),
                    "pages_crawled": getattr(company_data, 'pages_crawled', []),
                    "crawl_duration": getattr(company_data, 'crawl_duration', None),
                    "ai_summary": getattr(company_data, 'ai_summary', None)[:500] if getattr(company_data, 'ai_summary', None) else None  # Truncate for readability
                },
                "cost_tracking": {
                    "total_input_tokens": getattr(company_data, 'total_input_tokens', 0),
                    "total_output_tokens": getattr(company_data, 'total_output_tokens', 0),
                    "total_cost_usd": getattr(company_data, 'total_cost_usd', 0.0)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {company_url} with {model_name}: {str(e)}")
            return {
                "model": model_name,
                "model_description": model_config["description"],
                "company_url": company_url,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_seconds": 0
            }
    
    def calculate_extraction_quality(self, company_data: CompanyData) -> Dict[str, Any]:
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
                "value_length": len(value) if isinstance(value, (str, list)) else None
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
        logger.info("Starting AI model comparison test")
        logger.info(f"Testing {len(self.companies)} companies with {len(self.models)} models")
        
        for company_url in self.companies:
            logger.info(f"\\n--- Testing company: {company_url} ---")
            company_results = {}
            
            for model_name, model_config in self.models.items():
                result = self.test_company_with_model(company_url, model_name, model_config)
                company_results[model_name] = result
                
                # Add delay between model tests to avoid rate limiting
                if result['success']:
                    logger.info(f"✅ {model_name}: {result['extraction_quality']['coverage_percentage']}% coverage in {result['processing_time_seconds']}s")
                else:
                    logger.info(f"❌ {model_name}: Failed - {result.get('error', 'Unknown error')}")
                
                time.sleep(3)  # Delay between tests
            
            self.results[company_url] = company_results
            
            # Longer delay between companies
            time.sleep(5)
        
        logger.info("\\nComparison test completed")
        return self.results
    
    def generate_report(self, output_dir: str):
        """Generate both JSON and markdown reports"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = os.path.join(output_dir, f"ai_model_comparison_results_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate markdown report
        md_file = os.path.join(output_dir, f"ai_model_comparison_report_{timestamp}.md")
        self.generate_markdown_report(md_file)
        
        logger.info(f"Reports generated:")
        logger.info(f"  📊 Markdown: {md_file}")
        logger.info(f"  📁 JSON: {json_file}")
        
        return md_file, json_file
    
    def generate_markdown_report(self, output_file: str):
        """Generate detailed markdown report"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        report = f"""# Theodore AI Model Comparison Report

**Generated**: {timestamp}  
**Test Type**: Life Sciences Company Intelligence Extraction  
**Companies Tested**: {len(self.companies)}  
**Models Compared**: {len(self.models)}  

## Executive Summary

This report compares 5 different AI models' performance in extracting company intelligence from life sciences companies using Theodore's intelligent scraping system. The test simulates the "Add New Company" workflow from Theodore's UI.

### Models Tested:
"""
        
        for model_name, model_config in self.models.items():
            report += f"- **{model_name}**: {model_config['description']}\\n"
        
        report += f"""
### Test Companies (Life Sciences Focus):
"""
        for i, company in enumerate(self.companies, 1):
            report += f"{i}. {company}\\n"
        
        # Calculate overall statistics
        model_stats = self.calculate_model_statistics()
        
        report += """
---

## Performance Overview

| Model | Success Rate | Avg Coverage | Avg Time | Avg Cost | Best Performance |
|-------|--------------|--------------|----------|----------|-----------------|
"""
        
        for model_name, stats in model_stats.items():
            best_metric = "Coverage" if stats['avg_coverage'] == max(s['avg_coverage'] for s in model_stats.values()) else ""
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
                
                # Company description quality
                report += "**Company Description Quality:**\\n"
                for model_name, result in successful_results.items():
                    desc = result.get('extracted_data', {}).get('company_description', '')
                    if desc:
                        desc_quality = f"{len(desc)} chars - {desc[:100]}..." if len(desc) > 100 else f"{len(desc)} chars - {desc}"
                    else:
                        desc_quality = "No description extracted"
                    report += f"- {model_name}: {desc_quality}\\n"
                report += "\\n"
            
            else:
                report += "*No successful extractions for this company.*\\n\\n"
            
            report += "---\\n\\n"
        
        # Analysis and recommendations
        report += """## Analysis & Recommendations

### Key Findings:

"""
        
        # Best performing model by coverage
        best_coverage = max(model_stats.items(), key=lambda x: x[1]['avg_coverage'])
        report += f"1. **Best Data Coverage**: {best_coverage[0]} achieved {best_coverage[1]['avg_coverage']:.1f}% average field coverage\\n"
        
        # Fastest model
        fastest = min(((k, v) for k, v in model_stats.items() if v['avg_processing_time'] > 0), key=lambda x: x[1]['avg_processing_time'])
        report += f"2. **Fastest Processing**: {fastest[0]} averaged {fastest[1]['avg_processing_time']:.1f} seconds per company\\n"
        
        # Most cost-effective
        most_efficient = min(((k, v) for k, v in model_stats.items() if v['avg_cost'] > 0), key=lambda x: x[1]['avg_cost'])
        report += f"3. **Most Cost-Effective**: {most_efficient[0]} averaged ${most_efficient[1]['avg_cost']:.4f} per extraction\\n"
        
        # Success rate analysis
        highest_success = max(model_stats.items(), key=lambda x: x[1]['success_rate'])
        report += f"4. **Most Reliable**: {highest_success[0]} achieved {highest_success[1]['success_rate']:.1f}% success rate\\n"
        
        report += """
### Recommendations:

#### For Production Use:
- **High-Quality Analysis**: Use the model with the best coverage percentage for critical business intelligence
- **Cost-Conscious Deployments**: Choose the most cost-effective model for large-scale processing
- **Real-Time Applications**: Select the fastest model for user-facing features

#### For Different Use Cases:
- **Research & Analysis**: Prioritize coverage quality over speed
- **Bulk Processing**: Balance cost efficiency with acceptable quality
- **Interactive Features**: Prioritize speed while maintaining minimum quality thresholds

### Technical Insights:

1. **Processing Speed vs Quality**: Analyze correlation between processing time and data coverage
2. **Cost Efficiency**: Compare cost per successfully extracted field across models
3. **Reliability**: Consider success rates when choosing models for production

---

*Report generated by Theodore AI Model Comparison System*  
*Test methodology: Each model tested against the same 11 life sciences companies using identical scraping parameters*
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
            
            model_stats[model_name] = {
                'success_rate': (sum(successful_tests) / len(successful_tests) * 100) if successful_tests else 0,
                'avg_processing_time': (sum(processing_times) / len(processing_times)) if processing_times else 0,
                'avg_coverage': (sum(coverage_scores) / len(coverage_scores)) if coverage_scores else 0,
                'avg_cost': (sum(costs) / len(costs)) if costs else 0,
                'total_successful': sum(successful_tests),
                'total_tests': len(successful_tests)
            }
        
        return model_stats

def main():
    """Main execution function"""
    print("🤖 Theodore AI Model Comparison Test")
    print("Testing life sciences companies with multiple AI models")
    print("=" * 60)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "model_comparison_results")
    os.makedirs(output_dir, exist_ok=True)
    
    tester = SimpleModelComparison()
    
    try:
        # Run the comparison
        results = tester.run_comparison()
        
        # Generate reports
        md_file, json_file = tester.generate_report(output_dir)
        
        print(f"\\n✅ Test completed successfully!")
        print(f"📊 Detailed report: {md_file}")
        print(f"📁 Raw data: {json_file}")
        
        # Print quick summary
        model_stats = tester.calculate_model_statistics()
        print("\\n📈 Quick Summary:")
        for model_name, stats in model_stats.items():
            print(f"  {model_name}: {stats['success_rate']:.0f}% success, {stats['avg_coverage']:.1f}% coverage, {stats['avg_processing_time']:.1f}s avg")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
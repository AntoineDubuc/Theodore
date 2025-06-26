#!/usr/bin/env python3
"""
AI Model Comparison Test Script
Tests multiple AI models with 10 life sciences companies to compare extraction quality
"""

import os
import sys
import json
import time
import asyncio
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
from concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
from bedrock_client import BedrockClient
from gemini_client import GeminiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiModelTester:
    """Test multiple AI models with the same companies"""
    
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
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
        
        # Model configurations
        self.models = {
            "gemini_2_5_flash": {
                "client_type": "gemini",
                "model": "gemini-2.5-flash",
                "description": "Gemini 2.5 Flash - Fast, efficient model"
            },
            "gemini_2_5_pro": {
                "client_type": "gemini", 
                "model": "gemini-2.5-pro",
                "description": "Gemini 2.5 Pro - Advanced reasoning model"
            },
            "nova_pro": {
                "client_type": "bedrock",
                "model": "us.amazon.nova-pro-v1:0",
                "description": "Amazon Nova Pro - High-performance model"
            },
            "nova_micro": {
                "client_type": "bedrock",
                "model": "us.amazon.nova-micro-v1:0", 
                "description": "Amazon Nova Micro - Lightweight model"
            },
            "nova_nano": {
                "client_type": "bedrock",
                "model": "us.amazon.nova-nano-v1:0",
                "description": "Amazon Nova Nano - Ultra-lightweight model"
            }
        }
        
        self.results = {}
        
    def setup_model_client(self, model_config: Dict[str, str]):
        """Set up client for specific model"""
        if model_config["client_type"] == "gemini":
            # Update config for Gemini
            config = CompanyIntelligenceConfig()
            config.gemini_model = model_config["model"]
            return GeminiClient(config)
        elif model_config["client_type"] == "bedrock":
            # Update config for Bedrock
            config = CompanyIntelligenceConfig()
            config.bedrock_analysis_model = model_config["model"]
            return BedrockClient(config)
        else:
            raise ValueError(f"Unknown client type: {model_config['client_type']}")
    
    def setup_scraper(self, ai_client):
        """Set up scraper with specific AI client"""
        config = CompanyIntelligenceConfig()
        scraper = ConcurrentIntelligentScraperSync(config, ai_client)
        return scraper
    
    async def test_company_with_model(self, company_url: str, model_name: str, model_config: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with a specific model"""
        logger.info(f"Testing {company_url} with {model_name}")
        
        try:
            # Set up AI client for this model
            ai_client = self.setup_model_client(model_config)
            scraper = self.setup_scraper(ai_client)
            
            start_time = time.time()
            
            # Perform the research
            company_data = await scraper.research_company_async(
                company_url, 
                enhanced_extraction=True
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Extract key metrics
            result = {
                "model": model_name,
                "model_description": model_config["description"],
                "company_url": company_url,
                "processing_time_seconds": processing_time,
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "company_name": getattr(company_data, 'name', None),
                    "company_description": getattr(company_data, 'company_description', None),
                    "industry": getattr(company_data, 'industry', None),
                    "business_model": getattr(company_data, 'business_model', None),
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
                    "ai_summary": getattr(company_data, 'ai_summary', None)
                },
                "extraction_quality": self.calculate_extraction_quality(company_data),
                "cost_estimate": self.estimate_cost(processing_time, model_config)
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
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def calculate_extraction_quality(self, company_data: CompanyData) -> Dict[str, Any]:
        """Calculate quality metrics for extracted data"""
        key_fields = [
            'name', 'company_description', 'industry', 'business_model',
            'target_market', 'founding_year', 'location', 'employee_count_range',
            'funding_status', 'tech_stack', 'key_services', 'competitive_advantages',
            'leadership_team'
        ]
        
        populated_fields = 0
        total_fields = len(key_fields)
        
        for field in key_fields:
            value = getattr(company_data, field, None)
            if value and (
                (isinstance(value, str) and len(value.strip()) > 0) or
                (isinstance(value, list) and len(value) > 0) or
                (isinstance(value, (int, float)) and value is not None)
            ):
                populated_fields += 1
        
        coverage_percentage = (populated_fields / total_fields) * 100
        
        return {
            "total_fields": total_fields,
            "populated_fields": populated_fields,
            "coverage_percentage": coverage_percentage,
            "pages_scraped": len(getattr(company_data, 'pages_crawled', [])),
            "has_ai_summary": bool(getattr(company_data, 'ai_summary', None))
        }
    
    def estimate_cost(self, processing_time: float, model_config: Dict[str, str]) -> Dict[str, Any]:
        """Estimate cost based on model and processing time"""
        # Rough cost estimates (these would need real pricing data)
        cost_per_1k_tokens = {
            "gemini_2_5_flash": 0.0001,
            "gemini_2_5_pro": 0.001,
            "nova_pro": 0.0008,
            "nova_micro": 0.0001,
            "nova_nano": 0.00005
        }
        
        # Estimate tokens (rough approximation)
        estimated_tokens = processing_time * 1000  # Very rough estimate
        model_name = next(name for name, config in self.models.items() if config == model_config)
        
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k_tokens.get(model_name, 0.001)
        
        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": estimated_cost,
            "cost_per_1k_tokens": cost_per_1k_tokens.get(model_name, 0.001)
        }
    
    async def run_comparison_test(self):
        """Run the full comparison test"""
        logger.info("Starting AI model comparison test")
        logger.info(f"Testing {len(self.companies)} companies with {len(self.models)} models")
        
        for company_url in self.companies:
            logger.info(f"\\n--- Testing company: {company_url} ---")
            company_results = {}
            
            for model_name, model_config in self.models.items():
                result = await self.test_company_with_model(company_url, model_name, model_config)
                company_results[model_name] = result
                
                # Add delay between model tests to avoid rate limiting
                await asyncio.sleep(2)
            
            self.results[company_url] = company_results
            
            # Add delay between companies
            await asyncio.sleep(5)
        
        logger.info("\\nComparison test completed")
        return self.results
    
    def generate_markdown_report(self, output_file: str):
        """Generate detailed markdown report"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        report = f"""# AI Model Comparison Report

**Generated**: {timestamp}  
**Companies Tested**: {len(self.companies)}  
**Models Compared**: {len(self.models)}  

## Executive Summary

This report compares the performance of 5 different AI models across {len(self.companies)} life sciences companies using Theodore's intelligent scraping system.

### Models Tested:
"""
        
        for model_name, model_config in self.models.items():
            report += f"- **{model_name}**: {model_config['description']}\\n"
        
        report += f"""
### Companies Analyzed:
"""
        for company in self.companies:
            report += f"- {company}\\n"
        
        report += """
---

## Detailed Results

"""
        
        # Generate detailed results for each company
        for company_url, company_results in self.results.items():
            report += f"### {company_url}\\n\\n"
            
            # Create comparison table
            report += "| Model | Success | Processing Time | Coverage % | Pages Scraped | Estimated Cost |\\n"
            report += "|-------|---------|----------------|------------|---------------|----------------|\\n"
            
            for model_name, result in company_results.items():
                if result.get('success', False):
                    quality = result.get('extraction_quality', {})
                    cost = result.get('cost_estimate', {})
                    report += f"| {model_name} | ✅ | {result.get('processing_time_seconds', 0):.1f}s | {quality.get('coverage_percentage', 0):.1f}% | {quality.get('pages_scraped', 0)} | ${cost.get('estimated_cost_usd', 0):.4f} |\\n"
                else:
                    report += f"| {model_name} | ❌ | N/A | N/A | N/A | N/A |\\n"
            
            report += "\\n"
            
            # Add extracted data comparison
            successful_results = {k: v for k, v in company_results.items() if v.get('success', False)}
            if successful_results:
                report += "#### Extracted Information Comparison\\n\\n"
                
                # Company name comparison
                report += "**Company Names:**\\n"
                for model_name, result in successful_results.items():
                    name = result.get('data', {}).get('company_name', 'Not extracted')
                    report += f"- {model_name}: {name}\\n"
                report += "\\n"
                
                # Industry comparison
                report += "**Industry Classification:**\\n"
                for model_name, result in successful_results.items():
                    industry = result.get('data', {}).get('industry', 'Not extracted')
                    report += f"- {model_name}: {industry}\\n"
                report += "\\n"
                
                # Business model comparison
                report += "**Business Model:**\\n"
                for model_name, result in successful_results.items():
                    bm = result.get('data', {}).get('business_model', 'Not extracted')
                    report += f"- {model_name}: {bm}\\n"
                report += "\\n"
                
                # AI Summary comparison (truncated)
                report += "**AI Summary (First 200 chars):**\\n"
                for model_name, result in successful_results.items():
                    summary = result.get('data', {}).get('ai_summary', 'Not generated')
                    if summary and len(summary) > 200:
                        summary = summary[:200] + "..."
                    report += f"- **{model_name}**: {summary}\\n"
                report += "\\n"
            
            report += "---\\n\\n"
        
        # Performance summary
        report += "## Performance Summary\\n\\n"
        
        # Calculate averages
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
                    costs.append(result.get('cost_estimate', {}).get('estimated_cost_usd', 0))
                else:
                    successful_tests.append(0)
            
            model_stats[model_name] = {
                'success_rate': sum(successful_tests) / len(successful_tests) * 100,
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'avg_coverage': sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0,
                'avg_cost': sum(costs) / len(costs) if costs else 0,
                'total_successful': sum(successful_tests)
            }
        
        report += "| Model | Success Rate | Avg Processing Time | Avg Coverage % | Avg Cost | Successful Tests |\\n"
        report += "|-------|--------------|-------------------|----------------|----------|------------------|\\n"
        
        for model_name, stats in model_stats.items():
            report += f"| {model_name} | {stats['success_rate']:.1f}% | {stats['avg_processing_time']:.1f}s | {stats['avg_coverage']:.1f}% | ${stats['avg_cost']:.4f} | {stats['total_successful']}/{len(self.companies)} |\\n"
        
        report += """
---

## Conclusions

### Best Performing Models:
"""
        
        # Sort by coverage percentage
        sorted_by_coverage = sorted(model_stats.items(), key=lambda x: x[1]['avg_coverage'], reverse=True)
        report += "\\n**By Coverage Quality:**\\n"
        for i, (model_name, stats) in enumerate(sorted_by_coverage[:3], 1):
            report += f"{i}. **{model_name}**: {stats['avg_coverage']:.1f}% average coverage\\n"
        
        # Sort by processing time
        sorted_by_speed = sorted(model_stats.items(), key=lambda x: x[1]['avg_processing_time'])
        report += "\\n**By Processing Speed:**\\n"
        for i, (model_name, stats) in enumerate(sorted_by_speed[:3], 1):
            report += f"{i}. **{model_name}**: {stats['avg_processing_time']:.1f}s average processing time\\n"
        
        # Sort by cost efficiency
        sorted_by_cost = sorted(model_stats.items(), key=lambda x: x[1]['avg_cost'])
        report += "\\n**By Cost Efficiency:**\\n"
        for i, (model_name, stats) in enumerate(sorted_by_cost[:3], 1):
            report += f"{i}. **{model_name}**: ${stats['avg_cost']:.4f} average cost per extraction\\n"
        
        report += """
### Recommendations:

1. **For Production Use**: Choose the model with the best balance of coverage quality and cost efficiency
2. **For Development/Testing**: Use the fastest model for rapid iteration
3. **For High-Quality Analysis**: Use the model with the highest coverage percentage

---

*Generated by Theodore AI Model Comparison Test*
"""
        
        # Write the report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Markdown report generated: {output_file}")
    
    def save_json_results(self, output_file: str):
        """Save detailed JSON results"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"JSON results saved: {output_file}")

async def main():
    """Main execution function"""
    print("🤖 Theodore AI Model Comparison Test")
    print("=" * 50)
    
    tester = MultiModelTester()
    
    try:
        # Run the comparison test
        results = await tester.run_comparison_test()
        
        # Generate outputs
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_path = os.path.dirname(__file__)
        
        json_file = os.path.join(base_path, f"ai_model_comparison_results_{timestamp}.json")
        md_file = os.path.join(base_path, f"ai_model_comparison_report_{timestamp}.md")
        
        tester.save_json_results(json_file)
        tester.generate_markdown_report(md_file)
        
        print(f"\\n✅ Test completed successfully!")
        print(f"📊 Report: {md_file}")
        print(f"📁 Raw data: {json_file}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
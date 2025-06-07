#!/usr/bin/env python3
"""
Comprehensive test script for Intelligent Company Scraper with detailed logging
Logs every phase, decision, and result for complete review and analysis
"""

import asyncio
import logging
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient


class DetailedTestLogger:
    """
    Custom logger that captures all phases and results for detailed review
    """
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.results = {
            'test_start': datetime.now().isoformat(),
            'companies_tested': [],
            'phases': {},
            'errors': [],
            'summary': {}
        }
        
        # Set up file and console logging
        self.setup_logging()
    
    def setup_logging(self):
        """Set up comprehensive logging to file and console"""
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, mode='w'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*80)
        self.logger.info("🧠 INTELLIGENT COMPANY SCRAPER - DETAILED TEST")
        self.logger.info("="*80)
    
    def log_phase_start(self, phase: str, company: str, details: dict = None):
        """Log the start of a test phase"""
        phase_key = f"{company}_{phase}"
        self.results['phases'][phase_key] = {
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'details': details or {},
            'results': {}
        }
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🚀 PHASE: {phase.upper()} - {company}")
        self.logger.info(f"{'='*60}")
        
        if details:
            for key, value in details.items():
                self.logger.info(f"📋 {key}: {value}")
    
    def log_phase_result(self, phase: str, company: str, results: dict):
        """Log the results of a test phase"""
        phase_key = f"{company}_{phase}"
        
        if phase_key in self.results['phases']:
            self.results['phases'][phase_key]['end_time'] = datetime.now().isoformat()
            self.results['phases'][phase_key]['status'] = 'completed'
            self.results['phases'][phase_key]['results'] = results
        
        self.logger.info(f"\n📊 PHASE RESULTS: {phase.upper()}")
        self.logger.info("-" * 40)
        
        for key, value in results.items():
            if isinstance(value, list):
                self.logger.info(f"📝 {key}: {len(value)} items")
                for i, item in enumerate(value[:10], 1):  # Show first 10
                    self.logger.info(f"   {i}. {item}")
                if len(value) > 10:
                    self.logger.info(f"   ... and {len(value) - 10} more items")
            elif isinstance(value, str) and len(value) > 200:
                self.logger.info(f"📝 {key}: {value[:200]}... ({len(value)} chars total)")
            else:
                self.logger.info(f"📝 {key}: {value}")
    
    def log_error(self, phase: str, company: str, error: Exception):
        """Log an error that occurred during testing"""
        error_info = {
            'phase': phase,
            'company': company,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['errors'].append(error_info)
        
        self.logger.error(f"\n❌ ERROR in {phase.upper()} - {company}")
        self.logger.error(f"Error Type: {type(error).__name__}")
        self.logger.error(f"Error Message: {str(error)}")
        self.logger.exception("Full traceback:")
    
    def log_company_start(self, company_data: CompanyData):
        """Log the start of testing a company"""
        company_info = {
            'name': company_data.name,
            'website': company_data.website,
            'start_time': datetime.now().isoformat(),
            'phases': [],
            'final_result': None
        }
        
        self.results['companies_tested'].append(company_info)
        
        self.logger.info(f"\n{'🏢' * 20}")
        self.logger.info(f"🏢 TESTING COMPANY: {company_data.name}")
        self.logger.info(f"🌐 Website: {company_data.website}")
        self.logger.info(f"{'🏢' * 20}")
    
    def log_company_result(self, company_data: CompanyData, result: CompanyData):
        """Log the final result for a company"""
        # Find the company in results and update
        for company_info in self.results['companies_tested']:
            if company_info['name'] == company_data.name:
                company_info['end_time'] = datetime.now().isoformat()
                company_info['final_result'] = {
                    'scrape_status': result.scrape_status,
                    'crawl_duration': result.crawl_duration,
                    'pages_crawled': len(result.pages_crawled) if result.pages_crawled else 0,
                    'description_length': len(result.company_description) if result.company_description else 0,
                    'scrape_error': result.scrape_error
                }
                break
        
        self.logger.info(f"\n🎯 FINAL RESULT FOR {company_data.name}")
        self.logger.info("="*50)
        self.logger.info(f"Status: {result.scrape_status}")
        self.logger.info(f"Duration: {result.crawl_duration:.2f}s")
        self.logger.info(f"Pages Processed: {len(result.pages_crawled) if result.pages_crawled else 0}")
        
        if result.scrape_status == "success":
            self.logger.info(f"Description Length: {len(result.company_description)} characters")
            self.logger.info("\n📄 SALES INTELLIGENCE GENERATED:")
            self.logger.info("-" * 60)
            self.logger.info(result.company_description)
            self.logger.info("-" * 60)
        else:
            self.logger.error(f"Error: {result.scrape_error}")
    
    def save_results(self):
        """Save all results to JSON file for detailed analysis"""
        self.results['test_end'] = datetime.now().isoformat()
        
        # Calculate summary statistics
        successful_companies = [c for c in self.results['companies_tested'] 
                               if c.get('final_result', {}).get('scrape_status') == 'success']
        
        self.results['summary'] = {
            'total_companies_tested': len(self.results['companies_tested']),
            'successful_companies': len(successful_companies),
            'failed_companies': len(self.results['companies_tested']) - len(successful_companies),
            'total_errors': len(self.results['errors']),
            'total_phases': len(self.results['phases']),
            'success_rate': len(successful_companies) / len(self.results['companies_tested']) * 100 if self.results['companies_tested'] else 0
        }
        
        # Save to JSON file
        results_file = self.log_file.replace('.log', '_results.json')
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"\n📁 Results saved to: {results_file}")
        
        # Print summary
        self.logger.info(f"\n🎉 TEST SUMMARY")
        self.logger.info("="*40)
        for key, value in self.results['summary'].items():
            self.logger.info(f"{key}: {value}")


async def test_company_with_detailed_logging(
    scraper: IntelligentCompanyScraper, 
    company_data: CompanyData, 
    test_logger: DetailedTestLogger
):
    """
    Test a single company with detailed logging of each phase
    """
    
    test_logger.log_company_start(company_data)
    
    try:
        # Phase 1: Link Discovery
        test_logger.log_phase_start("link_discovery", company_data.name, {
            "target_url": company_data.website,
            "max_depth": scraper.max_depth,
            "expected_sources": ["robots.txt", "sitemap.xml", "recursive_crawl"]
        })
        
        try:
            all_links = await scraper._discover_all_links(scraper._normalize_url(company_data.website))
            test_logger.log_phase_result("link_discovery", company_data.name, {
                "total_links_discovered": len(all_links),
                "sample_links": all_links[:20],
                "all_links": all_links
            })
        except Exception as e:
            test_logger.log_error("link_discovery", company_data.name, e)
            return company_data
        
        # Phase 2: LLM Page Selection
        test_logger.log_phase_start("llm_page_selection", company_data.name, {
            "input_links": len(all_links),
            "max_pages_to_select": scraper.max_pages,
            "llm_client": "Gemini" if scraper.gemini_client else "Bedrock" if scraper.bedrock_client else "None"
        })
        
        try:
            selected_urls = await scraper._llm_select_promising_pages(
                all_links, company_data.name, scraper._normalize_url(company_data.website)
            )
            test_logger.log_phase_result("llm_page_selection", company_data.name, {
                "pages_selected": len(selected_urls),
                "selection_ratio": f"{len(selected_urls)}/{len(all_links)}",
                "selected_urls": selected_urls
            })
        except Exception as e:
            test_logger.log_error("llm_page_selection", company_data.name, e)
            return company_data
        
        # Phase 3: Parallel Content Extraction
        test_logger.log_phase_start("parallel_extraction", company_data.name, {
            "pages_to_extract": len(selected_urls),
            "concurrent_limit": scraper.concurrent_limit,
            "extraction_method": "Crawl4AI AsyncWebCrawler"
        })
        
        try:
            page_contents = await scraper._parallel_extract_content(selected_urls)
            
            # Calculate extraction statistics
            successful_extractions = len(page_contents)
            failed_extractions = len(selected_urls) - successful_extractions
            total_content_length = sum(len(page['content']) for page in page_contents)
            
            test_logger.log_phase_result("parallel_extraction", company_data.name, {
                "successful_extractions": successful_extractions,
                "failed_extractions": failed_extractions,
                "success_rate": f"{successful_extractions}/{len(selected_urls)}",
                "total_content_length": total_content_length,
                "average_content_length": total_content_length // successful_extractions if successful_extractions > 0 else 0,
                "extracted_pages": [page['url'] for page in page_contents]
            })
        except Exception as e:
            test_logger.log_error("parallel_extraction", company_data.name, e)
            return company_data
        
        # Phase 4: LLM Aggregation
        test_logger.log_phase_start("llm_aggregation", company_data.name, {
            "content_pages": len(page_contents),
            "total_content_chars": sum(len(page['content']) for page in page_contents),
            "llm_model": "Gemini 2.0 Flash" if scraper.gemini_client else "Claude Sonnet 4"
        })
        
        try:
            sales_intelligence = await scraper._llm_aggregate_sales_intelligence(
                page_contents, company_data.name
            )
            test_logger.log_phase_result("llm_aggregation", company_data.name, {
                "intelligence_generated": len(sales_intelligence) > 0,
                "intelligence_length": len(sales_intelligence),
                "intelligence_content": sales_intelligence,
                "word_count": len(sales_intelligence.split()) if sales_intelligence else 0
            })
        except Exception as e:
            test_logger.log_error("llm_aggregation", company_data.name, e)
            return company_data
        
        # Apply results and return
        company_data.company_description = sales_intelligence
        company_data.pages_crawled = selected_urls
        company_data.crawl_depth = len(selected_urls)
        company_data.scrape_status = "success"
        
        return company_data
        
    except Exception as e:
        test_logger.log_error("overall_process", company_data.name, e)
        company_data.scrape_status = "failed"
        company_data.scrape_error = str(e)
        return company_data


async def run_comprehensive_test():
    """
    Run comprehensive test with multiple companies and detailed logging
    """
    
    # Set up detailed logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/intelligent_scraper_test_{timestamp}.log"
    test_logger = DetailedTestLogger(log_file)
    
    test_logger.logger.info("🔧 Initializing test environment...")
    
    # Initialize configuration and clients
    config = CompanyIntelligenceConfig()
    
    try:
        bedrock_client = BedrockClient(config)
        test_logger.logger.info("✅ Bedrock client initialized successfully")
    except Exception as e:
        test_logger.logger.error(f"❌ Bedrock client initialization failed: {e}")
        bedrock_client = None
    
    # Initialize intelligent scraper
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    # Log scraper configuration
    test_logger.logger.info(f"🔧 Scraper Configuration:")
    test_logger.logger.info(f"   Max Depth: {scraper.max_depth}")
    test_logger.logger.info(f"   Max Pages: {scraper.max_pages}")
    test_logger.logger.info(f"   Concurrent Limit: {scraper.concurrent_limit}")
    test_logger.logger.info(f"   Gemini Client: {'Available' if scraper.gemini_client else 'Not Available'}")
    test_logger.logger.info(f"   Bedrock Client: {'Available' if scraper.bedrock_client else 'Not Available'}")
    
    # Test companies - variety of sizes and types
    test_companies = [
        CompanyData(name="Stripe", website="https://stripe.com"),
        CompanyData(name="Notion", website="https://notion.so"),
        CompanyData(name="Linear", website="https://linear.app"),
    ]
    
    # Reduce scope for detailed testing
    scraper.max_pages = 10
    scraper.max_depth = 2
    
    test_logger.logger.info(f"\n🎯 Testing {len(test_companies)} companies with detailed logging...")
    test_logger.logger.info(f"📊 Reduced scope: max_pages={scraper.max_pages}, max_depth={scraper.max_depth}")
    
    # Test each company
    for i, company_data in enumerate(test_companies, 1):
        test_logger.logger.info(f"\n🔄 Testing company {i}/{len(test_companies)}")
        
        start_time = time.time()
        
        # Run detailed test
        result = await test_company_with_detailed_logging(scraper, company_data, test_logger)
        
        # Calculate duration
        result.crawl_duration = time.time() - start_time
        
        # Log final result
        test_logger.log_company_result(company_data, result)
        
        # Delay between companies
        if i < len(test_companies):
            test_logger.logger.info(f"\n⏳ Waiting 15 seconds before next company...")
            await asyncio.sleep(15)
    
    # Save final results
    test_logger.save_results()
    
    test_logger.logger.info(f"\n{'🎉' * 20}")
    test_logger.logger.info("🎉 COMPREHENSIVE TESTING COMPLETED")
    test_logger.logger.info(f"📁 Detailed logs saved to: {log_file}")
    test_logger.logger.info(f"📊 Results saved to: {log_file.replace('.log', '_results.json')}")
    test_logger.logger.info(f"{'🎉' * 20}")


def main():
    """
    Main function to run the detailed test
    """
    print("🧪 INTELLIGENT COMPANY SCRAPER - DETAILED TESTING")
    print("=" * 60)
    print("This will run comprehensive tests with detailed logging.")
    print("All phases, decisions, and results will be logged for review.")
    print("=" * 60)
    
    # Run the test
    asyncio.run(run_comprehensive_test())


if __name__ == "__main__":
    main()
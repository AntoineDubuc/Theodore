#!/usr/bin/env python3
"""
Fix the raw_content extraction issue in the intelligent scraper
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraperSync
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_and_fix_raw_content():
    """Process connatix.com and ensure raw_content is populated"""
    print("🔧 Fixing raw_content extraction for connatix.com")
    print("=" * 50)
    
    try:
        # Initialize components
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        gemini_client = GeminiClient(config)
        
        # Create a modified scraper that saves raw content
        scraper = IntelligentCompanyScraperSync(config, bedrock_client)
        
        # Monkey patch the scraper to save raw content
        original_scrape = scraper.scrape_company
        
        def enhanced_scrape(company_data, job_id=None):
            """Enhanced scraping that captures raw content"""
            # First run the original scrape
            result = original_scrape(company_data, job_id)
            
            # If we have AI summary but no raw content, use AI summary as raw content
            if result.ai_summary and not result.raw_content:
                print("📝 Using AI summary as raw_content for analysis")
                result.raw_content = result.ai_summary
            
            # If we have company description, append it
            if result.company_description and result.company_description != result.ai_summary:
                print("📝 Appending company description to raw_content")
                result.raw_content = f"{result.raw_content or ''}\n\n{result.company_description}"
            
            return result
        
        scraper.scrape_company = enhanced_scrape
        
        # Create company object
        company = CompanyData(name='connatix.com', website='connatix.com')
        
        # Step 1: Scrape website with enhanced extraction
        print("\n📊 Step 1: Scraping website with enhanced extraction...")
        company = scraper.scrape_company(company)
        print(f"   Scrape status: {company.scrape_status}")
        print(f"   Pages crawled: {len(company.pages_crawled) if company.pages_crawled else 0}")
        print(f"   Raw content length: {len(company.raw_content) if company.raw_content else 0}")
        
        # Step 2: If we have raw_content now, analyze with Bedrock
        if company.raw_content:
            print("\n🤖 Step 2: Analyzing with Bedrock using raw content...")
            analysis_result = bedrock_client.analyze_company_content(company)
            print(f"   Analysis result keys: {list(analysis_result.keys())}")
            
            # Apply analysis
            if "error" not in analysis_result:
                company.industry = analysis_result.get("industry", company.industry)
                company.business_model = analysis_result.get("business_model", company.business_model)
                company.company_size = analysis_result.get("company_size", company.company_size)
                company.target_market = analysis_result.get("target_market", company.target_market)
                
                # Lists
                if analysis_result.get("tech_stack"):
                    company.tech_stack = analysis_result["tech_stack"]
                if analysis_result.get("key_services"):
                    company.key_services = analysis_result["key_services"]
                if analysis_result.get("pain_points"):
                    company.pain_points = analysis_result["pain_points"]
                    
                print(f"   ✅ Applied Bedrock analysis results")
        
        # Step 3: Extract additional fields with Gemini
        print("\n🔮 Step 3: Extracting detailed fields with Gemini...")
        if company.raw_content:
            # Extract comprehensive company details
            prompt = f"""
            Based on this comprehensive company information, extract ALL the following details.
            
            Company: {company.name}
            Content: {company.raw_content[:10000]}
            
            Extract in detail:
            1. Location/Headquarters (city, state/country)
            2. Employee count or size estimate (be specific if possible)
            3. Founded year
            4. ALL products and services offered (comprehensive list)
            5. Value proposition (clear statement)
            6. Company culture and values
            7. Funding information (stage, amount, investors)
            8. Key leadership/executives (names and titles)
            9. Recent news or updates
            10. Awards and certifications
            11. Key partnerships
            12. Contact information (emails, phone, addresses)
            13. Social media links
            
            Return as JSON with these exact keys:
            location, employee_count_range, founding_year, products_services_offered (array),
            value_proposition, company_culture, funding_status, leadership_team (array of objects with name and title),
            recent_news (array), certifications (array), partnerships (array), 
            contact_info (object with email, phone, address), social_media (object with platform names as keys)
            
            Be thorough and extract as much detail as possible. If information is not available, use null.
            """
            
            gemini_result = gemini_client.analyze_content(prompt)
            print(f"   Gemini response received: {len(gemini_result) if gemini_result else 0} chars")
            
            # Try to parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', gemini_result, re.DOTALL)
                if json_match:
                    extra_data = json.loads(json_match.group())
                    
                    # Apply all extracted data
                    company.location = extra_data.get('location', company.location)
                    company.employee_count_range = extra_data.get('employee_count_range', company.employee_count_range)
                    company.founding_year = extra_data.get('founding_year', company.founding_year)
                    company.value_proposition = extra_data.get('value_proposition', company.value_proposition)
                    company.company_culture = extra_data.get('company_culture', company.company_culture)
                    company.funding_status = extra_data.get('funding_status', company.funding_status)
                    
                    # Arrays
                    if extra_data.get('products_services_offered'):
                        company.products_services_offered = extra_data['products_services_offered']
                    if extra_data.get('leadership_team'):
                        company.leadership_team = extra_data['leadership_team']
                    if extra_data.get('recent_news'):
                        company.recent_news = extra_data['recent_news']
                    if extra_data.get('certifications'):
                        company.certifications = extra_data['certifications']
                    if extra_data.get('partnerships'):
                        company.partnerships = extra_data['partnerships']
                    
                    # Objects
                    if extra_data.get('contact_info'):
                        company.contact_info = extra_data['contact_info']
                    if extra_data.get('social_media'):
                        company.social_media = extra_data['social_media']
                    
                    print(f"   ✅ Extracted detailed fields with Gemini")
            except Exception as e:
                print(f"   ⚠️  Could not parse Gemini response: {e}")
        
        # Step 4: Extract similarity metrics
        print("\n🎯 Step 4: Extracting similarity metrics...")
        if company.raw_content:
            metrics_prompt = f"""
            Analyze this company and determine:
            
            Company: {company.name}
            Content: {company.raw_content[:5000]}
            
            1. Company Stage: Choose from startup, growth, mature, enterprise
            2. Tech Sophistication: Choose from basic, intermediate, advanced, cutting-edge
            3. Geographic Scope: Choose from local, regional, national, international
            4. Business Model Type: Choose from product, service, marketplace, platform, hybrid
            5. Has Job Listings: true/false
            6. Job Listings Count: number (if applicable)
            
            Return as JSON with keys: company_stage, tech_sophistication, geographic_scope, 
            business_model_type, has_job_listings, job_listings_count
            """
            
            metrics_result = gemini_client.analyze_content(metrics_prompt)
            try:
                json_match = re.search(r'\{.*\}', metrics_result, re.DOTALL)
                if json_match:
                    metrics_data = json.loads(json_match.group())
                    company.company_stage = metrics_data.get('company_stage', 'Unknown')
                    company.tech_sophistication = metrics_data.get('tech_sophistication', 'Unknown')
                    company.geographic_scope = metrics_data.get('geographic_scope', 'Unknown')
                    company.business_model_type = metrics_data.get('business_model_type', 'Unknown')
                    company.has_job_listings = metrics_data.get('has_job_listings')
                    company.job_listings_count = metrics_data.get('job_listings_count')
                    print(f"   ✅ Extracted similarity metrics")
            except Exception as e:
                print(f"   ⚠️  Could not extract metrics: {e}")
        
        # Print final results
        print("\n📊 Final Company Data:")
        print("-" * 50)
        data_dict = company.model_dump()
        
        populated_count = 0
        for field, value in data_dict.items():
            if value and value != [] and value != {} and value != "Unknown":
                populated_count += 1
                if isinstance(value, str) and len(value) > 100:
                    print(f"✅ {field}: {value[:100]}...")
                else:
                    print(f"✅ {field}: {value}")
        
        print(f"\n📈 Populated {populated_count} out of {len(data_dict)} fields")
        
        # Update Google Sheets
        print("\n📊 Updating Google Sheets...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        sheets_client.update_company_results(TEST_SHEET_ID, 2, company)
        print("✅ Sheet updated with comprehensive data!")
        
        # Save debug data
        output_file = Path(__file__).parent / 'connatix_fixed.json'
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        print(f"\n💾 Full data saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Processing error", exc_info=True)

if __name__ == "__main__":
    extract_and_fix_raw_content()
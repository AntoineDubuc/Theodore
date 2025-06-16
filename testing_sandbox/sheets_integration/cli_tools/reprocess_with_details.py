#!/usr/bin/env python3
"""
Reprocess connatix.com with detailed field extraction
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

def reprocess_with_details():
    """Reprocess connatix.com and extract all fields"""
    print("🔄 Reprocessing connatix.com with detailed extraction")
    print("=" * 50)
    
    try:
        # Initialize components
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        gemini_client = GeminiClient(config)
        scraper = IntelligentCompanyScraperSync(config, bedrock_client)
        
        # Create company object
        company = CompanyData(name='connatix.com', website='connatix.com')
        
        # Step 1: Scrape website
        print("\n📊 Step 1: Scraping website...")
        company = scraper.scrape_company(company)
        print(f"   Scrape status: {company.scrape_status}")
        print(f"   Pages crawled: {len(company.pages_crawled) if company.pages_crawled else 0}")
        
        # Check what data we have after scraping
        print("\n📋 After scraping:")
        print(f"   AI Summary: {company.ai_summary[:100] if company.ai_summary else 'None'}")
        print(f"   Industry: {company.industry}")
        print(f"   Raw content length: {len(company.raw_content) if company.raw_content else 0}")
        
        # Step 2: Analyze with Bedrock
        print("\n🤖 Step 2: Analyzing with Bedrock...")
        if company.raw_content:
            analysis_result = bedrock_client.analyze_company_content(company)
            print(f"   Analysis result keys: {list(analysis_result.keys())}")
            
            # Apply analysis
            if "error" not in analysis_result:
                company.industry = analysis_result.get("industry", company.industry)
                company.business_model = analysis_result.get("business_model", company.business_model)
                company.company_size = analysis_result.get("company_size", company.company_size)
                company.target_market = analysis_result.get("target_market", company.target_market)
                company.ai_summary = analysis_result.get("ai_summary", company.ai_summary)
                
                # Lists
                if analysis_result.get("tech_stack"):
                    company.tech_stack = analysis_result["tech_stack"]
                if analysis_result.get("key_services"):
                    company.key_services = analysis_result["key_services"]
                if analysis_result.get("pain_points"):
                    company.pain_points = analysis_result["pain_points"]
                
                print(f"   ✅ Applied analysis results")
        
        # Step 3: Extract additional fields with Gemini
        print("\n🔮 Step 3: Extracting additional fields with Gemini...")
        if company.raw_content:
            # Extract company details
            prompt = f"""
            Based on this company information, extract the following details:
            
            Company: {company.name}
            Content: {company.raw_content[:5000]}
            
            Extract:
            1. Location/Headquarters
            2. Employee count or size estimate
            3. Founded year
            4. Key products/services offered
            5. Value proposition
            6. Company description (1-2 sentences)
            7. Any funding information
            8. Key leadership/executives mentioned
            
            Return as JSON with these exact keys:
            location, employee_count_range, founding_year, products_services_offered,
            value_proposition, company_description, funding_status, leadership_team
            """
            
            gemini_result = gemini_client.analyze_content(prompt, max_tokens=1000)
            print(f"   Gemini response received: {len(gemini_result) if gemini_result else 0} chars")
            
            # Try to parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', gemini_result, re.DOTALL)
                if json_match:
                    extra_data = json.loads(json_match.group())
                    
                    # Apply extracted data
                    company.location = extra_data.get('location', company.location)
                    company.employee_count_range = extra_data.get('employee_count_range', company.employee_count_range)
                    company.founding_year = extra_data.get('founding_year', company.founding_year)
                    company.value_proposition = extra_data.get('value_proposition', company.value_proposition)
                    company.company_description = extra_data.get('company_description', company.company_description)
                    company.funding_status = extra_data.get('funding_status', company.funding_status)
                    
                    if extra_data.get('products_services_offered'):
                        company.products_services_offered = extra_data['products_services_offered']
                    if extra_data.get('leadership_team'):
                        company.leadership_team = extra_data['leadership_team']
                    
                    print(f"   ✅ Extracted additional fields")
            except Exception as e:
                print(f"   ⚠️  Could not parse Gemini response: {e}")
        
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
        print("✅ Sheet updated!")
        
        # Save debug data
        output_file = Path(__file__).parent / 'connatix_reprocessed.json'
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        print(f"\n💾 Full data saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Reprocessing error", exc_info=True)

if __name__ == "__main__":
    reprocess_with_details()
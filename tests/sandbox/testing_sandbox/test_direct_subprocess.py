#!/usr/bin/env python3
import subprocess
import json
import tempfile
import os
import sys

def test_subprocess_scraper():
    """Test the exact subprocess approach used in the main application"""
    
    company_name = "Anthropic"
    company_website = "https://anthropic.com"
    job_id = "test_job"
    
    script_content = f'''#!/usr/bin/env python3
import asyncio
import json
import sys
import os
sys.path.append("{os.getcwd()}")

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient

async def run_scraping():
    try:
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        company_data = CompanyData(
            name="{company_name}",
            website="{company_website}"
        )
        
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        result = await scraper.scrape_company_intelligent(company_data, "{job_id}")
        
        result_dict = {{
            "success": True,
            "name": result.name,
            "website": result.website,
            "scrape_status": result.scrape_status,
            "scrape_error": result.scrape_error,
            "company_description": result.company_description,
            "ai_summary": result.ai_summary,
            "industry": result.industry,
            "business_model": result.business_model,
            "target_market": result.target_market,
            "key_services": result.key_services or [],
            "company_size": result.company_size,
            "location": result.location,
            "tech_stack": result.tech_stack or [],
            "value_proposition": result.value_proposition,
            "pain_points": result.pain_points or [],
            "pages_crawled": result.pages_crawled or [],
            "crawl_duration": result.crawl_duration,
            "crawl_depth": result.crawl_depth
        }}
        
        return result_dict
        
    except Exception as e:
        import traceback
        return {{
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "scrape_status": "failed",
            "scrape_error": str(e)
        }}

if __name__ == "__main__":
    result = asyncio.run(run_scraping())
    print(json.dumps(result, default=str))
'''
    
    # Write script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        print(f"Running subprocess script at: {script_path}")
        
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd()
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)}")
        print(f"Stderr length: {len(result.stderr)}")
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"JSON parsed successfully!")
                print(f"Success: {data.get('success')}")
                print(f"Scrape status: {data.get('scrape_status')}")
                print(f"Description length: {len(str(data.get('company_description', '')))}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw stdout: {result.stdout[:500]}...")
        else:
            print(f"Subprocess failed!")
            print(f"Stderr: {result.stderr}")
            
    finally:
        # Clean up
        try:
            os.unlink(script_path)
        except:
            pass

if __name__ == "__main__":
    test_subprocess_scraper()
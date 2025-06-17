#!/usr/bin/env python3
"""
Test what the actual generated subprocess script looks like
"""
import sys
import os
import tempfile
sys.path.append(os.getcwd())

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient

def generate_test_script():
    """Generate the same script that would be used in subprocess"""
    
    config = CompanyIntelligenceConfig()
    bedrock_client = BedrockClient(config)
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    # Create test company data (same as what would be passed)
    company_data = CompanyData(name="OpenAI", website="https://openai.com")
    job_id = "test_debug"
    
    # Generate the script exactly as the scraper would
    safe_job_id = job_id if job_id else 'subprocess'
    
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
        import logging
        # Suppress debug output to keep stdout clean for JSON
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        company_data = CompanyData(
            name="{company_data.name}",
            website="{company_data.website}"
        )
        
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        # Capture the original print function and redirect to stderr
        import builtins
        original_print = builtins.print
        def debug_print(*args, **kwargs):
            kwargs['file'] = sys.stderr
            original_print(*args, **kwargs)
        builtins.print = debug_print
        
        try:
            result = await scraper.scrape_company_intelligent(company_data, "{safe_job_id}")
        finally:
            # Restore original print
            builtins.print = original_print
        
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
    
    return script_content

def test_generated_script():
    """Test the generated script by writing it to a file and running it"""
    
    print("🧪 Generating subprocess script...")
    script_content = generate_test_script()
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    print(f"📝 Script saved to: {script_path}")
    print(f"📏 Script length: {len(script_content)} characters")
    
    # Show first part of script
    print("\n📋 Script preview (first 20 lines):")
    lines = script_content.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:2d}: {line}")
    
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    print(f"\n🧪 Testing script execution with 10s timeout...")
    
    import subprocess
    import time
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout for testing
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Script completed in {duration:.2f} seconds")
        print(f"🔧 Return code: {result.returncode}")
        print(f"📤 Stdout length: {len(result.stdout)}")
        print(f"📤 Stderr length: {len(result.stderr)}")
        
        if result.stdout:
            print(f"\n📤 Stdout preview:")
            print(result.stdout[:500])
            if len(result.stdout) > 500:
                print("... (truncated)")
        
        if result.stderr:
            print(f"\n🔧 Stderr preview:")
            print(result.stderr[:500])
            if len(result.stderr) > 500:
                print("... (truncated)")
                
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        print(f"⏰ Script timed out after {duration:.2f} seconds")
        print(f"🔧 This confirms the subprocess is hanging!")
        
    except Exception as e:
        print(f"💥 Script execution failed: {e}")
    
    finally:
        # Clean up
        try:
            os.unlink(script_path)
            print(f"🗑️ Cleaned up temp script: {script_path}")
        except:
            pass

if __name__ == "__main__":
    test_generated_script()
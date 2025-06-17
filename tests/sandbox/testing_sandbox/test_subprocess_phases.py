#!/usr/bin/env python3
"""
Test each phase of the subprocess script individually to find the hang
"""
import asyncio
import json
import sys
import os
import time
sys.path.append(os.getcwd())

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_phase_1_basic_imports():
    """Test basic imports and setup"""
    try:
        print("🧪 Phase 1: Testing basic imports...", file=sys.stderr)
        
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        print("✅ Phase 1: All imports successful", file=sys.stderr)
        return {"success": True, "phase": "imports"}
    except Exception as e:
        print(f"❌ Phase 1: Import failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "imports"}

async def test_phase_2_client_creation():
    """Test creating clients"""
    try:
        print("🧪 Phase 2: Testing client creation...", file=sys.stderr)
        
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        print("✅ Phase 2: Clients created successfully", file=sys.stderr)
        return {"success": True, "phase": "client_creation"}
    except Exception as e:
        print(f"❌ Phase 2: Client creation failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "client_creation"}

async def test_phase_3_company_data():
    """Test creating company data"""
    try:
        print("🧪 Phase 3: Testing company data creation...", file=sys.stderr)
        
        from src.models import CompanyData
        
        company_data = CompanyData(
            name="OpenAI",
            website="https://openai.com"
        )
        
        print("✅ Phase 3: Company data created successfully", file=sys.stderr)
        return {"success": True, "phase": "company_data"}
    except Exception as e:
        print(f"❌ Phase 3: Company data creation failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "company_data"}

async def test_phase_4_scraper_creation():
    """Test creating scraper"""
    try:
        print("🧪 Phase 4: Testing scraper creation...", file=sys.stderr)
        
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        print("✅ Phase 4: Scraper created successfully", file=sys.stderr)
        return {"success": True, "phase": "scraper_creation"}
    except Exception as e:
        print(f"❌ Phase 4: Scraper creation failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "scraper_creation"}

async def test_phase_5_bedrock_simple_call():
    """Test a simple BedrockClient call"""
    try:
        print("🧪 Phase 5: Testing simple BedrockClient call...", file=sys.stderr)
        
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        start_time = time.time()
        response = bedrock_client.analyze_content("What is 2+2?")
        duration = time.time() - start_time
        
        print(f"✅ Phase 5: BedrockClient call completed in {duration:.2f}s", file=sys.stderr)
        print(f"✅ Phase 5: Response length: {len(response)}", file=sys.stderr)
        return {"success": True, "phase": "bedrock_call", "duration": duration, "response_length": len(response)}
    except Exception as e:
        print(f"❌ Phase 5: BedrockClient call failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "bedrock_call"}

async def test_phase_6_scraper_method_start():
    """Test starting the scraper method (but with quick timeout)"""
    try:
        print("🧪 Phase 6: Testing scraper method start...", file=sys.stderr)
        
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        company_data = CompanyData(
            name="OpenAI",
            website="https://openai.com"
        )
        
        print("🧪 Phase 6: Calling scraper with 5s timeout...", file=sys.stderr)
        
        # Try with very short timeout
        result = await asyncio.wait_for(
            scraper.scrape_company_intelligent(company_data, "test_phase_6"),
            timeout=5.0
        )
        
        print("✅ Phase 6: Scraper completed within 5s!", file=sys.stderr)
        return {"success": True, "phase": "scraper_method", "scrape_status": result.scrape_status}
        
    except asyncio.TimeoutError:
        print("⏰ Phase 6: Scraper timed out after 5s", file=sys.stderr)
        return {"success": False, "error": "Timeout after 5s", "phase": "scraper_method"}
    except Exception as e:
        print(f"❌ Phase 6: Scraper method failed: {e}", file=sys.stderr)
        return {"success": False, "error": str(e), "phase": "scraper_method"}

async def main():
    """Run all phases to find where it hangs"""
    
    print("🔍 SUBPROCESS PHASE TESTING", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    phases = [
        ("Basic Imports", test_phase_1_basic_imports),
        ("Client Creation", test_phase_2_client_creation),
        ("Company Data", test_phase_3_company_data),
        ("Scraper Creation", test_phase_4_scraper_creation),
        ("BedrockClient Call", test_phase_5_bedrock_simple_call),
        ("Scraper Method", test_phase_6_scraper_method_start)
    ]
    
    results = []
    
    for phase_name, phase_func in phases:
        print(f"\n🧪 Running Phase: {phase_name}", file=sys.stderr)
        
        try:
            start_time = time.time()
            result = await phase_func()
            duration = time.time() - start_time
            
            result["duration"] = duration
            results.append({"phase": phase_name, **result})
            
            if result["success"]:
                print(f"✅ {phase_name}: PASSED in {duration:.2f}s", file=sys.stderr)
            else:
                print(f"❌ {phase_name}: FAILED in {duration:.2f}s - {result.get('error', 'Unknown')}", file=sys.stderr)
                break  # Stop at first failure
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {phase_name}: EXCEPTION in {duration:.2f}s - {str(e)}", file=sys.stderr)
            results.append({"phase": phase_name, "success": False, "error": str(e), "duration": duration})
            break
    
    print("\n" + "=" * 50, file=sys.stderr)
    print("📊 PHASE TEST COMPLETE", file=sys.stderr)
    
    # Output results as JSON to stdout for the parent process
    print(json.dumps(results, default=str))

if __name__ == "__main__":
    asyncio.run(main())
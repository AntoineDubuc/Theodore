#!/usr/bin/env python3
"""
Test which import is causing the hang
"""
import json
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

def test_imports():
    try:
        print("🧪 Starting import test...", file=sys.stderr)
        start_time = time.time()
        
        print("🧪 Testing basic imports...", file=sys.stderr)
        from src.models import CompanyData, CompanyIntelligenceConfig
        print(f"✅ CompanyData imported in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        start_time = time.time()
        from src.bedrock_client import BedrockClient
        print(f"✅ BedrockClient imported in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        print("🧪 Testing config creation...", file=sys.stderr)
        start_time = time.time()
        config = CompanyIntelligenceConfig()
        print(f"✅ Config created in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        print("🧪 Testing BedrockClient constructor...", file=sys.stderr)
        start_time = time.time()
        bedrock_client = BedrockClient(config)
        print(f"✅ BedrockClient created in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        print("🧪 Testing scraper import...", file=sys.stderr)
        start_time = time.time()
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        print(f"✅ IntelligentCompanyScraper imported in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        print("🧪 Testing scraper constructor...", file=sys.stderr)
        start_time = time.time()
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        print(f"✅ IntelligentCompanyScraper created in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        return {"success": True, "message": "All imports successful"}
        
    except Exception as e:
        print(f"❌ Import failed: {e}", file=sys.stderr)
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}", file=sys.stderr)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    result = test_imports()
    print(json.dumps(result, default=str))